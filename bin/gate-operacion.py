#!/usr/bin/env python3
"""GATE de SERVIDOR antes de un cambio N1 o N2, en datos duros: el alias, el nivel y el plan de cambio. SOLO LECTURA.

    python -I bin/gate-operacion.py --plan borrador/operacion/plan-web-prueba-1-2026-11-17.md
    python -I bin/gate-operacion.py --plan <plan> --alias web-prueba-1      (ademas, que el plan sea para ese alias)
    opciones: --modulo <slug> | --inventario <ruta>  --json

Tres estados, nunca dos:  0 = OK, se puede preguntar   1 = FRENA, falta algo   2 = SIN DATOS, no se pudo saber

POR QUE EXISTE. AGENTS.md manda que lo que corre se toque solo si esta en el inventario, por su alias exacto y
hasta el nivel que el inventario le da; que en produccion un cambio sea N2; que N3 no lo haga nunca la IA; y que
sin vuelta atras escrita no haya cambio. Esas cuentas las hacia el modelo leyendo el plan, y un plan sin vuelta
atras o con un comando a medio escribir ("<servicio>") pasaba. Este script las hace siempre igual sobre el plan
de cambio, con el molde de references/mantenimiento.md de la skill operacion-de-servidores: los campos Que,
Alias, Nivel, Ventana y Respaldo verificado, y las secciones Comando exacto, Salida esperada, Como se verifica
y Vuelta atras, ninguna vacia. Las secciones se reconocen por su TITULO COMPLETO ("Comandos previos" no es
"Comando exacto"; una aclaracion entre parentesis al final, si). La Vuelta atras y el Respaldo verificado
FRENAN si el texto empieza con un negativo (no hay, ninguna, ninguno, sin, n/a, no aplica, no se hizo) o dice
irreversible, no se puede deshacer o no hay vuelta, salvo que lo que sigue describa un procedimiento (restaurar,
revertir, reinstalar, volver a..., o un comando entre comillas invertidas). FRENA si falta algo, si el nivel es
N3 (siempre) o si el inventario no lo autoriza. SIN DATOS si no puede leer el plan o el inventario.

QUE NO HACE. No se conecta a nada y no corre el comando. No calcula si la ventana esta abierta: la muestra.
No mide el respaldo: muestra el que declara el plan. Un OK no es el "si": dice que el plan se puede mostrar
y preguntar. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario (y sus utilidades de tabla)

OK, FRENA, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = chr(0xFEFF)
CAMPOS = (('que', 'Que'), ('alias', 'Alias'), ('nivel', 'Nivel'), ('ventana', 'Ventana'), ('respaldo verificado', 'Respaldo verificado'))
SECCIONES = (('comando exacto', 'Comando exacto'), ('salida esperada', 'Salida esperada'),
             ('como se verifica', 'Como se verifica'), ('vuelta atras', 'Vuelta atras'))
MARCADOR = re.compile(r'<[^<>\n]*>')
MARCADOR_EN_COMANDO = re.compile(r'<[A-Za-z][^<>\n]*>')
TITULO = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
# Lo que, escrito solo, quiere decir "no hay": no cuenta como contenido.
NEGATIVOS = ('no hay', 'no tiene', 'ninguna', 'ninguno', 'no aplica', 'n/a', 'na', 'no', 'pendiente', 'a definir',
             'a completar', 'tbd', 'sin vuelta atras', 'no hay vuelta atras', 'no tiene vuelta atras', 'no se puede')
# Lo que dice "no hay vuelta atras" (o "no hay respaldo") aunque traiga mas texto: un negativo al empezar, o una
# frase que dice que no se deshace. Vale salvo que lo que sigue describa un procedimiento.
NIEGA_AL_EMPEZAR = re.compile(r'^(?:no hay|ninguna|ninguno|sin|n/a|no aplica|no se hizo)(?![a-z0-9])')
NIEGA_EN = re.compile(r'irreversible|no se puede deshacer|no hay vuelta')
PROCEDIMIENTO = re.compile(r'restaur|revert|reinstal|reaplic|recuper|repon|reinici|rollback|vuelve a |volver a |'
                           r'se vuelve |downgrade|se baja a |se reemplaza|reemplazar|se levanta|levantar')
NO_MIRA = ('si el comando hace lo que dice el Que: eso lo mira la persona, y el verificador',
           'si la ventana esta abierta ahora: la muestra, no la calcula',
           'si el respaldo existe y se puede restaurar: lo declara el plan; todavia no lo mide ningun script',
           'si hay otro cambio abierto en el mismo alias, un incidente o un congelamiento')


def vacio(texto):
    """True si no queda nada despues de sacar marcadores <...>, cercos de codigo, rayas y simbolos, o si lo que
    queda solo dice "no hay"."""
    lineas = [l for l in texto.split('\n') if not l.strip().startswith('```')]
    resto = MARCADOR.sub('', '\n'.join(lineas))
    plano = inventario.plano(resto)
    if not re.search(r'[a-z0-9]', plano):
        return True
    return re.sub(r'[^a-z0-9/ ]', '', plano).strip() in NEGATIVOS


def niega(texto):
    """True si el texto dice que no hay (empieza con un negativo, o dice que no se deshace) y lo que sigue no
    describe un procedimiento."""
    plano = inventario.plano(MARCADOR.sub('', texto))
    m = NIEGA_AL_EMPEZAR.match(plano) or NIEGA_EN.search(plano)
    if not m:
        return False
    resto = plano[m.end():]
    return not (PROCEDIMIENTO.search(resto + ' ') or '`' in texto)


def titulo_de(texto):
    """El titulo de una seccion, plano y completo: sin numeracion adelante ni una aclaracion entre parentesis al final."""
    t = inventario.plano(texto)
    t = re.sub(r'^\d+[.)]\s*', '', t)
    t = re.sub(r'\s*\([^()]*\)\s*$', '', t)
    return t.strip(' :.')


def leer_plan(texto):
    """(campos, secciones). campos = {clave: valor}; secciones = {clave: texto}. Lo que no esta, no figura."""
    texto = texto.replace('\r\n', '\n')
    if texto.startswith(BOM):
        texto = texto[1:]
    lineas = texto.split('\n')
    campos, secciones = {}, {}
    filas = [inventario.celdas(l) for l in lineas]
    en_tabla = False
    for i, fila in enumerate(filas):
        if fila is None:
            en_tabla = False
            continue
        if not en_tabla:
            siguiente = filas[i + 1] if i + 1 < len(filas) else None
            en_tabla = bool(fila) and inventario.plano(fila[0]) == 'campo' and siguiente is not None and inventario.es_separador(siguiente)
            continue
        if inventario.es_separador(fila) or len(fila) < 2:
            continue
        nombre = inventario.plano(fila[0])
        for clave, _ in CAMPOS:
            if (nombre == clave or nombre.startswith(clave + ' ') or (clave == 'respaldo verificado' and nombre.startswith('respaldo'))) \
                    and clave not in campos:
                campos[clave] = inventario.limpio(fila[1])
                break
    actual, cerco = None, False
    for l in lineas:
        if l.strip().startswith('```'):
            cerco = not cerco
        m = None if cerco or l.strip().startswith('```') else TITULO.match(l.strip())
        if m:
            actual = None
            if len(m.group(1)) == 2:
                nombre = titulo_de(m.group(2))
                for clave, _ in SECCIONES:
                    if nombre == clave and clave not in secciones:
                        actual = clave
                        secciones[clave] = ''
                        break
            continue
        if actual is not None:
            secciones[actual] += l + '\n'
    return campos, secciones


def main(argv=None):
    ap = argparse.ArgumentParser(description='GATE de SERVIDOR antes de un cambio N1 o N2: alias, nivel y plan (solo lectura).')
    ap.add_argument('--plan', default='', help='el plan de cambio (molde de references/mantenimiento.md)')
    ap.add_argument('--alias', default='', help='opcional: el alias que se va a tocar; tiene que ser el del plan')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)

    def sin_datos(motivo):
        if a.json:
            print(json.dumps({'estado': 'SIN DATOS', 'motivo': motivo, 'plan': a.plan, 'chequeos': [], 'no_mira': list(NO_MIRA)},
                             ensure_ascii=True, indent=1))
        else:
            print('SIN DATOS -- %s' % motivo)
        return SIN_DATOS

    if not a.plan:
        return sin_datos('falta --plan <plan de cambio>: sin plan no hay cambio')
    try:
        with open(a.plan, 'rb') as h:
            crudo = h.read()
    except OSError as e:
        return sin_datos('no se pudo leer el plan %s: %s' % (a.plan, e.strerror or e))
    campos, secciones = leer_plan(crudo.decode('utf-8', errors='replace'))
    if not campos and not secciones:
        return sin_datos('%s no tiene el molde del plan de cambio (la tabla Campo | Valor y las secciones): '
                         'el molde esta en references/mantenimiento.md de la skill operacion-de-servidores' % a.plan)

    chequeos = []

    def chequeo(nombre, estado, detalle):
        chequeos.append({'chequeo': nombre, 'estado': estado, 'detalle': detalle})

    alias = '' if vacio(campos.get('alias', '')) else campos['alias']
    nivel = campos.get('nivel', '').strip().upper()
    if not alias:
        chequeo('alias', 'FRENA', 'el plan no dice el alias del inventario')
    elif a.alias and a.alias != alias:
        chequeo('alias', 'FRENA', 'el plan es para %s y se pidio %s: es el plan de otro servidor' % (alias, a.alias))
    else:
        chequeo('alias', 'OK', alias)
    if nivel == 'N3':
        chequeo('nivel', 'FRENA', 'N3 no lo hace la IA nunca: lo hace una persona, con el resumen a la vista')
    elif nivel == 'N0':
        chequeo('nivel', 'FRENA', 'N0 es leer y leer no necesita plan de cambio: un plan es N1 o N2')
    elif nivel not in ('N1', 'N2'):
        chequeo('nivel', 'FRENA', 'el plan no declara el nivel (N1 o N2)')
    else:
        chequeo('nivel', 'OK', nivel)

    activo = None
    if not alias or nivel not in ('N1', 'N2'):
        chequeo('inventario', 'SIN DATOS', 'no se miro: el plan no tiene un alias y un nivel N1 o N2')
    else:
        ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
        if not ruta:
            chequeo('inventario', 'SIN DATOS', '%s: sin inventario nada esta autorizado' % motivo)
        else:
            estado, activo, motivo = inventario.autorizar(ruta, alias, nivel)
            if estado == inventario.OK and activo['es_produccion'] and nivel == 'N1':
                chequeo('inventario', 'FRENA', '%s es de produccion: ahi un cambio es N2 (dos "si" con ANTES y DESPUES), no N1' % alias)
            elif estado == inventario.OK:
                chequeo('inventario', 'OK', 'tipo %s, ambiente %s, IA hasta %s' % (activo['tipo'] or '?', activo['ambiente'] or '?', activo['nivel_ia']))
            else:
                chequeo('inventario', estado, motivo)

    for clave, titulo in CAMPOS[0:1] + CAMPOS[3:]:
        if vacio(campos.get(clave, '')):
            chequeo(clave, 'FRENA', 'falta el campo %s del plan (o es el marcador del molde)' % titulo)
        elif clave == 'respaldo verificado' and niega(campos[clave]):
            chequeo(clave, 'FRENA', 'el Respaldo verificado dice que no hay (o que no se hizo): escribi cual, de cuando y '
                                    'como se verifico, o "no toca datos ni configuracion"')
        else:
            chequeo(clave, 'OK', campos[clave][:120])
    for clave, _ in SECCIONES:
        texto = secciones.get(clave)
        if texto is None or vacio(texto):
            que = 'falta la seccion' if texto is None else 'esta vacia la seccion'
            if clave == 'vuelta atras':
                chequeo(clave, 'FRENA', '%s Vuelta atras: sin vuelta atras escrita el cambio es N3, lo hace una persona' % que)
            else:
                chequeo(clave, 'FRENA', '%s %s' % (que, clave[0].upper() + clave[1:]))
        elif clave == 'vuelta atras' and niega(texto):
            chequeo(clave, 'FRENA', 'la Vuelta atras dice que no hay (o que no se deshace) y no describe un procedimiento: '
                                    'sin vuelta atras escrita el cambio es N3, lo hace una persona')
        elif clave == 'comando exacto' and MARCADOR_EN_COMANDO.search(texto):
            chequeo(clave, 'FRENA', 'el comando tiene un marcador %s: no es el comando exacto' % MARCADOR_EN_COMANDO.search(texto).group(0)[:40])
        else:
            chequeo(clave, 'OK', '')

    estados = [c['estado'] for c in chequeos]
    estado = 'FRENA' if 'FRENA' in estados else 'SIN DATOS' if 'SIN DATOS' in estados else 'OK'
    codigo = {'OK': OK, 'FRENA': FRENA, 'SIN DATOS': SIN_DATOS}[estado]
    ventana = {'plan': campos.get('ventana', ''), 'inventario': activo['ventana'] if activo else ''}
    if estado != 'OK':
        falta = 'completar el plan o el inventario y volver a correr este script; sin OK no se pregunta'
    elif nivel == 'N1':
        falta = 'un "si" de la persona sobre este plan, en su propio turno'
    else:
        falta = 'dos "si" en turnos distintos, con el ANTES (como esta hoy) y el DESPUES (la salida esperada) a la vista entre uno y otro'
    if a.json:
        print(json.dumps({'estado': estado, 'alias': alias, 'nivel': nivel, 'plan': a.plan, 'chequeos': chequeos, 'ventana': ventana,
                          'respaldo': campos.get('respaldo verificado', ''), 'falta': falta, 'no_mira': list(NO_MIRA)},
                         ensure_ascii=True, indent=1))
        return codigo
    print('GATE de SERVIDOR (plan de cambio) -- %s: %s, %s' % (estado, alias or 'sin alias', nivel or 'sin nivel'))
    print('  Plan: %s' % a.plan)
    for c in chequeos:
        print('  %-20s %-10s %s' % (c['chequeo'], c['estado'], c['detalle']))
    print('  Ventana: la del plan "%s"; la del inventario "%s". No la calcula este script: la mira la persona.' % (
        ventana['plan'] or 'sin declarar', ventana['inventario'] or 'sin declarar'))
    print('  Respaldo: "%s" -- lo declara el plan; ningun script lo mide todavia.' % (campos.get('respaldo verificado', '') or 'sin declarar')[:120])
    print('  Lo que falta antes de tocar: %s. DEC-005 no cubre esto.' % falta)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
