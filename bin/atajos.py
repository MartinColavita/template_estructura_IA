#!/usr/bin/env python3
"""Las marcas `atajo:` del codigo de uno o mas repos: que se simplifico a proposito, hasta donde aguanta y cuando
se mejora. SOLO LECTURA.

    python -I bin/atajos.py --repo <carpeta> [--repo <otra> ...] [--deuda <cerebro-digital/<modulo>/aplicacion/deuda.md>] [--json]

Tres estados, nunca dos:  0 = OK (cada atajo dice cuando se mejora; o no hay atajos en los archivos leidos)
                          1 = HALLAZGO (un atajo sin `cuando ...` o sin limite, o que cita una DT-nnn que no esta
                              abierta en deuda.md)
                          2 = SIN DATOS (la carpeta no existe o no es la raiz de su repo, git no pudo listar, cero
                              archivos de codigo leidos en alguno de los repos, o deuda.md ilegible)

LA MARCA (desarrollo/references/metodo/refactor.md, seccion Deuda tecnica), en un comentario del lenguaje:

    // atajo: <que se simplifico y hasta donde aguanta>; cuando <que tiene que pasar para mejorarlo> <#ID o DT-nnn>

POR QUE EXISTE. Un atajo tomado a sabiendas esta bien; uno que nadie vuelve a mirar se pudre. La marca deja el limite
a la vista donde esta el codigo, y esto las junta todas: las que no dicen cuando se mejoran (las que se pudren), y las
que citan una deuda que el Cerebro no tiene abierta. Idea tomada de DietrichGebert/ponytail (MIT), ver
desarrollo/references/referencias-externas.md.

QUE NO HACE. No escribe en deuda.md (eso es de cerebro-curator, con el "si" de una persona), no juzga si el limite
declarado es cierto ni si la carga real ya lo paso (eso es criterio de la revision), no lee documentacion (.md, .txt):
la marca es un comentario de codigo. Solo biblioteca estandar.
"""

import argparse
import json
import os
import re
import subprocess
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
MAX_BYTES = 2 * 1024 * 1024
SALTEAR = {'.git', 'node_modules', 'target', 'dist', 'build', 'out', '__pycache__', '.venv', 'venv', '.idea',
           '.gradle', 'coverage', 'vendor', '.next', '.nuxt'}
DOCS = ('.md', '.markdown', '.txt', '.rst', '.adoc')
# La marca va despues de un comentario: //, #, --, /*, * (dentro de un bloque) o <!--, al principio de la linea o
# despues de un espacio, `{` (JSX), `;`, `)` o `,`. Lo que la nombra en prosa o dentro de un string no cuenta.
MARCA = re.compile(r'(?:^|(?<=[\s{;),]))(?P<pre>//+|#+|--|/\*+|\*+|<!--)\s*atajo\s*:(?P<resto>.*)$', re.I)
REF = re.compile(r'(?<![\w-])(#\d+|DT-\d+)\b', re.I)
LIMPIAR = ' \t,;.:-'


class SinDatos(Exception):
    pass


def listar(repo):
    """Archivos del repo: los que git versiona o versionaria (respeta .gitignore); sin git, recorriendo la carpeta."""
    try:
        r = subprocess.run(['git', '-C', repo, 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
        es_git = r.returncode == 0 and r.stdout.strip() == 'true'
    except OSError:
        es_git = False
    if es_git:
        # Solo la raiz de un repo: una carpeta de adentro puede tener otro repo clonado e ignorado (back/<app>), y
        # git listaria lo del repo de afuera, no la app. Mejor SIN DATOS que un OK sobre lo que no se leyo.
        r = subprocess.run(['git', '-C', repo, 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        raiz = r.stdout.strip()
        if r.returncode != 0 or not raiz:
            raise SinDatos('git no pudo decir cual es la raiz del repo de %s' % repo)
        if os.path.normcase(os.path.realpath(raiz)) != os.path.normcase(os.path.realpath(repo)):
            raise SinDatos('%s esta dentro del repo %s pero no es su raiz: pasa la raiz del repo de codigo '
                           '(por ejemplo back/<app>)' % (repo, raiz))
        r = subprocess.run(['git', '-C', repo, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                           capture_output=True)
        if r.returncode != 0:
            raise SinDatos('git no pudo listar los archivos de %s: %s' % (repo, r.stderr.decode('utf-8', 'replace').strip()))
        rels = [p for p in r.stdout.decode('utf-8', 'replace').split('\0') if p]
        return [p for p in rels if not (set(p.replace('\\', '/').split('/')[:-1]) & SALTEAR)]
    out = []
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SALTEAR]
        for f in files:
            out.append(os.path.relpath(os.path.join(base, f), repo).replace(os.sep, '/'))
    return out


def leer_texto(ruta):
    """Contenido del archivo, o None si es binario, enorme o ilegible."""
    try:
        if os.path.getsize(ruta) > MAX_BYTES:
            return None
        with open(ruta, 'rb') as h:
            datos = h.read()
    except OSError:
        return None
    if b'\0' in datos[:8192]:
        return None
    return datos.decode('utf-8', 'replace')


STRING = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')


def buscar_marca(linea):
    """(resto, descartadas): el resto de la primera marca de la linea que no esta dentro de un string (o None), y
    cuantas se descartaron por estar dentro de uno. Se sacan los strings completos de lo que hay antes de la marca;
    si queda una comilla abierta, la marca esta adentro de un string."""
    descartadas = 0
    for m in MARCA.finditer(linea):
        antes = STRING.sub('', linea[:m.start('pre')])
        if any(q in antes for q in '"\'`'):
            descartadas += 1
            continue
        # el comentario termina en el primer cierre (*/ o -->): lo que sigue es codigo (JSX: */}</div>)
        return re.split(r'\*/|-->', m.group('resto'), maxsplit=1)[0].strip(), descartadas
    return None, descartadas


def interpretar(resto):
    """(limite, disparador, refs) de lo que sigue a `atajo:`."""
    refs = sorted({r.upper() if r.upper().startswith('DT-') else r for r in REF.findall(resto)})
    m = re.search(r';\s*cuando\b', resto, re.I) or re.search(r',\s*cuando\b', resto, re.I)
    limite = resto[:m.start()] if m else resto
    disparador = resto[m.end():] if m else ''
    limite = REF.sub('', limite).strip(LIMPIAR)
    disparador = REF.sub('', disparador).strip(LIMPIAR)
    return limite, disparador, refs


def deudas(ruta):
    """(abiertas, pagadas): los DT-nnn reales de deuda.md (la fila de ejemplo, con <...>, no cuenta)."""
    with open(ruta, 'r', encoding='utf-8-sig', errors='replace') as h:
        lineas = h.read().splitlines()
    abiertas, pagadas, seccion = set(), set(), ''
    for l in lineas:
        t = re.match(r'^##\s+(.+?)\s*$', l)
        if t:
            seccion = t.group(1).lower()
            continue
        m = re.match(r'^\|\s*(DT-\d+)\s*\|\s*([^|]*)\|', l, re.I)
        if not m or m.group(2).strip().startswith('<'):
            continue
        (pagadas if 'pagad' in seccion else abiertas).add(m.group(1).upper())
    return abiertas, pagadas


def main():
    ap = argparse.ArgumentParser(description='Las marcas atajo: del codigo, con su limite y su disparador.')
    ap.add_argument('--repo', action='append', required=True, help='carpeta del repo de codigo (se puede repetir)')
    ap.add_argument('--deuda', help='aplicacion/deuda.md del modulo, para chequear los DT-nnn citados')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    abiertas = pagadas = None
    if a.deuda:
        if not os.path.isfile(a.deuda):
            print('SIN DATOS -- no existe %s: sin deuda.md no se puede chequear ningun DT-nnn' % a.deuda)
            return SIN_DATOS
        abiertas, pagadas = deudas(a.deuda)

    leidos, atajos, en_string = 0, [], []
    for repo in a.repo:
        if not os.path.isdir(repo):
            print('SIN DATOS -- no existe la carpeta %s' % repo)
            return SIN_DATOS
        etiqueta = os.path.basename(os.path.abspath(repo))
        leidos_repo = 0
        for rel in sorted(listar(repo)):
            if rel.lower().endswith(DOCS):
                continue
            texto = leer_texto(os.path.join(repo, rel))
            if texto is None:
                continue
            leidos_repo += 1
            for n, linea in enumerate(texto.splitlines(), 1):
                resto, descartadas = buscar_marca(linea)
                if descartadas:
                    en_string.append('%s/%s:%d' % (etiqueta, rel, n))
                if resto is None:
                    continue
                limite, disparador, refs = interpretar(resto)
                problemas = []
                if not limite:
                    problemas.append('sin limite')
                if not disparador:
                    problemas.append('sin disparador (cuando ...)')
                if abiertas is not None:
                    for r in refs:
                        if r.startswith('DT-') and r in pagadas:
                            problemas.append('%s figura como pagada y la marca sigue' % r)
                        elif r.startswith('DT-') and r not in abiertas:
                            problemas.append('%s no esta abierta en deuda.md' % r)
                atajos.append({'archivo': '%s/%s' % (etiqueta, rel), 'linea': n, 'limite': limite,
                               'disparador': disparador, 'refs': refs, 'problemas': problemas})
        # La regla del cero, por repo: un repo sin codigo leido no queda tapado por otro que si lo tiene.
        if leidos_repo == 0:
            print('SIN DATOS -- cero archivos de codigo leidos en %s: no hay nada que contar' % repo)
            return SIN_DATOS
        leidos += leidos_repo

    con_problema = [x for x in atajos if x['problemas']]
    sin_ref = [x for x in atajos if not x['refs']]
    veredicto = 'HALLAZGO' if con_problema else 'OK'
    rc = HALLAZGO if con_problema else OK
    if a.json:
        print(json.dumps({'veredicto': veredicto, 'archivos_leidos': leidos, 'atajos': atajos,
                          'sin_referencia': len(sin_ref), 'descartadas_en_string': en_string},
                         ensure_ascii=False, indent=1))
        return rc

    print('Atajos -- %d archivo(s) de codigo leido(s) en %d repo(s): %d marca(s)' % (leidos, len(a.repo), len(atajos)))
    for x in atajos:
        print('  %s:%d  %s | cuando: %s | %s%s' % (
            x['archivo'], x['linea'], x['limite'] or '-', x['disparador'] or '-', ' '.join(x['refs']) or 'sin ref',
            ('   <- ' + '; '.join(x['problemas'])) if x['problemas'] else ''))
    if con_problema:
        print('HALLAZGO -- %d de %d atajo(s) con problema: sin disparador o sin limite se pudren; un DT-nnn que no '
              'esta abierto rompe la traza.' % (len(con_problema), len(atajos)))
    else:
        print('OK -- %d atajo(s), todos con limite y disparador.' % len(atajos))
    if sin_ref:
        print('  AVISO: %d atajo(s) sin #ID ni DT-nnn: el porque no queda en ningun lado. Proponer su DT-nnn en '
              'aplicacion/deuda.md (cerebro-curator, con el si de una persona).' % len(sin_ref))
    if abiertas is None and any(r.startswith('DT-') for x in atajos for r in x['refs']):
        print('  AVISO: sin --deuda no se chequeo que los DT-nnn citados existan.')
    if en_string:
        print('  AVISO: %d linea(s) con algo que parece una marca dentro de un string; no se contaron. Mirarlas: si '
              'alguna es un comentario de verdad, el script se equivoco: %s' % (len(en_string), ', '.join(en_string[:10])))
    print('  Lo que este script NO mira: si el limite declarado es cierto ni si la carga real ya lo paso (criterio de '
          'la revision), los TODO/FIXME que no usan la marca, ni los strings de varias lineas (docstrings, template '
          'literals): una marca escrita ahi se cuenta como si fuera un comentario.')
    return rc


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            # UTF-8 siempre: los comentarios van en espanol, y en Windows la salida redirigida seria cp1252.
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.exit(main())
    except SinDatos as e:
        print('SIN DATOS -- %s' % e)
        sys.exit(SIN_DATOS)
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
