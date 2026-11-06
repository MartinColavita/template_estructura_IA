#!/usr/bin/env python3
"""Prueba de bin/tendencia.py sobre sesiones de mentira.
Se corre:  python -B bin/probar-tendencia.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'tendencia.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def sesion(i, bloq, sd, fric, preg=0, err=0, fall=0):
    return json.dumps({'sesion': 's%d' % i, 'fecha': '2026-11-%02dT10:00:00' % (i + 1), 'veredictos': 2, 'bloqueantes': bloq, 'sin_datos_no_mirado': sd,
                       'sin_datos_declarado': 1, 'fricciones': fric, 'preguntas_bloqueantes': preg, 'errores_de_script': err, 'tareas_fallidas': fall,
                       'tareas_terminadas': 1, 'skills': {'guiar-tdd': 1}, 'escrito_por': 'bin/registrar-sesion.py'})


def main():
    print('== tendencia')
    tmp = tempfile.mkdtemp(prefix='probar-tend-')
    p = os.path.join(tmp, 'sesiones.jsonl')
    rc, out = correr('--sesiones', os.path.join(tmp, 'no.jsonl'))
    caso('sin archivo: SIN DATOS (2)', rc == 2)
    with open(p, 'w', encoding='utf-8') as h:
        h.write(sesion(1, 2, 1, 5) + '\n')
    rc, out = correr('--sesiones', p)
    caso('una sola sesion: SIN DATOS (2)', rc == 2 and 'al menos 2' in out)
    with open(p, 'w', encoding='utf-8') as h:
        for i, (b, s, f) in enumerate([(2, 2, 6), (2, 1, 5), (1, 1, 4), (0, 0, 2)]):
            h.write(sesion(i, b, s, f) + '\n')
    rc, out = correr('--sesiones', p, '--n', '2')
    caso('mejora: MEJOR (0) con los numeros', rc == 0 and out.startswith('MEJOR') and 'bloqueantes por veredicto 1,0 -> 0,2' in out, out[:400])
    rc, out = correr('--sesiones', p, '--n', '2', '--breve')
    caso('--breve: una sola linea con [tendencia]', rc == 0 and out.count('\n') == 1 and out.startswith('[tendencia]'))
    with open(p, 'w', encoding='utf-8') as h:
        for i, (b, s, f, e) in enumerate([(0, 0, 1, 0), (0, 0, 1, 0), (2, 1, 4, 1), (3, 2, 5, 1)]):
            h.write(sesion(i, b, s, f, err=e) + '\n')
    rc, out = correr('--sesiones', p, '--n', '2')
    caso('empeora: PEOR (1), dice que empeora y que hacer', rc == 1 and out.startswith('PEOR') and 'Empeora:' in out and 'mejorar-ecosistema' in out, out[:400])
    rc, out = correr('--sesiones', p, '--n', '2', '--json')
    d = json.loads(out)
    caso('--json: veredicto y detalle por medida', d['veredicto'] == 'PEOR' and len(d['detalle']) == 6 and d['skills_ultimas'] == {'guiar-tdd': 2})
    with open(p, 'w', encoding='utf-8') as h:
        for i in range(4):
            h.write(sesion(i, 1, 1, 3) + '\n')
    rc, out = correr('--sesiones', p, '--n', '2')
    caso('sin cambios: IGUAL (0)', rc == 0 and out.startswith('IGUAL') and 'Sin cambios' in out)
    with open(p, 'a', encoding='utf-8') as h:
        h.write('{"sesion": "ajena", "escrito_por": "otro"}\nbasura\n')
    rc, out = correr('--sesiones', p, '--n', '2')
    caso('ignora lineas que no escribio registrar-sesion.py', rc == 0 and 'IGUAL' in out)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
