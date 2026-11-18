#!/usr/bin/env python3
"""Salud de un servidor, leida del reporte fijo del colector. SOLO LECTURA.

    python -I bin/salud-host.py --ssh web-prueba-1                (pasa por el inventario, nivel N0, y trae el reporte)
    python -I bin/salud-host.py --ssh web-prueba-1 --guardar      (ademas deja el reporte crudo en borrador/operacion/<fecha>/)
    python -I bin/salud-host.py --archivo <reporte>               (un reporte ya traido; no se conecta a nada)
    opciones: --disco 90  --inodos 90  --dias-reinicio 7  --horas-reporte 24  --tope 60
              --modulo <slug> | --inventario <ruta>  --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA: el alias no esta autorizado)   2 = SIN DATOS
Con un HALLAZGO y un chequeo sin datos a la vez sale 1, y la linea de ese chequeo dice SIN DATOS.

POR QUE EXISTE. "Como esta el servidor" lo contestaba el modelo leyendo salidas sueltas de df o de systemctl:
cada vez miraba distinto, se le pasaba un disco lleno entre veinte montajes y un comando que no habia corrido
quedaba como "sin problemas". Aca el servidor imprime siempre el mismo reporte (el colector, que instala una
persona: assets/colector-salud.sh de la skill operacion-de-servidores) y este script lo lee siempre igual.
HALLAZGO: disco o inodos al umbral o por encima, una unidad de systemd caida, un reinicio pendiente hace mas
dias que el umbral, el reloj sin sincronizar. SIN DATOS: no conecta, el colector no esta, el reporte no se
puede leer, esta cortado, le falta una seccion o es viejo; y cada chequeo que el colector no pudo medir.

QUE NO HACE. No manda ningun comando al servidor: ssh entra sin pedir nada y el reporte llega solo si la
identidad de lectura tiene el colector como comando forzado (la barrera vive en el servidor). No cambia nada
en el servidor, no acepta claves de servidor nuevas ni pide contrasenas. No juzga memoria, carga ni journal:
los muestra como dato. Lo unico que escribe, y solo con --guardar, es el reporte crudo en borrador/.
Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
NOMBRE = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMATO = 1
SECCIONES = ('sistema', 'disco', 'inodos', 'memoria', 'carga', 'servicios', 'reinicio', 'reloj', 'journal')
UMBRAL_DISCO, UMBRAL_INODOS, DIAS_REINICIO, HORAS_REPORTE = 90, 90, 7, 24
# Tipos que no son "disco que se llena" de este servidor: viven en memoria, nacen llenos (una imagen de solo
# lectura) o son de otra maquina (red). Se saltean antes de leer sus cifras: un montaje de red puede traerlas rotas.
IGNORADOS = ('tmpfs', 'devtmpfs', 'ramfs', 'rootfs', 'squashfs', 'fuse.snapfuse', 'iso9660', 'udf', 'efivarfs', 'overlay',
             'nfs', 'nfs4', 'cifs', 'smb3', 'smbfs', '9p', 'fuse.sshfs', 'ceph', 'glusterfs', 'drvfs')
ENCABEZADO = re.compile(r'^colector-salud formato=(\d+)$')
SECCION = re.compile(r'^\[([a-z_]+)\]$')
DESTINO_SSH = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
NO_MIRA = ('por que esta asi: la causa la busca el criterio, empezando por que cambio (operacion/cambios.md)',
           'memoria, carga y journal: los muestra como dato, sin umbral',
           'los montajes de red o virtuales (los saltea por tipo) y los que la identidad de lectura no puede ver',
           'si la aplicacion contesta: eso es su chequeo de salud, no el del servidor',
           'los logs, las alertas, los parches pendientes y los respaldos: todavia no los mide ningun script')


def limpio(texto, largo=120):
    """Lo que viene de un servidor es dato: a la pantalla va sin caracteres de control y acotado."""
    return ''.join(c if 32 <= ord(c) < 127 else '?' for c in str(texto))[:largo]


def leer_reporte(texto):
    """(secciones, motivo). secciones = {nombre: [lineas]}; None con el motivo si no es un reporte entero."""
    if not texto.strip():
        return None, 'el reporte esta vacio'
    lineas = [l.strip() for l in texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
    inicio = formato = None
    for i, l in enumerate(lineas):
        m = ENCABEZADO.match(l)
        if m:
            inicio, formato = i, int(m.group(1))
            break
    if inicio is None:
        return None, 'no es un reporte del colector: falta la linea "colector-salud formato=%d"' % FORMATO
    if formato != FORMATO:
        return None, 'el reporte es del formato %d y este script lee el formato %d' % (formato, FORMATO)
    secciones, actual, fin = {}, None, False
    for l in lineas[inicio + 1:]:
        m = SECCION.match(l)
        if m and m.group(1) == 'fin':
            fin = True
            break
        if m:
            actual = m.group(1)
            if actual in secciones:
                return None, 'la seccion [%s] figura dos veces: no se puede saber cual vale' % actual
            secciones[actual] = []
        elif actual is not None and l:
            secciones[actual].append(l)
    if not fin:
        return None, 'el reporte esta cortado: falta la marca [fin]'
    faltan = [s for s in SECCIONES if s not in secciones]
    if faltan:
        return None, 'al reporte le falta la seccion %s' % ', '.join('[%s]' % s for s in faltan)
    return secciones, ''


def pares(lineas):
    """{clave: valor} de las lineas clave=valor (gana la primera); las claves repetidas, en 'todas'."""
    uno, todas = {}, {}
    for l in lineas:
        if '=' in l:
            k, v = l.split('=', 1)
            uno.setdefault(k.strip(), v.strip())
            todas.setdefault(k.strip(), []).append(v.strip())
    return uno, todas


def chequeo(nombre, estado, detalle, hallazgos=None):
    return {'chequeo': nombre, 'estado': NOMBRE[estado], 'detalle': detalle, 'hallazgos': hallazgos or []}


def mirar_tabla(nombre, lineas, umbral, sin_cuenta_es_ok):
    """disco e inodos: filas tipo|total|usados|porcentaje|montaje."""
    sd = pares(lineas)[0].get('sin_dato')
    if sd is not None:
        return chequeo(nombre, SIN_DATOS, 'el colector no pudo medirlo: %s' % limpio(sd))
    if not lineas:
        return chequeo(nombre, SIN_DATOS, 'el colector no listo ningun sistema de archivos')
    filas, cuantos, salteados = [], 0, set()
    for l in lineas:
        p = l.split('|', 4)
        if len(p) == 5 and p[0] in IGNORADOS:
            cuantos, salteados = cuantos + 1, salteados | set([p[0]])
            continue
        pct = p[3].rstrip('%') if len(p) == 5 else ''
        if len(p) != 5 or not p[1].isdigit() or not p[2].isdigit() or not (pct == '-' or pct.isdigit()) or not p[4]:
            return chequeo(nombre, SIN_DATOS, 'una fila no se entiende: %s' % limpio(l, 80))
        filas.append((p[0], int(p[1]), None if pct == '-' else int(pct), limpio(p[4])))
    reales = filas
    contables = sorted((f for f in reales if f[2] is not None and f[1] > 0), key=lambda f: -f[2])
    nota = '; %d salteado(s) por tipo (%s)' % (cuantos, ', '.join(sorted(salteados))) if cuantos else ''
    if not contables:
        if reales and sin_cuenta_es_ok:
            return chequeo(nombre, OK, 'ningun sistema de archivos lleva cuenta propia de %s%s' % (nombre, nota))
        return chequeo(nombre, SIN_DATOS, 'no quedo ningun sistema de archivos contable%s' % nota)
    llenos = [f for f in contables if f[2] >= umbral]
    if llenos:
        return chequeo(nombre, HALLAZGO, '%s (umbral %d %%)%s' % ('; '.join('%s al %d %%' % (f[3], f[2]) for f in llenos), umbral, nota),
                       [{'montaje': f[3], 'uso_pct': f[2], 'tipo': limpio(f[0], 20)} for f in llenos])
    return chequeo(nombre, OK, 'el mas lleno: %s al %d %% (umbral %d %%)%s' % (contables[0][3], contables[0][2], umbral, nota))


def mirar_servicios(lineas):
    uno, todas = pares(lineas)
    if 'sin_dato' in uno:
        return chequeo('servicios', SIN_DATOS, 'el colector no pudo medirlo: %s' % limpio(uno['sin_dato']))
    caidas = [limpio(u, 80) for u in todas.get('caida', [])]
    if not uno.get('caidas', '').isdigit():
        return chequeo('servicios', SIN_DATOS, 'falta la cuenta de unidades caidas: no se sabe si la lista corrio')
    if int(uno['caidas']) != len(caidas):
        return chequeo('servicios', SIN_DATOS, 'la cuenta dice %s unidades caidas y la lista trae %d: salida cortada' % (uno['caidas'], len(caidas)))
    estado = limpio(uno.get('estado', 'sin informar'), 30)
    if caidas:
        return chequeo('servicios', HALLAZGO, '%d unidad(es) caida(s): %s%s (estado del sistema: %s)' % (
            len(caidas), ', '.join(caidas[:10]), ' y %d mas' % (len(caidas) - 10) if len(caidas) > 10 else '', estado),
            [{'unidad': u} for u in caidas])
    return chequeo('servicios', OK, 'ninguna unidad caida (estado del sistema: %s)' % estado)


def mirar_reinicio(lineas, fecha, dias_max):
    uno = pares(lineas)[0]
    if 'sin_dato' in uno:
        return chequeo('reinicio', SIN_DATOS, 'el colector no pudo medirlo: %s' % limpio(uno['sin_dato']))
    pendiente, metodo = uno.get('pendiente', ''), limpio(uno.get('metodo', 'sin informar'), 30)
    if pendiente == 'no':
        return chequeo('reinicio', OK, 'no hay reinicio pendiente (metodo: %s)' % metodo)
    if pendiente != 'si':
        return chequeo('reinicio', SIN_DATOS, 'el colector no pudo saber si hay un reinicio pendiente (metodo: %s)' % metodo)
    if not uno.get('desde_epoch', '').isdigit():
        return chequeo('reinicio', SIN_DATOS, 'hay un reinicio pendiente pero no se sabe desde cuando (metodo: %s): '
                       'no se puede comparar con el umbral de %d dias' % (metodo, dias_max))
    dias = max(0.0, (fecha - int(uno['desde_epoch'])) / 86400.0)
    if dias > dias_max:
        return chequeo('reinicio', HALLAZGO, 'reinicio pendiente hace %d dias (umbral %d)' % (int(dias), dias_max), [{'dias': int(dias)}])
    return chequeo('reinicio', OK, 'reinicio pendiente hace %d dia(s), dentro del margen de %d' % (int(dias), dias_max))


def mirar_reloj(lineas):
    uno = pares(lineas)[0]
    if 'sin_dato' in uno:
        return chequeo('reloj', SIN_DATOS, 'el colector no pudo medirlo: %s' % limpio(uno['sin_dato']))
    if uno.get('sincronizado') == 'si':
        return chequeo('reloj', OK, 'sincronizado')
    if uno.get('sincronizado') == 'no':
        return chequeo('reloj', HALLAZGO, 'el reloj no esta sincronizado', [{'sincronizado': False}])
    return chequeo('reloj', SIN_DATOS, 'el colector no pudo saber si el reloj esta sincronizado')


def datos_de(secciones, fecha):
    """Lo que se muestra sin veredicto: (nombre, texto) por linea."""
    def numero(d, k):
        return int(d[k]) if d.get(k, '').isdigit() else None

    def o_sin_dato(d, texto):
        return 'sin dato (%s)' % limpio(d['sin_dato'], 60) if 'sin_dato' in d else texto or 'sin dato'

    mem, carga, jou, sis = [pares(secciones[s])[0] for s in ('memoria', 'carga', 'journal', 'sistema')]
    total, disp, st, sl = [numero(mem, k) for k in ('total_kb', 'disponible_kb', 'swap_total_kb', 'swap_libre_kb')]
    t_mem = ''
    if total and disp is not None:
        t_mem = 'disponible %d %% de %.1f GB' % (round(100.0 * disp / total), total / 1048576.0)
        if st and sl is not None:
            t_mem += '; swap en uso %d %% de %.1f GB' % (round(100.0 * (st - sl) / st), st / 1048576.0)
    t_carga = ' / '.join(limpio(carga[k], 10) for k in ('uno', 'cinco', 'quince') if k in carga)
    if t_carga and sis.get('cpus', '').isdigit():
        t_carga += ' con %s CPU' % sis['cpus']
    t_sis = ', '.join(x for x in (limpio(sis.get('so', ''), 40), 'nucleo %s' % limpio(sis['nucleo'], 40) if sis.get('nucleo') else '') if x)
    if sis.get('arranque_epoch', '').isdigit():
        t_sis += '%sencendido hace %d dia(s)' % (', ' if t_sis else '', max(0, (fecha - int(sis['arranque_epoch'])) // 86400))
    return [('memoria', o_sin_dato(mem, t_mem)), ('carga', o_sin_dato(carga, t_carga)),
            ('journal', o_sin_dato(jou, limpio(jou.get('uso', ''), 20))), ('sistema', t_sis or 'sin dato')]


def orden_ssh(destino, tope):
    """La orden exacta. No lleva comando remoto: el reporte lo imprime el comando forzado de la identidad de
    lectura. Sin terminal, sin preguntar nada (ni contrasena ni clave de servidor nueva)."""
    return ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'ConnectTimeout=%d' % max(1, min(tope, 15)), '--', destino]


def motivo_ssh(codigo, error):
    """Por que fallo, sin repetir lo que ssh imprime (trae el nombre real o la direccion del servidor)."""
    e = (error or '').lower()
    if 'permission denied' in e:
        return 'el servidor rechazo la identidad (clave o certificado)'
    if 'host key verification failed' in e:
        return 'la clave del servidor no esta verificada en esta maquina: la primera conexion la hace una persona'
    if 'could not resolve hostname' in e:
        return 'el alias no resuelve: falta en la configuracion de SSH de esta maquina'
    if 'timed out' in e or 'connection refused' in e or 'no route to host' in e or 'network is unreachable' in e:
        return 'no se pudo conectar (el servidor no contesta en ese puerto)'
    if codigo == 127 or 'not found' in e:
        return 'el colector no esta instalado donde lo busca el comando forzado'
    if codigo == 255:
        return 'ssh no pudo conectar o autenticar'
    return 'el colector termino con el codigo %s' % codigo


def traer_por_ssh(destino, tope):
    """(codigo, salida, motivo). codigo None = ssh no llego a correr o no termino a tiempo."""
    try:
        r = subprocess.run(orden_ssh(destino, tope), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=tope)
    except FileNotFoundError:
        return None, '', 'no hay ssh en esta maquina'
    except subprocess.TimeoutExpired:
        return None, '', 'el servidor no termino de contestar en %d segundos' % tope
    return r.returncode, r.stdout, '' if r.returncode == 0 else motivo_ssh(r.returncode, r.stderr)


def guardar(raiz, alias, texto):
    ahora = time.gmtime()
    carpeta = os.path.join(raiz, 'borrador', 'operacion', time.strftime('%Y-%m-%d', ahora))
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, 'salud-%s-%s.txt' % (re.sub(r'[^A-Za-z0-9._-]', '_', alias), time.strftime('%H%M%S', ahora)))
    with open(ruta, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)
    return os.path.relpath(ruta, raiz).replace(os.sep, '/')


def hace(segundos):
    s = max(0, int(segundos))
    return '%d min' % (s // 60) if s < 7200 else '%d h' % (s // 3600) if s < 172800 else '%d dias' % (s // 86400)


def fuera(codigo, motivo, a_json, alias=''):
    """Una salida sin reporte: SIN DATOS, o FRENA cuando el inventario no autoriza."""
    estado = 'FRENA' if codigo == HALLAZGO else 'SIN DATOS'
    if a_json:
        print(json.dumps({'estado': estado, 'alias': alias, 'motivo': motivo, 'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
    elif codigo == HALLAZGO:
        print('GATE de SERVIDOR -- FRENA: %s, nivel N0' % alias)
        print('  FRENA: %s' % motivo)
        print('  No se conecto a nada. Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    else:
        print('SIN DATOS -- %s' % motivo)
    return codigo


def main(argv=None):
    ap = argparse.ArgumentParser(description='Salud de un servidor, leida del reporte del colector (solo lectura).')
    ap.add_argument('--ssh', default='', metavar='ALIAS', help='alias del inventario; trae el reporte por ssh, sin mandar comandos')
    ap.add_argument('--archivo', default='', help='un reporte del colector ya traido')
    ap.add_argument('--disco', type=int, default=UMBRAL_DISCO, help='porcentaje de uso de disco desde el que es HALLAZGO (por defecto %d)' % UMBRAL_DISCO)
    ap.add_argument('--inodos', type=int, default=UMBRAL_INODOS, help='porcentaje de inodos desde el que es HALLAZGO (por defecto %d)' % UMBRAL_INODOS)
    ap.add_argument('--dias-reinicio', type=int, default=DIAS_REINICIO, help='dias de reinicio pendiente que se toleran (por defecto %d)' % DIAS_REINICIO)
    ap.add_argument('--horas-reporte', type=int, default=HORAS_REPORTE, help='con --archivo, horas desde las que el reporte es viejo (por defecto %d; 0 = no mirar)' % HORAS_REPORTE)
    ap.add_argument('--tope', type=int, default=60, help='segundos que se espera a ssh (por defecto 60)')
    ap.add_argument('--guardar', action='store_true', help='con --ssh, deja el reporte crudo en borrador/operacion/<fecha>/')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    raiz = os.path.abspath(a.raiz)

    if bool(a.ssh) == bool(a.archivo):
        return fuera(SIN_DATOS, 'va --ssh <alias> o --archivo <reporte>: uno de los dos', a.json)
    if a.archivo:
        etiqueta, origen = limpio(os.path.basename(a.archivo), 80), 'archivo'
        try:
            with open(a.archivo, 'rb') as h:
                texto = h.read().decode('utf-8', errors='replace')
        except OSError as e:
            return fuera(SIN_DATOS, 'no se pudo leer el reporte %s: %s' % (a.archivo, e.strerror or e), a.json)
    else:
        ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(raiz, a.modulo)
        if not ruta:
            return fuera(SIN_DATOS, '%s. Sin inventario nada esta autorizado: no se conecto a nada' % motivo, a.json, a.ssh)
        estado, activo, motivo = inventario.autorizar(ruta, a.ssh, 'N0')
        if estado == inventario.SIN_DATOS:
            return fuera(SIN_DATOS, '%s: no se conecto a nada' % motivo, a.json, a.ssh)
        if estado == inventario.FRENA:
            return fuera(HALLAZGO, motivo, a.json, a.ssh)
        if activo['tipo'] != 'servidor':
            return fuera(HALLAZGO, '%s es de tipo %s: el colector corre en un servidor' % (a.ssh, activo['tipo'] or '?'), a.json, a.ssh)
        if not DESTINO_SSH.match(activo['destino']):
            return fuera(SIN_DATOS, 'el Destino de %s en el inventario no es un alias de la configuracion de SSH (un nombre solo: '
                         'sin usuario, sin espacios, sin opciones): no se conecto a nada' % a.ssh, a.json, a.ssh)
        codigo, texto, motivo = traer_por_ssh(activo['destino'], a.tope)
        if codigo != 0:
            return fuera(SIN_DATOS, 'no se pudo traer el reporte de %s: %s' % (a.ssh, motivo or 'ssh salio con %s' % codigo), a.json, a.ssh)
        etiqueta, origen = a.ssh, 'ssh'

    secciones, motivo = leer_reporte(texto)
    if secciones is None:
        if origen == 'ssh':
            motivo += '. Si ssh entro y no imprimio el reporte, a la identidad de lectura le falta el comando forzado'
        return fuera(SIN_DATOS, 'lo que llego de %s no sirve: %s' % (etiqueta, motivo), a.json, a.ssh)
    sistema = pares(secciones['sistema'])[0]
    if not sistema.get('fecha_epoch', '').isdigit():
        return fuera(SIN_DATOS, 'el reporte de %s no trae su fecha: no se puede saber de cuando es' % etiqueta, a.json, a.ssh)
    fecha = int(sistema['fecha_epoch'])
    edad = int(time.time()) - fecha
    if origen == 'archivo' and a.horas_reporte > 0 and edad > a.horas_reporte * 3600:
        return fuera(SIN_DATOS, 'el reporte %s es de hace %s: no dice como esta el servidor hoy (para leerlo igual, --horas-reporte 0)' % (
            etiqueta, hace(edad)), a.json)

    chequeos = [mirar_tabla('disco', secciones['disco'], a.disco, False), mirar_tabla('inodos', secciones['inodos'], a.inodos, True),
                mirar_servicios(secciones['servicios']), mirar_reinicio(secciones['reinicio'], fecha, a.dias_reinicio),
                mirar_reloj(secciones['reloj'])]
    estados = [c['estado'] for c in chequeos]
    codigo = HALLAZGO if 'HALLAZGO' in estados else SIN_DATOS if 'SIN DATOS' in estados else OK
    datos = datos_de(secciones, fecha)
    guardado = guardar(raiz, a.ssh, texto) if a.guardar and origen == 'ssh' else ''
    umbrales = {'disco': a.disco, 'inodos': a.inodos, 'dias_reinicio': a.dias_reinicio}
    if a.json:
        print(json.dumps({'estado': NOMBRE[codigo], 'servidor': etiqueta, 'origen': origen, 'reporte_epoch': fecha,
                          'edad_segundos': edad, 'chequeos': chequeos, 'datos': dict(datos), 'umbrales': umbrales,
                          'guardado': guardado, 'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        return codigo
    print('SALUD de %s -- %s   (reporte de hace %s)' % (etiqueta, NOMBRE[codigo], hace(edad)))
    for c in chequeos:
        print('  %-10s %-10s %s' % (c['chequeo'], c['estado'], c['detalle']))
    print('  Datos sin veredicto (los mira el criterio):')
    for nombre, valor in datos:
        print('    %-9s %s' % (nombre, valor))
    print('  Umbrales: disco %d %%, inodos %d %%, reinicio pendiente %d dias (por defecto 90, 90 y 7; los fija DEC-008).' % (
        a.disco, a.inodos, a.dias_reinicio))
    if guardado:
        print('  Reporte crudo guardado en %s' % guardado)
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
