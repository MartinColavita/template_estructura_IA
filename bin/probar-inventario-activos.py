#!/usr/bin/env python3
"""Prueba de bin/operacion/inventario.py y de bin/activo-autorizado.py sobre inventarios de mentira.
Se corre:  python -B bin/probar-inventario-activos.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'activo-autorizado.py')
sys.path.insert(0, AQUI)
from operacion import inventario  # noqa: E402

ESPERADOS = []
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel máximo para la IA | '
            'Pruebas dinámicas | Ventana de cambios | Dueño (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
MOLDE = '| `<alias>` | servidor | prueba | `<alias-ssh>` | no | media | N0 | no | `<dia y horario>` | `<rol>` |\n'
FILAS = ('| `web-prueba-1` | servidor | prueba | `web-prueba-1` | no | media | N1 | no | martes 22 a 24 | operaciones |\n'
         '| `db-prod-1` | servidor | Producción | `db-prod-1` | no | alta | N0 | no | jueves 23 | operaciones |\n'
         '| `sin-decidir` | servidor | prueba | `x` | no | baja | ⚠ | no | | operaciones |\n'
         '| `pide-n3` | servidor | prueba | `x` | no | baja | N3 | no | | operaciones |\n'
         '| `app-prueba` | url | prueba | https://prueba.example.com | sí | media | N0 | pasivo | | producto |\n'
         '| `app-activa` | url | prueba | https://activa.example.com | sí | media | nada | activo | | producto |\n'
         '| `app-prod` | url | produccion | https://www.example.com | sí | alta | N0 | activo | | producto |\n'
         '| `app-sin-url` | url | prueba | `pendiente` | no | baja | N0 | pasivo | | producto |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)) if (detalle and not ok) else ''))


def escribir(ruta, texto, crlf=False):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write((texto.replace('\n', '\r\n') if crlf else texto).encode('utf-8'))
    return ruta


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== inventario de activos autorizados')
    tmp = tempfile.mkdtemp(prefix='probar-inv-')
    inv = escribir(os.path.join(tmp, 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'),
                   '---\nid: inventario\n---\n\n# Inventario\n\n' + CABECERA + MOLDE + FILAS + '\nTexto de abajo.\n')
    aut, pru = inventario.autorizar, inventario.autorizar_prueba

    activos, problemas = inventario.leer(inv)
    caso('lee las ocho filas reales y saltea la del molde', len(activos) == 8 and all('<' not in a['alias'] for a in activos), len(activos))
    caso('el ambiente se compara sin acentos ni mayusculas', [a['ambiente'] for a in activos if a['alias'] == 'db-prod-1'] == ['produccion'])
    caso('expuesto: si es True, no es False', [a['expuesto'] for a in activos if a['alias'] in ('app-prueba', 'web-prueba-1')] == [False, True]
         or sorted(str(a['expuesto']) for a in activos if a['alias'] in ('app-prueba', 'web-prueba-1')) == ['False', 'True'])
    caso('un N3 escrito en el inventario es un problema y queda en nada',
         any('pide-n3' in p and 'N3' in p for p in problemas) and [a['nivel_ia'] for a in activos if a['alias'] == 'pide-n3'] == ['nada'], problemas)

    caso('alias con N1, se pide leer (N0): OK', aut(inv, 'web-prueba-1', 'N0')[0] == 'OK')
    caso('alias con N1, se pide N1: OK', aut(inv, 'web-prueba-1', 'N1')[0] == 'OK')
    e, a, m = aut(inv, 'web-prueba-1', 'N2')
    caso('alias con N1, se pide N2: FRENA y dice hasta donde autoriza', e == 'FRENA' and 'hasta N1' in m and a['alias'] == 'web-prueba-1', m)
    e, a, m = aut(inv, 'web-prueba-2', 'N0')
    caso('un alias que no figura: FRENA, ni para leerlo', e == 'FRENA' and a is None and 'no esta en el inventario' in m, m)
    caso('el alias se compara exacto: con otra mayuscula no esta autorizado', aut(inv, 'Web-Prueba-1', 'N0')[0] == 'FRENA')
    caso('un alias que es prefijo de otro no esta autorizado', aut(inv, 'web-prueba', 'N0')[0] == 'FRENA')
    e, a, m = aut(inv, 'sin-decidir', 'N0')
    caso('nivel sin decidir: vale como nada, FRENA hasta para leer', e == 'FRENA' and 'sin decidir' in m, m)
    caso('pedir N3: FRENA siempre, aunque el alias exista', aut(inv, 'web-prueba-1', 'N3')[0] == 'FRENA')
    caso('un nivel que no existe: SIN DATOS', aut(inv, 'web-prueba-1', 'N9')[0] == 'SIN DATOS')

    caso('sin inventario: SIN DATOS, no "sin restricciones"', aut(os.path.join(tmp, 'no.md'), 'web-prueba-1')[0] == 'SIN DATOS')
    vacio = escribir(os.path.join(tmp, 'vacio.md'), '# Inventario\n\n' + CABECERA + MOLDE)
    e, a, m = aut(vacio, 'web-prueba-1')
    caso('inventario con solo el molde: SIN DATOS (Regla del cero)', e == 'SIN DATOS' and 'ningun activo' in m, m)
    sin_tabla = escribir(os.path.join(tmp, 'sin-tabla.md'), '# Inventario\n\nTodavia no hay nada.\n')
    caso('inventario sin tabla: SIN DATOS', aut(sin_tabla, 'web-prueba-1')[0] == 'SIN DATOS')
    doble = escribir(os.path.join(tmp, 'doble.md'), CABECERA + FILAS + '| `web-prueba-1` | servidor | prueba | `otro` | no | media | N2 | no | | ops |\n')
    e, a, m = aut(doble, 'web-prueba-1', 'N0')
    caso('alias repetido: SIN DATOS, no gana ninguna de las dos filas', e == 'SIN DATOS' and '2 veces' in m, m)
    caso('el alias repetido tambien sale como problema al leer', any('2 veces' in p for p in inventario.leer(doble)[1]))

    caso('prueba pasiva contra una url que la admite: OK', pru(inv, 'app-prueba', 'pasivo')[0] == 'OK')
    e, a, m = pru(inv, 'app-prueba', 'activo')
    caso('prueba activa contra una url que solo admite pasivo: FRENA', e == 'FRENA' and '"pasivo"' in m, m)
    caso('la prueba la gobierna su columna, no el nivel: nivel nada y pruebas activo es OK', pru(inv, 'app-activa', 'activo')[0] == 'OK')
    e, a, m = pru(inv, 'app-prod', 'activo')
    caso('prueba activa contra produccion: FRENA aunque la fila diga activo', e == 'FRENA' and 'produccion' in m, m)
    caso('prueba pasiva contra produccion con la fila en activo: OK', pru(inv, 'app-prod', 'pasivo')[0] == 'OK')
    e, a, m = pru(inv, 'web-prueba-1', 'pasivo')
    caso('prueba dinamica contra un servidor: FRENA, solo va contra una url', e == 'FRENA' and 'tipo servidor' in m, m)
    caso('url sin direccion exacta en Destino: SIN DATOS', pru(inv, 'app-sin-url', 'pasivo')[0] == 'SIN DATOS')
    caso('prueba contra un alias que no figura: FRENA', pru(inv, 'otra-app', 'pasivo')[0] == 'FRENA')
    caso('modo de prueba desconocido: SIN DATOS', pru(inv, 'app-prueba', 'agresivo')[0] == 'SIN DATOS')

    ruta, m = inventario.ubicar(tmp)
    caso('ubicar: con un solo modulo encuentra su inventario', ruta == inv, m)
    escribir(os.path.join(tmp, 'cerebro-digital', 'modulo-b', 'operacion', 'inventario.md'), CABECERA + FILAS)
    ruta, m = inventario.ubicar(tmp)
    caso('ubicar: con dos modulos no elige, pide cual', ruta is None and '2 inventarios' in m, m)
    caso('ubicar: con --modulo va a ese', inventario.ubicar(tmp, 'modulo-b')[0].endswith(os.path.join('modulo-b', 'operacion', 'inventario.md')))
    escribir(os.path.join(tmp, 'cerebro-digital', 'configuracion-ia', 'operacion', 'inventario.md'), CABECERA + FILAS)
    caso('ubicar: configuracion-ia no cuenta como modulo', '2 inventarios' in inventario.ubicar(tmp)[1])
    caso('ubicar: sin ninguno, lo dice', inventario.ubicar(os.path.join(tmp, 'vacio'))[0] is None)

    crlf = escribir(os.path.join(tmp, 'crlf.md'), '﻿' + CABECERA + FILAS, crlf=True)
    caso('archivo con BOM y saltos de Windows: se lee igual', aut(crlf, 'web-prueba-1', 'N1')[0] == 'OK')
    otro_orden = escribir(os.path.join(tmp, 'orden.md'),
                          '| Nivel maximo para la IA | **Alias** | Tipo |\n|---|---|---|\n| N2 | web-x | servidor |\n')
    caso('columnas en otro orden y con negrita: se reconocen por el encabezado', aut(otro_orden, 'web-x', 'N2')[0] == 'OK')
    dos_tablas = escribir(os.path.join(tmp, 'dos.md'), CABECERA + FILAS + '\n## Otra tabla\n\n| Columna | Que va |\n|---|---|\n'
                          '| **Alias** | web-fantasma |\n| **Tipo** | servidor |\n| web-fantasma-2 | servidor |\n')
    leidos = [x['alias'] for x in inventario.leer(dos_tablas)[0]]
    caso('una tabla de ayuda que nombra las columnas en sus filas no agrega activos (el encabezado es la fila de antes de los guiones)',
         aut(dos_tablas, 'web-fantasma')[0] == 'FRENA' and len(leidos) == 8 and 'Tipo' not in leidos and 'web-fantasma-2' not in leidos, leidos)
    sin_guiones = escribir(os.path.join(tmp, 'sin-guiones.md'), '| Alias | Nivel maximo para la IA |\n| web-y | N2 |\n')
    caso('filas con barras pero sin la linea de guiones no son una tabla: no autorizan nada', aut(sin_guiones, 'web-y', 'N2')[0] == 'SIN DATOS')

    rc, out = correr('--alias', 'web-prueba-1', '--inventario', inv, '--raiz', tmp)
    caso('el script: autorizado sale 0 y dice OK', rc == 0 and out.startswith('GATE de SERVIDOR -- OK') and 'NO mira' in out, out[:200])
    rc, out = correr('--alias', 'web-prueba-1', '--nivel', 'N2', '--inventario', inv, '--raiz', tmp)
    caso('el script: mas nivel del autorizado sale 1 y dice FRENA', rc == 1 and 'FRENA' in out, out[:200])
    rc, out = correr('--alias', 'web-prueba-1', '--inventario', os.path.join(tmp, 'no.md'), '--raiz', tmp)
    caso('el script: sin inventario sale 2', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--alias', 'app-prueba', '--prueba', 'activo', '--inventario', inv, '--raiz', tmp, '--json')
    d = json.loads(out)
    caso('el script: --prueba y --json', rc == 1 and d['estado'] == 'FRENA' and d['activo']['alias'] == 'app-prueba' and d['no_mira'], out[:200])
    rc, out = correr('--listar', '--inventario', inv, '--raiz', tmp)
    caso('el script: --listar muestra los activos y marca el problema del N3 (sale 1)', rc == 1 and 'web-prueba-1' in out and 'HALLAZGO' in out, out[:300])
    afuera = escribir(os.path.join(tmp, 'borrador', 'inventario.md'), CABECERA + FILAS)
    rc, out = correr('--alias', 'web-prueba-1', '--inventario', afuera, '--raiz', tmp)
    caso('el script: un inventario armado fuera de cerebro-digital/ no autoriza nada (SIN DATOS)', rc == 2 and 'cerebro-digital' in out, out[:200])
    raro = escribir(os.path.join(tmp, 'raro.md'), CABECERA +
                    '| `app-x` | url | Productivo | https://x.example.com | si | alta | N1 | activo | | producto |\n'
                    '| `app-y` | url |  | https://y.example.com | si | alta | N1 | activo | | producto |\n'
                    '| `web-y` | servidor | PRD | `web-y` | no | alta | N1 | no | | ops |\n'
                    '| `web-z` | servidor | prueba | `web-z` | no | alta | N1 | no | | ops |\n')
    caso('ambiente "Productivo": cuenta como produccion, la prueba activa FRENA', pru(raro, 'app-x', 'activo')[0] == 'FRENA')
    caso('ambiente vacio: cuenta como produccion, la prueba activa FRENA', pru(raro, 'app-y', 'activo')[0] == 'FRENA')
    lr = dict((x['alias'], x) for x in inventario.leer(raro)[0])
    caso('es_produccion: PRD si, prueba no', lr['web-y']['es_produccion'] and not lr['web-z']['es_produccion'])
    caso('un ambiente desconocido es un problema del inventario; uno vacio tambien',
         sum(1 for p_ in inventario.leer(raro)[1] if 'se trata como produccion' in p_) == 3, inventario.leer(raro)[1])
    rc, out = correr('--alias', 'web-prueba-1', '--raiz', tmp, '--modulo', 'modulo-a')
    caso('el script: busca el inventario del modulo desde la raiz', rc == 0, out[:200])
    rc, out = correr('--alias', 'web-prueba-1', '--raiz', tmp)
    caso('el script: con varios inventarios y sin --modulo, SIN DATOS', rc == 2 and 'inventarios' in out, out[:200])
    rc, out = correr()
    caso('el script: sin --alias ni --listar, SIN DATOS', rc == 2)

    raiz = os.path.dirname(AQUI)
    plantilla = os.path.join(raiz, 'cerebro-digital', 'modulo-ejemplo', 'operacion', 'inventario.md')
    if os.path.isfile(plantilla):
        e, a, m = aut(plantilla, 'web-prueba-1')
        caso('la plantilla del template nace vacia: nada autorizado, SIN DATOS', e == 'SIN DATOS', m)
    for f in ('activo-autorizado.py', os.path.join('operacion', 'inventario.py'), os.path.join('operacion', '__init__.py')):
        with open(os.path.join(AQUI, f), 'rb') as h:
            caso('%s es ASCII puro' % f.replace(os.sep, '/'), all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
