#!/usr/bin/env python3
"""Prueba de bin/clasificar-migraciones.py sobre SQL, diffs plantados y un repositorio git TEMPORAL.
Se corre:  python -B bin/probar-clasificar-migraciones.py   -> OK o FALLA, con el detalle de cada caso.
Necesita git en el PATH para los casos de --repo (si no esta, esos casos se saltean y se dice)."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'clasificar-migraciones.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def cargar():
    """El script como modulo, o None si todavia no existe o no carga (los casos de funcion fallan, no explotan)."""
    try:
        spec = importlib.util.spec_from_file_location('clasificar_migraciones_prueba', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def sql(mod, texto):
    """(clase, hallazgos, avisos, tipos de sentencia) de un SQL suelto."""
    if mod is None:
        return 'NO CARGA', [], [], []
    r = mod.clasificar_sql(texto)
    return r['clase'], r['hallazgos'], r['avisos'], [s['tipo'] for s in r['sentencias']]


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def diff_nuevo(ruta, contenido):
    lineas = contenido.rstrip('\n').split('\n')
    return ('diff --git a/%s b/%s\nnew file mode 100644\nindex 0000000..1111111\n--- /dev/null\n+++ b/%s\n@@ -0,0 +1,%d @@\n'
            % (ruta, ruta, ruta, len(lineas))) + ''.join('+' + l + '\n' for l in lineas)


def diff_modificado(ruta, agregadas, desde=10):
    return ('diff --git a/%s b/%s\nindex 1111111..2222222 100644\n--- a/%s\n+++ b/%s\n@@ -%d,0 +%d,%d @@\n'
            % (ruta, ruta, ruta, ruta, desde, desde + 1, len(agregadas))) + ''.join('+' + l + '\n' for l in agregadas)


def sh(cwd, *cmd):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def commit(repo, msg):
    sh(repo, 'git', 'add', '-A')
    rc, out = sh(repo, 'git', 'commit', '-q', '-m', msg)
    assert rc == 0, out


EXPANDE = 'CREATE TABLE pedido (\n  id BIGINT PRIMARY KEY,\n  cliente_id BIGINT NOT NULL\n);\nCREATE INDEX ix_pedido_cliente ON pedido (cliente_id);\n'
CONTRAE = '-- ya nadie la usa\nALTER TABLE cliente DROP COLUMN telefono_viejo;\n'
MEZCLA = 'ALTER TABLE cliente ADD COLUMN telefono VARCHAR(30);\nALTER TABLE cliente DROP COLUMN telefono_viejo;\n'


def main():
    print('== clasificar-migraciones')
    mod = cargar()
    caso('el script carga como modulo (lo usa gate-despliegue.py)', mod is not None and hasattr(mod, 'clasificar_sql'))

    # ---- lo que EXPANDE
    caso('crear una tabla: EXPANDIR', sql(mod, 'CREATE TABLE pedido (id INT PRIMARY KEY, nota TEXT NOT NULL);')[0] == 'EXPANDIR')
    caso('agregar una columna que admite nulos: EXPANDIR', sql(mod, 'ALTER TABLE cliente ADD COLUMN telefono VARCHAR(30) NULL;')[0] == 'EXPANDIR')
    caso('agregar una columna sin la palabra COLUMN (SQL Server): EXPANDIR', sql(mod, 'ALTER TABLE dbo.cliente ADD telefono VARCHAR(30) NULL')[0] == 'EXPANDIR')
    caso('indice concurrente: EXPANDIR', sql(mod, 'CREATE INDEX CONCURRENTLY ix_c ON cliente (apellido);')[0] == 'EXPANDIR')
    c, h, v, t = sql(mod, 'ALTER TABLE cliente ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;')
    caso('columna obligatoria CON valor por defecto: EXPANDIR y sin hallazgo', c == 'EXPANDIR' and not h, (c, h))

    # ---- lo que CONTRAE
    caso('borrar una columna: CONTRAER', sql(mod, 'ALTER TABLE cliente DROP COLUMN telefono_viejo;')[0] == 'CONTRAER')
    caso('borrar una tabla: CONTRAER', sql(mod, 'DROP TABLE IF EXISTS cliente_viejo;')[0] == 'CONTRAER')
    caso('renombrar una columna: CONTRAER', sql(mod, 'ALTER TABLE cliente RENAME COLUMN tel TO telefono;')[0] == 'CONTRAER')
    caso('renombrar una tabla: CONTRAER', sql(mod, 'ALTER TABLE cliente RENAME TO persona;')[0] == 'CONTRAER')
    caso('renombrar con sp_rename (SQL Server): CONTRAER', sql(mod, "EXEC sp_rename 'dbo.cliente.tel', 'telefono', 'COLUMN';")[0] == 'CONTRAER')
    caso('cambiar el tipo (PostgreSQL): CONTRAER', sql(mod, 'ALTER TABLE cliente ALTER COLUMN edad TYPE BIGINT;')[0] == 'CONTRAER')
    caso('cambiar el tipo (SQL Server): CONTRAER', sql(mod, 'ALTER TABLE cliente ALTER COLUMN nombre VARCHAR(50) NOT NULL')[0] == 'CONTRAER')
    caso('cambiar el tipo (MySQL, MODIFY): CONTRAER', sql(mod, 'ALTER TABLE cliente MODIFY COLUMN edad BIGINT;')[0] == 'CONTRAER')
    caso('SET NOT NULL: CONTRAER', sql(mod, 'ALTER TABLE cliente ALTER COLUMN email SET NOT NULL;')[0] == 'CONTRAER')
    caso('borrar una restriccion: CONTRAER', sql(mod, 'ALTER TABLE cliente DROP CONSTRAINT uq_cliente_email;')[0] == 'CONTRAER')
    caso('vaciar una tabla (TRUNCATE): CONTRAER', sql(mod, 'TRUNCATE TABLE auditoria;')[0] == 'CONTRAER')
    caso('borrar todas las filas (DELETE sin WHERE) es vaciar la tabla: CONTRAER', sql(mod, 'DELETE FROM auditoria;')[0] == 'CONTRAER')
    c, h, v, t = sql(mod, 'DELETE FROM auditoria WHERE fecha < now();')
    caso('FP: DELETE con WHERE cambia datos, no el esquema: NEUTRA con aviso', c == 'NEUTRA' and any('datos' in x for x in v), (c, v))
    c, h, v, t = sql(mod, "EXEC dbo.limpiar_todo;\nCREATE TABLE a (id INT);")
    caso('ejecuta algo que no se ve (EXEC, CALL o DO): SIN CLASIFICAR, no OK', c == 'SIN CLASIFICAR', (c, t))
    caso('FP: el DO NOTHING de un INSERT ... ON CONFLICT no es un bloque DO', sql(mod, 'INSERT INTO rol (id) VALUES (1) ON CONFLICT DO NOTHING;')[0] == 'NEUTRA')
    caso('varias acciones en un ALTER: alcanza con que una contraiga', sql(mod, 'ALTER TABLE t ADD CONSTRAINT fk FOREIGN KEY (a) REFERENCES b(id) ON DELETE CASCADE, DROP COLUMN x;')[0] == 'CONTRAER')

    # ---- MIXTA y la columna obligatoria de una
    c, h, v, t = sql(mod, MEZCLA)
    caso('expande y contrae en la misma migracion: MIXTA, con su hallazgo', c == 'MIXTA' and any('misma migracion' in x for x in h), (c, h))
    c, h, v, t = sql(mod, 'ALTER TABLE cliente ADD COLUMN email VARCHAR(80) NOT NULL;')
    caso('columna nueva obligatoria y sin valor por defecto: HALLAZGO (regla dura 1 del metodo)', any('obligatoria' in x for x in h), (c, h))

    # ---- falsos positivos
    caso('FP: la palabra DROP en un comentario no contrae',
         sql(mod, '-- DROP TABLE cliente;\n/* ALTER TABLE x DROP COLUMN y; */\nCREATE TABLE a (id INT);')[0] == 'EXPANDIR')
    caso('FP: la palabra DROP adentro de un texto no contrae', sql(mod, "INSERT INTO bitacora (msg) VALUES ('DROP TABLE cliente; TRUNCATE x');")[0] == 'NEUTRA')
    BARRA = ("INSERT INTO mensajes (clave, texto) VALUES ('bienvenida', 'It" + chr(92) + "'s ok');\n"
             "ALTER TABLE clientes DROP COLUMN email;\nINSERT INTO mensajes (clave, texto) VALUES ('adios', 'chau');\n")
    c, h, v, t = sql(mod, BARRA)
    caso('una comilla escapada con barra (MySQL) no esconde un DROP COLUMN: SIN CLASIFICAR, nunca NEUTRA', c == 'SIN CLASIFICAR', (c, t))
    c, h, v, t = sql(mod, BARRA.replace(chr(92) + "'", "''"))
    caso('la misma migracion con la comilla doblada (estandar): CONTRAER', c == 'CONTRAER', (c, t))
    c, h, v, t = sql(mod, "INSERT INTO m (t) VALUES ('It" + chr(92) + "'s ok');\n")
    caso('FP: una barra antes de una comilla que da lo mismo en las dos lecturas: NEUTRA, con aviso',
         c == 'NEUTRA' and any('barra' in x for x in v), (c, v))
    c, h, v, t = sql(mod, 'CREATE TABLE t (id INT, a INT);\nALTER TABLE t ADD CONSTRAINT uq_t UNIQUE (a);\nALTER TABLE t ALTER COLUMN a SET NOT NULL;\n')
    caso('FP: restringir una tabla creada en la misma migracion no es MIXTA', c == 'EXPANDIR' and not h, (c, h))
    caso('FP: ON DELETE CASCADE de una clave foranea no es borrar', sql(mod, 'CREATE TABLE h (id INT, p INT REFERENCES p(id) ON DELETE CASCADE ON UPDATE CASCADE);')[0] == 'EXPANDIR')
    caso('FP: borrar un indice no contrae', sql(mod, 'DROP INDEX ix_viejo;')[0] == 'NEUTRA')
    caso('FP: una vista que se borra y se vuelve a crear no contrae', sql(mod, 'DROP VIEW IF EXISTS v_clientes;\nCREATE VIEW v_clientes AS SELECT id FROM cliente;')[0] == 'NEUTRA')
    caso('una vista que se borra y NO se vuelve a crear: CONTRAER', sql(mod, 'DROP VIEW v_clientes;')[0] == 'CONTRAER')
    caso('FP: SET DEFAULT y DROP NOT NULL no contraen',
         sql(mod, 'ALTER TABLE c ALTER COLUMN a SET DEFAULT 0;\nALTER TABLE c ALTER COLUMN b DROP NOT NULL;')[0] == 'NEUTRA')
    caso('FP: una columna que se llama drop_date o rename_log no contrae', sql(mod, 'ALTER TABLE c ADD COLUMN drop_date DATE, ADD COLUMN rename_log TEXT;')[0] == 'EXPANDIR')
    caso('FP: una tabla temporal que se crea y se borra no cuenta', sql(mod, 'CREATE TABLE #tmp (id INT);\nINSERT INTO #tmp VALUES (1);\nDROP TABLE #tmp;')[0] == 'NEUTRA')
    caso('SQL Server: un ALTER adentro de IF ... BEGIN ... END se ve igual (EXPANDIR)',
         sql(mod, "IF COL_LENGTH('dbo.cliente', 'tel') IS NULL\nBEGIN\n    ALTER TABLE dbo.cliente ADD tel VARCHAR(30) NULL\nEND\nGO\n")[0] == 'EXPANDIR')
    caso('SQL Server: un DROP COLUMN adentro de IF ... BEGIN ... END no se escapa (CONTRAER)',
         sql(mod, "IF COL_LENGTH('dbo.cliente', 'tel') IS NOT NULL\nBEGIN\n    ALTER TABLE dbo.cliente DROP COLUMN tel\nEND\nGO\n")[0] == 'CONTRAER')
    c, h, v, t = sql(mod, 'CREATE FUNCTION limpiar() RETURNS void AS $$\nBEGIN\n  DROP TABLE temporal_x;\nEND;\n$$ LANGUAGE plpgsql;\nCREATE TABLE nueva (id INT);\n')
    caso('FP: el cuerpo de una funcion ($$ ... $$) no se clasifica, y lo que sigue si', c == 'EXPANDIR', (c, t))
    caso('lo que sigue a una funcion ($$ ... $$) se sigue mirando: un DROP TABLE despues es CONTRAER',
         sql(mod, 'CREATE FUNCTION f() RETURNS void AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;\nDROP TABLE cliente_viejo;\n')[0] == 'CONTRAER')
    c, h, v, t = sql(mod, 'CREATE TABLE a (id INT)\nGO\nCREATE PROCEDURE limpiar AS\nBEGIN\n  TRUNCATE TABLE staging;\n  DELETE FROM b;\nEND\nGO\n')
    caso('FP: el cuerpo de un procedimiento (hasta el GO) no se clasifica, y se avisa', c == 'EXPANDIR' and any('rutina' in x for x in v), (c, v))
    c, h, v, t = sql(mod, 'CREATE PROCEDURE limpiar()\nBEGIN\n  DELETE FROM b;\nEND;\nDROP TABLE cliente_viejo;\n')
    caso('una rutina sin separador de lote y con un DROP despues: no se puede separar, SIN CLASIFICAR', c == 'SIN CLASIFICAR', (c, t))

    # ---- ni expande ni contrae, y lo que no se reconoce
    c, h, v, t = sql(mod, "INSERT INTO rol (id, nombre) VALUES (1, '<rol>');\nUPDATE cliente SET activo = TRUE WHERE activo IS NULL;\n")
    caso('solo datos (el paso MIGRAR): NEUTRA, y avisa que el volumen no se mira', c == 'NEUTRA' and any('datos' in x for x in v), (c, v))
    caso('texto que no es SQL reconocible: SIN CLASIFICAR', sql(mod, 'esto no es una migracion\nni nada parecido\n')[0] == 'SIN CLASIFICAR')
    caso('un archivo vacio: SIN CLASIFICAR', sql(mod, '\n\n')[0] == 'SIN CLASIFICAR')
    if mod is not None:
        r = mod.clasificar_sql('-- uno\nCREATE TABLE a (id INT);\n\nALTER TABLE b DROP COLUMN c;\n')
        caso('cada sentencia lleva su numero de linea', [(s['linea'], s['tipo']) for s in r['sentencias']] == [(2, 'EXPANDIR'), (4, 'CONTRAER')], r['sentencias'])
    else:
        caso('cada sentencia lleva su numero de linea', False, 'no carga')

    # ---- por linea de comandos, con un diff plantado
    tmp = tempfile.mkdtemp(prefix='probar-migr-')
    d = escribir(os.path.join(tmp, 'barra.diff'), diff_nuevo('db/migration/V7__mensajes.sql', BARRA))
    rc, out = correr('--archivo', d)
    caso('por linea de comandos, la migracion con \\\' sale SIN DATOS (2), no OK', rc == 2 and 'SIN CLASIFICAR' in out, out[:400])
    d = escribir(os.path.join(tmp, 'expande.diff'), diff_nuevo('db/migration/V12__pedido.sql', EXPANDE) + diff_nuevo('src/Pedido.java', 'class Pedido {}\n'))
    rc, out = correr('--archivo', d)
    caso('diff con una migracion que expande: sale 0 y la nombra', rc == 0 and out.startswith('CLASIFICAR MIGRACIONES -- OK') and 'EXPANDIR' in out
         and 'db/migration/V12__pedido.sql' in out, out[:300])
    caso('la salida termina diciendo lo que NO mira (volumen, bloqueos, duracion)',
         'Lo que este script NO mira:' in out.strip().splitlines()[-1] and 'volumen' in out and 'bloqueos' in out and 'tarda' in out, out[-300:])
    d = escribir(os.path.join(tmp, 'contrae.diff'), diff_nuevo('db/migration/V13__borra.sql', CONTRAE))
    rc, out = correr('--archivo', d)
    caso('diff con una migracion que solo contrae: sale 0 (contraer sola es el paso 3), la marca y avisa que no se deshace',
         rc == 0 and 'CONTRAER' in out and 'no se deshace' in out, out[:400])
    d = escribir(os.path.join(tmp, 'contrae-y-codigo.diff'), diff_nuevo('db/migration/V13__borra.sql', CONTRAE) + diff_modificado('src/Cliente.java', ['// sin telefono viejo']))
    rc, out = correr('--archivo', d)
    caso('contrae y ademas trae cambios de codigo: avisa que contraer va en su propio despliegue', rc == 0 and 'propio despliegue' in out, out[:500])
    d = escribir(os.path.join(tmp, 'mixta.diff'), diff_nuevo('db/migration/V14__mezcla.sql', MEZCLA))
    rc, out = correr('--archivo', d)
    caso('diff con una migracion MIXTA: sale 1 (HALLAZGO)', rc == 1 and 'MIXTA' in out and 'HALLAZGO' in out, out[:400])
    rc, out = correr('--archivo', d, '--json')
    try:
        j = json.loads(out)
    except ValueError:
        j = {}
    caso('--json: estado, resumen, migraciones con sus sentencias y lo que no mira',
         rc == 1 and j.get('estado') == 'HALLAZGO' and j.get('resumen', {}).get('MIXTA') == 1 and j['migraciones'][0]['clase'] == 'MIXTA'
         and j['migraciones'][0]['sentencias'] and j.get('no_mira'), out[:300])
    caso('--json: sale en ASCII puro', bool(j) and all(ord(ch) < 128 for ch in out))

    d = escribir(os.path.join(tmp, 'sql-suelto.diff'), diff_nuevo('scripts/reporte.sql', EXPANDE))
    rc, out = correr('--archivo', d)
    caso('hay .sql pero no en una carpeta de migraciones reconocible: SIN DATOS (2), y los nombra',
         rc == 2 and 'SIN DATOS' in out and 'donde viven las migraciones' in out and 'scripts/reporte.sql' in out, out[:400])
    rc, out = correr('--archivo', d, '--carpeta', 'scripts')
    caso('con --carpeta se le dice donde viven: clasifica', rc == 0 and 'EXPANDIR' in out, out[:300])
    d = escribir(os.path.join(tmp, 'solo-codigo.diff'), diff_nuevo('src/Pedido.java', 'class Pedido {}\n'))
    rc, out = correr('--archivo', d)
    caso('con --archivo, un diff que no toca ninguna migracion es SIN DATOS (sin el arbol, el cero no se puede comprobar)',
         rc == 2 and 'SIN DATOS' in out, out[:300])
    rc, out = correr('--archivo', d, '--carpeta', 'db/migration')
    caso('idem aunque se pase --carpeta: no se pudo comprobar que la carpeta exista', rc == 2 and 'SIN DATOS' in out, out[:300])
    d = escribir(os.path.join(tmp, 'no-sql.diff'), diff_nuevo('app/migrations/0002_auto.py', 'from django.db import migrations\n'))
    rc, out = correr('--archivo', d)
    caso('una migracion nueva que no es SQL: SIN CLASIFICAR y SIN DATOS (2)', rc == 2 and 'SIN CLASIFICAR' in out, out[:400])
    d = escribir(os.path.join(tmp, 'modificada.diff'), diff_modificado('db/migration/V01__inicial.sql', ['ALTER TABLE cliente DROP COLUMN fax;']))
    rc, out = correr('--archivo', d)
    caso('una migracion que ya existia y se modifico: se clasifican sus lineas nuevas y se avisa', rc == 0 and 'CONTRAER' in out and 'ya existia' in out, out[:500])
    d = escribir(os.path.join(tmp, 'basura.diff'), diff_nuevo('db/migration/V15__rara.sql', 'esto no es SQL\n'))
    rc, out = correr('--archivo', d)
    caso('una migracion .sql que no se reconoce: SIN DATOS (2), no OK', rc == 2 and 'SIN CLASIFICAR' in out, out[:300])

    rc, out = correr('--archivo', os.path.join(tmp, 'no-existe.diff'))
    caso('el diff no existe: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    d = escribir(os.path.join(tmp, 'vacio.diff'), '')
    rc, out = correr('--archivo', d)
    caso('el diff esta vacio: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--archivo', tmp)
    caso('el diff no se puede leer (es una carpeta): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr()
    caso('sin --repo ni --archivo: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])

    # ---- por linea de comandos, contra un repositorio git temporal
    if shutil.which('git') is None:
        print('  (sin git en el PATH: se saltean los casos de --repo)')
    else:
        repo = os.path.join(tmp, 'repo')
        os.makedirs(repo)
        sh(repo, 'git', 'init', '-q', '-b', 'develop')
        sh(repo, 'git', 'config', 'user.name', 'Prueba')
        sh(repo, 'git', 'config', 'user.email', 'prueba@example.com')
        escribir(os.path.join(repo, 'db', 'migration', 'V01__inicial.sql'), 'CREATE TABLE cliente (id INT, telefono_viejo TEXT);\n')
        escribir(os.path.join(repo, 'src', 'app.txt'), 'uno\n')
        commit(repo, 'inicial')
        sh(repo, 'git', 'tag', 'v1')
        escribir(os.path.join(repo, 'src', 'app.txt'), 'dos\n')
        commit(repo, 'solo codigo')
        sh(repo, 'git', 'tag', 'v2')
        escribir(os.path.join(repo, 'db', 'migration', 'V02__pedido.sql'), EXPANDE)
        commit(repo, 'expande')
        sh(repo, 'git', 'tag', 'v3')
        escribir(os.path.join(repo, 'db', 'migration', 'V03__borra.sql'), CONTRAE)
        commit(repo, 'contrae')
        sh(repo, 'git', 'tag', 'v4')

        rc, out = correr('--repo', repo, '--base', 'v2', '--hasta', 'v3')
        caso('repo: el rango trae una migracion que expande: sale 0', rc == 0 and 'EXPANDIR' in out and 'V02__pedido.sql' in out, out[:300])
        rc, out = correr('--repo', repo, '--base', 'v1', '--hasta', 'v2')
        caso('repo: el rango no trae migraciones y la carpeta existe en el arbol: cero de verdad, sale 0',
             rc == 0 and 'no trae migraciones nuevas' in out, out[:300])
        rc, out = correr('--repo', repo, '--base', 'v1')
        caso('repo: sin --hasta toma HEAD, y ve la que expande y la que contrae', rc == 0 and 'EXPANDIR' in out and 'CONTRAER' in out, out[:400])
        rc, out = correr('--repo', repo, '--base', 'v3', '--hasta', 'v4', '--json')
        try:
            j = json.loads(out)
        except ValueError:
            j = {}
        caso('repo: --json con el rango y la clase', rc == 0 and j.get('rango') == {'base': 'v3', 'hasta': 'v4'} and j.get('resumen', {}).get('CONTRAER') == 1, out[:300])
        rc, out = correr('--repo', repo, '--base', 'v1', '--hasta', 'v2', '--carpeta', 'db/migraciones')
        caso('repo: una --carpeta que no existe en el arbol: SIN DATOS (2), no cero', rc == 2 and 'SIN DATOS' in out and 'db/migraciones' in out, out[:300])
        rc, out = correr('--repo', repo, '--base', 'no-existe', '--hasta', 'v2')
        caso('repo: una referencia que git no conoce: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out and 'no-existe' in out, out[:300])
        rc, out = correr('--repo', repo, '--base', 'v2', '--hasta', 'v2')
        caso('repo: un rango sin ningun cambio: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out and 'ningun cambio' in out, out[:300])
        rc, out = correr('--repo', repo)
        caso('repo: sin --base: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out and '--base' in out, out[:300])

        otro = os.path.join(tmp, 'sin-migraciones')
        os.makedirs(otro)
        sh(otro, 'git', 'init', '-q', '-b', 'develop')
        sh(otro, 'git', 'config', 'user.name', 'Prueba')
        sh(otro, 'git', 'config', 'user.email', 'prueba@example.com')
        escribir(os.path.join(otro, 'src', 'a.txt'), 'uno\n')
        commit(otro, 'uno')
        escribir(os.path.join(otro, 'src', 'a.txt'), 'dos\n')
        commit(otro, 'dos')
        rc, out = correr('--repo', otro, '--base', 'HEAD~1')
        caso('repo sin carpeta de migraciones reconocible: SIN DATOS (2), no "cero migraciones"',
             rc == 2 and 'SIN DATOS' in out and 'donde viven las migraciones' in out, out[:300])
        rc, out = correr('--repo', os.path.join(tmp, 'no-es-repo'), '--base', 'v1')
        caso('la ruta no es un repositorio git: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])

    try:
        with open(SCRIPT, 'rb') as h:
            datos = h.read()
        caso('clasificar-migraciones.py es ASCII puro', bool(datos) and all(b < 128 for b in datos))
    except OSError as e:
        caso('clasificar-migraciones.py es ASCII puro', False, e)

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
