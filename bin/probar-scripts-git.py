#!/usr/bin/env python3
"""Prueba sin red de gate-worktree.py, verificar-tdd.py, auditar-diff.py, datos-cierre.py e
inventariar-codigo.py sobre un repositorio git TEMPORAL que arma este mismo script.

    python -B bin/probar-scripts-git.py

Termina con 0 si todos los casos dan lo esperado, 1 si alguno no. Necesita git en el PATH.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ESPERADOS = []


def caso(nombre, cond, detalle=''):
    ESPERADOS.append((nombre, bool(cond), detalle))
    print('  %s %s%s' % ('OK   ' if cond else 'FALLA', nombre, (' -- ' + detalle) if detalle and not cond else ''))


def sh(cwd, *cmd):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def script(nombre, *args):
    r = subprocess.run([sys.executable, '-B', os.path.join(AQUI, nombre)] + list(args),
                       capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=AQUI)
    return r.returncode, r.stdout + r.stderr


def escribir(repo, rel, contenido):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as h:
        h.write(contenido)


def commit(repo, msg):
    sh(repo, 'git', 'add', '-A')
    rc, out = sh(repo, 'git', 'commit', '-q', '-m', msg)
    assert rc == 0, out


def main():
    if shutil.which('git') is None:
        print('SIN DATOS -- no hay git en el PATH.')
        return 2
    tmp = tempfile.mkdtemp(prefix='probar-scripts-git-')
    repo = os.path.join(tmp, 'repo')
    os.makedirs(repo)
    sh(repo, 'git', 'init', '-q', '-b', 'develop')
    sh(repo, 'git', 'config', 'user.name', 'Prueba')
    sh(repo, 'git', 'config', 'user.email', 'prueba@example.com')
    escribir(repo, 'README.md', '# app de prueba\n')
    escribir(repo, 'src/app.txt', 'base\n')
    commit(repo, 'base')
    rc, base = sh(repo, 'git', 'rev-parse', 'HEAD')
    base = base.strip()

    print('== gate-worktree')
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba', '--json')
    d = json.loads(out)
    caso('arbol limpio y sin worktrees: OK', rc == 0 and d['estado'] == 'OK' and d['worktrees_abiertos'] == 0, out[:200])
    caso('el techo por defecto es de 10 worktrees por maquina (AGENTS.md, GATE de WORKTREE)', d.get('techo') == 10, str(d.get('techo')))
    caso('avisa que no hay origin/develop', any('origin/develop' in v for v in d['avisos']))
    escribir(repo, 'src/sucio.txt', 'x\n')
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba', '--json')
    d = json.loads(out)
    caso('arbol sucio: FRENA', rc == 1 and d['arbol_sucio'] and any('sin commitear' in m for m in d['motivos']), out[:200])
    os.remove(os.path.join(repo, 'src', 'sucio.txt'))
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'inexistente', '--rama', 'task/1', '--json')
    caso('base inexistente: FRENA', rc == 1 and 'no existe' in out)
    rc, out = script('gate-worktree.py', '--repo', tmp, '--base', 'develop', '--rama', 'x')
    caso('carpeta que no es repo: SIN DATOS', rc == 2)
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba', '--fetch', '--json')
    d = json.loads(out)
    caso('--fetch que falla (sin origin): lo avisa, no mide en silencio contra referencias viejas',
         any(v.startswith('el fetch de') for v in d['avisos']), out[:300])
    sh(repo, 'git', 'branch', '-f', 'develop')
    escribir(repo, '.git/refs/remotes/origin/develop', 'f' * 40 + '\n')
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba', '--json')
    d = json.loads(out)
    caso('rev-list que falla (origin/develop apunta a un commit que no existe): la base no queda "al dia"',
         d['base_atras_de_origin'] is None and any('SIN DATOS' in v for v in d['avisos']), out[:400])
    os.remove(os.path.join(repo, '.git', 'refs', 'remotes', 'origin', 'develop'))
    indice = os.path.join(repo, '.git', 'index')
    with open(indice, 'rb') as h:
        indice_ok = h.read()
    with open(indice, 'wb') as h:
        h.write(b'basura que no es un indice de git')
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba')
    caso('git status que falla (indice roto): SIN DATOS, no "arbol limpio"', rc == 2 and 'limpio' not in out, out[:300])
    with open(indice, 'wb') as h:
        h.write(indice_ok)
    otro_wt = os.path.join(tmp, 'wt-abierto')
    sh(repo, 'git', 'worktree', 'add', '-q', otro_wt, '-b', 'task/999-otra')
    rc, out = script('gate-worktree.py', '--repo', repo, '--base', 'develop', '--rama', 'task/1234-prueba', '--techo', '1', '--json')
    d = json.loads(out)
    caso('con el techo alcanzado (1 abierto, techo 1): FRENA y dice cuantos hay y cual es el techo',
         rc == 1 and d['worktrees_abiertos'] == 1 and any('techo es 1' in m for m in d['motivos']), out[:300])
    sh(repo, 'git', 'worktree', 'remove', '--force', otro_wt)

    print('== verificar-tdd')
    sh(repo, 'git', 'checkout', '-q', '-b', 'task/1234-prueba')
    escribir(repo, 'tests/uno_test.txt', 'assert uno\n')
    commit(repo, 'test(rojo): 1 uno devuelve ok')
    escribir(repo, 'src/uno.txt', 'uno\n')
    commit(repo, 'uno: implementacion minima')
    escribir(repo, 'tests/dos_test.txt', 'assert dos\n')
    escribir(repo, 'src/dos.txt', 'dos\n')
    commit(repo, 'test(rojo): 2 dos (trae produccion, invalido)')
    escribir(repo, 'tests/guarda_test.txt', 'guardarrail\n')
    commit(repo, 'test(guardarrail): la guarda nace verde')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '3', '--id', '1234', '--json')
    d = json.loads(out)
    caso('item 1 cumple', d['items']['1']['veredicto'] == 'cumple', out[:300])
    caso('item 2 evidencia invalida (trae produccion)', d['items']['2']['veredicto'] == 'evidencia invalida')
    caso('item 3 falta', d['items']['3']['veredicto'] == 'falta')
    caso('veredicto HALLAZGO y exit 1', rc == 1 and d['estado'] == 'HALLAZGO')
    caso('avisa que no existe evidencia/1234', any('evidencia/1234' in v for v in d['avisos']))
    sh(repo, 'git', 'branch', 'evidencia/1234', 'HEAD')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '2', '--id', '1234', '--json')
    d = json.loads(out)
    caso('encuentra evidencia/1234 y el diff contra la rama esta vacio', d['evidencia'] == 'evidencia/1234' and d['diff_evidencia_vs_rama'] == 'vacio')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', 'HEAD', '--json')
    caso('sin commits en el rango: SIN DATOS', rc == 2)
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '3', '--modo', 'test-despues', '--motivo', 'esqueleto del repo', '--json')
    d = json.loads(out)
    caso('modo test-despues con motivo: red minima OK, sin rojo por item', rc == 0 and d['modo'] == 'test-despues' and any('red minima' in v for v in d['avisos']), out[:300])
    caso('modo test-despues: lo que no mira nombra la mutacion del verificador', any('mutacion' in v for v in d['no_mira']), out[:300])
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '3', '--modo', 'test-despues', '--json')
    d = json.loads(out)
    caso('modo test-despues SIN motivo: se audita como tdd y se marca', rc == 1 and d['modo'] == 'tdd' and any('SIN motivo' in h for h in d['hallazgos']), out[:300])
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '3', '--modo', 'test-despues')
    caso('sin --json tambien se imprimen los hallazgos que no son de un item', rc == 1 and 'hallazgo: modo test-despues declarado SIN motivo' in out, out[:300])
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--modo', 'sin-tests', '--motivo', 'spike', '--json')
    caso('modo sin-tests: SIN DATOS declarado', rc == 2 and 'sin-tests' in out)
    sh(repo, 'git', 'checkout', '-q', '-b', 'task/777-caract', base)
    escribir(repo, 'src/viejo.txt', 'cambio sin red\n')
    commit(repo, 'refactor: toco produccion antes de congelar')
    escribir(repo, 'tests/viejo_test.txt', 'congela\n')
    commit(repo, 'test(caracterizacion): congela lo que hace hoy')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--modo', 'caracterizacion', '--json')
    d = json.loads(out)
    caso('modo caracterizacion: produccion antes de congelar es HALLAZGO', rc == 1 and any('antes de congelar' in h for h in d['hallazgos']), out[:300])
    sh(repo, 'git', 'checkout', '-q', '-b', 'task/778-caract', base)
    escribir(repo, 'tests/viejo_test.txt', 'congela\n')
    commit(repo, 'test(caracterizacion): congela lo que hace hoy')
    escribir(repo, 'src/viejo.txt', 'cambio con red\n')
    commit(repo, 'refactor: ahora si')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--modo', 'caracterizacion', '--json')
    caso('modo caracterizacion: congelar primero es OK', rc == 0, out[:300])
    sh(repo, 'git', 'checkout', '-q', '-b', 'task/901-firma', base)
    escribir(repo, 'src/firmas.txt', 'firmas vacias' + chr(10))
    commit(repo, 'chore(firma): firmas minimas para que el rojo llegue a la asercion')
    escribir(repo, 'tests/uno_test.txt', 'assert uno' + chr(10))
    commit(repo, 'test(rojo): 1 uno')
    escribir(repo, 'src/uno.txt', 'uno' + chr(10))
    commit(repo, 'feat: uno')
    escribir(repo, 'tests/dos_test.txt', 'assert dos' + chr(10))
    commit(repo, 'test(verde-de-entrada): 2 ya lo cubria el verde del 1')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--items', '2', '--json')
    d = json.loads(out)
    caso('chore(firma) no cuenta como produccion antes del rojo y verde-de-entrada cumple', rc == 0 and d['items']['2']['veredicto'].startswith('cumple') and not any('antes del primer rojo' in v for v in d['avisos']), out[:300])
    sh(repo, 'git', 'checkout', '-q', '-b', 'task/902-sin-rojo', base)
    escribir(repo, 'src/tres.txt', 'tres' + chr(10))
    commit(repo, 'feat: tres, sin test primero')
    escribir(repo, 'tests/tres_test.txt', 'assert tres' + chr(10))
    commit(repo, 'test: tres, escrito despues')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--json')
    d = json.loads(out)
    caso('modo tdd sin ningun commit de rojo y con produccion: SIN DATOS (2), no OK', rc == 2 and d['estado'] == 'SIN DATOS' and any('ningun commit test(rojo)' in s for s in d['sin_datos']), out[:300])
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base)
    caso('sin --json el motivo tambien se imprime', rc == 2 and 'sin datos: cambios de produccion y ningun commit test(rojo)' in out, out[:300])
    escribir(repo, 'tests/cuatro_test.txt', 'assert cuatro' + chr(10))
    commit(repo, 'test(verde-de-entrada): 1 sin ningun rojo antes')
    rc, out = script('verificar-tdd.py', '--repo', repo, '--base', base, '--json')
    caso('un verde-de-entrada sin ningun rojo no tapa la falta de evidencia: SIN DATOS (2)', rc == 2, out[:300])
    sh(repo, 'git', 'checkout', '-q', 'task/1234-prueba')

    print('== datos-cierre')
    rc, out = script('datos-cierre.py', '--repo', repo, '--base', base, '--id', '1234', '--json')
    d = json.loads(out)
    caso('rama y conteo de commits', d['rama'] == 'task/1234-prueba' and d['commits_desde_base'] == 4, out[:200])
    caso('no esta pusheada (sin remoto)', d['pusheada'] is False and d['evidencia']['local'] is True)
    caso('sin remoto: exit 1 y link del MR sin dato', rc == 1 and d['link_merge_request_nuevo'] is None)
    sh(repo, 'git', 'remote', 'add', 'origin', 'git@gitlab.example.com:grupo/proyecto.git')
    rc, out = script('datos-cierre.py', '--repo', repo, '--base', 'develop', '--json')
    d = json.loads(out)
    caso('arma el link del MR desde el remoto ssh', (d['link_merge_request_nuevo'] or '').startswith('https://gitlab.example.com/grupo/proyecto/-/merge_requests/new?'))

    print('== auditar-diff')
    diff = os.path.join(tmp, 'cambios.diff')
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/src/config.properties\n+++ b/src/config.properties\n@@ -1,2 +1,4 @@\n linea\n+password = "SuperSecreta123"\n+usuario = <persona>\n+contacto = juan.perez@empresa-real.com\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('contrasena escrita: HALLAZGO', rc == 1 and any('contrasena' in h for h in d['hallazgos']), out[:300])
    caso('correo real: aviso', any('correo' in v for v in d['avisos']))
    caso('el marcador <persona> no es hallazgo', not any('config.properties:3' in h for h in d['hallazgos']))
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/docs/guia.md\n+++ b/docs/guia.md\n@@ -1 +1,2 @@\n hola\n+una linea mas de documentacion\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('solo documentacion: OK con aviso', rc == 0 and any('documentacion' in v for v in d['avisos']))
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('')
    rc, out = script('auditar-diff.py', '--archivo', diff)
    caso('diff vacio: SIN DATOS', rc == 2)
    rc, out = script('auditar-diff.py', '--repo', repo, '--base', 'develop', '--id', '9999', '--json')
    d = json.loads(out)
    caso('desde el repo: lee el diff de la rama y avisa que la rama no nombra la Tarea', d['lineas_agregadas'] > 0 and any('no nombra' in v for v in d['avisos']), out[:300])

    print('== inventariar-codigo')
    escribir(repo, 'openapi.yaml', 'openapi: 3.0.0\n')
    escribir(repo, 'db/migrations/V1__inicial.sql', 'create table x(id int); -- TODO indice\n')
    escribir(repo, 'Dockerfile', 'FROM scratch\n')
    escribir(repo, '.env', 'CLAVE=valor\n')
    rc, out = script('inventariar-codigo.py', repo, '--json')
    d = json.loads(out)
    caso('inventario OK con contrato, migraciones, contenedor, secreto y deuda',
         rc == 0 and d['contratos_api'] == ['openapi.yaml'] and d['migraciones'] and d['contenedores'] == ['Dockerfile']
         and '.env' in d['posibles_secretos'] and d['deuda_declarada'] >= 1, out[:400])
    caso('cuenta los tests y el repositorio', d['tests']['archivos_de_test'] == 3 and d['repositorio'].get('rama') == 'task/1234-prueba')
    caso('trae las filas medibles para DEC-004', len(d['dec_004']) == 6 and any('contrato' in f['criterio'].lower() and f['medido'].startswith('hay') for f in d['dec_004']))
    rc, out = script('inventariar-codigo.py', repo)
    caso('en texto imprime el bloque Para DEC-004', rc == 0 and 'Para DEC-004' in out)
    vacio = os.path.join(tmp, 'vacio')
    os.makedirs(vacio)
    rc, out = script('inventariar-codigo.py', vacio)
    caso('carpeta vacia: SIN DATOS', rc == 2)

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
