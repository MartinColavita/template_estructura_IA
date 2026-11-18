#!/usr/bin/env python3
"""Prueba dinamica contra una aplicacion que corre (DAST), detras del GATE de PRUEBA ACTIVA. Normaliza al esquema comun.
No cambia nada en el repositorio ni en el inventario: escribe solo lo crudo y el informe en borrador/seguridad/<fecha>/.

    python -I bin/escanear-ambiente.py --alias <alias> --imagen <zap@sha256:...>   (pasiva: ZAP baseline, arana + pasivo)
    python -I bin/escanear-ambiente.py --alias <alias> --activo           (activa: ZAP full scan; manda pedidos de ataque)
    python -I bin/escanear-ambiente.py --alias <alias> --reporte <zap.json | nuclei.jsonl | .sarif>   (normaliza uno ya hecho)
    opciones: --modulo <slug> | --inventario <ruta>   --minutos <n> (arana; 1 por defecto)
              --imagen <ref de ZAP por digest: ...@sha256:<64 hex>; sin ella, o con una etiqueta, SIN DATOS>
              --linea-base <informe.json>   --salida <dir>   --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA: el inventario no lo autoriza)   2 = SIN DATOS

LA BARRERA (AGENTS.md, GATE de PRUEBA ACTIVA), en datos duros y antes de todo:
  - Primero inventario.autorizar_prueba(alias, 'pasivo' | 'activo'). Sin OK no corre nada ni lee ningun reporte:
    FRENA (no esta, no es una URL, pide mas de lo autorizado, activa contra produccion) o SIN DATOS (sin inventario).
  - La URL es la EXACTA de la columna Destino del inventario. No hay --url: una URL que llega por argumento no se usa.
  - Pasiva por defecto. --activo es explicito, y el "si" de la persona en su propio turno, nombrando la URL, lo pide
    la skill antes de correrlo: este script no lo puede ver.
  - Lo que la herramienta haya pedido fuera del origen autorizado no se cuenta como de la aplicacion y deja la
    categoria en HALLAZGO: la configuracion se revisa antes de volver a correr.
  - Con --reporte, dast acepta solo una prueba dinamica: ZAP, Nuclei, o un SARIF de una de ellas con sus URIs en
    el alcance. Un SARIF de analisis estatico (Semgrep, CodeQL...) es SIN DATOS: no es una prueba contra la URL.
  - ZAP corre con --name zap-<marca>; si pasa el tope de tiempo, se lo frena con docker kill sobre ese nombre.

POR QUE EXISTE. Mandar pedidos a una aplicacion que corre es tocar algo vivo. Que la URL sea la autorizada, que el
modo no pase de lo permitido y que nunca sea activa contra produccion no puede depender de que el modelo lea bien una
tabla: lo decide el mismo lector del inventario que usan los demas scripts (bin/operacion/inventario.py).

QUE NO HACE. No baja la imagen de ZAP (docker run --pull never: si no esta en la maquina, SIN DATOS), no le pasa
opciones arbitrarias (-z, -u, --hook), no se autentica, no corre Nuclei (sus reportes si se leen). No copia la query,
el pedido, la respuesta, el ataque ni la evidencia: solo regla, direccion y huella. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario autorizado
from seguridad import normalizar  # noqa: E402  el lector unico de reportes y el esquema comun

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
FRENA = 1
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGEN = ''                                       # DEC-009: por digest (@sha256:...); no hay etiqueta por defecto
DIGEST = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/:-]*@sha256:[0-9a-f]{64}$')
TOPE = 3600
VENCIO = 'vencio'
NUNCA = ('-z', '-u', '--hook', '--auto', '-g')
NO_MIRA = ('la logica de negocio y la autorizacion por objeto con datos reales: eso es prueba manual o de aceptacion',
           'una prueba autenticada (con un usuario de prueba): fase 2',
           'si un hallazgo es explotable: lo contesta otro agente con contexto limpio',
           'el codigo, las dependencias y los secretos del repositorio: escanear-seguridad.py',
           'el servidor y sus imagenes: auditar-host.py y escanear-imagenes.py',
           'si el "si" de la persona para una prueba activa existio: eso lo pide la skill, en su propio turno')


def ejecutar(cmd, tope=TOPE):
    """El codigo de salida; None si no se pudo ejecutar; VENCIO si paso el tope."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=tope)
        return r.returncode
    except subprocess.TimeoutExpired:
        return VENCIO
    except OSError:
        return None


def gate(estado, a, modo, motivo):
    """El inventario no autorizo (FRENA) o no se pudo saber (SIN DATOS): no se corrio nada."""
    inf = normalizar.nuevo_informe('escanear-ambiente')
    inf['veredicto'] = estado
    inf['motivo'] = motivo
    inf['no_mira'] = list(NO_MIRA)
    if a.json:
        print(normalizar.a_json(inf))
    else:
        print('GATE de PRUEBA ACTIVA -- %s: %s, prueba %s' % (estado, a.alias or '(sin alias)', modo))
        print('  %s' % motivo)
        print('  No se corrio nada ni se leyo ningun reporte.')
        print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return FRENA if estado == normalizar.FRENA else SIN_DATOS


def correr_zap(url, modo, a, salida, alcance):
    """(resultado de normalizar.leer, '') o (None, motivo de SIN DATOS)."""
    if not DIGEST.match(a.imagen or ''):
        return None, ('la imagen de ZAP va por digest (DEC-009): --imagen ghcr.io/zaproxy/zaproxy@sha256:<digest>; '
                      '%s' % ('no se paso --imagen' if not a.imagen else 'se paso %s, sin @sha256:' % a.imagen[:80]))
    docker = shutil.which('docker')
    if not docker:
        return None, 'docker no esta instalado: ZAP corre en su imagen de contenedor (DEC-009)'
    if ejecutar([docker, 'image', 'inspect', a.imagen]) != 0:
        return None, ('la imagen %s no esta en la maquina: la baja una persona, fijada por digest (DEC-009); '
                      'este script nunca baja nada' % a.imagen)
    os.makedirs(salida, exist_ok=True)
    marca = '%s-%s' % (re.sub(r'[^A-Za-z0-9_.-]', '_', a.alias), time.strftime('%Y%m%d%H%M%S'))
    nombre = '%s-zap-%s.json' % (time.strftime('%H%M%S'), re.sub(r'[^A-Za-z0-9_.-]', '_', a.alias))
    contenedor = 'zap-' + marca
    cmd = ['docker', 'run', '--rm', '--pull', 'never', '--name', contenedor, '-v', '%s:/zap/wrk/:rw' % salida, a.imagen,
           'zap-full-scan.py' if modo == 'activo' else 'zap-baseline.py', '-t', url, '-J', nombre, '-m', str(a.minutos)]
    prohibidas = [t for t in cmd if t in NUNCA]
    if prohibidas:
        raise ValueError('el comando de ZAP lleva una opcion prohibida: %s' % ', '.join(prohibidas))
    rc = ejecutar([docker] + cmd[1:])
    if rc == VENCIO:
        frenado = ejecutar([docker, 'kill', contenedor], 120)
        return None, ('ZAP paso el tope de %d minutos: %s el contenedor %s' % (
            TOPE // 60, 'se freno' if frenado == 0 else 'NO se pudo frenar (frenalo a mano con docker kill)', contenedor))
    if rc is None or rc not in (0, 1, 2):
        return None, 'ZAP salio con %s: no termino bien (3 = otra falla)' % rc
    reporte = os.path.join(salida, nombre)
    if not os.path.isfile(reporte):
        return None, 'ZAP no dejo su reporte'
    return normalizar.leer(reporte, 'dast', '', alcance), ''


def solo_dinamica(r, nombre):
    """'' si el reporte es de una prueba dinamica (ZAP, Nuclei, o un SARIF de una de ellas); si no, el motivo."""
    if r['cubre'] == ['dast']:
        return ''
    return ('%s es de %s (%s), no de una prueba dinamica contra la URL: dast acepta ZAP o Nuclei, o un SARIF de una '
            'de ellas con sus URIs en el alcance' % (nombre, r['herramienta'] or 'una herramienta desconocida',
                                                     ', '.join(r['cubre']) or 'sin categoria'))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Prueba dinamica contra una URL del inventario autorizado (GATE de PRUEBA ACTIVA).', allow_abbrev=False)
    ap.add_argument('--alias', default='')
    ap.add_argument('--activo', action='store_true', help='prueba activa: manda pedidos de ataque (pide un "si" en su propio turno)')
    ap.add_argument('--reporte', default='', help='un reporte ya generado (ZAP -J, Nuclei JSONL o SARIF), en vez de correr ZAP')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--minutos', type=int, default=1)
    ap.add_argument('--imagen', default=IMAGEN)
    ap.add_argument('--linea-base', default='')
    ap.add_argument('--salida', default='')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    modo = 'activo' if a.activo else 'pasivo'
    if not a.alias:
        return gate(normalizar.SIN_DATOS, a, modo, 'falta --alias <alias>: la URL sale del inventario, nunca de un argumento')
    ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
    if not ruta:
        return gate(normalizar.SIN_DATOS, a, modo, '%s. Sin inventario, nada esta autorizado' % motivo)
    estado, activo, motivo = inventario.autorizar_prueba(ruta, a.alias, modo)
    if estado != inventario.OK:
        return gate(normalizar.FRENA if estado == inventario.FRENA else normalizar.SIN_DATOS, a, modo, motivo)
    if a.minutos < 1:
        return gate(normalizar.SIN_DATOS, a, modo, '--minutos tiene que ser 1 o mas')
    url = activo['destino']
    alcance = normalizar.origen(url)
    huellas = None
    if a.linea_base:
        huellas, error = normalizar.cargar_linea_base(a.linea_base)
        if huellas is None:
            return gate(normalizar.SIN_DATOS, a, modo, error)

    inf = normalizar.nuevo_informe('escanear-ambiente')
    inf['no_mira'] = list(NO_MIRA)
    herramientas, faltan, fuera, salida = [], [], [], ''
    if a.reporte:
        r = normalizar.leer(a.reporte, '', '', alcance)
        if not r['error']:
            motivo = solo_dinamica(r, os.path.basename(a.reporte))
            if motivo:
                r = None
                faltan.append(motivo)
        elif r['error'].startswith('no se sabe de que categoria'):
            r['error'] = solo_dinamica(dict(r, cubre=[]), os.path.basename(a.reporte))
    else:
        salida = os.path.abspath(a.salida) if a.salida else os.path.join(RAIZ, 'borrador', 'seguridad', time.strftime('%Y-%m-%d'))
        r, motivo = correr_zap(url, modo, a, salida, alcance)
        if r is None:
            faltan.append(motivo)
    if r is not None:
        if r['error']:
            faltan.append(r['error'])
        else:
            for h in r['hallazgos']:
                h['activo'], h['categoria'] = a.alias, 'dast'
            inf['hallazgos'] = r['hallazgos']
            fuera = sorted(set(r['fuera']))
            if 'dast' in r['evidencia'] or r['hallazgos']:
                herramientas.append(r['herramienta'])
            else:
                faltan.append('%s: el reporte no muestra que haya llegado a %s (regla del cero)' % (r['herramienta'] or 'la herramienta', url))
    extra = ''
    if fuera:
        extra = ('la herramienta salio del alcance autorizado (%s): pidio %d direccion(es) de otro origen (%s); lo de '
                 'afuera no se cuenta como de la aplicacion y la configuracion se revisa antes de volver a correr'
                 % (alcance, len(fuera), ', '.join(fuera[:3])))
    if huellas:
        normalizar.aplicar_linea_base(inf['hallazgos'], huellas)
    normalizar.poner_categoria(inf, 'dast', herramientas, faltan, extra)
    codigo = normalizar.cerrar(inf)
    pie = ['Prueba %s contra %s (%s, ambiente %s).' % (modo, url, a.alias, activo['ambiente'] or '?')]
    if salida and os.path.isdir(salida):
        with open(os.path.join(salida, '%s-informe.json' % time.strftime('%H%M%S')), 'w', encoding='utf-8') as h:
            h.write(normalizar.a_json(inf))
        pie.append('Crudo e informe normalizado (locales, nunca se versionan): %s' % salida)
    if a.json:
        print(normalizar.a_json(inf))
    else:
        print('\n'.join(normalizar.lineas_texto(inf, 'ESCANEAR AMBIENTE', pie)))
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
