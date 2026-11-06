#!/usr/bin/env python3
"""Esquema REAL de una base de datos, a Markdown y Mermaid. SOLO LECTURA, nunca filas de datos.

    python bin/esquema-base.py <archivo.sqlite | archivo.db | carpeta-o-archivo-con-DDL.sql> [--salida esquema.md] [--conteos] [--json]
    python bin/esquema-base.py <carpeta-de-migraciones> --aplicar      (corre V<n>__*.sql en orden sobre un SQLite en memoria y lee el esquema RESULTANTE)

Tres estados, nunca dos:  0 = esquema listo   1 = (no aplica)   2 = SIN DATOS (no es una base ni hay DDL)

POR QUE EXISTE. La radiografia lee el DDL que esta en el repositorio; pero el esquema que manda es el de la base
REAL (columnas que nadie migro, tablas que nadie usa, indices que faltan). Esto lo saca de un SQLite con biblioteca
estandar, o de archivos .sql (CREATE TABLE) de cualquier motor, y lo deja en texto versionable: tablas, columnas con
tipo y nulidad, claves, foraneas, indices, y el diagrama entidad-relacion en Mermaid. Con --conteos agrega SOLO la
cantidad de filas por tabla (un agregado), nunca contenido.

OTROS MOTORES (Postgres, MySQL, SQL Server). La biblioteca estandar no trae driver. Dos caminos: exportar el DDL
(`pg_dump --schema-only`, `mysqldump --no-data`, el generador de scripts de SSMS) y pasarselo a este script; o usar
una herramienta externa de documentacion de esquemas (tbls, SchemaCrawler) declarada en DEPENDENCIAS-EXTERNAS.md,
con acceso de SOLO LECTURA y sin datos. Lo que entra al Cerebro es el Markdown y el Mermaid, de donde salgan.

SOBRE UNA CARPETA sin --aplicar solo se leen los CREATE TABLE: un ALTER TABLE de una migracion posterior NO se refleja, y el
script lo avisa. Para ver el esquema que queda despues de todas las migraciones (dialecto SQLite), --aplicar.

QUE NO HACE. No lee filas, no modifica la base, no adivina relaciones que el DDL no declara.
"""

import argparse
import glob
import json
import os
import re
import sqlite3
import sys

OK, _, SIN_DATOS = 0, 1, 2
CREATE = re.compile(r'(?is)create\s+table\s+(?:if\s+not\s+exists\s+)?((?:[`"\[]?\w+[`"\]]?\s*\.\s*)?[`"\[]?\w+[`"\]]?)\s*\((.*?)\)\s*(?:;|$)')
CUENTA_CREATE = re.compile(r'(?i)create\s+table\b')
FK = re.compile(r'(?i)foreign\s+key\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)\s*references\s+[`"\[]?([\w.]+)[`"\]]?\s*\(\s*[`"\[]?(\w+)[`"\]]?')
PK_LINEA = re.compile(r'(?i)primary\s+key\s*\(([^)]*)\)')


def de_sqlite(ruta, conteos):
    con = sqlite3.connect('file:%s?mode=ro' % ruta.replace('\\', '/'), uri=True)
    try:
        return de_conexion(con, conteos)
    finally:
        con.close()


def aplicar_migraciones(carpeta):
    """Corre V<n>__*.sql en orden (por numero) sobre un SQLite en memoria y devuelve (conexion, aplicadas)."""
    archivos = sorted(glob.glob(os.path.join(carpeta, '**', 'V*__*.sql'), recursive=True),
                      key=lambda p: int(re.match(r'V(\d+)__', os.path.basename(p)).group(1)))
    con = sqlite3.connect(':memory:')
    for p in archivos:
        with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
            con.executescript(h.read())
    return con, [os.path.basename(p) for p in archivos]


def de_conexion(con, conteos):
    cur = con.cursor()
    tablas = []
    for (nombre,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
        cols = [{'nombre': c[1], 'tipo': c[2] or '', 'nulo': not c[3] and not c[5], 'pk': bool(c[5])} for c in cur.execute('PRAGMA table_info("%s")' % nombre).fetchall()]
        fks = [{'columna': f[3], 'tabla': f[2], 'ref': f[4]} for f in cur.execute('PRAGMA foreign_key_list("%s")' % nombre).fetchall()]
        idx = [i[1] for i in cur.execute('PRAGMA index_list("%s")' % nombre).fetchall() if not i[1].startswith('sqlite_autoindex')]
        t = {'tabla': nombre, 'columnas': cols, 'foraneas': fks, 'indices': idx}
        if conteos:
            t['filas'] = cur.execute('SELECT COUNT(*) FROM "%s"' % nombre).fetchone()[0]
        tablas.append(t)
    return tablas


def de_ddl(ruta):
    archivos = [ruta] if os.path.isfile(ruta) else sorted(glob.glob(os.path.join(ruta, '**', '*.sql'), recursive=True))
    tablas = []
    for p in archivos:
        try:
            with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
                sql = h.read()
        except OSError:
            continue
        vistos = len(CUENTA_CREATE.findall(sql))
        parseados = 0
        for m in CREATE.finditer(sql):
            parseados += 1
            nombre, cuerpo = re.sub(r'[`"\[\]\s]', '', m.group(1)), m.group(2)
            cols, fks, pks = [], [], set()
            for pk in PK_LINEA.finditer(cuerpo):
                pks.update(x.strip(' `"[]') for x in pk.group(1).split(','))
            for linea in re.split(r',\s*\n|,(?=\s*[`"\[]?\w+[`"\]]?\s+\w)', cuerpo):
                linea = linea.strip()
                if not linea or re.match(r'(?i)^(primary|foreign|constraint|unique|key|index|check)\b', linea):
                    fk = FK.search(linea)
                    if fk:
                        fks.append({'columna': fk.group(1), 'tabla': fk.group(2), 'ref': fk.group(3)})
                    continue
                mc = re.match(r'[`"\[]?(\w+)[`"\]]?\s+([\w()\s,]+?)(?:\s+(not\s+null|null|primary\s+key|default|references|unique|check|auto_increment|identity|generated)\b.*)?$', linea, re.I | re.S)
                if not mc:
                    continue
                nombre_col = mc.group(1)
                resto = linea.lower()
                es_pk = 'primary key' in resto or nombre_col in pks
                cols.append({'nombre': nombre_col, 'tipo': ' '.join(mc.group(2).split()), 'nulo': 'not null' not in resto and not es_pk, 'pk': es_pk})
                fk = re.search(r'(?i)references\s+((?:[`"\[]?\w+[`"\]]?\s*\.\s*)?[`"\[]?\w+[`"\]]?)\s*\(\s*[`"\[]?(\w+)', linea)
                if fk:
                    fks.append({'columna': nombre_col, 'tabla': re.sub(r'[`"\[\]\s]', '', fk.group(1)), 'ref': fk.group(2)})
            tablas.append({'tabla': nombre, 'columnas': cols, 'foraneas': fks, 'indices': [], 'origen': os.path.relpath(p, ruta if os.path.isdir(ruta) else os.path.dirname(ruta))})
        if parseados < vistos:
            print('  AVISO %s: vi %d CREATE TABLE y pude leer %d; el resto tiene una sintaxis que este script no reconoce (exportar el DDL mas simple, o usar tbls/SchemaCrawler)' % (os.path.basename(p), vistos, parseados))
    return tablas


def markdown(tablas, origen):
    L = ['# Esquema de la base - %s' % origen, '', '%d tabla(s). Generado por `bin/esquema-base.py` (solo esquema, nunca datos).' % len(tablas), '']
    for t in tablas:
        L.append('## %s%s' % (t['tabla'], (' - %s filas' % t['filas']) if 'filas' in t else ''))
        L.append('')
        L.append('| Columna | Tipo | Nulo | Clave |')
        L.append('|---|---|---|---|')
        for c in t['columnas']:
            clave = 'PK' if c['pk'] else ''
            for f in t['foraneas']:
                if f['columna'] == c['nombre']:
                    clave = (clave + ' ' if clave else '') + 'FK -> %s.%s' % (f['tabla'], f['ref'])
            L.append('| %s | %s | %s | %s |' % (c['nombre'], c['tipo'], 'si' if c['nulo'] else 'no', clave))
        if t.get('indices'):
            L.append('')
            L.append('Indices: ' + ', '.join('`%s`' % i for i in t['indices']))
        L.append('')
    L.append('```mermaid')
    L.append('erDiagram')
    for t in tablas:
        L.append('  %s {' % re.sub(r'\W', '_', t['tabla']))
        for c in t['columnas']:
            L.append('    %s %s%s' % (re.sub(r'\W', '_', c['tipo'].split('(')[0]) or 'col', c['nombre'], ' PK' if c['pk'] else (' FK' if any(f['columna'] == c['nombre'] for f in t['foraneas']) else '')))
        L.append('  }')
    for t in tablas:
        for f in t['foraneas']:
            L.append('  %s }o--|| %s : "%s"' % (re.sub(r'\W', '_', t['tabla']), re.sub(r'\W', '_', f['tabla']), f['columna']))
    L.append('```')
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description='Esquema de una base (SQLite o DDL) a Markdown y Mermaid.')
    ap.add_argument('origen')
    ap.add_argument('--salida', default='')
    ap.add_argument('--conteos', action='store_true', help='agrega la cantidad de filas por tabla (solo SQLite; un agregado, nunca contenido)')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--aplicar', action='store_true', help='carpeta de migraciones: correr V<n>__*.sql en orden sobre un SQLite en memoria y leer el esquema resultante')
    a = ap.parse_args()
    origen = os.path.abspath(a.origen)
    if not os.path.exists(origen):
        print('SIN DATOS -- no existe %s' % origen); return SIN_DATOS
    es_sqlite = False
    if os.path.isfile(origen):
        with open(origen, 'rb') as h:
            es_sqlite = h.read(16).startswith(b'SQLite format 3')
    aplicadas = []
    try:
        if a.aplicar and os.path.isdir(origen):
            con, aplicadas = aplicar_migraciones(origen)
            if not aplicadas:
                print('SIN DATOS -- --aplicar: no hay V<n>__*.sql en %s' % origen); return SIN_DATOS
            tablas = de_conexion(con, a.conteos)
            con.close()
            es_sqlite = True
        else:
            tablas = de_sqlite(origen, a.conteos) if es_sqlite else de_ddl(origen)
    except sqlite3.Error as e:
        print('SIN DATOS -- no pude leer la base%s: %s' % (' (al aplicar las migraciones; el dialecto no es SQLite?)' if a.aplicar else '', e)); return SIN_DATOS
    if not a.aplicar and not es_sqlite:
        alters = 0
        for p in ([origen] if os.path.isfile(origen) else glob.glob(os.path.join(origen, '**', '*.sql'), recursive=True)):
            try:
                with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
                    alters += len(re.findall(r'(?i)\balter\s+table\b', h.read()))
            except OSError:
                pass
        if alters:
            print('  AVISO vi %d ALTER TABLE que NO se reflejan en este esquema (solo se leen los CREATE TABLE): para el esquema resultante, --aplicar (SQLite) o una base migrada' % alters)
    if aplicadas:
        print('  (esquema resultante de aplicar en orden: %s)' % ', '.join(aplicadas))
    if a.conteos and not es_sqlite:
        print('  AVISO --conteos solo aplica a SQLite: con DDL no hay filas que contar')
    if not tablas:
        print('SIN DATOS -- no encontre tablas en %s (no es un SQLite ni tiene CREATE TABLE en .sql). Para otros motores: exportar el DDL o usar tbls/SchemaCrawler en solo lectura.' % origen); return SIN_DATOS
    if a.json:
        print(json.dumps({'origen': origen, 'motor': 'sqlite' if es_sqlite else 'ddl', 'tablas': tablas}, ensure_ascii=False, indent=1))
        return OK
    md = markdown(tablas, os.path.basename(origen))
    if a.salida:
        os.makedirs(os.path.dirname(os.path.abspath(a.salida)) or '.', exist_ok=True)
        with open(a.salida, 'w', encoding='utf-8', newline='\n') as h:
            h.write(md)
        print('OK -- esquema de %d tabla(s) (%s) escrito en %s' % (len(tablas), 'sqlite' if es_sqlite else 'ddl', a.salida))
    else:
        sys.stdout.write(md)
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
