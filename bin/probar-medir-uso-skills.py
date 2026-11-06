#!/usr/bin/env python3
"""Prueba de bin/medir-uso-skills.py sobre transcripciones de mentira en una carpeta temporal.
Se corre:  python -B bin/probar-medir-uso-skills.py   -> OK o FALLA, con el detalle de cada caso."""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'medir-uso-skills.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def linea(ts, cwd, sesion, contenido):
    return json.dumps({'type': 'assistant', 'timestamp': ts, 'cwd': cwd, 'sessionId': sesion, 'message': {'role': 'assistant', 'content': contenido}}) + '\n'


def main():
    print('== medir-uso-skills')
    tmp = tempfile.mkdtemp(prefix='probar-uso-')
    proy = os.path.join(tmp, 'projects', 'C--Users-x-Desktop-mi-app')
    os.makedirs(proy)
    hoy = datetime.datetime.now(datetime.timezone.utc)
    reciente = (hoy - datetime.timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    viejo = (hoy - datetime.timedelta(days=200)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    cwd = os.path.join(tmp, 'mi-app')
    with open(os.path.join(proy, 's1.jsonl'), 'w', encoding='utf-8') as h:
        h.write(linea(reciente, cwd, 's1', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'redactar-tarea'}}]))
        h.write(linea(reciente, cwd, 's1', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'redactar-tarea'}}]))
        h.write(linea(reciente, cwd, 's1', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'anthropic-skills:docx'}}]))
        h.write(linea(reciente, cwd, 's1', [{'type': 'text', 'text': '<command-name>/desarrollo</command-name>'}]))
        h.write(linea(viejo, cwd, 's0', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'planificar-lote'}}]))
        h.write('esto no es json\n')
    with open(os.path.join(proy, 's2.jsonl'), 'w', encoding='utf-8') as h:
        h.write(linea(reciente, os.path.join(tmp, 'otro-proyecto'), 's2', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'comentar-tarea'}}]))
    rc, out = correr('--transcripciones', os.path.join(tmp, 'projects'), '--dias', '60', '--json')
    d = json.loads(out) if rc == 0 else {}
    caso('corre y devuelve JSON (0)', rc == 0 and d, out[:300])
    if d:
        por = {f['skill']: f for f in d['skills']}
        caso('cuenta las invocaciones del modelo (redactar-tarea x2)', por['redactar-tarea']['por_modelo'] == 2 and por['redactar-tarea']['ultima_vez'] == reciente[:10])
        caso('cuenta los comandos de la persona (/desarrollo)', por['desarrollo']['por_persona'] == 1)
        caso('lo viejo queda fuera de la ventana (planificar-lote sin uso)', 'planificar-lote' in d['sin_uso'])
        caso('lista las skills de afuera usadas (docx)', any(x['skill'] == 'docx' for x in d['skills_de_afuera_usadas']))
        caso('suma tokens de lo que no se usa', d['tokens_sin_uso'] > 0 and len(d['sin_uso']) >= 20)
        caso('cuenta transcripciones y sesiones', d['transcripciones'] == 2 and d['sesiones'] == 2)
    rc, out = correr('--transcripciones', os.path.join(tmp, 'projects'), '--proyecto', cwd, '--json')
    d2 = json.loads(out) if rc == 0 else {}
    caso('--proyecto filtra por cwd (comentar-tarea queda afuera)', d2 and 'comentar-tarea' in d2['sin_uso'] and {f['skill']: f for f in d2['skills']}['redactar-tarea']['por_modelo'] == 2)
    rc, out = correr('--transcripciones', os.path.join(tmp, 'projects'))
    caso('en texto imprime la tabla y la advertencia de no borrar', rc == 0 and 'USO DE SKILLS' in out and 'NO se borra sola' in out)
    rc, out = correr('--transcripciones', os.path.join(tmp, 'vacio'))
    caso('sin transcripciones: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
