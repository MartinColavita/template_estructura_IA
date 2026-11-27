#!/usr/bin/env python3
"""Prueba de bin/sesion-proyecto.py sin abrir Claude: el comando que arma, el chequeo estatico de los agentes de
sesion principal y la lectura del evento init de una sesion (con archivos de mentira).
Se corre:  python -B bin/probar-sesion-proyecto.py   -> OK o FALLA, con el detalle de cada caso."""

import importlib.util
import json
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def cargar():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('sesion_proyecto', os.path.join(AQUI, 'sesion-proyecto.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)
    return p


def agente(raiz, nombre, desc):
    escribir(raiz, 'cerebro-digital/configuracion-ia/agentes/%s.md' % nombre,
             '---\nname: %s\ndescription: %s\ntools: Read\n---\n' % (nombre, desc))


def init(ruta, **campos):
    ev = {'type': 'system', 'subtype': 'init', 'mcp_servers': [], 'plugins': [], 'skills': [], 'agents': []}
    ev.update(campos)
    with open(ruta, 'w', encoding='utf-8') as h:
        h.write('Warning: algo que no es JSON\n')
        h.write(json.dumps({'type': 'system', 'subtype': 'hook_started'}) + '\n')
        h.write(json.dumps(ev) + '\n')


def main():
    sp = cargar()
    print('== sesion-proyecto: el comando')
    tmp = tempfile.mkdtemp(prefix='probar-sesion-')
    try:
        cmd = sp.comando(tmp, ['--agent', 'orquestador-seguridad'])
        caso('sin tu configuracion de usuario', cmd[cmd.index('--setting-sources') + 1] == 'project,local', str(cmd))
        caso('solo los MCP que se le pasan', '--strict-mcp-config' in cmd)
        caso('sin .mcp.json en el proyecto: ningun MCP', json.loads(cmd[cmd.index('--mcp-config') + 1]) == {'mcpServers': {}}, str(cmd))
        caso('apaga los conectores de claude.ai', json.loads(cmd[cmd.index('--settings') + 1]).get('disableClaudeAiConnectors') is True)
        caso('lo que pide la persona va al final (--agent)', cmd[-2:] == ['--agent', 'orquestador-seguridad'], str(cmd))
        escribir(tmp, '.mcp.json', '{"mcpServers": {"del-proyecto": {"command": "x"}}}')
        cmd = sp.comando(tmp, [])
        caso('con .mcp.json: usa ese archivo', cmd[cmd.index('--mcp-config') + 1] == os.path.join(tmp, '.mcp.json'), str(cmd))

        print('== sesion-proyecto: agentes de sesion principal')
        rc, _ = sp.chequeo_estatico(tmp)
        caso('sin agentes: SIN DATOS (2)', rc == 2)
        agente(tmp, 'orquestador-x', 'Orquestador de algo. Se usa SOLO como sesión principal (claude --agent orquestador-x).')
        agente(tmp, 'worker-y', 'Worker que produce. No pregunta.')
        escribir(tmp, '.claude/settings.json', '{"hooks": {}}')
        rc, msgs = sp.chequeo_estatico(tmp)
        caso('orquestador sin bloquear como subagente: HALLAZGO (1) y lo nombra', rc == 1 and any('orquestador-x' in m for m in msgs), str(msgs))
        caso('el worker no se exige', not any('worker-y' in m for m in msgs), str(msgs))
        escribir(tmp, '.claude/settings.json', '{"permissions": {"deny": ["Agent(orquestador-x)"]}}')
        rc, msgs = sp.chequeo_estatico(tmp)
        caso('bloqueado con deny Agent(nombre): OK (0)', rc == 0, str(msgs))
        escribir(tmp, '.claude/settings.json', '{"permissions": {"deny": ["Agent(worker-y)"]}}')
        rc, msgs = sp.chequeo_estatico(tmp)
        caso('bloquear un worker no cuenta por el orquestador', rc == 1, str(msgs))
        escribir(tmp, '.claude/settings.json', '{ esto no es json')
        rc, msgs = sp.chequeo_estatico(tmp)
        caso('settings.json roto: HALLAZGO, no OK', rc == 1, str(msgs))

        print('== sesion-proyecto: lo que cargo la sesion (evento init)')
        os.makedirs(os.path.join(tmp, 'cerebro-digital', 'configuracion-ia', 'skills', 'nuestra'), exist_ok=True)
        personales = os.path.join(tmp, 'personales')
        os.makedirs(os.path.join(personales, 'mia'))
        ev = os.path.join(tmp, 'init.jsonl')
        limpio = dict(mcp_servers=[{'name': 'del-proyecto', 'status': 'connected'}],
                      plugins=[{'name': 'cc-plugin-x', 'path': 'builtin'}],
                      skills=['nuestra', 'debug', 'loop'], agents=['orquestador-x', 'Explore'])
        init(ev, **limpio)
        rc, msgs = sp.leer_init(ev, tmp, personales)
        caso('solo lo del proyecto y lo que trae la herramienta: OK (0)', rc == 0, str(msgs))
        for nombre, extra, quien in (
                ('un MCP de la maquina', {'mcp_servers': limpio['mcp_servers'] + [{'name': 'gitlab-otro'}]}, 'gitlab-otro'),
                ('un conector de claude.ai', {'mcp_servers': [{'name': 'claude.ai Gmail'}]}, 'claude.ai Gmail'),
                ('un plugin instalado', {'plugins': [{'name': 'design', 'path': 'C:/x/plugins/design'}]}, 'design'),
                ('una skill de plugin (con dos puntos)', {'skills': ['nuestra', 'design:critique']}, 'design:critique'),
                ('una skill personal', {'skills': ['nuestra', 'mia']}, 'mia'),
                ('un agente de plugin', {'agents': ['feature-dev:code-reviewer']}, 'feature-dev:code-reviewer')):
            d = dict(limpio)
            d.update(extra)
            init(ev, **d)
            rc, msgs = sp.leer_init(ev, tmp, personales)
            caso('%s: HALLAZGO y lo nombra' % nombre, rc == 1 and any(quien in m for m in msgs), str(msgs))
        with open(ev, 'w', encoding='utf-8') as h:
            h.write('Error: no se pudo iniciar\n')
        rc, _ = sp.leer_init(ev, tmp, personales)
        caso('sin evento init: SIN DATOS (2), nunca OK', rc == 2)

        print('== sesion-proyecto: este repositorio')
        rc, msgs = sp.chequeo_estatico(RAIZ)
        caso('los orquestadores de ESTE repo estan bloqueados como subagentes', rc == 0, str(msgs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    malos = [e for e in ESPERADOS if not e[1]]
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not malos else 'FALLA', len(ESPERADOS) - len(malos), len(ESPERADOS)))
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
