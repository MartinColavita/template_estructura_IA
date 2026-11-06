"""Utilidades de texto y HTML para las auditorias mecanicas. Solo biblioteca estandar.

El HTML de Azure es simple (h3, p, ul/ol/li, table, pre, b, i, a, br, hr), asi que se
recorre con expresiones regulares sobre las etiquetas, sin armar un arbol completo. Lo que
importa es que el recorte sea SIEMPRE el mismo para el mismo texto.
"""

import html as _html
import io
import re
import unicodedata

_BLOQUE = re.compile(r'<\s*(br|/p|/li|/tr|/h[1-6]|/pre|/div|hr|/ul|/ol|/table)\b[^>]*>', re.I)
_ETIQUETA = re.compile(r'<[^>]+>')
_FIN_CELDA = re.compile(r'</t[hd]\s*>', re.I)
_NBSP = chr(0xa0)   # espacio duro de Azure; asi el .py queda ASCII
_ESPACIOS = re.compile('[ ' + chr(9) + chr(13) + chr(12) + chr(11) + _NBSP + ']+')


def leer(ruta):
    """Lee un archivo UTF-8 (con o sin BOM). Lanza OSError / UnicodeDecodeError si no puede."""
    with io.open(ruta, encoding='utf-8-sig') as f:
        return f.read()


def sin_acentos(s):
    """Minusculas y sin tildes, para comparar textos en castellano sin depender del acento."""
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def texto_plano(fragmento):
    """HTML -> texto legible: un renglon por bloque, sin etiquetas, entidades resueltas."""
    t = _BLOQUE.sub('\n', fragmento or '')
    t = _FIN_CELDA.sub(' ', t)   # sin esto, '#125274</td><td>1, 2' quedaba '#1252741, 2'
    t = _ETIQUETA.sub('', t)
    t = _html.unescape(t)
    renglones = [_ESPACIOS.sub(' ', r).strip() for r in t.split('\n')]
    return '\n'.join(r for r in renglones if r)


def normalizado(fragmento):
    """Texto plano en una sola linea: para comparar dos versiones del mismo contenido.

    Azure reescribe el HTML al guardarlo (agrega espacios, cambia comillas por entidades), asi
    que dos tarjetas iguales se comparan SIN etiquetas y con los espacios normalizados.
    """
    return _ESPACIOS.sub(' ', texto_plano(fragmento).replace('\n', ' ')).strip()


def iguales(a, b):
    return normalizado(a) == normalizado(b)


def primera_diferencia(a, b, contexto=60):
    """(posicion, recorte_a, recorte_b) de la primera diferencia, o None si son iguales."""
    na, nb = normalizado(a), normalizado(b)
    if na == nb:
        return None
    n = min(len(na), len(nb))
    k = next((i for i in range(n) if na[i] != nb[i]), n)
    return k, na[max(0, k - contexto):k + contexto], nb[max(0, k - contexto):k + contexto]


_H3 = re.compile(r'<h3\b[^>]*>(.*?)</h3\s*>', re.I | re.S)


def secciones(doc):
    """Lista ordenada de (titulo, cuerpo_html) partiendo por <h3>.

    Lo que hay antes del primer <h3> va con titulo ''. El titulo es texto plano.
    """
    res = []
    marcas = list(_H3.finditer(doc or ''))
    if not marcas:
        return [('', doc or '')]
    if marcas[0].start() > 0 and (doc[:marcas[0].start()]).strip():
        res.append(('', doc[:marcas[0].start()]))
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(doc)
        res.append((texto_plano(m.group(1)), doc[m.end():fin]))
    return res


def seccion(doc, *claves):
    """Cuerpo de la primera seccion cuyo titulo (sin acentos) contiene alguna clave. O None."""
    claves = [sin_acentos(c) for c in claves]
    for titulo, cuerpo in secciones(doc):
        t = sin_acentos(titulo)
        if any(c in t for c in claves):
            return cuerpo
    return None


_TAG_LISTA = re.compile(r'<(/?)(ol|ul|li)\b[^>]*>', re.I)


def listas(fragmento):
    """Listas de PRIMER nivel del fragmento: [(tag, [html_de_cada_li, ...]), ...].

    El html de cada <li> incluye sus listas anidadas (asi un Esquema trae sus filas adentro).
    Tolera un </li> que falta.
    """
    res, pila = [], []
    s = fragmento or ''
    for m in _TAG_LISTA.finditer(s):
        cierre, tag = m.group(1) == '/', m.group(2).lower()
        if tag in ('ol', 'ul'):
            if not cierre:
                pila.append({'tag': tag, 'items': [], 'li': None})
                continue
            if not pila:
                continue
            l = pila.pop()
            if l['li'] is not None:
                l['items'].append(s[l['li']:m.start()])
            if not pila:
                res.append((l['tag'], l['items']))
        else:
            if not pila:
                continue
            l = pila[-1]
            if not cierre:
                if l['li'] is not None:
                    l['items'].append(s[l['li']:m.start()])
                l['li'] = m.end()
            elif l['li'] is not None:
                l['items'].append(s[l['li']:m.start()])
                l['li'] = None
    return res


_TABLA = re.compile(r'<table\b[^>]*>(.*?)</table\s*>', re.I | re.S)
_FILA = re.compile(r'<tr\b[^>]*>(.*?)</tr\s*>', re.I | re.S)
_CELDA = re.compile(r'<t([hd])\b[^>]*>(.*?)</t[hd]\s*>', re.I | re.S)


def tablas(fragmento):
    """[[ [celda_texto, ...], ... ], ...]: cada tabla, fila por fila, en texto plano.

    La primera fila suele ser la de encabezados (<th>); se devuelve igual, quien llama decide.
    """
    res = []
    for t in _TABLA.finditer(fragmento or ''):
        filas = []
        for f in _FILA.finditer(t.group(1)):
            filas.append([texto_plano(c.group(2)) for c in _CELDA.finditer(f.group(1))])
        res.append(filas)
    return res


_A = re.compile(r'<a\b[^>]*href\s*=\s*"([^"]*)"[^>]*>(.*?)</a\s*>', re.I | re.S)


def enlaces(fragmento):
    """[(href, texto), ...] de todos los <a href> del fragmento."""
    return [(m.group(1), texto_plano(m.group(2))) for m in _A.finditer(fragmento or '')]


def sin_enlaces(fragmento):
    """El fragmento con los <a ...>...</a> sacados (para buscar lo que quedo afuera)."""
    return _A.sub(' ', fragmento or '')


_REGLA = re.compile(r'\b(RN-[A-Z]+-\d+[A-Z]?|DEC-\d+)\b')
_ID = re.compile(r'(?<![\w/])#(\d{5,7})\b')
_MARCA = re.compile(r'\[(T|H)-(\d+)\]')


def reglas_citadas(fragmento):
    """Codigos [RN-...] y [DEC-...] mencionados, en orden y sin repetir."""
    vistos = []
    for c in _REGLA.findall(texto_plano(fragmento)):
        if c not in vistos:
            vistos.append(c)
    return vistos


def ids_citados(fragmento):
    """Numeros #NNNNN mencionados en el texto (no en los href), sin repetir."""
    vistos = []
    for c in _ID.findall(texto_plano(fragmento)):
        if c not in vistos:
            vistos.append(c)
    return vistos


def marcas_lote(fragmento):
    """Marcadores [T-nn] / [H-nn] de un borrador del modo lote, sin repetir."""
    vistos = []
    for t, n in _MARCA.findall(fragmento or ''):
        c = '[%s-%s]' % (t, n)
        if c not in vistos:
            vistos.append(c)
    return vistos
