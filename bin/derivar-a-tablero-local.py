#!/usr/bin/env python3
"""Baja una ficha del Cerebro al TABLERO LOCAL, 1:1 contra su bloque '## Derivacion a backlog'. Sin MCP.

    python bin/derivar-a-tablero-local.py cerebro-digital/<modulo>/funcional/<ficha>.md [--tablero <carpeta>] [--dry-run] [--json]

Tres estados, nunca dos:  0 = arbol creado (o ya estaba)   1 = la ficha no se deriva (lo dice derivar-arbol.py)   2 = SIN DATOS

POR QUE EXISTE. En modo solo, sincronizar-backlog no tiene un MCP donde escribir: el tablero es la carpeta
backlog/ del modulo. Este script es la mitad mecanica de esa bajada: corre derivar-arbol.py (el conteo lo fija
la ficha, no el modelo), y crea con tablero-local.py 1 Epica por [S-nn], 1 Feature por [C-nn] y 1 Historia por
[F-nn], con la etiqueta tematica de la ficha, el documento fuente por referencia y las reglas asignadas. Es
IDEMPOTENTE: un nodo cuyo titulo ya existe abierto en el tablero no se vuelve a crear (se informa el #ID), que
es la deduplicacion mecanica; el criterio fino (mismo objetivo con otro titulo) sigue siendo de la skill.

QUE NO HACE. No redacta (la Historia queda con el titulo, la fuente y las reglas; el Gherkin lo escribe
redactar-tarea), no crea Tareas (GATE de NIVEL), no decide: si derivar-arbol.py dice que no se deriva, no se
deriva. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import subprocess
import sys

OK, NO_SE_DERIVA, SIN_DATOS = 0, 1, 2
AQUI = os.path.dirname(os.path.abspath(__file__))


def correr(script, *args):
    r = subprocess.run([sys.executable, '-I', os.path.join(AQUI, script)] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def main():
    ap = argparse.ArgumentParser(description='Baja una ficha al tablero local, 1:1 contra su bloque de derivacion.')
    ap.add_argument('ficha')
    ap.add_argument('--tablero', default='', help='carpeta del backlog; por defecto la del modulo de la ficha (cerebro-digital/<modulo>/backlog)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not os.path.isfile(a.ficha):
        print('SIN DATOS -- no existe la ficha %s' % a.ficha)
        return SIN_DATOS
    rc, out = correr('derivar-arbol.py', a.ficha, '--json')
    if rc != 0:
        print('NO SE DERIVA -- derivar-arbol.py dijo (codigo %d):' % rc)
        print(out.strip())
        return NO_SE_DERIVA if rc == 1 else SIN_DATOS
    try:
        arbol = json.loads(out)
    except ValueError:
        print('SIN DATOS -- derivar-arbol.py no devolvio JSON.')
        return SIN_DATOS
    nodos = arbol.get('nodos') or arbol.get('arbol') or []
    etiqueta = arbol.get('etiqueta') or ''
    fuente = arbol.get('documento_fuente') or a.ficha
    tablero = a.tablero
    if not tablero:
        partes = os.path.abspath(a.ficha).replace('\\', '/').split('/')
        if 'cerebro-digital' in partes and len(partes) > partes.index('cerebro-digital') + 1:
            tablero = '/'.join(partes[:partes.index('cerebro-digital') + 2] + ['backlog'])
    if not tablero:
        print('SIN DATOS -- no puedo deducir el tablero de la ruta de la ficha: pasa --tablero.')
        return SIN_DATOS
    tb = ['--tablero', tablero]

    existentes = {}
    if os.path.isdir(tablero):
        rc, out = correr('tablero-local.py', *tb, 'listar', '--json')
        if rc == 0:
            for f in json.loads(out):
                if f.get('estado') not in ('Closed', 'Removed'):
                    existentes[(f.get('tipo'), (f.get('titulo') or '').strip().lower())] = f['id']

    ids, creados, reutilizados = {}, [], []
    for n in nodos:
        tipo = {'Epica': 'Epica', 'Feature': 'Feature', 'Historia': 'Historia'}.get(n.get('tipo'), n.get('tipo'))
        titulo = (n.get('titulo') or '').strip()
        padre = ids.get(n.get('padre')) if n.get('padre') else 0
        clave = (tipo, titulo.lower())
        if clave in existentes:
            ids[n['clave']] = existentes[clave]
            reutilizados.append({'clave': n['clave'], 'id': existentes[clave], 'titulo': titulo})
            continue
        if a.dry_run:
            ids[n['clave']] = 0
            creados.append({'clave': n['clave'], 'id': 0, 'tipo': tipo, 'titulo': titulo, 'padre': padre})
            continue
        cuerpo = os.path.join(tablero, '.cuerpo-tmp.md')
        os.makedirs(tablero, exist_ok=True)
        with open(cuerpo, 'w', encoding='utf-8', newline='\n') as h:
            h.write('# %s %s\n\n**Documento fuente:** `%s` (%s)\n\n**Reglas:** %s\n\n<descripcion: la redacta redactar-tarea con la plantilla del tipo>\n'
                    % (tipo, titulo, fuente, n['clave'], ', '.join(n.get('reglas') or []) or '(ninguna asignada en la ficha)'))
        args = [*tb, 'crear', '--tipo', tipo, '--titulo', titulo, '--etiqueta', etiqueta, '--cuerpo', cuerpo, '--json']
        if padre:
            args += ['--padre', str(padre)]
        rc, out = correr('tablero-local.py', *args)
        try:
            os.remove(cuerpo)
        except OSError:
            pass
        if rc != 0:
            print('SIN DATOS -- tablero-local.py no pudo crear %s "%s": %s' % (tipo, titulo, out.strip()[-200:]))
            return SIN_DATOS
        nuevo = json.loads(out)['id']
        ids[n['clave']] = nuevo
        creados.append({'clave': n['clave'], 'id': nuevo, 'tipo': tipo, 'titulo': titulo, 'padre': padre})

    salida = {'estado': 'OK', 'ficha': a.ficha, 'tablero': tablero, 'etiqueta': etiqueta, 'creados': creados, 'reutilizados': reutilizados,
              'conteo': {'Epica': sum(1 for n in nodos if n.get('tipo') == 'Epica'), 'Feature': sum(1 for n in nodos if n.get('tipo') == 'Feature'),
                         'Historia': sum(1 for n in nodos if n.get('tipo') == 'Historia'), 'Tarea': 0}}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return OK
    print('DERIVAR A TABLERO LOCAL -- %s -> %s%s' % (a.ficha, tablero, '  (dry-run)' if a.dry_run else ''))
    print('  Conteo 1:1 de la ficha: %d Epica, %d Feature, %d Historia, 0 Tareas (GATE de NIVEL)' % (salida['conteo']['Epica'], salida['conteo']['Feature'], salida['conteo']['Historia']))
    for c in creados:
        print('  %s %-8s %s -> #%s%s' % ('crearia' if a.dry_run else 'creado ', c['tipo'], c['titulo'], c['id'] or '?', ('  (padre #%d)' % c['padre']) if c['padre'] else ''))
    for r in reutilizados:
        print('  ya existia %s -> #%d (no se duplica)' % (r['titulo'], r['id']))
    print('  Etiqueta tematica: %s | Documento fuente: %s' % (etiqueta or '(sin etiqueta: HALLAZGO de la ficha)', fuente))
    print('  Lo que este script NO hace: redactar cada nodo (redactar-tarea), ni crear Tareas (se confirma el nivel en su propio turno).')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
