#!/usr/bin/env python3
"""Auditoria de seguridad de un servidor: ssh-audit (desde afuera) y Lynis (el reporte que trae una persona),
normalizados al esquema comun de hallazgos (bin/seguridad/normalizar.py). SOLO LECTURA.

    python -I bin/auditar-host.py --host <alias> --ssh-audit <reporte.json>                 (ssh-audit -j, ya corrido)
    python -I bin/auditar-host.py --host <alias> --lynis <lynis-report.dat> --lynis-log <lynis.log>
    python -I bin/auditar-host.py --host <alias> --correr-ssh-audit [--puerto 22] [--politica "<nombre o archivo>"]
    opciones: --umbral ALTA|MEDIA|BAJA (por defecto ALTA; CRITICA y ALTA frenan siempre)  --max-dias 7 (edad del reporte de Lynis; 0 = no mira)
              --modulo <slug> | --inventario <ruta>  --raiz <repo>  --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA)   2 = SIN DATOS
Con un HALLAZGO y un chequeo sin datos a la vez sale 1, y la linea de ese chequeo dice SIN DATOS.

POR QUE EXISTE. "Que tan seguro esta el servidor" lo contestaba el modelo leyendo salidas sueltas, y el codigo
de salida de las herramientas engania: el de ssh-audit no dice si llego a conectar, y Lynis corrido sin root
saltea pruebas sin dejarlo escrito en su reporte. Aca se lee siempre igual. HALLAZGO: un algoritmo de SSH con
falla, un CVE que ssh-audit le atribuye a la version, una politica de ssh-audit que no pasa, una advertencia de
Lynis (en el umbral o por encima). SIN DATOS: no hay ningun reporte; un reporte ausente, vacio, ilegible, de
otra herramienta, de un formato que no trae notas o sin algoritmos negociados; Lynis cortado, viejo, con una
excepcion interna, o corrido sin privilegios (o sin el log que permite saberlo). El estado de la categoria host
y el veredicto los decide el paquete (poner_categoria y cerrar), igual que en los demas escaneres.

QUE NO HACE. Antes de nada pasa por el inventario: el alias tiene que ser un servidor autorizado hasta N0; si
no, FRENA y no lee nada. No ejecuta nada dentro del servidor: el reporte de Lynis lo genera una persona y se
lo pasa. Lo unico que corre, y solo con --correr-ssh-audit, es ssh-audit desde esta maquina, que se conecta
como un cliente y no deja nada (con --skip-rate-test: sin la rafaga de conexiones). Lista negra: lo que cambia
algo o ataca (--dheat, --conn-rate-test, --remediate, --active, -T/--targets, --asff, --pgsql, --bc-api-key)
FRENA si se pide, y tambien cualquier opcion que este script no conoce. No muestra la direccion ni el nombre
real del servidor. Lo unico que escribe es el reporte crudo de ssh-audit en borrador/seguridad/<fecha>-<alias
saneado>/ (sin barras ni nada que no sea letra, numero, punto o guion: un alias no saca nada del borrador).
Solo biblioteca estandar. ASCII puro.
"""

import argparse
import calendar
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario
from seguridad import normalizar  # noqa: E402  el esquema comun y sus reglas

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
NOMBRE = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = 'auditar-host'
NIVELES = ('INFO', 'BAJA', 'MEDIA', 'ALTA', 'CRITICA')
UMBRALES = ('ALTA', 'MEDIA', 'BAJA')      # CRITICA no: aflojaria la regla del paquete (CRITICA y ALTA frenan)
DIAS_LYNIS = 7
TOPE_SEGUNDOS = 120
SIN_ROOT = 'This test needs root permissions'        # el SKIPREASON de Lynis cuando le falta root
# Lo que cambia algo o ataca (investigacion 05, 3.3), mas lo que sale del inventario (-T) o carga al servidor
# con una rafaga de conexiones. Si se pide, FRENA; y la orden armada se revisa contra la misma lista.
PROHIBIDAS = ('--dheat', '--conn-rate-test', '-T', '--targets', '--remediate', 'remediate', '--active', '--asff', '--pgsql',
              '--bc-api-key')
DESTINO_SSH = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
HOST = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.:_-]*$')
FECHA = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})')
CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f]')
NO_MIRA = ('lo de adentro del servidor que Lynis no reviso, o todo lo de adentro si no se paso --lynis: este script no corre nada alla',
           'que el reporte de Lynis sea de este servidor: lo trae una persona',
           'la fecha de un reporte de ssh-audit pasado por archivo (no la trae): para algo de hoy, --correr-ssh-audit',
           'si el hallazgo pesa para el negocio, y que controles de la linea base aplican: eso lo fija la politica del modulo',
           'las imagenes (escanear-imagenes.py), la salud (salud-host.py) y el codigo de infraestructura (auditar-iac.py)')


def limpio(texto, largo=140):
    """Lo que viene de un servidor o de un escaner es dato: sin caracteres de control y acotado."""
    t = CONTROL.sub('', str(texto if texto is not None else ''))
    return t if len(t) <= largo else t[:largo - 3] + '...'


def saneado(alias):
    """El alias como nombre de carpeta: sin barras ni nada que no sea letra, numero, punto, guion o guion bajo."""
    return re.sub(r'[^A-Za-z0-9._-]', '_', alias or 'sin-alias')


def hallazgo(herramienta, regla, titulo, severidad, activo, cve=''):
    """Un hallazgo del esquema comun, con la huella y las reglas del paquete."""
    return normalizar.hallazgo(herramienta=herramienta, categoria='host', regla=limpio(regla, 80), titulo=limpio(titulo),
                               cve=limpio(cve, 30), severidad=severidad, activo=activo,
                               huella=normalizar.huella(herramienta, str(regla), '', 0, '', 'host', activo or '-'))


def leer(ruta, que):
    """(bytes, motivo). bytes None si no se pudo leer o esta vacio."""
    if not ruta or not os.path.isfile(ruta):
        return None, 'no existe %s' % que
    try:
        with open(ruta, 'rb') as h:
            crudo = h.read()
    except OSError as e:
        return None, 'no se pudo leer %s: %s' % (que, type(e).__name__)
    if not crudo.strip():
        return None, '%s esta vacio' % que
    return crudo, ''


def cuenta(hall, umbral):
    tope = NIVELES.index(umbral)
    sobre = [h for h in hall if NIVELES.index(h['severidad']) >= tope]
    return sobre, len(hall) - len(sobre)


def de_ssh_audit(datos, activo, umbral):
    """(chequeo, hallazgos) de un reporte JSON de ssh-audit (auditoria comun o de politica)."""
    nombre = 'ssh-audit'
    if not isinstance(datos, dict):
        return (nombre, SIN_DATOS, 'no es un reporte JSON de ssh-audit'), []
    hall = []
    if 'passed' in datos and 'errors' in datos:
        if not isinstance(datos.get('passed'), bool):
            return (nombre, SIN_DATOS, 'el reporte de politica no dice si pasa'), []
        pol = limpio(datos.get('policy', ''), 80)
        for e in datos.get('errors') or []:
            if isinstance(e, dict):
                actual = ', '.join(limpio(x, 40) for x in (e.get('actual') or [])[:4]) if isinstance(e.get('actual'), list) else limpio(e.get('actual'), 60)
                hall.append(hallazgo(nombre, 'politica:%s' % e.get('mismatched_field', '?'),
                                     'no pasa la politica %s en %s (hoy: %s)' % (pol, e.get('mismatched_field', '?'), actual), 'ALTA', activo))
        for w in datos.get('warnings') or []:
            hall.append(hallazgo(nombre, 'politica:aviso', 'aviso de la politica %s: %s' % (pol, limpio(w, 80)), 'MEDIA', activo))
        if not datos['passed'] and not hall:
            hall.append(hallazgo(nombre, 'politica', 'no pasa la politica %s' % pol, 'ALTA', activo))
        sobre, debajo = cuenta(hall, umbral)
        if sobre or not datos['passed']:
            return (nombre, HALLAZGO, 'la politica %s no pasa: %d diferencia(s)' % (pol, len(hall))), hall
        return (nombre, OK, 'pasa la politica %s%s' % (pol, '; %d aviso(s)' % debajo if debajo else '')), hall
    if 'kex' not in datos and 'banner' not in datos:
        return (nombre, SIN_DATOS, 'no es un reporte JSON de ssh-audit'), []
    secciones = ('kex', 'key', 'mac', 'enc')
    for s in secciones:
        if any(not isinstance(x, dict) for x in datos.get(s) or []):
            return (nombre, SIN_DATOS, 'formato de ssh-audit anterior a 3.0: no trae las notas por algoritmo'), []
    if not datos.get('kex') or not datos.get('key'):
        return (nombre, SIN_DATOS, 'el reporte no trae algoritmos negociados: no llego a conectar'), []
    for s in secciones:
        for a in datos.get(s) or []:
            notas = a.get('notes') or {}
            for nivel, sev in (('fail', 'ALTA'), ('warn', 'MEDIA')):
                for n in notas.get(nivel) or []:
                    hall.append(hallazgo(nombre, '%s:%s' % (s, a.get('algorithm', '?')), '%s %s: %s' % (s, a.get('algorithm', '?'), n), sev, activo))
    for c in datos.get('cves') or []:
        if not isinstance(c, dict):
            continue
        try:
            p = float(c.get('cvssv2') or 0)
        except (TypeError, ValueError):
            p = 0.0
        sev = 'CRITICA' if p >= 9 else 'ALTA' if p >= 7 else 'MEDIA' if p >= 4 else 'BAJA'
        cid = str(c.get('name', ''))
        hall.append(hallazgo(nombre, cid, '%s: %s' % (cid, c.get('description', '')), sev, activo, cve=cid if cid.startswith('CVE-') else ''))
    sobre, debajo = cuenta(hall, umbral)
    if sobre:
        return (nombre, HALLAZGO, '%d en el umbral %s o por encima; %d por debajo' % (len(sobre), umbral, debajo)), hall
    return (nombre, OK, 'ninguno en el umbral %s o por encima; %d por debajo' % (umbral, debajo)), hall


def de_lynis(dat, log, activo, umbral, max_dias):
    """(chequeos, hallazgos, indice) de lynis-report.dat y lynis.log."""
    crudo, motivo = leer(dat, 'el reporte de Lynis')
    if crudo is None:
        return [('lynis', SIN_DATOS, motivo)], [], None
    valores, listas = {}, {}
    for linea in crudo.decode('utf-8', 'replace').replace('\r\n', '\n').split('\n'):
        if '=' not in linea or linea.startswith('#'):
            continue
        k, v = linea.split('=', 1)
        if k.endswith('[]'):
            listas.setdefault(k[:-2], []).append(v)
        else:
            valores[k] = v
    if 'lynis_version' not in valores and 'report_version_major' not in valores:
        return [('lynis', SIN_DATOS, 'no es un reporte de Lynis (lynis-report.dat)')], [], None
    if valores.get('finish') != 'true':
        return [('lynis', SIN_DATOS, 'el reporte esta cortado: Lynis no termino (falta finish=true)')], [], None
    hall = []
    for nivel, sev in (('warning', 'ALTA'), ('suggestion', 'BAJA')):
        for v in listas.get(nivel, []):
            partes = (v.split('|') + ['', '', ''])[:3]
            detalle = '' if partes[2].strip() in ('', '-') else ' (%s)' % partes[2]
            hall.append(hallazgo('lynis', partes[0] or '?', partes[1] + detalle, sev, activo))
    sobre, debajo = cuenta(hall, umbral)
    if sobre:
        chequeos = [('lynis', HALLAZGO, '%d advertencia(s) en el umbral %s o por encima; %d por debajo' % (len(sobre), umbral, debajo))]
    else:
        chequeos = [('lynis', OK, 'ninguna advertencia en el umbral %s o por encima; %d por debajo' % (umbral, debajo))]
    excepciones = listas.get('exception_event', [])
    if excepciones:
        chequeos.append(('lynis: excepciones', SIN_DATOS, '%d excepcion(es) interna(s): alguna prueba no termino bien (%s)' % (
            len(excepciones), ', '.join(limpio(e.split('|')[0], 20) for e in excepciones[:5]))))
    m = FECHA.match(valores.get('report_datetime_end', '').strip())
    if not m:
        chequeos.append(('lynis: fecha', SIN_DATOS, 'el reporte no trae su fecha (report_datetime_end)'))
    elif max_dias > 0:
        t = calendar.timegm(tuple(int(x) for x in m.groups()) + (0, 0, 0))
        dias = (time.time() - t) / 86400.0
        if dias > max_dias:
            chequeos.append(('lynis: fecha', SIN_DATOS, 'el reporte es de hace %d dias (tope %d dias): no dice como esta hoy' % (dias, max_dias)))
    if not log:
        chequeos.append(('lynis: privilegios', SIN_DATOS, 'sin --lynis-log no se sabe si corrio con privilegios (el reporte no lo dice)'))
    else:
        texto, motivo = leer(log, 'el log de Lynis')
        if texto is None:
            chequeos.append(('lynis: privilegios', SIN_DATOS, motivo))
        else:
            n = texto.decode('utf-8', 'replace').count(SIN_ROOT)
            if n:
                chequeos.append(('lynis: privilegios', SIN_DATOS, 'corrio sin privilegios: %d prueba(s) no se hicieron por falta de root' % n))
            else:
                chequeos.append(('lynis: privilegios', OK, 'ninguna prueba salteada por falta de root'))
    indice = valores.get('hardening_index', '')
    return chequeos, hall, (limpio(indice, 5) if indice.strip().isdigit() else None)


def instalada(nombre):
    return shutil.which(nombre)


def ejecutar(orden):
    """(codigo, salida, error). codigo None si no se pudo ejecutar o no termino."""
    try:
        r = subprocess.run(orden, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=TOPE_SEGUNDOS)
    except (OSError, subprocess.SubprocessError) as e:
        return None, '', type(e).__name__
    return r.returncode, r.stdout, r.stderr


def resolver(destino):
    """(host, puerto) del alias de SSH, leidos de la configuracion local con 'ssh -G' (no se conecta). ssh-audit
    no lee ~/.ssh/config: sin esto, el Destino del inventario no le dice nada."""
    host, puerto = destino, None
    if instalada('ssh'):
        rc, salida, _ = ejecutar(['ssh', '-G', destino])
        if rc == 0:
            for linea in salida.splitlines():
                partes = linea.strip().split(None, 1)
                if len(partes) == 2 and partes[0].lower() == 'hostname':
                    host = partes[1].strip()
                elif len(partes) == 2 and partes[0].lower() == 'port' and partes[1].strip().isdigit():
                    puerto = int(partes[1].strip())
    return host, puerto


def revisar_orden(orden):
    """La lista negra sobre la orden armada: ValueError si lleva algo prohibido."""
    malas = [o for o in orden[1:] if o.split('=')[0] in PROHIBIDAS]
    if malas:
        raise ValueError('opcion prohibida: %s' % ', '.join(malas))


def correr_ssh_audit(destino, alias, puerto, politica, raiz):
    """(datos, guardado, motivo). datos None si no hay reporte usable. El motivo nunca repite la direccion."""
    if not instalada('ssh-audit'):
        return None, '', 'ssh-audit no esta instalado en esta maquina'
    host, puerto_cfg = resolver(destino)
    if not HOST.match(host or ''):
        return None, '', 'la configuracion de SSH no da un nombre de servidor usable para %s' % alias
    orden = ['ssh-audit', '-j', '--skip-rate-test', '-p', str(puerto or puerto_cfg or 22)]
    if politica:
        orden += ['-P', politica]
    orden.append(host)
    revisar_orden(orden)
    rc, salida, _ = ejecutar(orden)
    if rc is None:
        return None, '', 'ssh-audit no se pudo ejecutar o no termino'
    try:
        datos = json.loads(salida) if salida.strip() else None
    except ValueError:
        datos = None
    if datos is None:
        return None, '', 'ssh-audit no devolvio un reporte JSON (salio con %s): no conecto o fallo' % rc
    carpeta = os.path.join(raiz, 'borrador', 'seguridad', '%s-%s' % (time.strftime('%Y%m%d'), saneado(alias)))
    os.makedirs(carpeta, exist_ok=True)
    guardado = os.path.join(carpeta, 'ssh-audit.json')
    with open(guardado, 'w', encoding='utf-8') as h:
        h.write(salida)
    return datos, guardado, ''


def informe(chequeos, hall, indice=None, guardado=''):
    """(informe, codigo). El estado de la categoria host y el veredicto los decide el paquete."""
    inf = normalizar.nuevo_informe(ORIGEN)
    inf['no_mira'] = list(NO_MIRA)
    inf['hallazgos'] = hall
    normalizar.poner_categoria(inf, 'host', sorted(set(c.split(':')[0] for c, e, _ in chequeos if e != SIN_DATOS)),
                               ['%s: %s' % (c, m) for c, e, m in chequeos if e == SIN_DATOS],
                               '; '.join('%s: %s' % (c, m) for c, e, m in chequeos if e == HALLAZGO))
    inf['chequeos'] = [{'chequeo': c, 'estado': NOMBRE[e], 'motivo': m} for c, e, m in chequeos]
    if indice is not None:
        inf['indice_lynis'] = indice
    if guardado:
        inf['crudo'] = guardado
    return inf, normalizar.cerrar(inf)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Auditoria de seguridad de un servidor (solo lectura).', allow_abbrev=False)
    ap.add_argument('--host', default='', help='alias del servidor en el inventario')
    ap.add_argument('--ssh-audit', default='', help='reporte JSON de ssh-audit -j')
    ap.add_argument('--lynis', default='', help='lynis-report.dat')
    ap.add_argument('--lynis-log', default='', help='lynis.log de la misma corrida (dice si salteo pruebas por falta de root)')
    ap.add_argument('--correr-ssh-audit', action='store_true')
    ap.add_argument('--puerto', type=int, default=0)
    ap.add_argument('--politica', default='')
    ap.add_argument('--umbral', default='ALTA', choices=UMBRALES)
    ap.add_argument('--max-dias', type=int, default=DIAS_LYNIS)
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a, sobrantes = ap.parse_known_args(argv)
    alias = a.host

    def frena(motivo):
        if a.json:
            inf = normalizar.nuevo_informe(ORIGEN)
            inf.update(veredicto=normalizar.FRENA, motivo=motivo, no_mira=list(NO_MIRA))
            print(normalizar.a_json(inf))
        else:
            print('AUDITORIA DEL SERVIDOR %s -- FRENA: %s' % (alias or '?', motivo))
        return HALLAZGO

    def sin_datos(motivo):
        if a.json:
            print(normalizar.a_json(informe([('entrada', SIN_DATOS, motivo)], [])[0]))
        else:
            print('AUDITORIA DEL SERVIDOR %s -- SIN DATOS: %s' % (alias or '?', motivo))
        return SIN_DATOS

    pedidas = [s for s in sobrantes if s.split('=')[0] in PROHIBIDAS]
    if pedidas:
        return frena('se pidio %s, que cambia algo o ataca: no se corre nunca, ni con un "si"' % ', '.join(limpio(p, 30) for p in pedidas))
    if sobrantes:
        return frena('opcion que este script no conoce (%s): no se pasa a ninguna herramienta' % ', '.join(limpio(s, 30) for s in sobrantes[:3]))
    if not alias:
        return sin_datos('falta --host <alias>: lo que se audita sale del inventario')
    ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
    estado, fila, motivo = inventario.autorizar(ruta, alias, 'N0') if ruta else (inventario.SIN_DATOS, None, motivo)
    if estado == inventario.OK and fila['tipo'] != 'servidor':
        estado, motivo = inventario.FRENA, '%s es de tipo %s: este script audita un activo de tipo servidor' % (alias, fila['tipo'] or '?')
    if estado == inventario.FRENA:
        return frena(motivo)
    if estado != inventario.OK:
        return sin_datos(motivo)
    if a.politica.startswith('-'):
        return frena('la politica no puede empezar con un guion: se leeria como una opcion de ssh-audit')
    if not (a.ssh_audit or a.lynis or a.correr_ssh_audit):
        return sin_datos('no hay ningun reporte (--ssh-audit, --lynis) ni se pidio --correr-ssh-audit')
    if a.ssh_audit and a.correr_ssh_audit:
        return sin_datos('--ssh-audit y --correr-ssh-audit juntos: se elige uno')

    chequeos, hall, indice, guardado = [], [], None, ''
    if a.correr_ssh_audit:
        if not DESTINO_SSH.match(fila['destino']):
            chequeos.append(('ssh-audit', SIN_DATOS, 'el Destino de %s en el inventario no es un alias de SSH usable' % alias))
        else:
            datos, guardado, motivo = correr_ssh_audit(fila['destino'], alias, a.puerto, a.politica, os.path.abspath(a.raiz))
            if datos is None:
                chequeos.append(('ssh-audit', SIN_DATOS, motivo))
            else:
                c, h = de_ssh_audit(datos, alias, a.umbral)
                chequeos.append(c)
                hall += h
    elif a.ssh_audit:
        crudo, motivo = leer(a.ssh_audit, 'el reporte de ssh-audit')
        try:
            datos = json.loads(crudo.decode('utf-8-sig')) if crudo is not None else None
        except (ValueError, UnicodeDecodeError):
            datos, motivo = None, 'el reporte de ssh-audit no es un JSON legible'
        if datos is None:
            chequeos.append(('ssh-audit', SIN_DATOS, motivo))
        else:
            c, h = de_ssh_audit(datos, alias, a.umbral)
            chequeos.append(c)
            hall += h
    if a.lynis:
        c, h, indice = de_lynis(a.lynis, a.lynis_log, alias, a.umbral, a.max_dias)
        chequeos += c
        hall += h

    inf, codigo = informe(chequeos, hall, indice, guardado)
    if a.json:
        print(normalizar.a_json(inf))
        return codigo
    print('AUDITORIA DEL SERVIDOR %s -- %s' % (alias, inf['veredicto']))
    tope = NIVELES.index(a.umbral)
    for c, e, m in chequeos:
        print('  %-20s %s -- %s' % (c, NOMBRE[e], m))
        for h in [x for x in hall if x['herramienta'] == c and NIVELES.index(x['severidad']) >= tope][:20]:
            print('    - %-7s %s%s' % (h['severidad'], (h['regla'] + ': ') if h['herramienta'] == 'lynis' else '', h['titulo']))
    if indice is not None:
        print('  Indice de endurecimiento de Lynis: %s (dato, sin veredicto: no es un nivel de cumplimiento)' % indice)
    if guardado:
        print('  Reporte crudo (no se versiona): %s' % guardado)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
