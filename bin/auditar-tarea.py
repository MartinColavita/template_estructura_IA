#!/usr/bin/env python3
"""Auditoria MECANICA de UNA Tarea: lo que se cuenta, lo cuenta este script.

    python bin/auditar-tarea.py <tarea.html> [--historia <criterios.html>] [--json] [--salida <archivo>]

<tarea.html> es la Descripcion de la Tarea (System.Description, guardada desde el tablero, o el
borrador del modo lote). <criterios.html> es el campo Criterios de aceptacion de la Historia
padre (o su borrador). Sin --historia, todo chequeo que necesita al padre sale NO AUDITABLE,
nunca OK (Regla del cero).

Tres estados, nunca dos:  0 = sin hallazgos   1 = hay HALLAZGO o NO AUDITABLE   2 = SIN DATOS
SIN DATOS: la Tarea no se pudo leer, vino vacia o no tiene ni un <h3>. Cualquier error que no
se esperaba tambien da 2, nunca 0 ni 1.

POR QUE EXISTE. cargar-a-azure 2b (el autochequeo al escribir) y auditar-tarea (el segundo
chequeo, de otro agente) tenian chequeos que son CONTEO: secciones, numeracion de los tests,
Escenarios del padre contra la tabla, reglas citadas, enlaces, HTML, guardarrailes, Modos de
falla, Datos a confirmar y tamano. Un modelo leyendo una tarjeta de 30.000 caracteres tarda,
gasta y cada sesion cuenta distinto. Este script cuenta igual siempre, en segundos. Al auditor
le queda solo lo que pide criterio, y el reporte lo lista al final ("Lo que este script NO
mira"). Lo que este script marca HALLAZGO, el modelo no lo da por bueno.

Cada renglon del reporte nombra su fuente: "2b-N" es la fila N del checklist de cierre de
cargar-a-azure (seccion 2b), "AT-N" es el chequeo N de auditar-tarea, "ESQ" es la forma del
Esquema y "TAM" el tamano (plantillas/tarea.md, "Tamano y forma").

FUENTE UNICA DEL ESQUELETO. La lista de <h3> esperada se lee en cada corrida del bloque html de
la Tarea en tablero/checklists/mapa-campos-azure.md. Si se cambia el
esqueleto alla, este script lo sigue solo.

SOLO LECTURA: no usa la red, no toca Azure, GitLab ni el Cerebro. Escribe, como mucho, el
archivo que se le pide con --salida. Solo biblioteca estandar; ASCII puro en este archivo.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auditoria import cerebro, historia, texto, tarea  # noqa: E402
from auditoria import reporte as rep  # noqa: E402

HERRAMIENTA = 'auditar-tarea'
WARN = tarea.WARN
FLECHA = tarea.FLECHA
# Secciones que el pipeline agrega a proposito y no estan en el esqueleto (ya comparadas
# sin acentos): no son AVISO. "Esfuerzo IA" es la de estimar-story-points.
SECCIONES_EXTRA_CONOCIDAS = ('esfuerzo ia',)

PARA_EL_AUDITOR = [
    'AT-4b: cada regla citada DICE lo que el test le atribuye (abrir la regla en el Cerebro; '
    'una regla que no define el criterio del test es trazabilidad falsa).',
    'AT-6: cada test es verificable: entrada concreta y resultado esperado concreto.',
    '2b-10: PHI que la heuristica no ve (nombres, direcciones, diagnosticos): leer el texto.',
    'AT-8: cada test puede fallar, y cada guardarrail esta bien ganado (afirma sobre la fuente '
    'y ningun otro test de la lista lo implica).',
    'AT-10: no hay tests de implementacion (clases internas, conteo de llamadas, orden).',
    'AT-12: spec inventada: cada validacion y cada fila de Casos de error rastrea a una regla, '
    'al Gherkin del padre o al contrato de un sistema externo.',
    'AT-13: ningun test sobra (cada uno rastrea a una validacion, un caso de error, un codigo, '
    'una regla o un Escenario).',
    'AT-16: el resultado de cada test lo puede producir la capa que la Tarea declara.',
    'AT-7: confirmar o descartar los AVISO de conjunciones (un item = una sola condicion).',
    'AT-1: confirmar los AVISO de validaciones (una regla por test, no un campo por test).',
    'AT-2 / AT-3: comparar palabra por palabra el payload de cada fila, el resultado del test y '
    'el schema del contrato (campos del cuerpo de exito y nullable); el script solo mira que '
    'los codigos aparezcan.',
    'AT-5: que los tests de cada fila alcancen para cerrar ese Escenario (el script solo cuenta '
    'filas y titulos).',
    'AT-9: hay al menos una invariante de negocio protegida (el script solo busca la etiqueta).',
    'AT-11: cada familia de Modos de falla esta cubierta por un test real o descartada con un '
    'motivo valido (el script solo mira que las seis esten escritas).',
]


# ---------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------

def rangos(nums):
    """[1, 2, 3, 7] -> '1 a 3, 7'."""
    nums = sorted(set(nums))
    partes, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        partes.append(str(nums[i]) if j == i else
                      ('%d, %d' % (nums[i], nums[j]) if j == i + 1 else
                       '%d a %d' % (nums[i], nums[j])))
        i = j + 1
    return ', '.join(partes)


def corto(s, largo=110):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= largo else s[:largo - 3] + '...'


def palabra_en(valor, textos):
    """'exacto' si el valor aparece tal cual (como palabra), 'suelto' si aparece sin tildes ni
    mayusculas (y con '_' como espacio: BARRIO_PRIVADO vale "barrio privado"), None si no.

    Un valor que solo aparece como pedazo de otro identificador (VIGENCIA_HASTA adentro de
    VIGENCIA_HASTA_SUPERA_TOPE) no cuenta.
    """
    rx = re.compile(r'(?<![\w])' + re.escape(valor) + r'(?![\w])')
    if any(rx.search(t) for t in textos):
        return 'exacto'
    v = tarea.n(valor)
    if not v:
        return None
    rx2 = re.compile(r'(?<![\w])' + re.escape(v).replace('_', '[_ ]') + r'(?![\w])')
    if any(rx2.search(tarea.n(t)) for t in textos):
        return 'suelto'
    return None


def cuerpo_sin_seccion(doc, clave):
    """Todo el documento menos la seccion cuyo titulo empieza con clave."""
    return '\n'.join(t + '\n' + c for t, c in texto.secciones(doc)
                     if not tarea.clave_titulo(t).startswith(clave))


def _sin_comillas_ni_codigo(html_li):
    s = re.sub(r'<code\b[^>]*>.*?</code\s*>', ' ', html_li or '', flags=re.I | re.S)
    s = tarea.plano(tarea.sin_listas(s))
    s = re.sub(r'"[^"]*"', ' ', s)
    s = re.sub('[' + chr(0x201c) + '][^' + chr(0x201d) + ']*[' + chr(0x201d) + ']', ' ', s)
    s = re.sub('[' + chr(0xab) + '][^' + chr(0xbb) + ']*[' + chr(0xbb) + ']', ' ', s)
    return s


def flechas(s):
    return s.count(FLECHA) + s.count('->')


# ---------------------------------------------------------------------------------------
# Chequeos
# ---------------------------------------------------------------------------------------

def ch_secciones(r, d, capa, esq, error_esq):
    c = '2b-1'
    if not esq:
        r.no_auditable(c, 'no pude leer el esqueleto de la Tarea en %s' % tarea.MAPA,
                       error_esq or '')
        return
    claves = tarea.claves_esqueleto(esq)
    nucleos = [tarea.clave_titulo(t) for t in esq]
    exactos = [tarea.n(t) for t in esq]
    secs = d['secciones']
    asignado = {}       # indice del esqueleto -> posicion en la tarjeta
    usados = set()
    for pos, t in enumerate(secs):
        nt = tarea.n(t)
        if nt in exactos and exactos.index(nt) not in asignado:
            asignado[exactos.index(nt)] = pos
            usados.add(pos)
    extras = []
    for pos, t in enumerate(secs):
        if pos in usados:
            continue
        ct = tarea.clave_titulo(t)
        palabras = set(ct.split())
        elegido = None
        for i, (k, nuc) in enumerate(zip(claves, nucleos)):
            if i in asignado:
                continue
            ws = nuc.split()
            if (ct == nuc or ct.startswith(k)) and len(set(ws) & palabras) * 2 >= len(ws):
                elegido = i
                break
        if elegido is None:
            extras.append(t)
        else:
            asignado[elegido] = pos
            usados.add(pos)

    # Exenciones
    exentas, motivo = set(), ''
    if capa == 'front':
        exentas = {i for i, k in enumerate(claves) if k in ('contrato', 'validaciones', 'casos')}
        motivo = 'exencion de front (redactar-tarea 3.1): no define contrato propio'
    elif capa == 'ui':
        try:
            a, b = claves.index('contrato'), claves.index('modos')
            exentas = set(range(a, b + 1))
        except ValueError:
            exentas = set()
        motivo = 'Tarea de solo UI/config sin SDD: el bloque del medio se borra entero (N/A)'

    hallazgos = 0
    exentas_ausentes = []
    for i, titulo in enumerate(esq):
        if i not in asignado:
            if i in exentas:
                exentas_ausentes.append(titulo)
            else:
                r.hallazgo(c, 'falta la seccion "%s"' % titulo,
                           'se compara contra el esqueleto de %s' % tarea.MAPA)
                hallazgos += 1
        elif tarea.n(secs[asignado[i]]) != exactos[i]:
            r.hallazgo(c, 'la seccion "%s" tiene que llamarse "%s"' % (secs[asignado[i]], titulo),
                       'nombre exacto del esqueleto')
            hallazgos += 1
    maximo, max_i = -1, None
    for pos in sorted(usados):
        i = next(k for k, v in asignado.items() if v == pos)
        if i < maximo:
            r.hallazgo(c, 'orden: "%s" esta despues de "%s"' % (secs[pos], esq[max_i]),
                       'el esqueleto pone "%s" antes' % esq[i])
            hallazgos += 1
        else:
            maximo, max_i = i, i
    for t in extras:
        if texto.sin_acentos(t).strip() in SECCIONES_EXTRA_CONOCIDAS:
            r.ok(c, 'seccion extra conocida: "%s" (la agrega el pipeline)' % t)
            continue
        r.aviso(c, 'seccion que no esta en el esqueleto: "%s"' % t,
                'no es hallazgo; si sobra, se saca')
    if exentas_ausentes:
        r.ok(c, 'no tiene %s: %s' % (', '.join('"%s"' % x for x in exentas_ausentes), motivo))
    if not hallazgos:
        r.ok(c, '%d secciones del esqueleto presentes, con el nombre exacto y en orden'
             % len(asignado))


def ch_reglas(r, d, doc, indice):
    c = '2b-2/AT-4a'
    citadas = d['reglas_citadas']
    if not indice:
        r.no_auditable(c, 'no pude armar el indice de reglas del Cerebro (cerebro-digital/)',
                       '%d reglas citadas sin verificar' % len(citadas))
    else:
        faltan = [x for x in citadas if x not in indice]
        for x in faltan:
            r.no_auditable(c, 'la regla %s no existe en el Cerebro' % x,
                           'auditar-tarea chequeo 4: si la regla no esta, ese punto no se audita')
        if citadas and not faltan:
            r.ok(c, 'las %d reglas citadas existen en el Cerebro' % len(citadas),
                 ', '.join(citadas))
        if not citadas:
            r.aviso(c, 'la Tarea no cita ninguna regla [RN-...]/[DEC-...]')
    apoyo = d['material_de_apoyo']
    if apoyo is None:
        return
    en_apoyo = texto.reglas_citadas(apoyo)
    resto = texto.reglas_citadas(cuerpo_sin_seccion(doc, 'material'))
    sobran = [x for x in en_apoyo if x not in resto]
    for x in sobran:
        r.hallazgo(c, '%s se cita solo en "Material de apoyo": sobra' % x,
                   'cargar-a-azure 2b fila 2: una regla que la Tarea no usa manda al dev al lugar '
                   'equivocado')
    if en_apoyo and not sobran:
        r.ok(c, 'las reglas de "Material de apoyo" se usan en el cuerpo')


_SIN_NUMERO = [
    re.compile(r'\b(?:la|las|una|otra|otras|dos|ambas)\s+Tareas?\s+(?:de\s+)?'
               r'(?:front|frontend|back|backend|e2e)\b', re.I),
    re.compile(r'\(\s*Related\s*\)', re.I),
    re.compile(r'\bambas\s+en\s+Related\b', re.I),
]
_REF_ID = re.compile(r'(?<![\w/])#\d{5,7}\b|\[T-\d+\]')


def ch_ids(r, d, doc):
    c = '2b-3'
    plano = texto.texto_plano(doc)
    vistos = 0
    for rx in _SIN_NUMERO:
        for m in rx.finditer(plano):
            ini = plano.rfind('\n', 0, m.start()) + 1
            fin = plano.find('\n', m.end())
            fin = len(plano) if fin < 0 else fin
            ventana = plano[max(ini, m.start() - 25):min(fin, m.end() + 70)]
            if not _REF_ID.search(ventana):
                r.hallazgo(c, 'menciona otra Tarea sin su #ID: "%s"' % m.group(0),
                           corto(plano[max(ini, m.start() - 40):min(fin, m.end() + 60)]))
                vistos += 1
    if not vistos:
        r.ok(c, 'no hay menciones a otra Tarea sin su #ID')
    ids = d['ids_citados']
    if ids:
        r.ok(c, '%d #ID mencionados; sus vinculos de Azure (Parent, Related) se miran al escribir, '
                'no aca' % len(ids), ', '.join('#' + x for x in ids))
        sueltos = texto.ids_citados(texto.sin_enlaces(re.sub(r'<pre\b.*?</pre\s*>', ' ', doc,
                                                             flags=re.I | re.S)))
        if sueltos:
            r.aviso(c, '#ID escritos sin enlace en el texto', ', '.join('#' + x for x in sueltos))
    if d['marcas']:
        r.aviso(c, 'borrador de lote: %d marcas [T-nn]/[H-nn] valen como #ID; se vuelve a mirar '
                   'despues del reemplazo' % len(d['marcas']), ', '.join(d['marcas']))


def ch_numeracion(r, d, capa):
    c = '2b-4/AT-15'
    if not d['hay_tests']:
        if capa == 'ui':
            r.ok(c, 'N/A: Tarea de solo UI/config, sin lista de tests')
        else:
            r.no_auditable(c, 'no hay seccion de tests: no hay numeracion que mirar')
        return
    tests = d['tests']
    total = len(tests)
    if not total:
        if d['tests_listas_ul']:
            r.hallazgo(c, 'los tests van con vinetas (<ul>): sin numero no hay a que apuntar desde '
                          'la tabla de Escenarios')
        else:
            r.hallazgo(c, 'la seccion de tests no tiene una lista numerada (<ol>)')
        return
    if d['tests_listas_ol'] > 1:
        r.hallazgo(c, 'la lista de tests esta partida en %d <ol>: el HTML vuelve a numerar desde 1 '
                      'en cada una' % d['tests_listas_ol'])
    existentes = set(range(1, total + 1))
    fuentes = [('la tabla de Escenarios', [x for f in d['sdd_filas'] for x in f['tests']]),
               ('"Modos de falla"', d['modos_tests']),
               ('la frase "no mapean"', d['no_mapean']),
               ('la prosa de la SDD', d['sdd_prosa_tests'])]
    malos = 0
    for nombre, nums in fuentes:
        fuera = sorted(set(x for x in nums if x not in existentes))
        if fuera:
            r.hallazgo(c, '%s nombra tests que no existen: %s' % (nombre, rangos(fuera)),
                       'la lista tiene %d tests (1 a %d)' % (total, total))
            malos += 1
    if not d['hay_tabla_sdd']:
        r.no_auditable(c, 'sin la tabla de Escenarios no se puede ver que test cierra que '
                          'Escenario')
        return
    en_tabla = set(x for f in d['sdd_filas'] for x in f['tests'])
    guard = set(t['n'] for t in tests if t['es_guardarrail'])
    declarados = set(d['no_mapean'])
    prosa = set(d['sdd_prosa_tests'])
    huerfanos = sorted(existentes - en_tabla - declarados - guard - prosa)
    solo_prosa = sorted((existentes & prosa) - en_tabla - declarados - guard)
    if huerfanos:
        r.hallazgo(c, 'tests huerfanos (ni en la tabla, ni en "no mapean", ni guardarrail): %s'
                   % rangos(huerfanos), 'un test que no cierra nada')
        malos += 1
    if solo_prosa:
        r.aviso(c, 'tests mapeados solo en la prosa de la SDD, fuera de la tabla: %s'
                % rangos(solo_prosa))
    if not malos:
        r.ok(c, 'tests numerados 1 a %d; todo numero citado existe y todo test esta mapeado, '
                'declarado o es guardarrail' % total)


def ch_escenarios(r, d, capa, criterios, error_historia, ruta_historia):
    c = '2b-5/AT-5'
    if not d['hay_sdd']:
        if capa == 'ui':
            r.ok(c, 'N/A: Tarea de solo UI/config, sin tabla de Escenarios')
        else:
            r.no_auditable(c, 'no hay seccion "Especificacion cerrada (SDD)": no hay tabla que '
                              'contar')
        return
    if not d['hay_tabla_sdd']:
        r.hallazgo(c, 'la seccion SDD no tiene la tabla de Escenarios (encabezado con '
                      '"Escenario" y "Tests")')
    filas = d['sdd_filas']
    viejas = [f for f in filas if f['no_lo_cubre']]
    if viejas:
        r.aviso(c, 'forma vieja: %d filas "No lo cubre esta Tarea"; usar la linea "No cubre" al '
                   'pie (plantilla, Tamano y forma)' % len(viejas))
    for f in filas:
        if f['no_lo_cubre']:
            if not f['ids']:
                r.aviso(c, 'la fila "%s" no nombra la Tarea que lo cubre' % corto(f['titulo'], 60))
            continue
        if f['parcial'] and not f['ids']:
            r.hallazgo(c, 'la fila "%s" cubre una parte y no nombra la otra Tarea con su #ID'
                       % corto(f['titulo'], 60), corto(f['parte']))
        if not f['tests']:
            r.hallazgo(c, 'la fila "%s" no tiene tests en "Tests que lo verifican"'
                       % corto(f['titulo'], 60), 'columna: "%s"' % corto(f['tests_texto'], 40))
    for x in d['no_cubre']:
        if not x['ids']:
            r.aviso(c, '"No cubre": "%s" no nombra la Tarea que lo cubre' % corto(x['titulo'], 60))

    declarados = [f['titulo'] for f in filas] + [x['titulo'] for x in d['no_cubre']]
    if criterios is None:
        r.no_auditable(c, 'sin la Historia padre no se cuentan sus Escenarios contra la tabla',
                       error_historia or 'no se paso --historia')
        return
    esc = historia.escenarios(criterios)
    if not esc:
        r.no_auditable(c, 'la Historia padre no tiene ningun Escenario: el loop BDD no existe',
                       'no paso su propio DoR; derivar Tareas de ella es prematuro')
        return
    padres = [e['titulo'] for e in esc]
    num_hist = re.findall(r'(\d{5,7})', os.path.basename(ruta_historia or ''))
    if num_hist and d['sdd_padre'] and num_hist[0] not in d['sdd_padre']:
        r.aviso(c, 'la tabla dice Historia #%s y el archivo de --historia es de #%s'
                % (d['sdd_padre'][0], num_hist[0]), 'revisar que sea el padre correcto')
    total = len(filas) + len(d['no_cubre'])
    if total == len(padres):
        r.ok(c, 'Escenarios del padre: %d = %d filas + %d en "No cubre"'
             % (len(padres), len(filas), len(d['no_cubre'])))
    else:
        r.hallazgo(c, 'el padre tiene %d Escenarios y la Tarea declara %d (%d filas + %d en '
                      '"No cubre")' % (len(padres), total, len(filas), len(d['no_cubre'])),
                   'cargar-a-azure 2b fila 5')
    textual = [tarea.titulo_textual(p) for p in padres]
    sueltos = [tarea.n(p) for p in textual]
    usados = [False] * len(padres)
    for t in declarados:
        tt = tarea.titulo_textual(t)
        k = next((i for i, p in enumerate(textual) if p == tt and not usados[i]), None)
        if k is not None:
            usados[k] = True
            continue
        if tt in textual:
            r.hallazgo(c, 'el Escenario "%s" esta declarado dos veces' % corto(t, 70))
            continue
        k = next((i for i, p in enumerate(sueltos) if p == tarea.n(tt) and not usados[i]), None)
        if k is not None:
            usados[k] = True
            r.hallazgo(c, '"%s" difiere solo en tildes o mayusculas del Escenario "%s"'
                       % (corto(t, 60), corto(padres[k], 60)), 'el titulo va textual')
        else:
            r.hallazgo(c, '"%s" no coincide con ningun Escenario del padre' % corto(t, 70),
                       'el titulo se copia textual del Gherkin')
    for i, p in enumerate(padres):
        if not usados[i]:
            r.hallazgo(c, 'el Escenario del padre "%s" no esta ni en la tabla ni en "No cubre"'
                       % corto(p, 70))


def ch_integracion(r, d, capa):
    c = '2b-6/AT-15'
    ri = d['requiere_integracion']
    if ri is None:
        if capa != 'ui':
            r.aviso(c, 'el Alcance no declara "Requiere test de integracion: si / no"')
        return
    tests = d['tests']
    if ri:
        a = [t['n'] for t in tests if 'integracion' in tarea.n(t['texto'])]
        if not a and 'integracion' in tarea.n(d['tests_intro']):
            r.aviso(c, 'ningun test dice "integracion", pero el encabezado de la lista lo declara '
                       'para todos', corto(d['tests_intro'], 90))
            a = [t['n'] for t in tests]

        def pide_integracion(renglon):
            # Dice "integracion", o nombra por numero SOLO tests de integracion ("Escribir los
            # tests 1 a 12" cuando los 12 lo son). "Los tests 1 a 28 pasan" no alcanza.
            if 'integracion' in tarea.n(renglon):
                return True
            refs = tarea.tests_mencionados(renglon)
            return bool(refs) and set(refs) <= set(a)
        b = [s for s in d['subtareas'] if pide_integracion(s)]
        cc = [x for x in d['dod'] if pide_integracion(x)]
        faltan = []
        if not a:
            faltan.append('un test de integracion en la lista')
        if not b:
            faltan.append('una subtarea que lo escriba')
        if not cc:
            faltan.append('un item en la Definicion de terminado')
        for x in faltan:
            r.hallazgo(c, 'dice "Requiere test de integracion: si" y falta %s' % x,
                       'las tres o ninguna')
        if not faltan:
            r.ok(c, 'requiere integracion: hay test, subtarea e item de DoD')
    else:
        malos = [t['n'] for t in tests if t['etiqueta_integracion']]
        if malos:
            r.hallazgo(c, 'dice "Requiere test de integracion: no" y hay tests etiquetados '
                          '"Integracion": %s' % rangos(malos))
        else:
            r.ok(c, 'no requiere integracion y ningun test se etiqueta como tal')


_RUTA = re.compile(r'(?<![\w@/.\-])((?:https?://)?(?:[\w.\-]+/)+[\w.\-]*\.'
                   r'(?:md|html|yaml|yml|json|py))(?![\w/])')


def ch_rutas(r, doc):
    c = '2b-7'
    s = re.sub(r'<pre\b.*?</pre\s*>', ' ', texto.sin_enlaces(doc), flags=re.I | re.S)
    rutas = []
    for m in _RUTA.finditer(texto.texto_plano(s)):
        if m.group(1) not in rutas:
            rutas.append(m.group(1))
    for x in rutas:
        r.hallazgo(c, 'ruta sin enlace: "%s"' % x, 'toda ruta o documento va como <a href>')
    if not rutas:
        r.ok(c, 'no hay rutas ni documentos fuera de un <a href>')


_TAGS_PRE = re.compile(r'</?(?:a|b|i|u|em|strong|br|span|code|font|sub|sup)\b[^>]*>', re.I)


def ch_markdown(r, doc):
    c = '2b-9'
    malos = 0
    if '```' in doc:
        r.hallazgo(c, 'hay fences de markdown (```): Azure los muestra literales')
        malos += 1
    sin_pre = re.sub(r'<pre\b.*?</pre\s*>', '\n', doc, flags=re.I | re.S)
    sin_code = re.sub(r'<code\b[^>]*>.*?</code\s*>', ' ', sin_pre, flags=re.I | re.S)
    plano = texto.texto_plano(sin_code)
    if '**' in plano:
        i = plano.find('**')
        r.hallazgo(c, 'hay "**" de markdown', corto(plano[max(0, i - 40):i + 40]))
        malos += 1
    renglones = [l for l in plano.split('\n')
                 if l.startswith(('- ', '* ', '| ')) or re.match(r'#{1,6} ', l)]
    if renglones:
        r.hallazgo(c, '%d renglones que empiezan como markdown ("- ", "* ", "| ", "# ")'
                   % len(renglones), ' / '.join(corto(x, 50) for x in renglones[:3]))
        malos += 1
    links = re.findall(r'\[[^\]\n]+\]\((?:https?://|/|\.|#)[^)\s]*\)', plano)
    if links:
        r.hallazgo(c, 'enlaces de markdown [texto](url)', ' / '.join(corto(x, 60) for x in links[:3]))
        malos += 1
    tildes = re.findall(r'`[^`\n]+`', plano)
    if tildes:
        r.hallazgo(c, 'codigo entre comillas invertidas de markdown; va en <code>',
                   ' / '.join(corto(x, 40) for x in tildes[:3]))
        malos += 1
    for k, p in enumerate(tarea.pres(doc)):
        q = _TAGS_PRE.sub('', p)
        if '<' in q or '>' in q:
            i = min(x for x in (q.find('<'), q.find('>')) if x >= 0)
            r.hallazgo(c, 'dentro del <pre> %d hay "<" o ">" sin escapar (&lt; &gt;)' % (k + 1),
                       corto(q[max(0, i - 30):i + 30].replace('\n', ' ')))
            malos += 1
    if not malos:
        r.ok(c, 'sin markdown crudo ni escapes rotos')


_PHI = [
    ('un numero de 7 u 8 cifras (documento?)', re.compile(r'(?<![\w#/.\-:])\d{7,8}(?![\w/.\-])')),
    ('un email', re.compile(r'[\w.+\-]+@[\w\-]+\.[\w.]+')),
    ('un CUIT', re.compile(r'(?<![\w\-])\d{2}-\d{8}-\d(?![\w\-])')),
    ('un telefono', re.compile(r'(?<![\w\-])(?:\+?54[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-])?'
                               r'(?:15[\s\-]?)?\d{4}-\d{4}(?![\w\-])')),
]


def ch_phi(r, doc):
    c = '2b-10'
    plano = texto.texto_plano(texto.sin_enlaces(doc))
    vistos = 0
    for nombre, rx in _PHI:
        hall = []
        for m in rx.finditer(plano):
            x = m.group(0)
            if nombre == 'un telefono' and re.match(r'^(19|20)\d\d-(19|20)\d\d$', x.strip()):
                continue
            if x not in hall:
                hall.append(x)
        if hall:
            r.aviso(c, 'posible PHI: %s' % nombre, ', '.join(hall[:5]) +
                    ' -- revisar; si es un dato real, va un marcador (<documento>, <telefono>)')
            vistos += 1
    if not vistos:
        r.ok(c, 'sin numeros de documento, emails, CUIT ni telefonos a la vista (heuristica)')


def ch_guardarrail(r, d):
    c = '2b-11/AT-8'
    guard = [t for t in d['tests'] if t['es_guardarrail']]
    if not guard:
        r.ok(c, 'ningun test se declara guardarrail')
        return
    sin_frase = [t['n'] for t in guard if not t['tiene_frase_rojo']]
    if sin_frase:
        r.hallazgo(c, 'guardarrailes sin la frase "se pone en rojo si ...": %s' % rangos(sin_frase),
                   'sin la frase la etiqueta no vale: se le exige su rojo previo')
    dod = [x for x in d['dod'] if 'guardarrail' in tarea.n(x)]
    if not dod:
        r.hallazgo(c, 'hay %d guardarrailes y la Definicion de terminado no los exceptua del '
                      'rojo previo' % len(guard))
    else:
        nums = set()
        for x in dod:
            for fr in re.split(r'(?<=\.)\s+', x):
                if 'guardarrail' in tarea.n(fr):
                    nums.update(tarea.tests_mencionados(fr))
        reales = set(t['n'] for t in guard)
        if nums and nums != reales:
            r.aviso(c, 'el DoD nombra como guardarrailes %s y en la lista son %s'
                    % (rangos(nums), rangos(reales)))
    if not sin_frase and dod:
        r.ok(c, '%d guardarrailes, todos con "se pone en rojo si", y el DoD los exceptua'
             % len(guard), rangos(t['n'] for t in guard))


def ch_modos(r, d, capa):
    c = 'AT-11'
    if not d['hay_modos']:
        if capa == 'ui':
            r.ok(c, 'N/A: Tarea de solo UI/config')
        else:
            r.hallazgo(c, 'falta la seccion "Modos de falla evaluados"',
                       'su ausencia no se distingue de "no habia nada que declarar"')
        return
    faltan = [f for f in tarea.FAMILIAS if f not in d['modos_falla']]
    vacias = [f for f in tarea.FAMILIAS
              if f in d['modos_falla'] and len(d['modos_falla'][f].strip(' .')) < 3]
    for f in faltan:
        r.hallazgo(c, 'falta la familia "%s" en Modos de falla' % f,
                   'cada familia: cubierta por un test o descartada con su motivo')
    for f in vacias:
        r.hallazgo(c, 'la familia "%s" esta vacia' % f)
    if not faltan and not vacias:
        r.ok(c, 'las seis familias de Modos de falla estan escritas')


def ch_tests_compuestos(r, d):
    """AT-6b: un item de 'Tests a escribir PRIMERO' con dos o mas comportamientos ('a -> x; b -> y') obliga al worker a un
    test con varias condiciones o a partir el item; se avisa para que lo decida quien redacta."""
    c = 'AT-6b'
    compuestos = []
    for t in d.get('tests') or []:
        txt = t.get('texto') or t.get('cabeza') or t.get('txt') or ''
        if isinstance(txt, str) and (txt.count('->') > 1 or ';' in txt):
            compuestos.append(str(t.get('n') or t.get('numero') or '?'))
    if compuestos:
        r.aviso(c, 'items con dos o mas comportamientos (mas de un "->" o un ";"): %s' % ', '.join(compuestos),
                'un item = un comportamiento; si son dos aserciones del mismo contrato, decirlo en el item')
    else:
        r.ok(c, 'cada item de la lista enumera un solo comportamiento')


def ch_datos_a_confirmar(r, d):
    c = 'AT-14'
    if not d['hay_datos_a_confirmar']:
        r.hallazgo(c, 'falta la seccion "Datos a confirmar"',
                   'obligatoria: sin pendientes se escribe "Ninguno."')
        return
    dac = d['datos_a_confirmar']
    if not dac:
        r.hallazgo(c, '"Datos a confirmar" esta vacia', 'sin pendientes se escribe "Ninguno."')
        return
    if dac == ['Ninguno.']:
        r.ok(c, '"Datos a confirmar" declara "Ninguno."')
        return
    total = len(d['tests'])
    por_n = {t['n']: t for t in d['tests']}
    malos = 0
    for item in dac:
        refs = tarea.tests_mencionados(item)
        no_existen = [x for x in refs if x not in por_n]
        sin_marca = [x for x in refs if x in por_n and not por_n[x]['tiene_warn']]
        if no_existen:
            r.hallazgo(c, 'un pendiente nombra tests que no existen: %s' % rangos(no_existen),
                       'la lista tiene %d tests; pendiente: %s' % (total, corto(item, 80)))
            malos += 1
        if sin_marca:
            r.hallazgo(c, 'tests que dependen de un pendiente y no traen la marca %s: %s'
                       % (WARN, rangos(sin_marca)), 'pendiente: %s' % corto(item, 90))
            malos += 1
    if not malos:
        r.ok(c, '%d pendientes declarados; los tests que nombran traen la marca %s'
             % (len(dac), WARN))


def ch_contrato(r, d, capa):
    """AT-3 (codigos del contrato y valores de enum) y AT-2 (filas de Casos de error)."""
    if capa in ('front', 'ui'):
        r.ok('AT-3', 'N/A: Tarea de %s, no define contrato propio' % capa)
        r.ok('AT-2', 'N/A: Tarea de %s, sin tabla "Casos de error" propia' % capa)
        return
    textos = [t['texto'] for t in d['tests']]
    # AT-3
    c = 'AT-3'
    if not d['hay_contrato']:
        r.no_auditable(c, 'falta el Contrato tecnico: no hay codigos ni catalogos que contar')
    elif d['contrato'] is None:
        r.aviso(c, 'el Contrato tecnico no trae un <pre> (fragmento OpenAPI): no hay codigos que '
                   'contar mecanicamente')
    else:
        malos = 0
        if not d['codigos_contrato']:
            r.aviso(c, 'el contrato no declara codigos de respuesta (responses)')
        sin = [x for x in d['codigos_contrato'] if not palabra_en(x, textos)]
        if sin:
            r.hallazgo(c, 'codigos del contrato sin test: %s' % ', '.join(sin),
                       'un codigo declarado y no probado es una promesa que nadie verifica')
            malos += 1
        heredados, faltan, sueltos = [], [], []
        for e in d['enums_detalle']:
            como = palabra_en(e['valor'], textos)
            if como == 'suelto':
                sueltos.append(e['valor'])
            elif not como:
                if re.search(r'#\d{5,7}|\[T-\d+\]', e['comentario']):
                    heredados.append(e['valor'])
                else:
                    faltan.append(e['valor'])
        if faltan:
            r.hallazgo(c, 'valores de enum que ningun test nombra: %s' % ', '.join(faltan),
                       'ejercitar dos de tres no prueba que el tercero este aceptado')
            malos += 1
        if heredados:
            r.aviso(c, 'valores de enum sin test que el contrato marca como de otra Tarea: %s'
                    % ', '.join(heredados))
        if sueltos:
            r.aviso(c, 'valores de enum que aparecen solo como texto, no literales: %s'
                    % ', '.join(sueltos))
        if not malos:
            r.ok(c, '%d codigos y %d valores de enum del contrato aparecen en los tests'
                 % (len(d['codigos_contrato']), len(d['enums'])))
    # AT-2
    c = 'AT-2'
    if not d['hay_casos_error']:
        r.no_auditable(c, 'falta "Casos de error": no hay filas que cruzar con los tests')
        return
    filas = d['casos_error']
    if not filas:
        r.hallazgo(c, '"Casos de error" no tiene tabla con filas')
        return
    malos = 0
    for k, f in enumerate(filas, 1):
        nombre = 'fila %d ("%s")' % (k, corto(f['condicion'], 50))
        ht = f['codigos_http']
        er = f['codigos_error']
        if tarea.n(f['codigo']).startswith('no es error'):
            continue
        if not ht and not er and not f['excepcion']:
            r.aviso(c, '%s sin codigo HTTP ni codigo de error reconocible' % nombre,
                    corto(f['codigo'] + ' | ' + f['payload'], 80))
            continue
        faltan = [x for x in ht + er if not palabra_en(x, textos)]
        if not ht and not er:
            faltan += [x for x in f['excepcion'] if not palabra_en(x, textos)]
        if faltan:
            r.hallazgo(c, '%s: ningun test tiene %s' % (nombre, ', '.join(faltan)),
                       'cada fila de Casos de error tiene su test')
            malos += 1
            continue
        if ht and er:
            juntos = any(all(palabra_en(x, [t]) for x in ht[:1] + er[:1]) for t in textos)
            if not juntos:
                r.aviso(c, '%s: el codigo %s y %s estan en tests distintos, ninguno los tiene '
                           'juntos' % (nombre, ht[0], er[0]))
    if not malos:
        r.ok(c, 'las %d filas de Casos de error tienen sus codigos en algun test' % len(filas))


def ch_validaciones(r, d):
    c = 'AT-1'
    if not d['validaciones']:
        return
    textos = [t['texto'] for t in d['tests']]
    sin = []
    for campo in d['validaciones_campos']:
        if campo and not palabra_en(campo, textos) and campo not in sin:
            sin.append(campo)
    for campo in sin:
        r.aviso(c, 'la validacion de "%s" no aparece nombrada en ningun test' % corto(campo, 50),
                'heuristica: confirmar a mano (una regla por test)')
    if not sin:
        r.ok(c, 'cada campo de Validaciones aparece en algun test (heuristica)')


# " y cuando" / " y si" en la entrada: una segunda condicion. " y sin" / " y con" no entran: en
# las Tareas reales casi siempre son datos de la MISMA condicion ("sin nombre, sin localidad y
# sin provincia").
_Y_CONDICION = re.compile(r'\sy\s+(?:cuando|si)\b', re.I)
# Dos "entrada -> resultado" separados por ';' o por un punto: dos casos en un item. Una cadena
# "A -> B -> C" (un camino) no cuenta.
_DOS_CASOS = re.compile('(?:' + FLECHA + '|->)[^;' + FLECHA + r']*(?:;|\.\s)[^' + FLECHA +
                        ']*(?:' + FLECHA + '|->)')


def ch_conjunciones(r, d):
    c = 'AT-7'
    vistos = []
    for t in d['tests']:
        if t['es_esquema'] and t['filas']:
            continue
        s = _sin_comillas_ni_codigo(t['html'])
        # La frase del guardarrail describe la regresion, no las condiciones del test.
        s = re.split(r'se\s+pone\s+en\s+rojo\s+si', s, flags=re.I)[0]
        motivo = None
        if re.search(r'\so\s', ' ' + s + ' '):
            motivo = '" o "'
        elif not t['es_esquema'] and _DOS_CASOS.search(s):
            motivo = 'dos pares entrada -> resultado'
        else:
            entrada = re.split(FLECHA + '|->', s)[0]
            if _Y_CONDICION.search(entrada):
                motivo = '" y " entre dos condiciones'
        if motivo:
            vistos.append(t['n'])
            r.aviso(c, 'test %d: %s; puede ser dos casos en un item' % (t['n'], motivo),
                    corto(t['cabeza'], 100))
    if not vistos and d['tests']:
        r.ok(c, 'ningun test une dos condiciones con " o " / " y " (heuristica)')


def ch_esquemas(r, d):
    c = 'ESQ'
    esq = [t for t in d['tests'] if t['es_esquema']]
    if not esq:
        return
    malos, viejos = 0, []
    for t in esq:
        if t['filas_ol']:
            r.hallazgo(c, 'test %d: las filas del Esquema van en <ol>; van en <ul> (con <ol> se '
                          'rompe la numeracion)' % t['n'])
            malos += 1
            continue
        if t['filas']:
            if len(t['filas']) < 2:
                r.hallazgo(c, 'test %d: el Esquema tiene %d fila; necesita 2 o mas'
                           % (t['n'], len(t['filas'])))
                malos += 1
            sin = [k for k, f in enumerate(t['filas'], 1) if not flechas(f)]
            if sin:
                r.hallazgo(c, 'test %d: filas del Esquema sin flecha entrada -> resultado: %s'
                           % (t['n'], rangos(sin)), 'una fila sin resultado no es verificable')
                malos += 1
        else:
            viejos.append(t['n'])
            if not flechas(t['cabeza']):
                r.hallazgo(c, 'test %d: Esquema sin filas y sin ninguna flecha entrada -> '
                              'resultado' % t['n'], corto(t['cabeza'], 90))
                malos += 1
    if viejos:
        r.aviso(c, 'formato viejo: Esquemas con las filas en el renglon (%s); van en un <ul> '
                   'anidado, una fila por caso' % rangos(viejos))
    if not malos:
        r.ok(c, '%d Esquemas con sus filas y su flecha' % len(esq), rangos(t['n'] for t in esq))


def ch_invariante(r, d, capa):
    if capa != 'back' or not d['tests']:
        return
    if not any(t['es_invariante'] for t in d['tests']):
        r.aviso('AT-9', 'ningun test se etiqueta "Invariante": confirmar que haya una invariante '
                        'de negocio protegida')
    else:
        r.ok('AT-9', 'hay al menos un test etiquetado "Invariante"')


def ch_tamano(r, d):
    total = len(d['tests'])
    if total > 30:
        r.aviso('TAM', '%d tests: conviene partir la Tarea (plantilla: Tamano y forma)' % total,
                'no cambia el veredicto; se parte, no se recorta la lista')
    else:
        r.ok('TAM', '%d tests (30 o menos)' % total)
    r.para_el_auditor.append('2b-8: Esfuerzo original, Actividad, el tag y el Parent son campos '
                             'de Azure, no de la Descripcion: se miran en la tarjeta')


# ---------------------------------------------------------------------------------------
# Armado
# ---------------------------------------------------------------------------------------

def auditar(doc, ruta='', criterios=None, error_historia=None, ruta_historia=None,
            indice=None, esqueleto=None, error_esqueleto=None):
    """Corre todos los chequeos sobre el html de la Tarea. Devuelve el Reporte."""
    r = rep.Reporte(HERRAMIENTA, ruta or '<tarea>')
    if doc is None or not doc.strip():
        r.falta_insumo('la Tarea vino vacia')
        return r
    if not re.search(r'<h3\b', doc, re.I):
        r.falta_insumo('la Tarea no tiene ninguna seccion <h3>: no parece la Descripcion de una '
                       'Tarea')
        return r
    largo = len(doc)
    doc = tarea.celdas_separadas(doc)
    d = tarea.parsear(doc, ruta)
    capa = d['capa']
    ch_secciones(r, d, capa, esqueleto, error_esqueleto)
    ch_reglas(r, d, doc, indice)
    ch_ids(r, d, doc)
    ch_numeracion(r, d, capa)
    ch_escenarios(r, d, capa, criterios, error_historia, ruta_historia)
    ch_integracion(r, d, capa)
    ch_rutas(r, doc)
    ch_markdown(r, doc)
    ch_phi(r, doc)
    ch_guardarrail(r, d)
    ch_modos(r, d, capa)
    ch_tests_compuestos(r, d)
    ch_datos_a_confirmar(r, d)
    ch_contrato(r, d, capa)
    ch_validaciones(r, d)
    ch_conjunciones(r, d)
    ch_esquemas(r, d)
    ch_invariante(r, d, capa)
    ch_tamano(r, d)
    if d['capa'] == 'desconocida':
        r.aviso('capa', 'no pude deducir la capa del "Alcance tecnico" (api/application/domain/'
                        'infra o front/componente): no se aplica la exencion de front; declarala con el '
                        'prefijo "Front:" o "Back:" en el titulo, o nombrando el repo en "Componente / repo"')
    esc = historia.escenarios(criterios) if criterios else None
    r.datos.update({
        'capa': capa,
        'tests': len(d['tests']),
        'escenarios_padre': len(esc) if esc is not None else None,
        'filas_sdd': len(d['sdd_filas']),
        'no_cubre': len(d['no_cubre']),
        'guardarrailes': sum(1 for t in d['tests'] if t['es_guardarrail']),
        'esquemas': sum(1 for t in d['tests'] if t['es_esquema']),
        'largo_caracteres': largo,
    })
    r.para_el_auditor = list(PARA_EL_AUDITOR) + r.para_el_auditor
    return r


def main(argv=None):
    p = argparse.ArgumentParser(
        prog='auditar-tarea.py',
        description='Auditoria mecanica de una Tarea. 0 = sin hallazgos, 1 = hallazgos o no '
                    'auditables, 2 = SIN DATOS.')
    p.add_argument('tarea', help='html de la Descripcion de la Tarea')
    p.add_argument('--historia', help='html de los Criterios de aceptacion de la Historia padre')
    p.add_argument('--json', action='store_true', help='salida en JSON')
    p.add_argument('--salida', help='ademas, guarda el reporte en este archivo')
    a = p.parse_args(argv)
    try:
        r = rep.Reporte(HERRAMIENTA, a.tarea)
        try:
            doc = texto.leer(a.tarea)
        except (OSError, UnicodeDecodeError) as e:
            r.falta_insumo('no se pudo leer la Tarea (%s: %s)' % (type(e).__name__, e))
            return rep.emitir(r, a.json, a.salida)
        criterios, error_historia = None, None
        if a.historia:
            try:
                criterios = texto.leer(a.historia)
                if not criterios.strip():
                    criterios, error_historia = None, 'el archivo de --historia vino vacio'
            except (OSError, UnicodeDecodeError) as e:
                error_historia = 'no se pudo leer --historia (%s: %s)' % (type(e).__name__, e)
        esq, error_esq = None, None
        try:
            esq = tarea.esqueleto()
        except (OSError, UnicodeDecodeError, ValueError) as e:
            error_esq = '%s: %s' % (type(e).__name__, e)
        try:
            indice = cerebro.indice_reglas()
        except OSError:
            indice = {}
        r = auditar(doc, a.tarea, criterios, error_historia, a.historia, indice, esq, error_esq)
        return rep.emitir(r, a.json, a.salida)
    except Exception as e:  # nunca 0 ni 1 por un error que no se esperaba
        sys.stderr.write('SIN DATOS -- error inesperado en auditar-tarea (%s: %s)\n'
                         % (type(e).__name__, e))
        return rep.SIN_DATOS


if __name__ == '__main__':
    sys.exit(main())
