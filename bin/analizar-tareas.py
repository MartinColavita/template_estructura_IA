#!/usr/bin/env python3
"""Analisis MECANICO del SET de Tareas de una Historia: lo que de analizar-tareas es CONTEO.

    python bin/analizar-tareas.py --historia <criterios.html> <tarea1.html> [<tarea2.html> ...]
                                  [--ids <mapa.json>] [--descripcion <descripcion.html>]
                                  [--json] [--salida <archivo>]

<criterios.html> es el campo Criterios de aceptacion de la Historia padre (o su borrador). Cada
<tarea.html> es la Descripcion de una Tarea de esa Historia (guardada del tablero o el borrador
del modo lote). --descripcion es la Descripcion de la Historia: con ella tambien se cruzan las
reglas del bloque "Reglas de negocio", no solo las del Gherkin.

Tres estados, nunca dos:  0 = sin hallazgos   1 = hay HALLAZGO o NO AUDITABLE   2 = SIN DATOS
SIN DATOS: la Historia no se pudo leer o vino vacia, o no se pudo leer ni una Tarea. Cualquier
error que no se esperaba tambien da 2, nunca 0 ni 1.

POR QUE EXISTE. analizar-tareas juzga el set completo, no una Tarea suelta: que cada Escenario
del padre sea FILA de alguna Tarea (la linea "No cubre" no cuenta), que los punteros "es de #X"
apunten a una Tarea que de verdad lo tiene, que cada regla de la Historia este en alguna Tarea,
que dos Tareas no definan el mismo endpoint con contratos distintos y que el test de
integracion declarado exista. Eso es conteo: un modelo leyendo seis tarjetas de 40.000
caracteres cuenta distinto cada vez. Este script cuenta igual siempre. Al auditor le queda lo
que pide criterio, y el reporte lo lista al final ("Lo que este script NO mira"). Lo que este
script marca HALLAZGO, el modelo no lo da por bueno.

QUIEN ES CADA TAREA. Para seguir un puntero "(#125280)" hay que saber que archivo es #125280:
- del nombre del archivo: "T09-..." o "T-09.html" es [T-09]; un numero de 5 a 7 cifras es #ID;
- de --ids: {"<archivo o clave>": "#NNNNNN" | NNNNNN | "[T-nn]"}. Vale el mapa-fichas.json
  ({"[T-09]": 125280}), el mapa-ids.json del lote y su items.json (clave, id, archivo);
- sin --ids, si junto a las Tareas hay un items.json, mapa-ids.json o mapa-fichas.json, se lee.
Un puntero a un #ID que no es de ninguna Tarea del set es AVISO (se verifica en el tablero),
nunca OK.

NUMERACION. Cada renglon lleva "AN-n" con el numero del chequeo de la skill analizar-tareas
(AN-1 contratos, AN-2 reglas, AN-5 errores, AN-6 dependencias, AN-7 Escenarios, AN-8 test de
integracion). AN-7 se parte en a (hueco), b (titulo textual), c (fila sin tests), d (punteros)
y e (cobertura parcial sin la otra Tarea). "set" son los problemas de los insumos.

SOLO LECTURA: no usa la red, no toca Azure, GitLab ni el Cerebro. Escribe, como mucho, el
archivo que se le pide con --salida. Solo biblioteca estandar; ASCII puro en este archivo.
"""

import argparse
import importlib.util
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from auditoria import historia, tarea, texto  # noqa: E402
from auditoria import reporte as rep  # noqa: E402

HERRAMIENTA = 'analizar-tareas'
MAPAS_JUNTO = ('items.json', 'mapa-ids.json', 'mapa-fichas.json')

PARA_EL_AUDITOR = [
    'AN-4: solapes de trabajo: dos Tareas que hacen lo mismo (mismo contrato, misma capa). El '
    'script solo avisa endpoints repetidos y Escenarios que dos Tareas dicen cubrir enteros.',
    'AN-5: confirmar o descartar los AVISO de codigos, y que los payloads de error coincidan '
    'entre la Tarea que los devuelve y la que los consume (el script solo cruza los codigos).',
    'AN-7: coberturas parciales que suman: que entre las partes declaradas quede el Escenario '
    'COMPLETO. El script solo mira que la Tarea nombrada tenga la fila, no que las dos partes '
    'cierren el Escenario; y un Escenario que necesita back y front y lo cubre entero una sola '
    'Tarea es sospechoso.',
    'AN-7, quien prueba la union: para cada Escenario repartido entre back y front, que Tarea lo '
    'prueba de punta a punta (el script avisa los que no cubre una Tarea e2e). "Requiere test de '
    'integracion" no lo tapa: es para dependencias externas.',
    'AN-3: comportamiento de la Historia sin Tarea que no sea un Escenario (Alcance, Casos de uso, '
    'Datos y estados de la Descripcion).',
    'AN-8: una Tarea que dice "Requiere test de integracion: si" y prueba todo contra dobles (el '
    'script solo mira que esten el test, la subtarea y el item del DoD).',
    'AN-9: Esfuerzo original y Actividad de cada Tarea: son campos de Azure, no de la Descripcion; '
    'el script no los ve.',
]


# ---------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------

def corto(s, largo=90):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= largo else s[:largo - 3] + '...'


def rangos(nums):
    """[1, 2, 3, 7] -> '1 a 3, 7'."""
    nums = sorted(set(nums))
    partes, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        partes.append(str(nums[i]) if j == i else
                      ('%d, %d' % (nums[i], nums[j]) if j == i + 1 else
                       '%d a %d' % (nums[i], nums[j])))
        i = j + 1
    return ', '.join(partes)


def _cargar_auditar_tarea():
    """El modulo bin/auditar-tarea.py (para reusar ch_integracion), o None si no carga."""
    ruta = os.path.join(AQUI, 'auditar-tarea.py')
    try:
        spec = importlib.util.spec_from_file_location('auditar_tarea_para_analizar', ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 -- sin el modulo se recheckea a mano (_integracion_minima)
        return None


# ---------------------------------------------------------------------------------------
# Identidades: que #ID / [T-nn] es cada archivo
# ---------------------------------------------------------------------------------------

_TOK_ID = re.compile(r'^\s*#?\s*(\d{5,7})\s*$')
_TOK_MARCA = re.compile(r'^\s*\[?\s*([TH])\s*-?\s*(\d{1,4})\s*\]?\s*$', re.I)
_REF = re.compile(r'(?<![\w/])#(\d{5,7})\b|\[([TH])-(\d+)\]')


def token(valor):
    """'#125280' | 'T-9' | 'H-2' | None, de un valor suelto (125280, '#125280', '[T-09]')."""
    if valor is None or isinstance(valor, bool):
        return None
    s = str(valor)
    m = _TOK_ID.match(s)
    if m:
        return '#' + m.group(1)
    m = _TOK_MARCA.match(s)
    if m:
        return '%s-%d' % (m.group(1).upper(), int(m.group(2)))
    return None


def mostrar(tok):
    """'#125280' -> '#125280';  'T-9' -> '[T-09]'."""
    if tok.startswith('#'):
        return tok
    letra, num = tok.split('-', 1)
    return '[%s-%02d]' % (letra, int(num))


def tokens_texto(s):
    """#ID y [T-nn]/[H-nn] de un texto, como tokens, en orden y sin repetir."""
    res = []
    for m in _REF.finditer(s or ''):
        t = ('#' + m.group(1)) if m.group(1) else '%s-%d' % (m.group(2), int(m.group(3)))
        if t not in res:
            res.append(t)
    return res


_RANGO_IDS = re.compile(r'#(\d{5,7})\s*(?:a|al|hasta|-|' + tarea.GUION_N + r')\s*#(\d{5,7})\b')


def tokens_con_rangos(s):
    """Como tokens_texto, y "#125272 a #125283" cuenta los doce (hasta 40)."""
    res = tokens_texto(s)
    for m in _RANGO_IDS.finditer(s or ''):
        a, b = int(m.group(1)), int(m.group(2))
        if a < b <= a + 40:
            for x in range(a + 1, b):
                if '#%d' % x not in res:
                    res.append('#%d' % x)
    return res


def tokens_nombre(ruta):
    """Lo que dice el nombre del archivo: 'T09-...' o 'T-09.html' -> T-9; 125280 -> #125280."""
    base = os.path.basename(ruta or '')
    res = []
    m = re.match(r'^\[?T-?(\d{1,3})(?!\d)', base, re.I)
    if m:
        res.append('T-%d' % int(m.group(1)))
    for x in re.findall(r'(?<!\d)(\d{5,7})(?!\d)', base):
        if '#' + x not in res:
            res.append('#' + x)
    return res


def leer_ids(ruta):
    """[(clave, valor)] de un mapa {"clave": valor} o del items.json de un lote."""
    d = json.loads(texto.leer(ruta))
    pares = []
    if isinstance(d, dict) and isinstance(d.get('items'), list):
        for it in d['items']:
            if not isinstance(it, dict) or not it.get('clave'):
                continue
            clave = str(it['clave'])
            if it.get('id'):
                pares.append((clave, str(it['id'])))
            pares.append((str(it.get('archivo') or clave + '.html'), clave))
        return pares
    if not isinstance(d, dict):
        raise ValueError('el mapa no es un objeto JSON {clave: valor}')
    for k, v in d.items():
        if str(k).startswith('_') or isinstance(v, bool) or not isinstance(v, (str, int)):
            continue
        pares.append((str(k), str(v)))
    return pares


def _es_archivo(clave, ruta):
    """La clave del mapa nombra este archivo (ruta, nombre, o nombre sin extension)."""
    k = clave.replace('\\', '/').strip().lower()
    base = os.path.basename(ruta).lower()
    if k == base or k == base.split('.')[0] or k == os.path.splitext(base)[0]:
        return True
    if '/' in k:
        return os.path.abspath(clave).lower() == os.path.abspath(ruta).lower() or \
            k.endswith('/' + base)
    return False


def identidades(ruta, pares):
    """Conjunto de tokens ('#125280', 'T-9') que identifican a este archivo."""
    ids = set(tokens_nombre(ruta))
    for k, v in pares:
        if _es_archivo(k, ruta) and token(v):
            ids.add(token(v))
    cambio = True
    while cambio:
        cambio = False
        for k, v in pares:
            tk, tv = token(k), token(v)
            if not tk or not tv:
                continue
            if tk in ids and tv not in ids:
                ids.add(tv)
                cambio = True
            elif tv in ids and tk not in ids:
                ids.add(tk)
                cambio = True
    return set(t for t in ids if not t.startswith('H-'))


def _orden_tok(t):
    return (not t.startswith('#'), t)


# ---------------------------------------------------------------------------------------
# Lectura del set
# ---------------------------------------------------------------------------------------

_E2E = re.compile(r'\b(e2e|end to end|de punta a punta|back y (?:el )?front juntos|'
                  r'front y (?:el )?back juntos|prueba la union)\b')


def leer_tarea(ruta, doc, pares):
    d = tarea.parsear(doc, ruta)
    secs = [(t, c) for t, c in texto.secciones(tarea.celdas_separadas(doc)) if t]
    _, dep = tarea.buscar(secs, 'dependencias')
    _, obj = tarea.buscar(secs, 'objetivo')
    _, con = tarea.buscar(secs, 'contrato')
    nombre = os.path.basename(ruta)
    if nombre.lower().endswith('.html'):
        nombre = nombre[:-5]
    ids = identidades(ruta, pares)
    e2e = bool(re.search(r'(^|[-_ .])e2e([-_ .]|$)', tarea.n(os.path.basename(ruta)))) or \
        bool(_E2E.search(tarea.n(texto.texto_plano(obj or ''))))
    return {'ruta': ruta, 'nombre': nombre, 'ids': ids, 'd': d, 'capa': d['capa'], 'e2e': e2e,
            'dep': dep, 'contrato_html': con}


def etiqueta(T):
    ids = sorted(T['ids'], key=_orden_tok)
    return T['nombre'] + ((' (' + ', '.join(mostrar(t) for t in ids) + ')') if ids else '')


# ---------------------------------------------------------------------------------------
# AN-7: Escenarios del padre contra las filas de todas las Tareas
# ---------------------------------------------------------------------------------------

# Senales de que una fila cubre SOLO una parte. "un solo tramo" o "solo esos datos" no entran:
# aparecen en filas que cubren el Escenario entero.
_PARCIAL_EXTRA = re.compile(r'(^solo\b|^solamente\b|\bsolo (?:el|la|lo|los|las) (?:lado|parte|'
                            r'back|front|pantalla|guardado|control|controles)\b|'
                            r'\bsolo del? (?:back|front|lado)\b|\b(?:el|del) lado\b|'
                            r'(?<!forma )\bparte del?\b|\blo completa\b|\bla otra mitad\b)')


def es_parcial(fila):
    np_ = tarea.n(fila['parte'])
    if np_.startswith('todo el escenario'):
        return False
    return bool(fila['parcial'] or _PARCIAL_EXTRA.search(np_))


def _ubicador(escs):
    textual = [tarea.titulo_textual(e['titulo']) for e in escs]
    suelto = [tarea.n(t) for t in textual]

    def ubicar(titulo):
        tt = tarea.titulo_textual(titulo)
        if tt in textual:
            return textual.index(tt), True
        nt = tarea.n(tt)
        if nt in suelto:
            return suelto.index(nt), False
        return None, False
    return ubicar


def ch_escenarios(r, escs, ts, id_historia):
    """AN-7a a e. Devuelve (cobertura {i: [(T, fila)]}, huecos [titulos])."""
    if not escs:
        r.no_auditable('AN-7', 'la Historia no tiene ningun Escenario: no hay loop BDD que cerrar',
                       'Regla del cero: no se derivan Tareas de una Historia sin Gherkin')
        return {}, []
    ubicar = _ubicador(escs)
    titulos = [e['titulo'] for e in escs]
    cobertura = dict((i, []) for i in range(len(escs)))
    punteros = []          # (T, i_escenario, token, origen)
    malos = {'7b': 0, '7c': 0, '7e': 0}

    def valido(tok, T):
        return tok not in T['ids'] and tok != id_historia and not tok.startswith('H-')

    def titulo_ok(T, titulo, donde):
        i, exacto = ubicar(titulo)
        if i is None:
            r.hallazgo('AN-7b', '%s: %s "%s" no coincide con ningun Escenario del padre'
                       % (etiqueta(T), donde, corto(titulo, 70)),
                       'el titulo se copia textual del Gherkin; si no, no se puede rastrear')
            malos['7b'] += 1
        elif not exacto:
            r.hallazgo('AN-7b', '%s: %s "%s" difiere solo en tildes o mayusculas del Escenario "%s"'
                       % (etiqueta(T), donde, corto(titulo, 60), corto(titulos[i], 60)),
                       'el titulo va textual')
            malos['7b'] += 1
        return i

    for T in ts:
        d = T['d']
        if d['sdd_padre'] and id_historia and ('#' + d['sdd_padre'][0]) != id_historia:
            r.aviso('AN-7', '%s: su tabla dice Historia #%s y el padre del set es %s'
                    % (etiqueta(T), d['sdd_padre'][0], id_historia),
                    'revisar que la Tarea sea de esta Historia')
        if not d['hay_tabla_sdd']:
            if T['capa'] == 'ui':
                r.ok('AN-7', '%s: Tarea de solo UI/config, sin tabla de Escenarios' % etiqueta(T))
            else:
                r.aviso('AN-7', '%s no tiene la tabla de Escenarios: no aporta cobertura'
                        % etiqueta(T), 'auditar-tarea lo marca en su chequeo 5')
        for f in d['sdd_filas']:
            i = titulo_ok(T, f['titulo'], 'la fila')
            toks = [t for t in tokens_texto(f['parte']) if valido(t, T)]
            if f['no_lo_cubre']:
                for t in toks:
                    punteros.append((T, i, t, 'fila "No lo cubre"'))
                continue
            if i is not None:
                cobertura[i].append((T, f))
            if not f['tests']:
                r.hallazgo('AN-7c', '%s: la fila "%s" cubre y no tiene tests que la verifiquen'
                           % (etiqueta(T), corto(f['titulo'], 60)),
                           'columna de tests: "%s"' % corto(f['tests_texto'], 40))
                malos['7c'] += 1
            if es_parcial(f) and not toks:
                r.hallazgo('AN-7e', '%s: la fila "%s" cubre solo una parte y no nombra la Tarea que '
                           'completa el resto (#ID o [T-nn])' % (etiqueta(T), corto(f['titulo'], 60)),
                           corto(f['parte'], 100))
                malos['7e'] += 1
            for t in toks:
                punteros.append((T, i, t, 'fila que cubre una parte'))
        for x in d['no_cubre']:
            i = titulo_ok(T, x['titulo'], '"No cubre" nombra')
            for t in tokens_texto(x['texto']):
                if valido(t, T):
                    punteros.append((T, i, t, '"No cubre"'))

    # AN-7a: cada Escenario es fila que cubre de alguna Tarea
    huecos = []
    for i, t in enumerate(titulos):
        if cobertura[i]:
            quienes = []
            for T, _ in cobertura[i]:
                if T['nombre'] not in quienes:
                    quienes.append(T['nombre'])
            r.ok('AN-7a', '"%s": %s' % (corto(t, 70), ', '.join(quienes)))
            continue
        huecos.append(t)
        dicen = []
        for T, j, tok, origen in punteros:
            if j == i:
                x = '%s dice %s (%s)' % (T['nombre'], mostrar(tok), origen)
                if x not in dicen:
                    dicen.append(x)
        r.hallazgo('AN-7a', 'hueco: el Escenario "%s" no es fila de ninguna Tarea del set'
                   % corto(t, 70), ('; '.join(dicen) if dicen else 'ninguna Tarea lo nombra') +
                   '. Aparecer en "No cubre" no cuenta como cobertura')

    # AN-7d: los punteros apuntan a una Tarea que lo tiene como fila
    fuera, vistos, buenos, falsos = {}, set(), 0, 0
    for T, i, tok, origen in punteros:
        if i is None or (id(T), i, tok) in vistos:
            continue
        vistos.add((id(T), i, tok))
        destinos = [U for U in ts if tok in U['ids']]
        if not destinos:
            fuera.setdefault(tok, [])
            if T['nombre'] not in fuera[tok]:
                fuera[tok].append(T['nombre'])
            continue
        if any(U is V for U in destinos for V, _ in cobertura[i]):
            buenos += 1
            continue
        U = destinos[0]
        if any(i == ubicar(f['titulo'])[0] for f in U['d']['sdd_filas'] if f['no_lo_cubre']):
            como = 'tiene ese Escenario como "No lo cubre esta Tarea"'
        elif any(i == ubicar(x['titulo'])[0] for x in U['d']['no_cubre']):
            como = 'lo pone en su "No cubre"'
        else:
            como = 'no lo tiene como fila'
        r.hallazgo('AN-7d', 'puntero falso: %s dice que "%s" es de %s, y %s %s'
                   % (T['nombre'], corto(titulos[i], 60), mostrar(tok), etiqueta(U), como),
                   'desde: %s. Si el puntero es falso, nadie cubre esa parte' % origen)
        falsos += 1
    for tok in sorted(fuera, key=_orden_tok):
        r.aviso('AN-7d', '%s no es ninguna Tarea del set: no se puede verificar que cubra lo que le '
                'atribuyen; verificar en el tablero' % mostrar(tok),
                'lo nombran: ' + ', '.join(fuera[tok]))
    if buenos and not falsos:
        r.ok('AN-7d', '%d punteros a Tareas del set: todas tienen la fila' % buenos)
    if not malos['7b']:
        r.ok('AN-7b', 'todos los titulos de las filas y de "No cubre" coinciden textual con el padre')
    if not malos['7c']:
        r.ok('AN-7c', 'toda fila que cubre tiene sus tests')
    if not malos['7e']:
        r.ok('AN-7e', 'toda fila que cubre una parte nombra la otra Tarea')

    # Quien prueba la union, y dos Tareas que dicen cubrir entero el mismo Escenario
    for i, t in enumerate(titulos):
        cub = []
        for T, f in cobertura[i]:
            if all(T is not U for U, _ in cub):
                cub.append((T, f))
        capas = set(T['capa'] for T, _ in cub if not T['e2e'])
        if 'back' in capas and 'front' in capas and not any(T['e2e'] for T, _ in cub):
            r.aviso('AN-7', 'quien prueba la union: "%s" se reparte entre %s y ninguna Tarea e2e lo '
                    'cubre' % (corto(t, 60), ', '.join(T['nombre'] for T, _ in cub)),
                    'cada una da verde por su lado; preguntar en que Tarea vive la prueba de punta '
                    'a punta')
        enteros = [T['nombre'] for T, f in cub if tarea.n(f['parte']).startswith('todo el escenario')]
        if len(enteros) >= 2:
            r.aviso('AN-4', 'posible solape: %s dicen cubrir entero "%s"'
                    % (' y '.join(enteros), corto(t, 60)), 'confirmar que cada una hace su lado')
    return cobertura, huecos


# ---------------------------------------------------------------------------------------
# AN-2: reglas de la Historia en alguna Tarea
# ---------------------------------------------------------------------------------------

def ch_reglas(r, escs, desc, error_desc, ts):
    c = 'AN-2'
    de_hist = []          # (codigo, de donde)
    for e in escs:
        for x in historia.reglas_del_escenario(e):
            if x not in [y for y, _ in de_hist]:
                de_hist.append((x, 'Escenario "%s"' % corto(e['titulo'], 50)))
    if desc is not None:
        rn = historia.reglas_de_negocio(desc)
        if rn is None:
            r.aviso(c, 'la Descripcion no tiene el bloque "Reglas de negocio": solo se cruzan las '
                       'reglas del Gherkin')
        else:
            for it in rn:
                for x in it['citadas']:
                    if x not in [y for y, _ in de_hist]:
                        de_hist.append((x, 'bloque Reglas de negocio'))
    elif error_desc:
        r.no_auditable(c, error_desc, 'las reglas del bloque "Reglas de negocio" no se cruzaron')
    else:
        r.aviso(c, 'sin --descripcion: solo se cruzan las reglas del Gherkin, no las del bloque '
                   '"Reglas de negocio"')
    if not de_hist:
        r.aviso(c, 'la Historia no cita ninguna regla [RN-...]/[DEC-...]: no hay reglas que cruzar')
        return
    en_tareas = {}
    for T in ts:
        for x in T['d']['reglas_citadas']:
            en_tareas.setdefault(x, []).append(T['nombre'])
    faltan = 0
    for x, donde in de_hist:
        if not en_tareas.get(x):
            r.hallazgo(c, 'la regla %s de la Historia no la cita ninguna Tarea del set' % x,
                       'esta en: %s. Una regla sin Tarea es un hueco: preguntar a que Tarea va'
                       % donde)
            faltan += 1
    if not faltan:
        r.ok(c, 'las %d reglas de la Historia estan en alguna Tarea' % len(de_hist),
             ', '.join(x for x, _ in de_hist))
    extra = [x for x in en_tareas if x not in [y for y, _ in de_hist]]
    if extra:
        r.aviso(c, 'reglas que citan las Tareas y la Historia no: %s' % ', '.join(extra),
                'no es hallazgo: puede ser una regla compartida o un alcance de mas')


# ---------------------------------------------------------------------------------------
# AN-1: contratos que no se pisan
# ---------------------------------------------------------------------------------------

_METODOS = ('get', 'post', 'put', 'patch', 'delete', 'head', 'options')
_CLAVE_YAML = re.compile(r'''^(?:-\s+)?['"]?([^'":]+?)['"]?\s*:(?:\s|$)''')
_MENCION = re.compile(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/{}.\-:]*)')


def _yaml_lineas(s):
    res = []
    for raw in (s or '').replace('\r\n', '\n').replace('\t', '    ').split('\n'):
        st = raw.strip()
        if st and not st.startswith('#'):
            res.append((len(raw) - len(raw.lstrip(' ')), st, raw))
    return res


def _fin(ls, k):
    j = k + 1
    while j < len(ls) and ls[j][0] > ls[k][0]:
        j += 1
    return j


def _hijos(ls, k):
    ini, fin = (0, len(ls)) if k < 0 else (k + 1, _fin(ls, k))
    res, j = [], ini
    while j < fin:
        res.append(j)
        j = _fin(ls, j)
    return res


def _clave(st):
    m = _CLAVE_YAML.match(st)
    return m.group(1).strip() if m else None


def _bloque(ls, k):
    return '\n'.join(raw for _, _, raw in ls[k:_fin(ls, k)])


def norm_ruta(ruta):
    return re.sub(r'\{[^}]*\}', '{}', ruta.strip().rstrip('/').lower()) or '/'


def norm_yaml(s):
    """Para comparar dos fragmentos: sin comentarios, sin espacios, comillas unificadas."""
    lineas = [re.sub(r'(^|\s)#.*$', '', l) for l in (s or '').split('\n')]
    return re.sub(r'\s+', '', '\n'.join(lineas)).replace('"', "'")


def endpoints(contrato):
    """{(METODO, ruta_normalizada): (ruta, bloque)} de los 'paths:' del contrato."""
    ls = _yaml_lineas(contrato)
    res = {}
    for k in range(len(ls)):
        if _clave(ls[k][1]) != 'paths':
            continue
        for kr in _hijos(ls, k):
            ruta = _clave(ls[kr][1])
            if not ruta or not ruta.startswith('/'):
                continue
            for km in _hijos(ls, kr):
                met = (_clave(ls[km][1]) or '').lower()
                if met in _METODOS:
                    res[(met.upper(), norm_ruta(ruta))] = (ruta, _bloque(ls, km))
    return res


def esquemas(contrato):
    """{nombre: bloque} de 'components: schemas:' del contrato."""
    ls = _yaml_lineas(contrato)
    res = {}
    for k in range(len(ls)):
        if _clave(ls[k][1]) != 'schemas':
            continue
        for kn in _hijos(ls, k):
            nombre = _clave(ls[kn][1])
            if nombre:
                res[nombre] = _bloque(ls, kn)
    return res


def mencionados(seccion_html):
    """{(METODO, ruta_normalizada): ruta} de "POST /api/..." escritos en la prosa del contrato."""
    plano = texto.texto_plano(re.sub(r'<pre\b.*?</pre\s*>', ' ', seccion_html or '',
                                     flags=re.I | re.S))
    res = {}
    for m in _MENCION.finditer(plano):
        ruta = m.group(2).rstrip('.,;:')
        res[(m.group(1), norm_ruta(ruta))] = ruta
    return res


def _diferencia(a, b, contexto=35):
    n = min(len(a), len(b))
    k = next((i for i in range(n) if a[i] != b[i]), n)
    return a[max(0, k - contexto):k + contexto], b[max(0, k - contexto):k + contexto]


def ch_contratos(r, ts):
    c = 'AN-1'
    bloques, menciones, schemas = {}, {}, {}
    for T in ts:
        contrato = T['d']['contrato'] or ''
        for clave, (ruta, cuerpo) in endpoints(contrato).items():
            bloques.setdefault(clave, []).append((T, ruta, norm_yaml(cuerpo)))
        for clave, ruta in mencionados(T['contrato_html']).items():
            menciones.setdefault(clave, []).append((T, ruta))
        for nombre, cuerpo in esquemas(contrato).items():
            schemas.setdefault(nombre, []).append((T, norm_yaml(cuerpo)))
    choques = 0
    for clave in sorted(bloques):
        lst = bloques[clave]
        nombres = ', '.join(T['nombre'] for T, _, _ in lst)
        endpoint = '%s %s' % (clave[0], lst[0][1])
        if len(lst) < 2:
            continue
        textos = [x for _, _, x in lst]
        if len(set(textos)) == 1:
            r.aviso(c, 'repetido: %s esta definido igual en %s' % (endpoint, nombres),
                    'no choca, pero dos Tareas no deberian definir el mismo endpoint')
        else:
            a, b = next((x, y) for x in textos for y in textos if x != y)
            da, db = _diferencia(a, b)
            r.hallazgo(c, 'choque: %s esta definido distinto en %s' % (endpoint, nombres),
                       'primera diferencia (sin espacios ni comentarios): "%s" contra "%s"; '
                       'preguntar cual vale' % (da, db))
            choques += 1
    for clave in sorted(menciones):
        quienes = []
        for T, _, _ in bloques.get(clave, []):
            if T['nombre'] not in quienes:
                quienes.append(T['nombre'])
        for T, _ in menciones[clave]:
            if T['nombre'] not in quienes:
                quienes.append(T['nombre'])
        if len(quienes) >= 2 and len(bloques.get(clave, [])) < 2:
            r.aviso(c, '%s Tareas tocan el mismo endpoint %s %s: %s' % (len(quienes), clave[0],
                    menciones[clave][0][1], ', '.join(quienes)),
                    'sin dos bloques "paths:" que comparar; confirmar que extienden partes '
                    'distintas y no se pisan (AN-4)')
    for nombre in sorted(schemas):
        lst = schemas[nombre]
        if len(lst) < 2:
            continue
        nombres = ', '.join(T['nombre'] for T, _ in lst)
        if len(set(x for _, x in lst)) == 1:
            r.aviso(c, 'repetido: el schema %s esta igual en %s' % (nombre, nombres))
        else:
            r.aviso(c, 'el schema %s aparece distinto en %s' % (nombre, nombres),
                    'confirmar que una extiende a la otra y no se pisan')
    if not bloques:
        r.ok(c, 'ninguna Tarea define endpoints en un bloque "paths:": no hay contratos que choquen')
    elif not choques:
        r.ok(c, '%d endpoints definidos en "paths:", ninguno con dos contratos distintos'
             % len(bloques))


# ---------------------------------------------------------------------------------------
# AN-8: coherencia del test de integracion, Tarea por Tarea
# ---------------------------------------------------------------------------------------

def _integracion_minima(r, d, capa):
    """Si no se pudo cargar bin/auditar-tarea.py: el mismo chequeo, minimo."""
    ri = d['requiere_integracion']
    if ri is None:
        if capa != 'ui':
            r.aviso('x', 'el Alcance no declara "Requiere test de integracion: si / no"')
        return
    if ri:
        faltan = []
        if not any('integracion' in tarea.n(t['texto']) for t in d['tests']) and \
                'integracion' not in tarea.n(d['tests_intro']):
            faltan.append('un test de integracion en la lista')
        if not any('integracion' in tarea.n(s) for s in d['subtareas']):
            faltan.append('una subtarea que lo escriba')
        if not any('integracion' in tarea.n(x) for x in d['dod']):
            faltan.append('un item en la Definicion de terminado')
        for x in faltan:
            r.hallazgo('x', 'dice "Requiere test de integracion: si" y falta %s' % x,
                       'las tres o ninguna')
        if not faltan:
            r.ok('x', 'requiere integracion: hay test, subtarea e item de DoD')
    else:
        malos = [t['n'] for t in d['tests'] if t['etiqueta_integracion']]
        if malos:
            r.hallazgo('x', 'dice "Requiere test de integracion: no" y hay tests etiquetados '
                            '"Integracion": %s' % rangos(malos))
        else:
            r.ok('x', 'no requiere integracion y ningun test se etiqueta como tal')


def ch_integracion(r, ts, at):
    for T in ts:
        sub = rep.Reporte('x', T['ruta'])
        hecho = False
        if at is not None and hasattr(at, 'ch_integracion'):
            try:
                at.ch_integracion(sub, T['d'], T['capa'])
                hecho = True
            except Exception:  # noqa: BLE001 -- si cambio su forma, se recheckea a mano
                sub.renglones = []
        if not hecho:
            _integracion_minima(sub, T['d'], T['capa'])
        for nivel, _, det, ev in sub.renglones:
            r._agregar(nivel, 'AN-8', '%s: %s' % (T['nombre'], det), ev)


# ---------------------------------------------------------------------------------------
# AN-6: dependencias
# ---------------------------------------------------------------------------------------

def dependencias(dep_html):
    """(depende_de, de_esto_depende): tokens de cada parte de la seccion Dependencias."""
    dep, inv, modo = [], [], 'dep'
    for linea in texto.texto_plano(dep_html or '').split('\n'):
        nl = tarea.n(linea).lstrip(' -*')
        if nl.startswith('depende de'):
            modo = 'dep'
        elif nl.startswith('de esto depende'):
            modo = 'inv'
        elif nl.startswith('coordinacion'):
            modo = 'otra'
        if modo == 'otra':
            continue
        destino = dep if modo == 'dep' else inv
        for t in tokens_con_rangos(linea):
            if t not in destino:
                destino.append(t)
    return dep, inv


def ch_dependencias(r, ts, id_historia):
    c = 'AN-6'
    aristas = set()       # (A depende de B), entre Tareas del set
    for T in ts:
        if T['dep'] is None:
            if T['capa'] == 'back':
                r.aviso(c, '%s no tiene la seccion "Dependencias"' % etiqueta(T))
            continue
        dep, inv = dependencias(T['dep'])
        en_set, fuera = [], {'dep': [], 'inv': []}
        for modo, lista in (('dep', dep), ('inv', inv)):
            for t in lista:
                if t in T['ids'] or t == id_historia or t.startswith('H-'):
                    continue
                destinos = [U for U in ts if U is not T and t in U['ids']]
                if destinos:
                    for U in destinos:
                        aristas.add((id(T), id(U)) if modo == 'dep' else (id(U), id(T)))
                        x = '%s %s' % ('depende de' if modo == 'dep' else 'de esto depende',
                                       U['nombre'])
                        if x not in en_set:
                            en_set.append(x)
                elif mostrar(t) not in fuera[modo]:
                    fuera[modo].append(mostrar(t))
        if en_set:
            r.ok(c, '%s: %s (en el set)' % (T['nombre'], '; '.join(en_set)))
        if fuera['dep'] or fuera['inv']:
            partes = []
            if fuera['dep']:
                partes.append('depende de ' + ', '.join(fuera['dep']))
            if fuera['inv']:
                partes.append('de esto depende ' + ', '.join(fuera['inv']))
            r.aviso(c, '%s nombra Tareas fuera del set: verificar en el tablero que existan'
                    % T['nombre'], '; '.join(partes))
        if not dep and not inv:
            r.ok(c, '%s: Dependencias no nombra otras Tareas' % T['nombre'])
    por_id = dict((id(T), T) for T in ts)
    for a, b in sorted(aristas):
        if a < b and (b, a) in aristas:
            r.aviso(c, 'dependencia circular: %s y %s dependen una de la otra'
                    % (por_id[a]['nombre'], por_id[b]['nombre']),
                    'segun lo que dice la seccion Dependencias de cada una')


# ---------------------------------------------------------------------------------------
# AN-5: codigos que espera el front y no declara ningun back
# ---------------------------------------------------------------------------------------

_HTTP = re.compile(r'(?<![\w#.,/\-])([45]\d\d)(?![\w/\-]|[.,]\d)')
_CTX_HTTP = re.compile(r'\b(http|status|codigo|devuelve|devuelven|responde|respuesta|rechaza|'
                       r'error|errores|back|backend|servidor|servicio|api|msw|provisorio)\b')
_UNIDAD = re.compile(r'^\s*(caracteres|chars|ms|px|%|hs|horas|min|minutos|segundos|dias|km|'
                     r'metros)\b')


def codigos_esperados(T):
    """{codigo: [n de test]}: HTTP 4xx/5xx y codigos de error que nombran los tests."""
    res = {}
    for t in T['d']['tests']:
        x = t['texto']
        http = []
        for m in _HTTP.finditer(x):
            if _UNIDAD.match(tarea.n(x[m.end():m.end() + 15])):
                continue
            if _CTX_HTTP.search(tarea.n(x[max(0, m.start() - 40):m.end() + 40])):
                http.append(m.group(1))
        # Sin un HTTP en el test, solo cuenta un codigo de error declarado como tal: un
        # '"error":' o "codigo de error". "lanza un error" es del front, no del back.
        errs = tarea.codigos_error(x) if (http or re.search(r'"error"\s*:', x) or
                                          'codigo de error' in tarea.n(x)) else []
        for cod in http + errs:
            if t['n'] not in res.setdefault(cod, []):
                res[cod].append(t['n'])
    return res


def codigos_declarados(T):
    d = T['d']
    s = set(d['codigos_contrato'])
    s.update(re.findall(r'\b([A-Z][A-Z0-9_]{2,})\b', d['contrato'] or ''))
    for f in d['casos_error']:
        s.update(f['codigos_http'])
        s.update(f['codigos_error'])
        s.update(re.findall(r'\b([A-Z][A-Z0-9_]{2,})\b', f['payload'] + ' ' + f['codigo']))
    return s


def ch_errores(r, ts):
    c = 'AN-5'
    fronts = [T for T in ts if T['capa'] == 'front' and not T['e2e']]
    backs = [T for T in ts if T['capa'] == 'back']
    esperados = {}
    for T in fronts:
        for cod, tests in codigos_esperados(T).items():
            esperados.setdefault(cod, []).append('%s (test %s)' % (T['nombre'], rangos(tests)))
    if not esperados:
        r.ok(c, 'las Tareas de front no nombran codigos de error del back en sus tests')
        return
    if not backs:
        r.aviso(c, 'no hay Tarea de back en el set: los codigos que esperan las Tareas de front no '
                   'se pueden cruzar', ', '.join(sorted(esperados)))
        return
    declarados = set()
    for T in backs:
        declarados |= codigos_declarados(T)
    faltan = 0
    for cod in sorted(esperados):
        if cod not in declarados:
            r.aviso(c, 'el front espera %s y ninguna Tarea de back del set lo declara en su contrato '
                    'ni en Casos de error' % cod, '; '.join(esperados[cod]))
            faltan += 1
    if not faltan:
        r.ok(c, 'los %d codigos que esperan las Tareas de front estan declarados en algun back'
             % len(esperados), ', '.join(sorted(esperados)))


# ---------------------------------------------------------------------------------------
# Armado
# ---------------------------------------------------------------------------------------

def analizar(criterios, ruta_historia, tareas, descripcion=None, error_descripcion=None,
             pares=None, error_ids=None, fuente_ids=None, at=None):
    """Corre los chequeos del set. tareas: [(ruta, html | None, error | None)]. Sin efectos."""
    r = rep.Reporte(HERRAMIENTA, '%s + %d Tareas' % (ruta_historia or '<historia>', len(tareas)))
    if criterios is None or not criterios.strip():
        r.falta_insumo('la Historia (--historia) no se pudo leer o vino vacia')
        return r
    if not tareas:
        r.falta_insumo('no se paso ninguna Tarea: no hay set que analizar')
        return r
    pares = pares or []
    ts, vistos = [], set()
    for ruta, doc, error in tareas:
        clave = os.path.abspath(ruta).lower() if ruta else ''
        if clave and clave in vistos:
            r.aviso('set', 'el archivo %s se paso dos veces: se cuenta una' % ruta)
            continue
        vistos.add(clave)
        if error or doc is None:
            r.no_auditable('set', 'no se pudo leer la Tarea %s: el set queda incompleto'
                           % (ruta or '""'), error or '')
            continue
        if not doc.strip() or not re.search(r'<h3\b', doc, re.I):
            r.no_auditable('set', 'la Tarea %s vino vacia o sin ninguna seccion <h3>: no parece la '
                           'Descripcion de una Tarea; el set queda incompleto' % ruta)
            continue
        ts.append(leer_tarea(ruta, doc, pares))
    if not ts:
        r.falta_insumo('no se pudo leer ninguna Tarea del set')
        return r

    m = re.findall(r'(?<!\d)(\d{5,7})(?!\d)', os.path.basename(ruta_historia or ''))
    id_historia = '#' + m[0] if m else None
    if not id_historia:
        padres = [T['d']['sdd_padre'][0] for T in ts if T['d']['sdd_padre']]
        id_historia = ('#' + max(set(padres), key=padres.count)) if padres else None

    if error_ids:
        r.no_auditable('AN-7d', error_ids, 'los punteros "es de #X" se resuelven solo por el nombre '
                       'de cada archivo')
    elif fuente_ids:
        r.ok('set', 'quien es cada Tarea: nombre del archivo y %s' % ', '.join(fuente_ids))
    for T in ts:
        if not T['ids']:
            r.aviso('set', 'no se que #ID ni [T-nn] es %s: los punteros hacia ella no se pueden '
                    'resolver' % T['nombre'], 'pasar --ids con el mapa, o nombrar el archivo T-nn')
    for i, T in enumerate(ts):
        for U in ts[i + 1:]:
            comun = T['ids'] & U['ids']
            if comun:
                r.aviso('set', '%s y %s son la misma Tarea (%s): dos versiones en el mismo set?'
                        % (T['nombre'], U['nombre'], ', '.join(mostrar(x) for x in
                                                              sorted(comun, key=_orden_tok))))

    escs = historia.escenarios(criterios)
    _, huecos = ch_escenarios(r, escs, ts, id_historia)
    ch_reglas(r, escs, descripcion, error_descripcion, ts)
    ch_contratos(r, ts)
    ch_errores(r, ts)
    ch_dependencias(r, ts, id_historia)
    ch_integracion(r, ts, at)

    r.datos.update({
        'historia': id_historia or '',
        'escenarios': len(escs),
        'tareas': len(ts),
        'tareas_sin_leer': len(tareas) - len(ts),
        'escenarios_sin_cobertura': huecos,
        'filas_por_tarea': dict((T['nombre'], sum(1 for f in T['d']['sdd_filas']
                                                  if not f['no_lo_cubre'])) for T in ts),
    })
    r.para_el_auditor = list(PARA_EL_AUDITOR)
    return r


def _leer(ruta):
    """(contenido, None) o (None, motivo)."""
    if not ruta:
        return None, 'ruta vacia'
    try:
        return texto.leer(ruta), None
    except (OSError, UnicodeDecodeError) as e:
        return None, '%s: %s' % (type(e).__name__, e)


def correr(ruta_historia, rutas_tareas, ruta_ids=None, ruta_desc=None):
    criterios, _ = _leer(ruta_historia)
    tareas = []
    for ruta in rutas_tareas:
        doc, error = _leer(ruta)
        tareas.append((ruta, doc, error))
    desc, error_desc = None, None
    if ruta_desc:
        desc, error = _leer(ruta_desc)
        if error:
            error_desc = 'no se pudo leer --descripcion (%s)' % error
        elif not desc.strip():
            desc, error_desc = None, 'la Descripcion (--descripcion) vino vacia'
    pares, error_ids, fuentes = [], None, []
    if ruta_ids:
        try:
            pares = leer_ids(ruta_ids)
            fuentes.append(ruta_ids)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            error_ids = 'no se pudo leer --ids %s (%s)' % (ruta_ids, type(e).__name__)
    else:
        dirs = []
        for ruta in rutas_tareas:
            dd = os.path.dirname(os.path.abspath(ruta)) if ruta else None
            if dd and dd not in dirs:
                dirs.append(dd)
        for dd in dirs:
            for nombre in MAPAS_JUNTO:
                p = os.path.join(dd, nombre)
                if os.path.isfile(p):
                    try:
                        pares += leer_ids(p)
                        fuentes.append(p)
                    except (OSError, UnicodeDecodeError, ValueError):
                        continue
    return analizar(criterios, ruta_historia, tareas, desc, error_desc, pares, error_ids, fuentes,
                    _cargar_auditar_tarea())


def main(argv=None):
    p = argparse.ArgumentParser(
        prog='analizar-tareas.py',
        description='Analisis mecanico del set de Tareas de una Historia (solo lectura). 0 = sin '
                    'hallazgos, 1 = hallazgos o no auditables, 2 = SIN DATOS.')
    p.add_argument('--historia', required=True,
                   help='html de los Criterios de aceptacion de la Historia padre')
    p.add_argument('tareas', nargs='*', help='html de la Descripcion de cada Tarea del set')
    p.add_argument('--ids', help='JSON {"<archivo o clave>": "#NNNNNN" | "[T-nn]"}')
    p.add_argument('--descripcion', help='html de la Descripcion de la Historia (Reglas de negocio)')
    p.add_argument('--json', action='store_true', help='salida en JSON')
    p.add_argument('--salida', help='ademas, guarda el reporte en este archivo')
    a = p.parse_intermixed_args(argv)   # un pedido mal armado sale con 2: no midio nada
    try:
        r = correr(a.historia, a.tareas, a.ids, a.descripcion)
    except Exception as e:  # noqa: BLE001 -- a proposito: ningun error puede dar 0 ni 1
        r = rep.Reporte(HERRAMIENTA, a.historia)
        r.falta_insumo('el script fallo de una forma que no se esperaba (%s: %s). Esto NO es un '
                       'OK: es un bug de analizar-tareas, no del set' % (type(e).__name__, e))
    try:
        return rep.emitir(r, a.json, a.salida)
    except OSError as e:
        sys.stderr.write('analizar-tareas: no se pudo escribir --salida %s (%s)\n'
                         % (a.salida, type(e).__name__))
        rep.emitir(r, a.json, None)
        return rep.SIN_DATOS


if __name__ == '__main__':
    sys.exit(main())
