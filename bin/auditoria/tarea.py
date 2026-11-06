"""Lectura de la Descripcion de UNA Tarea (HTML de Azure o borrador del modo lote).

Por que existe. auditar-tarea, cargar-a-azure 2b y analizar-tareas cuentan las mismas cosas
de la misma tarjeta: secciones, filas de la tabla de Escenarios, tests, modos de falla. Si cada
script recorta el HTML a su manera, dos scripts cuentan distinto la misma Tarea. parsear() es
el recorte unico; los chequeos viven en bin/auditar-tarea.py.

Formato que entiende (el esqueleto de checklists/mapa-campos-azure.md y el de las Tareas ya
cargadas, que es mas viejo):
- Secciones por <h3>. Los tests son los <li> del <ol> de "Tests a escribir PRIMERO": el numero
  es la POSICION en la lista (la numeracion del <ol> es implicita), no un numero escrito.
- La tabla de Escenarios (SDD), con la forma vieja (una fila "No lo cubre esta Tarea: es de
  #X" por Escenario que no cubre) o la nueva (la linea "No cubre:" al pie).
- Un Esquema con sus filas en un <ul> anidado (forma nueva) o escritas en el renglon
  ("Esquema, dos casos: ...", forma vieja).

esqueleto() lee la lista de <h3> esperada DE mapa-campos-azure.md en cada corrida: la fuente
unica es ese archivo, no una lista copiada aca.

Solo biblioteca estandar. ASCII puro: los caracteres no ASCII se arman con chr().
"""

import html as _html
import os
import re

from . import texto

WARN = chr(0x26a0)                 # la marca de pendiente
FLECHA = chr(0x2192)               # la flecha de entrada -> resultado
PUNTO_MEDIO = chr(0xb7)            # separador de la linea "No cubre"
GUION_N = chr(0x2013)              # guion medio (rangos "1-3")
GUION_M = chr(0x2014)              # raya
COMILLAS = '"\'`' + chr(0x201c) + chr(0x201d) + chr(0xab) + chr(0xbb) + chr(0x2018) + chr(0x2019)
_VS16 = chr(0xfe0f)                # selector de variante que a veces acompana al WARN

MAPA = 'tablero/checklists/mapa-campos-azure.md'   # relativo a la raiz

FAMILIAS = ('estado', 'concurrencia', 'autorizacion', 'dependencia caida', 'limites',
            'idempotencia')


# ---------------------------------------------------------------------------------------
# Normalizacion
# ---------------------------------------------------------------------------------------

def n(s):
    """Para comparar: sin tildes, minusculas, espacios colapsados, sin el selector VS16."""
    s = texto.sin_acentos((s or '').replace(_VS16, '').replace(chr(0xa0), ' '))
    return re.sub(r'\s+', ' ', s).strip()


def clave_titulo(t):
    """Titulo de seccion sin la marca WARN, sin lo que va entre parentesis y normalizado."""
    s = n(t).replace(WARN, ' ')
    s = re.sub(r'\([^)]*\)', ' ', s)
    return re.sub(r'\s+', ' ', s).strip(' :.')


def titulo_textual(s):
    """Titulo de Escenario para comparar TEXTUAL: solo espacios y comillas de los costados."""
    s = re.sub(r'\s+', ' ', (s or '').replace(chr(0xa0), ' ')).strip()
    return s.strip(COMILLAS + ' ').strip()


def plano(fragmento):
    """Texto plano en una sola linea."""
    return texto.normalizado(fragmento)


_FIN_CELDA = re.compile(r'(</t[dh]\s*>)', re.I)


def celdas_separadas(doc):
    """El html con un espacio despues de cada </td> y </th>.

    texto.texto_plano() corta renglones en </tr> pero no entre celdas, asi que "#125274</td>
    <td>1, 2" se leia como "#1252741, 2". Con el espacio, cada celda queda separada y el resto
    del html no cambia.
    """
    return _FIN_CELDA.sub(r'\1 ', doc or '')


# ---------------------------------------------------------------------------------------
# El esqueleto esperado, leido de mapa-campos-azure.md
# ---------------------------------------------------------------------------------------

def esqueleto(raiz=None):
    """Lista ordenada de los <h3> del esqueleto de la Tarea en mapa-campos-azure.md.

    Lanza OSError si no puede leer el archivo y ValueError si no encuentra el bloque.
    """
    raiz = raiz or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    s = texto.leer(os.path.join(raiz, *MAPA.split('/'))).replace('\r\n', '\n')
    m = re.search(r'^\*\*Tarea\*\*\s*\(`System\.Description`\)', s, re.M)
    if not m:
        raise ValueError('no encuentro el renglon "**Tarea** (`System.Description`)" en ' + MAPA)
    i = s.find('```html', m.end())
    j = s.find('```', i + 7) if i >= 0 else -1
    if i < 0 or j < 0:
        raise ValueError('no encuentro el bloque ```html del esqueleto de la Tarea en ' + MAPA)
    titulos = [t for t, _ in texto.secciones(s[i + 7:j]) if t]
    if not titulos:
        raise ValueError('el bloque del esqueleto de la Tarea no tiene <h3> en ' + MAPA)
    return titulos


def claves_esqueleto(titulos):
    """Una clave corta por titulo (la primera palabra; dos si la primera se repite)."""
    nucleos = [clave_titulo(t) for t in titulos]
    primeras = [x.split(' ')[0] for x in nucleos]
    res = []
    for x, p in zip(nucleos, primeras):
        res.append(' '.join(x.split(' ')[:2]) if primeras.count(p) > 1 else p)
    return res


# ---------------------------------------------------------------------------------------
# Numeros de test
# ---------------------------------------------------------------------------------------

_SEP_RANGO = r'\s*(?:al|a|hasta|' + GUION_N + r'|-)\s*'
_ITEM = r'\d{1,3}(?:' + _SEP_RANGO + r'\d{1,3})?'
_LISTA = _ITEM + r'(?:\s*(?:,|;|\by\b|\be\b|\bo\b)\s*' + _ITEM + r')*'
_REF = re.compile(r'\b(?:tests?|pruebas?)\s+(?:n(?:ro)?\.?\s*)?(' + _LISTA + r')', re.I)
_DE_OTRA = re.compile(r'^\s*(?:de|del)\s+(?:#|\[|la\b|el\b|las\b|los\b|su\b|sus\b|otra|esa|esta)',
                      re.I)
_NUM_CELDA = re.compile(r'(?<![#\w\-/.\[])(\d{1,3})(?:' + _SEP_RANGO + r'(\d{1,3}))?(?![\w/.\]])')


def _expandir(lista):
    res = []
    for m in re.finditer(r'(\d{1,3})(?:' + _SEP_RANGO + r'(\d{1,3}))?', lista):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        if b is not None and a < b <= a + 300:
            res.extend(range(a, b + 1))
        else:
            res.append(a)
            if b is not None:
                res.append(b)
    return res


def numeros(celda):
    """Numeros de test de una celda: "1, 44, 45", "31 a 38", "13 a 19, 41". Sin repetir."""
    res = []
    for m in _NUM_CELDA.finditer(celda or ''):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        ns = list(range(a, b + 1)) if (b is not None and a < b <= a + 300) else \
            ([a] + ([b] if b is not None else []))
        for x in ns:
            if x not in res:
                res.append(x)
    return res


def tests_mencionados(prosa):
    """Numeros de test que una frase nombra ("el test 8", "los tests 14 a 16 y 20").

    No cuenta los tests de OTRA Tarea ("el test 1 de #125231", "sus tests 2 y 3").
    """
    res = []
    s = prosa or ''
    for m in _REF.finditer(s):
        if _DE_OTRA.match(s[m.end():m.end() + 14]):
            continue
        if re.search(r'\bsus\s*$', s[max(0, m.start() - 6):m.start()], re.I):
            continue
        for x in _expandir(m.group(1)):
            if x not in res:
                res.append(x)
    return res


# ---------------------------------------------------------------------------------------
# Piezas
# ---------------------------------------------------------------------------------------

_TAG_L = re.compile(r'<(/?)(ul|ol)\b[^>]*>', re.I)


def sin_listas(fragmento):
    """El fragmento sin sus <ul>/<ol> (con todo lo que tienen adentro)."""
    s = fragmento or ''
    out, prof, pos = [], 0, 0
    for m in _TAG_L.finditer(s):
        if prof == 0:
            out.append(s[pos:m.start()])
        prof = max(0, prof - 1) if m.group(1) else prof + 1
        pos = m.end()
    if prof == 0:
        out.append(s[pos:])
    return ''.join(out)


def items(fragmento, tags=('ul', 'ol')):
    """Los <li> de las listas de primer nivel del fragmento, en html."""
    res = []
    for tag, its in texto.listas(fragmento):
        if tag in tags:
            res.extend(its)
    return res


_PRE = re.compile(r'<pre\b[^>]*>(.*?)</pre\s*>', re.I | re.S)


def pres(fragmento):
    """Contenido html de cada <pre> del fragmento."""
    return [m.group(1) for m in _PRE.finditer(fragmento or '')]


def texto_pre(pre_html):
    """Texto de un <pre>: sin etiquetas (Azure mete <a> adentro) y con las entidades resueltas."""
    return _html.unescape(re.sub(r'<[^>]+>', '', pre_html))


_CODIGO_RESP = re.compile(r'(?:^|[\s{,])[\'"]?([1-5]\d\d)[\'"]?\s*:', re.M)


def codigos_respuesta(contrato):
    res = []
    for c in _CODIGO_RESP.findall(contrato or ''):
        if c not in res:
            res.append(c)
    return res


def enums_detalle(contrato):
    """[{'valor', 'comentario'}] de cada enum: [A, B] (en una o varias lineas) o con '- A'.

    'comentario' es el comentario YAML (#...) del renglon donde esta el valor: el contrato lo
    usa para marcar lo que viene de otra Tarea ("# de #125232") y lo nuevo ("# nuevo").
    """
    res, vistos = [], set()
    s = contrato or ''
    for m in re.finditer(r'\benum\s*:', s):
        resto = s[m.end():]
        pares = []
        r = resto.lstrip(' \t')
        if r.startswith('['):
            fin = r.find(']')
            cuerpo = r[1:fin if fin >= 0 else len(r)]
            cola = r[fin + 1:].split('\n', 1)[0] if fin >= 0 else ''
            renglones = cuerpo.split('\n')
            for k, linea in enumerate(renglones):
                valores, _, com = linea.partition('#')
                if k == len(renglones) - 1 and '#' in cola:
                    com = com or cola.split('#', 1)[1]
                for v in valores.split(','):
                    pares.append((v.strip().strip('\'"'), com.strip()))
        elif r[:1] in ('\n', '\r', ''):
            for linea in resto.split('\n')[1:]:
                mi = re.match(r'^\s*-\s*([^#]+?)\s*(?:#(.*))?$', linea)
                if not mi:
                    break
                pares.append((mi.group(1).strip().strip('\'"'), (mi.group(2) or '').strip()))
        for v, com in pares:
            if v and v not in vistos:
                vistos.add(v)
                res.append({'valor': v, 'comentario': com})
    return res


def valores_enum(contrato):
    """Valores de cada enum del contrato, en orden y sin repetir."""
    return [e['valor'] for e in enums_detalle(contrato)]


_UPPER_COMILLAS = re.compile(r'"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)"')
_UPPER_SNAKE = re.compile(r'\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b')


def codigos_error(payload):
    """Codigos de error (MAYUSCULAS_CON_GUION_BAJO o "MAYUSCULAS" entre comillas)."""
    res = []
    for rx in (_UPPER_COMILLAS, _UPPER_SNAKE):
        for c in rx.findall(payload or ''):
            if len(c) >= 3 and c not in res:
                res.append(c)
    return res


def _columna(encabezado, *claves, defecto=None):
    for i, c in enumerate(encabezado):
        if any(k in n(c) for k in claves):
            return i
    return defecto


def _celda(fila, i):
    return fila[i] if (i is not None and i < len(fila)) else ''


def _ids(s):
    return re.findall(r'(?<![\w/])#(\d{5,7})\b', s or '')


def _es_encabezado_sdd(fila):
    ns = [n(c) for c in fila]
    return any('escenario' in c for c in ns) and any('test' in c for c in ns)


# Una fila que dice que cubre una PARTE del Escenario. "solo" y "es de" no entran: aparecen en
# filas que cubren el Escenario entero ("un solo tramo", "el tope es de 1 anio").
_PARCIAL = re.compile(r'\b(en parte|parcial|parcialmente|la parte|una parte|lo completa|'
                      r'la completa|lo completan|la completan|la otra mitad|mitad|el resto|'
                      r'lo pinta|lo cubre|lo cubren|la cubre|la cubren)\b')


def _tabla_sdd(cuerpo):
    for t in texto.tablas(cuerpo):
        if t and _es_encabezado_sdd(t[0]):
            return t
    return None


def _no_cubre(lineas):
    """La linea "No cubre: titulo (#ID) . titulo (#ID)" -> [{'titulo', 'ids'}]."""
    for l in lineas:
        if not n(l).startswith('no cubre'):
            continue
        resto = l.split(':', 1)[1] if ':' in l else l[len('No cubre'):]
        sep = PUNTO_MEDIO if PUNTO_MEDIO in resto else ';'
        res = []
        for pedazo in resto.split(sep):
            p = pedazo.strip().rstrip('.').strip()
            if not p:
                continue
            ids = _ids(p) + texto.marcas_lote(p)
            t = p
            while True:
                t2 = re.sub(r'\s*\((?:[^()]*?(?:#\d|\[T-\d)[^()]*)\)\s*$', '', t)
                t2 = re.sub(r'\s*[-' + GUION_N + GUION_M + r':]\s*(?:#\d{5,7}|\[T-\d+\])\s*$', '', t2)
                if t2 == t:
                    break
                t = t2
            res.append({'titulo': re.sub(r'\s+', ' ', t).strip(), 'ids': ids, 'texto': p})
        return res
    return []


def _frases(plano_multilinea):
    res = []
    for l in plano_multilinea.split('\n'):
        res.extend(x for x in re.split(r'(?<=[.;])\s+(?=[A-Z' + chr(0xc1) + chr(0xc9) + r'])', l)
                   if x.strip())
    return res


def _capa(alcance_html, nombre_archivo, titulo=None):
    """'back' | 'front' | 'desconocida', por las senales del Alcance tecnico.

    Primero el prefijo del titulo ("Front: ...", "Back: ..."), si se conoce. Despues el renglon
    "Componente / repo", que pesa mas (<repo-front>, <repo-back>), y las
    palabras de cada lado. Empate: el nombre del archivo (T01-front-...), y si no,
    'desconocida'. Ojo: una Tarea de front puede nombrar "domain/services" del core del front,
    por eso no alcanza con encontrar "domain".
    """
    pre = n(titulo or '')
    if re.match(r'^(front|frontend)\s*[:' + GUION_M + '-]', pre):
        return 'front'
    if re.match(r'^(back|backend)\s*[:' + GUION_M + '-]', pre):
        return 'back'
    t = n(texto.texto_plano(alcance_html or ''))
    front, back = 0, 0
    for linea in t.split('\n'):
        if linea.startswith('componente') or 'repo' in linea.split(':', 1)[0]:
            if re.search(r'front', linea):
                front += 5
            if re.search(r'back', linea):
                back += 5
    front += len(re.findall(r'\b(front|frontend|react|view|vista|componentes?|vite|vitest|tsx|'
                            r'hook|reducer|pantalla|pagina)\b', t))
    back += len(re.findall(r'\b(api|application|domain|infra|backend|quarkus|junit|endpoint|'
                           r'flyway|migracion)\b', t))
    if front > back:
        return 'front'
    if back > front:
        return 'back'
    nom = n(os.path.basename(nombre_archivo or ''))
    if re.search(r'(^|[-_ .])front([-_ .]|$)', nom):
        return 'front'
    if re.search(r'(^|[-_ .])back([-_ .]|$)', nom):
        return 'back'
    return 'desconocida'


_INTEGRACION = re.compile(r'requiere test de integracion\s*:?\s*(si|no)\b')


def _esquema(cabeza):
    """El item es un Esquema: "Esquema" al principio, o despues de un prefijo corto que
    termina en '.', ':' o ')' ("Formateador. Esquema", "(P-048) Esquema", "Guardarrail (...):
    Esquema")."""
    m = re.search(r'\bEsquema\b', cabeza)
    if not m or m.start() > 70:
        return False
    antes = cabeza[:m.start()].strip()
    return antes == '' or bool(re.search(r'[.:)\]' + WARN + _VS16 + r']$', antes))


def _test(i, li):
    cabeza_html = sin_listas(li)
    cabeza = plano(cabeza_html)
    anidadas = texto.listas(li)
    filas = [plano(x) for tag, its in anidadas if tag == 'ul' for x in its]
    filas_ol = [plano(x) for tag, its in anidadas if tag == 'ol' for x in its]
    txt = plano(li)
    ca = n(cabeza)
    return {
        'n': i,
        'html': li,
        'texto': txt,
        'cabeza': cabeza,
        'es_esquema': _esquema(cabeza),
        'filas': filas,
        'filas_ol': filas_ol,
        'es_guardarrail': 'guardarrail' in ca[:100],
        'tiene_frase_rojo': 'se pone en rojo si' in n(txt),
        'reglas': texto.reglas_citadas(li),
        'tiene_warn': WARN in txt,
        'es_invariante': 'invariante' in ca[:80],
        'etiqueta_integracion': bool(re.match(r'^\W*integracion\b\s*[:(]', ca)),
    }


def _modos(cuerpo):
    res = {}
    renglones = [plano(x) for x in items(cuerpo)] or texto.texto_plano(cuerpo).split('\n')
    for r in renglones:
        etiqueta, dos_puntos, resto = r.partition(':')
        k = n(etiqueta)
        for f in FAMILIAS:
            if k.startswith(f) and f not in res:
                res[f] = (resto if dos_puntos else r[len(etiqueta):]).strip()
    return res


def _campo_validacion(li):
    """El nombre del campo de una validacion: el <code> o el texto entre comillas de la
    etiqueta en negrita; la etiqueta misma si es corta. '' si no se puede saber."""
    m = re.match(r'\s*<b>(.*?)</b>', li, re.S | re.I) or re.match(r'\s*<code>(.*?)</code>', li,
                                                                   re.S | re.I)
    etiqueta = m.group(1) if m else ''
    if not etiqueta:
        t = plano(li)
        etiqueta = t.split(':', 1)[0] if ':' in t[:60] else ''
    c = re.search(r'<code>(.*?)</code>', etiqueta, re.S | re.I)
    if c:
        return plano(c.group(1)).strip(' :')
    t = re.sub(r'\([^)]*\)', ' ', plano(etiqueta))
    t = re.sub(r'\s+', ' ', t).strip(' :,.')
    q = re.search('[' + re.escape(COMILLAS) + ']([^' + re.escape(COMILLAS) + ']+)[' +
                  re.escape(COMILLAS) + ']', t)
    if q:
        return q.group(1)
    return t if 0 < len(t.split()) <= 2 else ''


# ---------------------------------------------------------------------------------------
# La Tarea entera
# ---------------------------------------------------------------------------------------

def buscar(secs, clave):
    """(titulo, cuerpo) de la primera seccion cuyo titulo normalizado empieza con clave."""
    for t, c in secs:
        if clave_titulo(t).startswith(clave):
            return t, c
    return None, None


def parsear(doc, nombre_archivo=None, titulo=None):
    """La Tarea como dict. Ver el encabezado del modulo para el formato que entiende.

    titulo: el System.Title, si quien llama lo tiene (su prefijo "Front:"/"Back:" decide la
    capa). Si no, se mira lo que haya antes del primer <h3> y despues el Alcance tecnico.
    'capa' es 'back' | 'front' | 'ui' | 'desconocida'; 'ui' es la Tarea chica de solo UI/config:
    no es de back y no tiene ni SDD ni tests (el bloque del medio se borro entero).
    """
    largo = len(doc or '')
    doc = celdas_separadas(doc)
    todas = texto.secciones(doc)
    secs = [(t, c) for t, c in todas if t]
    res = {'secciones': [t for t, _ in secs], 'largo': largo}

    _, alcance = buscar(secs, 'alcance')
    if titulo is None and todas and not todas[0][0]:
        titulo = (texto.texto_plano(todas[0][1]).split('\n') or [''])[0]
    res['capa_alcance'] = _capa(alcance, nombre_archivo, titulo)
    mi = _INTEGRACION.search(n(texto.texto_plano(alcance or '')))
    res['requiere_integracion'] = None if not mi else (mi.group(1) == 'si')

    # Contrato
    _, contrato = buscar(secs, 'contrato')
    res['hay_contrato'] = contrato is not None
    ps = pres(contrato) if contrato else []
    res['contrato'] = '\n'.join(texto_pre(p) for p in ps) if ps else None
    res['codigos_contrato'] = codigos_respuesta(res['contrato'])
    res['enums'] = valores_enum(res['contrato'])
    res['enums_detalle'] = enums_detalle(res['contrato'])

    # Validaciones
    _, val = buscar(secs, 'validaciones')
    lis = items(val) if val else []
    res['validaciones'] = [plano(x) for x in lis]
    res['validaciones_campos'] = [_campo_validacion(x) for x in lis]

    # Casos de error
    _, ce = buscar(secs, 'casos de error')
    filas = []
    tabs = texto.tablas(ce) if ce else []
    if tabs and tabs[0]:
        enc = tabs[0][0]
        ic = _columna(enc, 'condici', defecto=0)
        ik = _columna(enc, 'codigo', 'resultado', 'http', 'excepci', defecto=1)
        ip = _columna(enc, 'payload', 'mensaje', 'cuerpo', defecto=2)
        ir = _columna(enc, 'regla', defecto=3)
        for f in tabs[0][1:]:
            if not any(x.strip() for x in f):
                continue
            cod, pay = _celda(f, ik), _celda(f, ip)
            filas.append({'condicion': _celda(f, ic), 'codigo': cod, 'payload': pay,
                          'regla': _celda(f, ir),
                          'codigos_http': re.findall(r'(?<![\d.])([1-5]\d\d)(?![\d.])', cod),
                          'codigos_error': codigos_error(pay),
                          'excepcion': re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z0-9]*)+)\b', cod)})
    res['casos_error'] = filas
    res['hay_casos_error'] = ce is not None

    # SDD
    _, sdd = buscar(secs, 'especificacion')
    res['hay_sdd'] = sdd is not None
    sdd = sdd or ''
    tabla = _tabla_sdd(sdd)
    res['hay_tabla_sdd'] = tabla is not None
    res['sdd_padre'] = _ids(' '.join(tabla[0])) if tabla else []
    sdd_filas = []
    if tabla:
        enc = tabla[0]
        it = _columna(enc, 'escenario', defecto=0)
        ip = _columna(enc, 'parte', 'cubre', defecto=1)
        iv = _columna(enc, 'test', defecto=2)
        for f in tabla[1:]:
            if not any(x.strip() for x in f):
                continue
            parte = _celda(f, ip)
            np_ = n(parte)
            no_lo = bool(re.search(r'\bno (?:lo|la) cubre\b', np_))
            sdd_filas.append({
                'titulo': re.sub(r'\s+', ' ', _celda(f, it)).strip(),
                'parte': parte,
                'tests_texto': _celda(f, iv),
                'tests': numeros(_celda(f, iv)),
                'no_lo_cubre': no_lo,
                'parcial': (not no_lo and not np_.startswith('todo el escenario') and
                            bool(_PARCIAL.search(np_))),
                'ids': _ids(parte) + texto.marcas_lote(parte),
            })
    res['sdd_filas'] = sdd_filas
    prosa = texto.texto_plano(re.sub(r'<table\b.*?</table\s*>', '\n', sdd, flags=re.I | re.S))
    res['no_cubre'] = _no_cubre(prosa.split('\n'))
    no_mapean, en_prosa = [], []
    for fr in _frases(prosa):
        nf = n(fr)
        if 'no mapea' in nf:
            antes = fr[:nf.find('no mapea')]
            for x in (tests_mencionados(antes) or numeros(antes)):
                if x not in no_mapean:
                    no_mapean.append(x)
        elif not nf.startswith('no cubre'):
            for x in tests_mencionados(fr):
                if x not in en_prosa:
                    en_prosa.append(x)
    res['no_mapean'] = no_mapean
    res['sdd_prosa_tests'] = en_prosa

    # Tests
    _, tests = buscar(secs, 'tests')
    res['hay_tests'] = tests is not None
    tests = tests or ''
    listas = texto.listas(tests)
    ols = [its for tag, its in listas if tag == 'ol']
    res['tests_listas_ol'] = len(ols)
    res['tests_listas_ul'] = sum(1 for tag, _ in listas if tag == 'ul')
    lis = [x for its in ols for x in its]
    res['tests'] = [_test(i + 1, li) for i, li in enumerate(lis)]
    intro = texto.texto_plano(sin_listas(tests))
    res['tests_intro'] = intro
    res['datos_base'] = None
    for l in intro.split('\n'):
        if n(l).startswith('datos base'):
            res['datos_base'] = l.split(':', 1)[1].strip() if ':' in l else l
            break

    # Modos de falla
    _, modos = buscar(secs, 'modos')
    res['hay_modos'] = modos is not None
    res['modos_falla'] = _modos(modos) if modos else {}
    res['modos_tests'] = tests_mencionados(texto.texto_plano(modos or ''))

    # Subtareas, DoD, Datos a confirmar, Material de apoyo
    _, sub = buscar(secs, 'subtareas')
    res['subtareas'] = [plano(x) for x in items(sub)] if sub else []
    _, dod = buscar(secs, 'definicion')
    res['hay_dod'] = dod is not None
    res['dod'] = ([plano(x) for x in items(dod)] or
                  [l for l in texto.texto_plano(dod).split('\n') if l]) if dod else []
    _, dac = buscar(secs, 'datos a confirmar')
    res['hay_datos_a_confirmar'] = dac is not None
    if dac is None:
        res['datos_a_confirmar'] = []
    else:
        lis = [plano(x) for x in items(dac)]
        plano_dac = texto.texto_plano(sin_listas(dac))
        if lis:
            res['datos_a_confirmar'] = lis
        elif n(plano_dac).startswith('ninguno'):
            res['datos_a_confirmar'] = ['Ninguno.']
        else:
            res['datos_a_confirmar'] = [l for l in plano_dac.split('\n') if l.strip()]
    _, apoyo = buscar(secs, 'material')
    res['material_de_apoyo'] = apoyo

    res['reglas_citadas'] = texto.reglas_citadas(doc)
    res['ids_citados'] = texto.ids_citados(doc)
    res['marcas'] = texto.marcas_lote(doc)
    res['capa'] = ('ui' if res['capa_alcance'] != 'back' and not res['hay_sdd'] and
                   not res['hay_tests'] else res['capa_alcance'])
    return res
