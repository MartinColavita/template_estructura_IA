#!/usr/bin/env python3
"""Prueba de bin/armar-e2e.py sobre una Historia de mentira (archivo y tablero local).
Se corre:  python -B bin/probar-armar-e2e.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'armar-e2e.py')
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


HISTORIA = '''---
id: 7
tipo: Historia
titulo: "Cancelar una reserva"
estado: New
---

# Cancelar una reserva

## Criterios de aceptacion

Escenario: Cancelar una reserva activa
  Dado una reserva activa de la sala 1 de 10 a 12
  Cuando la cancelo
  Entonces su estado es cancelada

Escenario: Cancelar una reserva ya cancelada
  Dado una reserva cancelada
  Cuando la cancelo de nuevo
  Entonces recibo RESERVA_YA_CANCELADA

Escenario: Sin pasos todavia

## Notas para QA
- **Pantalla / ruta:** Reservas de la sala · /salas/1/reservas
- **Rol / usuario de prueba:** operador
- **Datos iniciales:** una reserva activa de <persona> de 10 a 12
- **Identificadores:** `<completar>`
- **Ambiente:** ⚠ a definir
'''


def main():
    print('== armar-e2e')
    tmp = tempfile.mkdtemp(prefix='probar-e2e-')
    h = os.path.join(tmp, 'historia.md'); escribir(h, HISTORIA)
    salida = os.path.join(tmp, 'qa', 'tests')
    rc, out = correr(h, '--motor', 'playwright', '--salida', salida, '--url', 'http://127.0.0.1:5173')
    caso('playwright: arma el esqueleto (0) y avisa el Escenario sin pasos', rc == 0 and 'sin pasos' in out, out[:300])
    spec = os.path.join(salida, 'historia-7-cancelar-una-reserva.spec.ts')
    t = open(spec, encoding='utf-8').read()
    caso('un test por Escenario con el titulo textual y la traza', t.count("test('Escenario: ") == 3 and ('Historia #7 %s Escenario: Cancelar una reserva activa' % MEDIO) in t)
    caso('los pasos del Gherkin viajan como comentarios y cada test nace fixme', '// Dado una reserva activa de la sala 1 de 10 a 12' in t and t.count('test.fixme') == 3)
    caso('la URL base queda como valor por defecto', "'http://127.0.0.1:5173'" in t)
    caso('las Notas para QA entran: la ruta va al goto y las lineas con valor como comentarios', "const RUTA = '/salas/1/reservas'" in t and 'page.goto(BASE + RUTA)' in t and '// Rol / usuario de prueba: operador' in t and 'Datos iniciales: una reserva activa' in t)
    caso('lo que falta en las Notas para QA (completar / a definir) se avisa como pregunta a la Historia', 'AVISO la Historia no trae' in out and 'identificadores estables' in out and 'ambiente' in out and 'rol' not in out.split('no trae en sus Notas para QA:')[1].split('.')[0])
    rc, out = correr(h, '--motor', 'playwright', '--salida', salida)
    caso('si ya existe con todos los Escenarios: OK (0) y no se toca', rc == 0 and 'no se toca' in out)
    escribir(spec, t.replace('// Historia #7 %s Escenario: Cancelar una reserva ya cancelada' % MEDIO, '// (borrado)'))
    rc, out = correr(h, '--motor', 'playwright', '--salida', salida)
    caso('si ya existe y le falta un Escenario: HALLAZGO (1) y lo nombra, sin pisar', rc == 1 and 'ya cancelada' in out and '(borrado)' in open(spec, encoding='utf-8').read())
    rc, out = correr(h, '--motor', 'proceso', '--salida', salida)
    py = os.path.join(salida, 'historia-7-cancelar-una-reserva.test.py')
    caso('proceso: unittest con skip por Escenario y el Gherkin en el docstring', rc == 0 and os.path.isfile(py) and open(py, encoding='utf-8').read().count("@unittest.skip") == 3 and 'Cuando la cancelo' in open(py, encoding='utf-8').read())
    r = subprocess.run([sys.executable, '-m', 'py_compile', py], capture_output=True)
    caso('proceso: el archivo compila', r.returncode == 0)
    rc, out = correr(h, '--motor', 'http', '--salida', os.path.join(tmp, 'qa2'))
    py2 = os.path.join(tmp, 'qa2', 'historia-7-cancelar-una-reserva.test.py')
    caso('http: usa E2E_BASE_URL y urllib', rc == 0 and 'E2E_BASE_URL' in open(py2, encoding='utf-8').read())
    # tablero local por #id
    nucleo = os.path.join(tmp, 'nucleo')
    escribir(os.path.join(nucleo, 'cerebro-digital', 'reservas', 'backlog', '7-cancelar.md'), HISTORIA)
    rc, out = correr('#7', '--motor', 'playwright', '--nucleo', nucleo)
    caso('por #id del tablero local: lo encuentra y escribe en qa/e2e/tests del nucleo', rc == 0 and os.path.isfile(os.path.join(nucleo, 'qa', 'e2e', 'tests', 'historia-7-cancelar-una-reserva.spec.ts')), out[:300])
    rc, out = correr('#99', '--motor', 'playwright', '--nucleo', nucleo)
    caso('#id inexistente: SIN DATOS (2)', rc == 2)
    escribir(os.path.join(tmp, 'sin.md'), '---\nid: 8\ntipo: Historia\ntitulo: "Sin gherkin"\n---\n\n# Sin gherkin\n\nTexto libre.\n')
    rc, out = correr(os.path.join(tmp, 'sin.md'), '--motor', 'playwright', '--salida', salida)
    caso('Historia sin Gherkin: SIN DATOS (2) y manda a redactar', rc == 2 and 'redactar' in out)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
