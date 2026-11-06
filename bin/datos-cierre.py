#!/usr/bin/env python3
"""Los DATOS DUROS del comentario de cierre de una Tarea, leidos del repositorio. SOLO LECTURA.

    python bin/datos-cierre.py --repo <worktree> --base <ref-o-sha-de-la-base> [--id 1234] [--json]

Tres estados, nunca dos:  0 = todos los datos se pudieron leer   1 = algun dato queda "sin dato"
2 = SIN DATOS (no es un repo o no hay commits)

POR QUE EXISTE. comentar-tarea manda que la rama, el ultimo commit, la cantidad de commits, si se
pusheo, la rama de respaldo y el link del Merge Request salgan del repositorio y nunca de la memoria
del worker, y que lo que no se pudo leer vaya como "sin dato". Este script lee exactamente eso y lo
deja listo para pegar; la prosa del resumen tecnico la pone la skill, con el resumen del worker.

QUE NO HACE. No abre el Merge Request, no pushea, no comenta la tarjeta. Solo biblioteca estandar.
ASCII puro en este archivo.
"""

import argparse
import json
import re
import subprocess
import sys

OK, INCOMPLETO, SIN_DATOS = 0, 1, 2
SIN = '(sin dato)'


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return (r.stdout.strip() if r.returncode == 0 else None)


def url_web(remoto):
    if not remoto:
        return None
    m = re.match(r'git@([^:]+):(.+?)(\.git)?$', remoto)
    if m:
        return 'https://%s/%s' % (m.group(1), m.group(2))
    m = re.match(r'(https?://)(?:[^@/]+@)?([^/]+/.+?)(\.git)?$', remoto)
    if m:
        return m.group(1) + m.group(2)
    return None


def main():
    ap = argparse.ArgumentParser(description='Datos duros del cierre de una Tarea (solo lectura).')
    ap.add_argument('--repo', required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--id', default='')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if git(a.repo, 'rev-parse', '--is-inside-work-tree') is None:
        print('SIN DATOS -- %s no es un repositorio git.' % a.repo)
        return SIN_DATOS
    rama = git(a.repo, 'branch', '--show-current') or SIN
    sha = git(a.repo, 'rev-parse', '--short', 'HEAD') or SIN
    asunto = git(a.repo, 'log', '-1', '--format=%s') or SIN
    cuenta = git(a.repo, 'rev-list', '--count', a.base + '..HEAD')
    archivos = git(a.repo, 'diff', '--name-only', a.base + '...HEAD')
    lista = archivos.splitlines() if archivos else []
    grupos = sorted(set('/'.join(f.split('/')[:2]) for f in lista))
    en_origin = git(a.repo, 'rev-parse', '--verify', '--quiet', 'refs/remotes/origin/' + rama) is not None if rama != SIN else False
    sin_pushear = git(a.repo, 'rev-list', '--count', 'origin/%s..HEAD' % rama) if en_origin else None
    pusheada = (en_origin and sin_pushear == '0')
    evidencia = {}
    if a.id:
        for ref, donde in (('refs/heads/evidencia/' + a.id, 'local'), ('refs/remotes/origin/evidencia/' + a.id, 'origin')):
            evidencia[donde] = git(a.repo, 'rev-parse', '--verify', '--quiet', ref) is not None
    remoto = git(a.repo, 'remote', 'get-url', 'origin')
    web = url_web(remoto)
    link_mr = None
    if web and rama != SIN:
        link_mr = ('%s/-/merge_requests/new?merge_request%%5Bsource_branch%%5D=%s&merge_request%%5Btarget_branch%%5D=%s'
                   % (web, rama, a.base.replace('origin/', '')))

    salida = {
        'rama': rama, 'ultimo_commit': sha, 'asunto': asunto,
        'commits_desde_base': int(cuenta) if cuenta is not None else None,
        'archivos_tocados': len(lista), 'archivos': lista[:200], 'carpetas_tocadas': grupos,
        'pusheada': pusheada, 'commits_sin_pushear': int(sin_pushear) if sin_pushear is not None else None,
        'evidencia': evidencia, 'remoto': remoto, 'link_merge_request_nuevo': link_mr,
    }
    faltan = [k for k in ('rama', 'ultimo_commit', 'commits_desde_base', 'remoto') if salida[k] in (None, SIN)]
    estado = INCOMPLETO if faltan else OK
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('DATOS DE CIERRE -- %s' % ('completos' if not faltan else 'faltan: ' + ', '.join(faltan)))
        print('  Rama: %s (%s)' % (rama, 'pusheada' if pusheada else ('sin pushear' if rama != SIN else SIN)))
        print('  Ultimo commit: %s "%s"' % (sha, asunto))
        print('  Commits desde la base %s: %s' % (a.base, cuenta if cuenta is not None else SIN))
        print('  Archivos tocados: %d  (carpetas: %s)' % (len(lista), ', '.join(grupos) or SIN))
        if a.id:
            print('  Respaldo evidencia/%s: local %s / origin %s' % (a.id, 'si' if evidencia.get('local') else 'no', 'si' if evidencia.get('origin') else 'no'))
        print('  Merge Request: %s' % (link_mr or SIN + ' -- no se pudo armar el link'))
        print('  Lo que no esta aca lo pone la skill con el resumen del worker; lo que no se pudo leer va "sin dato", no se inventa.')
    return estado


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
