#!/usr/bin/env python3
"""Registra UNA sesion de trabajo con Claude Code como una linea de metricas en cerebro-digital/configuracion-ia/sesiones.jsonl.
Lo dispara el hook SessionEnd (.claude/settings.json) o se corre a mano.

    python bin/registrar-sesion.py                                  (desde el hook: lee el JSON del hook por stdin)
    python bin/registrar-sesion.py --transcripcion <sesion.jsonl> [--nucleo <raiz>] [--salida <sesiones.jsonl>] [--json]

Tres estados, nunca dos:  0 = registrada   1 = (no aplica)   2 = SIN DATOS (sin transcripcion, o vacia)

POR QUE EXISTE. Para decir si el ecosistema funciona mejor o peor hace falta un dato por sesion, y nadie lo va a
anotar a mano. Esto lee la transcripcion de la sesion que termina y guarda SOLO CONTEOS: que skills se usaron, cuantos
veredictos hubo y con cuantos bloqueantes y SIN DATOS de cada clase, cuantas fricciones reportaron los agentes, cuantas
Tareas terminaron o fallaron, cuantas preguntas frenaron, cuantos scripts dieron error, cuanto duro. Nunca texto de
la conversacion, nunca datos de personas. bin/tendencia.py compara estas lineas y contesta en una frase.

QUE NO HACE. No escribe en el Cerebro mas que esta linea; no modifica skills; no juzga. Solo biblioteca estandar.
"""

import argparse
import datetime
import json
import os
import re
import sys

OK, _, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMANDO = re.compile(r'<command-name>/([a-z0-9][a-z0-9:-]*)</command-name>')
VEREDICTO = re.compile(r'VEREDICTO-INICIO(.*?)VEREDICTO-FIN', re.S)
BLOQ = re.compile(r'BLOQUEANTES:\s*(\d+)')
SD_MIRAR = re.compile(r'SIN DATOS \(no se pudo mirar\):\s*(\d+)')
SD_DECL = re.compile(r'SIN DATOS \(pendiente declarado\):\s*(\d+)')
FRICCION = re.compile(r'(?i)^\s*#*\s*\**\s*(?:\d+\.\s*)?\**FRICCIONES\**', re.M)
ITEM = re.compile(r'^\s*\d+\.\s', re.M)


def textos_de(d):
    """Todos los textos de una linea de transcripcion (texto del modelo, resultados de herramientas, comandos)."""
    out, usos = [], []
    msg = d.get('message') or {}
    cont = msg.get('content')
    if isinstance(cont, str):
        out.append(cont)
    elif isinstance(cont, list):
        for c in cont:
            if not isinstance(c, dict):
                continue
            t = c.get('type')
            if t == 'text':
                out.append(c.get('text') or '')
            elif t == 'tool_use':
                usos.append((c.get('name') or '', c.get('input') or {}))
            elif t == 'tool_result':
                r = c.get('content')
                if isinstance(r, str):
                    out.append(r)
                elif isinstance(r, list):
                    out += [x.get('text') or '' for x in r if isinstance(x, dict)]
    return out, usos


def fricciones_en(texto):
    n = 0
    for m in FRICCION.finditer(texto):
        bloque = texto[m.end():m.end() + 6000]
        corte = re.search(r'\n\s*#{1,3}\s|\n\s*\*\*[A-ZÁÉÍÓÚ][^\n]{0,40}\*\*\s*\n', bloque)
        if corte:
            bloque = bloque[:corte.start()]
        n += len(ITEM.findall(bloque))
    return n


def medir(ruta):
    m = {'skills': {}, 'veredictos': 0, 'bloqueantes': 0, 'sin_datos_no_mirado': 0, 'sin_datos_declarado': 0,
         'fricciones': 0, 'tareas_terminadas': 0, 'tareas_fallidas': 0, 'preguntas_bloqueantes': 0,
         'errores_de_script': 0, 'scripts_corridos': 0, 'lineas': 0, 'inicio': '', 'fin': ''}
    with open(ruta, 'r', encoding='utf-8', errors='replace') as h:
        for linea in h:
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            m['lineas'] += 1
            ts = d.get('timestamp') or ''
            if ts:
                m['inicio'] = m['inicio'] or ts
                m['fin'] = ts
            textos, usos = textos_de(d)
            for nombre, inp in usos:
                if nombre == 'Skill':
                    sk = str(inp.get('skill') or inp.get('command') or '').strip().lstrip('/').split(':')[-1]
                    if sk:
                        m['skills'][sk] = m['skills'].get(sk, 0) + 1
                elif nombre == 'Bash' or nombre == 'PowerShell':
                    cmd = str(inp.get('command') or '')
                    if re.search(r'\bbin[/\\][\w-]+\.py\b', cmd):
                        m['scripts_corridos'] += 1
            for t in textos:
                for sk in COMANDO.findall(t):
                    sk = sk.split(':')[-1]
                    m['skills'][sk] = m['skills'].get(sk, 0) + 1
                for v in VEREDICTO.findall(t):
                    m['veredictos'] += 1
                    m['bloqueantes'] += sum(int(x) for x in BLOQ.findall(v))
                    m['sin_datos_no_mirado'] += sum(int(x) for x in SD_MIRAR.findall(v))
                    m['sin_datos_declarado'] += sum(int(x) for x in SD_DECL.findall(v))
                m['fricciones'] += fricciones_en(t)
                m['tareas_terminadas'] += len(re.findall(r'^\s*TAREA-TERMINADA\b', t, re.M))
                m['tareas_fallidas'] += len(re.findall(r'^\s*TAREA-FALLIDA\b', t, re.M))
                m['preguntas_bloqueantes'] += len(re.findall(r'^\s*PREGUNTA-ORQUESTADOR:', t, re.M))
                m['errores_de_script'] += len(re.findall(r'SIN DATOS -- error del script', t))
    if m['inicio'] and m['fin']:
        try:
            a = datetime.datetime.fromisoformat(m['inicio'].replace('Z', '+00:00'))
            b = datetime.datetime.fromisoformat(m['fin'].replace('Z', '+00:00'))
            m['duracion_min'] = max(0, int((b - a).total_seconds() // 60))
        except ValueError:
            m['duracion_min'] = None
    else:
        m['duracion_min'] = None
    return m


def main():
    ap = argparse.ArgumentParser(description='Registra una sesion como una linea de metricas.')
    ap.add_argument('--transcripcion', default='')
    ap.add_argument('--nucleo', default=RAIZ)
    ap.add_argument('--salida', default='')
    ap.add_argument('--sesion', default='', help='id de la sesion (por defecto el del hook o el nombre del archivo)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    ruta, sesion, cwd = a.transcripcion, a.sesion, ''
    if not ruta and not sys.stdin.isatty():
        try:
            hook = json.loads(sys.stdin.read() or '{}')
            ruta = hook.get('transcript_path') or ''
            sesion = sesion or hook.get('session_id') or ''
            cwd = hook.get('cwd') or ''
        except ValueError:
            pass
    if not ruta or not os.path.isfile(ruta):
        print('SIN DATOS -- no hay transcripcion que leer (%s)' % (ruta or 'ni --transcripcion ni JSON del hook por stdin'))
        return SIN_DATOS
    m = medir(ruta)
    if m['lineas'] == 0:
        print('SIN DATOS -- la transcripcion esta vacia'); return SIN_DATOS
    sesion = sesion or os.path.splitext(os.path.basename(ruta))[0]
    fila = {'sesion': sesion, 'fecha': (m['fin'] or m['inicio'] or datetime.datetime.now().isoformat())[:19], 'cwd': cwd,
            'duracion_min': m['duracion_min'], 'skills': m['skills'], 'veredictos': m['veredictos'], 'bloqueantes': m['bloqueantes'],
            'sin_datos_no_mirado': m['sin_datos_no_mirado'], 'sin_datos_declarado': m['sin_datos_declarado'], 'fricciones': m['fricciones'],
            'tareas_terminadas': m['tareas_terminadas'], 'tareas_fallidas': m['tareas_fallidas'], 'preguntas_bloqueantes': m['preguntas_bloqueantes'],
            'errores_de_script': m['errores_de_script'], 'scripts_corridos': m['scripts_corridos'], 'escrito_por': 'bin/registrar-sesion.py'}
    salida = a.salida or os.path.join(a.nucleo, 'cerebro-digital', 'configuracion-ia', 'sesiones.jsonl')
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    lineas = []
    if os.path.isfile(salida):
        with open(salida, 'r', encoding='utf-8', errors='replace') as h:
            lineas = [l for l in h.read().split('\n') if l.strip()]
    lineas = [l for l in lineas if ('"sesion": "%s"' % sesion) not in l]   # idempotente: la misma sesion se reemplaza
    lineas.append(json.dumps(fila, ensure_ascii=True, sort_keys=True))
    with open(salida, 'w', encoding='utf-8', newline='\n') as h:
        h.write('\n'.join(lineas) + '\n')
    if a.json:
        print(json.dumps(fila, ensure_ascii=False, indent=1))
    else:
        print('OK -- sesion %s registrada en %s: %d skill(s) usadas, %d veredicto(s) (%d bloqueantes, %d SIN DATOS sin mirar), %d friccion(es), %d Tarea(s) terminadas, %d fallidas, %d pregunta(s), %d error(es) de script, %s min' % (
            sesion[:12], os.path.relpath(salida, a.nucleo) if salida.startswith(a.nucleo) else salida, sum(m['skills'].values()), m['veredictos'], m['bloqueantes'],
            m['sin_datos_no_mirado'], m['fricciones'], m['tareas_terminadas'], m['tareas_fallidas'], m['preguntas_bloqueantes'], m['errores_de_script'], m['duracion_min'] if m['duracion_min'] is not None else '?'))
        print('  Lo que este script NO guarda: texto de la conversacion, codigo, datos de personas. Solo conteos.')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
