#!/usr/bin/env python3
"""Prueba de bin/armar-corpus.py sobre una radiografia de mentira.
Se corre:  python -B bin/probar-armar-corpus.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'armar-corpus.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== armar-corpus')
    tmp = tempfile.mkdtemp(prefix='probar-corpus-')
    rad = os.path.join(tmp, 'radiografia.json')
    with open(rad, 'w', encoding='utf-8') as h:
        json.dump({'modulos': [{'modulo': 'reservas', 'archivos': 5}, {'modulo': 'reportes', 'archivos': 2}],
                   'api': [{'archivo': 'reservas/api.py', 'linea': 10, 'modulo': 'reservas', 'metodo': 'GET', 'ruta': '/reservas'},
                           {'archivo': 'reservas/api.py', 'linea': 20, 'modulo': 'reservas', 'metodo': 'POST', 'ruta': '/reservas'},
                           {'archivo': 'reservas/api.py', 'linea': 30, 'modulo': 'reservas', 'metodo': 'GET', 'ruta': '/reservas/{id}'}],
                   'reglas_candidatas': [{'archivo': 'reservas/domain.py', 'linea': 8, 'modulo': 'reservas', 'tipo': 'constante con nombre', 'valor': 'MAX_DIAS = 30'},
                                         {'archivo': 'reservas/domain.py', 'linea': 15, 'modulo': 'reservas', 'tipo': 'condicion que frena', 'valor': 'if dias > MAX_DIAS: raise'},
                                         {'archivo': 'reportes/x.py', 'linea': 1, 'modulo': 'reportes', 'tipo': 'constante con nombre', 'valor': 'N = 1'}]}, h)
    salida = os.path.join(tmp, 'corpus.json')
    rc, out = correr(rad, '--slice', 'reservas', '--salida', salida)
    caso('arma el corpus del slice (0)', rc == 0 and os.path.isfile(salida), out[:300])
    c = json.load(open(salida, encoding='utf-8'))
    ids = [x['id'] for x in c['casos']]
    caso('un caso por endpoint (3) mas un borde por regla (2) = 5, con ids unicos', len(c['casos']) == 5 and len(set(ids)) == 5, str(ids))
    post = next(x for x in c['casos'] if x['metodo'] == 'POST')
    caso('el POST muta y pide cuerpo a completar; el GET no muta', post['muta'] and '<completar' in post['cuerpo'] and not next(x for x in c['casos'] if x['nombre'].startswith('GET /reservas$') or x['ruta'] == '/reservas' and x['metodo'] == 'GET')['muta'])
    caso('el parametro de ruta queda como <completar>', any('<completar: id de prueba>' in x['ruta'] for x in c['casos']))
    caso('cada caso cita archivo:linea', all(':' in x['origen'] for x in c['casos']))
    caso('los bordes nombran la constante y no inventan valores', any('MAX_DIAS = 30' in (x.get('borde') or '') for x in c['casos']) and all('<completar' in x['ruta'] for x in c['casos'] if x.get('borde')))
    caso('no mezcla reglas de otro modulo', not any('N = 1' in (x.get('borde') or '') for x in c['casos']))
    rc, out = correr(rad, '--slice', 'noexiste', '--salida', salida)
    caso('modulo inexistente: SIN DATOS (2) y lista los que hay', rc == 2 and 'reservas' in out)
    with open(rad, 'w', encoding='utf-8') as h:
        json.dump({'modulos': [{'modulo': 'vacio', 'archivos': 1}], 'api': [], 'reglas_candidatas': []}, h)
    rc, out = correr(rad, '--slice', 'vacio', '--salida', salida)
    caso('modulo sin endpoints ni reglas: SIN DATOS (2), se arma a mano', rc == 2 and 'a mano' in out)
    rc, out = correr(os.path.join(tmp, 'no.json'), '--slice', 'x')
    caso('radiografia inexistente: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
