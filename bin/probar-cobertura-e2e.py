#!/usr/bin/env python3
"""Prueba de bin/cobertura-e2e.py sobre Historias y pruebas de mentira.
Se corre:  python -B bin/probar-cobertura-e2e.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'cobertura-e2e.py')
ESPERADOS = []
MEDIO = '·'


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def escribir(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(t)


def main():
    print('== cobertura-e2e')
    tmp = tempfile.mkdtemp(prefix='probar-cob-')
    bl = os.path.join(tmp, 'backlog')
    escribir(os.path.join(bl, '3-cancelar.md'), '---\nid: 3\ntipo: Historia\ntitulo: "Cancelar una reserva"\n---\n\nEscenario: Cancelar una reserva activa\n  Dado x\n  Cuando y\n  Entonces z\n\nEscenario: Cancelar una ya cancelada\n  Dado x\n  Cuando y\n  Entonces z\n')
    escribir(os.path.join(bl, '4-ver.md'), '---\nid: 4\ntipo: Historia\ntitulo: "Ver las reservas"\n---\n\nEscenario: Sala sin reservas\n  Dado x\n  Cuando y\n  Entonces z\n')
    escribir(os.path.join(bl, '5-tarea.md'), '---\nid: 5\ntipo: Tarea\ntitulo: "Una Tarea"\n---\n\nEscenario: No cuenta (es Tarea)\n  Dado x\n')
    qa = os.path.join(tmp, 'qa')
    escribir(os.path.join(qa, 'tests', 'h3.spec.ts'), "import { test } from '@playwright/test';\n// Historia #3 %s Escenario: Cancelar una reserva activa\ntest('Escenario: Cancelar una reserva activa', async ({ page }) => {\n  await page.goto('/');\n});\n\n// Historia #3 %s Escenario: Cancelar una ya cancelada\ntest('Escenario: Cancelar una ya cancelada', async ({ page }) => {\n  test.fixme(true, 'sin automatizar');\n});\n" % (MEDIO, MEDIO))
    escribir(os.path.join(qa, 'node_modules', 'x', 'h.spec.ts'), '// Historia #4 %s Escenario: Sala sin reservas\n' % MEDIO)
    rc, out = correr(qa, '--historias', bl)
    caso('HALLAZGO (1): 1 automatizado, 1 esqueleto, 1 sin prueba; la Tarea no cuenta; node_modules se ignora', rc == 1 and '1 automatizado(s), 1 solo esqueleto, 1 sin prueba' in out and '3 Escenario(s)' in out, out[:400])
    rc, out = correr(qa, '--historias', bl, '--json')
    d = json.loads(out)
    caso('--json: filas con estado por Escenario', d['veredicto'] == 'HALLAZGO' and {f['escenario']: f['estado'] for f in d['filas']}['Cancelar una ya cancelada'] == 'esqueleto')
    escribir(os.path.join(qa, 'tests', 'h3.spec.ts'), "// Historia #3 %s Escenario: Cancelar una reserva activa\ntest('a', async () => {});\n// Historia #3 %s Escenario: Cancelar una ya cancelada\ntest('b', async () => {});\n" % (MEDIO, MEDIO))
    escribir(os.path.join(qa, 'tests', 'h4.test.py'), "# Historia #4 - Escenario: Sala sin reservas\ndef test_sala(): pass\n")
    rc, out = correr(qa, '--historias', bl, '--mermaid')
    caso('todo automatizado (traza con guion tambien vale): OK (0) y el mermaid', rc == 0 and 'pie title' in out, out[:300])
    rc, out = correr(qa, '--historias', os.path.join(bl, '4-ver.md'))
    caso('con un archivo de Historia suelto: OK (0)', rc == 0)
    rc, out = correr(os.path.join(tmp, 'no'), '--historias', bl)
    caso('carpeta de pruebas inexistente: SIN DATOS (2)', rc == 2)
    rc, out = correr(qa, '--historias', os.path.join(bl, '5-tarea.md'))
    caso('sin Historias con Gherkin: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
