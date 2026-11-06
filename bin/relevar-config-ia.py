#!/usr/bin/env python3
"""Releva la configuracion de IA que YA tiene un proyecto (Claude Code, Gemini, Cursor, Copilot, opencode)
y propone donde va cada cosa al adoptar este template. SOLO LECTURA.

    python bin/relevar-config-ia.py <ruta-del-proyecto> [--nucleo <ruta del repositorio del Cerebro>] [--json]

Tres estados, nunca dos:  0 = relevamiento listo   1 = (no aplica)   2 = SIN DATOS (la ruta no existe o no tiene configuracion de IA)

POR QUE EXISTE. Un proyecto que ya trabaja con Claude Code trae su CLAUDE.md, sus skills, sus comandos, su
.mcp.json y, a veces, reglas que chocan con las del template (idioma, TDD, commits). Leerlo todo a mano gasta
tokens y se olvida la mitad. Esto lo lista en segundos, saca de las instrucciones lo que es dato (comandos de
build y test, reglas duras, menciones de idioma) y dice a que archivo del Cerebro iria cada cosa. La
decision sigue siendo de una persona: el metodo esta en desarrollo/references/metodo/adoptar-proyecto-existente.md.

QUE NO HACE. No modifica nada, no copia reglas al Cerebro, no resuelve colisiones: las marca. Solo biblioteca
estandar. ASCII en el codigo.
"""

import argparse
import glob
import json
import os
import re
import sys

OK, _, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASURA = {'.git', 'node_modules', 'target', 'build', 'dist', 'vendor', '.venv', 'venv', '__pycache__', '.idea'}
INSTRUCCIONES = ('CLAUDE.md', 'CLAUDE.local.md', 'AGENTS.md', 'GEMINI.md', '.cursorrules', '.windsurfrules', '.clinerules')
COMANDO = re.compile(r'^\s*(?:\$\s*)?((?:npm|pnpm|yarn|bun|npx|mvn|\./mvnw|mvnw|gradle|\./gradlew|gradlew|pytest|python -m pytest|python3? -m pytest|go (?:test|build|run)|cargo (?:test|build|run)|dotnet (?:test|build|run)|make|php artisan|bundle exec|rails|flutter|swift (?:test|build))\b[^\n`]*)')
REGLA = re.compile(r'(?i)\b(always|never|must|do not|don\'t|siempre|nunca|debe|debes|prohibido|no uses|no usar|obligatorio|no negociable)\b|^\s*[-*]\s+\*\*[^*]{3,80}\*\*')
COMANDO_INLINE = re.compile(r'`((?:npm|pnpm|yarn|bun|npx|mvn|gradle|pytest|cargo|go|dotnet|make|python3?|php|bundle|rails|flutter|swift)\s[^`]{1,80})`')
IDIOMA = re.compile(r'(?i)\b(in english|english only|en ingl[eé]s|respond in english|write in english)\b')


def leer(p):
    try:
        with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
            return h.read()
    except OSError:
        return ''


def frontmatter(texto):
    m = re.match(r'---\n(.*?)\n---', texto, re.S)
    if not m:
        return {}
    d = {}
    for l in m.group(1).split('\n'):
        mm = re.match(r'^(name|description):\s*(.*)$', l)
        if mm:
            d[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return d


def recorrer(raiz):
    for base, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in BASURA]
        rel = os.path.relpath(base, raiz).replace(os.sep, '/')
        yield base, rel if rel != '.' else '', files


def main():
    ap = argparse.ArgumentParser(description='Releva la configuracion de IA de un proyecto existente.')
    ap.add_argument('ruta')
    ap.add_argument('--nucleo', default=RAIZ, help='repositorio del Cerebro, para detectar colisiones de nombres de skills')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    raiz = os.path.abspath(a.ruta)
    if not os.path.isdir(raiz):
        print('SIN DATOS -- no existe la carpeta %s' % raiz)
        return SIN_DATOS

    instrucciones, skills, comandos_cfg, agentes, mcp, otros = [], [], [], [], [], []
    comandos, reglas, idioma = [], [], []
    for base, rel, files in recorrer(raiz):
        for f in files:
            p = os.path.join(base, f)
            r = (rel + '/' + f) if rel else f
            if f in INSTRUCCIONES or r in ('.github/copilot-instructions.md',) or '/.cursor/rules/' in '/' + r or '/.claude/rules/' in '/' + r:
                t = leer(p)
                enc = [l.strip('# ').strip() for l in t.split('\n') if l.startswith('#')]
                instrucciones.append({'archivo': r, 'lineas': t.count('\n') + 1, 'encabezados': enc[:25]})
                for n, l in enumerate(t.split('\n'), 1):
                    m = COMANDO.match(l.strip('`'))
                    if m:
                        comandos.append({'archivo': r, 'linea': n, 'comando': m.group(1).strip()[:120]})
                    else:
                        for mi in COMANDO_INLINE.finditer(l):
                            comandos.append({'archivo': r, 'linea': n, 'comando': mi.group(1).strip()[:120]})
                    if REGLA.search(l) and len(l.strip()) > 15 and not l.strip().startswith('#'):
                        reglas.append({'archivo': r, 'linea': n, 'texto': l.strip()[:160]})
                    if IDIOMA.search(l):
                        idioma.append({'archivo': r, 'linea': n, 'texto': l.strip()[:120]})
            elif f == 'SKILL.md' and ('/.claude/skills/' in '/' + r or '/.agents/skills/' in '/' + r or '/.opencode/skills/' in '/' + r or '/.gemini/skills/' in '/' + r):
                fm = frontmatter(leer(p))
                skills.append({'archivo': r, 'name': fm.get('name', os.path.basename(base)), 'description': fm.get('description', '')[:160]})
            elif '/.claude/commands/' in '/' + r and f.endswith('.md'):
                comandos_cfg.append(r)
            elif '/.claude/agents/' in '/' + r and f.endswith('.md'):
                agentes.append(r)
            elif f in ('.mcp.json',) or r in ('.gemini/settings.json', '.claude/settings.json', '.claude/settings.local.json', 'opencode.json'):
                t = leer(p)
                servidores = []
                try:
                    d = json.loads(t)
                    servidores = list((d.get('mcpServers') or d.get('mcp') or {}).keys())
                except ValueError:
                    pass
                (mcp if servidores or f == '.mcp.json' else otros).append({'archivo': r, 'servidores': servidores})

    if not (instrucciones or skills or comandos_cfg or agentes or mcp or otros):
        print('SIN DATOS -- %s no tiene configuracion de IA (CLAUDE.md, AGENTS.md, skills, .mcp.json): se absorbe como cualquier aplicacion (absorber-aplicacion).' % raiz)
        return SIN_DATOS

    nucleo_skills = set()
    if a.nucleo and os.path.isdir(os.path.join(a.nucleo, 'cerebro-digital', 'configuracion-ia', 'skills')):
        nucleo_skills = set(os.listdir(os.path.join(a.nucleo, 'cerebro-digital', 'configuracion-ia', 'skills')))
        for lado in ('back', 'front'):
            d = os.path.join(a.nucleo, lado, '.claude', 'skills')
            if os.path.isdir(d):
                nucleo_skills.update(os.listdir(d))
    colisiones = sorted(set(s['name'] for s in skills) & nucleo_skills)

    destinos = [
        ('Comandos de build y test (%d)' % len(comandos), 'tdd-stack-back.md / tdd-stack-front.md de la skill desarrollo, y el README del repo', 'son el dato que el verificador necesita para correr la suite'),
        ('Reglas duras (%d)' % len(reglas), 'arquitectura/esqueleto-proyectos.md (C8) o decisiones.md como DEC-nnn; lo que choque con AGENTS.md se pregunta', 'una regla del repo que contradiga al Cerebro la gana el Cerebro (C6), pero antes se decide'),
        ('Menciones de idioma (%d)' % len(idioma), 'CHOQUE con AGENTS.md (todo en espanol) y con C3 (nombres): se decide en el encuadre', 'si el proyecto escribe en ingles, la regla del template se adapta o se declara la excepcion'),
        ('Skills propias (%d, %d colisiones)' % (len(skills), len(colisiones)), 'se quedan en el repo como skills scoped (nested); una colision de nombre con las del nucleo se renombra', 'dos skills con el mismo nombre y distinto contenido dejan de ser deterministas'),
        ('Comandos y agentes de Claude (%d, %d)' % (len(comandos_cfg), len(agentes)), 'se quedan en el repo; los que dupliquen una skill del nucleo se retiran', 'cada pregunta, un solo control'),
        ('Servidores MCP (%d archivos)' % len(mcp), 'por maquina (integracion-*/ del Cerebro); el .mcp.json del repo no se versiona con tokens', 'los tokens nunca van en un archivo'),
        ('Memoria del asistente', 'no se migra: el Cerebro pasa a ser la memoria compartida; lo durable que haya en CLAUDE.md va a aplicacion/aprendizajes.md', 'una memoria por maquina no es fuente de verdad'),
    ]
    salida = {'ruta': raiz, 'instrucciones': instrucciones, 'comandos': comandos, 'reglas_duras': reglas, 'idioma': idioma, 'skills': skills,
              'colisiones_de_nombre': colisiones, 'comandos_claude': comandos_cfg, 'agentes_claude': agentes, 'mcp': mcp, 'otros': otros,
              'destinos': [{'que': q, 'destino': d, 'por_que': p} for q, d, p in destinos]}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return OK
    print('RELEVAMIENTO de configuracion de IA en %s' % raiz)
    print('  Instrucciones (%d): ' % len(instrucciones) + (', '.join('%s (%d lineas)' % (i['archivo'], i['lineas']) for i in instrucciones) or 'ninguna'))
    print('  Comandos de build/test encontrados (%d):' % len(comandos))
    for c in comandos[:15]:
        print('    - %s  (%s:%d)' % (c['comando'], c['archivo'], c['linea']))
    print('  Reglas duras (%d):' % len(reglas))
    for r in reglas[:15]:
        print('    - %s  (%s:%d)' % (r['texto'], r['archivo'], r['linea']))
    if idioma:
        print('  CHOQUE de idioma (%d): el proyecto pide ingles; el template, espanol. Se decide en el encuadre.' % len(idioma))
    print('  Skills propias (%d): ' % len(skills) + (', '.join(s['name'] for s in skills) or 'ninguna') + (('  | COLISIONES con el nucleo: ' + ', '.join(colisiones)) if colisiones else ''))
    print('  Comandos de Claude (%d), agentes (%d), MCP (%d: %s)' % (len(comandos_cfg), len(agentes), len(mcp), ', '.join(s for m in mcp for s in m['servidores']) or '-'))
    print('  Destino propuesto de cada cosa:')
    for q, d, p in destinos:
        print('    - %s -> %s. (%s)' % (q, d, p))
    print('  Lo que este script NO hace: no copia nada al Cerebro ni resuelve colisiones; el metodo es adoptar-proyecto-existente.md y la decision es de una persona.')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
