#!/usr/bin/env python3
"""Prueba de bin/armar-mision.py sobre ESTE repositorio del Cerebro (las rutas que cita tienen que existir)
y una Tarea de mentira en una carpeta temporal.
Se corre:  python -B bin/probar-armar-mision.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
NUCLEO = os.path.dirname(AQUI)
SCRIPT = os.path.join(AQUI, 'armar-mision.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout + r.stderr).replace(chr(92), '/')


def main():
    print('== armar-mision')
    tmp = tempfile.mkdtemp(prefix='probar-mision-')
    tarea = os.path.join(tmp, 'tarea.md')
    with open(tarea, 'w', encoding='utf-8') as h:
        h.write('# Tarea #1234 Crear reserva\n\n**Capa:** api + application. Contrato: endpoint POST /reservas (openapi).\n\n- **Modo de pruebas:** test-despues: esqueleto del repo\n\n## Tests a escribir PRIMERO\n1. reserva valida -> 201\n\n## Criterios de aceptacion\nEscenario: reserva valida\n  Dado un socio\n  Cuando reserva\n  Entonces 201\n')
    base = ['--id', '1234', '--titulo', 'Crear reserva', '--tarea', tarea, '--worktree', os.path.join(tmp, 'wt'),
            '--rama', 'task/1234-crear-reserva', '--sha-base', 'abc1234', '--nucleo', NUCLEO, '--repo', 'back', '--modulo', 'modulo-ejemplo']
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', *base)
    caso('worker: se arma (0)', rc == 0 and out.startswith('# Misi'), out[:300])
    caso('worker: pega la Tarea entera y el Gherkin del padre', 'reserva valida -> 201' in out and 'Escenario: reserva valida' in out)
    caso('worker: copia las 8 convenciones C1..C8 del orquestador', all(('**C%d**' % i) in out for i in range(1, 9)))
    caso('worker back sin migraciones: no manda a leer migracion-de-base.md', 'migracion-de-base.md' not in out)
    caso('worker: recibe guiar-tdd y armar-swagger, NO auditar-codigo', 'guiar-tdd' in out and 'armar-swagger' in out and 'auditar-codigo/SKILL.md' not in out)
    caso('worker: toma el modo de pruebas de la Tarea', 'test-despues: esqueleto del repo' in out)
    caso('worker: no repite el Gherkin (lo senala arriba)', out.count('Escenario: reserva valida') == 1 and 'está arriba' in out)
    caso('worker: C8 pendiente va en una linea, sin la fila entera', 'no te aplica' in out)
    caso('worker: canal IntelliJ', 'PREGUNTA-ORQUESTADOR' in out and 'TAREA-TERMINADA' in out)
    rc, out = correr('--rol', 'verificador', '--entorno', 'orca', '--motor', 'gemini', *base)
    caso('verificador: se arma (0)', rc == 0, out[:300])
    caso('verificador: recibe verificar-tdd, auditar-codigo y code-review.md, NO guiar-tdd', 'verificar-tdd/SKILL.md' in out and 'auditar-codigo/SKILL.md' in out and 'code-review.md' in out and 'guiar-tdd/SKILL.md' not in out)
    caso('verificador: C4 cuenta las marcas atajo: que agrega el cambio con atajos.py --base (el comando, no la convencion)',
         re.search(r'atajos\.py" --repo "[^"]+" --base \S+', out) is not None, out[:300])
    caso('verificador en modo test-despues: corre la mutacion sobre las lineas nuevas', 'Modo test-después' in out and 'mutación' in out, out[:300])
    for literal, esperado in (('test-después: esqueleto del repo', '--modo test-despues --motivo "esqueleto del repo"'),
                              ('caracterización primero', '--modo caracterizacion`')):
        rc2, out2 = correr('--rol', 'verificador', '--entorno', 'intellij', '--motor', 'claude', '--modo-pruebas', literal, *base)
        caso('el modo tal como lo escribe la plantilla (%s) llega a verificar-tdd sin tildes' % literal.split(':')[0], rc2 == 0 and esperado in out2, out2[:200])
    caso('verificador: el comando de verificar-tdd lleva --modo y --motivo de la Tarea', '--modo test-despues --motivo "esqueleto del repo"' in out, out[:200])
    caso('verificador: bloque VEREDICTO canonico y las dos clases de SIN DATOS', 'VEREDICTO-INICIO' in out and 'VEREDICTO-FIN' in out and 'pendiente declarado' in out)
    caso('verificador Gemini en Orca: canal por lineas', 'PREGUNTA-ORQUESTADOR' in out)
    rc, out = correr('--rol', 'worker', '--entorno', 'orca', '--motor', 'claude', *base)
    caso('worker Claude en Orca: canal ask/worker_done', 'worker_done' in out)
    with open(tarea, 'w', encoding='utf-8') as h:
        h.write('# Tarea sin gherkin\n\n## Tests a escribir PRIMERO\n1. algo\n')
    rc, out = correr('--rol', 'verificador', '--entorno', 'intellij', '--motor', 'claude', *base)
    caso('sin Gherkin del padre: lo avisa y el modo cae a tdd', rc == 0 and 'SIN DATOS' in out and 'queda **SIN DATOS**' in out and '--modo tdd' in out, out[:300])
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', *base)
    caso('Tarea sin API: no manda a leer endpoint ni contrato', 'no hace falta leer' in out and 'crear-endpoint.md` — cómo' not in out)
    salida = os.path.join(tmp, 'salida', 'mision.md')
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'gemini', '--out', salida, *base)
    caso('--out escribe el archivo', rc == 0 and os.path.isfile(salida) and 'mision escrita' in out)
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', *base[:-2], '--modulo', 'no-existe')
    caso('modulo inexistente: SIN DATOS (2) y lista lo que falta', rc == 2 and 'no existen' in out, out[:300])
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', *[x if x != tarea else os.path.join(tmp, 'nada.md') for x in base])
    caso('Tarea inexistente: SIN DATOS (2)', rc == 2)
    # front: sin las convenciones del back; base: migraciones controladas
    h.close() if False else None
    tarea_front = os.path.join(tmp, 'tarea-front.md')
    with open(tarea_front, 'w', encoding='utf-8') as hf:
        hf.write('# Tarea #7 Pantalla lista\n\n- **Modo de pruebas:** TDD\n\n## Tests a escribir PRIMERO\n\n1. render\n\n## Criterios de aceptacion (Gherkin de la Historia padre)\n\nEscenario: ver lista\n  Dado x\n  Cuando y\n  Entonces z\n')
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', '--id', '7', '--titulo', 'Pantalla', '--tarea', tarea_front, '--worktree', 'C:/wt', '--rama', 'task/7', '--sha-base', 'abc', '--nucleo', NUCLEO, '--repo', 'front', '--modulo', 'modulo-ejemplo')
    caso('front: no copia C1, C2 ni C5 y manda a frontend/reglas-generales', rc == 0 and '**C1**' not in out and '**C5**' not in out and '**C3**' in out and 'no aplican a este repositorio' in out, out[:400])
    rc, out = correr('--rol', 'verificador', '--entorno', 'intellij', '--motor', 'claude', '--id', '7', '--titulo', 'Pantalla', '--tarea', tarea_front, '--worktree', 'C:/wt', '--rama', 'task/7', '--sha-base', 'abc', '--nucleo', NUCLEO, '--repo', 'front', '--modulo', 'modulo-ejemplo')
    caso('front verificador: C1, C2 y C5 son N/A en el bloque', 'N/A (front)' in out)
    tarea_base = os.path.join(tmp, 'tarea-base.md')
    with open(tarea_base, 'w', encoding='utf-8') as hb:
        hb.write('# Tarea #8 Migracion V2\n\n- **Modo de pruebas:** TDD\n\nAgrega la columna estado con una migracion V2 (ALTER TABLE).\n\n## Tests a escribir PRIMERO\n\n1. migrar\n')
    rc, out = correr('--rol', 'worker', '--entorno', 'intellij', '--motor', 'claude', '--id', '8', '--titulo', 'Migracion', '--tarea', tarea_base, '--worktree', 'C:/wt', '--rama', 'task/8', '--sha-base', 'abc', '--nucleo', NUCLEO, '--repo', 'back', '--modulo', 'modulo-ejemplo')
    caso('Tarea con migraciones: el worker lee migracion-de-base.md', rc == 0 and 'migracion-de-base.md' in out and 'vuelta atrás' in out, out[:400])
    rc, out = correr('--rol', 'verificador', '--entorno', 'intellij', '--motor', 'claude', '--id', '8', '--titulo', 'Migracion', '--tarea', tarea_base, '--worktree', 'C:/wt', '--rama', 'task/8', '--sha-base', 'abc', '--nucleo', NUCLEO, '--repo', 'back', '--modulo', 'modulo-ejemplo')
    caso('Tarea con migraciones: el verificador controla migraciones con esquema-base.py', 'esquema-base.py' in out and 'Control de **migraciones**' in out, out[:400])
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
