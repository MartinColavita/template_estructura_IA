#!/usr/bin/env python3
"""Prueba de bin/lote.py SIN RED y sin tocar borrador/: todo pasa en una carpeta temporal.

    python -B bin/probar-lote.py

Sale 0 si todos los casos dan lo esperado, 1 si alguno no.

Corre lote.py como lo corre una sesion (un proceso aparte, por la linea de comandos), con una
ficha y borradores HTML armados a mano. Los scripts de auditoria se reemplazan por dobles
(--bin) para que el resultado no dependa de ellos; si los de verdad ya estan en bin/, tambien
se prueba la llamada real. Lo que mas importa: que el mismo pedido de lo mismo, byte por byte
(mision y cierre); que un script que falta sea SIN DATOS y nunca OK; y que lo que se escribe
sea exactamente lo que se audito (la huella).
"""

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
LOTE_PY = os.path.join(AQUI, 'lote.py')
MISIONES = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'planificar-lote',
                        'misiones')

AVISO = chr(0x26a0)
MEDIO = chr(0xb7)
I_ = chr(0xed)
O_ = chr(0xf3)
NL = chr(10)
NO_SELLA = 'NO SE SELLA: '
OTRA_VERSION = NO_SELLA + 'el informe del auditor es de otra versi' + O_ + 'n (re-auditar)'
FASES = 'preparar, arranque, redactar, auditar, cierre, escribir'

resultados = []


def chequeo(nombre, obtenido, esperado):
    bien = obtenido == esperado
    resultados.append(bien)
    print(('ok    ' if bien else 'FALLA ') + nombre +
          ('' if bien else '  (obtuve ' + repr(obtenido)[:400] + ', esperaba ' +
           repr(esperado)[:400] + ')'))


def correr(*args):
    """(codigo, stdout+stderr como texto, stdout en bytes) de una corrida de lote.py."""
    entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
    p = subprocess.run([sys.executable, '-B', LOTE_PY] + [str(a) for a in args],
                       capture_output=True, env=entorno, cwd=RAIZ, timeout=300)
    return p.returncode, (p.stdout + p.stderr).decode('utf-8', 'replace'), p.stdout


def escribir(ruta, contenido):
    d = os.path.dirname(ruta)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(ruta, 'w', encoding='utf-8', newline='') as f:
        f.write(contenido)


def leer(ruta):
    with io.open(ruta, encoding='utf-8') as f:
        return f.read()


def leer_bytes(ruta):
    with open(ruta, 'rb') as f:
        return f.read()


def leer_json(ruta):
    with io.open(ruta, encoding='utf-8') as f:
        return json.load(f)


def item_de(L, clave):
    return [i for i in leer_json(os.path.join(L, 'items.json'))['items'] if i['clave'] == clave][0]


def fila(cierre, clave):
    """Las celdas de la fila de la tabla del cierre que corresponde a esa clave."""
    for linea in cierre.split(NL):
        if linea.startswith('| ') and not linea.startswith('| #'):
            celdas = [c.strip() for c in linea.strip().strip('|').split(' | ')]
            if len(celdas) == 10 and celdas[2].startswith(clave):
                return celdas
    return None


def celda(cierre, clave, n):
    f = fila(cierre, clave)
    return f[n] if f else None


def huella_de(mision):
    m = re.search(r'\*\*Huella:\*\* ([0-9a-f]+)', mision)
    return m.group(1) if m else None


FICHA = (
    '---' + NL + 'id: ficha-prueba' + NL + 'fuente_maqueta: entregables/disenos/maqueta-prueba.html' +
    NL + '---' + NL + NL + '# Ficha de prueba' + NL + NL + '## Derivaci' + O_ + 'n a backlog' +
    NL + NL + '- [S-01] Slice de prueba' + NL + '- [C-01] Capacidad ' + MEDIO + ' slice: S-01' + NL +
    '- [F-01] Buscar a la persona ' + MEDIO + ' capacidad: C-01 ' + MEDIO + ' reglas: RN-MOD-001' + NL)
FICHA_SIN_MAQUETA = '---' + NL + 'id: otra' + NL + '---' + NL + NL + '# Sin maqueta' + NL

CRITERIOS = ('<p><b>Escenario:</b> Persona encontrada <i>[RN-MOD-001]</i><br><b>Dado</b> una persona'
             '<br><b>Cuando</b> busco<br><b>Entonces</b> lo veo</p>')
H01 = '<h3>Objetivo</h3><p>Lo cubren [T-01] y [T-02].</p>'
T01 = ('<h3>Objetivo</h3><p>Usa [T-02] y cuelga de [H-01].</p>' + NL + '<h3>' + AVISO +
       ' Datos a confirmar</h3><ul><li>P-001 el codigo</li><li>P-004 otra</li></ul>')
T02 = ('<h3>Objetivo</h3><p>MALO: cuelga de [H-01].</p><h3>' + AVISO +
       ' Datos a confirmar</h3><p>Ninguno.</p>')
T03 = ('<h3>Objetivo</h3><p>Cuelga de [H-01].</p><h3>' + AVISO +
       ' Datos a confirmar</h3><ul><li>la paginacion</li></ul>')
T04 = '<h3>Objetivo</h3><p>Se pisa.</p>'
E01 = '<h3>Objetivo</h3><p>Ya cargada en el tablero.</p>'

# Doble de los scripts de auditoria: anota con que argumentos lo llamaron y devuelve un json
# con la forma de bin/auditoria/reporte.py. CON HALLAZGOS si el insumo dice MALO; el doble de
# analizar-tareas, si existe el archivo bandera.
DOBLE = (
    'import io, json, os, sys' + NL +
    'args = sys.argv[1:]' + NL +
    'herr = %r' + NL +
    "with io.open(%r, 'a', encoding='utf-8') as f:" + NL +
    "    f.write(herr + ' ' + json.dumps(args) + chr(10))" + NL +
    'bandera = %r' + NL +
    "salida = args[args.index('--salida') + 1]" + NL +
    "if herr == 'auditar-historia':" + NL +
    "    principal = args[args.index('--criterios') + 1]" + NL +
    "elif herr == 'auditar-tarea':" + NL +
    '    principal = args[0]' + NL +
    'else:' + NL +
    "    principal = args[args.index('--historia') + 1]" + NL +
    "if herr == 'analizar-tareas':" + NL +
    '    malo = os.path.exists(bandera)' + NL +
    'else:' + NL +
    "    malo = 'MALO' in io.open(principal, encoding='utf-8').read()" + NL +
    "d = {'herramienta': herr, 'insumo': principal, 'codigo': 1 if malo else 0," + NL +
    "     'veredicto': 'CON HALLAZGOS' if malo else 'SIN HALLAZGOS', 'sin_datos': None," + NL +
    "     'datos': {'tests': 1}, 'para_el_auditor': ['lo de criterio']," + NL +
    "     'renglones': [{'nivel': 'HALLAZGO' if malo else 'OK', 'chequeo': '1'," + NL +
    "                    'detalle': 'doble', 'evidencia': ''}]}" + NL +
    "io.open(salida, 'w', encoding='utf-8').write(json.dumps(d))" + NL +
    'print(json.dumps(d))' + NL +
    "sys.exit(d['codigo'])" + NL)


def informe_auditor(veredicto, huella=None, p=None, f=None):
    o = ['# Auditor' + I_ + 'a', '', '**Veredicto:** ' + veredicto]
    if huella:
        o.append('**Huella:** ' + huella)
    o += ['', '## F', '- ' + (f or 'Ninguno.'), '', '## P', '- ' + (p or 'Ninguno.'), '',
          '## Avisos del script', '- Ninguno.', '']
    return NL.join(o)


def main():
    base = tempfile.mkdtemp(prefix='probar-lote-')
    salida_real = os.path.join(RAIZ, 'borrador')
    antes_output = sorted(os.listdir(salida_real)) if os.path.isdir(salida_real) else None
    caches = [os.path.join(AQUI, '__pycache__'), os.path.join(AQUI, 'auditoria', '__pycache__')]
    antes_cache = [os.path.exists(x) for x in caches]
    try:
        probar(base)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    despues_output = sorted(os.listdir(salida_real)) if os.path.isdir(salida_real) else None
    chequeo('La prueba no creo nada en borrador/ del repo', despues_output, antes_output)
    chequeo('La prueba no dejo __pycache__ nuevos en bin/',
            [os.path.exists(x) for x in caches], antes_cache)

    total, malos = len(resultados), resultados.count(False)
    print()
    print(('OK -- ' if not malos else 'FALLA -- ') + str(total - malos) + ' de ' + str(total) +
          ' casos dieron lo esperado.')
    return 1 if malos else 0


def probar(base):
    ficha = os.path.join(base, 'ficha.md')
    escribir(ficha, FICHA)
    ficha2 = os.path.join(base, 'ficha-sin-maqueta.md')
    escribir(ficha2, FICHA_SIN_MAQUETA)
    raiz = os.path.join(base, 'borrador')
    L = os.path.join(raiz, 'lote-20261001-prueba')
    rel_lote = L.replace(os.sep, '/')

    # --- preparar ---------------------------------------------------------------------
    c, out, _ = correr('preparar', 'prueba', '--ficha', ficha, '--fecha', '20261001',
                       '--raiz-output', raiz)
    chequeo('preparar: sale 0', c, 0)
    chequeo('preparar: crea CONTEXTO.md, items.json, tiempos.json, auditorias/ y antes/',
            [os.path.exists(os.path.join(L, x)) for x in
             ('CONTEXTO.md', 'items.json', 'tiempos.json', 'auditorias', 'antes')], [True] * 5)
    ctx = leer(os.path.join(L, 'CONTEXTO.md'))
    titulos = [l[3:] for l in ctx.split(NL) if l.startswith('## ')]
    chequeo('preparar: CONTEXTO.md tiene las 8 secciones, en orden', titulos, [
        'Alcance', 'Fuentes le' + I_ + 'das', 'Decidido por fuente (F)',
        'Recomendaciones aplicadas (R)', 'Preguntas (P)', 'Dedup por ' + I_ + 'tem',
        'Estado de las tarjetas a editar', 'Conocimiento para el Cerebro'])
    chequeo('preparar: Fuentes leidas cita la maqueta y el [F-01] de la ficha',
            ('entregables/disenos/maqueta-prueba.html' in ctx, '[F-01] Buscar a la persona' in ctx),
            (True, True))
    items = leer_json(os.path.join(L, 'items.json'))
    chequeo('preparar: items.json arranca vacio, con esquema y la maqueta del lote',
            (items['items'], '_esquema' in items, items['lote'].get('maqueta')),
            ([], True, 'entregables/disenos/maqueta-prueba.html'))
    t = leer_json(os.path.join(L, 'tiempos.json'))
    chequeo('preparar: tiempos.json marca el inicio de preparar',
            (bool(t['fases']['preparar'][0]['inicio']), t['fases']['preparar'][0]['fin']),
            (True, None))
    antes_ctx = leer_bytes(os.path.join(L, 'CONTEXTO.md'))
    c, out, _ = correr('preparar', 'prueba', '--ficha', ficha, '--fecha', '20261001',
                       '--raiz-output', raiz)
    chequeo('preparar: no pisa una carpeta que ya existe (sale 1 y no la toca)',
            (c, leer_bytes(os.path.join(L, 'CONTEXTO.md')) == antes_ctx), (1, True))
    c, out, _ = correr('preparar', 'nada', '--ficha', os.path.join(base, 'no-existe.md'),
                       '--fecha', '20261001', '--raiz-output', raiz)
    chequeo('preparar: ficha que no se puede leer es SIN DATOS y no crea la carpeta',
            (c, os.path.exists(os.path.join(raiz, 'lote-20261001-nada'))), (2, False))
    c, out, _ = correr('preparar', 'Tema Malo', '--ficha', ficha, '--raiz-output', raiz)
    chequeo('preparar: tema con espacios o mayusculas no sirve (2)', c, 2)
    c, out, _ = correr('preparar', 'otra', '--ficha', ficha2, '--fecha', '20261001',
                       '--raiz-output', raiz)
    ctx2 = leer(os.path.join(raiz, 'lote-20261001-otra', 'CONTEXTO.md'))
    chequeo('preparar: ficha sin fuente_maqueta ni bloque de derivacion queda avisado',
            (c, AVISO + ' La ficha no cita `fuente_maqueta`' in ctx2, 'Derivaci' + O_ + 'n a backlog'
             in ctx2), (0, True, True))

    # --- item -------------------------------------------------------------------------
    c, out, _ = correr('item', L, '--clave', 'H-01', '--tipo', 'Historia', '--accion', 'ALTA',
                       '--titulo', 'Buscar a la persona', '--padre', '200051', '--flujo', 'F-01',
                       '--gates', 'OK', '--dedup', '3 consultas ' + MEDIO + ' 0 cand.')
    h = item_de(L, 'H-01')
    chequeo('item: una Historia nueva toma sus archivos y la ficha por default',
            (c, h['archivo'], h['criterios'], h['padre'], h['ficha'] == items['lote']['ficha']),
            (0, 'H-01.html', 'H-01-criterios.html', '#200051', True))
    cmd_t01 = ('item', L, '--clave', 'T-01', '--tipo', 'Tarea', '--accion', 'ALTA', '--titulo',
               'Back: buscar persona', '--padre', 'H-01', '--puntos', '3')
    c, out, _ = correr(*cmd_t01)
    t1 = item_de(L, 'T-01')
    chequeo('item: una Tarea de [H-01] toma los Criterios de H-01 como criterios_padre',
            (c, t1['padre'], t1['criterios_padre'], t1['puntos']), (0, '[H-01]',
                                                                    'H-01-criterios.html', 3))
    primero = leer_bytes(os.path.join(L, 'items.json'))
    correr(*cmd_t01)
    chequeo('item: el mismo pedido dos veces deja items.json igual (idempotente)',
            leer_bytes(os.path.join(L, 'items.json')) == primero, True)
    c, out, _ = correr('item', L, '--clave', 'T-01', '--dedup', '2 consultas ' + MEDIO + ' 0 cand.',
                       '--gates', 'OK')
    t1 = item_de(L, 'T-01')
    chequeo('item: actualizar cambia solo lo que se pasa',
            (c, t1['titulo'], t1['puntos'], t1['gates']), (0, 'Back: buscar persona', 3, 'OK'))
    for clave, titulo in (('T-02', 'Front: pantalla'), ('T-03', 'Back: paginar')):
        correr('item', L, '--clave', clave, '--tipo', 'Tarea', '--accion', 'ALTA', '--titulo',
               titulo, '--padre', '[H-01]', '--gates', 'OK', '--dedup', '1 consulta')
    correr('item', L, '--clave', 'T-04', '--tipo', 'Tarea', '--accion', 'PISA', '--id', '#125280',
           '--titulo', 'Back: ajustar validacion', '--padre', '#125063', '--criterios-padre',
           'padre-125063-criterios.html', '--gates', 'OK', '--cambia',
           'Se agrega el caso de error de la sala no disponible.')
    correr('item', L, '--clave', 'R-01', '--tipo', 'Tarea', '--accion', 'RELACION', '--titulo',
           'Relacionar #125100 con [T-01]', '--id', '125100', '--relacion', '[T-01]', '--gates', 'OK')
    c, out, _ = correr('item', L, '--clave', 'E-01', '--tipo', 'Tarea', '--accion', 'EXISTE',
                       '--id', '125200', '--titulo', 'Back: alta ya cargada', '--padre', '[H-01]',
                       '--archivo', 'existe-125200.html')
    e1 = item_de(L, 'E-01')
    chequeo('item: EXISTE (Tarea ya cargada) se anota con su #ID, su html y su padre',
            (c, e1['accion'], e1['id'], e1['archivo'], e1['criterios_padre']),
            (0, 'EXISTE', '125200', 'existe-125200.html', 'H-01-criterios.html'))
    c, out, _ = correr('item', L, '--clave', 'E-02', '--tipo', 'Tarea', '--accion', 'EXISTE',
                       '--titulo', 'x')
    chequeo('item: EXISTE sin --id no se acepta (1)', c, 1)
    c, out, _ = correr('item', L, '--clave', 'E-03', '--tipo', 'Historia', '--accion', 'EXISTE',
                       '--id', '1234567', '--titulo', 'x')
    chequeo('item: EXISTE es solo para Tareas (1)', c, 1)
    c, out, _ = correr('item', L, '--clave', 'T-05', '--tipo', 'Historia', '--accion', 'ALTA',
                       '--titulo', 'x')
    chequeo('item: una Historia con clave T-nn choca (1)', c, 1)
    c, out, _ = correr('item', L, '--clave', 'T-06', '--tipo', 'Tarea', '--accion', 'PISA',
                       '--titulo', 'x')
    chequeo('item: PISA sin --id no se acepta (1)', c, 1)
    c, out, _ = correr('item', L, '--clave', 'T-07', '--tipo', 'Tarea', '--accion', 'ALTA')
    chequeo('item: un item nuevo sin titulo no se acepta (1)', c, 1)
    c, out, _ = correr('item', L, '--clave', 'T-01', '--padre', 'la historia de pepe')
    chequeo('item: un padre que no es #ID ni [H-nn] es un pedido mal armado (2)', c, 2)
    claves = [i['clave'] for i in leer_json(os.path.join(L, 'items.json'))['items']]
    chequeo('item: items.json queda ordenado por clave y sin los rechazados', claves,
            ['E-01', 'H-01', 'R-01', 'T-01', 'T-02', 'T-03', 'T-04'])

    # --- borradores del lote ------------------------------------------------------------
    for nombre, contenido in (('H-01-criterios.html', CRITERIOS), ('H-01.html', H01),
                              ('T-01.html', T01), ('T-02.html', T02), ('T-03.html', T03),
                              ('T-04.html', T04), ('padre-125063-criterios.html', CRITERIOS),
                              ('antes/125280.html', '<p>lo de antes</p>'),
                              ('existe-125200.html', E01)):
        escribir(os.path.join(L, nombre), contenido)

    # --- mision -----------------------------------------------------------------------
    c1, m1, b1 = correr('mision', L, 'redactar', 'T-01')
    c2, m2, b2 = correr('mision', L, 'redactar', 'T-01')
    chequeo('mision redactar: el mismo item da el mismo texto, byte por byte', (c1, b1 == b2),
            (0, True))
    chequeo('mision redactar: lista el brief, los Criterios del padre, las hermanas y las skills',
            (rel_lote + '/CONTEXTO.md' in m1, rel_lote + '/H-01-criterios.html' in m1,
             'Tarea hermana T-02' in m1, 'Tarea ya cargada #125200' in m1,
             '**plantillas/tarea**' in m1, '**estimar-story-points**' in m1,
             rel_lote + '/T-01.json' in m1),
            (True, True, True, True, True, True, True))
    chequeo('mision redactar: no queda ningun {marcador} sin reemplazar',
            re.findall(r'\{[a-z_]+\}', m1), [])
    c, ma, _ = correr('mision', L, 'auditar', 'T-01')
    chequeo('mision auditar: sin el brief, con el chequeo mecanico y la huella de lo auditado',
            (c, rel_lote + '/CONTEXTO.md' in ma, rel_lote + '/auditorias/T-01.md' in ma,
             rel_lote + '/auditorias/T-01-auditor.md' in ma, '**auditar-tarea**' in ma,
             len(huella_de(ma) or ''), re.findall(r'\{[a-z_]+\}', ma)),
            (0, False, True, True, True, 16, []))
    c, mh, _ = correr('mision', L, 'auditar', 'H-01')
    chequeo('mision auditar (Historia): incluye la maqueta vigente y los pendientes del Cerebro',
            (c, '`entregables/disenos/maqueta-prueba.html`' in mh,
             '`cerebro-digital/modulo-ejemplo/pendientes.md`' in mh,
             '**auditar-historia**' in mh), (0, True, True, True))
    c, mc, bc1 = correr('mision', L, 'corregir', 'H-01')
    _, _, bc2 = correr('mision', L, 'corregir', 'H-01')
    chequeo('mision corregir (Historia): sus Criterios y el informe del auditor, siempre igual',
            (c, rel_lote + '/H-01-criterios.html' in mc, rel_lote + '/auditorias/H-01-auditor.md'
             in mc, '**plantillas/historia-de-usuario**' in mc, bc1 == bc2,
             re.findall(r'\{[a-z_]+\}', mc)), (0, True, True, True, True, []))
    c, mp, _ = correr('mision', L, 'redactar', 'T-04')
    chequeo('mision redactar (PISA): le pasa el ANTES de la tarjeta', (c, rel_lote +
            '/antes/125280.html' in mp), (0, True))
    c, _, _ = correr('mision', L, 'redactar', 'R-01')
    chequeo('mision: una RELACION no se redacta (1)', c, 1)
    c, _, _ = correr('mision', L, 'auditar', 'E-01')
    chequeo('mision: una Tarea EXISTE no se audita sola (1)', c, 1)
    c, _, _ = correr('mision', L, 'auditar', 'T-99')
    chequeo('mision: una clave que no esta (1)', c, 1)
    c, _, bg = correr('mision', L, 'redactar', 'T-01', '--guardar')
    chequeo('mision --guardar: deja en misiones/ lo mismo que imprime',
            leer_bytes(os.path.join(L, 'misiones', 'T-01-redactar.md')) == bg, True)

    # --- cierre sin auditoria (es opcional) ----------------------------------------------
    c, cierre0, _ = correr('cierre', L)
    chequeo('cierre sin auditoria: la columna dice "no se pidio" y no frena ninguna fila',
            (celda(cierre0, 'T-01', 6), celda(cierre0, 'H-01', 6),
             'Ninguna fila dice FRENA ni SIN DATOS.' in cierre0),
            ('no se pidi' + O_, 'no se pidi' + O_, True))
    chequeo('cierre sin auditoria: avisa que ninguna tarjeta lleva sello',
            'Auditor' + I_ + 'a: no se pidi' + O_ + '. Ninguna tarjeta lleva sello.' in cierre0, True)

    # --- auditar ----------------------------------------------------------------------
    vacio = os.path.join(base, 'bin-vacio')
    os.makedirs(vacio)
    c, out, _ = correr('auditar', L, '--bin', vacio)
    d1 = leer_json(os.path.join(L, 'auditorias', 'T-01.json'))
    chequeo('auditar: sin los scripts es SIN DATOS (2), nunca OK',
            (c, d1['veredicto'], 'no existe' in (d1.get('sin_datos') or ''),
             os.path.exists(os.path.join(L, 'auditorias', 'T-01.md')),
             os.path.exists(os.path.join(L, 'auditorias', 'set-H-01.json'))),
            (2, 'SIN DATOS', True, True, True))
    dobles = os.path.join(base, 'bin-dobles')
    log = os.path.join(base, 'llamadas.log')
    bandera = os.path.join(base, 'set-malo')
    for herr in ('auditar-tarea', 'auditar-historia', 'analizar-tareas'):
        escribir(os.path.join(dobles, herr + '.py'), DOBLE % (herr, log, bandera))
    c, out, _ = correr('auditar', L, '--bin', dobles)
    llamadas = [l.split(' ', 1) for l in leer(log).strip().split(NL)]
    args = {}
    for herr, a in llamadas:
        args.setdefault(herr, []).append(json.loads(a))
    chequeo('auditar: con hallazgos sale 1; corre en orden de clave y la EXISTE no se audita sola',
            (c, [x[0] for x in llamadas]), (1, ['auditar-historia', 'auditar-tarea',
                                                'auditar-tarea', 'auditar-tarea', 'auditar-tarea',
                                                'analizar-tareas']))
    t01_args = args['auditar-tarea'][0]
    chequeo('auditar: a la Tarea le pasa los Criterios del padre (--historia)',
            (t01_args[0].endswith('T-01.html'), t01_args[1], t01_args[2].endswith(
                'H-01-criterios.html'), '--json' in t01_args), (True, '--historia', True, True))
    h_args = args['auditar-historia'][0]
    chequeo('auditar: a la Historia le pasa Criterios, Descripcion, ficha y flujo',
            [x in h_args for x in ('--criterios', '--descripcion', '--ficha', '--flujo', 'F-01')],
            [True] * 5)
    a_args = args['analizar-tareas'][0]
    chequeo('auditar: analizar-tareas recibe los Criterios, la Descripcion del [H-nn], los #ID y '
            'las 4 Tareas (con la EXISTE)',
            (a_args[0], a_args[a_args.index('--descripcion') + 1].endswith('H-01.html'),
             a_args[a_args.index('--ids') + 1].endswith('items.json'),
             sum(1 for x in a_args if x.endswith(('T-01.html', 'T-02.html', 'T-03.html',
                                                  'existe-125200.html')))),
            ('--historia', True, True, 4))
    chequeo('auditar: deja json, md y huella por item y por set',
            [os.path.exists(os.path.join(L, 'auditorias', n + x)) for n in ('T-02', 'set-H-01')
             for x in ('.json', '.md', '.huella.json')], [True] * 6)
    chequeo('auditar: el veredicto de cada item sale del script',
            (leer_json(os.path.join(L, 'auditorias', 'T-01.json'))['veredicto'],
             leer_json(os.path.join(L, 'auditorias', 'T-02.json'))['veredicto']),
            ('SIN HALLAZGOS', 'CON HALLAZGOS'))
    correr('item', L, '--clave', 'T-08', '--tipo', 'Tarea', '--accion', 'ALTA', '--titulo',
           'Sin archivo', '--padre', '#125063', '--criterios-padre', 'padre-125063-criterios.html',
           '--gates', 'OK', '--dedup', '1 consulta')
    c, out, _ = correr('auditar', L, '--bin', dobles)
    d8 = leer_json(os.path.join(L, 'auditorias', 'T-08.json'))
    chequeo('auditar: un item sin su archivo es SIN DATOS sin llamar al script (2)',
            (c, d8['veredicto'], 'falta el archivo' in (d8.get('sin_datos') or '')),
            (2, 'SIN DATOS', True))
    escribir(os.path.join(L, 'T-08.html'), T03)
    c, out, _ = correr('auditar', L, '--bin', dobles)
    chequeo('auditar: con el archivo ya escrito vuelve a 1 (queda el hallazgo de T-02)', c, 1)

    # --- informes de los auditores y la huella --------------------------------------------
    hu = {}
    for clave in ('H-01', 'T-01', 'T-02', 'T-03', 'T-04', 'T-08'):
        hu[clave] = huella_de(correr('mision', L, 'auditar', clave)[1])

    def informar(clave, veredicto, huella=True, p=None, f=None):
        escribir(os.path.join(L, 'auditorias', clave + '-auditor.md'), informe_auditor(
            veredicto, hu[clave] if huella is True else huella, p, f))

    informar('H-01', 'COMPLETA | CON HUECOS | NO AUDITABLE')
    informar('T-01', 'COMPLETA', p='P-1 ' + MEDIO + ' el orden por defecto ' + MEDIO +
             ' Recomiendo: por fecha', f='F-1 ' + MEDIO + ' falta el test del 404 ' + MEDIO +
             ' fuente: RN-MOD-001 ' + MEDIO + ' arreglo: agregar el test')
    informar('T-02', 'COMPLETA')
    informar('T-03', 'CON HUECOS', huella=None)
    informar('T-04', 'COMPLETA', huella='deadbeefdeadbeef')
    informar('T-08', 'COMPLETA')
    ctx = leer(os.path.join(L, 'CONTEXTO.md'))
    ctx = ctx.replace('## Decidido por fuente (F)' + NL, '## Decidido por fuente (F)' + NL + NL +
                      '- Texto del boton: Guardar ' + MEDIO + ' maqueta v1.2' + NL)
    ctx = ctx.replace('## Recomendaciones aplicadas (R)' + NL, '## Recomendaciones aplicadas (R)' +
                      NL + NL + 'Ninguno.' + NL)
    ctx = ctx.replace('## Preguntas (P)' + NL, '## Preguntas (P)' + NL + NL + 'Ninguno.' + NL)
    escribir(os.path.join(L, 'CONTEXTO.md'), ctx)

    _, cierre, _ = correr('cierre', L)
    chequeo('huella: un informe del auditor sin la linea Huella no se sella',
            (celda(cierre, 'T-03', 6) or '').startswith(OTRA_VERSION), True)
    chequeo('huella: un informe con otra Huella no se sella (y suma lo del set)',
            ((celda(cierre, 'T-04', 6) or '').startswith(OTRA_VERSION),
             NO_SELLA + 'set #125063 sin informe' in (celda(cierre, 'T-04', 6) or '')), (True, True))
    informar('T-03', 'CON HUECOS')
    informar('T-04', 'COMPLETA')
    _, cierre, _ = correr('cierre', L)
    chequeo('set: sin el informe del auditor del set, sus Tareas no se sellan',
            NO_SELLA + 'set [H-01] sin informe del auditor' in (celda(cierre, 'T-01', 6) or ''),
            True)

    # --- el auditor del set -------------------------------------------------------------
    c, ms, bs1 = correr('mision', L, 'auditar', 'set-H-01')
    _, _, bs2 = correr('mision', L, 'auditar', 'set-H-01')
    chequeo('mision auditar set-H-01: mismo texto dos veces; Tareas, Criterios, Descripcion, '
            'chequeo del set, skill y huella',
            (c, bs1 == bs2, all(rel_lote + '/' + x in ms for x in (
                'T-01.html', 'T-02.html', 'T-03.html', 'existe-125200.html',
                'H-01-criterios.html', 'H-01.html', 'auditorias/set-H-01.md',
                'auditorias/set-H-01-auditor.md')),
             'ya cargada: #125200' in ms, '**analizar-tareas**' in ms,
             'CIERRA | CON HUECOS | NO AUDITABLE' in ms, len(huella_de(ms) or ''),
             re.findall(r'\{[a-z_]+\}', ms)),
            (0, True, True, True, True, True, 16, []))
    c, _, _ = correr('mision', L, 'redactar', 'set-H-01')
    chequeo('mision: un set no se redacta (1)', c, 1)
    c, _, _ = correr('mision', L, 'auditar', 'set-H-99')
    chequeo('mision: un set que no existe (1)', c, 1)
    hu['set-H-01'] = huella_de(ms)
    hu['set-125063'] = huella_de(correr('mision', L, 'auditar', 'set-125063')[1])
    informar('set-H-01', 'CIERRA', p='P-1 ' + MEDIO + ' quien prueba la union ' + MEDIO +
             ' Recomiendo: T-02')
    informar('set-125063', 'CIERRA')
    escribir(bandera, 'x')
    c, _, _ = correr('auditar', L, '--bin', dobles)
    _, cierre, _ = correr('cierre', L)
    chequeo('set: si analizar-tareas no da SIN HALLAZGOS, se avisa en sus Tareas como pendientes',
            (c, celda(cierre, 'T-01', 6), celda(cierre, 'T-04', 6)),
            (1, 'COMPLETA (script: SIN HALLAZGOS) ' + MEDIO + ' set [H-01] CON HALLAZGOS (van como '
             'pendientes a confirmar)', 'COMPLETA (script: SIN HALLAZGOS) ' + MEDIO +
             ' set #125063 CON HALLAZGOS (van como pendientes a confirmar)'))
    # el set CON HALLAZGOS sin informe valido del auditor no se sella (no alcanza con el script)
    informe_set = os.path.join(L, 'auditorias', 'set-H-01-auditor.md')
    guardado_set = leer_bytes(informe_set)
    os.remove(informe_set)
    _, cierre_s, _ = correr('cierre', L)
    chequeo('set: CON HALLAZGOS y sin informe del auditor del set, sus Tareas no se sellan',
            NO_SELLA + 'set [H-01] sin informe del auditor' in (celda(cierre_s, 'T-01', 6) or ''),
            True)
    with open(informe_set, 'wb') as f:
        f.write(guardado_set)
    os.remove(bandera)
    correr('auditar', L, '--bin', dobles)
    # el script del set que no pudo analizar (SIN DATOS) tampoco deja sellar
    json_set = os.path.join(L, 'auditorias', 'set-H-01.json')
    guardado_json = leer_bytes(json_set)
    d_set = leer_json(json_set)
    d_set['codigo'] = 2
    escribir(json_set, json.dumps(d_set))
    _, cierre_s, _ = correr('cierre', L)
    chequeo('set: el script del set en SIN DATOS no deja sellar sus Tareas',
            NO_SELLA + 'set [H-01] SIN DATOS' in (celda(cierre_s, 'T-01', 6) or ''), True)
    with open(json_set, 'wb') as f:
        f.write(guardado_json)

    # --- cierre -----------------------------------------------------------------------
    c1, cierre, b1 = correr('cierre', L)
    c2, _, b2 = correr('cierre', L)
    chequeo('cierre: el mismo lote da el mismo CIERRE.md, byte por byte, igual a lo que imprime',
            (b1 == b2, leer_bytes(os.path.join(L, 'CIERRE.md')) == b1), (True, True))
    encabezado = ('| # | Acci' + O_ + 'n | ' + chr(0xcd) + 'tem | Padre | Puntos | GATES y ' +
                  chr(0xa7) + '2b | Auditor' + I_ + 'a | `' + AVISO + '` abiertos | Dedup | Archivo |')
    chequeo('cierre: el encabezado es exactamente el de planificar-lote', encabezado in
            cierre.split(NL), True)
    f1 = fila(cierre, 'T-01')
    chequeo('cierre: T-01 lleva veredicto del auditor y del script, sus P-nnn, dedup y gates',
            (f1[1], f1[3], f1[4], f1[5], f1[6], f1[7], f1[8]) if f1 else None,
            ('ALTA', '`[H-01]`', '3', 'OK', 'COMPLETA (script: SIN HALLAZGOS)', 'P-001, P-004',
             '2 consultas ' + MEDIO + ' 0 cand.'))
    chequeo('cierre: COMPLETA del auditor contra un HALLAZGO del script no se sella',
            celda(cierre, 'T-02', 6), NO_SELLA + 'el auditor dijo COMPLETA y el script CON HALLAZGOS')
    chequeo('cierre: un informe sin veredicto elegido no se sella',
            (celda(cierre, 'H-01', 6) or '').startswith(NO_SELLA + 'el informe del auditor no dice'),
            True)
    f3 = fila(cierre, 'T-03')
    chequeo('cierre: CON HUECOS se carga (no frena) y cuenta sus pendientes',
            (f3[6], f3[7]) if f3 else None, ('CON HUECOS (script: SIN HALLAZGOS)', '1'))
    f4 = fila(cierre, 'T-04')
    chequeo('cierre: la fila PISA va en negrita, sin dedup y avisa la falta de Datos a confirmar',
            (f4[1], f4[6], f4[8], f4[7].startswith('SIN DATOS')) if f4 else None,
            ('**PISA**', 'COMPLETA (script: SIN HALLAZGOS)', 'no aplica', True))
    fr = fila(cierre, 'R-01')
    chequeo('cierre: la RELACION no se audita',
            (fr[1], fr[6], fr[7]) if fr else None, ('RELACI' + chr(0xd3) + 'N', 'no aplica', '-'))
    fe = fila(cierre, 'E-01')
    chequeo('cierre: la EXISTE es una fila informativa que no se escribe',
            ((fe[1], fe[5], fe[6]) if fe else None,
             'Las filas EXISTE no se escriben' in cierre),
            (('EXISTE', 'no se escribe (ya cargada)', 'no aplica (entra al set)'), True))
    chequeo('cierre: la auditoria no frena filas (ni la que no se sella)',
            'Ninguna fila dice FRENA ni SIN DATOS.' in cierre, True)
    chequeo('cierre: copia F de CONTEXTO.md y marca vacio el Conocimiento',
            ('- Texto del boton: Guardar' in cierre,
             'SIN DATOS: la secci' + O_ + 'n ' + chr(0xab) + 'Conocimiento para el Cerebro' in cierre,
             'Se agrega el caso de error de la sala no disponible.' in cierre),
            (True, True, True))
    chequeo('cierre: suma los F y los P de los auditores (items y sets)',
            ('**De las auditor' + I_ + 'as (F)**' in cierre,
             '- T-01 ' + MEDIO + ' F-1 ' + MEDIO + ' falta el test del 404' in cierre,
             '- T-01 ' + MEDIO + ' P-1 ' + MEDIO + ' el orden por defecto' in cierre,
             '- set-H-01 ' + MEDIO + ' P-1 ' + MEDIO + ' quien prueba la union' in cierre),
            (True, True, True, True))
    chequeo('cierre: termina con la linea de los sellos y la pregunta',
            cierre.rstrip(NL).split(NL)[-3:],
            ['Las tarjetas con veredicto en la columna Auditor' + I_ + 'a llevan su sello (las que '
             'dicen NO SE SELLA o no se pidi' + O_ + ', no), y sus hallazgos van como pendientes a '
             'confirmar (molde de [[comentar-tarea]]).', '',
             chr(0xbf) + 'Escribo todo el lote?'])
    chequeo('cierre: sale 0 porque la auditoria no frena ninguna fila', c1, 0)

    original = leer_bytes(os.path.join(L, 'T-01.html'))
    with open(os.path.join(L, 'T-01.html'), 'ab') as f:
        f.write(b'<p>cambio</p>')
    _, cierre_v, _ = correr('cierre', L)
    chequeo('huella: si el archivo cambio despues de auditar, la fila no se sella',
            (celda(cierre_v, 'T-01', 6) or '').startswith(NO_SELLA + 'cambi' + O_ + ' archivo'), True)
    correr('auditar', L, '--bin', dobles)
    _, cierre_v, _ = correr('cierre', L)
    chequeo('huella: re-correr solo el script no alcanza: el informe del auditor es de otra version',
            (celda(cierre_v, 'T-01', 6) or '').startswith(OTRA_VERSION), True)
    with open(os.path.join(L, 'T-01.html'), 'wb') as f:
        f.write(original)
    correr('auditar', L, '--bin', dobles)
    _, cierre_r, _ = correr('cierre', L)
    chequeo('huella: con el archivo como se audito, vuelve a pasar', celda(cierre_r, 'T-01', 6),
            'COMPLETA (script: SIN HALLAZGOS)')

    # --- ids --------------------------------------------------------------------------
    afuera = os.path.join(base, 'afuera', 'T-09.html')
    escribir(afuera, '<p>Usa [T-01].</p>')
    correr('item', L, '--clave', 'T-09', '--tipo', 'Tarea', '--accion', 'ALTA', '--titulo',
           'Fuera del lote', '--archivo', afuera)
    mapa = {'[H-01]': '125271', 'T-01': '#125272', '[T-02]': '125273', '[T-03]': 125274}
    escribir(os.path.join(L, 'mapa-ids.json'), json.dumps(mapa))
    c, out, _ = correr('ids', L)
    final = leer(os.path.join(L, 'T-01.final.html'))
    chequeo('ids: escribe <clave>.final.html con los #ID y sin marcas (0)',
            (c, '#125273' in final, '#125271' in final, '[' in final.replace('[[', '')),
            (0, True, True, False))
    chequeo('ids: el original auditado no se toca', leer_bytes(os.path.join(L, 'T-01.html')),
            original)
    chequeo('ids: el .final.html va siempre a la carpeta del lote, nunca al lado de un archivo de '
            'afuera',
            (os.path.exists(os.path.join(L, 'T-09.final.html')),
             os.path.exists(os.path.join(base, 'afuera', 'T-09.final.html')),
             os.path.exists(os.path.join(L, 'H-01-criterios.final.html')),
             os.path.exists(os.path.join(L, 'E-01.final.html'))),
            (True, False, True, False))
    chequeo('ids: anota el #ID en items.json', item_de(L, 'T-01')['id'], '125272')
    escribir(os.path.join(L, 'mapa-parcial.json'), json.dumps({'[H-01]': '125271'}))
    c, out, _ = correr('ids', L, '--mapa', 'mapa-parcial.json')
    chequeo('ids: una marca sin #ID en el mapa sale 1 y se nombra', (c, '[T-02]' in out), (1, True))

    # --- comparar ---------------------------------------------------------------------
    azure = os.path.join(L, 'azure-T-01.html')
    escribir(azure, '<div>  <h3>Objetivo</h3>' + NL + '<p>Usa&nbsp;#125273 y   cuelga de #125271.</p>'
             '<h3>&#9888; Datos a confirmar</h3><ul><li>P-001 el codigo</li>' + NL +
             '<li>P-004 otra</li></ul></div>')
    c, out, _ = correr('comparar', os.path.join(L, 'T-01.html'), azure, '--mapa', 'mapa-ids.json')
    chequeo('comparar: --mapa con el nombre solo (desde la raiz) se busca junto al auditado, y lo '
            'reescrito por Azure es IGUAL (0)', (c, out.startswith('IGUALES')), (0, True))
    c, out, _ = correr('comparar', os.path.join(L, 'T-01.html'), azure, '--mapa', 'no-hay.json')
    chequeo('comparar: un mapa que no esta en ningun lado es SIN DATOS (2)', c, 2)
    c, out, _ = correr('comparar', os.path.join(L, 'T-01.html'), azure)
    chequeo('comparar: sin el mapa las marcas no coinciden: DISTINTOS (1) y avisa las marcas',
            (c, 'Primera diferencia' in out, 'marcas sin #ID' in out), (1, True, True))
    escribir(os.path.join(L, 'azure-T-02.html'), '<h3>Objetivo</h3><p>Otro texto.</p>')
    c, out, _ = correr('comparar', os.path.join(L, 'T-02.html'), os.path.join(L, 'azure-T-02.html'))
    chequeo('comparar: otro texto es DISTINTOS (1)', c, 1)
    c, out, _ = correr('comparar', os.path.join(L, 'T-01.html'), os.path.join(L, 'no-esta.html'))
    chequeo('comparar: un archivo que no se lee es SIN DATOS (2)', c, 2)
    escribir(os.path.join(L, 'vacio.html'), '<p> </p>')
    c, out, _ = correr('comparar', os.path.join(L, 'vacio.html'), os.path.join(L, 'vacio.html'))
    chequeo('comparar: dos textos vacios no son IGUALES: SIN DATOS (2)', c, 2)
    escribir(os.path.join(L, 'azure-T-01.json'), json.dumps(
        {'id': 125272, 'fields': {'System.Description': leer(azure)}}))
    c, out, _ = correr('comparar', os.path.join(L, 'T-01.html'), os.path.join(L, 'azure-T-01.json'),
                       '--mapa', os.path.join(L, 'mapa-ids.json'), '--campo', 'System.Description')
    chequeo('comparar --campo: lee el campo del json del work item (0)', c, 0)

    # --- item --desde-json --------------------------------------------------------------
    escribir(os.path.join(L, 'T-03.json'), json.dumps(
        {'clave': 'T-03', 'titulo': 'Back: paginar resultados', 'tipo': 'Tarea', 'padre': '[H-01]',
         'puntos': 5, 'actividad': 'Development', 'relaciones': ['#125100']}))
    c, out, _ = correr('item', L, '--clave', 'T-03', '--desde-json')
    t3 = item_de(L, 'T-03')
    chequeo('item --desde-json: toma titulo, puntos, actividad y relaciones del <clave>.json',
            (c, t3['titulo'], t3['puntos'], t3['actividad'], t3['relaciones'], t3['gates']),
            (0, 'Back: paginar resultados', 5, 'Development', ['#125100'], 'OK'))
    c, out, _ = correr('item', L, '--clave', 'T-03', '--desde-json', '--puntos', '8')
    chequeo('item --desde-json: lo que se pasa por la linea de comandos gana',
            (c, item_de(L, 'T-03')['puntos']), (0, 8))
    c, out, _ = correr('item', L, '--clave', 'T-02', '--desde-json')
    chequeo('item --desde-json: sin <clave>.json es SIN DATOS (2)', c, 2)

    # --- tiempos ----------------------------------------------------------------------
    c1, _, _ = correr('tiempos', L, 'arranque', 'inicio', '--ahora', '2026-10-01T10:00:00')
    c2, _, _ = correr('tiempos', L, 'arranque', 'inicio', '--ahora', '2026-10-01T10:01:00')
    c3, _, _ = correr('tiempos', L, 'arranque', 'fin', '--ahora', '2026-10-01T10:04:30')
    c4, _, _ = correr('tiempos', L, 'arranque', 'fin', '--ahora', '2026-10-01T10:05:00')
    chequeo('tiempos: inicio, inicio repetido (1), fin, fin sin inicio (1)', (c1, c2, c3, c4),
            (0, 1, 0, 1))
    c, out, _ = correr('tiempos', L)
    chequeo('tiempos: el informe mide la fase', (c, '| arranque | 5 min | 4 min 30 s | 1 |' in out),
            (0, True))
    c, out, _ = correr('tiempos', L, 'cafe', 'inicio')
    chequeo('tiempos: una fase que no existe es un pedido mal armado (2) y dice cuales son',
            (c, FASES in out), (2, True))
    c, out, _ = correr('tiempos', '--help')
    chequeo('tiempos: la ayuda y el docstring nombran las fases',
            (c, FASES in out.replace(NL, ' ').replace('  ', ' '), FASES in leer(LOTE_PY)),
            (0, True, True))
    c, _, _ = correr('tiempos', L, 'cierre', 'inicio', '--ahora', 'ayer')
    chequeo('tiempos: --ahora que no es ISO (2)', c, 2)
    correr('tiempos', L, 'cierre', 'inicio', '--ahora', '2026-10-01T11:00:00')
    c, _, _ = correr('tiempos', L, 'cierre', 'fin', '--ahora', '2026-10-01T10:00:00')
    chequeo('tiempos: un fin anterior al inicio no se anota (1)', c, 1)
    for nombre, minutos in (('rapido', (5, 5, 10, 8, 5, 5)), ('lento', (5, 5, 20, 10, 5, 5))):
        d = os.path.join(base, 'tiempos-' + nombre)
        fases = {}
        for (fase, m), h in zip(zip(('preparar', 'arranque', 'redactar', 'auditar', 'cierre',
                                     'escribir'), minutos), range(10, 16)):
            fases[fase] = [{'inicio': '2026-10-01T%02d:00:00-03:00' % h,
                            'fin': '2026-10-01T%02d:%02d:00-03:00' % (h, m)}]
        escribir(os.path.join(d, 'tiempos.json'), json.dumps({'fases': fases}))
        c, out, _ = correr('tiempos', d)
        esperado = 'DENTRO del objetivo' if nombre == 'rapido' else 'PASADO por 10 min 00 s'
        chequeo('tiempos: un lote ' + nombre + ' sale ' + esperado.split(' ')[0],
                (c, esperado in out), (0, True))

    # --- estado -----------------------------------------------------------------------
    escribir(os.path.join(L, 'T-03.html'), T03.replace('[H-01]', '[H-01] y [T-09] y [T-10]'))
    c, out, _ = correr('estado', L)
    chequeo('estado: resume items, EXISTE, sets, faltantes, auditoria vencida y marcas huerfanas',
            (c, 'Tarea ALTA: 5' in out, 'Tarea EXISTE: 1' in out,
             '| T-01 | Tarea | ALTA | json |' in out, 'VENCIDA' in out,
             'Set [H-01] (4 Tareas)' in out, '[T-10] en T-03' in out, '[T-09] en T-03' in out),
            (1, True, True, True, True, True, True, False))
    c, _, _ = correr('estado', os.path.join(base, 'no-hay-lote'))
    chequeo('estado: una carpeta que no existe es SIN DATOS (2)', c, 2)

    # --- la llamada real, si los scripts ya estan -----------------------------------------
    R = os.path.join(raiz, 'lote-20261001-real')
    correr('preparar', 'real', '--ficha', ficha, '--fecha', '20261001', '--raiz-output', raiz)
    correr('item', R, '--clave', 'H-01', '--tipo', 'Historia', '--accion', 'ALTA', '--titulo',
           'Buscar a la persona', '--flujo', 'F-01')
    for clave in ('T-01', 'T-02'):
        correr('item', R, '--clave', clave, '--tipo', 'Tarea', '--accion', 'ALTA', '--titulo',
               'Back: ' + clave, '--padre', '[H-01]')
    for nombre, contenido in (('H-01-criterios.html', CRITERIOS), ('H-01.html', H01),
                              ('T-01.html', T01), ('T-02.html', T02)):
        escribir(os.path.join(R, nombre), contenido)
    c, out, _ = correr('auditar', R)
    for nombre, herr in (('T-01', 'auditar-tarea'), ('H-01', 'auditar-historia'),
                         ('set-H-01', 'analizar-tareas')):
        d = leer_json(os.path.join(R, 'auditorias', nombre + '.json'))
        if os.path.isfile(os.path.join(AQUI, herr + '.py')):
            chequeo('auditar (real): ' + herr + '.py corre y deja su json',
                    (c in (0, 1, 2), d.get('herramienta'), d.get('codigo') in (0, 1, 2),
                     d.get('veredicto') in ('SIN HALLAZGOS', 'CON HALLAZGOS', 'SIN DATOS')),
                    (True, herr, True, True))
        else:
            chequeo('auditar (real): sin ' + herr + '.py en bin/ es SIN DATOS',
                    (c, d.get('veredicto')), (2, 'SIN DATOS'))

    # --- archivos ---------------------------------------------------------------------
    def ascii_ok(ruta):
        try:
            leer_bytes(ruta).decode('ascii')
            return True
        except UnicodeDecodeError:
            return False

    chequeo('archivos: lote.py y probar-lote.py son ASCII puro',
            (ascii_ok(LOTE_PY), ascii_ok(os.path.abspath(__file__))), (True, True))
    sh, ps1 = leer_bytes(os.path.join(AQUI, 'lote.sh')), leer_bytes(os.path.join(AQUI, 'lote.ps1'))
    chequeo('archivos: lote.sh ASCII con LF; lote.ps1 ASCII sin BOM',
            (ascii_ok(os.path.join(AQUI, 'lote.sh')), b'\r' in sh,
             ascii_ok(os.path.join(AQUI, 'lote.ps1')), ps1[:3] == b'\xef\xbb\xbf'),
            (True, False, True, False))
    estados = []
    for nombre in ('redactar', 'auditar', 'corregir'):
        b = leer_bytes(os.path.join(MISIONES, nombre + '.md'))
        try:
            b.decode('utf-8')
            utf8 = True
        except UnicodeDecodeError:
            utf8 = False
        estados.append((nombre, utf8, b[:3] == b'\xef\xbb\xbf', b'\r' in b))
    chequeo('archivos: las misiones son UTF-8 sin BOM y con LF', estados,
            [(n, True, False, False) for n in ('redactar', 'auditar', 'corregir')])
    chequeo('archivos: auditar.md pide la Huella y documenta el formato de F y P',
            [x in leer(os.path.join(MISIONES, 'auditar.md')) for x in
             ('**Huella:** {huella}', '## F', '## P', '`F:`')], [True] * 4)


if __name__ == '__main__':
    sys.exit(main())
