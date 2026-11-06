#!/usr/bin/env python3
"""Prueba de bin/esquema-base.py sobre un SQLite de mentira y un DDL en .sql.
Se corre:  python -B bin/probar-esquema-base.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'esquema-base.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== esquema-base')
    tmp = tempfile.mkdtemp(prefix='probar-esquema-')
    db = os.path.join(tmp, 'app.sqlite')
    con = sqlite3.connect(db)
    con.executescript('''
        CREATE TABLE sala (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, capacidad INTEGER);
        CREATE TABLE reserva (id INTEGER PRIMARY KEY, sala_id INTEGER NOT NULL REFERENCES sala(id), estado TEXT NOT NULL, persona TEXT);
        CREATE INDEX ix_reserva_estado ON reserva(estado);
        INSERT INTO sala VALUES (1, 'A', 10);
        INSERT INTO reserva VALUES (1, 1, 'activa', 'dato@persona.com');
        INSERT INTO reserva VALUES (2, 1, 'cerrada', 'otro@persona.com');
    ''')
    con.commit(); con.close()
    rc, out = correr(db)
    caso('sqlite: OK (0) y escribe markdown con las dos tablas', rc == 0 and '## sala' in out and '## reserva' in out, out[:300])
    caso('columnas con tipo, nulidad y clave; la foranea se ve', '| sala_id | INTEGER | no | FK -> sala.id |' in out, out[:600])
    caso('el indice aparece', 'ix_reserva_estado' in out)
    caso('el mermaid erDiagram trae la relacion', 'erDiagram' in out and 'reserva }o--|| sala' in out)
    caso('NUNCA salen filas de datos', 'persona.com' not in out and 'activa' not in out)
    rc, out = correr(db, '--conteos')
    caso('--conteos agrega solo la cantidad de filas', '2 filas' in out and 'persona.com' not in out)
    rc, out = correr(db, '--json')
    d = json.loads(out)
    caso('--json: motor sqlite y 2 tablas', d['motor'] == 'sqlite' and len(d['tablas']) == 2)
    ddl = os.path.join(tmp, 'ddl')
    os.makedirs(ddl)
    with open(os.path.join(ddl, 'V1__inicial.sql'), 'w', encoding='utf-8') as h:
        h.write('''CREATE TABLE cliente (
  id BIGSERIAL PRIMARY KEY,
  documento VARCHAR(20) NOT NULL,
  plan_id INT REFERENCES plan(id)
);
CREATE TABLE plan (id INT NOT NULL, nombre VARCHAR(50), PRIMARY KEY (id));
CREATE TABLE pedido (
  id INT NOT NULL,
  cliente_id INT NOT NULL,
  estado VARCHAR(10),
  CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES cliente(id)
);
CREATE TABLE "ventas"."item" (id INT PRIMARY KEY, pedido_id INT REFERENCES [dbo].[pedido](id));
''')
    salida = os.path.join(tmp, 'esquema.md')
    rc, out = correr(ddl, '--salida', salida)
    caso('ddl en carpeta: OK (0) y escribe el archivo', rc == 0 and os.path.isfile(salida), out[:300])
    t = open(salida, encoding='utf-8').read()
    caso('ddl: 4 tablas (una con esquema entre comillas), la PK por linea y la PK por constraint', '4 tabla(s)' in t and '## ventas.item' in t and '| id | BIGSERIAL | no | PK |' in t and '| id | INT | no | PK |' in t, t[:800])
    caso('ddl: foranea inline, por CONSTRAINT y con esquema entre corchetes', 'FK -> plan.id' in t and 'FK -> cliente.id' in t and 'FK -> dbo.pedido.id' in t, t[:1500])
    rc, out = correr(ddl, '--conteos')
    caso('--conteos con DDL avisa que solo aplica a SQLite', 'solo aplica a SQLite' in out)
    mig = os.path.join(tmp, 'migraciones'); os.makedirs(mig)
    with open(os.path.join(mig, 'V1__inicial.sql'), 'w', encoding='utf-8') as h:
        h.write('CREATE TABLE reserva (id INTEGER PRIMARY KEY, sala_id INTEGER NOT NULL);\n')
    with open(os.path.join(mig, 'V2__estado.sql'), 'w', encoding='utf-8') as h:
        h.write("ALTER TABLE reserva ADD COLUMN estado TEXT NULL DEFAULT 'activa';\n")
    rc, out = correr(mig)
    caso('carpeta de migraciones sin --aplicar: avisa que hay ALTER TABLE sin reflejar', rc == 0 and 'estado' not in out.split('erDiagram')[0] and 'ALTER TABLE que NO se reflejan' in out, out[:400])
    rc, out = correr(mig, '--aplicar')
    caso('--aplicar: el esquema resultante tiene la columna estado y dice que aplico V1 y V2', rc == 0 and '| estado | TEXT | si |' in out and 'V1__inicial.sql, V2__estado.sql' in out, out[:500])
    rc, out = correr(os.path.join(tmp, 'vacia'))
    caso('ruta inexistente: SIN DATOS (2)', rc == 2)
    vacio = os.path.join(tmp, 'sin-sql'); os.makedirs(vacio)
    rc, out = correr(vacio)
    caso('carpeta sin .sql: SIN DATOS (2) y sugiere exportar el DDL', rc == 2 and 'DDL' in out)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
