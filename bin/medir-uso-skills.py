#!/usr/bin/env python3
"""Mide que skills del ecosistema se USAN de verdad, leyendo las transcripciones locales de Claude Code. SOLO LECTURA.

    python -B bin/medir-uso-skills.py [--dias 60] [--proyecto <ruta del nucleo o de un repo>] [--transcripciones <carpeta>] [--json]

Tres estados, nunca dos:  0 = medicion lista   1 = (no aplica)   2 = SIN DATOS (no hay transcripciones que leer)

POR QUE EXISTE. El proyecto de origen termino con skills de mas: cada una pedia cosas, se pisaban y el codigo
se sobregiraba. Sacar skills "a ojo" es tan malo como agregarlas a ojo. Claude Code guarda cada sesion como
un .jsonl por proyecto (~/.claude/projects/<proyecto>/ y, con Orca, su perfil); ahi queda cada invocacion de
una skill por el modelo (tool_use "Skill") y cada comando /nombre que escribio la persona. Este script las
cuenta: cuantas veces, por quien, cuando fue la ultima, y cruza con las skills del ecosistema (canonicas y
scoped) con su costo aproximado de contexto. Lo que no se usa en --dias y pesa, es candidato a poda; la
propuesta la arma mejorar-ecosistema y la decide una persona.

QUE NO HACE. No borra nada, no lee el contenido de las conversaciones (solo nombres de skills y fechas), no
juzga: lista. Si Claude Code guarda las transcripciones en otro lado, se pasa --transcripciones. Solo biblioteca
estandar. ASCII puro.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

OK, _, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATAS = [os.path.expanduser('~/.claude/projects'),
              os.path.expanduser('~/AppData/Roaming/orca/claude-profiles')]
COMANDO = re.compile(r'<command-name>/([a-z0-9][a-z0-9:-]*)</command-name>')


def skills_del_ecosistema():
    out = {}
    for base, origen in ((os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills'), 'canonica'),
                         (os.path.join(RAIZ, 'back', '.claude', 'skills'), 'back'),
                         (os.path.join(RAIZ, 'front', '.claude', 'skills'), 'front')):
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            p = os.path.join(base, d, 'SKILL.md')
            if os.path.isfile(p):
                try:
                    chars = sum(os.path.getsize(f) for f in glob.glob(os.path.join(base, d, '**', '*.md'), recursive=True))
                except OSError:
                    chars = 0
                out.setdefault(d, {'nombre': d, 'origen': [], 'tokens_aprox': chars // 4})
                out[d]['origen'].append(origen)
    return out


def transcripciones(carpetas):
    archivos = []
    for c in carpetas:
        if not os.path.isdir(c):
            continue
        archivos += glob.glob(os.path.join(c, '**', '*.jsonl'), recursive=True)
    return sorted(set(archivos))


def main():
    ap = argparse.ArgumentParser(description='Uso real de las skills, leido de las transcripciones de Claude Code.')
    ap.add_argument('--dias', type=int, default=60)
    ap.add_argument('--proyecto', default='', help='si se pasa, cuenta solo sesiones cuyo cwd empieza por esta ruta')
    ap.add_argument('--transcripciones', action='append', default=[], help='carpeta(s) con .jsonl; por defecto las de Claude Code y Orca')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    carpetas = a.transcripciones or CANDIDATAS
    archivos = transcripciones(carpetas)
    if not archivos:
        print('SIN DATOS -- no encontre transcripciones .jsonl en: %s' % ', '.join(carpetas))
        return SIN_DATOS
    desde = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.dias)
    proyecto = os.path.normcase(os.path.abspath(a.proyecto)) if a.proyecto else ''
    uso = {}
    sesiones, leidas = set(), 0

    def anotar(nombre, quien, fecha, cwd):
        u = uso.setdefault(nombre, {'modelo': 0, 'persona': 0, 'ultima': '', 'proyectos': set()})
        u[quien] += 1
        if fecha > u['ultima']:
            u['ultima'] = fecha
        if cwd:
            u['proyectos'].add(cwd)

    for f in archivos:
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as h:
                for linea in h:
                    if '"Skill"' not in linea and '<command-name>' not in linea:
                        continue
                    try:
                        d = json.loads(linea)
                    except ValueError:
                        continue
                    ts = d.get('timestamp') or ''
                    cwd = d.get('cwd') or ''
                    if proyecto and not os.path.normcase(os.path.abspath(cwd)).startswith(proyecto):
                        continue
                    try:
                        cuando = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except ValueError:
                        cuando = None
                    if cuando and cuando < desde:
                        continue
                    sesiones.add(d.get('sessionId') or f)
                    fecha = ts[:10]
                    msg = d.get('message') or {}
                    cont = msg.get('content')
                    if isinstance(cont, list):
                        for c in cont:
                            if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') == 'Skill':
                                inp = c.get('input') or {}
                                nombre = str(inp.get('skill') or inp.get('command') or '').strip().lstrip('/')
                                if nombre:
                                    anotar(nombre.split(':')[-1], 'modelo', fecha, cwd)
                            elif isinstance(c, dict) and c.get('type') == 'text':
                                for m in COMANDO.finditer(c.get('text') or ''):
                                    anotar(m.group(1).split(':')[-1], 'persona', fecha, cwd)
                    elif isinstance(cont, str):
                        for m in COMANDO.finditer(cont):
                            anotar(m.group(1).split(':')[-1], 'persona', fecha, cwd)
            leidas += 1
        except OSError:
            continue

    eco = skills_del_ecosistema()
    filas = []
    for nombre, info in sorted(eco.items()):
        u = uso.get(nombre, {'modelo': 0, 'persona': 0, 'ultima': '', 'proyectos': set()})
        filas.append({'skill': nombre, 'origen': '+'.join(info['origen']), 'tokens_aprox': info['tokens_aprox'],
                      'por_modelo': u['modelo'], 'por_persona': u['persona'], 'ultima_vez': u['ultima'] or '-',
                      'proyectos': len(u['proyectos'])})
    sin_uso = [f for f in filas if f['por_modelo'] + f['por_persona'] == 0]
    ajenas = sorted((n, v['modelo'] + v['persona']) for n, v in uso.items() if n not in eco)
    salida = {'dias': a.dias, 'transcripciones': leidas, 'sesiones': len(sesiones), 'proyecto': a.proyecto or '(todos)',
              'skills': filas, 'sin_uso': [f['skill'] for f in sin_uso],
              'tokens_sin_uso': sum(f['tokens_aprox'] for f in sin_uso),
              'skills_de_afuera_usadas': [{'skill': n, 'veces': v} for n, v in ajenas],
              'no_mira': ['si la skill se disparo por contexto sin invocacion explicita (Claude Code no lo registra como tool_use)',
                          'si fue util: eso lo mira mejorar-ecosistema con la persona',
                          'sesiones de otras herramientas (Gemini CLI, opencode, Antigravity) que no guardan .jsonl aca']}
    if a.json:
        salida['skills'] = filas
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return OK
    print('USO DE SKILLS en los ultimos %d dias -- %d transcripciones, %d sesiones (%s)' % (a.dias, leidas, len(sesiones), a.proyecto or 'todos los proyectos'))
    print('  %-28s %-14s %7s %7s %10s %6s' % ('skill', 'origen', 'modelo', 'persona', 'ultima', 'tokens'))
    for f in sorted(filas, key=lambda x: (-(x['por_modelo'] + x['por_persona']), x['skill'])):
        print('  %-28s %-14s %7d %7d %10s %6d' % (f['skill'], f['origen'], f['por_modelo'], f['por_persona'], f['ultima_vez'], f['tokens_aprox']))
    print('  Sin uso en %d dias: %d skill(s), ~%d tokens de contexto si se cargaran enteras: %s' % (a.dias, len(sin_uso), salida['tokens_sin_uso'], ', '.join(salida['sin_uso']) or '-'))
    if ajenas:
        print('  Skills usadas que NO son del ecosistema: ' + ', '.join('%s (%d)' % (n, v) for n, v in ajenas[:12]))
    print('  Lo que este script NO mira: ' + '; '.join(salida['no_mira']) + '.')
    print('  Una skill sin uso NO se borra sola: mejorar-ecosistema arma la propuesta con esta evidencia y la decide una persona.')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
