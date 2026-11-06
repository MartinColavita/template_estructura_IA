#!/usr/bin/env python3
"""Prueba sin red de derivar-arbol.py con fichas temporales.

    python -B bin/probar-derivar-arbol.py

Termina con 0 si todos los casos dan lo esperado, 1 si alguno no.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESPERADOS = []
MEDIO = chr(0xb7)
AVISO = chr(0x26a0)

FICHA_OK = ('---\nid: flujo-prueba\ntipo: flujo\nestado: F-Draft\nmodulo: modulo-ejemplo\ntitle: Prueba\nauthor: equipo\n---\n'
            '# Prueba\n\n## Derivacion a backlog\n\n**Etiqueta tem\u00e1tica:** `reserva-salas`\n\n'
            '### Slices [Epicas]\n- [S-01] Reservas\n\n### Capacidades [Features]\n- [C-01] Gestion de reservas ' + MEDIO + ' Slice: S-01\n\n'
            '### Flujos [Historias]\n- [F-01] Crear una reserva ' + MEDIO + ' Capacidad: C-01 ' + MEDIO + ' Reglas: RN-MOD-001\n'
            '- [F-02] Cancelar una reserva ' + MEDIO + ' Capacidad: C-01 ' + MEDIO + ' Reglas: RN-MOD-002, DEC-002\n\n## Tickets derivados\n')


def caso(nombre, cond, detalle=''):
    ESPERADOS.append((nombre, bool(cond)))
    print('  %s %s%s' % ('OK   ' if cond else 'FALLA', nombre, (' -- ' + detalle) if detalle and not cond else ''))


def correr(ruta, *args):
    r = subprocess.run([sys.executable, '-B', os.path.join(AQUI, 'derivar-arbol.py'), ruta] + list(args),
                       capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=RAIZ)
    return r.returncode, r.stdout + r.stderr


def main():
    tmp = tempfile.mkdtemp(prefix='probar-derivar-')
    def ficha(nombre, contenido):
        p = os.path.join(tmp, nombre)
        with open(p, 'w', encoding='utf-8') as h:
            h.write(contenido)
        return p

    rc, out = correr(ficha('ok.md', FICHA_OK), '--json')
    d = json.loads(out) if rc == 0 else {}
    caso('ficha completa: arbol 1 + 1 + 2 = 4', rc == 0 and d.get('conteo', {}).get('total') == 4 and d['conteo']['Tareas'] == 0, out[:300])
    caso('cada Historia cuelga de su Feature y trae sus reglas',
         rc == 0 and all(n['padre'] == 'C-01' for n in d['nodos'] if n['tipo'] == 'Historia')
         and [n for n in d['nodos'] if n['clave'] == 'F-02'][0]['reglas'] == ['RN-MOD-002', 'DEC-002'])
    caso('etiqueta unica leida de la ficha', rc == 0 and d.get('etiqueta') == 'reserva-salas')

    rc, out = correr(ficha('sin-bloque.md', FICHA_OK.split('## Derivacion')[0] + '## Otra seccion\n'))
    caso('sin bloque: NO SE DERIVA (exit 1)', rc == 1 and 'no tiene el bloque' in out)

    rc, out = correr(ficha('con-aviso.md', FICHA_OK.replace('- [F-02] Cancelar', '- [F-02] ' + AVISO + ' Cancelar')))
    caso('bloque con advertencia: NO SE DERIVA', rc == 1 and 'no esta validado' in out)

    rc, out = correr(ficha('incoherente.md', FICHA_OK.replace('Capacidad: C-01 ' + MEDIO + ' Reglas: RN-MOD-001', 'Capacidad: C-09 ' + MEDIO + ' Reglas: RN-MOD-001')))
    caso('capacidad inexistente: NO SE DERIVA con el motivo', rc == 1 and 'C-09' in out)

    rc, out = correr(ficha('sin-etiqueta.md', FICHA_OK.replace('**Etiqueta tem\u00e1tica:** `reserva-salas`', '')))
    caso('sin etiqueta tematica: NO SE DERIVA', rc == 1 and 'Etiqueta' in out)

    rc, out = correr(os.path.join(tmp, 'no-existe.md'))
    caso('ficha inexistente: SIN DATOS', rc == 2)

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
