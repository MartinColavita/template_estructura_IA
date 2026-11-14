#!/usr/bin/env python3
"""Instalador del Cerebro: lo que hay que hacer UNA vez despues de clonar, y cada vez que se actualiza.

    python -I bin/instalar.py [--dry-run] [--sin-agentes]

Tres salidas, nunca dos:  0 = OK   1 = HALLAZGO (algo que arreglar, con el comando)   2 = SIN DATOS (esto no es un repo del Cerebro)

POR QUE EXISTE. Despues de clonar habia dos pasos a mano que nadie recordaba (activar el hook y
materializar los espejos de agentes) y tres cosas que nadie verificaba (que los espejos de skills sean
identicos a la fuente, que cada SKILL.md cumpla la especificacion, que el template haya sido
instanciado). Un paso que se olvida en silencio es un guardarrail apagado. Esto lo hace todo, siempre
igual, y dice que falta. Idempotente: se puede correr mil veces.

QUE HACE, en orden:
  1. Requisitos: git y Python 3.8+ (frenan); Node (solo avisa: hace falta unicamente para los servidores MCP, que corren con npx).
  2. Hook pre-commit: git config core.hooksPath .githooks (si esto ya es un repositorio git).
  3. Espejos de agentes: cerebro-digital/configuracion-ia/agentes -> .agents/agents y .claude/agents (no se versionan).
  4. Espejos de skills: .agents/skills y .claude/skills identicos a la fuente; back/ y front/ gemelos entre si.
  5. Especificacion de skills: bin/verificar-skills.py.
  6. Avisos: placeholders sin instanciar, .gemini/.env ausente, MCP sin configurar.
  7. Lo que sigue.

QUE NO HACE. No instala nada en la maquina, no toca el Cerebro ni el codigo, no configura MCP (eso
lleva tokens y es por persona). Solo biblioteca estandar. ASCII puro.
"""

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE_SKILLS = os.path.join('cerebro-digital', 'configuracion-ia', 'skills')
FUENTE_AGENTES = os.path.join('cerebro-digital', 'configuracion-ia', 'agentes')
ESPEJOS_SKILLS = (os.path.join('.agents', 'skills'), os.path.join('.claude', 'skills'))
ESPEJOS_AGENTES = (os.path.join('.agents', 'agents'), os.path.join('.claude', 'agents'))
GEMELOS = ((os.path.join('back', '.claude', 'skills'), os.path.join('back', '.agents', 'skills')),
           (os.path.join('front', '.claude', 'skills'), os.path.join('front', '.agents', 'skills')))

HALLAZGOS, AVISOS = [], []


def hallazgo(que, arreglo):
    HALLAZGOS.append((que, arreglo))
    print('  HALLAZGO: %s\n            -> %s' % (que, arreglo))


def aviso(que):
    AVISOS.append(que)
    print('  AVISO: %s' % que)


def sh(*args):
    try:
        r = subprocess.run(list(args), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=RAIZ)
    except OSError:
        return None, ''
    return r.returncode, (r.stdout or '').strip()


def arbol(base):
    """{ruta relativa: contenido normalizado} de todos los archivos debajo de base."""
    out = {}
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if x != '__pycache__']
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, base).replace(os.sep, '/')
            with open(p, 'rb') as h:
                out[rel] = h.read().replace(b'\r\n', b'\n')
    return out


def comparar(a, b):
    """Lista de diferencias entre dos carpetas (nombres o contenido). Vacia si son identicas."""
    ta, tb = arbol(a), arbol(b)
    difs = ['solo en %s: %s' % (os.path.basename(os.path.dirname(a)) + '/' + os.path.basename(a), r) for r in sorted(set(ta) - set(tb))]
    difs += ['solo en %s: %s' % (os.path.basename(os.path.dirname(b)) + '/' + os.path.basename(b), r) for r in sorted(set(tb) - set(ta))]
    difs += ['distinto: %s' % r for r in sorted(set(ta) & set(tb)) if ta[r] != tb[r]]
    return difs


def main():
    ap = argparse.ArgumentParser(description='Instalador del Cerebro (idempotente).')
    ap.add_argument('--dry-run', action='store_true', help='mostrar sin tocar nada')
    ap.add_argument('--sin-agentes', action='store_true', help='no regenerar los espejos de agentes')
    ap.add_argument('--con-archify', action='store_true', help='reinstalar o actualizar Archify en las carpetas globales de la maquina (la skill ya viene vendorizada en el template)')
    a = ap.parse_args()
    print('Instalador del Cerebro -- %s%s' % (RAIZ, '  (dry-run)' if a.dry_run else ''))
    if not os.path.isdir(os.path.join(RAIZ, FUENTE_SKILLS)):
        print('SIN DATOS -- no existe %s: esto no es un repositorio del Cerebro.' % FUENTE_SKILLS)
        return SIN_DATOS

    # 1. requisitos
    print('[1/7] requisitos')
    if sys.version_info < (3, 8):
        hallazgo('Python %d.%d' % sys.version_info[:2], 'instalar Python 3.8 o mas nuevo: los scripts de bin/ y el Doctor lo necesitan')
    else:
        print('  python %d.%d ok' % sys.version_info[:2])
    rc, salida = sh('git', '--version')
    if rc is None or rc != 0:
        hallazgo('no encuentro git', 'instalar git y volver a correr')
        es_repo = False
    else:
        print('  %s ok' % salida)
        rc, salida = sh('git', 'rev-parse', '--is-inside-work-tree')
        es_repo = rc == 0 and salida == 'true'
        if not es_repo:
            aviso('todavia no es un repositorio git: corre  git init  (o clona el remoto) y volve a correr; el hook se activa recien ahi')
    if shutil.which('node') and shutil.which('npx'):
        rc, salida = sh('node', '--version')
        print('  node %s ok (hace falta para los servidores MCP y para Spectral, el linter del contrato OpenAPI)' % salida)
    else:
        aviso('no encuentro node/npx: hace falta para los servidores MCP (corren con npx) y para Spectral, el linter del contrato OpenAPI (C5); sin ellos esos controles quedan SIN DATOS')

    # 2. hook
    print('[2/7] hook pre-commit')
    if not os.path.isfile(os.path.join(RAIZ, '.githooks', 'pre-commit')):
        hallazgo('falta .githooks/pre-commit', 'restaurarlo desde el template; sin el, los espejos y los conteos envejecen en silencio')
    elif es_repo:
        if a.dry_run:
            print('  (dry-run) git config core.hooksPath .githooks')
        else:
            sh('git', 'config', 'core.hooksPath', '.githooks')
            rc, salida = sh('git', 'config', '--get', 'core.hooksPath')
            if salida == '.githooks':
                print('  hook activo -> .githooks')
            else:
                hallazgo('no pude dejar core.hooksPath en .githooks (quedo "%s")' % salida, 'git config core.hooksPath .githooks')

    # 3. espejos de agentes
    print('[3/7] espejos de agentes (no se versionan)')
    fuente_ag = os.path.join(RAIZ, FUENTE_AGENTES)
    if not os.path.isdir(fuente_ag):
        aviso('no hay %s: sin agentes que materializar' % FUENTE_AGENTES)
    elif a.sin_agentes:
        print('  salteado (--sin-agentes)')
    else:
        espejos = None
        try:
            spec = importlib.util.spec_from_file_location('sync_espejos', os.path.join(RAIZ, 'bin', 'sync-espejos.py'))
            espejos = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(espejos)
        except (OSError, ImportError) as e:
            hallazgo('falta bin/sync-espejos.py (%s)' % type(e).__name__, 'restaurarlo desde el template')
        for rel in (ESPEJOS_AGENTES if espejos else ()):
            # sync-espejos: arma el espejo aparte y no pisa lo que se edito en el (estos espejos no se versionan)
            ok, msj = espejos.regenerar(fuente_ag, os.path.join(RAIZ, rel), dry_run=a.dry_run)
            if ok:
                print('  %s <- %s' % (rel, FUENTE_AGENTES))
            else:
                hallazgo('el espejo %s no se regenero' % rel, msj.replace(RAIZ + os.sep, ''))

    # 4. espejos de skills
    print('[4/7] espejos de skills == fuente')
    for rel in ESPEJOS_SKILLS:
        destino = os.path.join(RAIZ, rel)
        if not os.path.isdir(destino):
            hallazgo('falta el espejo %s' % rel, 'bin/sync-skills.sh (o .ps1) y  git add %s' % rel)
            continue
        difs = comparar(os.path.join(RAIZ, FUENTE_SKILLS), destino)
        if difs:
            hallazgo('el espejo %s difiere de la fuente (%d diferencias; p. ej. %s)' % (rel, len(difs), difs[0]),
                     'bin/sync-skills.sh (o .ps1) y  git add %s' % rel)
        else:
            print('  %s identico a la fuente' % rel)
    for a_, b_ in GEMELOS:
        pa, pb = os.path.join(RAIZ, a_), os.path.join(RAIZ, b_)
        if not os.path.isdir(pa) and not os.path.isdir(pb):
            continue
        if not os.path.isdir(pa) or not os.path.isdir(pb):
            hallazgo('existe uno de los gemelos %s / %s y no el otro' % (a_, b_), 'copiar el que existe sobre el que falta: son copias identicas')
            continue
        difs = comparar(pa, pb)
        if difs:
            hallazgo('%s y %s difieren (%d diferencias; p. ej. %s)' % (a_, b_, len(difs), difs[0]), 'todo cambio va en las DOS copias')
        else:
            print('  %s == %s' % (a_, b_))

    # 5. especificacion de skills
    print('[5/7] especificacion de skills')
    verificador = os.path.join(RAIZ, 'bin', 'verificar-skills.py')
    if not os.path.isfile(verificador):
        hallazgo('falta bin/verificar-skills.py', 'restaurarlo desde el template')
    else:
        rc, salida = sh(sys.executable, '-I', verificador, RAIZ)
        if rc == 0:
            print('  ' + salida.splitlines()[0])
        elif rc == 2:
            # 2 es tambien lo que devuelve cuando explota; la fuente de skills existe (se chequeo arriba): no se pudo
            # verificar, y eso no es OK (lo mismo que hace el hook)
            hallazgo('verificar-skills no pudo verificar las skills (SIN DATOS): ' + (salida.splitlines() or [''])[0],
                     'python -I bin/verificar-skills.py')
        else:
            hallazgo('hay skills fuera de la especificacion de Agent Skills, o un conteo que no cierra',
                     'python -I bin/verificar-skills.py  y corregir lo que lista')
            for linea in salida.splitlines()[1:8]:
                print('      ' + linea)

    # 6. avisos
    print('[6/7] instanciacion y configuracion por maquina')
    agents_md = os.path.join(RAIZ, 'AGENTS.md')
    if os.path.isfile(agents_md):
        with open(agents_md, 'rb') as h:
            if ('{{' + 'PROYECTO' + '}}').encode() in h.read():   # armado por partes: el instanciador reemplaza el literal
                aviso('AGENTS.md todavia tiene placeholders {{...}}: el template no fue instanciado; python -I bin/instanciar.py --help')
            else:
                print('  instanciado (sin placeholders en AGENTS.md)')
    if os.path.isfile(os.path.join(RAIZ, '.gemini', '.env.example')) and not os.path.isfile(os.path.join(RAIZ, '.gemini', '.env')):
        aviso('falta .gemini/.env (solo si vas a usar Gemini CLI): copiar .gemini/.env.example y completar')
    if not os.path.isfile(os.path.join(RAIZ, '.mcp.json')):
        aviso('no hay .mcp.json: los MCP de Azure DevOps y GitLab se configuran por maquina (cerebro-digital/configuracion-ia/integracion-azure-mcp/ e integracion-gitlab-mcp/)')
    hooks = os.path.join(RAIZ, '.claude', 'settings.json')
    if not os.path.isfile(hooks) or 'registrar-sesion.py' not in open(hooks, 'r', encoding='utf-8', errors='replace').read():
        aviso('sin los hooks de sesion en .claude/settings.json (registrar-sesion.py al terminar, tendencia.py al empezar): la tendencia mejor/peor no se mide sola')
    if not os.environ.get('STITCH_API_KEY'):
        aviso('sin STITCH_API_KEY en el entorno: el diseno con Stitch queda en modo manual (cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md)')

    # 6-bis. herramientas externas opcionales
    if a.con_archify:
        print('[6-bis] Archify (opcional, global, Apache-2.0)')
        if not (shutil.which('npx')):
            hallazgo('no encuentro npx para instalar Archify', 'instalar Node.js y volver a correr con --con-archify')
        elif a.dry_run:
            print('  (dry-run) npx -y skills add tt-a1i/archify -g -y --copy')
        else:
            rc, salida = sh('npx', '-y', 'skills', 'add', 'tt-a1i/archify', '-g', '-y', '--copy')
            if rc == 0 and 'archify' in salida.lower():
                print('  Archify instalado en las carpetas globales de skills de los agentes de esta maquina (ver DEPENDENCIAS-EXTERNAS.md)')
            else:
                hallazgo('la instalacion de Archify no termino bien (codigo %s)' % rc, 'correr a mano: npx -y skills add tt-a1i/archify -g -y --copy')

    # 7. cierre
    print('[7/7] resumen')
    if HALLAZGOS:
        print('HALLAZGO -- %d cosa(s) que arreglar, %d aviso(s). Los avisos no frenan.' % (len(HALLAZGOS), len(AVISOS)))
        return HALLAZGO
    print('OK -- sin hallazgos: espejos identicos y skills dentro de la especificacion. %d aviso(s).' % len(AVISOS))
    print('Lo que sigue: completar el Cerebro (COMO-USAR-ESTE-TEMPLATE.md o INSTALACION.md), DEC-003 (el stack) y los MCP por maquina.')
    return OK


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
