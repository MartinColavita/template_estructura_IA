#!/usr/bin/env python3
"""GATE de WORKTREE, en datos duros: lo que hay que mostrar ANTES de crear un worktree. SOLO LECTURA.

    python bin/gate-worktree.py --repo <ruta-del-repo-de-codigo> --base develop --rama task/1234-slug
    python bin/gate-worktree.py --repo <ruta> --base develop --rama task/1234-slug --repos <ruta2>,<ruta3> --json
    python bin/gate-worktree.py ... --fetch        (hace 'git fetch origin' en cada repo antes de medir)

Tres estados, nunca dos:  0 = se puede crear   1 = FRENA (hay algo que decidir)   2 = SIN DATOS

POR QUE EXISTE. AGENTS.md manda que de donde sale la rama se PREGUNTA, que se diga cuantos
worktrees hay abiertos (techo 8 por maquina), que con el arbol sucio se frene y que si la rama ya
tiene un worktree se avise antes. Esos cuatro datos los calculaba el modelo mirando salidas de git:
tardaba, gastaba tokens y a veces se equivocaba. Este script los mide siempre igual. La pregunta
al humano la sigue haciendo la skill: este script solo le da los numeros.

QUE NO HACE. No crea el worktree, no cambia de rama, no escribe nada. Con --fetch solo lee del
servidor. Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import json
import os
import subprocess
import sys

OK, FRENA, SIN_DATOS = 0, 1, 2


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout.strip()


def worktrees_de(repo):
    """[(ruta, rama)] sin contar el principal (el primero de la lista)."""
    rc, out = git(repo, 'worktree', 'list', '--porcelain')
    if rc != 0:
        return None
    bloques = [b for b in out.split('\n\n') if b.strip()]
    res = []
    for b in bloques[1:]:
        ruta, rama = None, None
        for linea in b.splitlines():
            if linea.startswith('worktree '):
                ruta = linea[9:]
            elif linea.startswith('branch '):
                rama = linea[7:].replace('refs/heads/', '')
        res.append((ruta, rama))
    return res


def main():
    ap = argparse.ArgumentParser(description='Datos duros del GATE de WORKTREE (solo lectura).')
    ap.add_argument('--repo', required=True, help='repo de codigo donde se va a crear el worktree')
    ap.add_argument('--base', required=True, help='rama base propuesta (p. ej. develop)')
    ap.add_argument('--rama', required=True, help='rama que se va a crear (p. ej. task/1234-slug)')
    ap.add_argument('--repos', default='', help='otros repos de la maquina, separados por coma (para el techo)')
    ap.add_argument('--techo', type=int, default=8)
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    repo = os.path.abspath(a.repo)
    rc, _ = git(repo, 'rev-parse', '--is-inside-work-tree')
    if rc != 0:
        print('SIN DATOS -- %s no es un repositorio git.' % repo)
        return SIN_DATOS

    todos = [repo] + [os.path.abspath(r) for r in a.repos.split(',') if r.strip()]
    fetch_fallido = []
    if a.fetch:
        for r in todos:
            if git(r, 'fetch', 'origin', '--prune')[0] != 0:
                fetch_fallido.append(r)

    abiertos = []
    for r in todos:
        w = worktrees_de(r)
        if w is None:
            print('SIN DATOS -- no pude listar los worktrees de %s.' % r)
            return SIN_DATOS
        abiertos += [(r, ruta, rama) for ruta, rama in w]

    rc, sucio = git(repo, 'status', '--porcelain')
    if rc != 0:
        # un status que falla no es un arbol limpio
        print('SIN DATOS -- git no pudo leer el estado del arbol de %s (git status salio %d).' % (repo, rc))
        return SIN_DATOS
    sucios = [l for l in sucio.splitlines() if l.strip()]

    con_worktree = [ruta for r, ruta, rama in abiertos if rama == a.rama and r == repo]
    rc_loc, _ = git(repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/' + a.rama)
    rc_rem, _ = git(repo, 'rev-parse', '--verify', '--quiet', 'refs/remotes/origin/' + a.rama)

    rc_base, _ = git(repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/' + a.base)
    rc_obase, _ = git(repo, 'rev-parse', '--verify', '--quiet', 'refs/remotes/origin/' + a.base)
    atras = adelante = None
    if rc_base == 0 and rc_obase == 0:
        rc_a, atras = git(repo, 'rev-list', '--count', a.base + '..origin/' + a.base)
        rc_d, adelante = git(repo, 'rev-list', '--count', 'origin/' + a.base + '..' + a.base)
        # un rev-list que falla no es "al dia"
        atras = int(atras) if rc_a == 0 and atras.isdigit() else None
        adelante = int(adelante) if rc_d == 0 and adelante.isdigit() else None

    motivos = []
    if len(abiertos) >= a.techo:
        motivos.append('hay %d worktrees abiertos y el techo es %d: no se crea otro' % (len(abiertos), a.techo))
    if sucios:
        motivos.append('el arbol de %s tiene %d cambio(s) sin commitear' % (repo, len(sucios)))
    if con_worktree:
        motivos.append('la rama %s ya tiene un worktree en %s' % (a.rama, con_worktree[0]))
    if rc_base != 0:
        motivos.append('la rama base %s no existe en este repo' % a.base)
    avisos = []
    if rc_loc == 0 and not con_worktree:
        avisos.append('la rama %s ya existe en local (se reusaria, no se crea de cero)' % a.rama)
    if rc_rem == 0:
        avisos.append('la rama %s ya existe en origin' % a.rama)
    for r in fetch_fallido:
        avisos.append('el fetch de %s fallo: lo de origin se midio contra referencias viejas' % r)
    if rc_base == 0 and rc_obase == 0 and (atras is None or adelante is None):
        avisos.append('git no pudo comparar %s con origin/%s: si la base esta al dia es SIN DATOS' % (a.base, a.base))
    if rc_obase != 0:
        avisos.append('no hay origin/%s: no se puede saber si la base esta al dia (proba --fetch)' % a.base)
    elif atras:
        avisos.append('la base local %s esta %d commit(s) atras de origin/%s: convendria traerla antes' % (a.base, atras, a.base))

    estado = FRENA if motivos else OK
    salida = {
        'estado': 'FRENA' if motivos else 'OK',
        'repo': repo, 'rama': a.rama, 'base': a.base,
        'worktrees_abiertos': len(abiertos), 'techo': a.techo,
        'worktrees': [{'repo': r, 'ruta': ruta, 'rama': rama} for r, ruta, rama in abiertos],
        'arbol_sucio': sucios[:20],
        'rama_ya_tiene_worktree': con_worktree, 'rama_existe_local': rc_loc == 0, 'rama_existe_origin': rc_rem == 0,
        'base_existe': rc_base == 0, 'base_atras_de_origin': atras, 'base_adelante_de_origin': adelante,
        'motivos': motivos, 'avisos': avisos,
    }
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('GATE de WORKTREE -- %s' % salida['estado'])
        print('  Worktrees abiertos en la maquina: %d de %d como maximo' % (len(abiertos), a.techo))
        for r, ruta, rama in abiertos:
            print('    - %s  (%s)' % (ruta, rama or 'sin rama'))
        print('  Arbol de %s: %s' % (repo, 'limpio' if not sucios else '%d cambio(s) sin commitear' % len(sucios)))
        if rc_base == 0 and rc_obase == 0:
            print('  Base %s: %s' % (a.base, 'SIN DATOS (git no pudo comparar)' if atras is None or adelante is None else
                                     'al dia con origin' if not atras and not adelante else
                                     '%d atras / %d adelante de origin' % (atras, adelante)))
        for m in motivos:
            print('  FRENA: ' + m)
        for v in avisos:
            print('  aviso: ' + v)
        print('  Lo que este script NO decide: de que rama sale el worktree. Eso se le PREGUNTA al humano, con estos datos a la vista.')
    return estado


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
