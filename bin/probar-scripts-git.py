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
        h.write('--- a/src/contador.c\n+++ b/src/contador.c\n@@ -1 +1,3 @@\n int x;\n+++ contador;\n'
                '+token = "abcdefghij123456"\n'
                '--- a/datos/clientes.csv\n+++ b/datos/clientes.csv\n@@ -0,0 +1,2 @@\n'
                '+Ana,11 4567-8901\n+4111111111111111\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('una linea agregada que empieza con "++" no se toma por cabecera: el secreto sigue en su archivo y linea',
         any(h.startswith('src/contador.c:3') for h in d['hallazgos']), out[:400])
    caso('en un archivo de datos avisan el telefono argentino (el criterio de phi.py) y la tarjeta',
         any('clientes.csv:1' in v and 'telefono' in v for v in d['avisos'])
         and any('clientes.csv:2' in v and 'tarjeta' in v for v in d['avisos']), out[:500])
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/datos/semilla.json\n+++ b/datos/semilla.json\n@@ -0,0 +1,5 @@\n'
                '+{"tel":"+54 11 4567 8901"}\n+{"cuil":"20301234563"}\n+{"dni":30123456}\n'
                '+{"cuit":"20-30123456-3"}\n+{"dni":"30.123.456"}\n'
                '--- a/src/rangos.py\n+++ b/src/rangos.py\n@@ -0,0 +1,3 @@\n+RANGO = "1000-2000"\n+VERSION = "1.234.567"\n+ID = 123456789\n'
                '--- a/db/v2.sql\n+++ b/db/v2.sql\n@@ -1,2 +1,2 @@\n--- comentario viejo\n+++ comentario nuevo\n'
                ' select 1;\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('en datos: telefono con espacios, CUIL sin guiones, DNI en JSON compacto, CUIT con guiones y DNI con puntos, cada uno avisa',
         all(any('semilla.json:%d' % i in v for v in d['avisos']) for i in range(1, 6)), out[:700])
    caso('en el codigo, un rango, una version con puntos o un numero suelto no avisan como telefono o documento',
         not any('rangos.py' in v for v in d['avisos']), out[:700])
    with open(diff + '.ff', 'w', encoding='utf-8', newline='') as h:
        h.write('--- a/src/ff.py\n+++ b/src/ff.py\n@@ -0,0 +1,3 @@\n+a = 1\x0cb = 2\n+c = "x y"\n'
                '+token = "abcdefghij123456"\n')
    rc_ff, out_ff = script('auditar-diff.py', '--archivo', diff + '.ff', '--json')
    caso('un salto de pagina o un U+2028 en una linea no descuadra el bloque: el secreto de la linea 3 se ve',
         rc_ff == 1 and any(h.startswith('src/ff.py:3') for h in json.loads(out_ff)['hallazgos']), out_ff[:400])
    caso('un comentario SQL borrado ("--- ...") no se toma por cabecera: la linea agregada queda en db/v2.sql:1',
         d['lineas_agregadas'] == 9 and 'db/v2.sql' in d['archivos'], out[:400])
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/ci/runner.toml\n+++ b/ci/runner.toml\n@@ -0,0 +1,3 @@\n+a = glrtr-abcdefghijklmnopqrstuv\n'
                '+b = glsoat-abcdefghijklmnopqrstuv\n+c = glrtrx-abcdefghijklmnopqrstuv\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('los prefijos de token de GitLab de la tabla oficial (glrtr-, glsoat-) son HALLAZGO; uno inventado (glrtrx-) no',
         any(h.startswith('ci/runner.toml:1') for h in d['hallazgos']) and any(h.startswith('ci/runner.toml:2') for h in d['hallazgos'])
         and not any(h.startswith('ci/runner.toml:3') for h in d['hallazgos']), out[:400])
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
    caso('desde el repo, sin palabras de cierre en los mensajes: ningun hallazgo de cierre',
         not any('cierra' in h for h in d['hallazgos']), out[:300])
    escribir(repo, 'src/app.txt', 'base\ncambio con enlace\n')
    commit(repo, 'feat: enlaza la tarjeta\n\nAB#1234 y Related to #12, sin cerrar nada')
    rc, out = script('auditar-diff.py', '--repo', repo, '--base', 'develop', '--json')
    d = json.loads(out)
    caso('un mensaje que solo enlaza (AB#1234, Related to #12) no es hallazgo', not any('cierra' in h for h in d['hallazgos']), out[:300])
    escribir(repo, 'src/app.txt', 'base\ncambio con enlace\ncambio que cierra\n')
    commit(repo, 'fix: cierra por afuera\n\nFixes AB#1234\nCloses: grupo/proyecto#7')
    rc, out = script('auditar-diff.py', '--repo', repo, '--base', 'develop', '--json')
    d = json.loads(out)
    cierres = [h for h in d['hallazgos'] if 'cierra' in h]
    caso('un mensaje de commit con "Fixes AB#1234" o "Closes: grupo/proyecto#7": HALLAZGO por cada uno, con el commit',
         rc == 1 and len(cierres) == 2 and all('mensaje de commit' in h for h in cierres), out[:500])
    caso('con --archivo no hay mensajes que leer: lo dice en lo que no mira',
         any('mensajes de commit' in x for x in json.loads(script('auditar-diff.py', '--archivo', diff + '.ff', '--json')[1])['no_mira']))
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/src/conexion.cfg\n+++ b/src/conexion.cfg\n@@ -0,0 +1,3 @@\n'
                '+DefaultEndpointsProtocol=https;AccountName=x;AccountKey=' + 'A' * 86 + '==\n'
                '+gh = github_pat_' + 'a1' * 30 + '\n'
                '+ia = sk-proj_' + 'b2' * 20 + '\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('el criterio comun de secretos.py: AccountKey=, github_pat_ y sk-proj_ son HALLAZGO (antes pasaban)',
         rc == 1 and all(any(h.startswith('src/conexion.cfg:%d' % i) for h in d['hallazgos']) for i in (1, 2, 3)), out[:500])
    caso('el valor del secreto no se imprime', 'AAAAAAAAAA' not in out and 'a1a1a1a1' not in out, out[:300])
    with open(diff, 'w', encoding='utf-8') as h:
        h.write('--- a/src/app.py\n+++ b/src/app.py\n@@ -0,0 +1,2 @@\n+password = "SuperSecreta123"  # <persona>\n'
                '+url = "postgres://admin:clave123@db.example.com/x"\n')
    rc, out = script('auditar-diff.py', '--archivo', diff, '--json')
    d = json.loads(out)
    caso('se conservan la regla de "clave o contrasena escrita" (aunque la linea tenga un marcador) y la de URL con usuario',
         rc == 1 and any(h.startswith('src/app.py:1') for h in d['hallazgos']) and any(h.startswith('src/app.py:2') for h in d['hallazgos']), out[:500])

    # una rama SIN commits propios, cuya base tiene un merge ajeno con "Closes #12": no es de esta rama
    repo2 = os.path.join(tmp, 'repo2')
    os.makedirs(repo2)
    sh(repo2, 'git', 'init', '-q', '-b', 'develop')
    sh(repo2, 'git', 'config', 'user.name', 'Prueba')
    sh(repo2, 'git', 'config', 'user.email', 'prueba@example.com')
    escribir(repo2, 'a.txt', 'a\n')
    commit(repo2, 'base')
    escribir(repo2, 'a.txt', 'a\nb\n')
    commit(repo2, 'Merge branch otra\n\nCloses #12')
    sh(repo2, 'git', 'checkout', '-q', '-b', 'task/77-sin-commits')
    escribir(repo2, 'a.txt', 'a\nb\nc sin commitear\n')
    rc, out = script('auditar-diff.py', '--repo', repo2, '--base', 'develop', '--json')
    d = json.loads(out)
    caso('rama sin commits propios: develop..HEAD resuelve (vacio) y se queda ahi; el "Closes #12" ajeno no frena',
         not any('cierra' in h for h in d['hallazgos']), out[:500])
    rc, out = script('auditar-diff.py', '--repo', repo2, '--base', 'no-existe', '--json')
    d = json.loads(out)
    caso('si ningun rango de mensajes resuelve, no cae a HEAD~1..HEAD: lo dice en lo que no mira',
         not any('cierra' in h for h in d['hallazgos']) and any('mensajes de commit' in x for x in d['no_mira']), out[:500])
    escribir(repo2, 'a.txt', 'a\nb\n')
    sh(repo2, 'git', 'checkout', '-q', '-b', 'task/78-cierra')
    escribir(repo2, 'a.txt', 'a\nb\nd\n')
    commit(repo2, 'fix: varios\n\nCloses issue #12\nFixes issues #13 and #14')
    rc, out = script('auditar-diff.py', '--repo', repo2, '--base', 'develop', '--json')
    d = json.loads(out)
    caso('"Closes issue #12" y "Fixes issues #13": HALLAZGO (cierre.py admite la palabra issue en el medio)',
         rc == 1 and len([h for h in d['hallazgos'] if 'cierra' in h]) == 2, out[:500])

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
