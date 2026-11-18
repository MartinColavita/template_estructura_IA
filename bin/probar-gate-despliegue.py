#!/usr/bin/env python3
"""Prueba de bin/gate-despliegue.py sobre fichas de ambientes plantadas y un repositorio git TEMPORAL.
Se corre:  python -B bin/probar-gate-despliegue.py   -> OK o FALLA, con el detalle de cada caso.
Necesita git en el PATH para los casos de migraciones (si no esta, esos casos se saltean y se dice)."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'gate-despliegue.py')
ESPERADOS = []
CAB = ('| Ambiente | Para qué es | Protegido | Quién aprueba (rol) | Dónde se aprueba | Qué entra (rama o tag) | '
       'Ventana de observación | Cómo se vuelve atrás | Cuánto tarda en volver |\n|---|---|---|---|---|---|---|---|---|\n')
MOLDE = ('| `<nombre-exacto-en-la-plataforma>` | `<para qué se usa>` | sí | `<rol>` | `<plataforma y pantalla>` | '
         '`<rama o tag>` | `<minutos>` | `<procedimiento>` | `<minutos>` |\n')
DES = '| `Desarrollo` | el equipo | no | | | rama develop | 10 minutos | volver a desplegar la anterior | 5 minutos |\n'
PRU = ('| `Prueba` | aceptacion | sí | lider tecnico | Azure DevOps, ambiente Prueba | tags v* | 30 minutos | '
       'volver a desplegar la anterior desde el pipeline | 5 minutos |\n')
PRO = ('| `Produccion` | usuarios | **sí** | responsable de producto | Azure DevOps, ambiente Produccion | tags v* | '
       '30 minutos | volver a desplegar la anterior | 10 minutos |\n')
D1, D2 = 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64
RAIZ_PRUEBA = []   # la raiz temporal: la ficha vale solo adentro de <raiz>/cerebro-digital/
AYUDA = ('\n## Cómo se llena cada columna\n\n| Columna | Qué va |\n|---|---|\n| **Ambiente** | `Fantasma` |\n'
         '| `Fantasma-2` | sí |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)) if (detalle and not ok) else ''))


def correr(*args, env=None):
    args = list(args) + (['--raiz', RAIZ_PRUEBA[0]] if RAIZ_PRUEBA and '--raiz' not in args else [])
    r = subprocess.run([sys.executable, '-I', SCRIPT] + args, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=env)
    return r.returncode, r.stdout + r.stderr


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def ficha(tmp, nombre, filas, afuera=False):
    """La ficha, adentro de <tmp>/cerebro-digital/fichas/ (o directo en tmp con afuera=True)."""
    carpeta = tmp if afuera or 'cerebro-digital' in tmp else os.path.join(tmp, 'cerebro-digital', 'fichas')
    return escribir(os.path.join(carpeta, nombre), '---\nid: ambientes\n---\n\n# Ambientes\n\n' + CAB + filas + AYUDA)


def sh(cwd, *cmd):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def commit(repo, msg, tag):
    sh(repo, 'git', 'add', '-A')
    rc, out = sh(repo, 'git', 'commit', '-q', '-m', msg)
    assert rc == 0, out
    sh(repo, 'git', 'tag', tag)


def linea(out, chequeo):
    """La linea del reporte de texto de un chequeo, o ''."""
    for l in out.splitlines():
        if l.strip().startswith(chequeo):
            return l
    return ''


def main():
    print('== gate-despliegue')
    tmp = tempfile.mkdtemp(prefix='probar-gate-desp-')
    RAIZ_PRUEBA.append(tmp)
    amb = ficha(tmp, 'ambientes.md', MOLDE + DES + PRU + PRO)
    base = ['--ambientes', amb]

    try:
        spec = importlib.util.spec_from_file_location('gate_despliegue_prueba', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ambientes, problemas = mod.leer_ambientes(amb)
    except Exception as e:  # noqa: BLE001 -- sin el script, los casos fallan y no explotan
        mod, ambientes, problemas = None, [], ['no carga: %s' % e]
    caso('lee las filas reales en orden, saltea el molde y la tabla de ayuda',
         [x['nombre'] for x in ambientes] == ['Desarrollo', 'Prueba', 'Produccion'], [x.get('nombre') for x in ambientes] or problemas)
    caso('protegido "sí" (con acento o en negrita) es True; "no" es False',
         [x.get('protegido') for x in ambientes] == [False, True, True], [x.get('protegido') for x in ambientes])

    # ---- lo que falta para empezar
    rc, out = correr('--version', 'v2', *base)
    caso('sin --ambiente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--ambiente', 'Prueba', *base)
    caso('sin --version: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', os.path.join(tmp, 'no-existe.md'))
    caso('sin ficha de ambientes: SIN DATOS (2), no "sin restricciones"', rc == 2 and 'SIN DATOS' in out, out[:300])
    solo_molde = ficha(tmp, 'molde.md', MOLDE)
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', solo_molde, '--pipeline', 'verde')
    caso('ficha con solo la fila de molde: SIN DATOS (2), Regla del cero', rc == 2 and 'SIN DATOS' in out and 'molde' in out, out[:300])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', os.path.dirname(amb))
    caso('la ficha no se puede leer (es una carpeta): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
    afuera = ficha(tmp, 'afuera.md', DES + PRU, afuera=True)
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', afuera, '--pipeline', 'verde',
                     '--artefacto', D1, '--en-el-anterior', D1)
    caso('una ficha fuera de <raiz>/cerebro-digital/ no autoriza nada: SIN DATOS (2) y lo dice',
         rc == 2 and 'SIN DATOS' in linea(out, 'Ambiente') and 'cerebro-digital' in linea(out, 'Ambiente'), out[:400])
    caso('la columna "Que entra" conserva el asterisco suelto ("tags v*")', 'tags v*' in linea(correr(
        '--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', *base)[1], 'Ambiente'))

    # ---- el ambiente
    rc, out = correr('--ambiente', 'Staging', '--version', 'v2', '--pipeline', 'verde', *base)
    caso('un ambiente que no figura: FRENA (1)', rc == 1 and 'FRENA' in out and 'no figura' in out, out[:300])
    rc, out = correr('--ambiente', 'prueba', '--version', 'v2', '--pipeline', 'verde', *base)
    caso('el nombre se compara exacto: con otra mayuscula FRENA y dice como figura', rc == 1 and '"Prueba"' in out, out[:300])
    rc, out = correr('--ambiente', 'Fantasma', '--version', 'v2', '--pipeline', 'verde', *base)
    caso('FP: un nombre que solo esta en la tabla de ayuda no es un ambiente', rc == 1 and 'no figura' in out, out[:300])
    doble = ficha(tmp, 'doble.md', DES + PRU + PRU)
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', doble, '--pipeline', 'verde')
    caso('un ambiente que figura dos veces: SIN DATOS (2), no gana ninguna fila', rc == 2 and '2 veces' in out, out[:300])

    # ---- la proteccion
    sin_quien = ficha(tmp, 'sin-quien.md', DES + PRU.replace('lider tecnico', '').replace('Azure DevOps, ambiente Prueba', ''))
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', sin_quien, '--pipeline', 'verde',
                     '--artefacto', D1, '--en-el-anterior', D1)
    caso('protegido sin quien aprueba ni donde: FRENA (1)', rc == 1 and 'quien aprueba' in linea(out, 'Proteccion'), out[:500])
    sin_decidir = ficha(tmp, 'sin-decidir.md', DES + PRU.replace('| sí |', '| ⚠ |'))
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', sin_decidir, '--pipeline', 'verde',
                     '--artefacto', D1, '--en-el-anterior', D1)
    caso('protegido sin decidir: vale como protegido y es SIN DATOS (2)', rc == 2 and 'SIN DATOS' in linea(out, 'Proteccion'), out[:500])

    # ---- lo que viene de la plataforma, por argumentos
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'rojo', '--artefacto', D1,
                     '--en-el-anterior', D1, *base)
    caso('pipeline en rojo: FRENA (1)', rc == 1 and 'FRENA' in linea(out, 'Pipeline'), out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--artefacto', D1, '--en-el-anterior', D1, *base)
    caso('sin --pipeline: SIN DATOS, no OK (el script no llama a ninguna API)', 'SIN DATOS' in linea(out, 'Pipeline') and rc == 2, out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', '--artefacto', D2,
                     '--en-el-anterior', D1, *base)
    caso('el artefacto no es el que esta en el ambiente anterior: FRENA (1)', rc == 1 and 'FRENA' in linea(out, 'Mismo artefacto')
         and 'Desarrollo' in linea(out, 'Mismo artefacto'), out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', *base)
    caso('sin --artefacto ni --en-el-anterior: SIN DATOS', 'SIN DATOS' in linea(out, 'Mismo artefacto'), out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', '--artefacto', 'registro/app:latest',
                     '--en-el-anterior', 'registro/app:latest', *base)
    caso('dos etiquetas iguales (:latest) no prueban que sea lo mismo: SIN DATOS, no OK',
         'SIN DATOS' in linea(out, 'Mismo artefacto') and rc == 2, out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', '--artefacto', 'sha256:aa',
                     '--en-el-anterior', 'sha256:aa', *base)
    caso('un digest que no tiene 64 hexadecimales: SIN DATOS', 'SIN DATOS' in linea(out, 'Mismo artefacto'), out[:500])
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', '--artefacto', 'registro/app@' + D1,
                     '--en-el-anterior', D1.upper().replace('SHA256', 'sha256'), *base)
    caso('imagen@sha256:<64 hex> contra el mismo digest (sin importar mayusculas): OK',
         'OK' in linea(out, 'Mismo artefacto'), out[:500])
    rc, out = correr('--ambiente', 'Desarrollo', '--version', 'v2', '--pipeline', 'verde', *base)
    caso('el primer ambiente no tiene anterior: el mismo artefacto NO APLICA', 'NO APLICA' in linea(out, 'Mismo artefacto'), out[:500])

    # ---- vuelta atras y ventana
    sin_vuelta = ficha(tmp, 'sin-vuelta.md', DES + PRU.replace('volver a desplegar la anterior desde el pipeline', '').replace('| 5 minutos |', '| |'))
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', sin_vuelta, '--pipeline', 'verde',
                     '--artefacto', D1, '--en-el-anterior', D1)
    caso('sin vuelta atras declarada: FRENA (1)', rc == 1 and 'FRENA' in linea(out, 'Vuelta atras'), out[:600])
    sin_ventana = ficha(tmp, 'sin-ventana.md', DES + PRU.replace('| 30 minutos |', '| |'))
    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--ambientes', sin_ventana, '--pipeline', 'verde',
                     '--artefacto', D1, '--en-el-anterior', D1)
    caso('sin ventana de observacion: AVISO, no frena', 'AVISO' in linea(out, 'Que mirar despues') and rc != 1, out[:600])

    # ---- migraciones, contra un repositorio git temporal
    if shutil.which('git') is None:
        print('  (sin git en el PATH: se saltean los casos de migraciones)')
    else:
        repo = os.path.join(tmp, 'app')
        os.makedirs(repo)
        sh(repo, 'git', 'init', '-q', '-b', 'develop')
        sh(repo, 'git', 'config', 'user.name', 'Prueba')
        sh(repo, 'git', 'config', 'user.email', 'prueba@example.com')
        escribir(os.path.join(repo, 'db', 'migration', 'V01__inicial.sql'), 'CREATE TABLE cliente (id INT, telefono_viejo TEXT);\n')
        escribir(os.path.join(repo, 'src', 'Cliente.java'), 'class Cliente { String telefonoViejo; }\n')
        commit(repo, 'inicial', 'v1')
        escribir(os.path.join(repo, 'db', 'migration', 'V02__telefono.sql'), 'ALTER TABLE cliente ADD COLUMN telefono VARCHAR(30) NULL;\n')
        escribir(os.path.join(repo, 'src', 'Cliente.java'), 'class Cliente { String telefonoViejo; String telefono; }\n')
        commit(repo, 'expande', 'v2')
        escribir(os.path.join(repo, 'src', 'Cliente.java'), 'class Cliente { String telefono; }\n')
        commit(repo, 'deja de usar telefono_viejo', 'v3')
        escribir(os.path.join(repo, 'db', 'migration', 'V03__borra.sql'), 'ALTER TABLE cliente DROP COLUMN telefono_viejo;\n')
        commit(repo, 'contrae', 'v4')
        escribir(os.path.join(repo, 'db', 'migration', 'V04__mezcla.sql'),
                 'ALTER TABLE cliente ADD COLUMN email VARCHAR(80) NULL;\nALTER TABLE cliente DROP COLUMN fax;\n')
        commit(repo, 'mixta', 'v5')
        plataforma = ['--pipeline', 'verde', '--artefacto', D1, '--en-el-anterior', D1]

        rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--repo', repo, '--desde', 'v1', *(plataforma + base))
        caso('camino feliz: todo en orden sale 0 (OK) y muestra quien aprueba y donde',
             rc == 0 and out.startswith('GATE de DESPLIEGUE -- OK') and 'lider tecnico' in out and 'Azure DevOps, ambiente Prueba' in out
             and 'EXPANDIR' in linea(out, 'Migraciones'), out[:900])
        caso('el reporte dice que despliega una persona y termina con lo que no mira',
             'una persona' in out and 'Lo que este script NO mira:' in out.strip().splitlines()[-1], out[-400:])
        caso('la vuelta atras nombra la version a la que se vuelve (la que esta en el ambiente)', 'v1' in linea(out, 'Vuelta atras'), out[:900])
        rc, out = correr('--ambiente', 'Desarrollo', '--version', 'v2', '--repo', repo, '--desde', 'v1', '--pipeline', 'verde', *base)
        caso('un ambiente no protegido, primero de la cadena: sale 0 y dice que no pide aprobacion',
             rc == 0 and 'no protegido' in linea(out, 'Proteccion'), out[:700])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v4', '--repo', repo, '--desde', 'v3', *(plataforma + base))
        caso('trae una migracion que CONTRAE y nadie declaro la version que dejo de usarlo: FRENA (1)',
             rc == 1 and 'CONTRAER' in linea(out, 'Migraciones') and 'FRENA' in linea(out, 'Migraciones'), out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v4', '--repo', repo, '--desde', 'v3', '--sin-uso-desplegado', 'v3',
                         *(plataforma + base))
        caso('CONTRAE, y la version que dejo de usarlo ya esta en el ambiente: sale 0 y recuerda los dos "si"',
             rc == 0 and 'dos "si"' in out, out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v4', '--repo', repo, '--desde', 'v2', '--sin-uso-desplegado', 'v3',
                         *(plataforma + base))
        caso('CONTRAE, y la version que dejo de usarlo NO esta en el ambiente (no es ancestro de --desde): FRENA (1)',
             rc == 1 and 'FRENA' in linea(out, 'Migraciones'), out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v5', '--repo', repo, '--desde', 'v4', *(plataforma + base))
        caso('trae una migracion MIXTA: FRENA (1)', rc == 1 and 'MIXTA' in linea(out, 'Migraciones'), out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v3', '--repo', repo, '--desde', 'v2', *(plataforma + base))
        caso('un rango sin migraciones nuevas: OK', rc == 0 and 'OK' in linea(out, 'Migraciones'), out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v9', '--repo', repo, '--desde', 'v1', *(plataforma + base))
        caso('una version que git no conoce: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in linea(out, 'Migraciones'), out[:900])
        rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--repo', repo, '--desde', 'v1', '--json', *(plataforma + base))
        try:
            j = json.loads(out)
        except ValueError:
            j = {}
        caso('--json: estado, ambiente con su fila, un chequeo por linea y lo que no mira',
             rc == 0 and j.get('estado') == 'OK' and j.get('ambiente', {}).get('nombre') == 'Prueba'
             and {c['chequeo'] for c in j.get('chequeos', [])} >= {'Ambiente', 'Proteccion', 'Pipeline en verde', 'Mismo artefacto',
                                                                 'Migraciones', 'Vuelta atras', 'Que mirar despues'}
             and j.get('no_mira'), out[:400])
        caso('--json: sale en ASCII puro', bool(j) and all(ord(ch) < 128 for ch in out))

    rc, out = correr('--ambiente', 'Prueba', '--version', 'v2', '--pipeline', 'verde', '--artefacto', D1,
                     '--en-el-anterior', D1, *base)
    caso('sin --repo: las migraciones son SIN DATOS y el gate sale 2, nunca 0', rc == 2 and 'SIN DATOS' in linea(out, 'Migraciones'), out[:700])

    # ---- donde se busca la ficha
    raiz = os.path.join(tmp, 'raiz')
    ficha(os.path.join(raiz, 'cerebro-digital', 'modulo-a', 'arquitectura'), 'ambientes.md', DES + PRU)
    rc, out = correr('--ambiente', 'Desarrollo', '--version', 'v2', '--raiz', raiz, '--pipeline', 'verde')
    caso('busca la ficha del unico modulo desde --raiz', 'figura' in linea(out, 'Ambiente') and 'OK' in linea(out, 'Ambiente'), out[:500])
    ficha(os.path.join(raiz, 'cerebro-digital', 'modulo-b', 'arquitectura'), 'ambientes.md', DES)
    rc, out = correr('--ambiente', 'Desarrollo', '--version', 'v2', '--raiz', raiz, '--pipeline', 'verde')
    caso('con dos modulos y sin --modulo: SIN DATOS (2), no elige', rc == 2 and 'modulo' in out, out[:300])
    rc, out = correr('--ambiente', 'Desarrollo', '--version', 'v2', '--raiz', raiz, '--modulo', 'modulo-b', '--pipeline', 'verde')
    caso('con --modulo va a ese', 'OK' in linea(out, 'Ambiente'), out[:300])

    plantilla = os.path.join(os.path.dirname(AQUI), 'cerebro-digital', 'modulo-ejemplo', 'arquitectura', 'ambientes.md')
    if os.path.isfile(plantilla):
        rc, out = correr('--ambiente', 'Produccion', '--version', 'v1', '--ambientes', plantilla, '--pipeline', 'verde',
                         '--raiz', os.path.dirname(AQUI))
        caso('la ficha del template nace con el molde: SIN DATOS (2), nada se promueve',
             rc == 2 and 'SIN DATOS' in out and 'molde' in out, out[:300])
    else:
        caso('la ficha del template existe', False, plantilla)

    try:
        with open(SCRIPT, 'rb') as h:
            datos = h.read()
        caso('gate-despliegue.py es ASCII puro', bool(datos) and all(b < 128 for b in datos))
    except OSError as e:
        caso('gate-despliegue.py es ASCII puro', False, e)

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
