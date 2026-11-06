"""Lectura de una Historia de usuario: el Gherkin (Criterios de aceptacion) y los bloques de
la Descripcion, los dos en el HTML de Azure.

Formato que produce el pipeline (mapa-campos-azure): un <p> por Escenario, palabras clave en
<b>, pasos separados por <br>, reglas en <i>[RN-...]</i> al final del renglon del Escenario.
Tambien acepta el Gherkin en texto plano (una palabra clave al principio de cada renglon).

Los Ejemplos de un "Esquema del escenario" llegan de dos formas, y las dos se leen igual:
renglones "| a | b |" (texto plano) o una <table> APARTE, justo despues del <p> que termina en
"<b>Ejemplos:</b>" (asi los guarda el tablero). La tabla se pasa a renglones "| a | b |" con
las celdas separadas; si no, texto_plano pegaba las celdas y se perdia cuantas columnas habia.

escenarios() y titulos() son la interfaz que usan auditar-tarea y analizar-tareas: no cambiar
su forma. A escenarios() solo se le AGREGAN claves.
"""

import html as _html
import re
import unicodedata

from . import texto

_CLAVES = ('caracteristica', 'antecedentes', 'esquema del escenario', 'escenario', 'ejemplos',
           'dado', 'cuando', 'entonces', 'y', 'pero')
_REGLA = re.compile(r'\b(RN-[A-Z]+-\d+[A-Z]?|DEC-\d+)\b')
_TABLA = re.compile(r'<table\b[^>]*>.*?</table\s*>', re.I | re.S)
_PENDIENTE = re.compile(r'\b(P-\d{3})\b')
_CU = re.compile(r'^\W*(CU-\d+)\b')
_OKF = re.compile(r'OKF\s*:\s*([^\s)]+)')
_RUTA = re.compile(r'(?<![\w/.-])((?:[\w.-]+/)*[\w.-]+\.(?:md|html?|pdf|png|jpe?g|svg|docx|xlsx))(?![\w-])'
                   r'(#[\w.-]*)?', re.I)


def _clave(renglon):
    """(clave_normalizada, resto) si el renglon arranca con una palabra clave de Gherkin."""
    r = renglon.strip()
    rs = texto.sin_acentos(r)
    for c in _CLAVES:
        if rs.startswith(c):
            resto = r[len(c):]
            if c in ('caracteristica', 'antecedentes', 'esquema del escenario', 'escenario', 'ejemplos'):
                if resto.startswith(':'):
                    return c, resto[1:].strip()
            elif resto[:1] in (' ', ''):
                return c, resto.strip()
    return None, r


def clave(renglon):
    """Igual que _clave, publica: la usa el chequeo de formato de auditar-historia."""
    return _clave(renglon)


def _tablas_a_renglones(fragmento):
    """Cada <table> pasa a renglones '| celda | celda |', uno por fila, celdas separadas."""
    def una(m):
        filas = (texto.tablas(m.group(0)) or [[]])[0]
        partes = []
        for f in filas:
            if not f:
                continue
            celdas = [_html.escape(c.replace('\n', ' ').strip(), quote=False) for c in f]
            partes.append('| ' + ' | '.join(celdas) + ' |')
        return '<br>' + '<br>'.join(partes) + '<br>'
    return _TABLA.sub(una, fragmento or '')


def renglones(criterios_html):
    """El Gherkin como lista de renglones de texto plano, en orden (tablas como '| a | b |')."""
    if not criterios_html:
        return []
    t = texto.texto_plano(_tablas_a_renglones(criterios_html))
    return unicodedata.normalize('NFC', t).split('\n')


def escenarios(criterios_html):
    """Lista de Escenarios, en orden:

    {'titulo': str (sin las reglas del final), 'tipo': 'Escenario' | 'Esquema del escenario',
     'reglas': [codigos], 'pasos': [(clave, texto), ...], 'ejemplos': [renglones],
     'encabezado_ejemplos': str}

    'ejemplos' son las FILAS DE DATOS ('| a | b |'), sin el encabezado; el encabezado (el
    primer renglon despues de cada "Ejemplos:") va aparte en 'encabezado_ejemplos'.
    Los pasos de Antecedentes NO se cuentan dentro de ningun Escenario (van en antecedentes()).
    """
    res, actual, en_ejemplos, espera_encabezado = [], None, False, False
    for r in renglones(criterios_html):
        c, resto = _clave(r)
        if c in ('escenario', 'esquema del escenario'):
            reglas = _REGLA.findall(resto)
            titulo = re.sub(r'\s*\[?\s*(RN-[A-Z]+-\d+[A-Z]?|DEC-\d+)\s*\]?', '', resto).strip()
            titulo = re.sub(r'[\s,;]+$', '', titulo)
            actual = {'titulo': titulo,
                      'tipo': 'Escenario' if c == 'escenario' else 'Esquema del escenario',
                      'reglas': reglas, 'pasos': [], 'ejemplos': [], 'encabezado_ejemplos': ''}
            res.append(actual)
            en_ejemplos = False
        elif c in ('caracteristica', 'antecedentes'):
            actual, en_ejemplos = None, False
        elif c == 'ejemplos':
            en_ejemplos = actual is not None
            espera_encabezado = en_ejemplos
        elif actual is not None:
            if en_ejemplos:
                fila = r.strip()
                if not fila:
                    continue
                if espera_encabezado:
                    if not actual['encabezado_ejemplos']:
                        actual['encabezado_ejemplos'] = fila
                    espera_encabezado = False
                else:
                    actual['ejemplos'].append(fila)
            elif c:
                actual['pasos'].append((c, resto))
            elif actual['pasos']:
                k, t = actual['pasos'][-1]
                actual['pasos'][-1] = (k, (t + ' ' + r.strip()).strip())
    return res


def antecedentes(criterios_html):
    """Pasos del bloque Antecedentes: [(clave, texto), ...]."""
    res, dentro = [], False
    for r in renglones(criterios_html):
        c, resto = _clave(r)
        if c == 'antecedentes':
            dentro = True
        elif c in ('escenario', 'esquema del escenario', 'caracteristica'):
            dentro = False
        elif dentro and c:
            res.append((c, resto))
    return res


def titulos(criterios_html):
    return [e['titulo'] for e in escenarios(criterios_html)]


def pasos_por_tipo(pasos):
    """[(tipo, clave, texto)]: 'Y' y 'Pero' heredan el tipo (dado/cuando/entonces) del anterior."""
    res, tipo = [], 'dado'
    for c, t in pasos:
        if c in ('dado', 'cuando', 'entonces'):
            tipo = c
        res.append((tipo, c, t))
    return res


def reglas_del_escenario(esc):
    """Reglas del renglon del Escenario + las que aparezcan en sus pasos, sin repetir."""
    vistas = list(esc.get('reglas') or [])
    for _, t in esc.get('pasos') or []:
        for c in _REGLA.findall(t):
            if c not in vistas:
                vistas.append(c)
    return vistas


# ------------------------------------------------------------------------------------------
# Descripcion: bloques de la plantilla historia-de-usuario
# ------------------------------------------------------------------------------------------

# El orden importa: el primero cuya clave aparezca en el titulo gana ("Casos de uso (alcance
# de pruebas)" es casos_uso y no alcance; "Fuera de alcance" no es alcance).
_BLOQUES = (
    ('casos_uso', ('casos de uso',)),
    ('datos_estados', ('datos y estados',)),
    ('reglas', ('reglas de negocio',)),
    ('documento_fuente', ('documento fuente',)),
    ('fuera_de_alcance', ('fuera de alcance',)),
    ('dependencias', ('dependencias',)),
    ('diseno', ('diseno', 'apoyo visual')),
    ('funcionalidad', ('funcionalidad', 'historia de usuario')),
    ('contexto', ('contexto',)),
    ('alcance', ('alcance',)),
)


def _tipo_bloque(titulo):
    t = texto.sin_acentos(titulo)
    for k, claves in _BLOQUES:
        if any(c in t for c in claves):
            return k
    return None


def _secciones_texto(doc):
    """Sin <h3>: titulos como renglones sueltos ('### Datos y estados', '<b>Reglas...</b>')."""
    res, titulo, cuerpo = [], '', []
    for r in texto.texto_plano(doc).split('\n'):
        limpio = r.strip().lstrip('#*').strip().rstrip(':*').strip()
        if limpio and len(limpio) < 70 and ':' not in limpio and _tipo_bloque(limpio) and \
                texto.sin_acentos(limpio).startswith(tuple(c for _, cs in _BLOQUES for c in cs)):
            res.append((titulo, '<br>'.join(cuerpo)))
            titulo, cuerpo = limpio, []
        else:
            cuerpo.append(_html.escape(r, quote=False))
    res.append((titulo, '<br>'.join(cuerpo)))
    return [(t, c) for t, c in res if t or c.strip()]


def bloques_descripcion(descripcion_html):
    """{clave: html_del_bloque} de los bloques reconocidos de la Descripcion.

    Claves posibles: funcionalidad, contexto, alcance, fuera_de_alcance, datos_estados, reglas,
    casos_uso, dependencias, documento_fuente, diseno. Un bloque que no esta NO aparece (asi
    quien llama distingue ausente de vacio). Si dos secciones caen en la misma clave, se juntan.
    """
    secs = texto.secciones(descripcion_html or '')
    if len(secs) == 1 and secs[0][0] == '':
        secs = _secciones_texto(descripcion_html or '')
    res = {}
    for titulo, cuerpo in secs:
        k = _tipo_bloque(titulo) if titulo else None
        if k:
            res[k] = (res[k] + '<br>' + cuerpo) if k in res else cuerpo
    return res


def _items(bloque_html):
    """Renglones de un bloque: un item por <li> de primer nivel, o un renglon por linea."""
    ls = texto.listas(bloque_html)
    if ls:
        return [texto.normalizado(li) for _, items in ls for li in items if texto.normalizado(li)]
    return [r for r in texto.texto_plano(bloque_html).split('\n') if r.strip()]


def casos_de_uso(descripcion_html):
    """[{'codigo': 'CU-nn' | '', 'texto': str, 'reglas': [codigos]}] del bloque Casos de uso,
    o None si el bloque no esta. Un renglon que no arranca con CU-nn se suma al anterior."""
    b = bloques_descripcion(descripcion_html).get('casos_uso')
    if b is None:
        return None
    res = []
    for it in _items(b):
        m = _CU.match(it)
        if m or not res:
            res.append({'codigo': m.group(1) if m else '', 'texto': it, 'reglas': []})
        else:
            res[-1]['texto'] += ' ' + it
        for c in _REGLA.findall(it):
            if c not in res[-1]['reglas']:
                res[-1]['reglas'].append(c)
    return res


def datos_y_estados(descripcion_html):
    """[{'texto': str, 'reglas': [codigos]}] del bloque Datos y estados, o None si no esta."""
    b = bloques_descripcion(descripcion_html).get('datos_estados')
    if b is None:
        return None
    return [{'texto': it, 'reglas': _sin_repetir(_REGLA.findall(it))} for it in _items(b)]


def reglas_de_negocio(descripcion_html):
    """[{'codigo': str, 'citadas': [codigos], 'okf': ruta | ''}] del bloque Reglas de negocio,
    o None si no esta. 'codigo' es la primera regla del renglon (la que el renglon define)."""
    b = bloques_descripcion(descripcion_html).get('reglas')
    if b is None:
        return None
    res = []
    for it in _items(b):
        cs = _sin_repetir(_REGLA.findall(it))
        m = _OKF.search(it)
        res.append({'codigo': cs[0] if cs else '', 'citadas': cs,
                    'okf': m.group(1).rstrip('.,;') if m else ''})
    return res


def documento_fuente(descripcion_html):
    """Rutas del bloque Documento fuente, en orden y sin repetir (la primera es LA fuente), o
    None si el bloque no esta. Toma los href y las rutas escritas como texto; sin '#ancla'.
    Sin seccion propia, vale un renglon "Documento fuente: <ruta>" dentro de otra seccion."""
    b = bloques_descripcion(descripcion_html).get('documento_fuente')
    if b is None:
        lineas = [r for r in texto.texto_plano(descripcion_html or '').split('\n')
                  if texto.sin_acentos(r).lstrip(' -*').startswith('documento fuente')]
        if not lineas:
            return None
        b = '<br>'.join(_html.escape(r, quote=False) for r in lineas)
    rutas = []
    for href, _ in texto.enlaces(b):
        h = _html.unescape(href).strip()
        if h and h.split('#')[0] not in rutas:
            rutas.append(h.split('#')[0])
    for m in _RUTA.finditer(texto.texto_plano(texto.sin_enlaces(b))):
        if m.group(1) not in rutas:
            rutas.append(m.group(1))
    return rutas


def pendientes_citados(fragmento):
    """Codigos P-nnn mencionados en el texto, en orden y sin repetir."""
    return _sin_repetir(_PENDIENTE.findall(texto.texto_plano(fragmento or '')))


def _sin_repetir(xs):
    vistos = []
    for x in xs:
        if x not in vistos:
            vistos.append(x)
    return vistos
