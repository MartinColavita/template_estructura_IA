#!/usr/bin/env python3
"""Prueba de bin/adoptar-proyecto.py con un proyecto de mentira: enlaza en una carpeta temporal (no toca back/ del nucleo).
Se corre:  python -B bin/probar-adoptar-proyecto.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'adoptar-proyecto.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def main():
    print('== adoptar-proyecto')
    tmp = tempfile.mkdtemp(prefix='probar-adoptar-')
    app = os.path.join(tmp, 'mi-app')
    escribir(app, 'CLAUDE.md', '# mi-app\n\n```bash\nnpm test\n```\n')
    escribir(app, 'src/server.js', "const app = require('express')();\napp.get('/salud', (q, r) => r.send('ok'));\n")
    destino = os.path.join(tmp, 'nucleo-back', 'mi-app')
    salida = os.path.join(tmp, 'salida')
    rc, out = correr(app, '--destino', destino, '--salida', salida, '--dry-run')
    caso('dry-run no crea nada', rc == 0 and not os.path.exists(destino) and not os.path.isdir(salida), out[:300])
    rc, out = correr(app, '--destino', destino, '--salida', salida)
    caso('enlaza y deja los cuatro informes (0)', rc == 0 and os.path.isdir(destino) and all(os.path.isfile(os.path.join(salida, f)) for f in ('01-relevamiento-ia.md', '02-inventario.md', '03-radiografia.md', '04-diagramas.md')), out[:400])
    caso('el proyecto sigue en su lugar y se ve por el enlace', os.path.isfile(os.path.join(app, 'CLAUDE.md')) and os.path.isfile(os.path.join(destino, 'CLAUDE.md')))
    caso('la radiografia encontro el endpoint', 'GET /salud' in open(os.path.join(salida, '03-radiografia.md'), encoding='utf-8').read())
    caso('muestra la linea de import sin tocar el CLAUDE.md', '@' in out and 'AGENTS.md' in out and 'no se toco' in out and 'AGENTS.md' not in open(os.path.join(app, 'CLAUDE.md'), encoding='utf-8').read())
    rc, out = correr(app, '--destino', destino, '--salida', salida)
    caso('destino existente: FRENA (1)', rc == 1 and 'ya existe' in out)
    if os.name == 'nt':
        os.rmdir(destino)
    else:
        os.unlink(destino)
    rc, out = correr(app, '--destino', destino, '--salida', salida, '--importar-reglas')
    texto = open(os.path.join(app, 'CLAUDE.md'), encoding='utf-8').read()
    caso('--importar-reglas agrega la linea @.../AGENTS.md al CLAUDE.md', rc == 0 and '/AGENTS.md' in texto and texto.count('AGENTS.md') == 1, texto[-200:])
    rc, out = correr(os.path.join(tmp, 'no-existe'), '--destino', os.path.join(tmp, 'x'))
    caso('ruta inexistente: FRENA (1)', rc == 1)
    try:
        if os.name == 'nt':
            os.rmdir(destino)
        else:
            os.unlink(destino)
    except OSError:
        pass
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
