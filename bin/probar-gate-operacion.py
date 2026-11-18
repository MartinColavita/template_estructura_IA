#!/usr/bin/env python3
"""Prueba de bin/gate-operacion.py con planes de cambio e inventarios de mentira.
Se corre:  python -B bin/probar-gate-operacion.py   -> OK o FALLA, con el detalle de cada caso."""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SCRIPT = os.path.join(AQUI, 'gate-operacion.py')
MOLDE = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'operacion-de-servidores', 'references', 'mantenimiento.md')
ESPERADOS = []
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `web-prueba-1` | servidor | prueba | `web-prueba-1` | no | media | N1 | no | martes 22 a 24 | operaciones |\n'
         '| `db-prod-1` | servidor | Producci\u00f3n | `db-prod-1` | no | alta | N2 | no | jueves 23 a 24 | operaciones |\n'
         '| `web-n0` | servidor | prueba | `web-n0` | no | baja | N0 | no | | operaciones |\n'
         '| `sin-decidir` | servidor | prueba | `x` | no | baja | \u26a0 | no | | operaciones |\n')
CAMPOS = (('Qu\u00e9', 'Reiniciar el servicio de la cola, que quedo trabado'), ('Alias', '`web-prueba-1`'), ('Nivel', 'N1'),
          ('Ventana', 'martes 22 a 24'), ('Respaldo verificado', 'no toca datos ni configuracion'))
SECCIONES = (('Comando exacto', '```sh\nsudo systemctl restart cola.service\n```'),
             ('Salida esperada', 'No imprime nada y sale con 0. `systemctl is-active cola.service` dice `active`.'),
             ('C\u00f3mo se verifica', '`python -I bin/salud-host.py --ssh web-prueba-1`: servicios en OK.'),
             ('Vuelta atr\u00e1s', 'Si no levanta: `sudo systemctl restart cola.service` una vez mas y, si sigue caido, se avisa; '
                              'el servicio no cambio de version ni de configuracion. Tarda un minuto.'))


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:500]) if (detalle and not ok) else ''))


def escribir(ruta, texto, crudo=False):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto if crudo else texto.encode('utf-8'))
    return ruta


def plan(campos=None, secciones=None, **cambia):
    """Un plan completo. campo='valor' o seccion='texto' cambia uno (por su nombre sin acentos ni espacios); None lo saca."""
    def clave(n):
        return re.sub(r'[^a-z]', '', n.lower().replace(chr(0xe9), 'e').replace(chr(0xe1), 'a').replace(chr(0xf3), 'o'))
    filas = ''
    for nombre, valor in campos or CAMPOS:
        valor = cambia.get(clave(nombre), valor)
        if valor is not None:
            filas += '| %s | %s |\n' % (nombre, valor)
    cuerpo = ''
    for nombre, texto in secciones or SECCIONES:
        texto = cambia.get(clave(nombre), texto)
        if texto is not None:
            cuerpo += '\n## %s\n\n%s\n' % (nombre, texto)
    return '# Plan de cambio \u2014 reiniciar la cola\n\n| Campo | Valor |\n|---|---|\n' + filas + cuerpo


def main():
    print('== gate-operacion')
    tmp = tempfile.mkdtemp(prefix='probar-gate-op-')
    repo = os.path.join(tmp, 'repo')
    inv = escribir(os.path.join(repo, 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)

    def correr(*args, **kw):
        r = subprocess.run([sys.executable, '-I', SCRIPT, '--raiz', kw.get('raiz', repo)] + list(args), capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        return r.returncode, r.stdout + r.stderr

    def con_plan(nombre, texto, *args, **kw):
        return correr('--plan', escribir(os.path.join(tmp, nombre), texto), *args, **kw)

    # --- el camino feliz
    rc, out = con_plan('n1.md', plan())
    caso('plan completo, N1, en un alias autorizado hasta N1: OK (0), con la ventana de los dos lados y lo que falta',
         rc == 0 and out.startswith('GATE de SERVIDOR') and ' -- OK' in out.splitlines()[0] and 'martes 22 a 24' in out
         and 'un "si"' in out and 'NO mira' in out, out)
    caso('el OK muestra el respaldo que declara el plan, sin darlo por medido', 'no toca datos' in out and 'ningun script' in out, out)
    rc, out = con_plan('n2.md', plan(alias='`db-prod-1`', nivel='N2', ventana='jueves 23 a 24'))
    caso('plan N2 en produccion, autorizado hasta N2: OK (0) y avisa los dos "si" con ANTES y DESPUES',
         rc == 0 and 'dos "si"' in out and 'ANTES' in out and 'DESPUES' in out, out)
    rc, out = con_plan('n1-alias.md', plan(), '--alias', 'web-prueba-1')
    caso('--alias igual al del plan: OK', rc == 0, out)

    # --- lo que FRENA por el inventario
    rc, out = con_plan('n1-prod.md', plan(alias='`db-prod-1`'))
    caso('N1 en produccion: FRENA (1), en produccion un cambio es N2', rc == 1 and 'FRENA' in out and 'produccion' in out, out)
    rc, out = con_plan('n2-prueba.md', plan(nivel='N2'))
    caso('N2 en un alias autorizado hasta N1: FRENA (1) y dice hasta donde', rc == 1 and 'hasta N1' in out, out)
    rc, out = con_plan('n0-alias.md', plan(alias='`web-n0`'))
    caso('N1 en un alias que solo se puede leer: FRENA (1)', rc == 1 and 'hasta N0' in out, out)
    rc, out = con_plan('otro.md', plan(alias='`web-prueba-9`'))
    caso('un alias que no esta en el inventario: FRENA (1)', rc == 1 and 'no esta en el inventario' in out, out)
    rc, out = con_plan('sin-decidir.md', plan(alias='`sin-decidir`'))
    caso('un alias con el nivel sin decidir: FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = con_plan('n3.md', plan(nivel='N3'))
    caso('N3: FRENA siempre, aunque el plan este completo; lo hace una persona', rc == 1 and 'persona' in out, out)
    rc, out = con_plan('n0.md', plan(nivel='N0'))
    caso('N0 en un plan de cambio: FRENA (1), leer no necesita plan', rc == 1 and 'N0' in out, out)
    rc, out = con_plan('sin-nivel.md', plan(nivel='<N1 o N2>'))
    caso('nivel sin declarar (el marcador del molde): FRENA (1)', rc == 1 and 'nivel' in out, out)
    rc, out = con_plan('alias-distinto.md', plan(), '--alias', 'db-prod-1')
    caso('--alias distinto del alias del plan: FRENA (1), el plan es para otro servidor', rc == 1 and 'otro' in out, out)

    # --- lo que FRENA por el plan
    for nombre, cambio, que in (
            ('va-sin.md', {'vueltaatras': None}, 'sin la seccion Vuelta atras'),
            ('va-vacia.md', {'vueltaatras': ''}, 'con la Vuelta atras vacia'),
            ('va-no-hay.md', {'vueltaatras': 'No hay.'}, 'con "No hay." como vuelta atras'),
            ('va-molde.md', {'vueltaatras': '<los pasos exactos para dejarlo como estaba>'}, 'con la vuelta atras del molde sin llenar'),
            ('va-cerco.md', {'vueltaatras': '```\n```'}, 'con un bloque de codigo vacio como vuelta atras'),
            ('va-raya.md', {'vueltaatras': chr(0x2014)}, 'con una raya como vuelta atras')):
        rc, out = con_plan(nombre, plan(**cambio))
        caso('plan %s: FRENA (1), sin vuelta atras escrita el cambio es N3' % que, rc == 1 and 'vuelta atras' in out.lower() and 'N3' in out, out)
    rc, out = con_plan('va-larga.md', plan(vueltaatras='No se puede volver con el paquete: se restaura la imagen del disco de las 22, que tarda 15 minutos.'))
    caso('una vuelta atras que empieza con "No se puede..." pero trae un procedimiento: OK, no es falsa alarma', rc == 0, out)
    # --- F2 8a: un texto que EMPIEZA con un negativo, o que dice que no se deshace, no es vuelta atras ni respaldo
    for n, (texto, que) in enumerate((
            ('Ninguna, el cambio es definitivo.', 'empieza con "Ninguna"'),
            ('Sin vuelta atras: se aplica una sola vez.', 'empieza con "Sin"'),
            ('N/A - es una sola vez', 'empieza con "N/A"'),
            ('No aplica para este cambio, es menor.', 'empieza con "No aplica"'),
            ('No hay forma de volver una vez aplicado.', 'empieza con "No hay"'),
            ('El cambio es irreversible.', 'dice "irreversible"'),
            ('Una vez aplicado no se puede deshacer.', 'dice "no se puede deshacer"'),
            ('Una vez hecho, no hay vuelta.', 'dice "no hay vuelta"'))):
        rc, out = con_plan('va-neg-%d.md' % n, plan(vueltaatras=texto))
        caso('vuelta atras que %s: FRENA (1)' % que, rc == 1 and 'vuelta atras' in out.lower(), out)
    rc, out = con_plan('va-irrev-proc.md', plan(vueltaatras='Irreversible para el paquete, pero se restaura la imagen del disco de las 22; tarda 15 minutos.'))
    caso('una vuelta atras que dice "irreversible" pero sigue con un procedimiento: OK', rc == 0, out)
    for n, (texto, que) in enumerate((('Sin respaldo', 'empieza con "Sin"'), ('Ninguno.', 'es "Ninguno"'),
                                      ('No se hizo, no hubo tiempo', 'empieza con "No se hizo"'))):
        rc, out = con_plan('resp-neg-%d.md' % n, plan(respaldoverificado=texto))
        caso('respaldo que %s: FRENA (1)' % que, rc == 1 and 'respaldo' in out.lower(), out)

    # --- F2 8b: las secciones se reconocen por su titulo completo, no por un prefijo
    previos = [(('Comandos previos' if n == 'Comando exacto' else n), t) for n, t in SECCIONES]
    rc, out = con_plan('cmd-previos.md', plan(secciones=previos))
    caso('"Comandos previos" no es "Comando exacto": FRENA (1), falta la seccion', rc == 1 and 'comando' in out.lower(), out)
    otra = [(('Salida esperada del monitoreo' if n == 'Salida esperada' else n), t) for n, t in SECCIONES]
    rc, out = con_plan('salida-otra.md', plan(secciones=otra))
    caso('"Salida esperada del monitoreo" no es "Salida esperada": FRENA (1)', rc == 1 and 'salida esperada' in out.lower(), out)
    rollback = [(('Vuelta atrás (rollback)' if n.startswith('Vuelta') else n), t) for n, t in SECCIONES]
    rc, out = con_plan('va-rollback.md', plan(secciones=rollback))
    caso('"Vuelta atras (rollback)": el titulo completo con una aclaracion entre parentesis se reconoce', rc == 0, out)

    rc, out = con_plan('cmd-sin.md', plan(comandoexacto=None))
    caso('sin comando exacto: FRENA (1)', rc == 1 and 'comando' in out.lower(), out)
    rc, out = con_plan('cmd-marcador.md', plan(comandoexacto='```sh\nsudo systemctl restart <servicio>\n```'))
    caso('un comando con un marcador <...>: FRENA (1), no es el comando exacto', rc == 1 and 'marcador' in out, out)
    rc, out = con_plan('cmd-redir.md', plan(comandoexacto='```sh\nsudo logrotate -d /etc/logrotate.conf 2>&1 > /dev/null\n```'))
    caso('un comando con redirecciones de shell (2>&1, > archivo) no es un marcador: OK', rc == 0, out)
    rc, out = con_plan('cmd-comentario.md', plan(comandoexacto='```sh\n# un comentario de shell no es un titulo\nsudo systemctl restart cola.service\n```'))
    caso('un comentario de shell (# ...) dentro del bloque del comando no corta la seccion: OK', rc == 0, out)
    rc, out = con_plan('salida-vacia.md', plan(salidaesperada=''))
    caso('salida esperada vacia: FRENA (1)', rc == 1 and 'salida esperada' in out.lower(), out)
    rc, out = con_plan('verif-sin.md', plan(comoseverifica=None))
    caso('sin "como se verifica": FRENA (1)', rc == 1 and 'verifica' in out.lower(), out)
    rc, out = con_plan('resp-sin.md', plan(respaldoverificado=None))
    caso('sin el campo Respaldo verificado: FRENA (1)', rc == 1 and 'respaldo' in out.lower(), out)
    rc, out = con_plan('vent-sin.md', plan(ventana='<cuando>'))
    caso('ventana sin declarar en el plan: FRENA (1)', rc == 1 and 'ventana' in out.lower(), out)
    rc, out = con_plan('que-sin.md', plan(que=None))
    caso('sin el campo Que: FRENA (1)', rc == 1 and 'que' in out.lower(), out)
    rc, out = con_plan('varios.md', plan(vueltaatras=None, salidaesperada='', ventana=None))
    caso('varios faltantes: los dice todos juntos, no de a uno', rc == 1 and out.count('FRENA') >= 3, out)

    # --- la forma no importa: acentos, negritas, saltos de Windows, BOM
    sin_acentos = plan().replace('C\u00f3mo', 'Como').replace('Vuelta atr\u00e1s', 'Vuelta atras').replace('| Qu\u00e9 |', '| **Que** |')
    rc, out = con_plan('sin-acentos.md', sin_acentos)
    caso('encabezados sin acentos y campos en negrita: se reconocen igual', rc == 0, out)
    rc, out = correr('--plan', escribir(os.path.join(tmp, 'crlf.md'), (chr(0xfeff) + plan()).replace('\n', '\r\n').encode('utf-8'), crudo=True))
    caso('plan con BOM y saltos de Windows: se lee igual', rc == 0, out)

    # --- SIN DATOS
    rc, out = correr('--plan', os.path.join(tmp, 'no-existe.md'))
    caso('plan ausente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = con_plan('vacio.md', '')
    caso('plan vacio: SIN DATOS (2), nunca OK', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = con_plan('otra-cosa.md', '# Notas\n\nHay que reiniciar la cola algun dia.\n')
    caso('un archivo que no tiene el molde del plan: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--plan', escribir(os.path.join(tmp, 'binario.md'), bytes(bytearray(range(256))) * 3, crudo=True))
    caso('un archivo ilegible (binario): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = con_plan('sin-inv.md', plan(), raiz=os.path.join(tmp, 'sin-repo'))
    caso('plan completo sin inventario: SIN DATOS (2), no "sin restricciones"', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = con_plan('sin-inv-y-mal.md', plan(vueltaatras=None), raiz=os.path.join(tmp, 'sin-repo'))
    caso('sin inventario y con el plan incompleto: FRENA (1), lo que falta se dice igual', rc == 1 and 'vuelta atras' in out.lower(), out)
    doble = escribir(os.path.join(tmp, 'doble', 'cerebro-digital', 'm', 'operacion', 'inventario.md'),
                     CABECERA + FILAS + '| `web-prueba-1` | servidor | prueba | `otro` | no | media | N2 | no | | ops |\n')
    rc, out = con_plan('doble.md', plan(), '--inventario', doble)
    caso('el alias figura dos veces en el inventario: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr()
    caso('sin --plan: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)

    # --- --json
    rc, out = con_plan('json.md', plan(vueltaatras=None), '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    chequeos = dict((c.get('chequeo'), c.get('estado')) for c in d.get('chequeos', []))
    caso('--json: estado, alias, nivel, un estado por chequeo, la ventana y lo que no mira',
         rc == 1 and d.get('estado') == 'FRENA' and d.get('alias') == 'web-prueba-1' and d.get('nivel') == 'N1'
         and chequeos.get('vuelta atras') == 'FRENA' and chequeos.get('inventario') == 'OK'
         and d.get('ventana', {}).get('inventario') == 'martes 22 a 24' and d.get('no_mira') and all(ord(c) < 128 for c in out), out[:600])

    # --- el molde de mantenimiento.md: sin llenar FRENA, y es el mismo formato que lee este script
    if os.path.isfile(MOLDE):
        with open(MOLDE, encoding='utf-8') as h:
            texto = h.read()
        m = re.search(r'````markdown\n(.*?)\n````', texto, re.S)
        caso('mantenimiento.md trae el molde del plan en un bloque ````markdown', m is not None)
        if m:
            rc, out = con_plan('molde.md', m.group(1))
            caso('el molde sin llenar: FRENA (1), nunca OK', rc == 1 and 'FRENA' in out, out)
            lleno = m.group(1)
            for a, b in (('<qu\u00e9 se cambia y por qu\u00e9, en criollo>', 'Reiniciar la cola'), ('<alias del inventario>', 'web-prueba-1'),
                         ('<N1 o N2>', 'N1'), ('<cu\u00e1ndo; la del inventario>', 'martes 22 a 24'),
                         ('<cu\u00e1l, de cu\u00e1ndo y c\u00f3mo se verific\u00f3; o \u00abno toca datos ni configuraci\u00f3n\u00bb>', 'no toca datos'),
                         ('<el comando, tal cual se va a correr>', 'sudo systemctl restart cola.service'),
                         ('<lo que tiene que imprimir y con qu\u00e9 c\u00f3digo sale>', 'Nada; sale con 0.'),
                         ('<el script o la medici\u00f3n que dice que qued\u00f3 bien>', '`python -I bin/salud-host.py --ssh web-prueba-1`'),
                         ('<los pasos exactos para dejarlo como estaba, y cu\u00e1nto tardan>', 'Volver a reiniciarlo; un minuto.')):
                lleno = lleno.replace(a, b)
            rc, out = con_plan('molde-lleno.md', lleno)
            caso('el molde con cada marcador reemplazado: OK (0)', rc == 0, out)
    else:
        caso('existe references/mantenimiento.md con el molde del plan', False, MOLDE)

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('gate-operacion.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
