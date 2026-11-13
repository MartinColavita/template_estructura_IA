#!/usr/bin/env python3
"""Prueba de bin/tablero-local.py sobre un tablero temporal.
Se corre:  python -B bin/probar-tablero-local.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'tablero-local.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(tablero, *args):
    r = subprocess.run([sys.executable, '-I', SCRIPT, '--tablero', tablero] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== tablero-local')
    tmp = tempfile.mkdtemp(prefix='probar-tablero-')
    tb = os.path.join(tmp, 'backlog')
    rc, out = correr(tb, 'listar')
    caso('sin tablero todavia: SIN DATOS (2)', rc == 2)
    rc, out = correr(tb, 'crear', '--tipo', 'Epica', '--titulo', 'Reservas de salas', '--etiqueta', 'reservas', '--json')
    d = json.loads(out)
    caso('crea la Epica #1', rc == 0 and d['id'] == 1 and os.path.isfile(d['archivo']), out[:200])
    rc, out = correr(tb, 'crear', '--tipo', 'Feature', '--titulo', 'Reserva de salas', '--padre', '1', '--etiqueta', 'reservas', '--json')
    caso('crea la Feature #2 con padre', rc == 0 and json.loads(out)['id'] == 2)
    caso('el nombre del archivo translitera las tildes', os.path.isfile(os.path.join(tb, '0002-reserva-de-salas.md')) and any(f.startswith('0002-') and 'reserva-de-salas' in f for f in os.listdir(tb)))
    rc, out = correr(tb, 'crear', '--tipo', 'Historia', '--titulo', 'Crear una reserva con validación', '--padre', '9', '--json')
    caso('padre inexistente: FRENA (1)', rc == 1 and 'no existe' in out)
    cuerpo = os.path.join(tmp, 'cuerpo.md')
    with open(cuerpo, 'w', encoding='utf-8') as h:
        h.write('# Historia\n\n## Criterios de aceptacion\nEscenario: reserva valida\n')
    rc, out = correr(tb, 'crear', '--tipo', 'Historia', '--titulo', 'Crear una reserva con validación', '--padre', '2', '--etiqueta', 'reservas', '--cuerpo', cuerpo, '--json')
    caso('crea la Historia #3 con cuerpo propio', rc == 0 and json.loads(out)['id'] == 3)
    rc, out = correr(tb, 'listar', '--json')
    filas = json.loads(out)
    caso('listar: 3 items en New', len(filas) == 3 and all(f['estado'] == 'New' for f in filas))
    rc, out = correr(tb, 'listar', '--tipo', 'Historia', '--json')
    caso('listar filtra por tipo', len(json.loads(out)) == 1)
    rc, out = correr(tb, 'ver', '3')
    caso('ver muestra frontmatter y cuerpo', rc == 0 and 'tipo: Historia' in out and 'Escenario: reserva valida' in out and '## Comentarios' in out)
    rc, out = correr(tb, 'tomar', '3', '--quien', 'martin', '--json')
    caso('tomar asigna y pasa a Active', rc == 0 and json.loads(out)['estado'] == 'Active')
    rc, out = correr(tb, 'tomar', '3', '--quien', 'otra', '--json')
    caso('tomar la de otro en Active: FRENA (1)', rc == 1 and 'coordinar' in out)
    rc, out = correr(tb, 'comentar', '3', '--texto', 'Cierre: rama task/3, MR !1', '--autor', 'ia')
    rc2, out2 = correr(tb, 'ver', '3')
    caso('comentar agrega la linea con fecha y autor', rc == 0 and '(ia): Cierre: rama task/3' in out2)
    rc, out = correr(tb, 'vincular', '3', '2', '--relacion', 'Related', '--json')
    rc2, out2 = correr(tb, 'ver', '2', '--json')
    caso('vincular Related es simetrico', rc == 0 and '3' in [str(x) for x in json.loads(out2)['campos']['relaciones']])
    rc, out = correr(tb, 'buscar', 'reserva', '--abiertos', '--json')
    caso('buscar por objetivo (dedup) encuentra los 3', len(json.loads(out)) == 3)
    rc, out = correr(tb, 'estado', '3', 'Closed')
    caso('Closed sin --confirmado: FRENA (1)', rc == 1 and 'confirmado' in out)
    rc, out = correr(tb, 'estado', '3', 'Closed', '--confirmado', '--json')
    caso('Closed con --confirmado: ok', rc == 0 and json.loads(out)['ahora'] == 'Closed')
    rc, out = correr(tb, 'estado', '2', 'Resolved')
    caso('Resolved sin --confirmado y sin DEC-005 firmada: FRENA (1)', rc == 1 and 'DEC-005' in out, out[:300])
    dec = os.path.join(os.path.dirname(tb), 'arquitectura', 'decisiones.md')
    os.makedirs(os.path.dirname(dec), exist_ok=True)
    with open(dec, 'w', encoding='utf-8') as h:
        h.write('## DEC-005 — Modo desatendido\n\n**Estado:** **Confirmado para el modo solo (2026-11-13, firmado por yo).**\n')
    rc, out = correr(tb, 'estado', '2', 'Resolved')
    caso('Resolved de una Feature con DEC-005 firmada: FRENA (la autorizacion es para una Tarea)', rc == 1, out[:300])
    rc, out = correr(tb, 'buscar', 'reserva', '--abiertos', '--json')
    caso('buscar --abiertos excluye la cerrada', len(json.loads(out)) == 2)
    rc, out = correr(tb, 'editar', '2', '--campo', 'iteracion', '--valor', 'sprint-1', '--json')
    caso('editar un campo', rc == 0 and json.loads(out)['ahora'] == 'sprint-1')
    rc, out = correr(tb, 'ver', '99')
    caso('item inexistente: SIN DATOS (2)', rc == 2)
    rc, out = correr(tb, 'crear', '--tipo', 'Tarea', '--titulo', 'Endpoint POST /reservas', '--padre', '3', '--json')
    caso('los ids son secuenciales (#4)', rc == 0 and json.loads(out)['id'] == 4)
    with open(dec, 'w', encoding='utf-8') as h:
        h.write('## DEC-005 — Modo desatendido\n\n**Estado:** ⚠ **Sin firmar** <la firma quien arranca>.\n\n## DEC-006 — x\n\n**Confirmado para el modo solo (otra DEC).**\n')
    rc, out = correr(tb, 'estado', '4', 'Resolved')
    caso('Resolved de una Tarea con DEC-005 sin firmar (y la firma en otra DEC): FRENA (1)', rc == 1, out[:300])
    with open(dec, 'w', encoding='utf-8') as h:
        h.write('## DEC-005 — Modo desatendido\n\n**Estado:** **Confirmado para el modo solo (2026-11-13, firmado por yo).**\n')
    rc, out = correr(tb, 'estado', '4', 'Resolved', '--json')
    caso('Resolved de una Tarea con DEC-005 firmada: ok sin --confirmado', rc == 0 and json.loads(out)['ahora'] == 'Resolved', out[:300])
    with open(dec, 'a', encoding='utf-8') as h:
        h.write('\n## DEC-006 — Modo\n\n**Confirmado al instanciar (2026-11-13): modo equipo, tablero local, autor yo.**\n')
    correr(tb, 'estado', '4', 'Active')
    rc, out = correr(tb, 'estado', '4', 'Resolved')
    caso('Resolved de una Tarea en un proyecto de equipo (DEC-006): FRENA aunque DEC-005 diga firmada', rc == 1, out[:300])
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
