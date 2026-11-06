#!/usr/bin/env python3
"""Prueba de bin/derivar-a-tablero-local.py con una ficha de mentira y un tablero temporal.
Se corre:  python -B bin/probar-derivar-a-tablero-local.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'derivar-a-tablero-local.py')
MEDIO = '·'
AVISO = '⚠'
FICHA = ('---\nid: flujo-prueba\ntipo: flujo\nestado: F-Draft\nmodulo: m\ntitle: Prueba\nauthor: equipo\n---\n'
         '# Prueba\n\n## Derivacion a backlog\n\n**Etiqueta temática:** `reserva-salas`\n\n'
         '### Slices [Epicas]\n- [S-01] Reservas\n\n### Capacidades [Features]\n- [C-01] Gestion de reservas ' + MEDIO + ' Slice: S-01\n\n'
         '### Flujos [Historias]\n- [F-01] Crear una reserva ' + MEDIO + ' Capacidad: C-01 ' + MEDIO + ' Reglas: RN-MOD-001\n'
         '- [F-02] Cancelar una reserva ' + MEDIO + ' Capacidad: C-01 ' + MEDIO + ' Reglas: RN-MOD-002\n')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== derivar-a-tablero-local')
    tmp = tempfile.mkdtemp(prefix='probar-derivar-tl-')
    funcional = os.path.join(tmp, 'cerebro-digital', 'm', 'funcional')
    os.makedirs(funcional)
    ficha = os.path.join(funcional, 'reservas.md')
    with open(ficha, 'w', encoding='utf-8', newline='\n') as h:
        h.write(FICHA)
    tablero = os.path.join(tmp, 'cerebro-digital', 'm', 'backlog')
    rc, out = correr(ficha, '--dry-run', '--json')
    d = json.loads(out) if rc == 0 else {}
    caso('dry-run: 4 nodos (1 Epica, 1 Feature, 2 Historias) y nada creado', rc == 0 and len(d.get('creados', [])) == 4 and not os.path.isdir(tablero), out[:300])
    rc, out = correr(ficha, '--json')
    d = json.loads(out) if rc == 0 else {}
    caso('crea el arbol en el tablero deducido de la ruta (0)', rc == 0 and d.get('tablero', '').replace('\\', '/').endswith('cerebro-digital/m/backlog') and len(d['creados']) == 4, out[:300])
    if d:
        por = {c['clave']: c for c in d['creados']}
        caso('la Feature cuelga de la Epica y las Historias de la Feature', por['C-01']['padre'] == por['S-01']['id'] and por['F-01']['padre'] == por['C-01']['id'] and por['F-02']['padre'] == por['C-01']['id'])
        caso('conteo 1:1 y 0 Tareas', d['conteo'] == {'Epica': 1, 'Feature': 1, 'Historia': 2, 'Tarea': 0})
        archivos = sorted(os.listdir(tablero))
        caso('cuatro archivos con la etiqueta y la fuente', len(archivos) == 4 and all('etiqueta: reserva-salas' in open(os.path.join(tablero, f), encoding='utf-8').read() and 'Documento fuente' in open(os.path.join(tablero, f), encoding='utf-8').read() for f in archivos))
        caso('la Historia trae sus reglas', any('RN-MOD-002' in open(os.path.join(tablero, f), encoding='utf-8').read() for f in archivos))
    rc, out = correr(ficha, '--json')
    d2 = json.loads(out) if rc == 0 else {}
    caso('segunda corrida: idempotente, reutiliza los 4 y no duplica', rc == 0 and len(d2.get('reutilizados', [])) == 4 and not d2.get('creados') and len(os.listdir(tablero)) == 4)
    con_aviso = os.path.join(funcional, 'con-aviso.md')
    with open(con_aviso, 'w', encoding='utf-8', newline='\n') as h:
        h.write(FICHA.replace('- [F-02] Cancelar', '- [F-02] ' + AVISO + ' Cancelar'))
    rc, out = correr(con_aviso)
    caso('ficha con aviso pendiente: NO SE DERIVA (1)', rc == 1 and 'NO SE DERIVA' in out)
    rc, out = correr(os.path.join(funcional, 'no-existe.md'))
    caso('ficha inexistente: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
