#!/usr/bin/env python3
"""Prueba de bin/auditar-tarea.py SIN RED y sin tarjetas reales: Tareas armadas a mano.

    python bin/probar-auditar-tarea.py

Sale 0 si todos los casos dan lo esperado, 1 si alguno no.

Las Tareas de prueba son SINTETICAS (un dominio de reservas inventado, reglas RN-PRU-nn que no
existen en ningun lado y un indice de reglas falso): no se copia ninguna tarjeta real al repo.
Los titulos de las secciones salen del mismo esqueleto que lee el script
(checklists/mapa-campos-azure.md), asi que si el esqueleto cambia, la prueba lo sigue.

Cubre: el caso sin hallazgos, una familia de HALLAZGO por chequeo, SIN DATOS, NO AUDITABLE sin
--historia, el Esquema nuevo y el viejo, la linea "No cubre", la forma vieja de la tabla y la
exencion de front.
"""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
spec = importlib.util.spec_from_file_location("at", os.path.join(AQUI, "auditar-tarea.py"))
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)

from auditoria import tarea  # noqa: E402

F = chr(0x2192)       # flecha
W = chr(0x26a0)       # marca de pendiente
RAYA = chr(0x2014)
O = chr(0xf3)         # o con tilde
I = chr(0xed)         # i con tilde
A = chr(0xe1)         # a con tilde
PUNTO = chr(0xb7)

ESQ = tarea.esqueleto()
CLAVES = tarea.claves_esqueleto(ESQ)
TITULO = dict(zip(CLAVES, ESQ))
INDICE = {'RN-PRU-01': 'cerebro-digital/x.md', 'RN-PRU-02': 'cerebro-digital/x.md'}


def tabla_sdd(filas):
    h = ('<table><tr><th>Escenario de la Historia #100001</th><th>Qu' + chr(0xe9) +
         ' parte cubre esta Tarea</th><th>Tests que lo verifican</th></tr>')
    return h + ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % f for f in filas) + \
        '</table>'


FILAS = [('Alta de una reserva', 'Todo el escenario', '1, 2'),
         ('Reserva repetida', 'Todo el escenario', '3, 4')]
NO_CUBRE = '<p><b>No cubre:</b> Aviso en pantalla (#100002)</p>'


def sdd(filas=None, no_cubre=NO_CUBRE, extra=''):
    return ('<p><b>Comportamiento exacto:</b> el alta guarda la reserva en PENDIENTE '
            '<i>[RN-PRU-01]</i>.</p>' + tabla_sdd(FILAS if filas is None else filas) +
            no_cubre + extra)


TESTS = [
    'Caso feliz: fecha 2026-10-01 ' + F + ' 201 + estado PENDIENTE <i>[RN-PRU-01]</i>',
    'Esquema ' + RAYA + ' estado al confirmar:<ul><li>reserva PENDIENTE ' + F +
    ' CONFIRMADA</li><li>reserva sin estado ' + F + ' 409</li></ul>',
    'Reserva repetida ' + F + ' 409 + RESERVA_DUPLICADA <i>[RN-PRU-02]</i>',
    'Invariante de negocio protegida: una reserva CONFIRMADA no vuelve a PENDIENTE ' + F +
    ' 409 <i>[RN-PRU-02]</i>',
]


def lista_tests(tests=None, intro='<p><b>Datos base:</b> fecha 2026-10-01.</p>'):
    return intro + '<ol>' + ''.join('<li>%s</li>' % t for t in (TESTS if tests is None else tests)) \
        + '</ol>'


MODOS = ['Estado', 'Concurrencia', 'Autorizaci' + O + 'n', 'Dependencia ca' + I + 'da',
         'L' + I + 'mites', 'Idempotencia']


def modos(familias=None):
    return '<ul>' + ''.join('<li><b>%s:</b> no aplica porque es un alta simple.</li>' % f
                            for f in (MODOS if familias is None else familias)) + '</ul>'


ALCANCE_BACK = ('<ul><li><b>Componente / repo:</b> backend-monolito</li><li><b>Capa:</b> '
                '<code>api</code> y <code>domain</code> del slice</li><li><b>Requiere test de '
                'integraci' + O + 'n:</b> no</li></ul>')
ALCANCE_FRONT = ('<ul><li><b>Componente / repo:</b> frontend-app</li><li><b>Capa:</b> view, '
                 'componente de front</li><li><b>Requiere test de integraci' + O + 'n:</b> no</li>'
                 '</ul>')
CONTRATO = ("<pre>paths:\n  /api/reservas:\n    post:\n      responses:\n"
            "        '201': { description: creada }\n"
            "        '409': { description: RESERVA_DUPLICADA }\n"
            "components:\n  schemas:\n    Reserva:\n      properties:\n"
            "        estado: { type: string, enum: [PENDIENTE, CONFIRMADA] }</pre>")
CASOS = ('<table><tr><th>Condici' + O + 'n</th><th>C' + O + 'digo</th><th>Payload</th>'
         '<th>Regla</th></tr><tr><td>reserva repetida</td><td>409</td>'
         '<td>{ "error": "RESERVA_DUPLICADA" }</td><td><i>[RN-PRU-02]</i></td></tr></table>')

BASE = {
    'objetivo': '<p>Exponer el alta de una reserva <i>[RN-PRU-01]</i>.</p>',
    'alcance': ALCANCE_BACK,
    'contrato': CONTRATO,
    'validaciones': '<ul><li><b><code>fecha</code>:</b> obligatoria <i>[RN-PRU-01]</i></li></ul>',
    'casos': CASOS,
    'dependencias': '<ul><li><b>Depende de:</b> la tabla de reservas.</li></ul>',
    'especificacion': sdd(),
    'tests': lista_tests(),
    'modos': modos(),
    'subtareas': '<ol><li>Escribir en rojo los tests 1 a 4.</li></ol>',
    'material': ('<ul><li><b>Documento fuente:</b> <a href="https://git.example/x.md">'
                 'cerebro-digital/x.md</a>. Reglas: RN-PRU-01 y RN-PRU-02.</li></ul>'),
    'resultado': '<p>MR con el endpoint en DESA.</p>',
    'definicion': '<ul><li>Los tests 1 a 4 tienen su rojo registrado.</li></ul>',
    'datos': '<p>Ninguno.</p>',
}


def armar(cambios=None, quitar=(), renombrar=None, agregar=(), cambiar_orden=None):
    """Una Tarea en html: la base, con cambios por clave de seccion."""
    cambios, renombrar = cambios or {}, renombrar or {}
    secs = [[renombrar.get(k, TITULO[k]), cambios.get(k, BASE[k])] for k in CLAVES
            if k not in quitar]
    if cambiar_orden:
        a, b = [i for i, k in enumerate([k for k in CLAVES if k not in quitar])
                if k in cambiar_orden]
        secs[a], secs[b] = secs[b], secs[a]
    secs += [list(x) for x in agregar]
    return '<hr>\n'.join('<h3>%s</h3>\n%s\n' % (t, c) for t, c in secs)


def gherkin(titulos):
    s = '<p><b>Caracter' + I + 'stica:</b> Reservas</p>'
    for t in titulos:
        s += ('<p><b>Escenario:</b> %s <i>[RN-PRU-01]</i><br>&nbsp;&nbsp;<b>Dado</b> una agenda<br>'
              '&nbsp;&nbsp;<b>Cuando</b> se pide<br>&nbsp;&nbsp;<b>Entonces</b> pasa algo</p>' % t)
    return s


HIST = gherkin(['Alta de una reserva', 'Reserva repetida', 'Aviso en pantalla'])
FRONT = {'alcance': ALCANCE_FRONT,
         'tests': lista_tests(['Pantalla: alta con fecha 2026-10-01 ' + F + ' se ve "Reserva creada"',
                               'Pantalla: alta sin fecha ' + F + ' se ve "Falta la fecha"',
                               'Pantalla: reserva repetida ' + F + ' se ve "Ya existe" '
                               '<i>[RN-PRU-02]</i>',
                               'Invariante: el boton queda inhabilitado al guardar ' + F +
                               ' no se manda dos veces'])}
FRONT_SIN = ('contrato', 'validaciones', 'casos')
UI_SIN = ('contrato', 'validaciones', 'casos', 'dependencias', 'especificacion', 'tests', 'modos')


def correr(html, historia=HIST, indice=INDICE, ruta='prueba-back.html',
           ruta_historia='H-100001-criterios.html'):
    return at.auditar(html, ruta, historia, None if historia is not None else
                      'no se paso --historia', ruta_historia, indice, ESQ, None)


def tiene(r, nivel, chequeo, texto=None):
    return any(n == nivel and c == chequeo and (texto is None or texto in d + ' ' + e)
               for n, c, d, e in r.renglones)


# (nombre, html, kwargs para correr, codigo esperado, [debe tener], [no debe tener])
# cada "debe" es (nivel, chequeo) o (nivel, chequeo, pedazo del detalle)
CASOS = [
    ("Tarea de back completa, con su Historia: sin hallazgos",
     armar(), {}, 0, [('OK', '2b-1'), ('OK', '2b-5/AT-5'), ('OK', 'AT-3'), ('OK', 'AT-2'),
                      ('OK', 'ESQ'), ('OK', '2b-4/AT-15')],
     [('HALLAZGO', None), ('NO_AUDITABLE', None)]),

    ("Sin --historia: el conteo de Escenarios es NO AUDITABLE, nunca OK",
     armar(), {'historia': None}, 1, [('NO_AUDITABLE', '2b-5/AT-5')],
     [('HALLAZGO', None), ('OK', '2b-5/AT-5')]),

    ("Historia padre sin Escenarios: NO AUDITABLE (Regla del cero)",
     armar(), {'historia': '<p>Caracteristica: sin escenarios</p>'}, 1,
     [('NO_AUDITABLE', '2b-5/AT-5', 'ningun Escenario')], []),

    ("Tarea vacia: SIN DATOS", '   ', {}, 2, [], []),
    ("Html sin ningun <h3>: SIN DATOS", '<p>solo un parrafo</p>', {}, 2, [], []),

    # 2b-1
    ("Falta una seccion del esqueleto",
     armar(quitar=('resultado',)), {}, 1, [('HALLAZGO', '2b-1', 'falta la seccion')], []),
    ("Seccion con otro nombre",
     armar(renombrar={'tests': 'Tests a escribir PRIMERO (TDD test-first)'}), {}, 1,
     [('HALLAZGO', '2b-1', 'tiene que llamarse')], []),
    ("Secciones fuera de orden",
     armar(cambiar_orden=('subtareas', 'material')), {}, 1, [('HALLAZGO', '2b-1', 'orden')], []),
    ("Seccion extra conocida (Esfuerzo IA): OK, ni AVISO ni HALLAZGO",
     armar(agregar=[('Esfuerzo IA', '<p>3 puntos</p>')]), {}, 0,
     [('OK', '2b-1', 'Esfuerzo IA')], [('HALLAZGO', None), ('AVISO', '2b-1')]),
    ("Seccion de mas desconocida: AVISO, no HALLAZGO",
     armar(agregar=[('Notas sueltas', '<p>algo</p>')]), {}, 0,
     [('AVISO', '2b-1', 'Notas sueltas')], [('HALLAZGO', None)]),

    # exenciones
    ("Tarea de front sin Contrato, Validaciones ni Casos de error: exencion de front",
     armar(FRONT, quitar=FRONT_SIN), {'ruta': 'prueba.html'}, 0,
     [('OK', '2b-1', 'exencion de front'), ('OK', 'AT-3', 'N/A'), ('OK', 'AT-2', 'N/A')],
     [('HALLAZGO', None)]),
    ("Tarea de back sin Contrato: HALLAZGO (no hay exencion)",
     armar(quitar=('contrato',)), {}, 1, [('HALLAZGO', '2b-1', 'Contrato')], []),
    ("Tarea de solo UI sin el bloque del medio: N/A",
     armar({'alcance': ALCANCE_FRONT, 'subtareas': '<ol><li>Agregar la columna.</li></ol>',
            'definicion': '<ul><li>La columna se ve.</li></ul>',
            'material': '<ul><li>Regla: RN-PRU-01.</li></ul>'}, quitar=UI_SIN),
     {'historia': None}, 0, [('OK', '2b-1', 'N/A'), ('OK', '2b-5/AT-5', 'N/A')],
     [('HALLAZGO', None), ('NO_AUDITABLE', None)]),
    ("Capa desconocida sin el bloque del medio: NO se exime como UI (se audita entera y avisa la capa)",
     armar({'alcance': '<ul><li><b>Componente / repo:</b> a definir</li><li><b>Capa:</b> a definir</li></ul>',
            'subtareas': '<ol><li>Hacer el cambio.</li></ol>',
            'definicion': '<ul><li>Queda hecho.</li></ul>',
            'material': '<ul><li>Regla: RN-PRU-01.</li></ul>'}, quitar=UI_SIN),
     {'historia': None, 'ruta': 'prueba.html'}, 1, [('HALLAZGO', '2b-1'), ('AVISO', 'capa', 'Front:')],
     [('OK', '2b-1')]),
    ("Tarea de back que nombra la pantalla en 'Fuera de alcance': sigue siendo de back (sin exencion de front)",
     armar({'alcance': '<ul><li><b>Componente / repo:</b> servicio-reservas</li><li><b>Capa afectada:</b> '
                       '<code>domain</code></li><li><b>Fuera de alcance:</b> la pantalla y la vista del listado '
                       '(Tarea aparte)</li></ul>'}, quitar=FRONT_SIN),
     {'historia': None, 'ruta': 'prueba.html'}, 1, [('HALLAZGO', '2b-1', 'Contrato')], [('OK', '2b-1')]),
    ("Una etiqueta 'Reporte:' no cuenta como el renglon del repo (no la vuelve de back)",
     armar(dict(FRONT, alcance='<ul><li><b>Componente / repo:</b> portal-web</li><li><b>Capa afectada:</b> '
                                'vista del listado</li><li><b>Reporte:</b> el del backoffice</li></ul>'),
           quitar=FRONT_SIN),
     {'ruta': 'prueba.html'}, 0, [('OK', '2b-1', 'exencion de front')], [('HALLAZGO', None)]),
    ("Tarea de back que dice 'front' en 'Fuera de alcance': el renglon del repo tampoco la vuelve de front",
     armar({'alcance': '<ul><li><b>Componente / repo:</b> servicio-reservas</li><li><b>Capa afectada:</b> '
                       '<code>domain</code></li><li><b>Fuera de alcance:</b> la pantalla (la hace la Tarea de '
                       'front)</li></ul>'}, quitar=FRONT_SIN),
     {'historia': None, 'ruta': 'prueba.html'}, 1, [('HALLAZGO', '2b-1', 'Contrato')], [('OK', '2b-1')]),

    # 2b-2 / AT-4a
    ("Regla citada que no existe en el Cerebro: NO AUDITABLE",
     armar({'objetivo': '<p>Alta <i>[RN-PRU-01]</i> <i>[RN-PRU-77]</i>.</p>'}), {}, 1,
     [('NO_AUDITABLE', '2b-2/AT-4a', 'RN-PRU-77')], []),
    ("Regla citada solo en Material de apoyo: sobra",
     armar({'material': '<ul><li>Reglas: RN-PRU-01, RN-PRU-02 y RN-PRU-03.</li></ul>'}),
     {'indice': dict(INDICE, **{'RN-PRU-03': 'x.md'})}, 1,
     [('HALLAZGO', '2b-2/AT-4a', 'RN-PRU-03')], []),

    # 2b-3
    ("Mencion a otra Tarea sin #ID",
     armar({'dependencias': '<ul><li><b>De esto depende:</b> la Tarea de front (Related).</li>'
                            '</ul>'}), {}, 1, [('HALLAZGO', '2b-3')], []),
    ("Mencion a otra Tarea con su marca [T-02] de lote: vale como #ID",
     armar({'dependencias': '<ul><li><b>De esto depende:</b> la Tarea de front [T-02].</li></ul>'}),
     {}, 0, [('OK', '2b-3'), ('AVISO', '2b-3', 'borrador de lote')], [('HALLAZGO', None)]),

    # 2b-4 / AT-15
    ("Test huerfano: ni en la tabla, ni en 'no mapean', ni guardarrail",
     armar({'tests': lista_tests(TESTS + ['Fecha 2026-10-02 ' + F + ' 201'])}), {}, 1,
     [('HALLAZGO', '2b-4/AT-15', 'huerfanos')], []),
    ("Test declarado en la frase 'no mapean': no es huerfano",
     armar({'tests': lista_tests(TESTS + ['Fecha 2026-10-02 ' + F + ' 201']),
            'especificacion': sdd(extra='<p>El test 5 no mapea a un Escenario.</p>')}), {}, 0,
     [('OK', '2b-4/AT-15')], [('HALLAZGO', None)]),
    ("La tabla nombra un test que no existe",
     armar({'especificacion': sdd([('Alta de una reserva', 'Todo el escenario', '1, 2'),
                                   ('Reserva repetida', 'Todo el escenario', '3, 4, 9')])}), {}, 1,
     [('HALLAZGO', '2b-4/AT-15', 'no existen')], []),
    ("Tests con vinetas (<ul>) en vez de <ol>",
     armar({'tests': '<ul>' + ''.join('<li>%s</li>' % t for t in TESTS) + '</ul>'}), {}, 1,
     [('HALLAZGO', '2b-4/AT-15', 'vinetas')], []),

    # 2b-5 / AT-5
    ("Linea 'No cubre' con dos titulos: cuentan para el total",
     armar({'especificacion': sdd(no_cubre='<p><b>No cubre:</b> Aviso en pantalla (#100002) ' +
                                  PUNTO + ' Aviso por mail ([T-03])</p>')}),
     {'historia': gherkin(['Alta de una reserva', 'Reserva repetida', 'Aviso en pantalla',
                           'Aviso por mail'])}, 0,
     [('OK', '2b-5/AT-5', '4 = 2 filas + 2')], [('HALLAZGO', None)]),
    ("Falta un Escenario del padre (ni fila ni No cubre)",
     armar(), {'historia': gherkin(['Alta de una reserva', 'Reserva repetida',
                                    'Aviso en pantalla', 'Cancelar una reserva'])}, 1,
     [('HALLAZGO', '2b-5/AT-5', 'Cancelar una reserva')], []),
    ("Titulo de fila que no es textual (difiere en una tilde)",
     armar({'especificacion': sdd([('Alta de una reserva', 'Todo el escenario', '1, 2'),
                                   ('Reserva repetid' + A, 'Todo el escenario', '3, 4')])}),
     {}, 1, [('HALLAZGO', '2b-5/AT-5', 'tildes')], []),
    ("Titulo de fila que no esta en el padre",
     armar({'especificacion': sdd([('Alta de una reserva', 'Todo el escenario', '1, 2'),
                                   ('Reserva duplicada', 'Todo el escenario', '3, 4')])}),
     {}, 1, [('HALLAZGO', '2b-5/AT-5', 'no coincide'),
             ('HALLAZGO', '2b-5/AT-5', 'Reserva repetida')], []),
    ("Forma vieja: fila 'No lo cubre esta Tarea' en vez de la linea: AVISO",
     armar({'especificacion': sdd(FILAS + [('Aviso en pantalla',
                                            'No lo cubre esta Tarea: es de #100002', '-')],
                                  no_cubre='')}), {}, 0,
     [('AVISO', '2b-5/AT-5', 'forma vieja'), ('OK', '2b-5/AT-5')], [('HALLAZGO', None)]),
    ("Fila que cubre una parte y no nombra la otra Tarea",
     armar({'especificacion': sdd([('Alta de una reserva', 'Todo el escenario', '1, 2'),
                                   ('Reserva repetida', 'El lado servidor; la otra mitad la '
                                    'pinta el front', '3, 4')])}), {}, 1,
     [('HALLAZGO', '2b-5/AT-5', 'otra Tarea')], []),
    ("Fila sin tests que no es 'no lo cubre'",
     armar({'especificacion': sdd([('Alta de una reserva', 'Todo el escenario', '1, 2, 3, 4'),
                                   ('Reserva repetida', 'Todo el escenario', '-')])}), {}, 1,
     [('HALLAZGO', '2b-5/AT-5', 'no tiene tests')], []),

    # 2b-6 / AT-15
    ("Requiere integracion 'si' sin subtarea ni item de DoD",
     armar({'alcance': ALCANCE_BACK.replace('</b> no<', '</b> s' + I + '<'),
            'tests': lista_tests(TESTS + ['Integraci' + O + 'n: contra la base real ' + F +
                                          ' 201']),
            'especificacion': sdd(extra='<p>El test 5 no mapea a un Escenario.</p>')}), {}, 1,
     [('HALLAZGO', '2b-6/AT-15', 'subtarea'), ('HALLAZGO', '2b-6/AT-15', 'Definicion')], []),
    ("Requiere integracion 'si' con test, subtarea e item de DoD",
     armar({'alcance': ALCANCE_BACK.replace('</b> no<', '</b> s' + I + '<'),
            'tests': lista_tests(TESTS + ['Integraci' + O + 'n: contra la base real ' + F +
                                          ' 201']),
            'especificacion': sdd(extra='<p>El test 5 no mapea a un Escenario.</p>'),
            'subtareas': '<ol><li>Escribir el test de integraci' + O + 'n.</li></ol>',
            'definicion': '<ul><li>El test de integraci' + O + 'n pasa.</li></ul>'}), {}, 0,
     [('OK', '2b-6/AT-15')], [('HALLAZGO', None)]),
    ("Requiere integracion 'no' y un test etiquetado Integracion",
     armar({'tests': lista_tests(TESTS + ['Integraci' + O + 'n: contra la base real ' + F +
                                          ' 201']),
            'especificacion': sdd(extra='<p>El test 5 no mapea a un Escenario.</p>')}), {}, 1,
     [('HALLAZGO', '2b-6/AT-15', 'no')], []),

    # 2b-7, 2b-9, 2b-10
    ("Ruta de un documento fuera de un <a href>",
     armar({'resultado': '<p>Ver <code>docs/ARQUITECTURA.md</code>.</p>'}), {}, 1,
     [('HALLAZGO', '2b-7', 'docs/ARQUITECTURA.md')], []),
    ("Markdown crudo (**) en el html",
     armar({'resultado': '<p>MR **mergeado** en develop.</p>'}), {}, 1,
     [('HALLAZGO', '2b-9', '**')], []),
    ("'<' sin escapar adentro del <pre>",
     armar({'contrato': CONTRATO.replace('/api/reservas:', '/api/<recurso>:')}), {}, 1,
     [('HALLAZGO', '2b-9', '<pre>')], []),
    ("Un email de un dominio de ejemplo: AVISO de PHI, no HALLAZGO",
     armar({'resultado': '<p>Avisar a alguien@example.com.</p>'}), {}, 0,
     [('AVISO', '2b-10', 'email')], [('HALLAZGO', None)]),
    ("Un email de un dominio real: HALLAZGO de PHI (inequivoco)",
     armar({'resultado': '<p>Avisar a juan.perez@acme.com.ar.</p>'}), {}, 1,
     [('HALLAZGO', '2b-10', 'email')], []),
    ("Un CUIT de persona con el verificador valido: HALLAZGO de PHI (inequivoco)",
     armar({'resultado': '<p>Facturar al CUIT 20-12345678-6.</p>'}), {}, 1,
     [('HALLAZGO', '2b-10', 'CUIT')], []),
    ("Un CUIT de persona con el verificador mal: AVISO, no frena",
     armar({'resultado': '<p>Facturar al CUIT 20-12345678-3.</p>'}), {}, 0,
     [('AVISO', '2b-10', 'CUIT')], [('HALLAZGO', None)]),
    ("Un CUIT de empresa: AVISO, no frena",
     armar({'resultado': '<p>Facturar al CUIT 30-71234567-8.</p>'}), {}, 0,
     [('AVISO', '2b-10', 'CUIT')], [('HALLAZGO', None)]),
    ("Un email dentro de un enlace mailto: HALLAZGO",
     armar({'resultado': '<p>Escribirle a <a href="mailto:ana@acme.com">Ana</a>.</p>'}), {}, 1,
     [('HALLAZGO', '2b-10', 'email')], []),
    ("Una imagen @2x y un framework .js no son emails: no frenan",
     armar({'resultado': '<p>Se usa logo@2x.png y foo@next.js.</p>'}), {}, 0,
     [], [('HALLAZGO', None)]),
    ("Un email de un dominio de Paraguay (.com.py): HALLAZGO, no es una extension de archivo",
     armar({'resultado': '<p>Contacto: juan@empresa.com.py.</p>'}), {}, 1,
     [('HALLAZGO', '2b-10', 'email')], []),
    ("Un email seguido de dos puntos: HALLAZGO",
     armar({'resultado': '<p>Escribile a juan@gmail.com: ya sabe.</p>'}), {}, 1,
     [('HALLAZGO', '2b-10', 'email')], []),
    ("Un CUIT sin guiones: AVISO (puede ser una fecha u otro numero), no frena",
     armar({'resultado': '<p>Referencia 20123456786.</p>'}), {}, 0,
     [('AVISO', '2b-10', 'CUIT')], [('HALLAZGO', None)]),
    ("Versiones de paquete y remotos de git no son emails: no frenan",
     armar({'resultado': '<p>Se fija react@18.3.1 y @tiberriver256/mcp-server-azure-devops@0.1.54; remoto git@github.com:org/x.git y https://org@dev.azure.com/x.</p>'}), {}, 0,
     [], [('HALLAZGO', None)]),
    ("Un DNI con puntos y un telefono: AVISO (ambiguo), no frenan; un rango de anios no se marca",
     armar({'resultado': '<p>DNI 12.345.678, tel 4555-1234, vigencia 2024-2025.</p>'}), {}, 0,
     [('AVISO', '2b-10', 'DNI'), ('AVISO', '2b-10', 'telefono')], [('HALLAZGO', None)]),

    # 2b-11 / AT-8
    ("Guardarrail sin la frase 'se pone en rojo si'",
     armar({'tests': lista_tests(TESTS + ['<b>Guardarra' + I + 'l (nace verde):</b> la constante '
                                          'de estados tiene dos valores ' + F + ' pasa']),
            'definicion': '<ul><li>Los tests 1 a 4 tienen su rojo. El test 5 es guardarra' + I +
                          'l.</li></ul>'}), {}, 1,
     [('HALLAZGO', '2b-11/AT-8', 'se pone en rojo si')], []),
    ("Guardarrail bien escrito pero el DoD no lo exceptua",
     armar({'tests': lista_tests(TESTS + ['<b>Guardarra' + I + 'l (nace verde):</b> la constante '
                                          'de estados tiene dos valores ' + F + ' pasa. <b>Se pone '
                                          'en rojo si</b> alguien agrega un estado'])}), {}, 1,
     [('HALLAZGO', '2b-11/AT-8', 'Definicion de terminado')], []),

    # AT-11, AT-14
    ("Modos de falla sin la familia idempotencia",
     armar({'modos': modos(MODOS[:5])}), {}, 1, [('HALLAZGO', 'AT-11', 'idempotencia')], []),
    ("Sin la seccion Modos de falla",
     armar(quitar=('modos',)), {}, 1, [('HALLAZGO', 'AT-11', 'falta la seccion')], []),
    ("Datos a confirmar vacia (sin 'Ninguno.')",
     armar({'datos': '<ul></ul>'}), {}, 1, [('HALLAZGO', 'AT-14', 'vacia')], []),
    ("Pendiente que bloquea el test 3 y el test no trae la marca",
     armar({'datos': '<ul><li>El codigo del repetido (P-001). Bloquea el test 3.</li></ul>'}),
     {}, 1, [('HALLAZGO', 'AT-14', '3')], []),
    ("Pendiente que bloquea el test 3 y el test trae la marca",
     armar({'datos': '<ul><li>El codigo del repetido (P-001). Bloquea el test 3.</li></ul>',
            'tests': lista_tests(TESTS[:2] + [W + ' (P-001) ' + TESTS[2]] + TESTS[3:])}), {}, 0,
     [('OK', 'AT-14')], [('HALLAZGO', None)]),

    # AT-3, AT-2
    ("Codigo del contrato sin test (404)",
     armar({'contrato': CONTRATO.replace("        '409'", "        '404': { description: NO }\n"
                                                         "        '409'")}), {}, 1,
     [('HALLAZGO', 'AT-3', '404')], []),
    ("Valor de enum que ningun test nombra",
     armar({'contrato': CONTRATO.replace('CONFIRMADA]', 'CONFIRMADA, ANULADA]')}), {}, 1,
     [('HALLAZGO', 'AT-3', 'ANULADA')], []),
    ("Valor de enum sin test que el contrato marca como de otra Tarea: AVISO",
     armar({'contrato': CONTRATO.replace('CONFIRMADA] }', 'CONFIRMADA, ANULADA] }   # de #100009')}),
     {}, 0, [('AVISO', 'AT-3', 'ANULADA')], [('HALLAZGO', None)]),
    ("Fila de Casos de error cuyo codigo de error ningun test tiene",
     armar({'casos': CASOS.replace('</table>', '<tr><td>sin cupo</td><td>409</td><td>{ "error": '
                                               '"SIN_CUPO" }</td><td>-</td></tr></table>')}), {}, 1,
     [('HALLAZGO', 'AT-2', 'SIN_CUPO')], []),

    # ESQ
    ("Esquema con una sola fila",
     armar({'tests': lista_tests([TESTS[0], 'Esquema ' + RAYA + ' estado:<ul><li>PENDIENTE ' + F +
                                  ' CONFIRMADA</li></ul>'] + TESTS[2:])}), {}, 1,
     [('HALLAZGO', 'ESQ', '1 fila')], []),
    ("Esquema con una fila sin flecha",
     armar({'tests': lista_tests([TESTS[0], 'Esquema ' + RAYA + ' estado:<ul><li>PENDIENTE ' + F +
                                  ' CONFIRMADA</li><li>sin estado da error</li></ul>'] +
                                 TESTS[2:])}), {}, 1,
     [('HALLAZGO', 'ESQ', 'sin flecha')], []),
    ("Esquema viejo, con las filas en el renglon: AVISO formato viejo",
     armar({'tests': lista_tests([TESTS[0], 'Esquema, dos casos: reserva PENDIENTE ' + F +
                                  ' CONFIRMADA; reserva sin estado ' + F + ' 409'] + TESTS[2:])}),
     {}, 0, [('AVISO', 'ESQ', 'formato viejo')], [('HALLAZGO', None)]),
    ("Esquema viejo sin ninguna flecha",
     armar({'tests': lista_tests([TESTS[0], 'Esquema, dos casos: PENDIENTE y sin estado'] +
                                 TESTS[2:])}), {}, 1, [('HALLAZGO', 'ESQ', 'sin filas')], []),

    # AT-7, TAM
    ("Un item con ' o ' entre dos condiciones: AVISO",
     armar({'tests': lista_tests(TESTS[:3] + ['Invariante: reserva CONFIRMADA o ANULADA ' + F +
                                              ' 409 <i>[RN-PRU-02]</i>'])}), {}, 0,
     [('AVISO', 'AT-7', 'test 4')], [('HALLAZGO', None)]),
    ("Mas de 30 tests: AVISO de tamano, no cambia el veredicto",
     armar({'tests': lista_tests(TESTS + ['Fecha 2026-11-%02d %s 201' % (k, F)
                                          for k in range(1, 28)]),
            'especificacion': sdd(extra='<p>Los tests 5 a 31 no mapean a un Escenario.</p>')}),
     {}, 0, [('AVISO', 'TAM', '31 tests')], [('HALLAZGO', None)]),
]


def correr_casos():
    malos = 0
    for nombre, html, kw, esperado, debe, no_debe in CASOS:
        r = correr(html, **kw)
        problemas = []
        if r.codigo() != esperado:
            problemas.append('codigo %d (se esperaba %d)' % (r.codigo(), esperado))
        for x in debe:
            if not tiene(r, *x):
                problemas.append('falta %s' % (x,))
        for nivel, chequeo in no_debe:
            if any(n == nivel and (chequeo is None or c == chequeo) for n, c, _, _ in r.renglones):
                problemas.append('sobra %s %s: %s' % (nivel, chequeo or '', '; '.join(
                    '[%s] %s' % (c, d) for n, c, d, _ in r.renglones if n == nivel)[:300]))
        ok = not problemas
        malos += not ok
        print(('  OK     ' if ok else '  FALLA  ') + nombre +
              ('' if ok else '  -- ' + ' | '.join(problemas)))
    return malos, len(CASOS)


def correr_extra():
    """Piezas del parser y la linea de comandos."""
    casos = []

    def chequeo(nombre, obtenido, esperado):
        casos.append((nombre, obtenido == esperado, obtenido, esperado))

    chequeo('numeros de celda: "13 a 19, 41, 42"', tarea.numeros('13 a 19, 41, 42'),
            list(range(13, 20)) + [41, 42])
    chequeo('numeros de celda: guion y "#ID" no cuentan', tarea.numeros('-, #125232'), [])
    chequeo('tests de OTRA Tarea no cuentan ("el test 1 de #125231")',
            tarea.tests_mencionados('Ajustar el test 1 de #125231 y los tests 3 y 4'), [3, 4])
    chequeo('tests mencionados con rango "19 a 21"',
            tarea.tests_mencionados('Bloquea los tests 19 a 21.'), [19, 20, 21])
    chequeo('enum en varias lineas, con comentario',
            tarea.valores_enum('enum: [A, B,   # nuevos\n       C]'), ['A', 'B', 'C'])
    chequeo('codigos de respuesta con y sin comillas',
            tarea.codigos_respuesta("responses:\n  '200': { description: x }\n  404: x"),
            ['200', '404'])
    d = tarea.parsear(armar({'especificacion': sdd(no_cubre='<p><b>No cubre:</b> Aviso en '
                                                            'pantalla (#100002)</p>')}))
    chequeo('#ID de una celda no se pega a la celda de al lado', '1000021' in d['ids_citados'],
            False)
    chequeo('numeracion implicita del <ol>', [t['n'] for t in d['tests']], [1, 2, 3, 4])
    chequeo('el Esquema trae sus filas del <ul>', d['tests'][1]['filas'][:1],
            ['reserva PENDIENTE ' + F + ' CONFIRMADA'])
    chequeo('capa detectada en el Alcance', d['capa'], 'back')
    chequeo('la linea No cubre', [x['titulo'] for x in d['no_cubre']], ['Aviso en pantalla'])
    chequeo('el prefijo "Front:" del titulo manda sobre el Alcance',
            tarea.parsear(armar(), titulo='Front: alta de reservas')['capa_alcance'], 'front')
    chequeo('sin SDD ni tests y sin ser de back, la capa es "ui"',
            tarea.parsear(armar({'alcance': ALCANCE_FRONT}, quitar=UI_SIN))['capa'], 'ui')

    # Linea de comandos. El indice de reglas es el falso: las RN-PRU no existen en el Cerebro.
    guardado_indice = at.cerebro.indice_reglas
    at.cerebro.indice_reglas = lambda *a: dict(INDICE)
    try:
        correr_main(chequeo)
    finally:
        at.cerebro.indice_reglas = guardado_indice

    malos = 0
    for nombre, ok, obtenido, esperado in casos:
        malos += not ok
        print(('  OK     ' if ok else '  FALLA  ') + nombre +
              ('' if ok else '  -- obtuve %r, se esperaba %r' % (obtenido, esperado)))
    return malos, len(casos)


def correr_main(chequeo):
    with tempfile.TemporaryDirectory() as tmp:
        t = os.path.join(tmp, 'tarea.html')
        h = os.path.join(tmp, 'H-100001-criterios.html')
        sal = os.path.join(tmp, 'reporte.json')
        with io.open(t, 'w', encoding='utf-8') as f:
            f.write(armar())
        with io.open(h, 'w', encoding='utf-8') as f:
            f.write(HIST)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codigo = at.main([t, '--historia', h, '--json', '--salida', sal])
        try:
            j = json.loads(buf.getvalue())
            claves = sorted(k for k in ('tests', 'escenarios_padre', 'filas_sdd', 'no_cubre',
                                        'largo_caracteres', 'capa') if k in j['datos'])
        except ValueError:
            j, claves = {}, []
        chequeo('main --json: sale 0 y trae los datos', (codigo, claves, j.get('datos', {}).get(
            'escenarios_padre')), (0, ['capa', 'escenarios_padre', 'filas_sdd',
                                       'largo_caracteres', 'no_cubre', 'tests'], 3))
        chequeo('main --salida: escribe el reporte', os.path.exists(sal), True)
        with contextlib.redirect_stdout(io.StringIO()):
            codigo = at.main([t, '--historia', os.path.join(tmp, 'no-existe.html')])
        chequeo('main con --historia que no existe: NO AUDITABLE (1)', codigo, 1)
        with contextlib.redirect_stdout(io.StringIO()):
            codigo = at.main([os.path.join(tmp, 'no-existe.html')])
        chequeo('main con una Tarea que no existe: SIN DATOS (2)', codigo, 2)
        guardado = at.auditar

        def explota(*a, **k):
            raise AttributeError('forma inesperada')
        at.auditar = explota
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                codigo = at.main([t])
        finally:
            at.auditar = guardado
        chequeo('error inesperado dentro del script: SIN DATOS (2), nunca 0 ni 1', codigo, 2)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    m1, n1 = correr_casos()
    m2, n2 = correr_extra()
    malos, total = m1 + m2, n1 + n2
    print()
    print(('OK -- ' if not malos else 'FALLA -- ') + str(total - malos) + ' de ' + str(total) +
          ' casos dieron lo esperado.')
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
