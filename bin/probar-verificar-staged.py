#!/usr/bin/env python3
"""Prueba de bin/verificar-staged.py (la guarda de encoding del hook y del CI) sobre un repo de mentira.
Se corre:  python -B bin/probar-verificar-staged.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'verificar-staged.py')
ESPERADOS = []
SALTEADOS = []   # lo que no corrio se dice en la ultima linea: no es OK
BOM = b'\xef\xbb\xbf'


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'core.autocrlf=false'] + list(args),
                          capture_output=True, text=True)


def escribir(repo, rel, datos):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as h:
        h.write(datos)


def correr(repo, *args):
    r = subprocess.run([sys.executable, '-I', SCRIPT, '--repo', repo] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== verificar-staged')
    if shutil.which('git') is None:
        print('SIN DATOS -- no hay git en el PATH.')
        return 2
    tmp = tempfile.mkdtemp(prefix='probar-staged-')
    repo = os.path.join(tmp, 'repo')
    os.makedirs(repo)
    git(repo, 'init', '-q')
    escribir(repo, 'limpio.md', 'texto sano\n'.encode('utf-8'))
    escribir(repo, 'viejo.md', BOM + 'tenia BOM y ya estaba\n'.encode('utf-8'))
    git(repo, 'add', '-A')
    git(repo, 'commit', '-qm', 'base', '--no-verify')

    rc, out = correr(repo)
    caso('nada en stage: OK (0), lo dice', rc == 0 and 'ningun archivo' in out, out[:200])

    escribir(repo, 'nuevo.md', 'hola\n'.encode('utf-8'))
    git(repo, 'add', 'nuevo.md')
    rc, out = correr(repo)
    caso('un archivo sano en stage: OK (0)', rc == 0, out[:200])

    escribir(repo, 'con bom.md', BOM + 'hola\n'.encode('utf-8'))
    escribir(repo, 'control.md', b'antes\x07despues\n')
    escribir(repo, 'vt.md', b'antes\x0bdespues\n')
    escribir(repo, 'ff.md', b'antes\x0cdespues\n')
    escribir(repo, 'script.ps1', BOM + 'Write-Host "acento"\n'.encode('utf-8'))
    git(repo, 'add', '-A')
    rc, out = correr(repo)
    caso('BOM en un .md (nombre con espacio): HALLAZGO (1)', rc == 1 and 'con bom.md' in out and 'BOM' in out, out[:400])
    caso('caracteres de control BEL, VT y FF: HALLAZGO, cada uno', all(f in out for f in ('control.md', 'vt.md', 'ff.md')), out[:400])
    caso('un .ps1 con BOM es la excepcion declarada: no se marca', 'script.ps1' not in out, out[:400])

    git(repo, 'reset', '-q')
    for f in ('con bom.md', 'control.md', 'vt.md', 'ff.md', 'script.ps1', 'nuevo.md'):
        os.remove(os.path.join(repo, f))
    git(repo, 'mv', 'viejo.md', 'renombrado.md')
    rc, out = correr(repo)
    caso('un renombre (git mv) entra a la revision: el BOM del archivo renombrado se marca', rc == 1 and 'renombrado.md' in out, out[:400])

    git(repo, 'reset', '-q', '--hard')
    escribir(repo, 'disco.md', 'sano en disco\n'.encode('utf-8'))
    git(repo, 'add', 'disco.md')
    escribir(repo, 'disco.md', BOM + 'sucio solo en disco\n'.encode('utf-8'))
    rc, out = correr(repo)
    caso('se mira lo que se va a commitear (el stage), no el disco', rc == 0, out[:300])

    git(repo, 'reset', '-q', '--hard')
    git(repo, 'rm', '-q', 'limpio.md')
    rc, out = correr(repo)
    caso('un borrado en stage no se revisa ni frena', rc == 0, out[:300])
    git(repo, 'reset', '-q', '--hard')
    sub = git(repo, 'update-index', '--add', '--cacheinfo', '160000,' + 'a' * 40 + ',docs.md')
    if sub.returncode != 0:
        SALTEADOS.append('el submodulo (git no dejo armarlo en el indice)')
        print('  SALTEADO %s' % SALTEADOS[-1])
    else:
        rc, out = correr(repo)
        caso('un submodulo con nombre de texto (docs.md) no se lee ni frena', rc == 0 and 'docs.md' not in out, out[:300])
    git(repo, 'reset', '-q', '--hard')
    fantasma = git(repo, 'update-index', '--add', '--cacheinfo', '100644,' + 'b' * 40 + ',fantasma.md')
    if fantasma.returncode != 0:
        SALTEADOS.append('el blob ilegible (git no dejo armarlo en el indice)')
        print('  SALTEADO %s' % SALTEADOS[-1])
    else:
        rc, out = correr(repo)
        caso('un archivo en stage cuyo contenido git no puede leer: SIN DATOS (2), no OK', rc == 2 and 'fantasma.md' in out, out[:300])
    git(repo, 'reset', '-q', '--hard')
    if os.name != 'nt':   # Windows no acepta un salto de linea en un nombre de archivo
        escribir(repo, 'a\nb.md', BOM + b'x\n')
        escribir(repo, 'zz.md', b'sano\n')
        git(repo, 'add', '-A')
        rc, out = correr(repo)
        caso('un nombre con salto de linea no desarma la guarda: marca ese archivo y no otro', rc == 1 and 'zz.md' not in out, out[:300])
        git(repo, 'reset', '-q', '--hard')
        git(repo, 'clean', '-qfd')
    rc, out = correr(repo, '--todo')
    caso('--todo (para el CI): revisa todo lo versionado y marca el BOM de viejo.md', rc == 1 and 'viejo.md' in out, out[:400])

    rc, out = correr(tmp)
    caso('una carpeta que no es repo: SIN DATOS (2)', rc == 2, out[:200])

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.%s' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS),
                                                         (' SALTEADOS: ' + '; '.join(SALTEADOS)) if SALTEADOS else ''))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
