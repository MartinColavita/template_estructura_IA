#!/usr/bin/env python3
"""Prueba de bin/analizar-tareas.py SIN RED y sin tarjetas reales: un set armado a mano.

    python bin/probar-analizar-tareas.py

Sale 0 si todos los casos dan lo esperado, 1 si alguno no.

Las Tareas y la Historia de prueba son SINTETICAS (un dominio de reservas inventado, reglas
RN-PRU-nn que no existen en ningun lado, #ID de 6 cifras que no son de nadie) y se escriben en una
carpeta temporal que se borra al terminar: no se copia ninguna tarjeta real al repo.

Cubre: el set que cierra, el set con una Tarea e2e, el hueco (nadie lo nombra, o solo en "No
cubre"), el puntero falso, la fila parcial sin #ID, la fila sin tests, el titulo no textual, la
forma vieja de la tabla ("No lo cubre esta Tarea"), la regla sin Tarea (del Gherkin y del bloque
Reglas de negocio), el choque de contratos, el contrato repetido, el endpoint nombrado en dos
Tareas, los codigos del front que el back no declara, el test de integracion, las dependencias,
los mapas de #ID (--ids, mapa-fichas, items.json del lote, el que esta junto a las Tareas), SIN
DATOS, NO AUDITABLE, --json/--salida y el error inesperado.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
spec = importlib.util.spec_from_file_location('an', os.path.join(AQUI, 'analizar-tareas.py'))
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)

F = chr(0x2192)       # flecha
RAYA = chr(0x2014)
O = chr(0xf3)         # o con tilde
E = chr(0xe9)         # e con tilde
I = chr(0xed)         # i con tilde
PUNTO = chr(0xb7)

T_OBJ = 'Objetivo'
T_ALC = 'Alcance t' + E + 'cnico'
T_CON = 'Contrato t' + E + 'cnico (entrada/salida)'
T_CAS = 'Casos de error'
T_DEP = 'Dependencias'
T_SDD = 'Especificaci' + O + 'n cerrada (SDD)'
T_TES = 'Tests a escribir PRIMERO'
T_SUB = 'Subtareas'
T_DOD = 'Definici' + O + 'n de terminado'


# ---------------------------------------------------------------------------------------
# Armado de la Historia y de las Tareas
# ---------------------------------------------------------------------------------------

def gherkin(escenarios):
    """escenarios: [(titulo, regla)]."""
    s = '<p><b>Caracter' + I + 'stica:</b> Reservas</p>'
    for t, regla in escenarios:
        s += ('<p><b>Escenario:</b> %s <i>[%s]</i><br>&nbsp;&nbsp;<b>Dado</b> una agenda<br>'
              '&nbsp;&nbsp;<b>Cuando</b> se pide<br>&nbsp;&nbsp;<b>Entonces</b> pasa algo</p>'
              % (t, regla))
    return s


ESC = [('Alta de una reserva', 'RN-PRU-01'), ('Reserva repetida', 'RN-PRU-02'),
       ('Aviso en pantalla', 'RN-PRU-01')]
HIST = gherkin(ESC)


def alcance(capa, integracion='no'):
    repo, cap = (('backend-monolito', '<code>api</code> y <code>domain</code> del slice')
                 if capa == 'back' else
                 ('frontend-app', 'view, componente de front') if capa == 'front' else
                 ('los dos', 'back y front levantados'))
    return ('<ul><li><b>Componente / repo:</b> %s</li><li><b>Capa:</b> %s</li><li><b>Requiere test '
            'de integraci' + O + 'n:</b> %s</li></ul>') % (repo, cap, integracion)


def tabla(filas):
    h = ('<table><tr><th>Escenario de la Historia #100001</th><th>Qu' + E +
         ' parte cubre esta Tarea</th><th>Tests que lo verifican</th></tr>')
    return h + ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % f for f in filas) + \
        '</table>'


def no_cubre(items):
    if not items:
        return ''
    return '<p><b>No cubre:</b> ' + (' ' + PUNTO + ' ').join(items) + '</p>'


CONTRATO = ("<pre>paths:\n  /api/reservas:\n    post:\n      responses:\n"
            "        '201': { description: creada }\n"
            "        '409': { description: RESERVA_DUPLICADA }</pre>")
CASOS = ('<table><tr><th>Condici' + O + 'n</th><th>C' + O + 'digo</th><th>Payload</th>'
         '<th>Regla</th></tr><tr><td>reserva repetida</td><td>409</td>'
         '<td>{ "error": "RESERVA_DUPLICADA" }</td><td><i>[RN-PRU-02]</i></td></tr></table>')


def armar(capa='back', filas=(), nc=(), tests=(), contrato=None, casos=None, dep=None,
          integracion='no', subtareas=(), dod=(), objetivo='Hacer su parte de las reservas.',
          sin_tabla=False):
    secs = [(T_OBJ, '<p>%s</p>' % objetivo), (T_ALC, alcance(capa, integracion))]
    if contrato is not None:
        secs.append((T_CON, contrato))
    if casos is not None:
        secs.append((T_CAS, casos))
    if dep is not None:
        secs.append((T_DEP, '<ul>' + ''.join('<li>%s</li>' % x for x in dep) + '</ul>'))
    secs.append((T_SDD, '<p>Comportamiento.</p>' + ('' if sin_tabla else tabla(filas)) +
                 no_cubre(nc)))
    secs.append((T_TES, '<ol>' + ''.join('<li>%s</li>' % t for t in tests) + '</ol>'))
    secs.append((T_SUB, '<ol>' + ''.join('<li>%s</li>' % t for t in subtareas) + '</ol>'))
    secs.append((T_DOD, '<ul>' + ''.join('<li>%s</li>' % t for t in dod) + '</ul>'))
    return '<hr>\n'.join('<h3>%s</h3>\n%s\n' % s for s in secs)


def back(**k):
    base = dict(
        capa='back',
        filas=[('Alta de una reserva', 'Todo el escenario', '1'),
               ('Reserva repetida', 'El 409 del back. El aviso en pantalla es de [T-02]', '2')],
        nc=['Aviso en pantalla ([T-02])'],
        tests=['Caso feliz: alta ' + F + ' 201 <i>[RN-PRU-01]</i>',
               'Reserva repetida ' + F + ' 409 + RESERVA_DUPLICADA <i>[RN-PRU-02]</i>'],
        contrato=CONTRATO, casos=CASOS,
        dep=['<b>Depende de:</b> la tabla de reservas.', '<b>De esto depende:</b> [T-02].'])
    base.update(k)
    return armar(**base)


def front(**k):
    base = dict(
        capa='front',
        filas=[('Reserva repetida', 'El aviso cuando el back devuelve 409. El 409 es de [T-01]',
                '2'),
               ('Aviso en pantalla', 'Todo el escenario', '1, 2')],
        nc=['Alta de una reserva ([T-01])'],
        tests=['Pantalla: alta ' + F + ' se ve "Reserva creada" <i>[RN-PRU-01]</i>',
               'Pantalla: el back devuelve 409 RESERVA_DUPLICADA ' + F + ' se ve "Ya existe" '
               '<i>[RN-PRU-02]</i>'],
        dep=['<b>Depende de:</b> [T-01], que define el 409.'])
    base.update(k)
    return armar(**base)


def e2e(**k):
    base = dict(
        capa='otra', objetivo='Probar el back y el front juntos, levantados de verdad.',
        filas=[('Reserva repetida', 'Un caso de punta a punta', '1')],
        nc=['Alta de una reserva ([T-01])', 'Aviso en pantalla ([T-02])'],
        tests=['Integraci' + O + 'n: reserva repetida en DESA ' + F + ' se ve "Ya existe" '
               '<i>[RN-PRU-02]</i>'],
        integracion='s' + I, subtareas=['Escribir el test de integraci' + O + 'n 1.'],
        dod=['El test de integraci' + O + 'n 1 pasa en DESA.'],
        dep=['<b>Depende de:</b> [T-01] y [T-02], desplegadas.'])
    base.update(k)
    return armar(**base)


# ---------------------------------------------------------------------------------------
# Corrida
# ---------------------------------------------------------------------------------------

class Caso(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix='caso-', dir=base)

    def archivo(self, nombre, contenido):
        ruta = os.path.join(self.dir, nombre)
        with io.open(ruta, 'w', encoding='utf-8', newline='\n') as f:
            f.write(contenido)
        return ruta

    def ruta(self, nombre):
        return os.path.join(self.dir, nombre)

    def correr(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            try:
                codigo = an.main(args + ['--json'])
            except SystemExit as e:
                codigo = e.code
        try:
            d = json.loads(buf.getvalue())
        except ValueError:
            d = {}
        return codigo, d

    def set(self, tareas, historia=HIST, extra=()):
        """tareas: [(nombre, html)]. Devuelve (codigo, json)."""
        h = self.archivo('H-100001-criterios.html', historia)
        rutas = [self.archivo(nom, html) for nom, html in tareas]
        return self.correr(['--historia', h] + rutas + list(extra))


def renglones(d, nivel=None, chequeo=None, texto=None):
    res = []
    for x in d.get('renglones') or []:
        if nivel and x['nivel'] != nivel:
            continue
        if chequeo and x['chequeo'] != chequeo:
            continue
        if texto and texto not in x['detalle'] + ' ' + x['evidencia']:
            continue
        res.append(x)
    return res


def cuantos(d, nivel, chequeo=None, texto=None):
    return len(renglones(d, nivel, chequeo, texto))


RESULTADOS = []


def chequeo(nombre, obtenido, esperado, d=None):
    ok = obtenido == esperado
    RESULTADOS.append(ok)
    print(('ok    ' if ok else 'FALLA ') + nombre)
    if not ok:
        print('      esperado: %r' % (esperado,))
        print('      obtenido: %r' % (obtenido,))
        for x in (d or {}).get('renglones') or []:
            if x['nivel'] in ('HALLAZGO', 'NO_AUDITABLE', 'AVISO'):
                print('        %s [%s] %s -- %s' % (x['nivel'], x['chequeo'], x['detalle'],
                                                   x['evidencia']))


def casos(base):
    B, FR = ('T-01.html', back()), ('T-02.html', front())

    # --- el set que cierra ------------------------------------------------------------
    c, d = Caso(base).set([B, FR])
    chequeo('set que cierra: 0, sin hallazgos, cada Escenario con su Tarea',
            (c, cuantos(d, 'HALLAZGO'), cuantos(d, 'NO_AUDITABLE'), cuantos(d, 'OK', 'AN-7a'),
             d.get('datos', {}).get('escenarios_sin_cobertura')), (0, 0, 0, 3, []), d)
    chequeo('set que cierra: punteros, reglas, contrato, codigos, dependencias e integracion OK',
            [cuantos(d, 'OK', x) >= 1 for x in ('AN-7d', 'AN-2', 'AN-1', 'AN-5', 'AN-6', 'AN-8')],
            [True] * 6, d)
    chequeo('set que cierra: "Reserva repetida" repartida entre back y front sin e2e es AVISO',
            cuantos(d, 'AVISO', 'AN-7', 'quien prueba la union'), 1, d)
    chequeo('set que cierra: datos con escenarios, tareas y filas por Tarea',
            (d['datos'].get('escenarios'), d['datos'].get('tareas'),
             d['datos'].get('filas_por_tarea')), (3, 2, {'T-01': 2, 'T-02': 2}), d)

    c, d = Caso(base).set([B, FR, ('T-03.html', e2e())])
    chequeo('con una Tarea e2e que lo cubre: no hay aviso de union, y su integracion cierra',
            (c, cuantos(d, 'AVISO', 'AN-7', 'quien prueba la union'),
             cuantos(d, 'OK', 'AN-8', 'hay test, subtarea')), (0, 0, 1), d)

    # --- AN-7a: huecos ----------------------------------------------------------------
    c, d = Caso(base).set([B, FR], historia=gherkin(ESC + [('Cancelar una reserva',
                                                             'RN-PRU-01')]))
    chequeo('hueco: un Escenario que ninguna Tarea nombra es HALLAZGO (1)',
            (c, cuantos(d, 'HALLAZGO', 'AN-7a', 'ninguna Tarea lo nombra'),
             d['datos'].get('escenarios_sin_cobertura')), (1, 1, ['Cancelar una reserva']), d)

    fr = front(filas=[('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2')],
               nc=['Alta de una reserva ([T-01])', 'Aviso en pantalla ([T-01])'])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('hueco: un Escenario que solo esta en "No cubre" no cuenta como cobertura',
            (c, cuantos(d, 'HALLAZGO', 'AN-7a', 'Aviso en pantalla')), (1, 1), d)
    chequeo('hueco: los dos "No cubre" que se apuntan entre si son punteros falsos',
            cuantos(d, 'HALLAZGO', 'AN-7d', 'puntero falso'), 2, d)

    # --- AN-7d: puntero falso con el Escenario cubierto por otra -----------------------
    t3 = front(filas=[('Alta de una reserva', 'La pantalla del alta. Guardarla es de [T-01]',
                       '1')],
               nc=['Reserva repetida ([T-01])', 'Aviso en pantalla ([T-02])'])
    b = back(nc=['Aviso en pantalla ([T-03])'])
    c, d = Caso(base).set([('T-01.html', b), FR, ('T-03.html', t3)])
    chequeo('puntero falso: "No cubre" apunta a una Tarea del set que no tiene la fila',
            (c, cuantos(d, 'HALLAZGO', 'AN-7d', '[T-03]'), cuantos(d, 'HALLAZGO', 'AN-7a')),
            (1, 1, 0), d)

    b = back(nc=['Aviso en pantalla (#100099)'])
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('puntero a un #ID que no esta en el set: AVISO, no HALLAZGO',
            (c, cuantos(d, 'AVISO', 'AN-7d', '#100099'), cuantos(d, 'HALLAZGO')), (0, 1, 0), d)

    # --- AN-7e, 7c, 7b -----------------------------------------------------------------
    b = back(filas=[('Alta de una reserva', 'Todo el escenario', '1'),
                    ('Reserva repetida', 'Solo el lado del back: el 409', '2')])
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('fila que cubre solo una parte y no nombra la otra Tarea: HALLAZGO AN-7e',
            (c, cuantos(d, 'HALLAZGO', 'AN-7e', 'Reserva repetida')), (1, 1), d)

    b = back(filas=[('Alta de una reserva', 'Todo el escenario', '1'),
                    ('Reserva repetida', 'Que la serie siga con un solo tramo', '2')])
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('"un solo tramo" no es cobertura parcial', cuantos(d, 'HALLAZGO', 'AN-7e'), 0, d)

    fr = front(filas=[('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('Aviso en pantalla', 'Todo el escenario', RAYA)])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('fila que cubre sin tests: HALLAZGO AN-7c',
            (c, cuantos(d, 'HALLAZGO', 'AN-7c', 'Aviso en pantalla')), (1, 1), d)

    fr = front(filas=[('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('aviso en Pantalla', 'Todo el escenario', '1')])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('titulo que difiere en mayusculas: HALLAZGO AN-7b, pero no es hueco',
            (c, cuantos(d, 'HALLAZGO', 'AN-7b', 'difiere solo'), cuantos(d, 'HALLAZGO', 'AN-7a')),
            (1, 1, 0), d)

    fr = front(filas=[('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('Aviso por pantalla', 'Todo el escenario', '1')])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('titulo que no es de ningun Escenario: HALLAZGO AN-7b y el Escenario queda hueco',
            (c, cuantos(d, 'HALLAZGO', 'AN-7b', 'no coincide'),
             cuantos(d, 'HALLAZGO', 'AN-7a', 'Aviso en pantalla')), (1, 1, 1), d)

    # --- forma vieja de la tabla -------------------------------------------------------
    viejo = 'No lo cubre esta Tarea: es de '
    b = back(filas=[('Alta de una reserva', 'Todo el escenario', '1'),
                    ('Reserva repetida', 'El 409. El aviso es de [T-02]', '2'),
                    ('Aviso en pantalla', viejo + '[T-02]', RAYA)], nc=[])
    fr = front(filas=[('Alta de una reserva', viejo + '[T-01]', RAYA),
                      ('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('Aviso en pantalla', 'Todo el escenario', '1, 2')], nc=[])
    c, d = Caso(base).set([('T-01.html', b), ('T-02.html', fr)])
    chequeo('forma vieja ("No lo cubre esta Tarea: es de"): no es cobertura, y sus punteros se '
            'siguen', (c, cuantos(d, 'HALLAZGO'), d['datos']['filas_por_tarea']),
            (0, 0, {'T-01': 2, 'T-02': 2}), d)

    fr = front(filas=[('Alta de una reserva', viejo + '[T-01]', RAYA),
                      ('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('Aviso en pantalla', viejo + '[T-01]', RAYA)], nc=[])
    c, d = Caso(base).set([('T-01.html', b), ('T-02.html', fr)])
    chequeo('forma vieja: dos filas "No lo cubre" que se apuntan entre si dejan un hueco',
            (c, cuantos(d, 'HALLAZGO', 'AN-7a', 'Aviso en pantalla'),
             cuantos(d, 'HALLAZGO', 'AN-7d')), (1, 1, 2), d)

    # --- AN-2: reglas ------------------------------------------------------------------
    c, d = Caso(base).set([B, FR], historia=gherkin(ESC[:2] + [('Aviso en pantalla',
                                                                 'RN-PRU-03')]))
    chequeo('regla de la Historia que ninguna Tarea cita: HALLAZGO AN-2',
            (c, cuantos(d, 'HALLAZGO', 'AN-2', 'RN-PRU-03')), (1, 1), d)

    k = Caso(base)
    desc = k.archivo('H-100001-descripcion.html',
                     '<h3>Reglas de negocio</h3><ul><li>[RN-PRU-01] alta (OKF: x.md)</li>'
                     '<li>[RN-PRU-04] cancelacion (OKF: x.md)</li></ul>')
    c, d = k.set([B, FR], extra=['--descripcion', desc])
    chequeo('regla del bloque Reglas de negocio (--descripcion) sin Tarea: HALLAZGO AN-2',
            (c, cuantos(d, 'HALLAZGO', 'AN-2', 'RN-PRU-04')), (1, 1), d)
    c, d = Caso(base).set([B, FR], extra=['--descripcion', os.path.join(base, 'no-existe.html')])
    chequeo('--descripcion que no se puede leer: NO AUDITABLE (1)',
            (c, cuantos(d, 'NO_AUDITABLE', 'AN-2')), (1, 1), d)

    # --- AN-1: contratos ---------------------------------------------------------------
    otro = ("<pre>paths:\n  /api/reservas:\n    post:\n      responses:\n"
            "        '201': { description: creada }\n"
            "        '422': { description: FECHA_INVALIDA }</pre>")
    b3 = back(contrato=otro, filas=[('Alta de una reserva', 'Todo el escenario', '1')],
              nc=['Reserva repetida ([T-01])', 'Aviso en pantalla ([T-02])'])
    c, d = Caso(base).set([B, FR, ('T-03.html', b3)])
    chequeo('choque: el mismo POST /api/reservas con dos contratos distintos es HALLAZGO AN-1',
            (c, cuantos(d, 'HALLAZGO', 'AN-1', 'choque')), (1, 1), d)

    igual1 = ("<pre>paths:\n  /api/reservas/{id}:\n    get:\n      responses:\n"
              "        '200': { description: ok }   # de #100050\n</pre>")
    igual2 = ("<pre>paths:\n  /api/reservas/{reservaId}:\n    get:\n      responses:\n"
              "        \"200\":  {description: ok}\n</pre>")
    b1 = back(contrato=igual1)
    b3 = back(contrato=igual2, filas=[('Alta de una reserva', 'Todo el escenario', '1')],
              nc=['Reserva repetida ([T-01])', 'Aviso en pantalla ([T-02])'])
    c, d = Caso(base).set([('T-01.html', b1), FR, ('T-03.html', b3)])
    chequeo('mismo endpoint con el mismo contrato (otros espacios, comentarios y nombre del '
            'parametro): AVISO repetido, no HALLAZGO',
            (c, cuantos(d, 'AVISO', 'AN-1', 'repetido'), cuantos(d, 'HALLAZGO', 'AN-1')),
            (0, 1, 0), d)

    prosa = ('<p>Mismo endpoint de #100050: POST /api/reservas. Solo se muestra lo que '
             'cambia.</p><pre>components:\n  schemas:\n    Reserva:\n      type: object\n</pre>')
    prosa2 = prosa.replace('type: object', 'properties: { nota: { type: string } }')
    b1 = back(contrato=prosa)
    b3 = back(contrato=prosa2, filas=[('Alta de una reserva', 'Todo el escenario', '1')],
              nc=['Reserva repetida ([T-01])', 'Aviso en pantalla ([T-02])'])
    c, d = Caso(base).set([('T-01.html', b1), FR, ('T-03.html', b3)])
    chequeo('dos Tareas que extienden el mismo endpoint en prosa: AVISO, no choque',
            (c, cuantos(d, 'AVISO', 'AN-1', 'tocan el mismo endpoint'),
             cuantos(d, 'AVISO', 'AN-1', 'schema Reserva'), cuantos(d, 'HALLAZGO', 'AN-1')),
            (0, 1, 1, 0), d)

    # --- AN-5: codigos -----------------------------------------------------------------
    fr = front(tests=['Pantalla: alta ' + F + ' se ve "Reserva creada" <i>[RN-PRU-01]</i>',
                      'Pantalla: el back devuelve 409 ' + F + ' se ve "Ya existe" '
                      '<i>[RN-PRU-02]</i>',
                      'Pantalla: el back responde 404 ' + F + ' se ve "No existe"',
                      'Pantalla: un texto de 400 caracteres ' + F + ' se corta',
                      'Core: el adapter lanza un error con "CAMPO_RARO" ' + F + ' se ve un aviso'])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('el front espera un 404 que ningun back declara: AVISO AN-5 (y "400 caracteres" o '
            '"lanza un error" no cuentan)',
            (c, cuantos(d, 'AVISO', 'AN-5', '404'), cuantos(d, 'AVISO', 'AN-5', '400'),
             cuantos(d, 'AVISO', 'AN-5', 'CAMPO_RARO')), (0, 1, 0, 0), d)

    # --- AN-8: integracion -------------------------------------------------------------
    b = back(integracion='s' + I)
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('"Requiere test de integracion: si" sin test, subtarea ni DoD: 3 HALLAZGO AN-8',
            (c, cuantos(d, 'HALLAZGO', 'AN-8', 'T-01')), (1, 3), d)

    # --- AN-6: dependencias ------------------------------------------------------------
    b = back(dep=['<b>Depende de:</b> #100099, la tabla.', '<b>De esto depende:</b> [T-02].'])
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('dependencia fuera del set: AVISO AN-6 "verificar en el tablero"',
            (c, cuantos(d, 'AVISO', 'AN-6', '#100099')), (0, 1), d)
    b = back(dep=['<b>Depende de:</b> [T-02].'])
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('dos Tareas que dependen una de la otra: AVISO AN-6 circular',
            cuantos(d, 'AVISO', 'AN-6', 'circular'), 1, d)
    fr = front(dep=['<b>Depende de:</b> las Tareas #100011 a #100013.'])
    k = Caso(base)
    m = k.archivo('mapa.json', json.dumps({'[T-01]': 100011, '[T-02]': 100012}))
    c, d = k.set([B, ('T-02.html', fr)], extra=['--ids', m])
    chequeo('rango "#100011 a #100013": #100011 esta en el set, #100013 no',
            (cuantos(d, 'OK', 'AN-6', 'depende de T-01'), cuantos(d, 'AVISO', 'AN-6', '#100013'),
             cuantos(d, 'AVISO', 'AN-6', '#100011')), (1, 1, 0), d)

    # --- AN-4 --------------------------------------------------------------------------
    fr = front(filas=[('Alta de una reserva', 'Todo el escenario', '1'),
                      ('Reserva repetida', 'El aviso del 409. El 409 es de [T-01]', '2'),
                      ('Aviso en pantalla', 'Todo el escenario', '1, 2')], nc=[])
    c, d = Caso(base).set([B, ('T-02.html', fr)])
    chequeo('dos Tareas que dicen cubrir entero el mismo Escenario: AVISO AN-4',
            (c, cuantos(d, 'AVISO', 'AN-4', 'Alta de una reserva')), (0, 1), d)

    # --- quien es cada Tarea -----------------------------------------------------------
    con_ids = lambda h: h.replace('[T-01]', '#100011').replace('[T-02]', '#100012')  # noqa: E731
    bi, fi = con_ids(back()), con_ids(front())
    c, d = Caso(base).set([('back.html', bi), ('front.html', fi)])
    chequeo('sin --ids y con nombres sin T-nn: los punteros por #ID no se resuelven (AVISO)',
            (c, cuantos(d, 'AVISO', 'AN-7d', 'no es ninguna Tarea'),
             cuantos(d, 'AVISO', 'set', 'no se que #ID')), (0, 2, 2), d)
    k = Caso(base)
    m = k.archivo('ids.json', json.dumps({'back.html': '#100011', 'front': 100012}))
    c, d = k.set([('back.html', bi), ('front.html', fi)], extra=['--ids', m])
    chequeo('--ids {archivo: #ID}: los punteros se resuelven y se verifican',
            (c, cuantos(d, 'AVISO', 'AN-7d'), cuantos(d, 'OK', 'AN-7d')), (0, 0, 1), d)
    k = Caso(base)
    m = k.archivo('mapa-fichas.json', json.dumps({'[T-01]': 100011, '[T-02]': 100012}))
    c, d = k.set([('T01-back.html', bi), ('T02-front.v2.html', fi)], extra=['--ids', m])
    chequeo('--ids con el formato de mapa-fichas ({"[T-nn]": NNNNNN}) y archivos "T01-..."',
            (c, cuantos(d, 'AVISO', 'AN-7d'), cuantos(d, 'OK', 'AN-7d')), (0, 0, 1), d)
    k = Caso(base)
    k.archivo('mapa-ids.json', json.dumps({'[T-01]': '100011', '[T-02]': '100012'}))
    c, d = k.set([('T-01.html', bi), ('T-02.html', fi)])
    chequeo('sin --ids: lee el mapa-ids.json que esta junto a las Tareas',
            (c, cuantos(d, 'AVISO', 'AN-7d'), cuantos(d, 'OK', 'set', 'mapa-ids.json')), (0, 0, 1), d)
    k = Caso(base)
    items = {'items': [{'clave': 'T-01', 'tipo': 'Tarea', 'id': '100011', 'archivo': 'b.html'},
                       {'clave': 'T-02', 'tipo': 'Tarea', 'id': None, 'archivo': 'f.html'}]}
    m = k.archivo('items.json', json.dumps(items))
    c, d = k.set([('b.html', back()), ('f.html', fi)], extra=['--ids', m])
    chequeo('--ids con el items.json del lote (clave, id, archivo)',
            (c, cuantos(d, 'AVISO', 'AN-7d'), cuantos(d, 'HALLAZGO')), (0, 0, 0), d)
    c, d = Caso(base).set([B, FR], extra=['--ids', os.path.join(base, 'no-existe.json')])
    chequeo('--ids que no se puede leer: NO AUDITABLE (1)',
            (c, cuantos(d, 'NO_AUDITABLE', 'AN-7d')), (1, 1), d)
    c, d = Caso(base).set([B, FR, ('T02-front.v2.html', front())])
    chequeo('dos archivos de la misma Tarea ([T-02]) en el set: AVISO',
            cuantos(d, 'AVISO', 'set', 'misma Tarea'), 1, d)

    # --- SIN DATOS y NO AUDITABLE ------------------------------------------------------
    k = Caso(base)
    t1 = k.archivo('T-01.html', back())
    c, d = k.correr(['--historia', k.ruta('no-existe.html'), t1])
    chequeo('Historia que no existe: SIN DATOS (2)', (c, d.get('veredicto')), (2, 'SIN DATOS'))
    h = k.archivo('H-100001-criterios.html', HIST)
    c, d = k.correr(['--historia', h, k.ruta('no-1.html'), k.ruta('no-2.html')])
    chequeo('ninguna Tarea legible: SIN DATOS (2)', (c, d.get('veredicto')), (2, 'SIN DATOS'))
    c, d = k.correr(['--historia', h])
    chequeo('sin Tareas: SIN DATOS (2)', (c, d.get('veredicto')), (2, 'SIN DATOS'))
    vacia = k.archivo('vacia.html', '   ')
    c, d = k.correr(['--historia', vacia, t1])
    chequeo('Historia vacia: SIN DATOS (2)', c, 2)
    c, d = k.correr(['--historia', h, t1, k.ruta('no-existe.html'), ''])
    chequeo('una Tarea que no se puede leer (o la ruta vacia del lote): NO AUDITABLE (1)',
            (c, cuantos(d, 'NO_AUDITABLE', 'set')), (1, 2), d)
    sin_h3 = k.archivo('T-09.html', '<p>solo un parrafo</p>')
    c, d = k.correr(['--historia', h, t1, sin_h3])
    chequeo('una Tarea sin <h3>: NO AUDITABLE (1)',
            (c, cuantos(d, 'NO_AUDITABLE', 'set', 'sin ninguna seccion')), (1, 1), d)
    c, d = Caso(base).set([B, FR], historia='<p>Caracteristica: sin escenarios</p>')
    chequeo('Historia sin Escenarios: NO AUDITABLE (Regla del cero)',
            (c, cuantos(d, 'NO_AUDITABLE', 'AN-7')), (1, 1), d)
    b = back(sin_tabla=True)
    c, d = Caso(base).set([('T-01.html', b), FR])
    chequeo('Tarea sin tabla de Escenarios: AVISO, y lo que solo ella cubria queda hueco',
            (c, cuantos(d, 'AVISO', 'AN-7', 'no tiene la tabla'),
             cuantos(d, 'HALLAZGO', 'AN-7a', 'Alta de una reserva')), (1, 1, 1), d)

    # --- main: --salida, argumentos mezclados, error inesperado ------------------------
    k = Caso(base)
    h = k.archivo('H-100001-criterios.html', HIST)
    t1, t2 = k.archivo('T-01.html', back()), k.archivo('T-02.html', front())
    sal = k.ruta('set.json')
    c, d = k.correr(['--historia', h, t1, '--salida', sal, t2])
    try:
        with io.open(sal, encoding='utf-8') as f:
            guardado = json.load(f)
    except (OSError, ValueError):
        guardado = {}
    chequeo('main: argumentos mezclados, --salida escribe el mismo json',
            (c, guardado.get('codigo'), guardado.get('datos', {}).get('tareas'),
             sorted(k2 for k2 in ('escenarios', 'tareas', 'escenarios_sin_cobertura',
                                  'filas_por_tarea') if k2 in guardado.get('datos', {}))),
            (0, 0, 2, ['escenarios', 'escenarios_sin_cobertura', 'filas_por_tarea', 'tareas']))
    c, _ = k.correr(['--json'])
    chequeo('main: sin --historia es un pedido mal armado: 2', c, 2)
    guardado_fn = an.analizar

    def explota(*a, **kw):
        raise AttributeError('forma inesperada')
    an.analizar = explota
    try:
        c, d = k.correr(['--historia', h, t1, t2])
    finally:
        an.analizar = guardado_fn
    chequeo('error inesperado dentro del script: SIN DATOS (2), con su json', (c, d.get('codigo')),
            (2, 2))


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    base = tempfile.mkdtemp(prefix='probar-analizar-tareas-')
    try:
        casos(base)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    malos = RESULTADOS.count(False)
    print()
    print(('OK -- ' if not malos else 'FALLA -- ') + str(len(RESULTADOS) - malos) + ' de ' +
          str(len(RESULTADOS)) + ' casos dieron lo esperado.')
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
