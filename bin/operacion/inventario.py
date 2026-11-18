"""Inventario de activos autorizados: lo unico que la IA puede tocar, y hasta donde. SOLO LECTURA.

Lee la tabla de cerebro-digital/<modulo>/operacion/inventario.md. Columnas (se reconocen por una
palabra del encabezado, sin acentos y sin importar el orden):

    Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA |
    Pruebas dinamicas | Ventana de cambios | Duenio (rol)

Lo que decide (AGENTS.md, GATE de SERVIDOR):
- un alias que no figura, o que pide mas nivel del que el inventario le da   -> FRENA
- no hay inventario, no se pudo leer, esta vacio o el alias figura dos veces -> SIN DATOS
- un nivel sin decidir (vacio, con la marca de pendiente o con otro texto)   -> 'nada'
- N3 no existe como nivel autorizable: lo hace una persona, nunca la IA
- una prueba dinamica activa contra produccion                               -> FRENA siempre
- un ambiente que no es desarrollo ni prueba (vacio, 'Productivo', 'PRD', 'staging', mal codificado) cuenta como
  PRODUCCION: ante la duda, la barrera mas dura. Si no es un nombre conocido, ademas es un problema del inventario

El alias se compara EXACTO (mayusculas incluidas): ante la duda, no esta autorizado.
Solo biblioteca estandar. ASCII puro.
"""

import glob
import os
import re
import unicodedata

OK, FRENA, SIN_DATOS = 'OK', 'FRENA', 'SIN DATOS'
NIVELES = ('nada', 'N0', 'N1', 'N2')
PRUEBAS = ('no', 'pasivo', 'activo')
TIPOS = ('servidor', 'url', 'cluster', 'imagen', 'nube', 'otro')
COLUMNAS = (('alias', 'alias'), ('tipo', 'tipo'), ('ambiente', 'ambiente'), ('destino', 'destino'),
            ('expuesto', 'expuesto'), ('criticidad', 'criticidad'), ('nivel', 'nivel_ia'),
            ('pruebas', 'pruebas_dinamicas'), ('ventana', 'ventana'), ('due', 'dueno'))
PRODUCCION = ('produccion', 'prod', 'production')
NO_PRODUCCION = ('desarrollo', 'dev', 'prueba', 'test', 'testing', 'qa')   # los de DEC-007 y sus sinonimos comunes
BOM = chr(0xFEFF)
RAYAS = '-' + chr(0x2013) + chr(0x2014)       # guion, raya corta y raya larga: una celda "vacia"
SEPARADOR = re.compile(r'^:?-{2,}:?$')


def plano(texto):
    """Minusculas, sin acentos, sin marcas de markdown y sin espacios de mas (para comparar encabezados y valores)."""
    t = unicodedata.normalize('NFD', texto)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[`*_]', '', t)).strip().lower()


def celdas(linea):
    """Las celdas de una fila de tabla markdown, o None si la linea no es una fila."""
    l = linea.strip()
    if not l.startswith('|'):
        return None
    l = l[1:-1] if l.endswith('|') else l[1:]
    return [c.strip() for c in l.split('|')]


def es_separador(fila):
    return bool(fila) and all(SEPARADOR.match(c) for c in fila)


def limpio(valor):
    return re.sub(r'[`*]', '', valor).strip()


def nivel_de(valor):
    """(nivel, decidido). Lo que no es exactamente nada, N0, N1 o N2 queda en 'nada' y sin decidir."""
    v = limpio(valor)
    for n in NIVELES:
        if v.lower() == n.lower():
            return n, True
    return 'nada', False


def pruebas_de(valor):
    v = plano(valor)
    return v if v in PRUEBAS else 'no'


def expuesto_de(valor):
    v = plano(valor)
    return True if v == 'si' else False if v == 'no' else None


def leer(ruta):
    """(activos, problemas). Lanza OSError si el archivo no se puede abrir.

    Cada activo: alias, tipo, ambiente, destino, expuesto (True, False o None), criticidad, nivel_ia,
    nivel_decidido, pruebas_dinamicas, ventana, dueno, linea. Una tabla cuenta solo si su ENCABEZADO
    (la fila que va justo antes de la linea de guiones) tiene la columna Alias: una tabla de ayuda que
    nombra las columnas en sus filas no agrega activos. Las filas de molde (alias vacio, con '<' o con
    una raya) se saltean: son el ejemplo de la plantilla, no un activo."""
    with open(ruta, 'rb') as h:
        texto = h.read().decode('utf-8', errors='replace').replace('\r\n', '\n')
    if texto.startswith(BOM):
        texto = texto[1:]
    lineas = texto.split('\n')
    filas = [celdas(l) for l in lineas]
    activos, problemas = [], []
    orden, en_tabla = None, False             # orden: columnas de la tabla en curso, o None si no es la del inventario
    for i, fila in enumerate(filas):
        n = i + 1
        if fila is None:
            orden, en_tabla = None, False     # la tabla termino
            continue
        if not en_tabla:
            en_tabla = True
            orden = None
            siguiente = filas[i + 1] if i + 1 < len(filas) else None
            encabezado = [plano(c) for c in fila]
            if siguiente is not None and es_separador(siguiente) and any(e.startswith('alias') for e in encabezado):
                orden = {}
                for j, e in enumerate(encabezado):
                    for palabra, clave in COLUMNAS:
                        if palabra in e and clave not in orden.values():
                            orden[j] = clave
                            break
            continue
        if orden is None or es_separador(fila):
            continue
        dato = dict((clave, '') for _, clave in COLUMNAS)
        for j, c in enumerate(fila):
            if j in orden:
                dato[orden[j]] = limpio(c)
        alias = dato['alias']
        if not alias or '<' in alias or '>' in alias or not alias.strip(RAYAS):
            continue
        nivel, decidido = nivel_de(dato['nivel_ia'])
        if limpio(dato['nivel_ia']).upper() == 'N3':
            problemas.append('linea %d: %s pide el nivel N3, que no es autorizable (lo hace una persona): queda en nada' % (n, alias))
        ambiente = plano(dato['ambiente'])
        if ambiente not in PRODUCCION + NO_PRODUCCION:
            problemas.append('linea %d: %s tiene el ambiente "%s", que no es desarrollo, prueba ni produccion: se trata '
                             'como produccion' % (n, alias, dato['ambiente']))
        tipo = plano(dato['tipo'])
        if tipo not in TIPOS:
            problemas.append('linea %d: %s tiene el tipo "%s"; los validos son %s' % (n, alias, dato['tipo'], ', '.join(TIPOS)))
        activos.append({'alias': alias, 'tipo': tipo, 'ambiente': ambiente, 'es_produccion': ambiente not in NO_PRODUCCION,
                        'destino': dato['destino'],
                        'expuesto': expuesto_de(dato['expuesto']), 'criticidad': plano(dato['criticidad']),
                        'nivel_ia': nivel, 'nivel_decidido': decidido, 'pruebas_dinamicas': pruebas_de(dato['pruebas_dinamicas']),
                        'ventana': dato['ventana'], 'dueno': dato['dueno'], 'linea': n})
    vistos = {}
    for a in activos:
        vistos.setdefault(a['alias'], []).append(a['linea'])
    for alias, donde in sorted(vistos.items()):
        if len(donde) > 1:
            problemas.append('el alias %s figura %d veces (lineas %s): no se puede saber cual vale' % (
                alias, len(donde), ', '.join(str(x) for x in donde)))
    return activos, problemas


def ubicar(raiz, modulo=''):
    """(ruta, motivo). La ruta del inventario del modulo, o None con el motivo."""
    base = os.path.join(raiz, 'cerebro-digital')
    if modulo:
        ruta = os.path.join(base, modulo, 'operacion', 'inventario.md')
        return (ruta, '') if os.path.isfile(ruta) else (None, 'no existe %s' % os.path.relpath(ruta, raiz))
    rutas = sorted(r for r in glob.glob(os.path.join(base, '*', 'operacion', 'inventario.md'))
                   if os.path.basename(os.path.dirname(os.path.dirname(r))) != 'configuracion-ia')
    if not rutas:
        return None, 'ningun modulo de cerebro-digital/ tiene operacion/inventario.md'
    if len(rutas) > 1:
        return None, 'hay %d inventarios (%s): hay que decir de cual modulo' % (
            len(rutas), ', '.join(os.path.basename(os.path.dirname(os.path.dirname(r))) for r in rutas))
    return rutas[0], ''


def en_el_cerebro(ruta, raiz):
    """True si la ruta esta adentro de <raiz>/cerebro-digital/: un inventario armado en otro lado (borrador/, una
    carpeta temporal) no autoriza nada."""
    base = os.path.normcase(os.path.realpath(os.path.join(raiz, 'cerebro-digital')))
    r = os.path.normcase(os.path.realpath(ruta))
    return r.startswith(base + os.sep)


def cargar(ruta):
    """(activos, motivo). activos es None cuando no hay de donde decidir (SIN DATOS), con su motivo."""
    if not ruta or not os.path.isfile(ruta):
        return None, 'no hay inventario de activos (%s)' % (ruta or 'sin ruta')
    try:
        activos, _ = leer(ruta)
    except OSError as e:
        return None, 'no se pudo leer el inventario: %s' % e
    if not activos:
        return None, 'el inventario no tiene ningun activo cargado (solo el molde): nada esta autorizado'
    return activos, ''


def buscar(ruta, alias):
    """(estado, activo, motivo): si <alias> figura en el inventario, una sola vez. No mira niveles."""
    activos, motivo = cargar(ruta)
    if activos is None:
        return SIN_DATOS, None, motivo
    iguales = [a for a in activos if a['alias'] == alias]
    if len(iguales) > 1:
        return SIN_DATOS, None, 'el alias %s figura %d veces en el inventario: no se puede saber cual vale' % (alias, len(iguales))
    if not iguales:
        return FRENA, None, '%s no esta en el inventario autorizado: para la IA no existe, ni para leerlo' % alias
    return OK, iguales[0], ''


def autorizar(ruta, alias, nivel='N0'):
    """(estado, activo, motivo) para tocar <alias> con el nivel pedido (N0 leer, N1, N2)."""
    if nivel == 'N3':
        return FRENA, None, 'N3 no lo hace la IA nunca: lo hace una persona, con el resumen a la vista'
    if nivel not in NIVELES[1:]:
        return SIN_DATOS, None, 'nivel desconocido: %s (va N0, N1 o N2)' % nivel
    estado, activo, motivo = buscar(ruta, alias)
    if estado != OK:
        return estado, activo, motivo
    if NIVELES.index(nivel) > NIVELES.index(activo['nivel_ia']):
        return FRENA, activo, 'el inventario autoriza %s hasta %s%s y se pidio %s' % (
            alias, activo['nivel_ia'], '' if activo['nivel_decidido'] else ' (nivel sin decidir)', nivel)
    return OK, activo, ''


def autorizar_prueba(ruta, alias, modo='pasivo'):
    """(estado, activo, motivo) para una prueba dinamica (pedidos a una aplicacion que corre) contra <alias>.
    La gobierna la columna Pruebas dinamicas, no el nivel: mandar pedidos no es entrar al servidor."""
    if modo not in PRUEBAS[1:]:
        return SIN_DATOS, None, 'modo desconocido: %s (va pasivo o activo)' % modo
    estado, activo, motivo = buscar(ruta, alias)
    if estado != OK:
        return estado, activo, motivo
    if activo['tipo'] != 'url':
        return FRENA, activo, '%s es de tipo %s: una prueba dinamica solo va contra un activo de tipo url' % (alias, activo['tipo'] or '?')
    if not re.match(r'^https?://[^\s/]+', activo['destino']):
        return SIN_DATOS, activo, '%s no tiene una URL exacta en la columna Destino' % alias
    if modo == 'activo' and activo['es_produccion']:
        return FRENA, activo, 'una prueba activa contra produccion no se corre nunca (el ambiente "%s" cuenta como produccion)' % (
            activo['ambiente'] or 'vacio')
    if PRUEBAS.index(modo) > PRUEBAS.index(activo['pruebas_dinamicas']):
        return FRENA, activo, 'el inventario autoriza para %s pruebas dinamicas "%s" y se pidio "%s"' % (
            alias, activo['pruebas_dinamicas'], modo)
    return OK, activo, ''
