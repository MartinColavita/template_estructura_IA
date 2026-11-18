#!/usr/bin/env python3
"""GATE de SERVIDOR, en datos duros: si un servidor, un cluster o una URL esta autorizado, y hasta donde. SOLO LECTURA.

    python -I bin/activo-autorizado.py --alias web-test-1                    (leer: nivel N0)
    python -I bin/activo-autorizado.py --alias web-test-1 --nivel N1         (un cambio que se deshace)
    python -I bin/activo-autorizado.py --alias app-test --prueba pasivo      (una prueba dinamica contra una URL)
    python -I bin/activo-autorizado.py --listar [--json]                     (todo el inventario, con sus problemas)
    opciones: --modulo <slug> | --inventario <ruta>   (por defecto, el unico inventario de cerebro-digital/)

Tres estados, nunca dos:  0 = OK, autorizado   1 = FRENA, no esta autorizado   2 = SIN DATOS, no se pudo saber

POR QUE EXISTE. AGENTS.md manda que solo se toque lo que figura en el inventario autorizado, por su alias
exacto, y hasta el nivel que el inventario le da. Esa cuenta la hacia el modelo leyendo una tabla, y un
alias parecido o un nivel sin decidir pasaban por autorizados. Este script la hace siempre igual, y es
el mismo lector (bin/operacion/inventario.py) que usan los demas scripts que tocan algo que corre.

QUE NO HACE. No se conecta a nada, no escribe nada, y no reemplaza la pregunta a la persona: un OK dice
que el destino esta en la lista, no que haya que tocarlo. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario

OK, FRENA, SIN_DATOS = 0, 1, 2
CODIGO = {inventario.OK: OK, inventario.FRENA: FRENA, inventario.SIN_DATOS: SIN_DATOS}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO_MIRA = ('si conviene tocarlo: eso lo decide la persona',
           'si el alias resuelve al servidor correcto: lo resuelve la configuracion de SSH de la maquina, fuera del repo',
           'la ventana de cambios y el plan con su vuelta atras: los mira gate-operacion.py')


def main():
    ap = argparse.ArgumentParser(description='Si un activo esta en el inventario autorizado, y hasta que nivel (solo lectura).')
    ap.add_argument('--alias', default='')
    ap.add_argument('--nivel', default='N0', help='N0 leer (por defecto), N1 o N2')
    ap.add_argument('--prueba', default='', help='pasivo o activo: una prueba dinamica contra una URL')
    ap.add_argument('--listar', action='store_true')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not a.alias and not a.listar:
        print('SIN DATOS -- falta --alias <alias> (o --listar)')
        return SIN_DATOS
    ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
    if not ruta:
        print('SIN DATOS -- %s. Sin inventario, nada esta autorizado.' % motivo)
        return SIN_DATOS
    if not inventario.en_el_cerebro(ruta, a.raiz):
        print('SIN DATOS -- %s no esta adentro de cerebro-digital/: un inventario de otro lado no autoriza nada.' % ruta)
        return SIN_DATOS
    if a.listar:
        activos, motivo = inventario.cargar(ruta)
        if activos is None:
            print('SIN DATOS -- %s' % motivo)
            return SIN_DATOS
        _, problemas = inventario.leer(ruta)
        if a.json:
            print(json.dumps({'inventario': ruta, 'activos': activos, 'problemas': problemas}, ensure_ascii=True, indent=1))
        else:
            print('INVENTARIO de activos autorizados -- %d activo(s) en %s' % (len(activos), ruta))
            for x in activos:
                print('  %-22s %-9s %-11s IA hasta %-4s pruebas %-7s %s' % (
                    x['alias'], x['tipo'] or '?', x['ambiente'] or '?',
                    x['nivel_ia'] + ('' if x['nivel_decidido'] else '*'), x['pruebas_dinamicas'], x['ventana']))
            if any(not x['nivel_decidido'] for x in activos):
                print('  * nivel sin decidir: vale como nada.')
            for p in problemas:
                print('  HALLAZGO: ' + p)
            print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
        return FRENA if problemas else OK
    if a.prueba:
        estado, activo, motivo = inventario.autorizar_prueba(ruta, a.alias, a.prueba)
        pedido = 'prueba dinamica %s' % a.prueba
    else:
        estado, activo, motivo = inventario.autorizar(ruta, a.alias, a.nivel)
        pedido = 'nivel %s' % a.nivel
    if a.json:
        print(json.dumps({'estado': estado, 'alias': a.alias, 'pedido': pedido, 'motivo': motivo, 'activo': activo,
                          'inventario': ruta, 'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        return CODIGO[estado]
    print('GATE de SERVIDOR -- %s: %s, %s' % (estado, a.alias, pedido))
    if motivo:
        print('  %s: %s' % ('FRENA' if estado == inventario.FRENA else 'sin datos', motivo))
    if activo:
        print('  En el inventario: tipo %s, ambiente %s, IA hasta %s%s, pruebas dinamicas %s, ventana: %s' % (
            activo['tipo'] or '?', activo['ambiente'] or '?', activo['nivel_ia'],
            '' if activo['nivel_decidido'] else ' (sin decidir)', activo['pruebas_dinamicas'], activo['ventana'] or 'sin declarar'))
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return CODIGO[estado]


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
