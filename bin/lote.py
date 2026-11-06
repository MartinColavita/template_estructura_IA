#!/usr/bin/env python3
"""Modo lote (skill planificar-lote): la parte MECANICA, hecha siempre igual.

    python bin/lote.py preparar <tema> --ficha <ruta.md> [--fecha AAAAMMDD] [--raiz-output <dir>]
    python bin/lote.py item <carpeta> --clave T-01 [--tipo Tarea|Historia]
                       [--accion ALTA|PISA|RELACION|EXISTE] [--titulo "..."]
                       [--padre "#125063" | "[H-01]"] [--criterios-padre <ruta>] [--archivo <ruta>]
                       [--criterios <ruta>] [--puntos N] [--actividad Development] [--id 125280]
                       [--flujo F-04] [--ficha <ruta.md>] [--relacion "#ID" ...] [--dedup "..."]
                       [--gates "..."] [--cambia "..."] [--desde-json]
    python bin/lote.py mision <carpeta> redactar|auditar|corregir <clave> [<clave> ...] [--guardar]
    python bin/lote.py mision <carpeta> auditar set-<padre>          (ej. set-H-01, set-125063)
    python bin/lote.py auditar <carpeta> [--bin <dir>]
    python bin/lote.py cierre <carpeta>
    python bin/lote.py ids <carpeta> [--mapa mapa-ids.json]
    python bin/lote.py comparar <archivo_auditado> <archivo_azure> [--mapa mapa-ids.json]
                       [--campo System.Description]
    python bin/lote.py tiempos <carpeta> [<fase> inicio|fin] [--ahora AAAA-MM-DDTHH:MM]
                       fases: preparar, arranque, redactar, auditar, cierre, escribir
    python bin/lote.py estado <carpeta>

Codigos de salida, como el resto de bin/:
    0 = listo   1 = hay algo que arreglar (hallazgos, diferencias, faltantes, carpeta que ya
    existe)   2 = SIN DATOS (no se pudo leer un insumo, o el pedido esta mal armado)

POR QUE EXISTE. El modo lote (cerebro-digital/configuracion-ia/skills/planificar-lote/SKILL.md)
lo corre un modelo distinto en cada sesion, y cada modelo improvisaba: otros nombres de archivo,
otras misiones para los sub-agentes, otra tabla de cierre. Lo que es mecanico -armar la carpeta,
anotar los items, escribir la mision de cada agente, correr las auditorias de conteo, armar la
tabla, reemplazar las marcas [T-nn] por su #ID, comparar la tarjeta con lo auditado, medir el
tiempo- lo hace este script: el mismo pedido da siempre el mismo resultado, byte por byte.
Al modelo le queda lo que pide criterio.

QUE NO HACE. No usa la red. No escribe en Azure DevOps, ni en GitLab, ni en el Cerebro:
escribe solo dentro de la carpeta del lote (borrador/lote-<AAAAMMDD>-<tema>/, nunca versionada).
Escribir en el tablero sigue siendo de la IA, por el MCP, despues del "si" del cierre.

SUBCOMANDOS
  preparar  Crea borrador/lote-<fecha>-<tema>/ con CONTEXTO.md (esqueleto fijo de secciones),
            items.json, tiempos.json (marca el inicio de 'preparar'), auditorias/ y antes/. Lee
            el frontmatter de la ficha (fuente_maqueta) y su bloque de derivacion. Si la carpeta
            ya existe, no la pisa: sale 1.
  item      Agrega o actualiza UN item de items.json, por su clave (idempotente: el mismo
            pedido dos veces deja el mismo archivo). Al crearlo pide --tipo, --accion y --titulo;
            al actualizarlo cambia solo lo que se le pasa. --desde-json toma titulo, puntos,
            actividad y relaciones del <clave>.json que dejo el agente que redacto (lo que se
            pase por la linea de comandos gana). EXISTE = una Tarea ya cargada en el tablero,
            con su html guardado: no se escribe, solo entra al analisis del set de su padre.
  mision    Imprime la mision de un sub-agente: la plantilla de planificar-lote/misiones/<tipo>.md
            con los datos del item. Mismo item, mismo texto. "auditar set-<padre>" es la del
            auditor del conjunto de Tareas de un padre. --guardar la deja tambien en
            misiones/<clave>-<tipo>.md dentro del lote.
  auditar   Por item, en orden de clave: Tarea -> bin/auditar-tarea.py; Historia ->
            bin/auditar-historia.py; y por cada padre con 2 o mas Tareas (contando las EXISTE),
            bin/analizar-tareas.py (con --descripcion si el padre es una [H-nn] del lote).
            Deja auditorias/<clave>.json, .md y .huella.json (que version de cada insumo se
            audito). Un script que no esta o que falla es SIN DATOS, nunca OK.
  cierre    Escribe CIERRE.md con la tabla del cierre de planificar-lote, las secciones que
            salen de CONTEXTO.md, los F y P de los auditores y la pregunta final. Sale 1 si
            alguna fila no se escribe. La auditoria es OPCIONAL (se corre solo si se pide) y
            nunca frena una fila: si no se pidio, la columna dice "no se pidio"; si se pidio y
            algo no cierra, dice "NO SE SELLA: ..." y esa tarjeta se escribe sin sello.
  ids       Reemplaza [T-nn]/[H-nn] por #ID en cada archivo del lote y lo escribe en
            <carpeta>/<clave>.final.html (y <clave>-criterios.final.html); el original auditado
            no se toca. Sale 1 si queda una marca sin #ID.
  comparar  Fase 5, "verificar antes de sellar": el texto auditado (con el mapa aplicado) contra
            el de Azure, sin etiquetas y con los espacios normalizados. Un --mapa que no existe
            tal cual se busca en la carpeta del archivo auditado.
  tiempos   Marca inicio/fin de una fase, o informa las duraciones contra el objetivo. Las fases
            son las de planificar-lote: preparar, arranque, redactar, auditar, cierre, escribir.
  estado    Resumen de una pantalla: items, auditorias, sets, archivos que faltan, marcas.

LA HUELLA. Cada auditoria queda atada a la version que miro: el script guarda el sha256 de
cada insumo (auditorias/<clave>.huella.json) y la mision del auditor le pasa una firma corta
de esa version, que el auditor copia en su informe ("Huella: <firma>"). Si despues cambia un
archivo, el cierre marca NO SE SELLA en esa fila: lo auditado ya no es lo que se va a escribir,
asi que no se publica un sello que lo afirme (la fila se escribe igual).

ARCHIVOS DEL LOTE (la tabla de planificar-lote, mas los de este script)
  CONTEXTO.md               brief comun: alcance, fuentes, F, R, P, dedup, estado de tarjetas
  items.json                {"_esquema": {...}, "lote": {...}, "items": [...]}
  <clave>.html              Descripcion del item (la escribe el agente que redacta)
  <clave>-criterios.html    Historia: Criterios de aceptacion
  <clave>.json              lo que devuelve el agente que redacta (titulo, puntos, relaciones)
  auditorias/<clave>.json   resultado del script de auditoria (y .md, y .huella.json)
  auditorias/<clave>-auditor.md   informe del agente auditor (formato fijo: misiones/auditar.md:
                            "Veredicto:", "Huella:", secciones "## F" y "## P", un renglon "- "
                            por hallazgo; tambien se lee un renglon que empiece con "F:" o "P:")
  auditorias/set-<padre>.json     analizar-tareas sobre las Tareas de un mismo padre (y su
                            -auditor.md, con el mismo formato)
  antes/<id>.html           lo que tenia cada tarjeta que se PISA
  misiones/                 las misiones guardadas con --guardar
  CIERRE.md                 la tabla del cierre
  mapa-ids.json             {"[T-01]": "125272", ...}, despues de escribir
  <clave>.final.html        el texto con los #ID, el que se carga en la fase 5
  tiempos.json              {"fases": {"<fase>": [{"inicio": ISO, "fin": ISO | null}]}}

ESQUEMA DE CADA ITEM (items.json -> items[]; tambien queda escrito en "_esquema")
  clave            T-nn (Tarea) o H-nn (Historia); otra letra solo para RELACION y EXISTE
  tipo             Tarea | Historia
  accion           ALTA | PISA | RELACION | EXISTE
  titulo           el titulo tal como se va a escribir
  padre            "#ID" de una tarjeta que ya existe, o "[H-nn]" de una Historia del lote
  criterios_padre  Tarea: archivo con los Criterios del padre como van a quedar
                   (default para un padre [H-nn]: el "criterios" de ese item)
  archivo          Descripcion en HTML (default <clave>.html)
  criterios        Historia: Criterios de aceptacion en HTML (default <clave>-criterios.html)
  puntos           Puntos de historia, o null
  actividad        Tarea: Development, Testing, ...
  relaciones       lista de "#ID" / "[T-nn]" / "[H-nn]" (Related)
  id               #ID en Azure (obligatorio en PISA y EXISTE); null hasta que se escribe
  ficha, flujo     ficha fuente (default: la del lote) y su [F-nn]
  dedup, gates     opcionales, para las columnas Dedup y "GATES y 2b" del cierre (sin ellos: SIN DATOS)
  cambia           PISA: que cambia, en dos lineas (va a "Lo que se pisa")
Las rutas son relativas a la carpeta del lote, o al repo, o absolutas.

Solo biblioteca estandar. ASCII puro en este archivo: los acentos de lo que se escribe salen
de chr() (ver es()), igual que en bin/auditoria/.
"""

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from auditoria import cerebro, reporte, texto  # noqa: E402

RAIZ = cerebro.raiz_repo()
MISIONES = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'planificar-lote',
                        'misiones')
PENDIENTES = 'cerebro-digital/modulo-ejemplo/pendientes.md'

OK, ARREGLAR, SIN_DATOS = 0, 1, 2
TIPOS = ('Tarea', 'Historia')
ACCIONES = ('ALTA', 'PISA', 'RELACION', 'EXISTE')
ESCRIBIBLES = ('ALTA', 'PISA')
DEL_SET = ('ALTA', 'PISA', 'EXISTE')
TIPOS_MISION = ('redactar', 'auditar', 'corregir')
PALABRAS = {'redactar': 150, 'auditar': 200, 'corregir': 120}
VEREDICTOS = ('COMPLETA', 'CON HUECOS', 'NO AUDITABLE', 'CIERRA')
# (fase, minimo, maximo) en minutos: la tabla "Tiempos esperados" de planificar-lote.
FASES = (('preparar', 5, 5), ('arranque', 5, 5), ('redactar', 10, 12), ('auditar', 5, 8),
         ('cierre', 5, 5), ('escribir', 5, 5))
NOMBRES_FASES = ', '.join(f for f, _, _ in FASES)
OBJETIVO = (30, 40)

CAMPOS = ('clave', 'tipo', 'accion', 'titulo', 'padre', 'criterios_padre', 'archivo', 'criterios',
          'puntos', 'actividad', 'relaciones', 'id', 'ficha', 'flujo', 'dedup', 'gates', 'cambia')

ESQUEMA = {
    'clave': 'T-nn (Tarea) o H-nn (Historia); es la marca [T-nn]/[H-nn] en los textos',
    'tipo': 'Tarea | Historia',
    'accion': 'ALTA | PISA | RELACION | EXISTE (Tarea ya cargada: solo entra al set del padre)',
    'titulo': 'titulo tal como se va a escribir',
    'padre': '#ID de una tarjeta que ya existe, o [H-nn] de una Historia del lote',
    'criterios_padre': 'Tarea: archivo con los Criterios del padre como van a quedar',
    'archivo': 'Descripcion en HTML (default <clave>.html)',
    'criterios': 'Historia: Criterios de aceptacion en HTML (default <clave>-criterios.html)',
    'puntos': 'Puntos de historia, o null',
    'actividad': 'Tarea: Development | Testing | Design | Documentation | Deployment | Requirements',
    'relaciones': 'lista de #ID / [T-nn] / [H-nn] (Related)',
    'id': '#ID en Azure: obligatorio en PISA y EXISTE; null hasta que se escribe',
    'ficha': 'ficha fuente (default: la del lote)',
    'flujo': 'Historia: el [F-nn] de la ficha',
    'dedup': 'opcional: columna Dedup del cierre (N consultas, 0 cand. / #ID); sin el: SIN DATOS',
    'gates': 'opcional: columna GATES y 2b del cierre (OK / FRENA: cual); sin el: SIN DATOS',
    'cambia': 'PISA: que cambia, en dos lineas',
    '_rutas': 'relativas a la carpeta del lote, o al repo, o absolutas',
}

_SK = 'cerebro-digital/configuracion-ia/skills/'
_AZ = 'tablero/'
SKILLS = {
    'redactar-tarea': _SK + 'redactar-tarea/SKILL.md',
    'plantillas/tarea': _AZ + 'plantillas/tarea.md',
    'plantillas/historia-de-usuario': _AZ + 'plantillas/historia-de-usuario.md',
    'checklists/mapa-campos-azure': _AZ + 'checklists/mapa-campos-azure.md',
    'estimar-story-points': _SK + 'estimar-story-points/SKILL.md',
    'auditar-tarea': _SK + 'auditar-tarea/SKILL.md',
    'auditar-historia': _SK + 'auditar-historia/SKILL.md',
    'analizar-tareas': _SK + 'analizar-tareas/SKILL.md',
}
SKILLS_DE = {
    ('redactar', 'Tarea'): ('redactar-tarea', 'plantillas/tarea', 'checklists/mapa-campos-azure',
                            'estimar-story-points'),
    ('redactar', 'Historia'): ('redactar-tarea', 'plantillas/historia-de-usuario',
                               'checklists/mapa-campos-azure', 'estimar-story-points'),
    ('auditar', 'Tarea'): ('auditar-tarea',),
    ('auditar', 'Historia'): ('auditar-historia',),
    ('auditar', 'set'): ('analizar-tareas',),
    ('corregir', 'Tarea'): ('redactar-tarea', 'plantillas/tarea', 'checklists/mapa-campos-azure'),
    ('corregir', 'Historia'): ('redactar-tarea', 'plantillas/historia-de-usuario',
                               'checklists/mapa-campos-azure'),
}

# Acentos y signos de lo que se ESCRIBE (CONTEXTO.md, CIERRE.md, misiones), sin romper el ASCII
# de este archivo. En el codigo se escribe "Acci<o>n" y es() lo convierte.
_ES = (('<a>', chr(0xe1)), ('<e>', chr(0xe9)), ('<i>', chr(0xed)), ('<o>', chr(0xf3)),
       ('<u>', chr(0xfa)), ('<n>', chr(0xf1)), ('<I>', chr(0xcd)), ('<O>', chr(0xd3)),
       ('<?>', chr(0xbf)), ('<S>', chr(0xa7)), ('<!>', chr(0x26a0)), ('<.>', chr(0xb7)),
       ('<lq>', chr(0xab)), ('<rq>', chr(0xbb)))
AVISO = chr(0x26a0)


def es(s):
    for k, v in _ES:
        s = s.replace(k, v)
    return s


class Falla(Exception):
    """Corta el subcomando con un mensaje y un codigo (1 = arreglar, 2 = SIN DATOS)."""

    def __init__(self, codigo, mensaje):
        Exception.__init__(self, mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


# ---------------------------------------------------------------------------------------
# Archivos y rutas
# ---------------------------------------------------------------------------------------

def _leer_json(ruta):
    with io.open(ruta, encoding='utf-8-sig') as f:
        return json.load(f)


def _escribir(ruta, contenido):
    d = os.path.dirname(ruta)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(contenido)


def _escribir_json(ruta, datos):
    _escribir(ruta, json.dumps(datos, ensure_ascii=False, indent=2) + '\n')


def _barras(r):
    return r.replace(os.sep, '/') if r else r


def _adentro(ruta, base):
    """La ruta relativa a base (con /) si ruta esta adentro de base; si no, None."""
    try:
        rel = os.path.relpath(ruta, base)
    except ValueError:      # otra unidad, en Windows
        return None
    if rel == '.' or rel.startswith('..') or os.path.isabs(rel):
        return None
    return _barras(rel)


def _mostrar(ruta):
    """Como se muestra una ruta: relativa al repo si esta adentro; si no, absoluta."""
    if not ruta:
        return ''
    a = os.path.normpath(os.path.abspath(ruta))
    return _adentro(a, RAIZ) or _barras(a)


def _resolver(carpeta, ruta):
    """Ruta absoluta de algo anotado en items.json: primero el lote, despues el repo."""
    if not ruta:
        return None
    if os.path.isabs(ruta):
        return os.path.normpath(ruta)
    en_lote = os.path.join(os.path.abspath(carpeta), ruta)
    if os.path.exists(en_lote):
        return os.path.normpath(en_lote)
    en_raiz = os.path.join(RAIZ, ruta)
    if os.path.exists(en_raiz):
        return os.path.normpath(en_raiz)
    return os.path.normpath(en_lote)


def _para_guardar(carpeta, ruta):
    """Como se anota una ruta en items.json: relativa al lote, o al repo, o absoluta."""
    if not ruta:
        return None
    if not os.path.isabs(ruta):
        if os.path.exists(os.path.join(carpeta, ruta)) or not os.path.exists(ruta):
            return _barras(os.path.normpath(ruta))
        ruta = os.path.abspath(ruta)
    a = os.path.normpath(ruta)
    return _adentro(a, os.path.abspath(carpeta)) or _adentro(a, RAIZ) or _barras(a)


def _sha(ruta):
    try:
        with open(ruta, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (OSError, TypeError):
        return None


def _leer_texto(ruta):
    """El texto de un archivo, o None si no se puede leer."""
    if not ruta:
        return None
    try:
        return texto.leer(ruta)
    except (OSError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------------------
# items.json
# ---------------------------------------------------------------------------------------

def _orden(clave):
    """Orden natural de claves: T-2 antes que T-10."""
    return [(0, int(p), '') if p.isdigit() else (1, 0, p) for p in re.findall(r'\d+|\D+', clave)]


def _ordenados(items):
    return sorted(items, key=lambda i: _orden(i['clave']))


def _ordenar_campos(it):
    salida = {c: it.get(c) for c in CAMPOS}
    if salida['relaciones'] is None:
        salida['relaciones'] = []
    for k in sorted(it):
        if k not in salida:
            salida[k] = it[k]
    return salida


def _cargar(carpeta):
    if not os.path.isdir(carpeta):
        raise Falla(SIN_DATOS, 'SIN DATOS -- no existe la carpeta del lote: ' + carpeta)
    ruta = os.path.join(carpeta, 'items.json')
    try:
        datos = _leer_json(ruta)
    except (OSError, ValueError) as e:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer ' + _mostrar(ruta) + ' (' +
                    type(e).__name__ + ')')
    if (not isinstance(datos, dict) or not isinstance(datos.get('items'), list) or
            any(not isinstance(i, dict) or not i.get('clave') for i in datos['items'])):
        raise Falla(SIN_DATOS, 'SIN DATOS -- ' + _mostrar(ruta) + ' no tiene la forma esperada '
                    '(ver el esquema en bin/lote.py)')
    if not isinstance(datos.get('lote'), dict):
        datos['lote'] = {}
    for it in datos['items']:
        it.setdefault('tipo', None)
        it.setdefault('accion', None)
    return datos


def _guardar(carpeta, datos):
    items = [_ordenar_campos(i) for i in _ordenados(datos['items'])]
    _escribir_json(os.path.join(carpeta, 'items.json'),
                   {'_esquema': ESQUEMA, 'lote': datos.get('lote', {}), 'items': items})


def _buscar(datos, clave):
    for it in datos['items']:
        if it.get('clave') == clave:
            return it
    return None


def _items(datos, acciones=None):
    res = _ordenados(datos['items'])
    if acciones:
        res = [i for i in res if i.get('accion') in acciones]
    return res


# ---------------------------------------------------------------------------------------
# Huellas: que version de cada insumo se audito
# ---------------------------------------------------------------------------------------

def _insumos(carpeta, it, lote):
    """(rol, ruta absoluta) de lo que se audita de un item."""
    if it.get('tipo') == 'Tarea':
        roles = (('archivo', it.get('archivo')), ('criterios_padre', it.get('criterios_padre')))
    else:
        roles = (('archivo', it.get('archivo')), ('criterios', it.get('criterios')),
                 ('ficha', it.get('ficha') or lote.get('ficha')))
    return [(rol, _resolver(carpeta, r)) for rol, r in roles if r]


def _huella(insumos):
    return {rol: _sha(r) for rol, r in insumos}


def _firma(huella):
    """Firma corta de una huella: la que el auditor copia en su informe."""
    linea = '\n'.join(k + '=' + (huella[k] or '-') for k in sorted(huella))
    return hashlib.sha256(linea.encode('utf-8')).hexdigest()[:16]


def _cambios(ruta_huella, nueva):
    """None si coincide; ['?'] si no hay huella guardada; si no, los insumos que cambiaron."""
    try:
        vieja = _leer_json(ruta_huella)
    except (OSError, ValueError):
        return ['?']
    if not isinstance(vieja, dict):
        return ['?']
    cambiados = sorted(k for k in set(vieja) | set(nueva) if vieja.get(k) != nueva.get(k))
    return cambiados or None


def _grupos(datos):
    """[(padre, [Tareas])] de los padres con 2 o mas Tareas (contando las EXISTE), en orden."""
    g = {}
    for it in _items(datos, DEL_SET):
        if it.get('tipo') == 'Tarea' and it.get('padre'):
            g.setdefault(it['padre'], []).append(it)
    return [(p, ts) for p, ts in sorted(g.items(), key=lambda x: _orden(x[0])) if len(ts) >= 2]


def _nombre_set(padre):
    return 'set-' + padre.strip('[]#')


def _insumos_set(carpeta, datos, padre, tareas):
    """(rol, ruta absoluta) de lo que analiza el set: Criterios, Descripcion y cada Tarea."""
    crit = next((t.get('criterios_padre') for t in tareas if t.get('criterios_padre')), None)
    desc = None
    if padre.startswith('['):
        ph = _buscar(datos, padre[1:-1])
        if ph and ph.get('accion') in ESCRIBIBLES and ph.get('archivo'):
            desc = ph['archivo']
    roles = [('criterios', crit), ('descripcion', desc)] + [(t['clave'], t.get('archivo'))
                                                            for t in tareas]
    return [(rol, _resolver(carpeta, r)) for rol, r in roles if r]


# ---------------------------------------------------------------------------------------
# preparar
# ---------------------------------------------------------------------------------------

SECCIONES_CONTEXTO = (
    ('Alcance',
     'Una l<i>nea por <i>tem: clave <.> acci<o>n <.> t<i>tulo <.> padre. Es lo que muestra el '
     'arranque.'),
    ('Fuentes le<i>das',
     'Agregar cada ruta le<i>da: reglas del Cerebro, contratos de Tareas ya cargadas.'),
    ('Decidido por fuente (F)',
     'Una l<i>nea por decisi<o>n: qu<e> se decidi<o> <.> fuente (ruta, regla, maqueta o '
     '<lq>respuesta del arranque<rq>) <.> arreglo exacto. Lo respondido en el arranque pasa '
     'ac<a>. Sin nada: <lq>Ninguno.<rq>'),
    ('Recomendaciones aplicadas (R)',
     'Una l<i>nea por recomendaci<o>n t<e>cnica: qu<e> <.> por qu<e>. No decide c<o>digos '
     'HTTP, c<o>digos de error, n<u>meros de regla ni valores de negocio, y no se guarda en el '
     'Cerebro. Sin nada: <lq>Ninguno.<rq>'),
    ('Preguntas (P)',
     'P-001 <.> pregunta <.> Recomiendo: ... Despu<e>s del arranque quedan ac<a> s<o>lo las que '
     'no se contestaron (lo respondido pasa a F). Sin nada: <lq>Ninguno.<rq>'),
    ('Dedup por <i>tem',
     'Una l<i>nea por <i>tem: clave <.> consultas corridas <.> candidatos (#ID y estado) <.> '
     'veredicto. Sin MCP: SIN DATOS. El resumen de cada fila va con lote.py item --dedup.'),
    ('Estado de las tarjetas a editar',
     'Una l<i>nea por tarjeta que se pisa o de la que cuelga algo: #ID <.> Estado <.> Ruta de '
     'iteraci<o>n <.> Asignado <.> System.Rev (le<i>do en la fase 0). Sin nada: '
     '<lq>Ninguno.<rq>'),
    ('Conocimiento para el Cerebro',
     'Lo que fijaron las respuestas del arranque: qu<e> <.> destino en el Cerebro. Lo aplicado '
     'por R no va ac<a>. Sin nada: <lq>Ninguno.<rq>'),
)


def _contexto(nombre, ficha, maqueta, deriv):
    o = [es('# Contexto del lote ') + nombre, '',
         es('<!-- Brief com<u>n del lote (planificar-lote, fase 0). Lo leen los agentes que '
            'redactan, no los que auditan. Las secciones no se borran: vac<i>a no se distingue '
            'de <lq>nadie la mir<o><rq>. lote.py cierre copia de ac<a> F, R, P y el '
            'Conocimiento para el Cerebro. -->'), '']
    for titulo, guia in SECCIONES_CONTEXTO:
        o += ['## ' + es(titulo), '']
        if titulo.startswith('Fuentes'):
            o.append('- Ficha: `' + (ficha or '?') + '`')
            if maqueta:
                o.append(es('- Maqueta vigente (`fuente_maqueta` de la ficha): `') + maqueta + '`')
            else:
                o.append(es('- <!> La ficha no cita `fuente_maqueta`: ninguna maqueta decide.'))
            if deriv is None:
                o.append(es('- <!> La ficha no tiene el bloque <lq>Derivaci<o>n a backlog<rq>: '
                            'no se derivan Historias de ella (va a curaci<o>n).'))
            elif not deriv.get('F'):
                o.append(es('- <!> El bloque <lq>Derivaci<o>n a backlog<rq> no enumera Flujos '
                            '[F-nn].'))
            else:
                for clave, f in deriv['F'].items():
                    partes = ['[' + clave + '] ' + f.get('titulo', '')]
                    if f.get('capacidad'):
                        partes.append('capacidad: ' + f['capacidad'])
                    if f.get('reglas'):
                        partes.append('reglas: ' + ', '.join(f['reglas']))
                    o.append('- ' + es(' <.> ').join(partes))
            o.append('')
        o += [es('<!-- ' + guia + ' -->'), '']
    return '\n'.join(o)


def cmd_preparar(a):
    tema = (a.tema or '').strip().lower()
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', tema):
        raise Falla(SIN_DATOS, "lote: el tema '" + str(a.tema) + "' no sirve: solo minusculas, "
                    "numeros y guiones (ej. alta-reservas)")
    fecha = a.fecha or datetime.date.today().strftime('%Y%m%d')
    try:
        bien = len(fecha) == 8 and fecha.isdigit() and bool(
            datetime.datetime.strptime(fecha, '%Y%m%d'))
    except ValueError:
        bien = False
    if not bien:
        raise Falla(SIN_DATOS, "lote: la fecha '" + fecha + "' no es AAAAMMDD")
    try:
        ficha = cerebro.leer_ficha(a.ficha)
    except (OSError, UnicodeDecodeError) as e:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer la ficha ' + a.ficha + ' (' +
                    type(e).__name__ + '). Sin ficha no se prepara el lote.')
    raiz_out = os.path.abspath(a.raiz_output or os.path.join(RAIZ, 'borrador'))
    nombre = 'lote-' + fecha + '-' + tema
    carpeta = os.path.join(raiz_out, nombre)
    if os.path.exists(carpeta):
        raise Falla(ARREGLAR, 'lote: ya existe ' + _mostrar(carpeta) + '. No se pisa: puede tener '
                    'el trabajo de otro lote. Usa otro tema, o seguila con los otros subcomandos.')
    os.makedirs(os.path.join(carpeta, 'auditorias'))
    os.makedirs(os.path.join(carpeta, 'antes'))
    maqueta = ficha['frontmatter'].get('fuente_maqueta') or None
    ruta_ficha = _para_guardar(carpeta, a.ficha)
    _escribir(os.path.join(carpeta, 'CONTEXTO.md'),
              _contexto(nombre, ruta_ficha, maqueta, ficha['derivacion']))
    _guardar(carpeta, {'lote': {'tema': tema, 'fecha': fecha, 'ficha': ruta_ficha,
                                'maqueta': maqueta}, 'items': []})
    ahora = _ahora(None)
    _escribir_json(os.path.join(carpeta, 'tiempos.json'),
                   {'fases': {'preparar': [{'inicio': _iso(ahora), 'fin': None}]}})
    c = _mostrar(carpeta)
    print('Lote preparado: ' + c)
    print('  CONTEXTO.md, items.json, tiempos.json, auditorias/, antes/')
    if maqueta:
        print('  Maqueta vigente (fuente_maqueta): ' + maqueta)
    else:
        print('  AVISO: la ficha no cita fuente_maqueta: ninguna maqueta decide.')
    if ficha['derivacion'] is None:
        print("  AVISO: la ficha no tiene el bloque 'Derivacion a backlog': no se derivan "
              "Historias de ella.")
    print("  Tiempo: 'preparar' empezo a las " + ahora.strftime('%H:%M') + '.')
    print('Siguiente: completar CONTEXTO.md, cargar cada item con')
    print('  python bin/lote.py item ' + c + ' --clave T-01 --tipo Tarea --accion ALTA '
          '--titulo "..." --padre "[H-01]"')
    print('y al terminar la fase 0:  python bin/lote.py tiempos ' + c + ' preparar fin')
    return OK


# ---------------------------------------------------------------------------------------
# item
# ---------------------------------------------------------------------------------------

def _ref(valor, que):
    """'#125063' / '125063' -> '#125063';  'H-01' / '[H-01]' -> '[H-01]'."""
    v = (valor or '').strip()
    if not v:
        return None
    m = re.match(r'^\[?([THth])-([0-9]+)\]?$', v)
    if m:
        return '[' + m.group(1).upper() + '-' + m.group(2) + ']'
    d = v.lstrip('#')
    if d.isascii() and d.isdigit():
        return '#' + d
    raise Falla(SIN_DATOS, 'lote: ' + que + " '" + valor + "' no es un #ID ni una marca "
                "[T-nn] / [H-nn]")


def _id(valor):
    d = (valor or '').strip().lstrip('#')
    if not (d.isascii() and d.isdigit()):
        raise Falla(SIN_DATOS, "lote: --id '" + str(valor) + "' no es un #ID")
    return d


def _numero(valor):
    try:
        n = float(str(valor).replace(',', '.'))
    except ValueError:
        raise Falla(SIN_DATOS, "lote: --puntos '" + str(valor) + "' no es un numero")
    if n < 0:
        raise Falla(SIN_DATOS, 'lote: --puntos no puede ser negativo')
    return int(n) if n == int(n) else n


def _criterios_del_padre(datos, padre):
    """Default de criterios_padre: el archivo de Criterios de la Historia [H-nn] del lote."""
    if padre and padre.startswith('['):
        clave = padre[1:-1]
        p = _buscar(datos, clave)
        if p and p.get('criterios'):
            return p['criterios']
        return clave + '-criterios.html'
    return None


def _tipo(v):
    for t in TIPOS:
        if t.lower() == v.strip().lower():
            return t
    raise argparse.ArgumentTypeError('tiene que ser Tarea o Historia')


def _accion(v):
    s = texto.sin_acentos(v.strip()).upper()
    if s in ACCIONES:
        return s
    raise argparse.ArgumentTypeError('tiene que ser ALTA, PISA, RELACION o EXISTE')


def _desde_json(carpeta, clave):
    """titulo, puntos, actividad y relaciones del <clave>.json que dejo el agente que redacto."""
    ruta = os.path.join(carpeta, clave + '.json')
    try:
        d = _leer_json(ruta)
    except (OSError, ValueError) as e:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer ' + _mostrar(ruta) + ' (' +
                    type(e).__name__ + ')')
    if not isinstance(d, dict):
        raise Falla(SIN_DATOS, 'SIN DATOS -- ' + _mostrar(ruta) + ' no es un objeto json')
    if d.get('clave') and str(d['clave']).strip().strip('[]').upper() != clave:
        raise Falla(ARREGLAR, 'lote: ' + _mostrar(ruta) + " dice clave '" + str(d['clave']) +
                    "', no " + clave)
    rel = d.get('relaciones')
    if rel is not None and not isinstance(rel, list):
        raise Falla(SIN_DATOS, 'SIN DATOS -- en ' + _mostrar(ruta) + ' "relaciones" no es una lista')
    return d


def cmd_item(a):
    carpeta = a.carpeta
    datos = _cargar(carpeta)
    clave = a.clave.strip().strip('[]').upper()
    if not re.match(r'^[A-Z]-[0-9]{2,3}$', clave):
        raise Falla(SIN_DATOS, "lote: la clave '" + a.clave + "' no sirve: T-nn (Tarea) o H-nn "
                    "(Historia), como T-01")
    desde = _desde_json(carpeta, clave) if a.desde_json else {}
    titulo = a.titulo if a.titulo is not None else desde.get('titulo')
    puntos = a.puntos if a.puntos is not None else desde.get('puntos')
    actividad = a.actividad if a.actividad is not None else desde.get('actividad')
    relaciones = a.relacion if a.relacion is not None else desde.get('relaciones')

    it = _buscar(datos, clave)
    nuevo = it is None
    if nuevo:
        faltan = [n for n, v in (('--tipo', a.tipo), ('--accion', a.accion), ('--titulo', titulo))
                  if not v]
        if faltan:
            raise Falla(ARREGLAR, 'lote: ' + clave + ' es nuevo y le falta ' + ', '.join(faltan))
        it = {c: None for c in CAMPOS}
        it['clave'], it['relaciones'] = clave, []
    else:
        it = dict(it)
    if a.tipo:
        it['tipo'] = a.tipo
    if a.accion:
        it['accion'] = a.accion
    if titulo is not None:
        it['titulo'] = str(titulo).strip()
    if a.padre is not None:
        default_viejo = _criterios_del_padre(datos, it.get('padre'))
        it['padre'] = _ref(a.padre, '--padre')
        if a.criterios_padre is None and it.get('criterios_padre') in (None, default_viejo):
            it['criterios_padre'] = _criterios_del_padre(datos, it['padre'])
    if a.criterios_padre is not None:
        it['criterios_padre'] = _para_guardar(carpeta, a.criterios_padre)
    if a.archivo is not None:
        it['archivo'] = _para_guardar(carpeta, a.archivo)
    if a.criterios is not None:
        it['criterios'] = _para_guardar(carpeta, a.criterios)
    if puntos is not None:
        it['puntos'] = _numero(puntos)
    if actividad is not None:
        it['actividad'] = str(actividad).strip() or None
    if a.id is not None:
        it['id'] = _id(a.id)
    if a.flujo is not None:
        f = a.flujo.strip().strip('[]').upper()
        if not re.match(r'^F-[0-9]+$', f):
            raise Falla(SIN_DATOS, "lote: --flujo '" + a.flujo + "' no es un F-nn")
        it['flujo'] = f
    if a.ficha is not None:
        it['ficha'] = _para_guardar(carpeta, a.ficha)
    if relaciones is not None:
        rel = []
        for r in relaciones:
            x = _ref(str(r), '--relacion')
            if x and x not in rel:
                rel.append(x)
        it['relaciones'] = rel
    for campo in ('dedup', 'gates', 'cambia'):
        v = getattr(a, campo)
        if v is not None:
            it[campo] = v.strip() or None

    if it['accion'] != 'RELACION':
        if not it.get('archivo'):
            it['archivo'] = clave + '.html'
        if it['tipo'] == 'Historia' and not it.get('criterios'):
            it['criterios'] = clave + '-criterios.html'
    if not it.get('ficha'):
        it['ficha'] = datos['lote'].get('ficha')
    if it['accion'] in ESCRIBIBLES:
        letra = {'Tarea': 'T', 'Historia': 'H'}[it['tipo']]
        if clave[0] != letra:
            raise Falla(ARREGLAR, 'lote: ' + clave + ' es ' + it['tipo'] + ': su clave tiene que '
                        'empezar con ' + letra + '- (la marca del texto es [' + letra + '-nn])')
    if it['accion'] == 'PISA' and not it.get('id'):
        raise Falla(ARREGLAR, 'lote: ' + clave + ' es PISA: hace falta --id de la tarjeta que se '
                    'pisa (su ANTES va en antes/<id>.html)')
    if it['accion'] == 'EXISTE':
        if it['tipo'] != 'Tarea':
            raise Falla(ARREGLAR, 'lote: EXISTE es para una Tarea ya cargada que entra al set de '
                        'su padre; ' + clave + ' es ' + str(it['tipo']))
        if not it.get('id'):
            raise Falla(ARREGLAR, 'lote: ' + clave + ' es EXISTE: hace falta --id de la Tarea ya '
                        'cargada')

    if nuevo:
        datos['items'].append(it)
    else:
        datos['items'] = [it if i.get('clave') == clave else i for i in datos['items']]
    _guardar(carpeta, datos)
    print(('agregado: ' if nuevo else 'actualizado: ') + clave)
    print(json.dumps(_ordenar_campos(it), ensure_ascii=False, indent=2))
    if desde.get('padre') and _ref(str(desde['padre']), 'padre del json') != it.get('padre'):
        print('AVISO: ' + clave + '.json dice padre ' + str(desde['padre']) + ' y items.json ' +
              str(it.get('padre')) + ': no se cambio; revisar.')
    if it['tipo'] == 'Tarea' and it['accion'] != 'RELACION' and not it.get('padre'):
        print('AVISO: ' + clave + ' no tiene --padre: sin padre no se audita contra un Gherkin.')
    if it['accion'] == 'PISA' and it.get('id') and not os.path.exists(
            os.path.join(carpeta, 'antes', it['id'] + '.html')):
        print('AVISO: falta antes/' + it['id'] + '.html: sin el ANTES guardado la fila no se '
              'escribe.')
    if it['accion'] == 'EXISTE' and not os.path.isfile(_resolver(carpeta, it['archivo'])):
        print('AVISO: falta ' + it['archivo'] + ': sin el html guardado del tablero, el set no la '
              'puede analizar.')
    return OK


# ---------------------------------------------------------------------------------------
# mision
# ---------------------------------------------------------------------------------------

_PH = re.compile(r'\{([a-z_]+)\}')


def _render(plantilla, valores, nombre):
    faltan = sorted(set(k for k in _PH.findall(plantilla) if k not in valores))
    if faltan:
        raise Falla(SIN_DATOS, 'lote: la plantilla ' + nombre + ' usa {' + '}, {'.join(faltan) +
                    '}, que lote.py no conoce')
    return _PH.sub(lambda m: valores[m.group(1)], plantilla)


def _ruta_md(ruta):
    return '`' + ruta + '`'


TXT_REGLAS = ('Las reglas [RN-...] / [DEC-...] que cita, s<o>lo en el archivo del Cerebro donde '
              'est<a> cada una (`git grep -n <c<o>digo> -- cerebro-digital`).')


def _txt_maqueta(maqueta):
    if maqueta:
        return (_ruta_md(maqueta) + ' <.> la maqueta vigente (la que la ficha cita en '
                '`fuente_maqueta`)')
    return ('<!> La ficha no cita `fuente_maqueta`: ninguna maqueta decide. Lo que sea '
            'comportamiento de pantalla y no tenga otra fuente es una P.')


def _skills(clave_skills):
    return es('\n'.join('- **' + s + '** <.> `' + SKILLS[s] + '`' for s in SKILLS_DE[clave_skills]))


def _valores_mision(datos, carpeta, it, mision):
    c = os.path.abspath(carpeta)
    lote = datos['lote']
    clave, tipo = it['clave'], it['tipo']

    def m(ruta):
        return _mostrar(_resolver(c, ruta)) if ruta else None

    contexto = _mostrar(os.path.join(c, 'CONTEXTO.md'))
    ficha = m(it.get('ficha') or lote.get('ficha'))
    maqueta = lote.get('maqueta')
    archivo = m(it.get('archivo'))
    criterios = m(it.get('criterios'))
    crit_padre = m(it.get('criterios_padre'))
    padre = it.get('padre') or '(sin padre)'
    flujo = it.get('flujo')
    script = _mostrar(os.path.join(c, 'auditorias', clave + '.md'))
    informe = _mostrar(os.path.join(c, 'auditorias', clave + '-auditor.md'))
    json_item = _mostrar(os.path.join(c, clave + '.json'))
    antes = (_mostrar(os.path.join(c, 'antes', it['id'] + '.html'))
             if it.get('accion') == 'PISA' and it.get('id') else None)

    leer, salida = [], []

    def lee(s):
        leer.append('- ' + es(s))

    def sale(s):
        salida.append('- ' + es(s))

    txt_ficha = ((_ruta_md(ficha) + ' <.> la ficha fuente' +
                  (' (flujo [' + flujo + '])' if flujo else '')) if ficha else
                 '<!> El <i>tem no tiene ficha fuente.')
    if crit_padre:
        txt_crit_padre = (_ruta_md(crit_padre) + ' <.> los Criterios de aceptaci<o>n de la '
                          'Historia padre ' + padre + ', como van a quedar')
    else:
        txt_crit_padre = ('<!> No hay archivo con los Criterios de la Historia padre ' + padre +
                          ': sin ellos no se mapean los Escenarios. Es una P.')

    if mision == 'redactar':
        lee(_ruta_md(contexto) + ' <.> el brief com<u>n del lote: alcance, fuentes, decisiones F '
            'y R, preguntas')
        lee(txt_ficha)
        lee(_txt_maqueta(maqueta))
        if tipo == 'Tarea':
            p = it.get('padre')
            if p and p.startswith('['):
                ph = _buscar(datos, p[1:-1])
                desc = m(ph.get('archivo') if ph else p[1:-1] + '.html')
                lee(_ruta_md(desc) + ' <.> la Descripci<o>n de la Historia padre ' + p +
                    ' (borrador del lote)')
            lee(txt_crit_padre)
            if p:
                for h in _items(datos, DEL_SET):
                    if h['clave'] == clave or h.get('tipo') != 'Tarea' or h.get('padre') != p:
                        continue
                    if h.get('accion') == 'EXISTE':
                        lee(_ruta_md(m(h.get('archivo'))) + ' <.> Tarea ya cargada #' +
                            str(h.get('id')) + ' <lq>' + (h.get('titulo') or '') + '<rq>: su '
                            'contrato manda (no lo pises ni lo repitas)')
                    else:
                        lee(_ruta_md(m(h.get('archivo'))) + ' <.> Tarea hermana ' + h['clave'] +
                            ' <lq>' + (h.get('titulo') or '') + '<rq>, si ya est<a> escrita: '
                            'no repitas ni pises su contrato')
        if antes:
            lee(_ruta_md(antes) + ' <.> lo que la tarjeta #' + it['id'] + ' tiene hoy (el ANTES): '
                'respet<a> su intenci<o>n')
        sale(_ruta_md(archivo) + ' <.> la Descripci<o>n, en HTML')
        if tipo == 'Historia':
            sale(_ruta_md(criterios) + ' <.> los Criterios de aceptaci<o>n: Gherkin en espa<n>ol, '
                 'en HTML')
        sale(_ruta_md(json_item) + ' <.> t<i>tulo, tipo, padre, puntos, actividad y relaciones')
    elif mision == 'auditar':
        if tipo == 'Tarea':
            lee(_ruta_md(archivo) + ' <.> el borrador de la Tarea')
            lee(txt_crit_padre)
        else:
            lee(_ruta_md(archivo) + ' <.> la Descripci<o>n del borrador')
            lee(_ruta_md(criterios) + ' <.> los Criterios de aceptaci<o>n del borrador')
            lee(txt_ficha)
            lee(_txt_maqueta(maqueta))
            lee(_ruta_md(PENDIENTES) + ' <.> los pendientes del Cerebro (los P-nnn que cite la '
                'Historia)')
        lee(_ruta_md(script) + ' <.> el chequeo mec<a>nico (lote.py auditar)')
        lee(TXT_REGLAS)
        sale(_ruta_md(informe) + ' <.> tu informe, con el formato de abajo')
    else:
        lee(_ruta_md(archivo) + ' <.> el borrador (la Descripci<o>n)')
        if tipo == 'Historia':
            lee(_ruta_md(criterios) + ' <.> los Criterios de aceptaci<o>n del borrador')
        lee(_ruta_md(informe) + ' <.> el informe del auditor: los F a aplicar')
        lee(_ruta_md(script) + ' <.> el chequeo mec<a>nico')
        lee(_ruta_md(contexto) + ' <.> el brief del lote, para las fuentes de cada F')
        lee('Las fuentes que cita cada F, y s<o>lo esas.')
        sale(_ruta_md(archivo) + ' <.> lo pis<a>s con la versi<o>n corregida')
        if tipo == 'Historia':
            sale(_ruta_md(criterios) + ' <.> <i>dem, si un F lo toca')
        sale(_ruta_md(json_item) + ' <.> s<o>lo si un F cambia el t<i>tulo o los puntos')

    return {
        'clave': clave,
        'tipo': tipo,
        'accion': it['accion'],
        'titulo': it.get('titulo') or '',
        'padre': padre,
        'archivo': archivo or '',
        'criterios': criterios or 'no aplica',
        'criterios_padre': crit_padre or es('(no hay archivo: es una P)'),
        'contexto': contexto,
        'ficha': ficha or es('(sin ficha)'),
        'maqueta': maqueta or es('(la ficha no cita `fuente_maqueta`: ninguna maqueta decide)'),
        'flujo': flujo or '-',
        'carpeta': _mostrar(c),
        'auditoria': script,
        'informe': informe,
        'leer': '\n'.join(leer),
        'skills': _skills((mision, tipo)),
        'salida': '\n'.join(salida),
        'informe_max_palabras': str(PALABRAS[mision]),
        'huella': _firma(_huella(_insumos(c, it, lote))),
        'veredictos': 'COMPLETA | CON HUECOS | NO AUDITABLE',
        'aprobado': 'COMPLETA',
    }


def _valores_set(datos, carpeta, padre, tareas):
    """Valores de la mision del auditor del conjunto de Tareas de un padre."""
    c = os.path.abspath(carpeta)
    lote = datos['lote']
    nombre = _nombre_set(padre)
    insumos = _insumos_set(c, datos, padre, tareas)
    rutas = dict(insumos)
    script = _mostrar(os.path.join(c, 'auditorias', nombre + '.md'))
    informe = _mostrar(os.path.join(c, 'auditorias', nombre + '-auditor.md'))
    leer = []

    def lee(s):
        leer.append('- ' + es(s))

    if rutas.get('criterios'):
        lee(_ruta_md(_mostrar(rutas['criterios'])) + ' <.> los Criterios de aceptaci<o>n de la '
            'Historia padre ' + padre + ', como van a quedar')
    else:
        lee('<!> No hay archivo con los Criterios de la Historia padre ' + padre + ': el set es '
            'NO AUDITABLE.')
    if rutas.get('descripcion'):
        lee(_ruta_md(_mostrar(rutas['descripcion'])) + ' <.> la Descripci<o>n de la Historia '
            'padre (sus Reglas de negocio)')
    for t in tareas:
        estado = {'ALTA': 'nueva', 'PISA': 'se pisa: #' + str(t.get('id')),
                  'EXISTE': 'ya cargada: #' + str(t.get('id'))}.get(t.get('accion'), '?')
        lee(_ruta_md(_mostrar(rutas.get(t['clave'])) if rutas.get(t['clave']) else '?') +
            ' <.> ' + t['clave'] + ' <lq>' + (t.get('titulo') or '') + '<rq> (' + estado + ')')
    lee(_ruta_md(script) + ' <.> el chequeo mec<a>nico del set (lote.py auditar), con la lista de '
        'lo que deja al criterio')
    lee(TXT_REGLAS)
    return {
        'clave': nombre,
        'tipo': 'set de Tareas',
        'accion': str(len(tareas)) + ' Tareas',
        'titulo': 'las Tareas de ' + padre,
        'padre': padre,
        'archivo': '',
        'criterios': 'no aplica',
        'criterios_padre': _mostrar(rutas['criterios']) if rutas.get('criterios') else
        es('(no hay archivo: es una P)'),
        'contexto': _mostrar(os.path.join(c, 'CONTEXTO.md')),
        'ficha': _mostrar(_resolver(c, lote.get('ficha'))) if lote.get('ficha') else es('(sin ficha)'),
        'maqueta': lote.get('maqueta') or es('(la ficha no cita `fuente_maqueta`)'),
        'flujo': '-',
        'carpeta': _mostrar(c),
        'auditoria': script,
        'informe': informe,
        'leer': '\n'.join(leer),
        'skills': _skills(('auditar', 'set')),
        'salida': es('- ' + _ruta_md(informe) + ' <.> tu informe, con el formato de abajo'),
        'informe_max_palabras': str(PALABRAS['auditar']),
        'huella': _firma(_huella(insumos)),
        'veredictos': 'CIERRA | CON HUECOS | NO AUDITABLE',
        'aprobado': 'CIERRA',
    }


def cmd_mision(a):
    datos = _cargar(a.carpeta)
    ruta_plantilla = os.path.join(MISIONES, a.tipo_mision + '.md')
    plantilla = _leer_texto(ruta_plantilla)
    if plantilla is None:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer la plantilla ' +
                    _mostrar(ruta_plantilla))
    plantilla = plantilla.replace('\r\n', '\n')
    textos = []
    for pedido in a.claves:
        crudo = pedido.strip().strip('[]')
        if crudo.lower().startswith('set-'):
            if a.tipo_mision != 'auditar':
                raise Falla(ARREGLAR, 'lote: un set no se redacta ni se corrige; se audita con '
                            '"mision <carpeta> auditar ' + crudo + '"')
            grupos = _grupos(datos)
            grupo = next(((p, ts) for p, ts in grupos if _nombre_set(p).lower() == crudo.lower()),
                         None)
            if grupo is None:
                raise Falla(ARREGLAR, "lote: no hay ningun set '" + crudo + "' (un padre necesita "
                            "2 o mas Tareas en el lote). Sets: " +
                            (', '.join(_nombre_set(p) for p, _ in grupos) or 'ninguno'))
            nombre = _nombre_set(grupo[0])
            valores = _valores_set(datos, a.carpeta, grupo[0], grupo[1])
        else:
            nombre = crudo.upper()
            it = _buscar(datos, nombre)
            if it is None:
                raise Falla(ARREGLAR, 'lote: no hay ningun item ' + nombre + ' en items.json')
            if it.get('accion') == 'RELACION':
                raise Falla(ARREGLAR, 'lote: ' + nombre + ' es una RELACION: no se redacta ni se '
                            'audita')
            if it.get('accion') == 'EXISTE':
                raise Falla(ARREGLAR, 'lote: ' + nombre + ' es EXISTE (ya cargada): no se redacta '
                            'ni se audita sola; entra al set de su padre')
            if it.get('tipo') not in TIPOS:
                raise Falla(SIN_DATOS, 'lote: ' + nombre + ' no tiene tipo (Tarea o Historia)')
            valores = _valores_mision(datos, a.carpeta, it, a.tipo_mision)
        t = _render(plantilla, valores, a.tipo_mision + '.md').rstrip('\n') + '\n'
        if a.guardar:
            _escribir(os.path.join(a.carpeta, 'misiones', nombre + '-' + a.tipo_mision + '.md'), t)
        textos.append(t)
    sys.stdout.write('\n---\n\n'.join(textos))
    return OK


# ---------------------------------------------------------------------------------------
# auditar
# ---------------------------------------------------------------------------------------

def _reporte_de(d):
    """Rearma el Reporte desde su json, para escribir el .md con el formato de siempre."""
    r = reporte.Reporte(str(d.get('herramienta') or '?'), str(d.get('insumo') or '?'))
    for x in d.get('renglones') or []:
        if isinstance(x, dict):
            r.renglones.append((str(x.get('nivel', '')), str(x.get('chequeo', '')),
                                str(x.get('detalle', '')), str(x.get('evidencia', ''))))
    r.para_el_auditor = [str(x) for x in (d.get('para_el_auditor') or [])]
    r.datos = d.get('datos') if isinstance(d.get('datos'), dict) else {}
    if d.get('sin_datos'):
        r.sin_datos = str(d['sin_datos'])
    elif d.get('codigo') == SIN_DATOS:
        r.sin_datos = 'el script dijo SIN DATOS'
    return r


def _sin_datos(herramienta, insumo, motivo):
    r = reporte.Reporte(herramienta, insumo)
    r.falta_insumo(motivo)
    return r.como_dict()


def _correr_script(script, args, ruta_json, herramienta, insumo):
    """Corre un script de auditoria y devuelve su dict (nunca lanza)."""
    if os.path.exists(ruta_json):
        os.remove(ruta_json)
    if not os.path.isfile(script):
        return _sin_datos(herramienta, insumo, 'no existe ' + _mostrar(script) + ': la '
                          'auditoria mecanica no corrio')
    cmd = [sys.executable, '-B', script] + args + ['--json', '--salida', ruta_json]
    entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=300, env=entorno, cwd=RAIZ)
    except (OSError, subprocess.SubprocessError) as e:
        return _sin_datos(herramienta, insumo, 'no se pudo correr ' + os.path.basename(script) +
                          ' (' + type(e).__name__ + ')')
    if p.returncode not in (OK, ARREGLAR, SIN_DATOS):
        cola = (p.stderr or b'').decode('utf-8', 'replace').strip().split('\n')[-1:]
        return _sin_datos(herramienta, insumo, os.path.basename(script) + ' salio con codigo ' +
                          str(p.returncode) + (': ' + cola[0] if cola and cola[0] else ''))
    try:
        d = _leer_json(ruta_json)
    except (OSError, ValueError):
        try:
            d = json.loads((p.stdout or b'').decode('utf-8', 'replace'))
        except ValueError:
            return _sin_datos(herramienta, insumo, os.path.basename(script) + ' no devolvio un '
                              'json legible')
    if not isinstance(d, dict) or d.get('codigo') not in (OK, ARREGLAR, SIN_DATOS):
        return _sin_datos(herramienta, insumo, os.path.basename(script) + ' devolvio un json '
                          'sin codigo 0/1/2')
    codigo = max(d['codigo'], p.returncode)
    d['codigo'] = codigo
    d['veredicto'] = {OK: 'SIN HALLAZGOS', ARREGLAR: 'CON HALLAZGOS', SIN_DATOS: 'SIN DATOS'}[codigo]
    return d


def _escribir_auditoria(carpeta, nombre, d, huella=None):
    base = os.path.join(carpeta, 'auditorias', nombre)
    _escribir_json(base + '.json', d)
    _escribir(base + '.md', _reporte_de(d).markdown())
    if huella is not None:
        _escribir_json(base + '.huella.json', huella)


def _contar(d, nivel):
    return sum(1 for x in d.get('renglones') or [] if isinstance(x, dict) and x.get('nivel') == nivel)


def cmd_auditar(a):
    carpeta = os.path.abspath(a.carpeta)
    datos = _cargar(carpeta)
    lote = datos['lote']
    dir_bin = os.path.abspath(a.bin) if a.bin else AQUI
    filas, peor = [], OK
    for it in _items(datos):
        clave = it['clave']
        if it.get('accion') == 'RELACION':
            filas.append((clave, '-', 'NO APLICA (RELACION)', None, ''))
            continue
        if it.get('accion') == 'EXISTE':
            filas.append((clave, '-', 'NO APLICA (EXISTE: entra al set)', None, ''))
            continue
        ruta_json = os.path.join(carpeta, 'auditorias', clave + '.json')
        insumos = _insumos(carpeta, it, lote)
        huella = _huella(insumos)
        rutas = dict(insumos)
        if it.get('tipo') == 'Tarea':
            herramienta, script = 'auditar-tarea', os.path.join(dir_bin, 'auditar-tarea.py')
            principal = rutas.get('archivo')
            args = [principal or '']
            if rutas.get('criterios_padre'):
                args += ['--historia', rutas['criterios_padre']]
        elif it.get('tipo') == 'Historia':
            herramienta, script = 'auditar-historia', os.path.join(dir_bin, 'auditar-historia.py')
            principal = rutas.get('criterios')
            args = ['--criterios', principal or '']
            if rutas.get('archivo') and os.path.isfile(rutas['archivo']):
                args += ['--descripcion', rutas['archivo']]
            if rutas.get('ficha') and os.path.isfile(rutas['ficha']):
                args += ['--ficha', rutas['ficha']]
            if it.get('flujo'):
                args += ['--flujo', it['flujo']]
        else:
            d = _sin_datos('lote.py', clave, 'el item no tiene tipo (Tarea o Historia)')
            _escribir_auditoria(carpeta, clave, d, huella)
            filas.append((clave, '?', d['veredicto'], d, 'auditorias/' + clave + '.md'))
            peor = max(peor, SIN_DATOS)
            continue
        if not principal or not os.path.isfile(principal):
            d = _sin_datos(herramienta, _mostrar(principal), 'falta el archivo ' +
                           _mostrar(principal) + ': no hay nada que auditar')
        else:
            d = _correr_script(script, args, ruta_json, herramienta, _mostrar(principal))
        _escribir_auditoria(carpeta, clave, d, huella)
        filas.append((clave, herramienta, d['veredicto'], d, 'auditorias/' + clave + '.md'))
        peor = max(peor, d['codigo'])

    for padre, tareas in _grupos(datos):
        nombre = _nombre_set(padre)
        ruta_json = os.path.join(carpeta, 'auditorias', nombre + '.json')
        insumos = _insumos_set(carpeta, datos, padre, tareas)
        rutas = dict(insumos)
        if not rutas.get('criterios'):
            d = _sin_datos('analizar-tareas', padre, 'ninguna Tarea de ' + padre + ' declara los '
                           'Criterios del padre (--criterios-padre)')
        else:
            args = ['--historia', rutas['criterios']]
            if rutas.get('descripcion') and os.path.isfile(rutas['descripcion']):
                args += ['--descripcion', rutas['descripcion']]
            args += ['--ids', os.path.join(carpeta, 'items.json')]
            args += [rutas.get(t['clave']) or '' for t in tareas]
            d = _correr_script(os.path.join(dir_bin, 'analizar-tareas.py'), args, ruta_json,
                               'analizar-tareas', padre)
        _escribir_auditoria(carpeta, nombre, d, _huella(insumos))
        filas.append(('set ' + padre, 'analizar-tareas', d['veredicto'], d,
                      'auditorias/' + nombre + '.md'))
        peor = max(peor, d['codigo'])

    print('Auditoria mecanica del lote ' + os.path.basename(carpeta))
    print('')
    print('| Item | Script | Veredicto | Hallazgos | No auditables | Avisos | Reporte |')
    print('|---|---|---|---|---|---|---|')
    for clave, herr, ver, d, rep in filas:
        if d is None:
            print('| %s | %s | %s | - | - | - | - |' % (clave, herr, ver))
            continue
        extra = (' (' + str(d.get('sin_datos')) + ')') if d.get('sin_datos') else ''
        print('| %s | %s | %s%s | %d | %d | %d | %s |' % (
            clave, herr, ver, extra, _contar(d, 'HALLAZGO'), _contar(d, 'NO_AUDITABLE'),
            _contar(d, 'AVISO'), rep))
    print('')
    print('Resultado: ' + {OK: 'SIN HALLAZGOS', ARREGLAR: 'CON HALLAZGOS',
                           SIN_DATOS: 'SIN DATOS'}[peor] +
          '. Lo que el script marca HALLAZGO es hallazgo; SIN DATOS no es OK.')
    print('Siguiente: python bin/lote.py mision ' + _mostrar(carpeta) + ' auditar <clave>  (un '
          'agente distinto del que redacto, por item y por set-<padre>)')
    return peor


# ---------------------------------------------------------------------------------------
# Lectura de lo auditado (cierre y estado)
# ---------------------------------------------------------------------------------------

def _mecanico(carpeta, nombre):
    """'SIN HALLAZGOS' / 'CON HALLAZGOS' / 'SIN DATOS', o None si el script no corrio."""
    try:
        d = _leer_json(os.path.join(carpeta, 'auditorias', nombre + '.json'))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return 'SIN DATOS'
    return {OK: 'SIN HALLAZGOS', ARREGLAR: 'CON HALLAZGOS', SIN_DATOS: 'SIN DATOS'}.get(
        d.get('codigo'), 'SIN DATOS')


def _informe(carpeta, nombre):
    """El informe del auditor: {'veredicto', 'huella', 'F': [...], 'P': [...]}, o None si no hay.

    'veredicto' es '' si no se lee uno de VEREDICTOS (o quedo el molde con las opciones).
    Los F y P son los renglones '- ' de las secciones '## F' y '## P', mas los renglones que
    empiezan con 'F:' o 'P:' en cualquier lado.
    """
    s = _leer_texto(os.path.join(carpeta, 'auditorias', nombre + '-auditor.md'))
    if s is None:
        return None
    res = {'veredicto': None, 'huella': None, 'F': [], 'P': []}
    seccion = None
    for linea in s.replace('\r\n', '\n').split('\n'):
        if linea.startswith('## '):
            palabras = texto.sin_acentos(linea[3:]).strip().split(' ')
            seccion = palabras[0].upper() if palabras else None
            continue
        l = linea.strip()
        plano = l.replace('*', '').strip()
        sa = texto.sin_acentos(plano)
        if sa.startswith('veredicto:'):
            if res['veredicto'] is None:
                v = plano.split(':', 1)[1].strip()
                res['veredicto'] = v if ('|' not in v and v.startswith(VEREDICTOS)) else ''
            continue
        if sa.startswith('huella:'):
            if res['huella'] is None:
                res['huella'] = plano.split(':', 1)[1].strip().strip('`').strip() or None
            continue
        suelto = plano[2:].strip() if plano.startswith('- ') else plano
        if suelto[:2] in ('F:', 'P:'):
            res[suelto[0]].append(suelto[2:].strip())
        elif seccion in ('F', 'P') and l.startswith('- ') and \
                not texto.sin_acentos(l[2:]).strip().startswith('ninguno'):
            res[seccion].append(l[2:].strip())
    if res['veredicto'] is None:
        res['veredicto'] = ''
    return res


_P = re.compile(r'\bP-[0-9]+\b')


def _unicos(xs):
    vistos = []
    for x in xs:
        if x not in vistos:
            vistos.append(x)
    return vistos


def _abiertos(carpeta, it):
    """Columna de los abiertos: los P-nnn de 'Datos a confirmar', o cuantos pendientes hay."""
    if it.get('accion') in ('RELACION', 'EXISTE'):
        return '-'
    doc = _leer_texto(_resolver(carpeta, it.get('archivo')))
    if doc is None:
        return 'SIN DATOS'
    cuerpo = texto.seccion(doc, 'datos a confirmar')
    if cuerpo is None:
        if it.get('tipo') == 'Tarea':
            return es('SIN DATOS: falta <lq>Datos a confirmar<rq>')
        plano = texto.texto_plano(doc + '\n' + (_leer_texto(
            _resolver(carpeta, it.get('criterios'))) or ''))
        codigos = _unicos(_P.findall(plano))
        return ', '.join(codigos) if codigos else str(plano.count(AVISO))
    plano = texto.texto_plano(cuerpo)
    codigos = _unicos(_P.findall(plano))
    if codigos:
        return ', '.join(codigos)
    lis = [texto.texto_plano(li) for _, items in texto.listas(cuerpo) for li in items]
    renglones = lis if lis else plano.split('\n')
    n = sum(1 for r in renglones if r.strip() and not texto.sin_acentos(r.strip()).startswith(
        ('ninguno', '(obligatoria')))
    if n == 0 and not plano.strip():
        return es('SIN DATOS: <lq>Datos a confirmar<rq> vac<i>a')
    return str(n)


def _celda(s):
    return (s or '').replace('|', '/').replace('\n', ' ').strip()


NO_SELLA = 'NO SE SELLA: '
NO_PEDIDA = 'no se pidi<o>'
OTRA_VERSION = NO_SELLA + 'el informe del auditor es de otra versi<o>n (re-auditar)'


def _col_auditoria(carpeta, it, lote):
    """La columna Auditoria. Informa, nunca frena: la auditoria es opcional.

    'no se pidio' si no corrio nada; 'NO SE SELLA: ...' si se pidio y no cierra (la tarjeta se
    escribe igual, sin sello); si no, el veredicto del auditor y el del script.
    """
    if it.get('accion') == 'RELACION':
        return 'no aplica'
    clave = it['clave']
    mec = _mecanico(carpeta, clave)
    inf = _informe(carpeta, clave)
    if mec is None and inf is None:
        return es(NO_PEDIDA)
    if mec is None:
        return es(NO_SELLA + 'el script no corri<o> (lote.py auditar)')
    actual = _huella(_insumos(carpeta, it, lote))
    venc = _cambios(os.path.join(carpeta, 'auditorias', clave + '.huella.json'), actual)
    if venc == ['?']:
        return es(NO_SELLA + 'no se sabe qu<e> versi<o>n se audit<o> (lote.py auditar)')
    if venc:
        return es(NO_SELLA + 'cambi<o> ' + ', '.join(venc) + ' despu<e>s de auditar (re-auditar)')
    if mec == 'SIN DATOS':
        return NO_SELLA + 'el script no pudo auditar'
    if inf is None:
        return NO_SELLA + 'falta el informe del auditor (script: ' + mec + ')'
    if not inf['veredicto']:
        return NO_SELLA + 'el informe del auditor no dice el veredicto (script: ' + mec + ')'
    if inf['huella'] != _firma(actual):
        return es(OTRA_VERSION)
    if inf['veredicto'].startswith(('COMPLETA', 'CIERRA')) and mec != 'SIN HALLAZGOS':
        return NO_SELLA + 'el auditor dijo COMPLETA y el script ' + mec
    return inf['veredicto'] + ' (script: ' + mec + ')'


def _estado_set(carpeta, datos, padre, tareas):
    """(resumen, nota): nota es None si no hay nada que decir en las filas de sus Tareas.

    Como la auditoria de cada item, el analisis del set es opcional y nunca frena: si no se
    pidio, no dice nada; si se pidio y no cierra, la nota dice por que esas Tareas no se sellan.
    """
    nombre = _nombre_set(padre)
    mec = _mecanico(carpeta, nombre)
    actual = _huella(_insumos_set(carpeta, datos, padre, tareas))
    inf = _informe(carpeta, nombre)
    if mec is None and inf is None:
        return es(NO_PEDIDA), None
    aud = 'sin informe' if inf is None else (inf['veredicto'] or 'sin veredicto')
    resumen = (mec or 'sin correr') + es(' <.> auditor: ') + aud
    pre = NO_SELLA + 'set ' + padre + ' '
    if mec is None:
        return resumen, pre + 'sin correr (lote.py auditar)'
    venc = _cambios(os.path.join(carpeta, 'auditorias', nombre + '.huella.json'), actual)
    if venc == ['?']:
        return resumen, pre + es('sin huella: no se sabe qu<e> versi<o>n se audit<o>')
    if venc:
        return resumen, pre + es('vencido: cambi<o> ' + ', '.join(venc) + ' despu<e>s de auditar')
    if mec == 'SIN DATOS':
        return resumen, pre + 'SIN DATOS (el script no pudo analizar el set)'
    if inf is None:
        return resumen, pre + 'sin informe del auditor (lote.py mision <carpeta> auditar ' + \
            nombre + ')'
    if not inf['veredicto']:
        return resumen, pre + 'el informe del auditor no dice el veredicto'
    if inf['huella'] != _firma(actual):
        return resumen, pre + es('el informe del auditor es de otra versi<o>n (re-auditar)')
    if mec != 'SIN HALLAZGOS':
        return resumen, 'set ' + padre + ' ' + mec + ' (van como pendientes a confirmar)'
    return resumen, None


def _antes(carpeta, it):
    return os.path.join(carpeta, 'antes', (it.get('id') or '?') + '.html')


def _col_gates(carpeta, it):
    if it.get('accion') == 'PISA' and (not it.get('id') or not os.path.isfile(_antes(carpeta, it))):
        return 'FRENA: falta el ANTES (antes/' + (it.get('id') or '?') + '.html)'
    return it.get('gates') or 'SIN DATOS'


def _col_dedup(it):
    if it.get('dedup'):
        return it['dedup']
    return 'SIN DATOS' if it.get('accion') == 'ALTA' else 'no aplica'


def _frena(*celdas):
    return any(c.startswith(('FRENA', 'SIN DATOS')) for c in celdas)


def _se_sella(celda_auditoria):
    """True si la fila lleva sello: hubo auditoria y nada la invalida."""
    return not celda_auditoria.startswith((NO_SELLA, es(NO_PEDIDA), 'no aplica'))


# ---------------------------------------------------------------------------------------
# cierre
# ---------------------------------------------------------------------------------------

ENCABEZADO = ('| # | Acci<o>n | <I>tem | Padre | Puntos | GATES y <S>2b | Auditor<i>a | `<!>` '
              'abiertos | Dedup | Archivo |')


def _secciones_md(s):
    """{titulo_sin_acentos: cuerpo} de un .md partido por '## '."""
    res, actual, cuerpo = {}, None, []
    for linea in (s or '').replace('\r\n', '\n').split('\n'):
        if linea.startswith('## '):
            if actual is not None:
                res[actual] = '\n'.join(cuerpo)
            actual, cuerpo = texto.sin_acentos(linea[3:]).strip(), []
        elif actual is not None:
            cuerpo.append(linea)
    if actual is not None:
        res[actual] = '\n'.join(cuerpo)
    return res


def _seccion_contexto(secs, prefijo, titulo):
    if secs is None:
        return es('SIN DATOS: no se pudo leer CONTEXTO.md.')
    for k in secs:
        if k.startswith(prefijo):
            cuerpo = re.sub(r'<!--.*?-->', '', secs[k], flags=re.S).strip()
            if cuerpo:
                return cuerpo
            break
    return es('SIN DATOS: la secci<o>n <lq>' + titulo + '<rq> de CONTEXTO.md est<a> vac<i>a (si '
              'no hay nada, se escribe <lq>Ninguno.<rq>).')


def _armar_cierre(carpeta, datos):
    lote = datos['lote']
    accion_es = {'ALTA': 'ALTA', 'PISA': '**PISA**', 'RELACION': es('RELACI<O>N'),
                 'EXISTE': 'EXISTE'}
    grupos = _grupos(datos)
    estado_sets = dict((p, _estado_set(carpeta, datos, p, ts)) for p, ts in grupos)
    filas, frenan, hay_existe, sellos, pedidas = [], [], False, 0, 0
    for n, it in enumerate(_items(datos), 1):
        item = it['clave'] + (' (#' + it['id'] + ')' if it.get('id') else '') + es(' <.> ') + \
            (it.get('titulo') or '')
        padre = ('`' + it['padre'] + '`') if it.get('padre') else '-'
        puntos = '-' if it.get('puntos') is None else str(it['puntos'])
        archivo = it.get('archivo')
        archivo = ('`' + _mostrar(_resolver(carpeta, archivo)) + '`') if archivo else '-'
        if it.get('accion') == 'EXISTE':
            hay_existe = True
            celdas = (str(n), 'EXISTE', item, padre, puntos, 'no se escribe (ya cargada)',
                      'no aplica (entra al set)', '-', 'no aplica')
        else:
            gates = _col_gates(carpeta, it)
            audit = _col_auditoria(carpeta, it, lote)
            dedup = _col_dedup(it)
            if it.get('tipo') == 'Tarea' and it.get('accion') != 'RELACION' and \
                    it.get('padre') in estado_sets:
                nota = estado_sets[it['padre']][1]
            else:
                nota = None
            if not audit.startswith((es(NO_PEDIDA), 'no aplica')) or nota:
                pedidas += 1
            sella = _se_sella(audit) and not (nota or '').startswith(NO_SELLA)
            if nota:
                audit = audit + es(' <.> ') + nota
            if sella:
                sellos += 1
            if _frena(gates, dedup):
                frenan.append(str(n))
            celdas = (str(n), accion_es.get(it.get('accion'), str(it.get('accion'))), item, padre,
                      puntos, gates, audit, _abiertos(carpeta, it), dedup)
        filas.append('| ' + ' | '.join(_celda(x) for x in celdas) + ' | ' + archivo + ' |')

    ctx = _leer_texto(os.path.join(carpeta, 'CONTEXTO.md'))
    secs = _secciones_md(ctx) if ctx is not None else None
    o = ['# Cierre del lote ' + os.path.basename(os.path.abspath(carpeta)), '',
         es(ENCABEZADO), '|---|---|---|---|---|---|---|---|---|---|']
    o += filas
    o.append('')
    if not filas:
        o.append(es('SIN DATOS: items.json no tiene <i>tems.'))
    elif frenan:
        o.append('Filas que no se escriben (FRENA o SIN DATOS): ' + ', '.join(frenan) + '.')
    else:
        o.append('Ninguna fila dice FRENA ni SIN DATOS.')
    if hay_existe:
        o.append(es('Las filas EXISTE no se escriben: son Tareas ya cargadas que entran al '
                    'an<a>lisis del set.'))
    if grupos:
        o.append(es('An<a>lisis del set (analizar-tareas): ') + '; '.join(
            '`' + p + '` ' + estado_sets[p][0] for p, _ in grupos) + '.')

    informes = [(it['clave'], _informe(carpeta, it['clave'])) for it in _items(datos, ESCRIBIBLES)]
    informes += [(_nombre_set(p), _informe(carpeta, _nombre_set(p))) for p, _ in grupos]

    def de_auditores(letra):
        res = []
        for nombre, inf in informes:
            res += ['- ' + nombre + es(' <.> ') + x for x in (inf or {}).get(letra, [])]
        return res or ['Ninguno.']

    o += ['', '## Aplicado sin preguntar', '', es('**Por fuente (F)**'), '',
          _seccion_contexto(secs, 'decidido por fuente', 'Decidido por fuente (F)'), '',
          es('**Por recomendaci<o>n t<e>cnica (R)**'), '',
          _seccion_contexto(secs, 'recomendaciones aplicadas', 'Recomendaciones aplicadas (R)'),
          '', es('**De las auditor<i>as (F)**'), ''] + de_auditores('F') + \
        ['', '## Lo que se pisa', '']
    pisas = _items(datos, ('PISA',))
    if not pisas:
        o.append('Ninguno.')
    for it in pisas:
        antes = _antes(carpeta, it)
        donde = ('ANTES en `' + _mostrar(antes) + '`') if os.path.isfile(antes) else (
            es('<!> falta el ANTES (`antes/') + (it.get('id') or '?') +
            es('.html`): la fila no se escribe'))
        o.append('- ' + it['clave'] + ' (#' + (it.get('id') or '?') + ') ' + es('<lq>') +
                 (it.get('titulo') or '') + es('<rq>: ') +
                 (it.get('cambia') or es('SIN DATOS: falta qu<e> cambia (lote.py item --cambia)')) +
                 es(' <.> ') + donde)
    o += ['', '## Conocimiento para el Cerebro', '',
          _seccion_contexto(secs, 'conocimiento para el cerebro', 'Conocimiento para el Cerebro'),
          '', '## Preguntas que quedaron', '',
          _seccion_contexto(secs, 'preguntas', 'Preguntas (P)'), '',
          es('**De las auditor<i>as (P)**'), ''] + de_auditores('P')
    if sellos:
        o += ['', es('Las tarjetas con veredicto en la columna Auditor<i>a llevan su sello (las que '
                     'dicen NO SE SELLA o no se pidi<o>, no), y sus hallazgos van como pendientes a '
                     'confirmar (molde de [[comentar-tarea]]).')]
    elif pedidas:
        o += ['', es('Auditor<i>a: se pidi<o>, pero ninguna fila cerr<o> (NO SE SELLA). Ninguna '
                     'tarjeta lleva sello; se escriben igual.')]
    else:
        o += ['', es('Auditor<i>a: no se pidi<o>. Ninguna tarjeta lleva sello.')]
    o += ['', es('<?>Escribo todo el lote?'), '']
    return '\n'.join(o), frenan, len(filas)


def cmd_cierre(a):
    carpeta = os.path.abspath(a.carpeta)
    datos = _cargar(carpeta)
    contenido, frenan, n = _armar_cierre(carpeta, datos)
    _escribir(os.path.join(carpeta, 'CIERRE.md'), contenido)
    sys.stdout.write(contenido)
    return ARREGLAR if (frenan or not n) else OK


# ---------------------------------------------------------------------------------------
# ids y comparar
# ---------------------------------------------------------------------------------------

def _leer_mapa(ruta, carpeta=None):
    candidatos = [ruta] + ([os.path.join(carpeta, ruta)] if carpeta and not os.path.isabs(ruta)
                           else [])
    elegido = next((c for c in candidatos if os.path.isfile(c)), None)
    if elegido is None:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no existe el mapa ' + ruta +
                    ((' (ni en ' + _mostrar(carpeta) + ')') if carpeta else ''))
    try:
        crudo = _leer_json(elegido)
    except (OSError, ValueError) as e:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer el mapa ' + ruta + ' (' +
                    type(e).__name__ + ')')
    if not isinstance(crudo, dict):
        raise Falla(SIN_DATOS, 'SIN DATOS -- el mapa tiene que ser {"[T-01]": "125272", ...}')
    mapa = {}
    for k, v in crudo.items():
        marca = _ref(str(k), 'la clave del mapa')
        if not marca or not marca.startswith('['):
            raise Falla(SIN_DATOS, "SIN DATOS -- '" + str(k) + "' no es una marca [T-nn]/[H-nn]")
        d = str(v).strip().lstrip('#')
        if not (d.isascii() and d.isdigit()):
            raise Falla(SIN_DATOS, "SIN DATOS -- el #ID de " + marca + " ('" + str(v) +
                        "') no es un numero")
        mapa[marca] = d
    return mapa


def _aplicar_mapa(s, mapa):
    for marca in sorted(mapa):
        s = s.replace(marca, '#' + mapa[marca])
    return s


def cmd_ids(a):
    carpeta = os.path.abspath(a.carpeta)
    datos = _cargar(carpeta)
    mapa = _leer_mapa(a.mapa or 'mapa-ids.json', carpeta)
    escritos, pendientes, faltan = [], [], []
    for it in _items(datos, ESCRIBIBLES):
        for campo, sufijo in (('archivo', '.final.html'), ('criterios', '-criterios.final.html')):
            if not it.get(campo):
                continue
            ruta = _resolver(carpeta, it[campo])
            try:
                with io.open(ruta, encoding='utf-8-sig', newline='') as f:
                    s = f.read()
            except (OSError, UnicodeDecodeError):
                faltan.append(_mostrar(ruta))
                continue
            t = _aplicar_mapa(s, mapa)
            # Siempre dentro del lote: aunque el borrador viva en otro lado, el texto final
            # es del lote y no se escribe al lado de un archivo ajeno.
            destino = os.path.join(carpeta, it['clave'] + sufijo)
            with io.open(destino, 'w', encoding='utf-8', newline='') as f:
                f.write(t)
            escritos.append(_mostrar(destino))
            resto = texto.marcas_lote(t)
            if resto:
                pendientes.append((_mostrar(destino), resto))
    cambiados = False
    for it in datos['items']:
        marca = '[' + it['clave'] + ']'
        if marca in mapa and not it.get('id'):
            it['id'] = mapa[marca]
            cambiados = True
    if cambiados:
        _guardar(carpeta, datos)
    print('Marcas reemplazadas con ' + str(len(mapa)) + ' #ID del mapa.')
    for e in escritos:
        print('  escrito: ' + e)
    for f in faltan:
        print('  FALTA: ' + f)
    for d, resto in pendientes:
        print('  SIN #ID en ' + d + ': ' + ', '.join(resto))
    if pendientes or faltan:
        print('Quedan marcas sin #ID o archivos que faltan: esas tarjetas no se escriben asi.')
        return ARREGLAR
    print('Ninguna marca quedo sin #ID. Los originales auditados no se tocaron.')
    return OK


def _leer_azure(ruta, campo):
    s = _leer_texto(ruta)
    if s is None:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer ' + ruta)
    if not campo:
        return s
    try:
        d = json.loads(s)
    except ValueError:
        raise Falla(SIN_DATOS, 'SIN DATOS -- ' + ruta + ' no es json, y se pidio --campo')
    for fuente in (d.get('fields') if isinstance(d, dict) else None, d):
        if isinstance(fuente, dict) and isinstance(fuente.get(campo), str):
            return fuente[campo]
    raise Falla(SIN_DATOS, 'SIN DATOS -- ' + ruta + ' no trae el campo ' + campo)


def cmd_comparar(a):
    auditado = _leer_texto(a.auditado)
    if auditado is None:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer ' + a.auditado)
    azure = _leer_azure(a.azure, a.campo)
    if a.mapa:
        auditado = _aplicar_mapa(auditado, _leer_mapa(
            a.mapa, os.path.dirname(os.path.abspath(a.auditado))))
    if not texto.normalizado(auditado) or not texto.normalizado(azure):
        raise Falla(SIN_DATOS, 'SIN DATOS -- uno de los dos textos esta vacio: no se comparo nada')
    if texto.iguales(auditado, azure):
        print('IGUALES -- el texto de Azure es el auditado (sin etiquetas y con los espacios '
              'normalizados). Se puede sellar.')
        return OK
    k, ra, rb = texto.primera_diferencia(auditado, azure)
    print('DISTINTOS -- la tarjeta no es lo auditado: no se sella.')
    print('  Primera diferencia en el caracter ' + str(k) + ':')
    print('  auditado: ...' + ra + '...')
    print('  azure:    ...' + rb + '...')
    resto = texto.marcas_lote(auditado)
    if resto:
        print('  Ojo: el auditado todavia tiene marcas sin #ID (' + ', '.join(resto) +
              '). Falta --mapa?')
    return ARREGLAR


# ---------------------------------------------------------------------------------------
# tiempos
# ---------------------------------------------------------------------------------------

def _ahora(texto_iso):
    if texto_iso:
        try:
            return datetime.datetime.fromisoformat(texto_iso).astimezone()
        except ValueError:
            raise Falla(SIN_DATOS, "lote: --ahora '" + texto_iso + "' no es una fecha ISO "
                        "(AAAA-MM-DDTHH:MM)")
    return datetime.datetime.now().astimezone()


def _iso(dt):
    return dt.isoformat(timespec='seconds')


def _duracion(seg):
    seg = int(round(seg))
    return '%d min %02d s' % (seg // 60, seg % 60)


def _leer_tiempos(carpeta):
    ruta = os.path.join(carpeta, 'tiempos.json')
    try:
        t = _leer_json(ruta)
    except (OSError, ValueError) as e:
        raise Falla(SIN_DATOS, 'SIN DATOS -- no se pudo leer ' + _mostrar(ruta) + ' (' +
                    type(e).__name__ + ')')
    if not isinstance(t, dict) or not isinstance(t.get('fases'), dict):
        raise Falla(SIN_DATOS, 'SIN DATOS -- ' + _mostrar(ruta) + ' no tiene la forma esperada')
    return ruta, t


def _medir(t):
    """[(fase, minimo, maximo, segundos_cerrados, abierto_desde | None, tramos)]."""
    res = []
    for fase, mn, mx in FASES:
        seg, abierto, tramos = 0.0, None, t['fases'].get(fase) or []
        for tr in tramos:
            ini = datetime.datetime.fromisoformat(tr['inicio'])
            if tr.get('fin'):
                seg += (datetime.datetime.fromisoformat(tr['fin']) - ini).total_seconds()
            else:
                abierto = ini
        res.append((fase, mn, mx, seg, abierto, len(tramos)))
    return res


def _informe_tiempos(carpeta, t):
    o = ['Tiempos del lote ' + os.path.basename(os.path.abspath(carpeta)), '',
         '| Fase | Esperado | Medido | Tramos |', '|---|---|---|---|']
    total, faltan, marcas = 0.0, [], []
    for fase, mn, mx, seg, abierto, n in _medir(t):
        esperado = ('%d min' % mn) if mn == mx else ('%d a %d min' % (mn, mx))
        if abierto is not None:
            medido = 'en curso desde ' + abierto.strftime('%H:%M')
            faltan.append(fase)
        elif n == 0:
            medido = 'sin medir'
            faltan.append(fase)
        else:
            medido = _duracion(seg)
        total += seg
        o.append('| %s | %s | %s | %d |' % (fase, esperado, medido, n))
        for tr in t['fases'].get(fase) or []:
            marcas.append(datetime.datetime.fromisoformat(tr['inicio']))
            if tr.get('fin'):
                marcas.append(datetime.datetime.fromisoformat(tr['fin']))
    o.append('')
    linea = 'Suma de las fases: ' + _duracion(total) + ' (objetivo: %d a %d min)' % OBJETIVO
    if faltan:
        linea += ' -- incompleto: falta cerrar ' + ', '.join(faltan)
    elif total <= OBJETIVO[1] * 60:
        linea += ' -- DENTRO del objetivo'
    else:
        linea += ' -- PASADO por ' + _duracion(total - OBJETIVO[1] * 60)
    o.append(linea)
    if marcas:
        o.append('Reloj (del primer inicio a la ultima marca): ' +
                 _duracion((max(marcas) - min(marcas)).total_seconds()) +
                 ' (incluye las esperas entre fases)')
    return '\n'.join(o) + '\n'


def cmd_tiempos(a):
    carpeta = os.path.abspath(a.carpeta)
    if not os.path.isdir(carpeta):
        raise Falla(SIN_DATOS, 'SIN DATOS -- no existe la carpeta del lote: ' + a.carpeta)
    ruta, t = _leer_tiempos(carpeta)
    if a.fase is None:
        sys.stdout.write(_informe_tiempos(carpeta, t))
        return OK
    fases = [f for f, _, _ in FASES]
    if a.fase not in fases:
        raise Falla(SIN_DATOS, "lote: la fase '" + a.fase + "' no existe. Son: " + NOMBRES_FASES)
    if a.marca not in ('inicio', 'fin'):
        raise Falla(SIN_DATOS, 'lote: despues de la fase va inicio o fin')
    ahora = _ahora(a.ahora)
    tramos = t['fases'].setdefault(a.fase, [])
    abierto = tramos and not tramos[-1].get('fin')
    if a.marca == 'inicio':
        if abierto:
            raise Falla(ARREGLAR, "lote: '" + a.fase + "' ya tiene un inicio sin fin (" +
                        tramos[-1]['inicio'] + '). Marca el fin primero.')
        tramos.append({'inicio': _iso(ahora), 'fin': None})
    else:
        if not abierto:
            raise Falla(ARREGLAR, "lote: '" + a.fase + "' no tiene un inicio abierto: no hay que "
                        "cerrar.")
        if ahora < datetime.datetime.fromisoformat(tramos[-1]['inicio']):
            raise Falla(ARREGLAR, 'lote: el fin es anterior al inicio (' + tramos[-1]['inicio'] +
                        ')')
        tramos[-1]['fin'] = _iso(ahora)
    _escribir_json(ruta, t)
    print(a.fase + ' ' + a.marca + ': ' + _iso(ahora))
    if a.marca == 'fin':
        ini = datetime.datetime.fromisoformat(tramos[-1]['inicio'])
        print('  duro ' + _duracion((ahora - ini).total_seconds()))
    return OK


# ---------------------------------------------------------------------------------------
# estado
# ---------------------------------------------------------------------------------------

def cmd_estado(a):
    carpeta = os.path.abspath(a.carpeta)
    datos = _cargar(carpeta)
    lote = datos['lote']
    items = _items(datos)
    claves = set(i['clave'] for i in items)
    o = ['Lote ' + os.path.basename(carpeta),
         'Ficha: ' + str(lote.get('ficha')) + ' -- maqueta: ' + str(lote.get('maqueta') or
                                                                    '(ninguna)')]
    cuenta = {}
    for it in items:
        k = (it.get('tipo') or '?', it.get('accion') or '?')
        cuenta[k] = cuenta.get(k, 0) + 1
    o.append('Items: ' + str(len(items)) + (' -- ' + ', '.join(
        '%s %s: %d' % (t, ac, n) for (t, ac), n in sorted(cuenta.items())) if cuenta else ''))
    o += ['', '| Item | Tipo | Accion | Faltan | Script | Auditor | Marcas |',
          '|---|---|---|---|---|---|---|']
    algo_falta, marcas_total, huerfanas = False, 0, []
    for it in items:
        clave = it['clave']
        if it.get('accion') == 'RELACION':
            o.append('| %s | %s | RELACION | - | - | - | - |' % (clave, it.get('tipo')))
            continue
        if it.get('accion') == 'EXISTE':
            falta = '-' if os.path.isfile(_resolver(carpeta, it.get('archivo')) or '') else 'archivo'
            algo_falta = algo_falta or falta != '-'
            o.append('| %s | %s | EXISTE | %s | - (entra al set) | - | - |' % (
                clave, it.get('tipo'), falta))
            continue
        faltan = []
        roles = [('archivo', it.get('archivo'))]
        if it.get('tipo') == 'Historia':
            roles.append(('criterios', it.get('criterios')))
        else:
            roles.append(('criterios_padre', it.get('criterios_padre')))
        roles.append(('json', clave + '.json'))
        for rol, r in roles:
            if not r:
                faltan.append(rol + ' (sin declarar)')
            elif not os.path.isfile(_resolver(carpeta, r)):
                faltan.append(rol)
        if it.get('accion') == 'PISA' and not os.path.isfile(_antes(carpeta, it)):
            faltan.append('antes/' + (it.get('id') or '?') + '.html')
        mec = _mecanico(carpeta, clave)
        actual = _huella(_insumos(carpeta, it, lote))
        if mec is None:
            script = 'sin correr'
        else:
            venc = _cambios(os.path.join(carpeta, 'auditorias', clave + '.huella.json'), actual)
            script = mec + (' (VENCIDA: ' + ', '.join(venc) + ')' if venc else '')
            if venc:
                algo_falta = True
        inf = _informe(carpeta, clave)
        if inf is None:
            aud = 'sin informe'
        elif not inf['veredicto']:
            aud = 'sin veredicto'
        elif inf['huella'] != _firma(actual):
            aud = inf['veredicto'] + es(' (de otra versi<o>n)')
            algo_falta = True
        else:
            aud = inf['veredicto']
        marcas = []
        for rol, r in roles[:2]:
            s = _leer_texto(_resolver(carpeta, r)) if r else None
            for mk in texto.marcas_lote(s or ''):
                marcas.append(mk)
                if mk[1:-1] not in claves:
                    huerfanas.append(mk + ' en ' + clave)
        marcas = _unicos(marcas)
        marcas_total += len(marcas)
        if faltan:
            algo_falta = True
        o.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            clave, it.get('tipo'), it.get('accion'), ', '.join(faltan) or '-', script, aud,
            ', '.join(marcas) or '-'))
    o.append('')
    for padre, tareas in _grupos(datos):
        resumen, problema = _estado_set(carpeta, datos, padre, tareas)
        if resumen == es(NO_PEDIDA):
            cola = ''
        else:
            cola = ' -- ' + problema if problema else ' -- OK'
        o.append('Set ' + padre + ' (' + str(len(tareas)) + ' Tareas): ' + resumen + cola)
        if problema and problema.startswith(NO_SELLA):
            algo_falta = True
    o.append('Marcas [T-nn]/[H-nn] en los textos: ' + str(marcas_total) +
             ' (se reemplazan por #ID en la fase 5 con lote.py ids)')
    if huerfanas:
        algo_falta = True
        o.append('Marcas que no son de ningun item: ' + ', '.join(_unicos(huerfanas)))
    try:
        _, t = _leer_tiempos(carpeta)
        partes = []
        for fase, _mn, _mx, seg, abierto, n in _medir(t):
            if abierto is not None:
                partes.append(fase + ' en curso')
            elif n:
                partes.append(fase + ' ' + _duracion(seg))
        o.append('Tiempos: ' + (', '.join(partes) or 'sin medir'))
    except Falla:
        o.append('Tiempos: SIN DATOS (no se pudo leer tiempos.json)')
    print('\n'.join(o))
    return ARREGLAR if algo_falta else OK


# ---------------------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('lote: ' + message + '\n\n' + self.format_usage())
        sys.exit(SIN_DATOS)


def _parser():
    p = _Parser(prog='lote.py', description='Modo lote (planificar-lote): la parte mecanica.')
    sub = p.add_subparsers(dest='subcomando')
    sub.required = True

    s = sub.add_parser('preparar', help='crea la carpeta del lote')
    s.add_argument('tema')
    s.add_argument('--ficha', required=True)
    s.add_argument('--fecha')
    s.add_argument('--raiz-output', dest='raiz_output')
    s.set_defaults(func=cmd_preparar)

    s = sub.add_parser('item', help='agrega o actualiza un item de items.json')
    s.add_argument('carpeta')
    s.add_argument('--clave', required=True)
    s.add_argument('--tipo', type=_tipo)
    s.add_argument('--accion', type=_accion, help='ALTA, PISA, RELACION o EXISTE')
    s.add_argument('--titulo')
    s.add_argument('--padre')
    s.add_argument('--criterios-padre', dest='criterios_padre')
    s.add_argument('--archivo')
    s.add_argument('--criterios')
    s.add_argument('--puntos')
    s.add_argument('--actividad')
    s.add_argument('--id')
    s.add_argument('--flujo')
    s.add_argument('--ficha')
    s.add_argument('--relacion', action='append')
    s.add_argument('--dedup')
    s.add_argument('--gates')
    s.add_argument('--cambia')
    s.add_argument('--desde-json', dest='desde_json', action='store_true',
                   help='toma titulo, puntos, actividad y relaciones de <carpeta>/<clave>.json')
    s.set_defaults(func=cmd_item)

    s = sub.add_parser('mision', help='imprime la mision de un sub-agente')
    s.add_argument('carpeta')
    s.add_argument('tipo_mision', choices=TIPOS_MISION)
    s.add_argument('claves', nargs='+', help='claves de items, o set-<padre> (solo auditar)')
    s.add_argument('--guardar', action='store_true')
    s.set_defaults(func=cmd_mision)

    s = sub.add_parser('auditar', help='corre las auditorias mecanicas del lote')
    s.add_argument('carpeta')
    s.add_argument('--bin', help='carpeta de los scripts de auditoria (default: bin/ del repo)')
    s.set_defaults(func=cmd_auditar)

    s = sub.add_parser('cierre', help='escribe CIERRE.md')
    s.add_argument('carpeta')
    s.set_defaults(func=cmd_cierre)

    s = sub.add_parser('ids', help='reemplaza [T-nn]/[H-nn] por #ID en <carpeta>/<clave>.final.html')
    s.add_argument('carpeta')
    s.add_argument('--mapa')
    s.set_defaults(func=cmd_ids)

    s = sub.add_parser('comparar', help='compara lo auditado con lo que quedo en Azure')
    s.add_argument('auditado')
    s.add_argument('azure')
    s.add_argument('--mapa', help='si no existe tal cual, se busca en la carpeta del auditado')
    s.add_argument('--campo', help='si el archivo de Azure es el json del work item')
    s.set_defaults(func=cmd_comparar)

    s = sub.add_parser('tiempos', help='marca o informa los tiempos por fase',
                       description='Fases: ' + NOMBRES_FASES + '. Sin fase, informa.')
    s.add_argument('carpeta')
    s.add_argument('fase', nargs='?', help='una de: ' + NOMBRES_FASES)
    s.add_argument('marca', nargs='?', help='inicio o fin')
    s.add_argument('--ahora', help='AAAA-MM-DDTHH:MM, para anotar una marca tardia')
    s.set_defaults(func=cmd_tiempos)

    s = sub.add_parser('estado', help='resumen de una pantalla')
    s.add_argument('carpeta')
    s.set_defaults(func=cmd_estado)
    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', newline='\n')
    except Exception:
        pass
    a = _parser().parse_args(argv)
    try:
        return a.func(a)
    except Falla as e:
        print(e.mensaje)
        return e.codigo
    except Exception as e:  # noqa: BLE001 -- ningun error inesperado puede dar 0 ni 1
        print('SIN DATOS -- lote.py fallo de una forma que no se esperaba: ' +
              type(e).__name__ + ': ' + str(e))
        print('  Es un bug de lote.py, no del lote. Avisar.')
        return SIN_DATOS


if __name__ == '__main__':
    sys.exit(main())
