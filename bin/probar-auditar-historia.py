#!/usr/bin/env python3
"""Prueba de bin/auditar-historia.py SIN RED y sin tarjetas reales.

    python bin/probar-auditar-historia.py

Sale 0 si todos los casos dan lo esperado, 1 si alguno no.

Los insumos son SINTETICOS y viven aca adentro: un Cerebro de juguete (reglas RN-PRU-..., una
ficha con su bloque de derivacion, una sin bloque, un pendientes.md) que se arma en una
carpeta temporal y se borra al terminar. Ninguna tarjeta real se copia al repo. Las formas
del HTML copian las del tablero: un <p> por Escenario, palabras clave en <b>, y los Ejemplos
de un Esquema como <table> APARTE, despues del <p> que termina en "<b>Ejemplos:</b> </p>".
"""

import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
spec = importlib.util.spec_from_file_location('ah', os.path.join(AQUI, 'auditar-historia.py'))
ah = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ah)
from auditoria import historia  # noqa: E402

A_, I_, O_, PM = chr(0xe1), chr(0xed), chr(0xf3), chr(0xb7)   # a, i, o con tilde; punto medio
SP = '&nbsp;&nbsp;'

# --- Cerebro de juguete -------------------------------------------------------------------

REGLAS_MD = ('---\nid: reglas-prueba\n---\n\n# Reglas de prueba\n\n'
             '## RN-PRU-001\nAl guardar, la programacion queda guardada.\n\n'
             '## RN-PRU-002\nLos obligatorios se validan al guardar.\n\n'
             '## RN-PRU-003\nOtra regla.\n\n## DEC-900\nUna decision.\n')
FICHA_MD = ('---\nid: ficha-prueba\ntipo: flujo-funcional\n---\n\n# Ficha de prueba\n\n'
            '## Derivaci' + O_ + 'n a backlog\n\n### Flujos [Historias]\n'
            '- [F-01] Guardar una programacion ' + PM + ' Capacidad: C-01 ' + PM +
            ' Reglas: RN-PRU-001, RN-PRU-002\n'
            '- [F-02] Otra cosa ' + PM + ' Capacidad: C-01 ' + PM + ' Reglas: RN-PRU-003\n'
            '- [F-03] Todo junto ' + PM + ' Capacidad: C-01 ' + PM +
            ' Reglas: RN-PRU-001, RN-PRU-002, RN-PRU-003\n'
            '- [F-04] Sin reglas ' + PM + ' Capacidad: C-01\n\n## Dudas y Preguntas\n- nada\n')
SIN_BLOQUE_MD = '---\nid: sin-bloque\n---\n\n# Ficha sin bloque\n\nMenciona RN-PRU-001.\n'
PENDIENTES_MD = ('---\nid: pendientes\n---\n\n# Pendientes\n\n## Abiertas\n\n'
                 '| # | Pregunta | Responsable |\n|---|---|---|\n'
                 '| P-101 | Algo sin definir | A definir |\n'
                 '| ~~P-103~~ | Tachada | A definir |\n\n'
                 '## Resueltas\n\n- **P-102** -- Resuelta el otro dia.\n')
# Una skill que nombra una regla de ejemplo: NO cuenta como regla del dominio.
SKILL_MD = '# skill\n\nEjemplo: [RN-PRU-999].\n'

ARCHIVOS = {
    'cerebro-digital/pruebas/reglas.md': REGLAS_MD,
    'cerebro-digital/pruebas/ficha-prueba.md': FICHA_MD,
    'cerebro-digital/pruebas/ficha-sin-bloque.md': SIN_BLOQUE_MD,
    'cerebro-digital/pruebas/pendientes.md': PENDIENTES_MD,
    'cerebro-digital/configuracion-ia/skills/x/SKILL.md': SKILL_MD,
    'entregables/disenos/maqueta.html': '<html><body>maqueta</body></html>\n',
}
FICHA = 'cerebro-digital/pruebas/ficha-prueba.md'

# --- Historia sana -----------------------------------------------------------------------

ESC1 = ('<p><b>Escenario:</b> Alta feliz <i>[RN-PRU-001]</i><br>'
        + SP + '<b>Cuando</b> el operador guarda<br>'
        + SP + '<b>Entonces</b> la programaci' + O_ + 'n queda guardada<br>'
        + SP + '<b>Y</b> el listado muestra 1 programaci' + O_ + 'n</p>')
TABLA = ('<table><tr><th>campo</th><th>orden</th></tr><tr><td>localidad </td><td>1</td></tr>'
         '<tr><td>provincia</td><td>2</td></tr></table>')
ESC2 = ('<p><b>Esquema del escenario:</b> Falta un obligatorio <i>[RN-PRU-002]</i><br>'
        + SP + '<b>Dado</b> que falta "&lt;campo&gt;"<br>'
        + SP + '<b>Cuando</b> el operador guarda<br>'
        + SP + '<b>Entonces</b> no se guarda<br>'
        + SP + '<b>Y</b> la pantalla avisa "falta: &lt;campo&gt;"<br>'
        + SP + '<b>Ejemplos:</b> </p>' + TABLA)
CRIT_OK = ('<p><b>Caracter' + I_ + 'stica:</b> Prueba</p>'
           '<p><b>Antecedentes:</b><br>' + SP + '<b>Dado</b> que el operador est' + A_ +
           ' en la pantalla de alta</p>' + ESC1 + ESC2)

DESC_OK = ('<h3>Funcionalidad / Historia de usuario</h3><p><b>Como</b> operador ...</p><hr>'
           '<h3>Datos y estados</h3><ul><li><b>Campo:</b> localidad (obligatorio) '
           '<i>[RN-PRU-002]</i></li></ul><hr>'
           '<h3>Reglas de negocio</h3><ul>'
           '<li><b>[RN-PRU-001]</b> Se guarda. <i>(OKF: cerebro-digital/pruebas/reglas.md#RN-PRU-001)</i></li>'
           '<li><b>[RN-PRU-002]</b> Obligatorios. <i>(OKF: cerebro-digital/pruebas/reglas.md#RN-PRU-002)</i></li>'
           '</ul><hr>'
           '<h3>Casos de uso (alcance de pruebas)</h3><ul>'
           '<li><b>CU-01</b> Alta feliz. <i>[RN-PRU-001]</i></li>'
           '<li><b>CU-02</b> Falta un obligatorio. <i>[RN-PRU-002]</i></li></ul><hr>'
           '<h3>Documento fuente</h3><p><a href="' + FICHA + '">' + FICHA +
           '</a> -- referencia, no contenido</p>')

CRIT_TEXTO = ('Caracteristica: Prueba\n'
              'Escenario: Alta feliz [RN-PRU-001]\n'
              '  Cuando el operador guarda\n'
              '  Entonces la programacion queda guardada\n'
              'Esquema del escenario: Falta un obligatorio [RN-PRU-002]\n'
              '  Cuando el operador guarda sin <campo>\n'
              '  Entonces no se guarda\n'
              '  Ejemplos:\n'
              '    | campo | orden |\n'
              '    | localidad | 1 |\n')


def sin(s, *pedazos):
    for p in pedazos:
        assert p in s, 'el fixture cambio: falta ' + p[:40]
        s = s.replace(p, '')
    return s


def cambia(s, viejo, nuevo):
    assert viejo in s, 'el fixture cambio: falta ' + viejo[:40]
    return s.replace(viejo, nuevo)


ENTONCES1 = (SP + '<b>Entonces</b> la programaci' + O_ + 'n queda guardada<br>'
             + SP + '<b>Y</b> el listado muestra 1 programaci' + O_ + 'n')

# (nombre, criterios, descripcion, ficha, flujo, esperado)
# esperado: {'codigo': n, 'hay': [(nivel, chequeo)], 'no_hay': [(nivel | None, chequeo | None)]}
CASOS = [
    ('Historia sana, con ficha y flujo: sin hallazgos ni avisos',
     CRIT_OK, DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'no_hay': [('HALLAZGO', None), ('AVISO', None), ('NO_AUDITABLE', None)]}),
    ('Sin --ficha ni --flujo: AVISO "sin ficha", no bloquea',
     CRIT_OK, DESC_OK, None, None, {'codigo': 0, 'hay': [('AVISO', 'AH-13')]}),
    ('--flujo sin --ficha: toma la ficha del Documento fuente',
     CRIT_OK, DESC_OK, None, 'F-01', {'codigo': 0, 'hay': [('OK', 'AH-13')]}),
    ('Regla del cero: 0 Escenarios es NO AUDITABLE, nunca OK',
     '<p><b>Caracter' + I_ + 'stica:</b> Prueba</p><p>texto suelto</p>', DESC_OK, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-2')], 'no_hay': [('OK', 'AH-3'), ('OK', 'AH-10')]}),
    ('Criterios vacios: 0 Escenarios, NO AUDITABLE',
     '', DESC_OK, None, None, {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-2')]}),
    ('Palabra vaga en el Entonces',
     cambia(CRIT_OK, 'queda guardada', 'se guarda correctamente'), DESC_OK, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-4')]}),
    ('Palabra vaga en un Y del Entonces ("sin errores")',
     cambia(CRIT_OK, 'el listado muestra 1', 'el listado se arma sin errores con 1'), DESC_OK,
     FICHA, 'F-01', {'codigo': 1, 'hay': [('HALLAZGO', 'AH-4')]}),
    ('"incorrecto" no cae por "correcto"',
     cambia(CRIT_OK, 'no se guarda', 'no se guarda el dato incorrecto'), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'no_hay': [('HALLAZGO', 'AH-4')]}),
    ('Escenario sin regla',
     sin(CRIT_OK, ' <i>[RN-PRU-001]</i>'), DESC_OK, None, None,
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-10')]}),
    ('Regla citada que no existe en el Cerebro: NO AUDITABLE',
     cambia(CRIT_OK, '[RN-PRU-001]</i>', '[RN-PRU-777]</i>'), DESC_OK, None, None,
     {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-10')]}),
    ('Regla que solo nombra una skill (configuracion-ia) no existe',
     cambia(CRIT_OK, '[RN-PRU-001]</i>', '[RN-PRU-999]</i>'), DESC_OK, None, None,
     {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-10')]}),
    ('Escenario sin Entonces',
     sin(CRIT_OK, '<br>' + ENTONCES1), DESC_OK, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-3')]}),
    ('Escenario sin Cuando (el Dado de los Antecedentes no alcanza)',
     cambia(CRIT_OK, SP + '<b>Cuando</b> el operador guarda<br>' + SP + '<b>Entonces</b> la',
            SP + '<b>Entonces</b> la'),
     DESC_OK, FICHA, 'F-01', {'codigo': 1, 'hay': [('HALLAZGO', 'AH-6')],
                              'no_hay': [('HALLAZGO', 'AH-3')]}),
    ('Esquema del escenario sin Ejemplos',
     sin(CRIT_OK, '<br>' + SP + '<b>Ejemplos:</b> ', TABLA), DESC_OK, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-2')]}),
    ('Esquema con Ejemplos que solo traen el encabezado',
     cambia(CRIT_OK, TABLA, '<table><tr><th>campo</th></tr></table>'), DESC_OK, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-2')]}),
    ('Titulos de Escenario repetidos (mayusculas y espacios no los salvan)',
     cambia(CRIT_OK, 'Falta un obligatorio <i>', 'Alta  Feliz <i>'), DESC_OK, None, None,
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-2')]}),
    ('Titulo que termina en punto: AVISO',
     cambia(CRIT_OK, 'Alta feliz <i>', 'Alta feliz. <i>'), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-2')]}),
    ('Palabras clave en ingles',
     CRIT_OK + '<p><b>Scenario:</b> happy path<br><b>When</b> x<br><b>Then</b> y</p>',
     DESC_OK, FICHA, 'F-01', {'codigo': 1, 'hay': [('HALLAZGO', 'AH-9')]}),
    ('Dos Cuando en un Escenario: AVISO de un comportamiento',
     cambia(CRIT_OK, SP + '<b>Entonces</b> la programaci',
            SP + '<b>Cuando</b> vuelve a guardar<br>' + SP + '<b>Entonces</b> la programaci'),
     DESC_OK, FICHA, 'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-5')]}),
    ('" o " en el Entonces: AVISO (lo de adentro de las comillas no cuenta)',
     cambia(CRIT_OK, 'queda guardada', 'queda guardada o queda en borrador'), DESC_OK, FICHA,
     'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-5')]}),
    ('" o " solo entre comillas: sin AVISO',
     cambia(CRIT_OK, 'avisa "falta: ', 'avisa "falta calle o altura: '), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'no_hay': [('AVISO', 'AH-5')]}),
    ('Cuando que esconde al actor ("se ..."): AVISO',
     cambia(CRIT_OK, '<b>Cuando</b> el operador guarda<br>' + SP + '<b>Entonces</b> la',
            '<b>Cuando</b> se guarda la programacion<br>' + SP + '<b>Entonces</b> la'),
     DESC_OK, FICHA, 'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-6')]}),
    ('Regla del flujo que ningun Escenario cita',
     CRIT_OK, DESC_OK, FICHA, 'F-03', {'codigo': 1, 'hay': [('HALLAZGO', 'AH-13')]}),
    ('Reglas citadas que no son del flujo: AVISO',
     CRIT_OK, DESC_OK, FICHA, 'F-02', {'codigo': 1, 'hay': [('AVISO', 'AH-13'), ('HALLAZGO', 'AH-13')]}),
    ('Flujo que no esta en el bloque: NO AUDITABLE',
     CRIT_OK, DESC_OK, FICHA, 'F-09', {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-13')]}),
    ('Flujo sin reglas asignadas: NO AUDITABLE (Regla del cero)',
     CRIT_OK, DESC_OK, FICHA, 'F-04', {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-13')]}),
    ('Ficha sin bloque de derivacion: NO AUDITABLE',
     CRIT_OK, DESC_OK, 'cerebro-digital/pruebas/ficha-sin-bloque.md', 'F-01',
     {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-13')]}),
    ('--ficha sin --flujo: NO AUDITABLE',
     CRIT_OK, DESC_OK, FICHA, None, {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-13')]}),
    ('Sin --descripcion: 1, 11 y 12 NO AUDITABLES',
     CRIT_OK, None, FICHA, 'F-01',
     {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-1'), ('NO_AUDITABLE', 'AH-11'),
                           ('NO_AUDITABLE', 'AH-12')]}),
    ('Documento fuente que no existe',
     CRIT_OK, DESC_OK.replace(FICHA, 'cerebro-digital/pruebas/no-existe.md'), None, None,
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-1')]}),
    ('Documento fuente que es una maqueta: AVISO "no tiene ficha", no bloquea',
     CRIT_OK, DESC_OK.replace(FICHA, 'entregables/disenos/maqueta.html'), None, None,
     {'codigo': 0, 'hay': [('AVISO', 'AH-1')]}),
    ('Sin bloque Documento fuente',
     CRIT_OK, DESC_OK.split('<h3>Documento fuente')[0], None, None,
     {'codigo': 1, 'hay': [('HALLAZGO', 'AH-1')]}),
    ('Sin bloque Casos de uso: NO AUDITABLE (ausente no es cumplido)',
     CRIT_OK, sin(DESC_OK, '<h3>Casos de uso (alcance de pruebas)</h3><ul>'
                  '<li><b>CU-01</b> Alta feliz. <i>[RN-PRU-001]</i></li>'
                  '<li><b>CU-02</b> Falta un obligatorio. <i>[RN-PRU-002]</i></li></ul><hr>'),
     FICHA, 'F-01', {'codigo': 1, 'hay': [('NO_AUDITABLE', 'AH-11')]}),
    ('CU-nn que no comparte regla con ningun Escenario: AVISO',
     CRIT_OK, cambia(DESC_OK, '</ul><hr><h3>Documento',
                     '<li><b>CU-03</b> Otra cosa. <i>[RN-PRU-003]</i></li></ul><hr><h3>Documento'),
     FICHA, 'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-11')]}),
    ('Sin bloque Datos y estados: AVISO',
     CRIT_OK, sin(DESC_OK, '<h3>Datos y estados</h3><ul><li><b>Campo:</b> localidad (obligatorio) '
                  '<i>[RN-PRU-002]</i></li></ul><hr>'), FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-12')]}),
    ('Punto abierto (P-101) en un Entonces: AVISO',
     cambia(CRIT_OK, 'queda guardada', 'queda guardada (ver P-101)'), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-19')]}),
    ('Punto resuelto (P-102) y tachado (P-103): sin AVISO',
     cambia(CRIT_OK, 'queda guardada', 'queda guardada (P-102, P-103)'), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'no_hay': [('AVISO', 'AH-19')]}),
    ('"a definir" en el texto de un Escenario: AVISO',
     cambia(CRIT_OK, 'queda guardada', 'queda guardada con un codigo a definir'), DESC_OK, FICHA,
     'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-19')]}),
    ('"presiona Confirmar" no es "a confirmar": sin AVISO',
     cambia(CRIT_OK, 'el operador guarda<br>' + SP + '<b>Entonces</b> la',
            'el operador presiona Confirmar<br>' + SP + '<b>Entonces</b> la'), DESC_OK, FICHA,
     'F-01', {'codigo': 0, 'no_hay': [('AVISO', 'AH-19')]}),
    ('Punto que no existe en pendientes (P-555) en la Descripcion: AVISO',
     CRIT_OK, cambia(DESC_OK, 'Obligatorios.', 'Obligatorios (P-555).'), FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-19')]}),
    ('Palabras clave sin negrita: AVISO de formato',
     cambia(CRIT_OK, '<b>Cuando</b> el operador guarda<br>' + SP + '<b>Entonces</b> la',
            'Cuando el operador guarda<br>' + SP + '<b>Entonces</b> la'),
     DESC_OK, FICHA, 'F-01', {'codigo': 0, 'hay': [('AVISO', 'AH-formato')]}),
    ('Dos Escenarios en un mismo <p>: AVISO de formato',
     cambia(CRIT_OK, 'n</p><p><b>Esquema', 'n<br><b>Esquema'), DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-formato')]}),
    ('Gherkin en texto plano: se lee igual, con AVISO de formato',
     CRIT_TEXTO, DESC_OK, FICHA, 'F-01',
     {'codigo': 0, 'hay': [('AVISO', 'AH-formato'), ('OK', 'AH-13')],
      'no_hay': [('HALLAZGO', None)]}),
]


def niveles(rep):
    return [(n, c) for n, c, _, _ in rep.renglones]


def cumple(rep, esperado):
    """'' si el reporte da lo esperado; si no, por que no."""
    hay = niveles(rep)
    if rep.codigo() != esperado['codigo']:
        return 'codigo %d, se esperaba %d' % (rep.codigo(), esperado['codigo'])
    for n, c in esperado.get('hay', []):
        if (n, c) not in hay:
            return 'falta un %s en %s' % (n, c)
    for n, c in esperado.get('no_hay', []):
        malos = [x for x in hay if (n is None or x[0] == n) and (c is None or x[1] == c)]
        if malos:
            return 'sobra %s' % (malos[0],)
    return ''


def escribir(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with io.open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(contenido)


def main():
    malos, total = 0, 0
    raiz = tempfile.mkdtemp(prefix='probar-auditar-historia-')
    try:
        for rel, contenido in ARCHIVOS.items():
            escribir(os.path.join(raiz, rel), contenido)

        def correr(crit, desc, ficha, flujo):
            pc = os.path.join(raiz, 'insumo', 'criterios.html')
            escribir(pc, crit)
            pd = None
            if desc is not None:
                pd = os.path.join(raiz, 'insumo', 'descripcion.html')
                escribir(pd, desc)
            return ah.auditar(pc, pd, os.path.join(raiz, ficha) if ficha else None, flujo, raiz=raiz)

        def chequeo(titulo, motivo):
            nonlocal malos, total
            total += 1
            malos += bool(motivo)
            print(('  OK     ' if not motivo else '  FALLA  ') + titulo + ('' if not motivo else
                                                                         '  -> ' + motivo))

        for nombre, crit, desc, ficha, flujo, esperado in CASOS:
            try:
                motivo = cumple(correr(crit, desc, ficha, flujo), esperado)
            except Exception as e:  # noqa: BLE001
                motivo = 'exploto: %s: %s' % (type(e).__name__, e)
            chequeo(nombre, motivo)

        # SIN DATOS: el archivo de criterios no existe.
        rep = ah.auditar(os.path.join(raiz, 'no-existe.html'), None, None, None, raiz=raiz)
        chequeo('Criterios que no existen: SIN DATOS (2)',
                '' if rep.codigo() == 2 and rep.sin_datos else 'codigo %d' % rep.codigo())

        # La <table> de Ejemplos aparte, como la guarda el tablero: filas con celdas separadas.
        e = historia.escenarios(CRIT_OK)
        obt = (e[1]['encabezado_ejemplos'], e[1]['ejemplos']) if len(e) == 2 else None
        esp = ('| campo | orden |', ['| localidad | 1 |', '| provincia | 2 |'])
        chequeo('escenarios(): Ejemplos en <table> aparte, encabezado aparte',
                '' if obt == esp else 'dio %r' % (obt,))
        e = historia.escenarios(CRIT_TEXTO)
        obt = (e[1]['encabezado_ejemplos'], e[1]['ejemplos']) if len(e) == 2 else None
        chequeo('escenarios(): Ejemplos en texto plano con barras',
                '' if obt == ('| campo | orden |', ['| localidad | 1 |']) else 'dio %r' % (obt,))
        claves = set(historia.escenarios(CRIT_OK)[0])
        chequeo('escenarios(): conserva sus claves (solo se agregan)',
                '' if {'titulo', 'tipo', 'reglas', 'pasos', 'ejemplos'} <= claves else
                'claves %s' % sorted(claves))
        chequeo('titulos(): los titulos sin las reglas',
                '' if historia.titulos(CRIT_OK) == ['Alta feliz', 'Falta un obligatorio'] else
                'dio %r' % historia.titulos(CRIT_OK))
        chequeo('antecedentes(): el Dado comun, fuera de los Escenarios',
                '' if [c for c, _ in historia.antecedentes(CRIT_OK)] == ['dado'] else 'otro')
        cus = historia.casos_de_uso(DESC_OK)
        chequeo('casos_de_uso(): codigo y reglas de cada CU',
                '' if [(c['codigo'], c['reglas']) for c in cus] ==
                [('CU-01', ['RN-PRU-001']), ('CU-02', ['RN-PRU-002'])] else 'dio %r' % cus)
        chequeo('documento_fuente(): la ruta, sin repetir href y texto',
                '' if historia.documento_fuente(DESC_OK) == [FICHA] else
                'dio %r' % historia.documento_fuente(DESC_OK))
        inline = DESC_OK.split('<h3>Documento fuente')[0] + (
            '<h3>Dependencias</h3><ul><li><b>Documento fuente:</b> ' + FICHA + '#F-01</li></ul>')
        chequeo('documento_fuente(): renglon "Documento fuente:" dentro de otra seccion',
                '' if historia.documento_fuente(inline) == [FICHA] else
                'dio %r' % historia.documento_fuente(inline))
        chequeo('bloques: Descripcion en markdown, sin <h3>',
                '' if historia.casos_de_uso('### Casos de uso\n- CU-01 algo [RN-PRU-001]\n') ==
                [{'codigo': 'CU-01', 'texto': '- CU-01 algo [RN-PRU-001]', 'reglas': ['RN-PRU-001']}]
                else 'dio %r' % historia.casos_de_uso('### Casos de uso\n- CU-01 algo [RN-PRU-001]\n'))

        # La CLI de punta a punta, contra el Cerebro de juguete: codigos 0 y 1, --json y --salida.
        guardado = ah.cerebro.raiz_repo
        ah.cerebro.raiz_repo = lambda: raiz
        stdout = sys.stdout
        try:
            pc = os.path.join(raiz, 'insumo', 'cli-criterios.html')
            pd = os.path.join(raiz, 'insumo', 'cli-descripcion.html')
            ps = os.path.join(raiz, 'insumo', 'reporte.json')
            escribir(pc, CRIT_OK)
            escribir(pd, DESC_OK)
            sys.stdout = io.StringIO()
            cod = ah.main(['--criterios', pc, '--descripcion', pd, '--ficha', FICHA,
                           '--flujo', 'F-01', '--json', '--salida', ps])
            impreso = sys.stdout.getvalue()
            escribir(pc, '<p>sin gherkin</p>')
            sys.stdout = io.StringIO()
            cod_cero = ah.main(['--criterios', pc])
        finally:
            sys.stdout = stdout
            ah.cerebro.raiz_repo = guardado
        try:
            d = json.loads(impreso)
            with io.open(ps, encoding='utf-8') as f:
                guardado_json = json.load(f)
            motivo = '' if (cod == 0 and d['codigo'] == 0 and guardado_json == d and
                            d['datos']['escenarios'] == 2 and d['datos']['esquemas'] == 1 and
                            d['datos']['antecedentes'] == 1 and d['datos']['flujo'] == 'F-01' and
                            d['datos']['reglas_citadas'] == ['RN-PRU-001', 'RN-PRU-002'] and
                            d['para_el_auditor']) else 'codigo %d, datos %r' % (cod, d.get('datos'))
        except (ValueError, OSError, KeyError) as e:
            motivo = 'json: %s' % e
        chequeo('CLI: Historia sana sale 0, --json parseable y --salida igual a lo impreso', motivo)
        chequeo('CLI: 0 Escenarios sale 1', '' if cod_cero == 1 else 'salio %d' % cod_cero)
    finally:
        shutil.rmtree(raiz, ignore_errors=True)

    print()
    print(('OK -- ' if not malos else 'FALLA -- ') + str(total - malos) + ' de ' + str(total) +
          ' casos dieron lo esperado.')
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
