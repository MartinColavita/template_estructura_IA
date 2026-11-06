#!/usr/bin/env python3
"""Prueba de bin/registrar-sesion.py sobre una transcripcion de mentira (formato .jsonl de Claude Code).
Se corre:  python -B bin/probar-registrar-sesion.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'registrar-sesion.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args, stdin=None):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace', input=stdin)
    return r.returncode, r.stdout + r.stderr


def linea(ts, contenido, tipo='assistant'):
    return json.dumps({'type': tipo, 'timestamp': ts, 'sessionId': 'ses-1', 'message': {'role': tipo, 'content': contenido}})


VEREDICTO = "VEREDICTO-INICIO\n5 verificar-tdd : OK\nBLOQUEANTES: 1   SIN DATOS (no se pudo mirar): 2   SIN DATOS (pendiente declarado): 3\nVEREDICTO-FIN"


def main():
    print('== registrar-sesion')
    tmp = tempfile.mkdtemp(prefix='probar-sesion-')
    tr = os.path.join(tmp, 'ses-1.jsonl')
    with open(tr, 'w', encoding='utf-8') as h:
        h.write(linea('2026-11-04T10:00:00Z', [{'type': 'text', 'text': '<command-name>/guiar-tdd</command-name>'}], 'user') + '\n')
        h.write(linea('2026-11-04T10:05:00Z', [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'desarrollar-asignadas'}}]) + '\n')
        h.write(linea('2026-11-04T10:06:00Z', [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'python bin/verificar-tdd.py --repo x'}}]) + '\n')
        h.write(linea('2026-11-04T10:07:00Z', [{'type': 'tool_result', 'content': [{'type': 'text', 'text': 'TAREA-TERMINADA\n' + VEREDICTO + '\n\n**FRICCIONES**\n1. una\n2. dos\n3. tres\n\n## Otra seccion\n1. no cuenta'}]}], 'user') + '\n')
        h.write(linea('2026-11-04T10:30:00Z', [{'type': 'text', 'text': 'PREGUNTA-ORQUESTADOR: que hago\nSIN DATOS -- error del script: X'}]) + '\n')
        h.write('esto no es json\n')
    salida = os.path.join(tmp, 'sesiones.jsonl')
    rc, out = correr('--transcripcion', tr, '--salida', salida, '--json')
    d = json.loads(out)
    caso('registra (0) y cuenta skills por tool_use y por /comando', rc == 0 and d['skills'] == {'guiar-tdd': 1, 'desarrollar-asignadas': 1}, out[:300])
    caso('cuenta veredictos, bloqueantes y las dos clases de SIN DATOS', d['veredictos'] == 1 and d['bloqueantes'] == 1 and d['sin_datos_no_mirado'] == 2 and d['sin_datos_declarado'] == 3)
    caso('cuenta fricciones (3, no las de otra seccion), Tareas terminadas, preguntas, errores de script y scripts corridos', d['fricciones'] == 3 and d['tareas_terminadas'] == 1 and d['preguntas_bloqueantes'] == 1 and d['errores_de_script'] == 1 and d['scripts_corridos'] == 1, str(d))
    caso('duracion en minutos y fecha', d['duracion_min'] == 30 and d['fecha'].startswith('2026-11-04'))
    caso('no guarda texto de la conversacion', 'que hago' not in open(salida, encoding='utf-8').read() and 'una' not in json.dumps(d['skills']))
    rc, out = correr('--transcripcion', tr, '--salida', salida)
    caso('volver a registrar la misma sesion no duplica la linea', rc == 0 and len([l for l in open(salida, encoding='utf-8').read().split('\n') if l.strip()]) == 1)
    hook = json.dumps({'session_id': 'hook-7', 'transcript_path': tr, 'cwd': tmp, 'hook_event_name': 'SessionEnd'})
    rc, out = correr('--salida', salida, stdin=hook)
    caso('desde el hook (JSON por stdin): usa transcript_path y session_id', rc == 0 and 'hook-7' in open(salida, encoding='utf-8').read(), out[:300])
    rc, out = correr('--transcripcion', os.path.join(tmp, 'no.jsonl'), '--salida', salida)
    caso('sin transcripcion: SIN DATOS (2)', rc == 2)
    vacia = os.path.join(tmp, 'vacia.jsonl'); open(vacia, 'w').close()
    rc, out = correr('--transcripcion', vacia, '--salida', salida)
    caso('transcripcion vacia: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
