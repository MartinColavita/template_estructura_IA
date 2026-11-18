#!/usr/bin/env python3
"""Por cada migracion de base nueva de un rango: EXPANDIR, CONTRAER o MIXTA. SOLO LECTURA.

    python -I bin/clasificar-migraciones.py --repo <repo-de-la-app> --base <ref> [--hasta <ref>] [--carpeta <ruta>] [--json]
    python -I bin/clasificar-migraciones.py --archivo cambios.diff [--carpeta <ruta>] [--json]

    --base     lo que ya esta en el ambiente (un tag o un commit); --hasta, la version candidata (por defecto HEAD).
    --carpeta  donde viven las migraciones, relativa al repositorio. Sin ella se reconocen las carpetas
               migration(s)/, migracion(es)/, flyway/, liquibase/, alembic/, db/migrate/ y changelog/.

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS

QUE DECIDE, por cada archivo de migracion nuevo (o modificado) del rango, leyendo su SQL sentencia por sentencia:
  EXPANDIR        agrega: tabla, columna, indice, secuencia, tipo. El codigo viejo sigue andando.
  CONTRAER        borra, renombra o restringe lo que ya existe: columna, tabla, restriccion, tipo de una
                  columna, SET NOT NULL, TRUNCATE, DELETE sin WHERE, una vista o rutina que no se vuelve a
                  crear. Los datos no vuelven.
  MIXTA           las dos cosas en la misma migracion: HALLAZGO (van en despliegues distintos).
  NEUTRA          ni una ni otra: datos, indices que se borran, vistas que se recrean, rutinas, permisos.
  SIN CLASIFICAR  no es SQL, no se reconoce, o ejecuta algo que no se ve (EXEC, CALL, DO): SIN DATOS.
  Tambien es HALLAZGO una columna nueva obligatoria y sin valor por defecto en una tabla que ya existe.
  CONTRAER sola sale 0: es el paso 3 del metodo. Su barrera (dos "si") la pone el GATE de DESPLIEGUE, y sus
  datos los toma bin/gate-despliegue.py de aca (importa este archivo).

POR QUE EXISTE. El metodo (desarrollo/references/metodo/migracion-de-base.md) pide expandir, migrar y contraer
en despliegues distintos, porque durante un despliegue conviven el codigo viejo y el nuevo. Saber si una
migracion borra algo lo decidia el modelo leyendo SQL: un DROP en un comentario o un ALTER escondido en un
bloque IF pasaban de largo. Esto lo cuenta igual siempre, y lo que no puede leer lo dice.

QUE NO HACE. No se conecta a ninguna base, no corre la migracion, no escribe nada. No lee YAML ni XML de
herramientas de migraciones. Comentarios, textos entre comillas y cuerpos $$...$$ se blanquean antes de buscar.
Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditoria import diff as lector  # noqa: E402  el lector de diff comun

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
CLASES = ('EXPANDIR', 'CONTRAER', 'MIXTA', 'NEUTRA', 'SIN CLASIFICAR')
CARPETAS = re.compile(r'(?i)(^|/)(migrations?|migracion(es)?|flyway|liquibase|alembic|db/migrate|changelog)(/|$)')
NO_ES_MIGRACION = re.compile(r'(?i)(\.(md|txt|rst|adoc|html?|png|jpe?g|gif|svg)$|(^|/)(readme[^/]*|__init__\.py)$)')
DOCS = re.compile(r'(?i)\.(md|txt|rst|adoc)$|(^|/)docs?/')
BOM = chr(0xFEFF)
NO_MIRA = ('el volumen de las tablas, los bloqueos que toma cada sentencia ni cuanto tarda: eso pide la base real '
           '(migracion-de-base.md)',
           'las migraciones que no son SQL (Java, Python, Ruby, o el XML y el YAML de una herramienta): salen SIN CLASIFICAR',
           'el cuerpo de una funcion, procedimiento o disparador, ni lo que corre adentro de un EXEC, CALL o DO',
           'el separador DELIMITER de MySQL (una rutina asi sale SIN CLASIFICAR)',
           'si la version que esta en el ambiente todavia usa lo que se contrae: eso lo declara una persona en el GATE de DESPLIEGUE')

# ---------------------------------------------------------------------------------------------------------
# El SQL: blanquear lo que no es codigo, partir en sentencias y en comandos
# ---------------------------------------------------------------------------------------------------------

DOLAR = re.compile(r'\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$')
GO = re.compile(r'(?im)^[ \t]*go[ \t]*(?:\d+)?[ \t]*$')
FUERTE = re.compile(r'''(?ix)(?<![\w$#@.])(?:
      (?P<rutina>(?:create(?:\s+or\s+(?:replace|alter))?|alter)\s+(?:definer\s*=\s*\S+\s+)?(?:function|procedure|proc|trigger|package(?:\s+body)?)\b)
    | (?P<tabla>create\s+(?:(?:global|local)\s+)?(?:temp\s+|temporary\s+|unlogged\s+)?table\b)
    | (?P<indice>create\s+(?:unique\s+)?(?:(?:non)?clustered\s+)?index\b)
    | (?P<vista>create\s+(?:or\s+replace\s+)?(?:materialized\s+)?view\b)
    | (?P<crea_otro>create\s+(?:sequence|type|schema|extension|domain)\b)
    | (?P<alter_tabla>alter\s+table\b)
    | (?P<alter_otro>alter\s+(?:index|materialized\s+view|view|sequence|type|schema|domain)\b)
    | (?P<borra>drop\s+(?:table|materialized\s+view|view|index|sequence|type|schema|function|procedure|proc|trigger|domain|extension|database|package)\b)
    | (?P<vacia>truncate\s+(?:table\s+)?(?=[\w\["`#]))
    | (?P<renombra>rename\s+table\b|(?:exec(?:ute)?\s+)?(?:\[?(?:dbo|sys)\]?\s*\.\s*)?\[?sp_rename\b)
    | (?P<opaca>exec(?:ute)?\b)
    | (?P<combina>merge\s+(?:into\b|(?=[\w\["`#])))
    | (?P<inserta>insert\s+(?:into\b|(?=[\w\["`#])))
    | (?P<actualiza>update\s+[\w\["`#.\]]+(?:\s+(?!set\b)\w+)?\s+set\b)
    | (?P<borra_filas>delete\s+(?:from\b|(?=[\w\["`#])))
)''')
# Primera palabra de una sentencia que no cambia el esquema por si sola (pero puede envolver un comando: se busca adentro)
NEUTRAS = ('set', 'use', 'begin', 'commit', 'start', 'end', 'declare', 'if', 'else', 'elsif', 'while', 'return',
           'with', 'select', 'rollback', 'lock', 'values')
# Primera palabra de una sentencia que no cambia el esquema y no envuelve nada (GRANT EXECUTE no es un EXEC)
ATOMICAS = ('grant', 'revoke', 'deny', 'comment', 'print', 'raiserror', 'throw', 'analyze', 'analyse', 'vacuum',
            'reindex', 'refresh', 'pragma', 'savepoint', 'release', 'checkpoint', 'notify', 'cluster', 'discard',
            'reset', 'show', 'explain')
IDENT = r'(?:"[^"]*"|\[[^\]]*\]|`[^`]*`|[\w$#@]+)'
NOMBRE = re.compile(r'\s*(' + IDENT + r'(?:\s*\.\s*' + IDENT + r')*)')
SI_EXISTE = re.compile(r'(?is)\s*(?:if\s+(?:not\s+)?exists\s+)?')


def enmascarar(texto, barra=False):
    """El texto con comentarios, textos entre comillas y cuerpos $$...$$ cambiados por espacios. Los saltos de
    linea quedan, asi cada posicion sigue siendo la del original y una palabra adentro de un comentario o de un
    texto no se toma por una sentencia. barra=True: la lectura de MySQL, donde una barra adentro de un texto
    escapa el caracter que sigue (It\\'s); la estandar solo escapa la comilla doblada (It''s)."""
    out, i, n = list(texto), 0, len(texto)

    def blanquear(a, b):
        for k in range(a, min(b, n)):
            if out[k] != '\n':
                out[k] = ' '
    while i < n:
        c = texto[i]
        if c == '-' and texto.startswith('--', i):
            j = texto.find('\n', i)
            j = n if j < 0 else j
            blanquear(i, j)
            i = j
        elif c == '/' and texto.startswith('/*', i):
            j = texto.find('*/', i + 2)
            j = n if j < 0 else j + 2
            blanquear(i, j)
            i = j
        elif c == "'":
            j = i + 1
            while j < n:
                if barra and texto[j] == chr(92):
                    j += 2
                    continue
                if texto[j] == "'":
                    if j + 1 < n and texto[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            blanquear(i + 1, j)
            i = j + 1
        elif c in '"`[':
            j = texto.find({'"': '"', '`': '`', '[': ']'}[c], i + 1)   # identificadores: quedan como estan
            i = n if j < 0 else j + 1
        elif c == '$':
            m = DOLAR.match(texto, i)
            if m and (i == 0 or not (texto[i - 1].isalnum() or texto[i - 1] == '_')):
                j = texto.find(m.group(0), m.end())
                if j < 0:
                    blanquear(m.end(), n)
                    i = n
                else:
                    blanquear(m.end(), j)
                    i = j + len(m.group(0))
            else:
                i += 1
        else:
            i += 1
    return ''.join(out)


def profundidad(s, corchetes=False):
    """La profundidad de parentesis (y de corchetes, si se pide) en cada posicion de s."""
    res, d = [], 0
    abre, cierra = ('([', ')]') if corchetes else ('(', ')')
    for c in s:
        if c in cierra:
            d = max(0, d - 1)
        res.append(d)
        if c in abre:
            d += 1
    return res


def partir_comas(s):
    """Los pedazos de s separados por comas que no estan adentro de parentesis ni corchetes."""
    prof, res, ini = profundidad(s, True), [], 0
    for k, c in enumerate(s):
        if c == ',' and prof[k] == 0:
            res.append(s[ini:k])
            ini = k + 1
    res.append(s[ini:])
    return [x.strip() for x in res if x.strip()]


def nombre(s):
    """(nombre, fin) del identificador (con su esquema, si lo tiene) al principio de s."""
    m = NOMBRE.match(s)
    return (m.group(1), m.end()) if m else ('', 0)


def clave(nom):
    """El ultimo tramo de un nombre, sin comillas ni corchetes, en minusculas: para comparar tablas."""
    partes = re.split(r'\s*\.\s*', nom.strip()) if nom else ['']
    return partes[-1].strip('"`[]').lower()


def marcas_fuertes(s):
    """[(tipo, inicio, fin_de_la_palabra_clave)] de cada comando que empieza en s, fuera de parentesis."""
    prof, res = profundidad(s), []
    for m in FUERTE.finditer(s):
        if prof[m.start()] != 0 or re.search(r'(?i)\bon\s*$', s[:m.start()]):   # ON DELETE CASCADE no es un DELETE
            continue
        res.append((m.lastgroup, m.start(), m.end()))
    return res


def comandos(masc, a, b, unidad_rutina):
    """Los comandos de la sentencia masc[a:b], como dicts {tipo, ini, fin, kw}. Lo que no se reconoce va como
    'desconocida'; una rutina cuyo cuerpo quedo partido por un ';', como 'inseparable'."""
    s = masc[a:b]
    if not s.strip():
        return []
    pal = re.match(r'\s*([A-Za-z_]+)', s)
    primera = pal.group(1).lower() if pal else ''
    ini0 = a + (pal.start(1) if pal else len(s) - len(s.lstrip()))
    if primera in ATOMICAS:
        return [{'tipo': 'neutra', 'ini': ini0, 'fin': b, 'kw': ini0}]
    if primera == 'call' or (primera == 'do' and re.match(r'(?is)\s*do\s*(\$|language\b)', s)):
        return [{'tipo': 'opaca', 'ini': ini0, 'fin': b, 'kw': ini0}]
    marcas = marcas_fuertes(s)
    if not marcas:
        return [{'tipo': 'neutra' if primera in NEUTRAS else 'desconocida', 'ini': ini0, 'fin': b, 'kw': ini0}]
    res = []
    for k, (tipo, ini, kw) in enumerate(marcas):
        fin = marcas[k + 1][1] if k + 1 < len(marcas) else len(s)
        if tipo in ('rutina', 'combina'):   # el resto de la sentencia es su cuerpo
            if tipo == 'rutina' and not unidad_rutina and re.search(r'(?i)\bbegin\b', s[kw:]):
                tipo = 'inseparable'
            res.append({'tipo': tipo, 'ini': a + ini, 'fin': b, 'kw': a + kw})
            break
        res.append({'tipo': tipo, 'ini': a + ini, 'fin': a + fin, 'kw': a + kw})
    return res


def tramos(masc):
    """[(a, b, unidad_rutina)]: las sentencias. Con GO, primero los lotes; un lote que empieza con una rutina es
    una sola unidad (su cuerpo no se parte por los ';' de adentro)."""
    lotes, prev = [], 0
    hay_go = False
    for m in GO.finditer(masc):
        hay_go = True
        lotes.append((prev, m.start()))
        prev = m.end()
    lotes.append((prev, len(masc)))
    res = []
    for a, b in lotes:
        marcas = marcas_fuertes(masc[a:b])
        if hay_go and marcas and marcas[0][0] == 'rutina':
            res.append((a, b, True))
            continue
        ini = a
        for m in re.finditer(';', masc[a:b]):
            res.append((ini, a + m.start(), False))
            ini = a + m.end()
        res.append((ini, b, False))
    return res

# ---------------------------------------------------------------------------------------------------------
# Clasificar cada comando
# ---------------------------------------------------------------------------------------------------------

VERBOS_NEUTROS = re.compile(r'(?i)(set|owner|enable|disable|validate|nocheck|check|with|attach|detach|inherit|no|cluster|'
                            r'reset|replica|force|engine|comment|default|character|collate|row_format|rebuild|switch|'
                            r'auto_increment|algorithm|lock)\b')
COLUMNA_NEUTRA = re.compile(r'(?is)((set|drop)\s+default\b|drop\s+not\s+null\b|set\s+(statistics|storage|compression)\b|'
                            r'(add|set|drop)\s+(generated|identity)\b|restart\b|(set|reset)\s*\(|(set\s+)?(visible|invisible)\b)')
OBJETOS = {'view': 'la vista', 'materialized view': 'la vista materializada', 'function': 'la funcion',
           'procedure': 'la rutina', 'proc': 'la rutina', 'trigger': 'la rutina (disparador)', 'package': 'la rutina (paquete)',
           'sequence': 'la secuencia', 'type': 'el tipo', 'schema': 'el esquema', 'domain': 'el dominio',
           'extension': 'la extension', 'database': 'la base'}
CON_VALOR = re.compile(r'(?i)\b(default|identity|generated|serial|bigserial|smallserial|auto_increment)\b')


def accion_alter(a, tabla, previa_columna):
    """(tipo, que, marca) de una accion de ALTER TABLE. marca: 'obligatoria', 'restriccion', 'desconocida' o None."""
    m = re.match(r'(?is)add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?(.*)', a)
    seguida = (previa_columna and not re.match(r'(?i)(add|drop|alter|rename|modify|change)\b', a)
               and not VERBOS_NEUTROS.match(a))   # SQL Server: ADD a INT NULL, b INT NULL
    if m or seguida:
        cuerpo = m.group(1) if m else a
        if re.match(r'(?i)(constraint|primary|foreign|unique|check|index|key|fulltext|spatial|period|exclude)\b', cuerpo):
            return 'NEUTRA', 'agrega una restriccion o un indice a %s' % tabla, 'restriccion'
        col = nombre(cuerpo)[0] if not cuerpo.startswith('(') else '(varias)'
        oblig = re.search(r'(?i)\bnot\s+null\b', cuerpo) and not CON_VALOR.search(cuerpo)
        return 'EXPANDIR', 'agrega la columna %s a %s' % (col, tabla), ('obligatoria' if oblig else None)
    m = re.match(r'(?is)drop\s+(.*)', a)
    if m:
        cuerpo = m.group(1)
        if re.match(r'(?i)(index|key)\b', cuerpo):
            return 'NEUTRA', 'borra un indice de %s' % tabla, None
        if re.match(r'(?i)(constraint|primary|foreign|check)\b', cuerpo):
            return 'CONTRAER', 'borra una restriccion de %s' % tabla, None
        if re.match(r'(?i)(default|system\s+versioning|period)\b', cuerpo):
            return 'NEUTRA', 'cambia un valor por defecto de %s' % tabla, None
        col = nombre(re.sub(r'(?is)^(column\s+)?(if\s+exists\s+)?', '', cuerpo))[0] or '(varias)'
        return 'CONTRAER', 'borra la columna %s de %s' % (col, tabla), None
    if re.match(r'(?i)rename\b', a):
        if re.match(r'(?i)rename\s+(index|key|constraint)\b', a):
            return 'NEUTRA', 'renombra un indice o una restriccion de %s' % tabla, None
        return 'CONTRAER', 'renombra %s o una de sus columnas' % tabla, None
    m = re.match(r'(?is)alter\s+(?:column\s+)?', a)
    if m:
        resto = a[m.end():]
        if re.match(r'(?i)index\b', resto):
            return 'NEUTRA', 'cambia un indice de %s' % tabla, None
        col, fin = nombre(resto)
        cambio = resto[fin:].strip()
        if COLUMNA_NEUTRA.match(cambio):
            return 'NEUTRA', 'cambia el valor por defecto o permite nulos en %s.%s' % (tabla, col), None
        if re.match(r'(?i)set\s+not\s+null\b', cambio):
            return 'CONTRAER', 'pasa %s.%s a obligatoria' % (tabla, col), None
        if re.match(r'(?i)(set\s+data\s+)?type\b', cambio):
            return 'CONTRAER', 'cambia el tipo de %s.%s' % (tabla, col), None
        return 'CONTRAER', 'cambia el tipo o la nulabilidad de %s.%s' % (tabla, col), None
    if re.match(r'(?i)(modify|change)\b', a):
        return 'CONTRAER', 'cambia una columna de %s (MODIFY o CHANGE)' % tabla, None
    if VERBOS_NEUTROS.match(a):
        return 'NEUTRA', 'cambia una opcion de %s' % tabla, None
    return 'NEUTRA', 'una accion de ALTER TABLE que no se reconoce en %s' % tabla, 'desconocida'


def combinar(tipos):
    if 'EXPANDIR' in tipos and 'CONTRAER' in tipos:
        return 'MIXTA'
    return 'CONTRAER' if 'CONTRAER' in tipos else 'EXPANDIR' if 'EXPANDIR' in tipos else 'NEUTRA'


def clasificar_sql(texto, numeros=None):
    """{clase, sentencias, hallazgos, avisos, motivo} de un SQL. numeros: el numero de linea real de cada linea
    del texto (para las lineas agregadas de una migracion modificada); sin el, la linea es la del texto.

    Una barra antes de una comilla adentro de un texto (It\\'s) se lee distinto segun el motor: en MySQL escapa
    la comilla y el texto sigue; en el estandar el texto termina ahi. Se clasifican las dos lecturas: si dan
    distinto, la migracion queda SIN CLASIFICAR (lo que una esconde, la otra lo ve)."""
    texto = texto.replace('\r\n', '\n').replace('\r', '\n').replace(BOM, ' ')
    masc = enmascarar(texto)
    otra = enmascarar(texto, barra=True)
    r = clasificar_mascara(masc, numeros)
    if otra != masc:
        r2 = clasificar_mascara(otra, numeros)
        n = masc.count('\n', 0, texto.find(chr(92) + "'")) + 1 if chr(92) + "'" in texto else 1
        n = numeros[n - 1] if numeros and n - 1 < len(numeros) else n
        if r2['clase'] != r['clase']:
            motivo = ('linea %d: una barra antes de una comilla adentro de un texto: segun el motor el texto termina '
                      'ahi o sigue, y las dos lecturas dan distinto (%s y %s)' % (n, r['clase'], r2['clase']))
            r['clase'], r['motivo'] = 'SIN CLASIFICAR', '; '.join(x for x in (r['motivo'], motivo) if x)
        else:
            r['avisos'].append('linea %d: una barra antes de una comilla adentro de un texto: se leyo como estandar y '
                               'como MySQL, y las dos dan %s' % (n, r['clase']))
    return r


def clasificar_mascara(masc, numeros=None):
    """clasificar_sql sobre un texto ya enmascarado."""
    def linea(pos):
        n = masc.count('\n', 0, pos) + 1
        return numeros[n - 1] if numeros and n - 1 < len(numeros) else n

    cmds = []
    for a, b, unidad in tramos(masc):
        cmds += comandos(masc, a, b, unidad)
    # lo que se vuelve a crear en el mismo archivo (vistas y rutinas): borrarlo antes no contrae
    creados = []
    for k, c in enumerate(cmds):
        if c['tipo'] == 'vista' or (c['tipo'] == 'rutina' and masc[c['ini']:c['kw']].lower().startswith('create')):
            resto = masc[c['kw']:c['fin']]
            creados.append((k, clave(nombre(SI_EXISTE.sub('', resto, 1))[0])))
    nuevas, temporales = set(), set()
    sentencias, hallazgos, avisos, sin_clasificar = [], [], [], []

    def anotar(c, tipo, que):
        sentencias.append({'linea': linea(c['ini']), 'tipo': tipo, 'que': que,
                           'texto': re.sub(r'\s+', ' ', masc[c['ini']:c['fin']]).strip()[:90]})

    for k, c in enumerate(cmds):
        t, n = c['tipo'], linea(c['ini'])
        resto = masc[c['kw']:c['fin']]
        objeto, fin_obj = nombre(SI_EXISTE.sub('', resto, 1))
        tabla = clave(objeto)
        propia = tabla in nuevas or tabla in temporales or tabla.startswith('#')
        if t == 'neutra':
            continue
        if t == 'desconocida':
            anotar(c, 'DESCONOCIDA', 'no se reconoce la sentencia')
            sin_clasificar.append('linea %d: no se reconoce la sentencia' % n)
        elif t == 'opaca':
            anotar(c, 'OPACA', 'ejecuta algo que no se ve (EXEC, CALL o DO)')
            sin_clasificar.append('linea %d: ejecuta algo que no se ve (EXEC, CALL o DO): lo que corre adentro no se clasifica' % n)
        elif t == 'inseparable':
            anotar(c, 'INSEPARABLE', 'una rutina con BEGIN ... END sin separador de lote')
            sin_clasificar.append('linea %d: una rutina con BEGIN ... END sin separador de lote (GO): no se sabe donde '
                                  'termina su cuerpo' % n)
        elif t == 'rutina':
            anotar(c, 'RUTINA', 'crea o cambia una rutina')
            avisos.append('linea %d: crea o cambia una rutina (funcion, procedimiento o disparador): su cuerpo no se '
                          'clasifica' % n)
        elif t == 'tabla':
            temp = re.search(r'(?i)\b(temp|temporary)\b', masc[c['ini']:c['kw']]) or tabla.startswith('#')
            if temp:
                temporales.add(tabla)
                anotar(c, 'NEUTRA', 'crea la tabla temporal %s' % objeto)
            else:
                nuevas.add(tabla)
                anotar(c, 'EXPANDIR', 'crea la tabla %s' % objeto)
        elif t == 'indice':
            anotar(c, 'EXPANDIR', 'crea un indice')
        elif t == 'vista':
            anotar(c, 'NEUTRA', 'crea o reemplaza la vista %s' % objeto)
        elif t == 'crea_otro':
            anotar(c, 'EXPANDIR', 'crea %s' % re.sub(r'\s+', ' ', masc[c['ini']:c['kw']]).strip().lower())
        elif t == 'alter_tabla':
            despues = re.sub(r'(?is)^\s*only\s+', '', SI_EXISTE.sub('', resto, 1))
            objeto, fin_obj = nombre(despues)
            tabla = clave(objeto)
            propia = tabla in nuevas or tabla in temporales or tabla.startswith('#')
            if propia:
                anotar(c, 'NEUTRA', 'cambia %s, que crea esta misma migracion' % objeto)
                continue
            tipos, ques, previa = [], [], False
            for acc in partir_comas(despues[fin_obj:]):
                tipo, que, marca = accion_alter(acc, objeto, previa)
                previa = tipo == 'EXPANDIR' and que.startswith('agrega la columna')
                tipos.append(tipo)
                if tipo != 'NEUTRA' or marca:
                    ques.append(que)
                if marca == 'obligatoria':
                    hallazgos.append('linea %d: columna nueva obligatoria y sin valor por defecto en %s, que ya tiene '
                                     'datos: rompe lo que inserta hoy (migracion-de-base.md, regla dura 1)' % (n, objeto))
                elif marca == 'restriccion':
                    avisos.append('linea %d: agrega una restriccion a %s, que ya tiene datos: puede fallar con los datos '
                                  'reales (se prueba con volumen, migracion-de-base.md)' % (n, objeto))
                elif marca == 'desconocida':
                    avisos.append('linea %d: una accion de ALTER TABLE que no se reconoce en %s: se mira a mano' % (n, objeto))
            anotar(c, combinar(tipos), '; '.join(ques) or 'cambia una opcion de %s' % objeto)
        elif t == 'alter_otro':
            que_obj = re.sub(r'\s+', ' ', masc[c['ini']:c['kw']]).strip().lower()
            if 'index' not in que_obj and re.search(r'(?i)\b(drop|rename)\b', resto):
                anotar(c, 'CONTRAER', 'borra o renombra parte de %s (%s)' % (objeto, que_obj))
            else:
                anotar(c, 'NEUTRA', 'cambia %s (%s)' % (objeto, que_obj))
        elif t == 'borra':
            que_obj = re.sub(r'\s+', ' ', masc[c['ini']:c['kw']]).strip().lower()[5:]
            nombres = [clave(x) for x in partir_comas(SI_EXISTE.sub('', resto, 1).split('(')[0])] or [tabla]
            if que_obj == 'index':
                anotar(c, 'NEUTRA', 'borra un indice')
            elif que_obj == 'table':
                ajenas = [x for x in nombres if not (x in nuevas or x in temporales or x.startswith('#'))]
                if ajenas:
                    anotar(c, 'CONTRAER', 'borra la tabla %s' % ', '.join(ajenas))
                else:
                    anotar(c, 'NEUTRA', 'borra una tabla temporal o creada en esta misma migracion')
            elif que_obj in ('view', 'materialized view', 'function', 'procedure', 'proc', 'trigger', 'package'):
                if any(j > k and nom == tabla for j, nom in creados):
                    anotar(c, 'NEUTRA', 'borra y vuelve a crear %s' % objeto)
                else:
                    anotar(c, 'CONTRAER', 'borra %s %s y no la vuelve a crear' % (OBJETOS.get(que_obj, que_obj), objeto))
            else:
                anotar(c, 'CONTRAER', 'borra %s %s' % (OBJETOS.get(que_obj, que_obj), objeto))
        elif t == 'vacia':
            anotar(c, 'NEUTRA' if propia else 'CONTRAER', 'vacia la tabla %s' % objeto)
        elif t == 'renombra':
            anotar(c, 'CONTRAER', 'renombra una tabla o una columna (RENAME TABLE o sp_rename)')
        elif t in ('inserta', 'actualiza', 'combina'):
            anotar(c, 'DATOS', 'cambia datos (%s)' % {'inserta': 'INSERT', 'actualiza': 'UPDATE', 'combina': 'MERGE'}[t])
            avisos.append('linea %d: cambia datos (%s): el volumen y lo que tarda no se miran' % (
                n, {'inserta': 'INSERT', 'actualiza': 'UPDATE', 'combina': 'MERGE'}[t]))
        elif t == 'borra_filas':
            destino = clave(nombre(re.sub(r'(?is)^\s*from\s+', '', resto))[0])
            if re.search(r'(?i)\bwhere\b', resto):
                anotar(c, 'DATOS', 'borra filas (DELETE con WHERE)')
                avisos.append('linea %d: borra filas (DELETE con WHERE): cambia datos, y los datos borrados no vuelven' % n)
            elif destino in nuevas or destino in temporales or destino.startswith('#'):
                anotar(c, 'NEUTRA', 'borra las filas de una tabla temporal o creada en esta misma migracion')
            else:
                anotar(c, 'CONTRAER', 'borra todas las filas de %s (DELETE sin WHERE: es vaciar la tabla)' % destino)

    tipos = [s['tipo'] for s in sentencias]
    if not cmds:
        sin_clasificar.append('no tiene ninguna sentencia SQL')
    expande = [s['linea'] for s in sentencias if s['tipo'] in ('EXPANDIR', 'MIXTA')]
    contrae = [s['linea'] for s in sentencias if s['tipo'] in ('CONTRAER', 'MIXTA')]
    if expande and contrae:
        hallazgos.insert(0, 'expande (linea %d) y contrae (linea %d) en la misma migracion: van en despliegues distintos '
                            '(migracion-de-base.md)' % (expande[0], contrae[0]))
    if sin_clasificar:
        clase = 'SIN CLASIFICAR'
    else:
        clase = combinar(['EXPANDIR' if t in ('EXPANDIR', 'MIXTA') else 'CONTRAER' if t == 'CONTRAER' else 'NEUTRA'
                          for t in tipos] + (['CONTRAER'] if 'MIXTA' in tipos else []))
    return {'clase': clase, 'sentencias': sentencias, 'hallazgos': hallazgos, 'avisos': avisos,
            'motivo': '; '.join(sin_clasificar)}

# ---------------------------------------------------------------------------------------------------------
# El diff y el rango
# ---------------------------------------------------------------------------------------------------------

# El lector de diff es el comun (auditoria/diff.py, el mismo de auditar-diff y atajos): cuenta las lineas de cada
# bloque de los dos lados, y un comentario SQL borrado ('--- ...') no se toma por cabecera.
leer_diff = lector.archivos


def es_migracion(ruta, carpeta=''):
    r = ruta.replace('\\', '/')
    if NO_ES_MIGRACION.search(r):
        return False
    if carpeta:
        c = carpeta.replace('\\', '/').strip('/')
        return r.startswith(c + '/')
    return bool(CARPETAS.search(os.path.dirname(r)))


def clasificar_archivo(a):
    """El resultado de una migracion del diff."""
    base = {'ruta': a['ruta'], 'nueva': a['nueva'], 'sentencias': [], 'hallazgos': [], 'avisos': []}
    if not a['ruta'].lower().endswith('.sql'):
        base.update(clase='SIN CLASIFICAR', motivo='no es SQL (%s): este script solo lee SQL; se mira a mano' % (
            os.path.splitext(a['ruta'])[1] or 'sin extension'))
        return base
    numeros = [n for n, _ in a['lineas']]
    r = clasificar_sql('\n'.join(t for _, t in a['lineas']), numeros)
    base.update(r)
    if not a['nueva']:
        base['avisos'].insert(0, 'ya existia y se modifico: si ya corrio en algun ambiente, la herramienta no la vuelve a '
                                 'correr; se clasificaron solo sus lineas nuevas')
    return base


def evaluar(archivos, carpeta='', arbol=None):
    """El veredicto sobre los archivos de un diff. arbol: las rutas del repositorio en la version candidata
    (None con --archivo, y entonces un cero de migraciones no se puede comprobar)."""
    res = {'estado': 'SIN DATOS', 'motivo': '', 'migraciones': [], 'hallazgos': [], 'avisos': [],
           'resumen': dict((c, 0) for c in CLASES), 'no_mira': list(NO_MIRA)}
    if not archivos:
        res['motivo'] = 'el diff no nombra ningun archivo: no hay nada que clasificar (o no es un diff)'
        return res
    c = carpeta.replace('\\', '/').strip('/') if carpeta else ''
    if arbol is not None and c and not any(p.startswith(c + '/') for p in arbol):
        res['motivo'] = 'la carpeta %s no existe en la version candidata: no se sabe donde viven las migraciones' % c
        return res
    migr = [a for a in archivos if es_migracion(a['ruta'], c)]
    otros = [a for a in archivos if not es_migracion(a['ruta'], c)]
    sueltos = [a['ruta'] for a in otros if a['ruta'].lower().endswith('.sql') and not a['borrada']]
    if not migr:
        if arbol is None:
            if sueltos and not c:
                res['motivo'] = ('no se sabe donde viven las migraciones: el diff trae SQL fuera de una carpeta de '
                                 'migraciones reconocible (%s). Pasale --carpeta <ruta>' % ', '.join(sueltos[:5]))
            else:
                res['motivo'] = ('el diff no toca ninguna migracion%s, y sin el arbol del repositorio no se puede comprobar '
                                 'que ese cero sea real (correlo con --repo)' % (' en %s' % c if c else ''))
            return res
        if not c and not any(es_migracion(p) for p in arbol):
            res['motivo'] = ('no se sabe donde viven las migraciones: el repositorio no tiene una carpeta de migraciones '
                             'reconocible%s. Pasale --carpeta <ruta>' % (
                                 ' y el rango trae SQL suelto (%s)' % ', '.join(sueltos[:5]) if sueltos else ''))
            return res
        res['estado'] = 'OK'
        res['motivo'] = 'el rango no trae migraciones nuevas'
        return res
    for a in migr:
        if a['borrada']:
            res['avisos'].append('%s: se borro una migracion: si ya corrio en algun ambiente, la herramienta pierde su '
                                 'historial' % a['ruta'])
            continue
        r = clasificar_archivo(a)
        res['migraciones'].append(r)
        res['resumen'][r['clase']] += 1
        res['hallazgos'] += ['%s: %s' % (a['ruta'], h) for h in r['hallazgos']]
        res['avisos'] += ['%s: %s' % (a['ruta'], v) for v in r['avisos']]
    contraen = [m['ruta'] for m in res['migraciones'] if m['clase'] in ('CONTRAER', 'MIXTA')]
    codigo = [a['ruta'] for a in otros if not DOCS.search(a['ruta']) and a['ruta'] not in sueltos]
    for r in contraen:
        res['avisos'].append('%s contrae: borrar, renombrar o restringir no se deshace; lleva dos "si" en turnos distintos '
                             '(GATE de DESPLIEGUE) y solo con la version que dejo de usarlo ya desplegada' % r)
    if contraen and codigo:
        res['avisos'].append('el mismo rango trae %d archivo(s) de codigo: contraer va en su propio despliegue, despues '
                             'de que la version que dejo de usarlo este en el ambiente' % len(codigo))
    if sueltos:
        res['avisos'].append('hay SQL fuera de la carpeta de migraciones (%s): no se clasifico' % ', '.join(sueltos[:5]))
    sin_clasif = [m for m in res['migraciones'] if m['clase'] == 'SIN CLASIFICAR']
    if res['hallazgos']:
        res['estado'] = 'HALLAZGO'
    elif sin_clasif:
        res['estado'] = 'SIN DATOS'
        res['motivo'] = '%d migracion(es) SIN CLASIFICAR: no se pudo saber si contraen' % len(sin_clasif)
    elif not res['migraciones']:
        res['estado'], res['motivo'] = 'OK', 'el rango no trae migraciones nuevas'
    else:
        res['estado'] = 'OK'
    return res


def git(repo, *args):
    # bytes y despues texto: en modo texto, una \r suelta del contenido se volveria un fin de linea
    r = subprocess.run(['git', '-C', repo] + list(args), capture_output=True)
    return r.returncode, r.stdout.decode('utf-8', 'replace')


def desde_repo(repo, base, hasta='HEAD', carpeta=''):
    """El veredicto sobre las migraciones que el rango base...hasta agrega en el repositorio (solo lectura)."""
    vacio = {'estado': 'SIN DATOS', 'motivo': '', 'migraciones': [], 'hallazgos': [], 'avisos': [],
             'resumen': dict((c, 0) for c in CLASES), 'no_mira': list(NO_MIRA)}
    if git(repo, 'rev-parse', '--is-inside-work-tree')[0] != 0:
        vacio['motivo'] = '%s no es un repositorio git' % repo
        return vacio
    for ref in (base, hasta):
        if git(repo, 'rev-parse', '--verify', '--quiet', ref + '^{commit}')[0] != 0:
            vacio['motivo'] = 'git no conoce la referencia %s en %s (proba con un fetch)' % (ref, repo)
            return vacio
    rc, diff = git(repo, '-c', 'core.quotepath=off', 'diff', '--no-color', '--no-ext-diff', '--no-textconv',
                   '--no-renames', base + '...' + hasta)
    if rc != 0:
        vacio['motivo'] = 'git no pudo armar el diff %s...%s' % (base, hasta)
        return vacio
    if not diff.strip():
        vacio['motivo'] = 'el rango %s...%s no trae ningun cambio: no hay nada que clasificar' % (base, hasta)
        return vacio
    rc, arbol = git(repo, '-c', 'core.quotepath=off', 'ls-tree', '-r', '--name-only', hasta)
    if rc != 0:
        vacio['motivo'] = 'git no pudo listar los archivos de %s' % hasta
        return vacio
    return evaluar(leer_diff(diff), carpeta, [p for p in arbol.splitlines() if p.strip()])


def imprimir(res, origen):
    print('CLASIFICAR MIGRACIONES -- %s  [%s; %d migracion(es) en el rango: %s]' % (
        res['estado'], origen, len(res['migraciones']),
        ', '.join('%d %s' % (n, c) for c, n in res['resumen'].items() if n) or 'ninguna'))
    for m in res['migraciones']:
        print('  %-15s %s%s' % (m['clase'], m['ruta'], '' if m['nueva'] else '  (ya existia)'))
        for s in m['sentencias']:
            print('      linea %d: %-11s %s' % (s['linea'], s['tipo'], s['que']))
        if m.get('motivo'):
            print('      SIN CLASIFICAR: %s' % m['motivo'])
    if res['motivo']:
        print('  %s: %s' % ('SIN DATOS' if res['estado'] == 'SIN DATOS' else 'nota', res['motivo']))
    for h in res['hallazgos']:
        print('  HALLAZGO: ' + h)
    for v in res['avisos'][:60]:
        print('  aviso: ' + v)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')


def main():
    ap = argparse.ArgumentParser(description='EXPANDIR, CONTRAER o MIXTA por cada migracion nueva de un rango (solo lectura).')
    ap.add_argument('--repo', default='')
    ap.add_argument('--base', default='')
    ap.add_argument('--hasta', default='HEAD')
    ap.add_argument('--archivo', default='', help='un diff ya generado (git diff), en vez de leerlo del repositorio')
    ap.add_argument('--carpeta', default='', help='donde viven las migraciones, relativa al repositorio')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if a.archivo:
        try:
            with open(a.archivo, 'rb') as h:
                texto = h.read().decode('utf-8', 'replace')
        except OSError as e:
            print('SIN DATOS -- no se pudo leer el diff %s: %s' % (a.archivo, e))
            return SIN_DATOS
        if not texto.strip():
            print('SIN DATOS -- el diff %s esta vacio: no hay nada que clasificar.' % a.archivo)
            return SIN_DATOS
        res, origen, rango = evaluar(leer_diff(texto), a.carpeta, None), 'diff %s' % a.archivo, None
    elif a.repo:
        if not a.base:
            print('SIN DATOS -- falta --base: lo que ya esta en el ambiente (un tag o un commit).')
            return SIN_DATOS
        res = desde_repo(os.path.abspath(a.repo), a.base, a.hasta or 'HEAD', a.carpeta)
        origen, rango = 'rango %s...%s' % (a.base, a.hasta or 'HEAD'), {'base': a.base, 'hasta': a.hasta or 'HEAD'}
    else:
        print('SIN DATOS -- falta --repo <repo> --base <ref>, o --archivo <diff>.')
        return SIN_DATOS

    codigo = {'OK': OK, 'HALLAZGO': HALLAZGO}.get(res['estado'], SIN_DATOS)
    if a.json:
        salida = dict(res)
        salida.update(rango=rango, archivo=a.archivo or None, carpeta=a.carpeta or None)
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        imprimir(res, origen)
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
