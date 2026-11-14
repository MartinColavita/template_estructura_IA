#!/usr/bin/env python3
"""Prueba del hook .githooks/pre-commit en una copia del repo con git: lo que frena y lo que deja pasar.
Copia lo versionado (y lo nuevo sin ignorar) a una carpeta temporal, hace un primer commit sin hook, lo activa y prueba.
Se corre:  python -B bin/probar-hook.py   -> OK o FALLA, con el detalle de cada caso. Tarda unos segundos por commit."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'core.autocrlf=false'] + list(args),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


def agregar(repo, rel, texto):
    with open(os.path.join(repo, rel), 'a', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def commit(repo):
    r = git(repo, 'commit', '-qm', 'prueba')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== hook pre-commit')
    if shutil.which('git') is None or shutil.which('bash') is None:
        print('SIN DATOS -- hacen falta git y bash en el PATH.')
        return 2
    archivos = git(RAIZ, 'ls-files', '-z', '-co', '--exclude-standard').stdout.split('\0')
    tmp = tempfile.mkdtemp(prefix='probar-hook-')
    repo = os.path.join(tmp, 'repo')
    for rel in (a for a in archivos if a):
        origen = os.path.join(RAIZ, rel)
        if os.path.isfile(origen):
            os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
            shutil.copy2(origen, os.path.join(repo, rel))
    for destino in ('.claude/agents', '.agents/agents'):   # los espejos de agentes no se versionan: se generan
        shutil.copytree(os.path.join(repo, 'cerebro-digital', 'configuracion-ia', 'agentes'), os.path.join(repo, destino))
    git(repo, 'init', '-q')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-qm', 'base', '--no-verify')
    git(repo, 'config', 'core.hooksPath', '.githooks')

    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- prueba -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('un commit sano pasa', rc == 0, out[-400:])

    with open(os.path.join(repo, 'nuevo.md'), 'wb') as h:
        h.write(b'\xef\xbb\xbfcon BOM\n')
    git(repo, 'add', 'nuevo.md')
    rc, out = commit(repo)
    caso('un archivo con BOM frena', rc != 0 and 'BOM' in out, out[-400:])
    git(repo, 'reset', '-q', '--hard')
    git(repo, 'clean', '-qfd')

    skill = 'cerebro-digital/configuracion-ia/skills/redactar-tarea/SKILL.md'
    agregar(repo, skill, '\nlinea de prueba\n')
    for espejo in ('.claude/skills/redactar-tarea/SKILL.md', '.agents/skills/redactar-tarea/SKILL.md'):
        shutil.copy2(os.path.join(repo, skill), os.path.join(repo, espejo))
        git(repo, 'add', espejo)
    rc, out = commit(repo)
    caso('una skill con el espejo en stage y la fuente sin stage frena', rc != 0 and 'no es igual a la fuente' in out, out[-400:])
    git(repo, 'reset', '-q', '--hard')

    agregar(repo, skill, '\nedicion a medias, sin sincronizar ni agregar\n')
    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- cuarta -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('una skill editada en el disco, sin agregar, no frena el commit de otra cosa (se mira lo que entra al commit)',
         rc == 0, out[-400:])
    git(repo, 'checkout', '-q', '--', skill)

    shutil.rmtree(os.path.join(repo, '.claude', 'agents'))
    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- quinta -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('sin el espejo de agentes (no se versiona): avisa y no frena', rc == 0 and 'AVISO' in out, out[-400:])
    shutil.copytree(os.path.join(repo, 'cerebro-digital', 'configuracion-ia', 'agentes'), os.path.join(repo, '.claude', 'agents'))

    with open(os.path.join(repo, 'AGENTS.md'), encoding='utf-8') as h:
        agents_md = h.read()
    with open(os.path.join(repo, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write(re.sub(r'\*\*[0-9]+ habilidades\*\*', '**99 habilidades**', agents_md, count=1))
    git(repo, 'add', 'AGENTS.md')
    rc, out = commit(repo)
    caso('un conteo de skills que no cierra frena (lo cuenta verificar-skills)', rc != 0 and '99' in out, out[-400:])
    git(repo, 'reset', '-q', '--hard')

    nueva = 'cerebro-digital/configuracion-ia/skills/zz-nueva/SKILL.md'
    os.makedirs(os.path.dirname(os.path.join(repo, nueva)))
    agregar(repo, nueva, '---\nname: zz-nueva\ndescription: Una skill a medio hacer.\n---\n')
    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- sexta -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('una skill nueva a medio hacer, sin agregar, no frena el commit de otra cosa', rc == 0, out[-400:])
    for espejo in ('.claude/skills', '.agents/skills'):
        os.makedirs(os.path.join(repo, espejo, 'zz-nueva'))
        shutil.copy2(os.path.join(repo, nueva), os.path.join(repo, espejo, 'zz-nueva', 'SKILL.md'))
    git(repo, 'add', 'cerebro-digital/configuracion-ia/skills/zz-nueva', '.claude/skills/zz-nueva', '.agents/skills/zz-nueva')
    with open(os.path.join(repo, 'AGENTS.md'), encoding='utf-8') as h:
        agents_md = h.read()
    with open(os.path.join(repo, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write(re.sub(r'\*\*([0-9]+) habilidades\*\*', lambda m: '**%d habilidades**' % (int(m.group(1)) + 1), agents_md, count=1))
    rc, out = commit(repo)
    caso('la skill nueva en stage con el conteo corregido solo en el disco: frena (el commit quedaria con el numero viejo)',
         rc != 0 and 'AGENTS.md' in out, out[-400:])
    git(repo, 'reset', '-q', '--hard')
    git(repo, 'clean', '-qfd')

    agente = 'cerebro-digital/configuracion-ia/agentes/cerebro-analyst.md'
    agregar(repo, agente, '\nlinea de prueba\n')
    for espejo in ('.claude/agents/cerebro-analyst.md', '.agents/agents/cerebro-analyst.md'):
        shutil.copy2(os.path.join(repo, agente), os.path.join(repo, espejo))
    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- otra -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('un agente sin stage (sus espejos no se versionan) no frena un commit de otra cosa', rc == 0, out[-400:])
    git(repo, 'reset', '-q', '--hard')
    for espejo in ('.claude/agents/cerebro-analyst.md', '.agents/agents/cerebro-analyst.md'):
        shutil.copy2(os.path.join(repo, agente), os.path.join(repo, espejo))

    with open(os.path.join(repo, 'bin', 'verificar-skills.py'), 'w', encoding='utf-8') as h:
        h.write('import sys\nprint("SIN DATOS -- error del script: algo exploto")\nsys.exit(2)\n')
    agregar(repo, 'COMO-USAR-ESTE-TEMPLATE.md', '\n<!-- tercera -->\n')
    git(repo, 'add', 'COMO-USAR-ESTE-TEMPLATE.md')
    rc, out = commit(repo)
    caso('verificar-skills que sale 2 (SIN DATOS) frena: no se dice OK sobre lo que no se pudo verificar', rc != 0 and 'no pudo verificar la especificacion' in out, out[-400:])

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
