#!/usr/bin/env python3
"""Deriva, de forma DETERMINISTA, el arbol Epica -> Feature -> Historia de una ficha del Cerebro,
1:1 contra su bloque '## Derivacion a backlog'. SOLO LECTURA.

    python bin/derivar-arbol.py cerebro-digital/<modulo>/funcional/<ficha>.md
    python bin/derivar-arbol.py <ficha.md> --json

Tres estados, nunca dos:  0 = arbol listo   1 = la ficha no se deriva (sin bloque, con la marca de advertencia (el triangulo), o incoherente)
2 = SIN DATOS (no se pudo leer)

POR QUE EXISTE. La Regla de cardinalidad de AGENTS.md dice que el conteo lo fija la ficha, no el
modelo: 1 Epica por [S-nn], 1 Feature por [C-nn], 1 Historia por [F-nn], 0 Tareas. Si lo cuenta un
script, dos modelos distintos producen el mismo arbol. sincronizar-backlog lo corre primero y
recien despues redacta cada nodo; si este script dice que no se deriva, no se deriva.

Lo que devuelve por nodo: tipo, clave, titulo, padre, reglas asignadas, la etiqueta tematica unica
de la ficha y el documento fuente (la ruta de la ficha). Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from auditoria import cerebro, texto  # noqa: E402

OK, NO_SE_DERIVA, SIN_DATOS = 0, 1, 2
RAIZ = cerebro.raiz_repo()
ETIQUETA = re.compile(r'\*\*Etiqueta tem[a\u00e1]tica:\*\*\s*`([^`]+)`')


def bloque_derivacion(s):
    i = s.find('## Derivaci')
    if i < 0:
        return None
    fin = s.find('\n## ', i + 3)
    return s[i:fin if fin > 0 else len(s)]


def main():
    ap = argparse.ArgumentParser(description='Arbol 1:1 desde el bloque de derivacion de una ficha.')
    ap.add_argument('ficha')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    ruta = os.path.abspath(a.ficha)
    if not os.path.isfile(ruta):
        print('SIN DATOS -- no existe %s' % ruta)
        return SIN_DATOS
    try:
        s = texto.leer(ruta).replace('\r\n', '\n')
    except (OSError, UnicodeDecodeError) as e:
        print('SIN DATOS -- no se pudo leer la ficha: %s' % e)
        return SIN_DATOS

    bloque = bloque_derivacion(s)
    if bloque is None:
        print('NO SE DERIVA -- la ficha no tiene el bloque "## Derivacion a backlog". Se pide cerrarlo en el Cerebro.')
        return NO_SE_DERIVA
    if chr(0x26a0) in bloque:
        print('NO SE DERIVA -- el bloque de derivacion tiene la marca de advertencia (no esta validado). Se pide cerrarlo en el Cerebro.')
        return NO_SE_DERIVA
    ficha = cerebro.leer_ficha(ruta)
    d = ficha['derivacion'] or {'S': {}, 'C': {}, 'F': {}}
    problemas = []
    if not d['S']:
        problemas.append('no hay ningun [S-nn]')
    if not d['F']:
        problemas.append('no hay ningun [F-nn]')
    for k, c in d['C'].items():
        if c.get('slice') and c['slice'] not in d['S']:
            problemas.append('%s apunta al slice %s que no existe' % (k, c['slice']))
        if not c.get('slice') and len(d['S']) > 1:
            problemas.append('%s no dice de que slice es y hay mas de uno' % k)
    for k, f in d['F'].items():
        if f.get('capacidad') and f['capacidad'] not in d['C']:
            problemas.append('%s apunta a la capacidad %s que no existe' % (k, f['capacidad']))
        if not f.get('capacidad') and len(d['C']) > 1:
            problemas.append('%s no dice de que capacidad es y hay mas de una' % k)
        if not f.get('reglas'):
            problemas.append('%s no tiene reglas asignadas' % k)
    m = ETIQUETA.search(s)
    etiqueta = m.group(1).strip() if m else None
    if not etiqueta:
        problemas.append('la ficha no declara "**Etiqueta tematica:** `...`"')
    if problemas:
        print('NO SE DERIVA -- el bloque es incoherente:')
        for p in problemas:
            print('  - ' + p)
        return NO_SE_DERIVA

    fuente = os.path.relpath(ruta, RAIZ).replace(os.sep, '/')
    unico_s = next(iter(d['S'])) if len(d['S']) == 1 else None
    unico_c = next(iter(d['C'])) if len(d['C']) == 1 else None
    nodos = []
    for k, v in d['S'].items():
        nodos.append({'tipo': 'Epica', 'clave': k, 'titulo': v['titulo'], 'padre': None, 'reglas': []})
    for k, v in d['C'].items():
        nodos.append({'tipo': 'Feature', 'clave': k, 'titulo': v['titulo'], 'padre': v.get('slice') or unico_s, 'reglas': []})
    for k, v in d['F'].items():
        nodos.append({'tipo': 'Historia', 'clave': k, 'titulo': v['titulo'], 'padre': v.get('capacidad') or unico_c, 'reglas': v.get('reglas', [])})
    salida = {'estado': 'OK', 'documento_fuente': fuente, 'etiqueta': etiqueta,
              'conteo': {'Epicas': len(d['S']), 'Features': len(d['C']), 'Historias': len(d['F']), 'Tareas': 0,
                         'total': len(d['S']) + len(d['C']) + len(d['F'])},
              'nodos': nodos}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('ARBOL 1:1 de %s' % fuente)
        print('  Etiqueta tematica (unica): %s' % etiqueta)
        for n in nodos:
            print('  %-8s %s  %s%s%s' % (n['tipo'], n['clave'], n['titulo'],
                                        ('  <- ' + n['padre']) if n['padre'] else '',
                                        ('  [' + ', '.join(n['reglas']) + ']') if n['reglas'] else ''))
        c = salida['conteo']
        print('  Conteo: %d Epica(s) + %d Feature(s) + %d Historia(s) = %d work items, 0 Tareas' % (c['Epicas'], c['Features'], c['Historias'], c['total']))
        print('  Lo que este script NO hace: redactar los nodos, buscar duplicados en el tablero ni escribir. Eso sigue en la skill, con confirmacion.')
    return OK


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
