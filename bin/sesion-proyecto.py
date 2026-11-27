#!/usr/bin/env python3
"""Abre una sesion de Claude Code que carga SOLO lo del proyecto, y verifica que asi sea.

    python -I bin/sesion-proyecto.py [-- argumentos para claude]      abre la sesion aislada
    python -I bin/sesion-proyecto.py --agent orquestador-seguridad     la sesion de una funcion, aislada
    python -I bin/sesion-proyecto.py --comando                         muestra el comando, sin abrir nada
    python -I bin/sesion-proyecto.py --verificar                       chequeo estatico (sin abrir Claude)
    python -I bin/sesion-proyecto.py --verificar --en-vivo             ademas abre una sesion corta y lee que cargo

Tres salidas, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS (sin agentes, sin claude, sin evento init)

POR QUE EXISTE. En una maquina con muchos plugins, MCP y conectores, todo eso entra a cualquier sesion: las
descripciones de las puertas del proyecto dejan de llegar al modelo (el listado de skills tiene cupo) y quedan a
mano herramientas de otros proyectos. Medido el 2026-11-25 en una maquina real: la sesion normal cargaba 45
servidores MCP, 339 herramientas MCP y 119 skills; la aislada, 0, 0 y 62 (38 del proyecto y las de la herramienta).
Y un orquestador de funcion lanzado como SUBAGENTE pierde su lista de herramientas (Claude Code ignora Agent(...)
dentro de un subagente): por eso se bloquea en .claude/settings.json con deny Agent(<nombre>), que impide lanzarlo
como subagente y deja abrirlo con claude --agent (probado en la misma fecha).

QUE HACE.
  - Abre:  claude --setting-sources project,local --strict-mcp-config --mcp-config <.mcp.json o ninguno>
           --settings {"disableClaudeAiConnectors": true} [lo que pida la persona].
    Sin la configuracion de usuario no entran los plugins ni las skills personales; con --strict-mcp-config, solo
    los MCP del .mcp.json del proyecto; los conectores de claude.ai, apagados. Las skills y plugins que trae la
    propia herramienta quedan (no son de la maquina).
  - --verificar: cada agente de cerebro-digital/configuracion-ia/agentes/ cuya descripcion dice "sesion principal"
    tiene que estar bloqueado como subagente en .claude/settings.json (permissions.deny "Agent(<nombre>)").
  - --en-vivo: corre una sesion de una vuelta en modo stream-json y lee el evento init: ningun MCP fuera del
    .mcp.json, ningun plugin instalado, ninguna skill de plugin ni personal, ningun agente de plugin.

QUE NO HACE. No toca la configuracion de la persona ni la del proyecto. No lee ni muestra secretos. Solo
biblioteca estandar. ASCII puro.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTES = os.path.join('cerebro-digital', 'configuracion-ia', 'agentes')
SKILLS = os.path.join('cerebro-digital', 'configuracion-ia', 'skills')
SESION_PRINCIPAL = re.compile(r'sesi(o|ó)n principal', re.I)


def comando(raiz, extra):
    """La linea de claude para una sesion aislada del proyecto (lista de argumentos, sin el ejecutable)."""
    mcp = os.path.join(raiz, '.mcp.json')
    return (['--setting-sources', 'project,local', '--strict-mcp-config',
             '--mcp-config', mcp if os.path.isfile(mcp) else json.dumps({'mcpServers': {}}),
             '--settings', json.dumps({'disableClaudeAiConnectors': True})] + list(extra))


def _descripcion(texto):
    m = re.match(r'---\n(.*?)\n---', texto.replace('\r\n', '\n'), re.S)
    if not m:
        return ''
    d = re.search(r'^description:\s*(.*?)(?=^\w[\w-]*:|\Z)', m.group(1), re.M | re.S)
    return d.group(1) if d else ''


def chequeo_estatico(raiz):
    """(codigo, mensajes): los agentes de sesion principal, bloqueados como subagentes."""
    carpeta = os.path.join(raiz, AGENTES)
    if not os.path.isdir(carpeta):
        return SIN_DATOS, ['no hay %s' % AGENTES.replace(os.sep, '/')]
    principales = []
    for f in sorted(os.listdir(carpeta)):
        if f.endswith('.md'):
            texto = open(os.path.join(carpeta, f), encoding='utf-8', errors='replace').read()
            if SESION_PRINCIPAL.search(_descripcion(texto)):
                principales.append(f[:-3])
    if not principales:
        return SIN_DATOS, ['ningun agente dice ser de sesion principal']
    try:
        conf = json.load(open(os.path.join(raiz, '.claude', 'settings.json'), encoding='utf-8'))
    except FileNotFoundError:
        conf = {}
    except ValueError as e:
        return HALLAZGO, ['.claude/settings.json no es JSON valido (%s): no se puede saber que esta bloqueado' % e]
    deny = set((conf.get('permissions') or {}).get('deny') or [])
    faltan = [a for a in principales if 'Agent(%s)' % a not in deny]
    if faltan:
        return HALLAZGO, ['%s: se usa solo como sesion principal y se puede lanzar como subagente (sin su lista de '
                          'herramientas). Falta "Agent(%s)" en permissions.deny de .claude/settings.json' % (a, a)
                          for a in faltan]
    return OK, ['%d agente(s) de sesion principal bloqueados como subagentes: %s' % (len(principales), ', '.join(principales))]


def leer_init(ruta, raiz, personales):
    """(codigo, mensajes): lo que cargo una sesion, leido de su evento init (salida stream-json)."""
    ev = None
    for linea in open(ruta, encoding='utf-8', errors='replace'):
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get('type') == 'system' and d.get('subtype') == 'init':
            ev = d
            break
    if ev is None:
        return SIN_DATOS, ['la sesion no informo que cargo (sin evento init)']
    del_proyecto = set()
    try:
        del_proyecto = set((json.load(open(os.path.join(raiz, '.mcp.json'), encoding='utf-8')).get('mcpServers') or {}))
    except (OSError, ValueError):
        pass
    propias = set(os.listdir(os.path.join(raiz, SKILLS))) if os.path.isdir(os.path.join(raiz, SKILLS)) else set()
    suyas = set(os.listdir(personales)) - propias if personales and os.path.isdir(personales) else set()
    malos = []
    for m in ev.get('mcp_servers') or []:
        n = m.get('name') if isinstance(m, dict) else m
        if n not in del_proyecto:
            malos.append('MCP que no es del proyecto: %s' % n)
    for p in ev.get('plugins') or []:
        if isinstance(p, dict) and p.get('path') != 'builtin':
            malos.append('plugin instalado en la maquina: %s' % p.get('name'))
    for s in ev.get('skills') or []:
        if ':' in s:
            malos.append('skill de un plugin: %s' % s)
        elif s in suyas:
            malos.append('skill personal de la maquina: %s' % s)
    for a in ev.get('agents') or []:
        if ':' in a:
            malos.append('agente de un plugin: %s' % a)
    if malos:
        return HALLAZGO, malos
    return OK, ['la sesion cargo %d MCP, %d plugin(s) de la herramienta, %d skills y %d agentes, todos del proyecto o de '
                'la herramienta' % (len(ev.get('mcp_servers') or []), len(ev.get('plugins') or []),
                                    len(ev.get('skills') or []), len(ev.get('agents') or []))]


def _claude():
    return shutil.which('claude')


def en_vivo(raiz):
    exe = _claude()
    if not exe:
        return SIN_DATOS, ['no se encontro el comando claude en el PATH']
    salida = os.path.join(tempfile.mkdtemp(prefix='sesion-proyecto-'), 'init.jsonl')
    with open(salida, 'w', encoding='utf-8') as h:
        try:
            subprocess.run([exe, '-p', 'Responde solo: ok', '--output-format', 'stream-json', '--verbose',
                            '--max-turns', '1'] + comando(raiz, []), cwd=raiz, stdout=h, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, timeout=240)
        except (OSError, subprocess.TimeoutExpired) as e:
            return SIN_DATOS, ['la sesion de prueba no corrio: %s' % e]
    return leer_init(salida, raiz, os.path.join(os.path.expanduser('~'), '.claude', 'skills'))


def main():
    args = sys.argv[1:]
    if '--' in args:
        args = args[:args.index('--')] + args[args.index('--') + 1:]
    if '--verificar' in args:
        rc, msgs = chequeo_estatico(RAIZ)
        if '--en-vivo' in args and rc != HALLAZGO:
            rc2, msgs2 = en_vivo(RAIZ)
            rc, msgs = max(rc, rc2) if HALLAZGO not in (rc, rc2) else HALLAZGO, msgs + msgs2
        print('%s -- sesion del proyecto' % ('OK' if rc == OK else 'HALLAZGO' if rc == HALLAZGO else 'SIN DATOS'))
        for m in msgs:
            print('  - ' + m)
        print('  Lo que este script NO mira: las skills y plugins que trae Claude Code (no se pueden sacar) ni lo que '
              'cada MCP del proyecto hace por dentro.')
        return rc
    linea = comando(RAIZ, [a for a in args if a != '--comando'])
    if '--comando' in args:
        print('claude ' + ' '.join(("'%s'" % a) if (' ' in a or '{' in a) else a for a in linea))
        return OK
    exe = _claude()
    if not exe:
        print('SIN DATOS -- no se encontro el comando claude en el PATH')
        return SIN_DATOS
    return subprocess.call([exe] + linea, cwd=RAIZ)


if __name__ == '__main__':
    sys.exit(main())
