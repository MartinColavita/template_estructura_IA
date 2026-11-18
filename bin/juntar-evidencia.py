#!/usr/bin/env python3
"""Evidencia de un incidente de seguridad: copia sin modificar, con SHA-256 y manifiesto de custodia, FUERA del
repositorio. Con --verificar es SOLO LECTURA.

    python -I bin/juntar-evidencia.py --incidente INC-001 --destino <carpeta fuera del repo> --pedido-por "<rol>"
                                      --fuente <archivo> [--fuente <archivo> ...]
    python -I bin/juntar-evidencia.py --verificar <carpeta de la evidencia> --hash-manifiesto <sha256>
    opciones: --json   (--raiz <repo> es solo para las pruebas: cambia cual es "el repositorio del Cerebro")

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA)   2 = SIN DATOS
Juntar: FRENA si el destino cae adentro del repositorio del Cerebro o de CUALQUIER repositorio git (una carpeta
del camino con .git, carpeta o archivo de un worktree): no copia nada. SIN DATOS si falta un dato de la custodia
o una fuente no se pudo leer (las demas se copian igual y queda anotado). Verificar: HALLAZGO si un hash no
coincide, falta un archivo o cambio el manifiesto; SIN DATOS si no hay manifiesto, no se puede leer, o falta
--hash-manifiesto (sin el ancla anotada en el incidente no se puede decir que el manifiesto no cambio).
En Windows exige Python 3.8 o mas: el realpath de 3.7 no resuelve junctions ni enlaces, y un destino "afuera"
podria caer adentro de un repositorio.

POR QUE EXISTE. En un incidente, lo que se junta tiene que poder probarse despues: que es la copia exacta de lo
que habia, de donde salio, cuando y quien lo pidio. Copiar a mano no deja nada de eso, y un registro copiado
adentro del repositorio termina versionado (un mapa para un atacante, o datos de personas). Este script copia
byte a byte, calcula el SHA-256 de cada archivo, vuelve a leer la copia para confirmar que quedo igual, la deja
de solo lectura y escribe el manifiesto de custodia. El hash del manifiesto va al documento del incidente:
con --verificar se recalcula todo contra ese ancla.

QUE NO HACE. No junta la memoria ni el disco de un equipo comprometido, ni corre nada en el: eso lo hace una
persona con herramientas de confianza, del mas volatil al menos volatil (RFC 3227). Se le pasan archivos que
ya salieron de ahi (registros centrales, exportaciones de auditoria, alertas, salidas de comandos de solo
lectura). No lee ni muestra el contenido de lo que copia. No borra, no mueve y no cambia el origen (leerlo
puede cambiar su fecha de acceso: por eso no se corre en el equipo comprometido). No baja nada.
Solo biblioteca estandar. ASCII puro.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
NOMBRE = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFIESTO = 'manifiesto-custodia.json'
FORMATO = 'juntar-evidencia/1'
INCIDENTE = re.compile(r'^INC-\d{3,}$')
BLOQUE = 1024 * 1024
CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f]')
NO_MIRA = ('la memoria y el disco del equipo comprometido: los junta una persona con herramientas de confianza, del mas volatil al menos volatil (RFC 3227)',
           'el contenido de los archivos: no lo lee ni lo muestra (puede traer datos de personas o secretos)',
           'si lo juntado alcanza para entender el incidente: lo decide quien lo investiga',
           'la fecha de acceso del origen: leerlo puede cambiarla, por eso se junta lo que ya salio del equipo comprometido',
           'quien tuvo la evidencia despues: cada traspaso lo anota una persona en el documento del incidente')


def limpio(texto, largo=200):
    t = CONTROL.sub('', str(texto if texto is not None else ''))
    return t if len(t) <= largo else t[:largo - 3] + '...'


def utc(t=None):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))


def hash_de(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(BLOQUE), b''):
            h.update(bloque)
    return h.hexdigest()


def python_apto(version=None, sistema=None):
    """'' si este Python resuelve bien las rutas; si no, el motivo. En Windows, realpath resuelve junctions y
    enlaces recien desde 3.8: con 3.7 un destino "afuera" podria caer adentro de un repositorio."""
    version = tuple(version or sys.version_info)[:2]
    if (sistema or os.name) == 'nt' and version < (3, 8):
        return ('en Windows este script necesita Python 3.8 o mas: con %d.%d, realpath no resuelve junctions ni enlaces '
                'y no se puede asegurar que el destino quede fuera de un repositorio' % version)
    return ''


def repo_git(ruta):
    """La carpeta del repositorio git que contiene a ruta (un ancestro con .git, carpeta o archivo), o ''."""
    actual = os.path.realpath(os.path.abspath(ruta))
    while True:
        if os.path.exists(os.path.join(actual, '.git')):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:
            return ''
        actual = padre


def adentro(ruta, raiz):
    """True si ruta cae adentro de raiz (resolviendo .., enlaces y mayusculas de Windows)."""
    r = os.path.normcase(os.path.realpath(os.path.abspath(ruta)))
    b = os.path.normcase(os.path.realpath(os.path.abspath(raiz)))
    try:
        return os.path.commonpath([r, b]) == b
    except ValueError:                          # otra unidad de disco: afuera
        return False


def copiar(origen, destino):
    """(item, aviso_sin_datos). Copia en bloques, con el hash de lo leido; relee la copia y el origen."""
    nombre = os.path.basename(destino)
    st = os.stat(origen)
    h = hashlib.sha256()
    with open(origen, 'rb') as f, open(destino, 'xb') as g:
        for bloque in iter(lambda: f.read(BLOQUE), b''):
            h.update(bloque)
            g.write(bloque)
    leido = h.hexdigest()
    os.chmod(destino, stat.S_IREAD)
    item = {'archivo': nombre, 'origen': os.path.abspath(origen), 'bytes': st.st_size, 'sha256': leido,
            'modificado_origen': utc(st.st_mtime), 'copiado': utc(), 'aviso': ''}
    if hash_de(destino) != leido:
        return item, '%s: la copia no quedo igual a lo leido (falla del disco de destino)' % nombre
    if hash_de(origen) != leido:
        item['aviso'] = 'el origen siguio cambiando mientras se copiaba (archivo vivo): la copia es la foto de ese momento'
    if st.st_size == 0:
        return item, '%s: el archivo esta vacio; se copio igual (puede ser evidencia de un borrado), pero no se puede decir que este todo' % nombre
    return item, ''


def juntar(a):
    """(estado, salida)."""
    falta = [que for que, valor in (('--fuente', a.fuente), ('--destino', a.destino), ('--pedido-por', a.pedido_por.strip()))
             if not valor]
    if falta:
        return SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': 'falta %s: sin eso no hay cadena de custodia' % ', '.join(falta)}
    if not INCIDENTE.match(a.incidente):
        return SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': 'el incidente va como INC-nnn (el codigo del documento del incidente)'}
    if adentro(a.destino, a.raiz):
        return HALLAZGO, {'estado': 'FRENA', 'motivo': 'el destino cae adentro del repositorio: la evidencia va afuera, donde fija DEC-009'}
    repo = repo_git(a.destino)
    if repo:
        return HALLAZGO, {'estado': 'FRENA', 'motivo': 'el destino cae adentro de un repositorio git (%s): ahi terminaria versionada; '
                                                       'la evidencia va afuera de todo repositorio, donde fija DEC-009' % limpio(repo)}
    base = os.path.join(a.destino, '%s-%s' % (a.incidente, time.strftime('%Y%m%d-%H%M%S', time.gmtime())))
    carpeta, n = base, 1
    while os.path.exists(carpeta):
        n += 1
        carpeta = '%s-%d' % (base, n)
    os.makedirs(carpeta)
    items, sin_datos = [], []
    for i, fuente in enumerate(a.fuente, 1):
        if not os.path.isfile(fuente):
            sin_datos.append('fuente %d (%s): no existe o no es un archivo' % (i, limpio(fuente)))
            continue
        try:
            item, aviso = copiar(fuente, os.path.join(carpeta, '%02d-%s' % (i, os.path.basename(fuente))))
        except OSError as e:
            sin_datos.append('fuente %d (%s): no se pudo leer o copiar (%s)' % (i, limpio(fuente), type(e).__name__))
            continue
        items.append(item)
        if aviso:
            sin_datos.append(aviso)
    manifiesto = {'formato': FORMATO, 'incidente': a.incidente, 'pedido_por': limpio(a.pedido_por, 120), 'juntado_en': utc(),
                  'juntado_por': 'bin/juntar-evidencia.py', 'algoritmo': 'sha256', 'items': items, 'sin_datos': sin_datos}
    ruta = os.path.join(carpeta, MANIFIESTO)
    with open(ruta, 'w', encoding='utf-8') as h:
        json.dump(manifiesto, h, ensure_ascii=True, indent=1)
    os.chmod(ruta, stat.S_IREAD)
    estado = SIN_DATOS if sin_datos or not items else OK
    if not items and not sin_datos:
        sin_datos.append('no se copio ningun archivo')
    return estado, {'estado': NOMBRE[estado], 'incidente': a.incidente, 'carpeta': carpeta, 'manifiesto': ruta,
                    'sha256_manifiesto': hash_de(ruta), 'items': items, 'sin_datos': sin_datos}


def verificar(a):
    """(estado, salida). SOLO LECTURA."""
    carpeta = a.verificar if os.path.isdir(a.verificar) else os.path.dirname(a.verificar)
    ruta = os.path.join(carpeta, MANIFIESTO)
    if not os.path.isfile(ruta):
        return SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': 'no hay %s en %s' % (MANIFIESTO, limpio(carpeta))}
    try:
        with open(ruta, 'rb') as h:
            m = json.loads(h.read().decode('utf-8'))
    except (OSError, ValueError, UnicodeDecodeError):
        return SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': 'el manifiesto no se puede leer'}
    items = m.get('items') if isinstance(m, dict) else None
    if not items or not isinstance(items, list):
        return SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': 'el manifiesto no lista ningun archivo: no hay nada que verificar'}
    hallazgos, sin_datos, avisos, verificados = [], [], [], 0
    if not a.hash_manifiesto.strip():
        sin_datos.append('falta --hash-manifiesto: sin el hash anotado en el incidente no se puede decir que el manifiesto '
                         'no cambio (alguien pudo reescribirlo junto con las copias)')
    elif hash_de(ruta) != a.hash_manifiesto.strip().lower():
        hallazgos.append('el manifiesto cambio: su hash no es el que quedo anotado en el incidente')
    nombres = set()
    for it in items:
        nombre = str((it or {}).get('archivo', ''))
        nombres.add(nombre)
        if not nombre or os.path.basename(nombre) != nombre or nombre in ('.', '..'):
            hallazgos.append('el manifiesto trae un nombre de archivo invalido: %s' % limpio(nombre, 60))
            continue
        copia = os.path.join(carpeta, nombre)
        if not os.path.isfile(copia):
            hallazgos.append('%s: falta en la carpeta de evidencia' % nombre)
            continue
        try:
            actual = hash_de(copia)
        except OSError as e:
            sin_datos.append('%s: no se pudo leer (%s)' % (nombre, type(e).__name__))
            continue
        if actual != str(it.get('sha256', '')).lower():
            hallazgos.append('%s: el hash no coincide con el del manifiesto (se modifico)' % nombre)
        else:
            verificados += 1
    for extra in sorted(set(os.listdir(carpeta)) - nombres - {MANIFIESTO}):
        avisos.append('%s: esta en la carpeta y no figura en el manifiesto' % limpio(extra, 80))
    estado = HALLAZGO if hallazgos else SIN_DATOS if sin_datos else OK
    return estado, {'estado': NOMBRE[estado], 'carpeta': carpeta, 'incidente': m.get('incidente', ''), 'verificados': verificados,
                    'de': len(items), 'hallazgos': hallazgos, 'sin_datos': sin_datos, 'avisos': avisos}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Evidencia de un incidente: copia, hash y custodia, fuera del repositorio.')
    ap.add_argument('--incidente', default='')
    ap.add_argument('--destino', default='', help='carpeta FUERA del repositorio (la de DEC-009)')
    ap.add_argument('--pedido-por', default='', help='quien pidio juntar la evidencia (rol o persona)')
    ap.add_argument('--fuente', action='append', default=[])
    ap.add_argument('--verificar', default='', help='carpeta de una evidencia ya juntada')
    ap.add_argument('--hash-manifiesto', default='', help='el SHA-256 del manifiesto anotado en el incidente')
    ap.add_argument('--raiz', default=RAIZ, help='solo para las pruebas: el repositorio del Cerebro (por defecto, este)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    motivo = python_apto()
    if motivo:
        estado, salida = SIN_DATOS, {'estado': 'SIN DATOS', 'motivo': motivo}
    else:
        estado, salida = verificar(a) if a.verificar else juntar(a)
    salida['no_mira'] = list(NO_MIRA)
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return estado
    if a.verificar:
        print('VERIFICACION DE EVIDENCIA %s -- %s' % (salida.get('carpeta', a.verificar), salida['estado']))
        if salida.get('motivo'):
            print('  %s' % salida['motivo'])
        else:
            print('  %d de %d archivo(s) coinciden con su hash' % (salida['verificados'], salida['de']))
        for x in salida.get('hallazgos', []):
            print('  HALLAZGO: ' + x)
        for x in salida.get('sin_datos', []):
            print('  SIN DATOS: ' + x)
        for x in salida.get('avisos', []):
            print('  aviso: ' + x)
    else:
        print('EVIDENCIA %s -- %s' % (a.incidente or '?', salida['estado']))
        if salida.get('motivo'):
            print('  %s' % salida['motivo'])
        else:
            print('  Carpeta: %s' % salida['carpeta'])
            for it in salida['items']:
                print('  %-30s %10d bytes  sha256 %s%s' % (it['archivo'], it['bytes'], it['sha256'], ('  (' + it['aviso'] + ')') if it['aviso'] else ''))
            for x in salida['sin_datos']:
                print('  SIN DATOS: ' + x)
            print('  Manifiesto: %s' % salida['manifiesto'])
            print('  sha256 del manifiesto: %s  <- anotalo en el documento del incidente: es el ancla para --verificar' % salida['sha256_manifiesto'])
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return estado


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
