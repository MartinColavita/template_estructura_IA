#!/usr/bin/env python3
"""Prueba de bin/instalar.py sobre un repositorio del Cerebro de mentira, en una carpeta temporal.
Se corre:  python -B bin/probar-instalar.py   -> OK o FALLA, con el detalle de cada caso.
Necesita git en el PATH (si no hay, los casos que lo usan se marcan SIN DATOS y la prueba falla)."""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def git(raiz, *args):
    r = subprocess.run(['git', '-C', raiz] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '').strip()


def instalar(raiz, *args):
    r = subprocess.run([sys.executable, '-I', os.path.join(raiz, 'bin', 'instalar.py')] + list(args),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def armar(raiz):
    skill = '---\nname: una-skill\ndescription: Hace algo. Usar cuando se pida.\n---\n\n# Una skill\n'
    for base in ('cerebro-digital/configuracion-ia/skills', '.agents/skills', '.claude/skills'):
        escribir(raiz, base + '/una-skill/SKILL.md', skill)
    escribir(raiz, 'cerebro-digital/configuracion-ia/agentes/un-agente.md', '---\nname: un-agente\n---\nAgente.\n')
    escribir(raiz, '.githooks/pre-commit', '#!/usr/bin/env bash\nexit 0\n')
    escribir(raiz, 'AGENTS.md', '# Proyecto\n')
    os.makedirs(os.path.join(raiz, 'bin'))
    for f in ('instalar.py', 'verificar-skills.py', 'sync-espejos.py'):
        shutil.copy(os.path.join(AQUI, f), os.path.join(raiz, 'bin', f))


def main():
    print('== instalar')
    tmp = tempfile.mkdtemp(prefix='probar-instalar-')
    armar(tmp)
    rc, out = git(tmp, 'init', '-q')
    if rc != 0:
        caso('git disponible', False, 'sin git no se puede probar el instalador')
    else:
        rc, out = instalar(tmp)
        caso('repo sano: OK (0)', rc == 0 and 'OK --' in out, out[-400:])
        rc2, hooks = git(tmp, 'config', '--get', 'core.hooksPath')
        caso('deja el hook activo', hooks == '.githooks', hooks)
        caso('materializa los espejos de agentes', os.path.isfile(os.path.join(tmp, '.claude', 'agents', 'un-agente.md')) and os.path.isfile(os.path.join(tmp, '.agents', 'agents', 'un-agente.md')))
        caso('avisa que no esta instanciado solo si hay placeholders', 'todavia tiene placeholders' not in out)

        escribir(tmp, '.claude/skills/una-skill/SKILL.md', '---\nname: una-skill\ndescription: Otra cosa.\n---\n')
        rc, out = instalar(tmp)
        caso('espejo desincronizado: HALLAZGO (1) y pide sync-skills', rc == 1 and 'sync-skills' in out, out[-400:])

        escribir(tmp, '.claude/skills/una-skill/SKILL.md', '---\nname: una-skill\ndescription: Hace algo. Usar cuando se pida.\n---\n\n# Una skill\n')
        escribir(tmp, 'cerebro-digital/configuracion-ia/skills/una-skill/SKILL.md', '---\nname: una-skill\ndescription: Hace algo. Usar cuando se pida.\n---\n\n# Una skill\n')
        escribir(tmp, 'AGENTS.md', '# {{PROYECTO}}\n')
        rc, out = instalar(tmp)
        caso('placeholders sin instanciar: aviso, no frena', rc == 0 and 'placeholders' in out, out[-400:])

        shutil.rmtree(os.path.join(tmp, '.claude', 'agents'))
        rc, out = instalar(tmp, '--dry-run')
        caso('dry-run no materializa los agentes', rc == 0 and not os.path.isdir(os.path.join(tmp, '.claude', 'agents')), out[-300:])

    vacio = tempfile.mkdtemp(prefix='probar-instalar-vacio-')
    os.makedirs(os.path.join(vacio, 'bin'))
    shutil.copy(os.path.join(AQUI, 'instalar.py'), os.path.join(vacio, 'bin', 'instalar.py'))
    rc, out = instalar(vacio)
    caso('sin cerebro-digital: SIN DATOS (2)', rc == 2)

    for d in (tmp, vacio):
        shutil.rmtree(d, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
