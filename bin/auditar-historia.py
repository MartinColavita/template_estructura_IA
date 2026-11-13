#!/usr/bin/env python3
"""Auditoria MECANICA de una Historia de usuario: lo que de auditar-historia es CONTEO.

    python bin/auditar-historia.py --criterios <criterios.html> [--descripcion <descripcion.html>]
                                   [--ficha <ruta.md>] [--flujo F-nn] [--json] [--salida <archivo>]

Tres estados, nunca dos:  0 = SIN HALLAZGOS   1 = CON HALLAZGOS (o algo NO AUDITABLE)
                          2 = SIN DATOS (no se pudo leer --criterios, o el pedido vino mal armado)

POR QUE EXISTE. La skill auditar-historia tiene 20 chequeos. La mitad son conteo: que haya
Escenarios, que cada uno tenga su Cuando y su Entonces, la lista negra de palabras vagas, que
cada Escenario cite una regla y que la regla exista, titulos repetidos, Esquemas sin Ejemplos,
las reglas de la Historia contra las del [F-nn] de la ficha, el Documento fuente, los puntos
abiertos citados y el formato del HTML. Un modelo leyendo la tarjeta entera cuenta distinto
cada vez, tarda y gasta tokens; un script cuenta igual siempre. Al auditor (el modelo) le
queda SOLO lo que pide criterio, y el reporte lo lista al final ("Lo que este script NO mira").
Lo que este script marca HALLAZGO, el modelo no lo da por bueno.

REGLA DEL CERO. 0 Escenarios no es "todo cumple": es NO AUDITABLE, y la Historia no deriva
Tareas. Un bloque ausente (Casos de uso) tampoco pasa: NO AUDITABLE, y se dice cual falta.
La falta de FICHA, en cambio, no bloquea (skill, "Veredictos"): sin --ficha ni --flujo los
chequeos 13 a 18 salen como AVISO "sin ficha: no se miraron". Si se pidio la ficha (vino
--ficha o --flujo) y no se pudo cruzar, eso si es NO AUDITABLE.

NUMERACION. Cada renglon lleva "AH-n" con el numero del chequeo de la skill (AH-4 = palabras
vagas, AH-10 = reglas citadas, AH-13 = reglas contra el [F-nn], AH-19 = puntos abiertos...).
"AH-formato" es el esqueleto HTML de mapa-campos-azure, que no es un chequeo numerado.

SOLO LECTURA: no toca Azure, ni GitLab, ni el Cerebro, ni la red. Escribe, como mucho, el
reporte en el archivo que diga --salida. Solo biblioteca estandar; ASCII puro en este archivo
(los acentos se comparan con auditoria.texto.sin_acentos).
"""

import argparse
import html
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auditoria import cerebro, historia, phi, reporte, texto  # noqa: E402

HERRAMIENTA = 'auditar-historia'

# Chequeo 4: la lista negra de la skill, mas sus variantes de uso frecuente. Se comparan sin
# acentos y como palabra entera ("incorrecto" no cae por "correcto").
VAGAS = ('correctamente', 'adecuadamente', 'exitosamente', 'debidamente', 'apropiadamente',
         'satisfactoriamente', 'sin problemas', 'sin errores', 'segun corresponda',
         'como corresponde', 'como corresponda', 'de forma apropiada', 'de forma adecuada',
         'de forma correcta', 'de manera adecuada', 'de manera correcta', 'de manera apropiada',
         'correcto', 'correcta', 'correctos', 'correctas', 'adecuado', 'adecuada', 'adecuados',
         'adecuadas', 'apropiado', 'apropiada')
_VAGA = re.compile(r'\b(' + '|'.join(re.escape(v) for v in sorted(VAGAS, key=len, reverse=True))
                   + r')\b')

# Chequeo 5, tercera senal: un Entonces que describe un efecto INTERNO seguido de un Y.
_INTERNO = re.compile(r'\b(consulta|consultan|invoca|invocan|llama a|llama al|registra en|'
                      r'persiste|persisten)\b')

# Chequeo 7: la lista negra ampliada de UI. No da hallazgo: cuenta, para el auditor.
_UI = re.compile(r'\b(boton|botones|combo|grilla|pestana|modal|columna|checkbox|tarjeta|ficha|'
                 r'pantalla|alerta|campo|leyenda|mensaje|popup|menu)\b')

# Chequeo 9: palabras clave en ingles al principio del renglon.
_INGLES = re.compile(r'^(Feature|Background|Scenario Outline|Scenario|Examples)\s*:|'
                     r'^(Given|When|Then|And|But)\s')

# Chequeo 19: marcas de punto abierto dentro del texto de un Escenario.
_MARCAS_ABIERTAS = re.compile(r'\b(a definir|a confirmar|en discusion|falta definir|por definir|'
                              r'sin definir)\b')   # \b: "presiona Confirmar" no es "a confirmar"
_ALERTA = chr(0x26a0)

_COMILLAS = re.compile('"[^"]*"|' + chr(0x201c) + '[^' + chr(0x201d) + ']*' + chr(0x201d))
_P = re.compile(r'<p\b[^>]*>(.*?)</p\s*>', re.I | re.S)
_TABLA = re.compile(r'<table\b[^>]*>.*?</table\s*>', re.I | re.S)
_CORTE = re.compile(r'<\s*(?:br|/p|/li|/tr|/h[1-6]|/div|hr|/pre)\b[^>]*>', re.I)
_APERTURA = re.compile(r'^(?:\s|<(?:p|div|span|li|ul|ol|font)\b[^>]*>)*', re.I)
_FLUJO = re.compile(r'^\s*[Ff]?\s*-?\s*(\d+)\s*$')

_NOMBRE_BLOQUE = {'casos_uso': 'Casos de uso', 'datos_estados': 'Datos y estados',
                  'reglas': 'Reglas de negocio', 'documento_fuente': 'Documento fuente',
                  'fuera_de_alcance': 'Fuera de alcance', 'dependencias': 'Dependencias',
                  'diseno': 'Diseno', 'funcionalidad': 'Funcionalidad', 'contexto': 'Contexto',
                  'alcance': 'Alcance'}


# ------------------------------------------------------------------------------------------
# Insumos del Cerebro
# ------------------------------------------------------------------------------------------

def leer_pendientes(raiz):
    """({P-nnn: ruta} abiertos, {P-nnn} resueltos, [rutas leidas]) de todos los pendientes.md.

    Abierto = fila de la tabla bajo un '## ...Abiertas'. Resuelto = item bajo '## Resueltas'
    o fila tachada (~~). Si aparece en las dos, gana resuelto.
    """
    base = os.path.join(raiz, 'cerebro-digital')
    abiertos, resueltos, leidos = {}, set(), []
    for d, subdirs, archivos in os.walk(base):
        rel = os.path.relpath(d, base).replace(os.sep, '/')
        if rel == 'configuracion-ia' or rel.startswith('configuracion-ia/'):
            subdirs[:] = []
            continue
        subdirs.sort()
        for a in sorted(archivos):
            if a.lower() != 'pendientes.md':
                continue
            ruta = os.path.join(d, a)
            try:
                s = texto.leer(ruta)
            except (OSError, UnicodeDecodeError):
                continue
            relruta = os.path.relpath(ruta, raiz).replace(os.sep, '/')
            leidos.append(relruta)
            seccion = None
            for linea in s.replace('\r\n', '\n').split('\n'):
                if linea.startswith('## '):
                    t = texto.sin_acentos(linea)
                    seccion = 'a' if 'abierta' in t else ('r' if 'resuelta' in t else None)
                    continue
                if seccion == 'a':
                    m = re.match(r'^\s*\|\s*(~~)?\s*(P-\d{3})\b', linea)
                    if m:
                        if m.group(1):
                            resueltos.add(m.group(2))
                        else:
                            abiertos.setdefault(m.group(2), relruta)
                elif seccion == 'r':
                    m = re.match(r'^\s*[-*]\s*(?:~~)?\s*\**\s*(P-\d{3})\b', linea)
                    if m:
                        resueltos.add(m.group(1))
    for c in resueltos:
        abiertos.pop(c, None)
    return abiertos, resueltos, leidos


def resolver_ruta(ruta, raiz):
    """(ruta_absoluta | None, motivo). Acepta ruta del repo, con o sin '#ancla', o un link de
    GitLab ('/-/blob/<rama>/<ruta>'). Se prueba contra la raiz y contra cerebro-digital/."""
    r = (ruta or '').strip().replace(chr(92), '/')
    if r.lower().startswith(('http://', 'https://')):
        m = re.search(r'/-/(?:blob|raw)/[^/]+/([^?#]+)', r) or re.search(r'[?&]path=([^&#]+)', r)
        if not m:
            return None, 'es un link externo: no se pudo verificar contra el repo'
        r = urllib.parse.unquote(m.group(1))
    r = r.split('#')[0].split('?')[0].strip()
    if not r:
        return None, 'ruta vacia'
    for base in (raiz, os.path.join(raiz, 'cerebro-digital')):
        p = os.path.normpath(os.path.join(base, r.lstrip('/')))
        if os.path.isfile(p):
            return p, ''
    return None, 'no existe en el repo'


def _es_ficha(ruta_abs):
    """True si es un .md del Cerebro con el bloque '## Derivacion a backlog'."""
    if not ruta_abs or not ruta_abs.lower().endswith('.md'):
        return False
    try:
        return cerebro.leer_ficha(ruta_abs)['derivacion'] is not None
    except (OSError, UnicodeDecodeError):
        return False


def _mismo_archivo(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


# ------------------------------------------------------------------------------------------
# Ayudas de texto
# ------------------------------------------------------------------------------------------

def _nombre(i, esc):
    t = esc['titulo'] or '(sin titulo)'
    return 'Escenario %d "%s"' % (i, t if len(t) <= 80 else t[:77] + '...')


def _texto_escenario(esc):
    return ' '.join([esc['titulo']] + [t for _, t in esc['pasos']] + esc['ejemplos'])


def _clave_titulo(t):
    return re.sub(r'\s+', ' ', texto.sin_acentos(t)).strip()


def _lista(xs, n=8):
    xs = list(xs)
    return ', '.join(xs[:n]) + (' (y %d mas)' % (len(xs) - n) if len(xs) > n else '')


# ------------------------------------------------------------------------------------------
# Chequeos
# ------------------------------------------------------------------------------------------

def _chequear_gherkin(rep, crit, escs, indice):
    """Bloque A: chequeos 2 a 6, 9 y 10 sobre los Escenarios."""
    n = len(escs)
    esquemas = sum(1 for e in escs if e['tipo'] != 'Escenario')

    # 9 -- se mira aun con 0 Escenarios: suele ser justo el motivo de que no se encuentre ninguno.
    ingles = [r.strip() for r in historia.renglones(crit) if _INGLES.match(r.strip())]
    if ingles:
        rep.hallazgo('AH-9', '%d renglones con palabras clave en ingles (va Escenario/Dado/Cuando/'
                     'Entonces/Y/Pero)' % len(ingles), _lista('"%s"' % x[:40] for x in ingles[:3]))
    elif n:
        rep.ok('AH-9', 'sin palabras clave en ingles')

    # 2 -- Regla del cero
    if not n:
        rep.no_auditable('AH-2', 'Regla del cero: 0 Escenarios en los Criterios de aceptacion. '
                         'Ningun chequeo del Gherkin puede pasar y la Historia NO deriva Tareas',
                         '%d renglones leidos' % len([r for r in historia.renglones(crit) if r]))
        return
    rep.ok('AH-2', '%d Escenarios (%d Esquemas del escenario)' % (n, esquemas))

    vistos, problemas_titulo = {}, False
    for i, e in enumerate(escs, 1):
        t = e['titulo'].strip()
        if not t:
            rep.aviso('AH-2', '%s: el Escenario no tiene titulo; la Tarea lo mapea por titulo '
                      'textual' % _nombre(i, e))
            problemas_titulo = True
        elif t.endswith('.'):
            rep.aviso('AH-2', '%s: el titulo termina en punto' % _nombre(i, e))
            problemas_titulo = True
        if t:
            vistos.setdefault(_clave_titulo(t), []).append(i)
    for k, idx in vistos.items():
        if len(idx) > 1:
            rep.hallazgo('AH-2', 'titulo de Escenario repetido: la tabla de la Tarea mapea por '
                         'titulo textual y no puede distinguirlos',
                         '"%s" en los Escenarios %s' % (escs[idx[0] - 1]['titulo'],
                                                         ', '.join(map(str, idx))))
            problemas_titulo = True
    if not problemas_titulo:
        rep.ok('AH-2', 'titulos de Escenario sin repetir')

    for i, e in enumerate(escs, 1):
        if e['tipo'] != 'Escenario' and not e['ejemplos']:
            rep.hallazgo('AH-2', '%s: Esquema del escenario sin filas de Ejemplos (sin "Ejemplos:" '
                         'o solo con el encabezado): no se puede correr' % _nombre(i, e),
                         ('encabezado: ' + e['encabezado_ejemplos']) if e['encabezado_ejemplos']
                         else '')
        elif e['tipo'] == 'Escenario' and e['ejemplos']:
            rep.aviso('AH-2', '%s: trae Ejemplos pero es "Escenario": con tabla va "Esquema del '
                      'escenario"' % _nombre(i, e))

    # 3 y 6 (presencia) -- cada Escenario con su Cuando y su Entonces
    sin_entonces = [i for i, e in enumerate(escs, 1) if not any(c == 'entonces' for c, _ in e['pasos'])]
    sin_cuando = [i for i, e in enumerate(escs, 1) if not any(c == 'cuando' for c, _ in e['pasos'])]
    for i in sin_entonces:
        rep.hallazgo('AH-3', '%s: no tiene Entonces; no hay resultado que verificar'
                     % _nombre(i, escs[i - 1]))
    if not sin_entonces:
        rep.ok('AH-3', 'los %d Escenarios tienen Entonces (que sea observable lo mira el auditor)' % n)
    for i in sin_cuando:
        rep.hallazgo('AH-6', '%s: no tiene Cuando; los Antecedentes ponen el Dado, pero la accion '
                     'va en el Escenario' % _nombre(i, escs[i - 1]))

    # 4, 5 y 6 (senales) -- paso por paso
    vagos = cinco = seis = 0
    for i, e in enumerate(escs, 1):
        pasos = historia.pasos_por_tipo(e['pasos'])
        entonces = [(c, t) for tipo, c, t in pasos if tipo == 'entonces']
        for c, t in entonces:
            m = _VAGA.search(texto.sin_acentos(t))
            if m:
                vagos += 1
                rep.hallazgo('AH-4', '%s: vocabulario vacio "%s" en el %s: no se puede convertir '
                             'en test' % (_nombre(i, e), m.group(1), c.capitalize()), t[:120])
        cuandos = [t for c, t in e['pasos'] if c == 'cuando']
        if len(cuandos) > 1:
            cinco += 1
            rep.aviso('AH-5', '%s: tiene %d Cuando; puede ser mas de un comportamiento'
                      % (_nombre(i, e), len(cuandos)))
        for c, t in entonces:
            s = texto.sin_acentos(_COMILLAS.sub(' ', t))
            if ' o ' in ' %s ' % s or ' y tambien ' in ' %s ' % s:
                cinco += 1
                rep.aviso('AH-5', '%s: "o" / "y tambien" dentro del %s: puede ser mas de un '
                          'resultado' % (_nombre(i, e), c.capitalize()), t[:120])
        if len(entonces) > 1 and _INTERNO.search(texto.sin_acentos(entonces[0][1])):
            cinco += 1
            rep.aviso('AH-5', '%s: el Entonces describe un efecto interno y sigue un Y: dos '
                      'comportamientos, y el primero no se ve desde afuera' % _nombre(i, e),
                      entonces[0][1][:120])
        for t in cuandos:
            s = texto.sin_acentos(t).strip()
            if s.startswith('se ') or re.match(r'^(el|la) sistema\b', s) or \
                    re.match(r'^es \w+(ado|ada|ido|ida)s?\b', s):
                seis += 1
                rep.aviso('AH-6', '%s: el Cuando esconde quien actua ("se ...", "el sistema", '
                          'voz pasiva)' % _nombre(i, e), t[:120])
    if not vagos:
        rep.ok('AH-4', 'ningun Entonces usa la lista negra de palabras vagas')
    if not cinco:
        rep.ok('AH-5', 'sin senales contables de mas de un comportamiento')
    if not sin_cuando and not seis:
        rep.ok('AH-6', 'los %d Escenarios tienen Cuando, sin "se ..." ni "el sistema"' % n)

    # 10 -- cada Escenario con su regla, y la regla existe
    sin_regla, solo_en_pasos, citas = [], [], {}
    for i, e in enumerate(escs, 1):
        rs = historia.reglas_del_escenario(e)
        if not rs:
            sin_regla.append(i)
        elif not e['reglas']:
            solo_en_pasos.append(i)
        for c in rs:
            citas.setdefault(c, []).append(i)
    for i in sin_regla:
        rep.hallazgo('AH-10', '%s: no cita ninguna [RN-...] ni [DEC-...]' % _nombre(i, escs[i - 1]))
    for i in solo_en_pasos:
        rep.aviso('AH-formato', '%s: la regla esta en un paso y no al final del renglon del '
                  'Escenario' % _nombre(i, escs[i - 1]))
    inexistentes = [c for c in citas if c not in indice]
    for c in inexistentes:
        rep.no_auditable('AH-10', 'la regla %s no existe en el Cerebro: no se deduce cual "deberia" '
                         'ser, se pregunta' % c, 'citada en los Escenarios %s'
                         % ', '.join(map(str, citas[c])))
    if not sin_regla and not inexistentes:
        rep.ok('AH-10', 'los %d Escenarios citan regla y las %d reglas citadas existen en el '
               'Cerebro (que digan lo que se les atribuye lo mira el auditor)' % (n, len(citas)))


def _chequear_formato(rep, crit, escs):
    """El esqueleto HTML de mapa-campos-azure: palabras clave en <b>, un <p> por Escenario."""
    if not (crit or '').strip():
        return
    if not re.search(r'<\s*(p|br|b|strong|div|li)\b', crit, re.I):
        rep.aviso('AH-formato', 'el Gherkin viene en texto plano: en Azure va en HTML, un <p> por '
                  'Escenario y las palabras clave en <b>')
        return
    sin_negrita = []
    for seg in _CORTE.split(_TABLA.sub('<br>', crit)):
        plano = texto.texto_plano(seg).strip()
        if not plano:
            continue
        c, _ = historia.clave(plano.split('\n')[0])
        if not c:
            continue
        crudo = _APERTURA.sub('', html.unescape(seg))
        if not re.match(r'<(b|strong)\b', crudo, re.I):
            sin_negrita.append(plano.split('\n')[0][:40])
    if sin_negrita:
        rep.aviso('AH-formato', '%d palabras clave sin negrita (van todas en <b>, no solo '
                  'Escenario:)' % len(sin_negrita), _lista('"%s"' % x for x in sin_negrita[:3]))
    if not escs:
        return
    parrafos = _P.findall(crit)
    if not parrafos:
        rep.aviso('AH-formato', 'el Gherkin no usa <p>: va un <p> por Escenario')
        return
    varios = dentro = no_primero = 0
    for p in parrafos:
        claves = [historia.clave(r)[0] for r in historia.renglones(p) if r.strip()]
        k = sum(1 for c in claves if c in ('escenario', 'esquema del escenario'))
        dentro += k
        if k > 1:
            varios += 1
        if k and claves[0] not in ('escenario', 'esquema del escenario'):
            no_primero += 1
    if varios:
        rep.aviso('AH-formato', '%d parrafos <p> con mas de un Escenario: va un <p> por Escenario'
                  % varios)
    if dentro < len(escs):
        rep.aviso('AH-formato', '%d Escenarios fuera de un <p>' % (len(escs) - dentro))
    if no_primero:
        rep.aviso('AH-formato', '%d parrafos <p> donde el Escenario no es el primer renglon (algo '
                  'quedo pegado arriba)' % no_primero)
    if not (sin_negrita or varios or dentro < len(escs) or no_primero):
        rep.ok('AH-formato', 'palabras clave en <b> y un <p> por Escenario')


def _chequear_descripcion(rep, desc, escs, indice, raiz, ficha_arg):
    """Chequeos 1, 10 (lado Descripcion), 11 y 12. Devuelve la ruta de la ficha declarada."""
    reglas_esc = set(c for e in escs for c in historia.reglas_del_escenario(e))
    bloques = historia.bloques_descripcion(desc)
    ficha_declarada = None

    # 1 -- Documento fuente
    rutas = historia.documento_fuente(desc)
    if rutas is None:
        rep.hallazgo('AH-1', 'la Descripcion no tiene el bloque "Documento fuente"')
    elif not rutas:
        rep.hallazgo('AH-1', 'el bloque "Documento fuente" no trae ninguna ruta')
    else:
        malas = 0
        for k, r in enumerate(rutas):
            p, motivo = resolver_ruta(r, raiz)
            if not p:
                malas += 1
                if motivo.startswith('es un link externo'):
                    rep.aviso('AH-1', 'Documento fuente: %s' % motivo, r)
                else:
                    rep.hallazgo('AH-1', 'Documento fuente: la ruta %s' % motivo, r)
            elif k == 0:
                if _es_ficha(p):
                    ficha_declarada = p
                    rep.ok('AH-1', 'el Documento fuente es una ficha del Cerebro con bloque '
                           '"Derivacion a backlog"', r)
                else:
                    rep.aviso('AH-1', 'la Historia no tiene ficha: el Documento fuente no es una '
                              'ficha con bloque "Derivacion a backlog" (no bloquea: los chequeos '
                              '11 a 18 quedan sin ficha)', r)
        if not malas and len(rutas) > 1:
            rep.ok('AH-1', 'las %d rutas del Documento fuente existen en el repo' % len(rutas))
        if ficha_arg and ficha_declarada and not _mismo_archivo(ficha_arg, ficha_declarada):
            rep.aviso('AH-1', 'la --ficha que se paso no es la que declara el Documento fuente',
                      '%s contra %s' % (ficha_arg, rutas[0]))

    # 10 (lado Descripcion) -- Reglas de negocio contra los Escenarios
    rn = historia.reglas_de_negocio(desc)
    if rn is None:
        rep.aviso('AH-10', 'la Descripcion no tiene el bloque "Reglas de negocio"')
    else:
        declaradas = []
        for it in rn:
            for c in it['citadas']:
                if c not in declaradas:
                    declaradas.append(c)
        for c in [c for c in declaradas if c not in indice]:
            rep.no_auditable('AH-10', 'la regla %s (bloque Reglas de negocio) no existe en el '
                             'Cerebro' % c)
        for c in sorted(reglas_esc - set(declaradas)):
            rep.aviso('AH-10', '%s la citan los Escenarios pero no esta en el bloque Reglas de '
                      'negocio' % c)
        for c in [c for c in declaradas if c not in reglas_esc and escs]:
            rep.aviso('AH-10', '%s esta en Reglas de negocio y ningun Escenario la cita: nadie la '
                      'verifica' % c)
        for it in rn:
            if not it['okf'] or not it['codigo']:
                continue
            p, motivo = resolver_ruta(it['okf'], raiz)
            if not p:
                rep.aviso('AH-10', 'la referencia OKF de %s %s' % (it['codigo'], motivo), it['okf'])
                continue
            try:
                if it['codigo'] not in texto.leer(p):
                    rep.aviso('AH-10', 'la referencia OKF de %s no menciona esa regla'
                              % it['codigo'], it['okf'])
            except (OSError, UnicodeDecodeError):
                rep.aviso('AH-10', 'no se pudo leer la referencia OKF de %s' % it['codigo'], it['okf'])

    # 11 -- Casos de uso
    cus = historia.casos_de_uso(desc)
    if cus is None:
        rep.no_auditable('AH-11', 'la Descripcion no tiene el bloque "Casos de uso": ausente no es '
                         'cumplido')
    elif not [c for c in cus if c['codigo']]:
        rep.no_auditable('AH-11', 'el bloque "Casos de uso" no trae ningun CU-nn (Regla del cero)')
    else:
        avisos, vistos = 0, set()
        for cu in cus:
            if not cu['codigo']:
                avisos += 1
                rep.aviso('AH-11', 'renglon de Casos de uso sin codigo CU-nn', cu['texto'][:100])
                continue
            if cu['codigo'] in vistos:
                avisos += 1
                rep.aviso('AH-11', '%s repetido en Casos de uso' % cu['codigo'])
            vistos.add(cu['codigo'])
            if not cu['reglas']:
                avisos += 1
                rep.aviso('AH-11', '%s no cita regla: no se puede cruzar con los Escenarios'
                          % cu['codigo'], cu['texto'][:100])
            elif not set(cu['reglas']) & reglas_esc:
                avisos += 1
                rep.aviso('AH-11', '%s: ningun Escenario comparte sus reglas; puede estar sin cubrir'
                          % cu['codigo'], '%s -- %s' % (', '.join(cu['reglas']), cu['texto'][:80]))
        if not avisos:
            rep.ok('AH-11', '%d CU-nn, cada uno comparte regla con algun Escenario (que lo cubra '
                   'de verdad lo mira el auditor)' % len(vistos))

    # 12 -- Datos y estados
    de = historia.datos_y_estados(desc)
    if de is None:
        rep.aviso('AH-12', 'la Descripcion no tiene el bloque "Datos y estados": solo se omite si '
                  'la Historia no toca datos ni estados; si los toca, las Tareas arman su contrato '
                  'sin fuente')
    elif not de:
        rep.aviso('AH-12', 'el bloque "Datos y estados" esta vacio')
    else:
        sueltos = 0
        for it in de:
            if it['reglas'] and not set(it['reglas']) & reglas_esc:
                sueltos += 1
                rep.aviso('AH-12', 'dato/estado cuyas reglas no cita ningun Escenario',
                          '%s -- %s' % (', '.join(it['reglas']), it['texto'][:80]))
        if not sueltos:
            rep.ok('AH-12', '%d renglones en Datos y estados; los que citan regla comparten alguna '
                   'con un Escenario' % len(de))

    # 19 (lado Descripcion) se cruza afuera, con los pendientes
    return ficha_declarada, bloques


def _chequear_ficha(rep, escs, desc, ficha, flujo, ficha_declarada, raiz):
    """Chequeo 13: las reglas de la Historia contra las que la ficha asigna a su [F-nn]."""
    if not ficha and not flujo:
        rep.aviso('AH-13', 'sin ficha: no se miraron los chequeos 13 a 18 (no bloquea; para '
                  'mirarlos, --ficha <ruta.md> --flujo F-nn)',
                  ('el Documento fuente declara %s'
                   % os.path.relpath(ficha_declarada, raiz).replace(os.sep, '/'))
                  if ficha_declarada else '')
        return ''
    origen = ''
    if not ficha:
        if not ficha_declarada:
            rep.no_auditable('AH-13', 'vino --flujo sin --ficha, y no hay un Documento fuente que '
                             'sea ficha: no se puede cruzar')
            return ''
        ficha, origen = ficha_declarada, ' (ficha tomada del Documento fuente)'
    if not flujo:
        rep.no_auditable('AH-13', 'vino --ficha sin --flujo F-nn: no se sabe contra que flujo cruzar')
        return ''
    ruta = ficha if os.path.isfile(ficha) else os.path.join(raiz, ficha)
    try:
        f = cerebro.leer_ficha(ruta)
    except (OSError, UnicodeDecodeError) as e:
        rep.no_auditable('AH-13', 'no se pudo leer la ficha (%s)' % type(e).__name__, ficha)
        return flujo
    d = f['derivacion']
    if d is None:
        rep.no_auditable('AH-13', 'la ficha no tiene el bloque "## Derivacion a backlog": ausente no '
                         'es cumplido', ficha)
        return flujo
    m = _FLUJO.match(flujo)
    clave = None
    if m:
        for k in d['F']:
            if int(k.split('-')[1]) == int(m.group(1)):
                clave = k
    if not clave:
        rep.no_auditable('AH-13', 'el flujo %s no esta en el bloque de derivacion de la ficha'
                         % flujo, 'flujos de la ficha: %s' % (_lista(sorted(d['F'])) or 'ninguno'))
        return flujo
    item = d['F'][clave]
    asignadas = []
    for c in item.get('reglas') or []:
        if c not in asignadas:
            asignadas.append(c)
    if not asignadas:
        rep.no_auditable('AH-13', '%s no tiene reglas asignadas en la ficha (Regla del cero)' % clave)
        return clave
    reglas_esc = set(c for e in escs for c in historia.reglas_del_escenario(e))
    reglas_desc = set()
    if desc:
        for it in historia.reglas_de_negocio(desc) or []:
            reglas_desc.update(it['citadas'])
    faltan = [c for c in asignadas if c not in reglas_esc]
    sobran = sorted((reglas_esc | reglas_desc) - set(asignadas))
    for c in faltan:
        rep.hallazgo('AH-13', '%s asigna %s y ningun Escenario la cita: regla huerfana aguas abajo'
                     % (clave, c), 'esta en la Descripcion, pero ningun Escenario la verifica'
                     if c in reglas_desc else '')
    for c in sobran:
        otros = [k for k, it in sorted(d['F'].items()) if c in (it.get('reglas') or [])]
        rep.aviso('AH-13', '%s no esta asignada a %s: puede venir de una regla compartida o ser '
                  'alcance de mas' % (c, clave),
                  ('asignada a %s' % ', '.join(otros)) if otros else
                  'no esta asignada a ningun F-nn de la ficha')
    if not faltan and not sobran:
        rep.ok('AH-13', 'las reglas de la Historia son exactamente las de %s%s'
               % (clave, origen), ', '.join(asignadas))
    elif not faltan:
        rep.ok('AH-13', 'los Escenarios citan las %d reglas que la ficha asigna a %s%s'
               % (len(asignadas), clave, origen))
    return clave


def _chequear_pendientes(rep, crit, desc, bloques, escs, raiz):
    """Chequeo 19, la parte contable: P-nnn citados y marcas de punto abierto."""
    abiertos, resueltos, leidos = leer_pendientes(raiz)
    citados_crit = historia.pendientes_citados(crit)
    if not leidos and (citados_crit or (desc and historia.pendientes_citados(desc))):
        rep.aviso('AH-19', 'no se encontro ningun pendientes.md en el Cerebro: los P-nnn citados no '
                  'se cruzaron')
        return
    avisos = 0
    for c in citados_crit:
        donde = [_nombre(i, e) for i, e in enumerate(escs, 1)
                 if c in historia.pendientes_citados(_texto_escenario(e))]
        if c in abiertos:
            avisos += 1
            rep.aviso('AH-19', 'Entonces sobre un punto abierto: confirmar (%s sigue abierto en %s)'
                      % (c, abiertos[c]), _lista(donde) or 'fuera de los Escenarios')
        elif c not in resueltos:
            avisos += 1
            rep.aviso('AH-19', '%s no figura en pendientes.md (ni abierto ni resuelto)' % c,
                      _lista(donde) or 'fuera de los Escenarios')
    for i, e in enumerate(escs, 1):
        s = texto.sin_acentos(_texto_escenario(e))
        marcas = sorted(set(_MARCAS_ABIERTAS.findall(s))) + (['marca de alerta'] if _ALERTA in s
                                                             else [])
        if marcas:
            avisos += 1
            rep.aviso('AH-19', '%s: el texto marca un punto abierto (%s): confirmar que el '
                      'Entonces no lo afirme como dato' % (_nombre(i, e), ', '.join(marcas)))
    if desc:
        por_bloque = dict((c, []) for c in historia.pendientes_citados(desc))
        for k, cuerpo in bloques.items():
            for c in historia.pendientes_citados(cuerpo):
                por_bloque.setdefault(c, []).append(_NOMBRE_BLOQUE.get(k, k))
        ab = [c for c in por_bloque if c in abiertos]
        if ab:
            avisos += 1
            rep.aviso('AH-19', 'la Descripcion cita %d puntos abiertos: confirmar que ningun '
                      'Entonces afirme sobre ellos' % len(ab),
                      _lista('%s (%s)' % (c, '/'.join(por_bloque[c]) or 'Descripcion') for c in ab))
        for c in por_bloque:
            if c not in abiertos and c not in resueltos:
                avisos += 1
                rep.aviso('AH-19', '%s, citado en la Descripcion, no figura en pendientes.md (ni '
                          'abierto ni resuelto)' % c, '/'.join(por_bloque[c]))
    if not avisos:
        rep.ok('AH-19', 'ningun P-nnn abierto citado ni marcas de punto abierto en los Escenarios '
               '(los que se afirman sin citarlos los mira el auditor)')


def _para_el_auditor(escs, desc):
    ui = [str(i) for i, e in enumerate(escs, 1) if _UI.search(texto.sin_acentos(_texto_escenario(e)))]
    res = [
        '3 y 4 - Que cada Entonces sea un resultado OBSERVABLE: la lista negra es un tamiz grueso '
        '("rapido", "intuitivo", "queda bien" no estan en la lista).',
        'PHI - Datos personales que la heuristica no ve (nombres, direcciones, diagnosticos): leer el texto; '
        'confirmar o descartar los AVISOS AH-PHI.',
        '5 - Un comportamiento por Escenario: un Y que introduce un sujeto distinto; confirmar o '
        'descartar los AVISOS AH-5.',
        '6 - Actor explicito y voz activa en cada Cuando (un Cuando sin sujeto, o "la parada queda '
        'normalizada"); confirmar los AVISOS AH-6.',
        '7 - Cero UI sin regla detras: %s; mirar que su regla respalde ese elemento de pantalla.'
        % (('%d de %d Escenarios nombran UI (%s)' % (len(ui), len(escs), _lista(ui, 12)))
           if ui else 'ningun Escenario nombra UI de la lista negra'),
        '8 - Cobertura de caminos: al menos un feliz y uno de error o borde; y uno de permiso si la '
        'Historia o sus reglas mencionan roles.',
        '10 - Que cada regla citada DIGA lo que el Escenario le atribuye (otro rol, otra pantalla, '
        'otro sistema = trazabilidad falsa). El script solo mira que exista.',
        '11 y 12 - Que cada CU-nn y cada campo/transicion de Datos y estados quede cubierto DE '
        'VERDAD por un Escenario (el script solo cruza reglas); confirmar los AVISOS AH-11/AH-12.'
        if desc else
        '11 y 12 - Sin Descripcion: Casos de uso y Datos y estados quedaron sin mirar.',
        '13 - Si hay AVISOS AH-13 (reglas de mas): decidir si es regla compartida o alcance '
        'inventado.',
        '14 - Que el titulo de la Historia describa el mismo alcance que su [F-nn] (ni mas amplio '
        'ni juntando dos).',
        '15 a 18 - Bloque de derivacion completo en los dos sentidos: prosa -> enumeracion, '
        'enumeracion -> prosa, reparto de reglas sin residuo, pendientes abiertos que tocan el '
        '[F-nn].',
        '19 - Entonces que afirman sobre un punto abierto SIN citarlo por numero; confirmar los '
        'AVISOS AH-19.',
        '20 - Que el Documento fuente (ficha o maqueta) no contradiga las reglas que la Historia cita.',
    ]
    return res


def auditar(criterios, descripcion=None, ficha=None, flujo=None, raiz=None):
    """Corre los chequeos y devuelve el Reporte. Sin efectos: no imprime ni escribe."""
    raiz = raiz or cerebro.raiz_repo()
    if ficha and not os.path.isfile(ficha) and os.path.isfile(os.path.join(raiz, ficha)):
        ficha = os.path.join(raiz, ficha)   # ruta relativa al repo, no al directorio actual
    rep = reporte.Reporte(HERRAMIENTA, criterios)
    try:
        crit = texto.leer(criterios)
    except (OSError, UnicodeDecodeError) as e:
        rep.falta_insumo('no se pudo leer --criterios %s (%s)' % (criterios, type(e).__name__))
        return rep

    escs = historia.escenarios(crit)
    ants = historia.antecedentes(crit)
    indice = cerebro.indice_reglas(raiz)
    citadas = []
    for e in escs:
        for c in historia.reglas_del_escenario(e):
            if c not in citadas:
                citadas.append(c)
    rep.datos = {'escenarios': len(escs),
                 'esquemas': sum(1 for e in escs if e['tipo'] != 'Escenario'),
                 'antecedentes': len(ants),
                 'reglas_citadas': citadas,
                 'flujo': ''}

    _chequear_gherkin(rep, crit, escs, indice)
    _chequear_formato(rep, crit, escs)

    desc, bloques, ficha_declarada = None, {}, None
    if descripcion:
        try:
            desc = texto.leer(descripcion)
        except (OSError, UnicodeDecodeError) as e:
            for ch in ('AH-1', 'AH-11', 'AH-12'):
                rep.no_auditable(ch, 'no se pudo leer --descripcion (%s)' % type(e).__name__,
                                 descripcion)
        else:
            if not desc.strip():
                for ch in ('AH-1', 'AH-11', 'AH-12'):
                    rep.no_auditable(ch, 'la Descripcion vino vacia (Regla del cero)', descripcion)
                desc = None
            else:
                ficha_declarada, bloques = _chequear_descripcion(rep, desc, escs, indice, raiz,
                                                                 ficha)
    else:
        rep.no_auditable('AH-1', 'sin --descripcion: el Documento fuente no se pudo mirar')
        rep.no_auditable('AH-11', 'sin --descripcion: los Casos de uso no se pudieron mirar')
        rep.no_auditable('AH-12', 'sin --descripcion: Datos y estados no se pudo mirar')

    rep.datos['flujo'] = _chequear_ficha(rep, escs, desc, ficha, flujo, ficha_declarada, raiz) or ''
    phi.revisar(rep, 'AH-PHI', crit + '\n' + (desc or ''),   # datos personales: lo inequivoco frena
                'los Criterios y la Descripcion' if desc else 'solo los Criterios (sin --descripcion)')
    _chequear_pendientes(rep, crit, desc, bloques, escs, raiz)
    rep.para_el_auditor = _para_el_auditor(escs, desc)
    return rep


def main(argv=None):
    p = argparse.ArgumentParser(
        prog='auditar-historia',
        description='Auditoria mecanica de una Historia (solo lectura). Salida: 0 sin hallazgos, '
                    '1 con hallazgos o no auditable, 2 SIN DATOS.')
    p.add_argument('--criterios', required=True, help='HTML (o texto) del campo Criterios de aceptacion')
    p.add_argument('--descripcion', help='HTML del campo Descripcion')
    p.add_argument('--ficha', help='ficha del Cerebro con el bloque Derivacion a backlog')
    p.add_argument('--flujo', help='el [F-nn] de la ficha al que rastrea la Historia')
    p.add_argument('--json', action='store_true', help='salida en JSON')
    p.add_argument('--salida', help='ademas de imprimirlo, guardar el reporte en este archivo')
    a = p.parse_args(argv)   # un pedido mal armado sale con 2: no midio nada
    try:
        rep = auditar(a.criterios, a.descripcion, a.ficha, a.flujo)
    except Exception as e:  # noqa: BLE001 -- a proposito: ningun error puede dar 0 ni 1
        rep = reporte.Reporte(HERRAMIENTA, a.criterios)
        rep.falta_insumo('el script fallo de una forma que no se esperaba (%s: %s). Esto NO es un '
                         'OK: es un bug de auditar-historia, no de la Historia' % (type(e).__name__, e))
    try:
        return reporte.emitir(rep, a.json, a.salida)
    except OSError as e:
        print('auditar-historia: no se pudo escribir --salida %s (%s)' % (a.salida, type(e).__name__),
              file=sys.stderr)
        reporte.emitir(rep, a.json, None)
        return reporte.SIN_DATOS


if __name__ == '__main__':
    sys.exit(main())
