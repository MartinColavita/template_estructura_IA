"""Lectura del Cerebro para las auditorias: que reglas existen y que dice una ficha.

- indice_reglas(): los codigos RN-... y DEC-... que el Cerebro DEFINE (titulo o primera celda de una tabla), salvo
  configuracion-ia/ (las skills mencionan reglas de ejemplo que no son del dominio). Es el
  mismo criterio que bin/probar-reglas.py: una regla "existe" si el Cerebro la define.
  Que diga lo que se le atribuye ya no es conteo: lo mira el auditor.
- leer_ficha(): frontmatter (clave: valor, plano) y el bloque "## Derivacion a backlog" con
  sus Slices, Capacidades y Flujos, cada Flujo con sus reglas asignadas.
"""

import os
import re

from . import texto

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Una regla EXISTE donde el Cerebro la DEFINE: un titulo (### RN-MOD-001 -- ...) o la primera celda de una fila de
# tabla (| RN-MOD-001 | ...). Nombrarla en un texto, en un ticket del tablero local (backlog/) o en un pendiente no la
# crea: antes, una regla inventada en un ticket se validaba sola. Las plantillas (plantilla-*.md) y un titulo que es un
# hueco (<...>) tampoco definen nada.
_REGLA = re.compile(r'\b(RN-[A-Z]+-\d+[A-Z]?|DEC-\d+)\b')   # un codigo citado (en el bloque de derivacion de una ficha)
_DEFINICION = re.compile(r'^(?:#{1,6}[ \t]+|\|[ \t]*)(RN-[A-Z]+-\d+[A-Z]?|DEC-\d+)\b(.*)$', re.M)


def raiz_repo():
    return RAIZ


def indice_reglas(raiz=None):
    """{codigo: ruta_relativa_del_primer_archivo_donde_aparece}."""
    raiz = raiz or RAIZ
    base = os.path.join(raiz, 'cerebro-digital')
    res = {}
    for d, subdirs, archivos in os.walk(base):
        rel = os.path.relpath(d, base).replace(os.sep, '/')
        if rel == 'configuracion-ia' or rel.startswith('configuracion-ia/') or 'backlog' in rel.split('/'):
            subdirs[:] = []
            continue
        subdirs.sort()
        for a in sorted(archivos):
            if not a.endswith('.md') or a.startswith('plantilla-'):
                continue
            ruta = os.path.join(d, a)
            try:
                s = texto.leer(ruta)
            except (OSError, UnicodeDecodeError):
                continue
            for codigo, resto in _DEFINICION.findall(s):
                if re.fullmatch(r'<[^>]*>', resto.strip(' \t|:-' + chr(0x2014) + chr(0x2013))):
                    continue
                res.setdefault(codigo, os.path.relpath(ruta, raiz).replace(os.sep, '/'))
    return res


_FM = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.S)
_ITEM = re.compile(r'^\s*-\s*\[(S|C|F)-(\d+)\]\s*(.*)$')
_PUNTO_MEDIO = chr(0xb7)   # el separador del bloque de derivacion; asi el .py queda ASCII


def leer_ficha(ruta):
    """{'frontmatter': {...}, 'derivacion': {'S': {...}, 'C': {...}, 'F': {...}} | None}.

    Cada F-nn trae {'titulo', 'capacidad', 'reglas': [codigos]}. Si la ficha no tiene el
    bloque, 'derivacion' es None (y una Historia que la cita no puede chequear el 13).
    """
    s = texto.leer(ruta).replace('\r\n', '\n')
    fm = {}
    m = _FM.match(s)
    if m:
        for linea in m.group(1).split('\n'):
            if ':' in linea and not linea.startswith(' '):
                k, v = linea.split(':', 1)
                fm[k.strip()] = v.strip().strip('"\'')
    deriv = None
    i = s.find('## Derivaci')
    if i >= 0:
        fin = s.find('\n## ', i + 3)
        bloque = s[i:fin if fin > 0 else len(s)]
        deriv = {'S': {}, 'C': {}, 'F': {}}
        for linea in bloque.split('\n'):
            mi = _ITEM.match(linea)
            if not mi:
                continue
            tipo, num, resto = mi.group(1), mi.group(2), mi.group(3)
            partes = [p.strip() for p in resto.split(_PUNTO_MEDIO)]
            item = {'titulo': partes[0]}
            for p in partes[1:]:
                ps = texto.sin_acentos(p)
                if ps.startswith('capacidad:'):
                    item['capacidad'] = p.split(':', 1)[1].strip()
                elif ps.startswith('slice:'):
                    item['slice'] = p.split(':', 1)[1].strip()
                elif ps.startswith('reglas:'):
                    item['reglas'] = _REGLA.findall(p)
            deriv[tipo]['%s-%s' % (tipo, num)] = item
    return {'frontmatter': fm, 'derivacion': deriv}
