#!/usr/bin/env python3
"""Prueba de bin/atajos.py sobre repos de mentira (con y sin git).
Se corre:  python -B bin/probar-atajos.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'atajos.py')
ESPERADOS = []

DEUDA = """# Deuda tecnica

## Abiertas

| # | Qué | Dónde | Por qué se aceptó | Riesgo | Cuándo se paga | Fuente |
|---|---|---|---|---|---|---|
| DT-001 | <qué está mal> | `<modulo>/…` | <la razón> | <qué puede pasar> | `#NNNN` | Doctor |
| DT-002 | Lee el archivo entero | `importar/` | Plazo | Memoria | #77 | !12 |

## Pagadas

| # | Qué | Cómo se pagó | Fecha |
|---|---|---|---|
| DT-003 | Sin paginacion | #80 | 2026-11-01 |
"""


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def escribir(p, t, binario=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if binario:
        with open(p, 'wb') as h:
            h.write(t)
        return
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(t)


def main():
    print('== atajos')
    tmp = tempfile.mkdtemp(prefix='probar-atajos-')
    app = os.path.join(tmp, 'app')
    escribir(os.path.join(app, 'src', 'a.py'), 'def leer(p):\n    # atajo: lee todo en memoria, alcanza hasta ~50 MB; cuando lleguen archivos grandes, DT-002\n    return open(p).read()\n')
    escribir(os.path.join(app, 'src', 'b.js'), 'let n = 0; // atajo: contador en memoria; cuando haya dos instancias #1234\n')
    escribir(os.path.join(app, 'src', 'c.ts'), '/* atajo: sin reintentos, cuando el proveedor falle seguido DT-002 */\nexport const x = 1;\n')
    escribir(os.path.join(app, 'src', 'd.js'), 'const s = "la marca atajo: no es comentario";\n')
    escribir(os.path.join(app, 'node_modules', 'x', 'i.js'), '// atajo: no se mira\n')
    escribir(os.path.join(app, 'README.md'), '# atajo: los docs no cuentan\n')
    escribir(os.path.join(app, 'img.bin'), b'\x00\x01// atajo: binario\n', binario=True)

    rc, out = correr('--repo', app)
    caso('sin git: 3 marcas con limite y disparador -> OK (0); prosa, node_modules, docs y binarios no cuentan',
         rc == 0 and '3 marca(s)' in out and 'OK -- 3 atajo(s)' in out, out[:500])
    caso('el cierre */ no queda dentro del disparador', 'cuando: el proveedor falle seguido |' in out, out[:500])
    caso('sin --deuda avisa que no chequeo los DT-nnn', 'sin --deuda no se chequeo' in out, out[:500])

    escribir(os.path.join(app, 'src', 'e.sql'), 'SELECT 1; -- atajo: sin indice en la tabla grande\n')
    escribir(os.path.join(app, 'src', 'f.java'), '    // atajo: ; cuando haya mas de mil filas #9\n')
    rc, out = correr('--repo', app)
    caso('atajo sin disparador y atajo sin limite -> HALLAZGO (1)',
         rc == 1 and 'sin disparador' in out and 'sin limite' in out and '2 de 5 atajo(s) con problema' in out, out[:600])
    caso('atajo sin #ID ni DT-nnn -> AVISO (no cambia el veredicto)', 'AVISO: 1 atajo(s) sin #ID ni DT-nnn' in out, out[:600])

    rc, out = correr('--repo', app, '--json')
    d = json.loads(out)
    por = {x['archivo'].split('/', 1)[1]: x for x in d['atajos']}
    caso('--json: veredicto, archivos leidos y problemas por marca',
         d['veredicto'] == 'HALLAZGO' and d['archivos_leidos'] == 6
         and por['src/e.sql']['problemas'] == ['sin disparador (cuando ...)']
         and por['src/a.py']['refs'] == ['DT-002'] and por['src/b.js']['refs'] == ['#1234'], out[:600])

    os.remove(os.path.join(app, 'src', 'e.sql'))
    os.remove(os.path.join(app, 'src', 'f.java'))
    deuda = os.path.join(tmp, 'deuda.md')
    escribir(deuda, DEUDA)
    rc, out = correr('--repo', app, '--deuda', deuda)
    caso('--deuda con DT-002 abierta: OK (0)', rc == 0, out[:500])
    escribir(os.path.join(app, 'src', 'g.py'), '# atajo: x; cuando y, DT-001\n# atajo: z; cuando w DT-003\n# atajo: q; cuando r dt-009\n')
    rc, out = correr('--repo', app, '--deuda', deuda)
    caso('--deuda: la fila de ejemplo (DT-001) y un DT inexistente no cuentan como abiertos; uno pagado se marca',
         rc == 1 and 'DT-001 no esta abierta' in out and 'DT-009 no esta abierta' in out
         and 'DT-003 figura como pagada' in out, out[:700])

    rc, out = correr('--repo', os.path.join(tmp, 'no-existe'))
    caso('carpeta inexistente: SIN DATOS (2)', rc == 2, out[:200])
    vacio = os.path.join(tmp, 'vacio')
    escribir(os.path.join(vacio, 'NOTAS.md'), 'solo docs\n')
    rc, out = correr('--repo', vacio)
    caso('cero archivos de codigo leidos: SIN DATOS (2), no OK', rc == 2 and 'cero archivos' in out, out[:200])
    rc, out = correr('--repo', app, '--deuda', os.path.join(tmp, 'no.md'))
    caso('--deuda inexistente: SIN DATOS (2)', rc == 2, out[:200])

    # strings, JSX y comentarios pegados al codigo; salida UTF-8 aunque se redirija
    app2 = os.path.join(tmp, 'app2')
    escribir(os.path.join(app2, 'src', 'h.js'),
             'const s = "ver // atajo: x";\n'
             "const t = '# atajo: tampoco';\n"
             'foo();// atajo: pegado al codigo; cuando haya colas #1\n')
    escribir(os.path.join(app2, 'src', 'i.jsx'),
             'return <div>{/* atajo: sin paginar; cuando pasen 100 filas #2 */}</div>;\n')
    escribir(os.path.join(app2, 'src', 'j.py'), '# atajo: sólo una instancia → memoria; cuando haya dos #3\n')
    rc, out = correr('--repo', app2)
    caso('lo que esta dentro de un string no cuenta; JSX {/* */} y // pegado al codigo si: 3 marcas, OK (0)',
         rc == 0 and '3 marca(s)' in out and 'tampoco' not in out and 'cuando: x' not in out, out[:600])
    caso('el cierre */} de JSX y lo que sigue no quedan en el disparador', 'cuando: pasen 100 filas |' in out, out[:600])
    r = subprocess.run([sys.executable, '-I', SCRIPT, '--repo', app2, '--json'], capture_output=True)
    try:
        d = json.loads(r.stdout.decode('utf-8'))
        ok = any(x['limite'] == 'sólo una instancia → memoria' for x in d['atajos'])
    except (UnicodeDecodeError, ValueError) as e:
        ok, d = False, '%s: %s' % (type(e).__name__, e)
    caso('--json sale en UTF-8 aunque se redirija: acentos y flechas intactos', ok, str(d)[:300])
    escribir(os.path.join(app2, 'src', 'k.py'),
             'msg = "can\'t"  # atajo: cache en memoria; cuando haya dos procesos #5\n'
             'c = \'"\'  # atajo: sin escape; cuando haya caracteres raros #6\n')
    rc, out = correr('--repo', app2)
    caso('una comilla suelta DENTRO de un string cerrado no esconde la marca que sigue: 5 marcas',
         rc == 0 and '5 marca(s)' in out, out[:700])
    caso('las lineas descartadas por string se listan como AVISO (no se esconden)',
         'AVISO: 1 linea(s) con algo que parece una marca dentro de un string' in out and 'app2/src/h.js:1' in out,
         out[-700:])
    rc, out = correr('--repo', app2, '--repo', vacio)
    caso('dos repos y uno sin codigo: SIN DATOS (2); el otro no lo tapa', rc == 2 and 'vacio' in out, out[:300])

    # con git: respeta el .gitignore y cuenta lo que todavia no se agrego
    repo = os.path.join(tmp, 'repo')
    escribir(os.path.join(repo, '.gitignore'), 'generado/\n')
    escribir(os.path.join(repo, 'generado', 'x.js'), '// atajo: ignorado por git\n')
    escribir(os.path.join(repo, 'src', 'nuevo.py'), '# atajo: un solo proceso; cuando haya dos #5\n')
    r = subprocess.run(['git', 'init', '-q', repo], capture_output=True)
    if r.returncode != 0:
        caso('con git (git init)', False, 'no se pudo inicializar un repo de prueba')
    else:
        rc, out = correr('--repo', repo)
        caso('con git: respeta .gitignore y cuenta lo no agregado -> OK (0), 1 marca',
             rc == 0 and '1 marca(s)' in out and 'ignorado por git' not in out, out[:400])
        rc, out = correr('--repo', os.path.join(repo, 'src'))
        caso('una carpeta de adentro de un repo, que no es su raiz: SIN DATOS (2), no lista el repo de afuera',
             rc == 2 and 'no es su raiz' in out, out[:300])

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        # el detalle de un caso que falla puede traer acentos o flechas: que se vea, no que tire la prueba
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
