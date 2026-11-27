#!/usr/bin/env python3
"""Puerta de Skills: cada skill declara su seccion y cada seccion tiene una puerta, la unica con descripcion visible.

    python -I bin/puerta-skills.py --medir [--json]   fase 0: que skills ve el modelo con descripcion y cuales solo
                                                       por nombre, en una sesion normal y en una aislada
    python -I bin/puerta-skills.py --verificar [--raiz DIR]
                                                       fase 1: secciones, puertas, indices y skillOverrides al dia
    python -I bin/puerta-skills.py --generar [--dry-run] [--raiz DIR]
                                                       fase 1: escribe el indice de cada puerta y skillOverrides

Tres salidas, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS (sin claude, o la respuesta no se pudo leer)

FASE 1 (el contrato). Cada skill de la fuente declara en su frontmatter
    metadata:
      seccion: <seccion>
      rol: puerta        # solo en la puerta de la seccion
Una skill VENDIDA de terceros no se edita: su seccion va en ASIGNADAS. Cada seccion tiene UNA puerta, la unica
con descripcion visible; las demas quedan "solo nombre" (skillOverrides de .claude/settings.json) y la puerta las
conoce por su indice generado, references/indice-seccion.md (la primera oracion de cada descripcion), que su
SKILL.md tiene que nombrar. Una seccion de una sola skill no lleva indice (no hay nada que rutear). --generar
escribe los indices y borra los sobrantes, de forma determinista (mismo input, mismos bytes); --verificar (y
bin/verificar-skills.py, que carga este modulo) dice lo que no cierra. Con la Puerta adoptada, la clave
skillOverrides de .claude/settings.json (la del proyecto, versionada) la maneja este script y cualquier otra entrada
es HALLAZGO: lo personal de cada persona va en .claude/settings.local.json. Si ninguna skill declara
metadata.seccion, la Puerta no esta adoptada: nada que verificar ni generar, y no frena. Despues de --generar,
python -I bin/sync-espejos.py skills lleva los indices a los espejos.

POR QUE EXISTE. Claude Code lista las skills con un cupo (~1% del contexto) y, cuando se desborda, saca las
DESCRIPCIONES de las menos usadas: el modelo ve el nombre y no sabe cuando usarla. Medido el 2026-11-27 en una
maquina real: en la sesion normal, 27 de las 38 skills del proyecto y 6 de sus 7 puertas quedaban solo por nombre;
en la sesion aislada (bin/sesion-proyecto.py), 8 y 3. Diseno completo: la pagina "Puerta de Skills".

COMO MIDE (--medir). Abre dos sesiones de una vuelta con claude -p (la normal y la aislada) y le pide al modelo
que clasifique cada skill de su listado en "con descripcion" o "solo nombre". Es el reporte del modelo, no un
conteo de la herramienta: alcanza para comparar antes y despues. El veredicto lo da la sesion AISLADA (la del
proyecto): HALLAZGO si alguna puerta queda solo por nombre; la normal se informa, porque depende de los plugins de
cada maquina. Cuesta dos llamadas cortas de la cuota de la persona.

QUE NO HACE. --medir y --verificar no modifican nada; --generar solo escribe (o borra) los indices y la clave
skillOverrides (el resto de settings.json queda tal cual). Solo biblioteca estandar. ASCII puro.
"""

import difflib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join('cerebro-digital', 'configuracion-ia', 'skills')
# Las puertas de antes de la fase 1 (sin metadata.rol todavia): para que la medicion de base sea comparable.
PUERTAS_ANTES = {'cerebro-orquestador', 'desarrollo', 'arquitectura-e-infraestructura', 'despliegue-continuo',
                 'operacion-de-servidores', 'seguridad', 'gestion-de-gitlab'}
# Skills VENDIDAS de terceros (no se editan, ver VENDIDAS en bin/verificar-skills.py): su seccion se asigna aca.
ASIGNADAS = {'archify': 'arquitectura'}
INDICE = os.path.join('references', 'indice-seccion.md')
# Lo que el SKILL.md de una puerta tiene que nombrar para que su indice se lea (si no, la puerta no rutea nada).
PUNTERO = 'references/indice-seccion.md'
SETTINGS = os.path.join('.claude', 'settings.json')
MAX_RESUMEN = 300
GENERAR = 'python -I bin/puerta-skills.py --generar'
INTRO_INDICE = ('Lo genera `%s` con la primera oraci\u00f3n de cada descripci\u00f3n: no se edita a mano.' % GENERAR)
PEDIDO = ('Sin usar herramientas ni cargar ninguna skill: devolve SOLO un JSON con la forma '
          '{"con_descripcion":[nombres],"solo_nombre":[nombres]} clasificando cada skill que aparece en tu listado '
          'de skills disponibles segun si ves su descripcion o unicamente su nombre. Nada de texto fuera del JSON.')


def metadatos(texto):
    """El bloque metadata del frontmatter como dict plano (seccion, rol, ...). Vacio si no hay."""
    m = re.match(r'---\n(.*?)\n---', texto.replace('\r\n', '\n'), re.S)
    if not m:
        return {}
    b = re.search(r'^metadata:[ \t]*\n((?:[ \t]+.*\n?)*)', m.group(1) + '\n', re.M)
    if not b:
        return {}
    out = {}
    for linea in b.group(1).split('\n'):
        kv = re.match(r'^[ \t]+([A-Za-z0-9_-]+):[ \t]*(.*?)[ \t]*(#.*)?$', linea)
        if kv:
            out[kv.group(1)] = kv.group(2).strip('"\'')
    return out


def propias(raiz):
    base = os.path.join(raiz, SKILLS)
    return {d for d in os.listdir(base) if os.path.isfile(os.path.join(base, d, 'SKILL.md'))} if os.path.isdir(base) else set()


def puertas(raiz):
    out = set()
    for d in propias(raiz):
        texto = open(os.path.join(raiz, SKILLS, d, 'SKILL.md'), encoding='utf-8', errors='replace').read()
        if metadatos(texto).get('rol') == 'puerta':
            out.add(d)
    return out


# ---------------------------------------------------------------------------------------------- fase 1: secciones

_VS = []


def _verificar_skills():
    """bin/verificar-skills.py como modulo: de ahi sale el frontmatter (la descripcion plegada como la lee la
    herramienta). Se carga una vez y desde el bin de este script, no desde la raiz que se mira."""
    if not _VS:
        spec = importlib.util.spec_from_file_location('verificar_skills_para_puerta',
                                                      os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                   'verificar-skills.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _VS.append(mod)
    return _VS[0]


def _datos(raiz):
    """{skill: {'seccion', 'rol', 'declarada', 'desc', 'texto'}} de cada skill de la fuente, por nombre."""
    fm = _verificar_skills().frontmatter
    out = {}
    for n in sorted(propias(raiz)):
        raw = open(os.path.join(raiz, SKILLS, n, 'SKILL.md'), 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        texto = raw.decode('utf-8', errors='replace').replace('\r\n', '\n')
        meta = metadatos(texto)
        datos, _cuerpo = fm(texto)
        declarada = meta.get('seccion') or ''
        out[n] = {'seccion': declarada or ASIGNADAS.get(n, ''), 'rol': meta.get('rol', ''), 'declarada': bool(declarada),
                  'desc': (datos or {}).get('description', ''), 'texto': texto}
    return out


def _secciones(datos):
    out = {}
    for n in sorted(datos):
        sec = datos[n]['seccion']
        if not sec:
            continue
        e = out.setdefault(sec, {'puerta': None, 'puertas': [], 'skills': []})
        e['skills'].append(n)
        if datos[n]['rol'] == 'puerta':
            e['puertas'].append(n)
    for e in out.values():
        e['puerta'] = e['puertas'][0] if len(e['puertas']) == 1 else None
    return out


def secciones(raiz):
    """{seccion: {'puerta': nombre o None (si no hay una sola), 'puertas': [...], 'skills': [...]}}, ordenadas."""
    return _secciones(_datos(raiz))


def adoptada(raiz):
    """True si alguna skill de la fuente declara metadata.seccion (las ASIGNADAS no cuentan: estan siempre)."""
    return any(d['declarada'] for d in _datos(raiz).values())


def resumen(desc):
    """La descripcion plegada en una linea, cortada en la primera oracion o, si no entra, en el ultimo espacio antes
    de MAX_RESUMEN caracteres (sin espacio, a MAX_RESUMEN justos), con '...'."""
    plano = ' '.join(desc.split())
    m = re.search(r'[.!?](?=\s|$)', plano)
    if m and m.end() <= MAX_RESUMEN:
        return plano[:m.end()]
    if len(plano) <= MAX_RESUMEN:
        return plano
    trozo = plano[:MAX_RESUMEN + 1]
    corte = trozo.rfind(' ')
    return (trozo[:corte] if corte > 0 else plano[:MAX_RESUMEN]).rstrip() + '...'


def _indice(datos, secs, seccion):
    e = secs.get(seccion) or {'puertas': [], 'skills': []}
    otras = [n for n in e['skills'] if n not in e['puertas']]
    if not otras:
        return None
    lineas = ['# \u00cdndice de la secci\u00f3n %s' % seccion, '', INTRO_INDICE, '']
    lineas += ['- `%s`: %s' % (n, resumen(datos[n]['desc'])) for n in otras]
    return '\n'.join(lineas) + '\n'


def indice_esperado(raiz, seccion):
    """El texto de references/indice-seccion.md de la puerta de esa seccion (UTF-8, LF), o None si la seccion tiene
    una sola skill (o no existe): ahi no hay nada que rutear y no va indice."""
    datos = _datos(raiz)
    return _indice(datos, _secciones(datos), seccion)


def _con_indice(datos, secs):
    """{puerta: seccion} de las puertas que llevan indice: la unica puerta de una seccion de mas de una skill."""
    return {secs[s]['puerta']: s for s in sorted(secs)
            if secs[s]['puerta'] and len(secs[s]['skills']) > 1}


def _sobrantes(raiz, datos, secs):
    """Skills con references/indice-seccion.md que no les toca (seccion de una sola skill, o dejo de ser puerta)."""
    con = _con_indice(datos, secs)
    return [n for n in sorted(datos) if n not in con and os.path.isfile(os.path.join(raiz, SKILLS, n, INDICE))]


def _overrides(datos):
    if not any(d['declarada'] for d in datos.values()):
        return {}
    return {n: 'name-only' for n in sorted(datos) if datos[n]['rol'] != 'puerta'}


def overrides_esperados(raiz):
    """{skill: 'name-only'} para cada skill de la fuente que no es puerta, ordenado. Vacio si no esta adoptada."""
    return _overrides(_datos(raiz))


def _leer_settings(raiz):
    """(dict, bytes) de .claude/settings.json; (None, None) si no existe. ValueError si no es JSON."""
    ruta = os.path.join(raiz, SETTINGS)
    if not os.path.isfile(ruta):
        return None, None
    raw = open(ruta, 'rb').read()
    d = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(d, dict):
        raise ValueError('no es un objeto JSON')
    return d, raw


def _rel(*partes):
    return '/'.join(p.replace(os.sep, '/') for p in partes)


# Lo que --generar no arregla: con esto roto no escribe nada. (puerta-sin-indice tampoco lo arregla, pero no frena
# la generacion: se corrige en el SKILL.md de la puerta.)
ESTRUCTURA = ('sin-seccion', 'rol-invalido', 'sin-puerta', 'varias-puertas', 'settings')


def problemas(raiz):
    """[(codigo, texto)] de lo que no cierra: cada uno es HALLAZGO. Vacio si la Puerta no esta adoptada."""
    datos = _datos(raiz)
    if not any(d['declarada'] for d in datos.values()):
        return []
    out = []
    for n in sorted(datos):
        if not datos[n]['seccion']:
            out.append(('sin-seccion', '%s no declara metadata.seccion (va en su frontmatter; si es una skill vendida, '
                                       'en ASIGNADAS de bin/puerta-skills.py)' % n))
    for n in sorted(datos):
        if datos[n]['rol'] and datos[n]['rol'] != 'puerta':
            out.append(('rol-invalido', '%s: metadata.rol "%s" (el unico valor es puerta, y solo en la puerta de su '
                                        'seccion)' % (n, datos[n]['rol'])))
    secs = _secciones(datos)
    for sec in sorted(secs):
        e = secs[sec]
        if not e['puertas']:
            out.append(('sin-puerta', 'la seccion %s no tiene puerta (%s): una de sus skills lleva metadata.rol: puerta'
                                      % (sec, ' '.join(e['skills']))))
        elif len(e['puertas']) > 1:
            out.append(('varias-puertas', 'la seccion %s tiene %d puertas (%s): va una sola'
                                          % (sec, len(e['puertas']), ' '.join(e['puertas']))))
    con_indice = _con_indice(datos, secs)
    for p, sec in sorted(con_indice.items()):
        if PUNTERO not in datos[p]['texto']:
            out.append(('puerta-sin-indice', 'el SKILL.md de %s, puerta de la seccion %s (%d skills), no nombra %s: las '
                                              'demas quedan solo por nombre y nadie las rutea; va una linea que lo apunte'
                                              % (p, sec, len(secs[sec]['skills']), PUNTERO)))
        rel = _rel(SKILLS, p, INDICE)
        ruta = os.path.join(raiz, SKILLS, p, INDICE)
        actual = open(ruta, 'rb').read() if os.path.isfile(ruta) else None
        if actual is None:
            out.append(('indice', 'falta el indice de la puerta %s (%s): correr %s' % (p, rel, GENERAR)))
        elif actual != _indice(datos, secs, sec).encode('utf-8'):
            out.append(('indice', 'el indice de la puerta %s (%s) no esta al dia con las skills de su seccion: correr %s'
                                  % (p, rel, GENERAR)))
    for n in _sobrantes(raiz, datos, secs):
        out.append(('indice-sobrante', '%s tiene %s y no es la puerta de una seccion de varias skills: correr %s (lo borra)'
                                       % (n, _rel(SKILLS, n, INDICE), GENERAR)))
    try:
        ajustes, _raw = _leer_settings(raiz)
    except ValueError as e:
        out.append(('settings', 'no pude leer %s: %s' % (_rel(SETTINGS), e)))
        return out
    if ajustes is None:
        return out
    actual = ajustes.get('skillOverrides') or {}
    if not isinstance(actual, dict):
        actual = {'(no es un objeto)': str(actual)}
    esperado = _overrides(datos)
    if actual != esperado:
        faltan = sorted(set(esperado) - set(actual))
        sobran = sorted(set(actual) - set(esperado))
        otro = sorted(n for n in set(actual) & set(esperado) if actual[n] != esperado[n])
        detalle = '; '.join(x for x in ('faltan: ' + ' '.join(faltan) if faltan else '',
                                        'sobran: ' + ' '.join(sobran) if sobran else '',
                                        'con otro valor: ' + ' '.join(otro) if otro else '') if x)
        out.append(('overrides', 'skillOverrides de %s no es el esperado (%s): correr %s' % (_rel(SETTINGS), detalle, GENERAR)))
    con = sorted(n for n in actual if n in datos and datos[n]['rol'] == 'puerta')
    if con:
        out.append(('puerta-con-override', '%s es puerta y tiene skillOverrides: una puerta no puede quedar solo por '
                                           'nombre (es la unica descripcion visible de su seccion)' % ' '.join(con)))
    return out


def notas(raiz):
    """Lo que no se pudo verificar y no es HALLAZGO: hoy, skillOverrides en una raiz sin .claude/settings.json."""
    if not adoptada(raiz) or os.path.isfile(os.path.join(raiz, SETTINGS)):
        return []
    return ['skillOverrides no se verifico: no hay %s en %s' % (_rel(SETTINGS), raiz)]


def generar(raiz, escribir=True):
    """(bloqueos, cambios). Con la estructura rota (sin seccion, sin puerta, dos puertas, rol raro, settings ilegible)
    no escribe nada y devuelve esos problemas. Si no, escribe lo que difiere, borra los indices sobrantes y devuelve
    [(ruta relativa, antes, despues)] (despues None = borrado)."""
    datos = _datos(raiz)
    if not any(d['declarada'] for d in datos.values()):
        return [], []
    bloqueos = [p for p in problemas(raiz) if p[0] in ESTRUCTURA]
    if bloqueos:
        return bloqueos, []
    cambios = []
    secs = _secciones(datos)
    for n in _sobrantes(raiz, datos, secs):
        ruta = os.path.join(raiz, SKILLS, n, INDICE)
        cambios.append((_rel(SKILLS, n, INDICE), open(ruta, 'rb').read(), None))
        if escribir:
            os.remove(ruta)
            if not os.listdir(os.path.dirname(ruta)):
                os.rmdir(os.path.dirname(ruta))
    for p, sec in sorted(_con_indice(datos, secs).items()):
        ruta = os.path.join(raiz, SKILLS, p, INDICE)
        actual = open(ruta, 'rb').read() if os.path.isfile(ruta) else None
        nuevo = _indice(datos, secs, sec).encode('utf-8')
        if actual != nuevo:
            cambios.append((_rel(SKILLS, p, INDICE), actual, nuevo))
            if escribir:
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, 'wb') as h:
                    h.write(nuevo)
    ajustes, raw = _leer_settings(raiz)
    esperado = _overrides(datos)
    actual = (ajustes or {}).get('skillOverrides')
    if not isinstance(actual, dict) or list(actual.items()) != list(esperado.items()):
        if actual is None and not esperado:
            return [], cambios
        nuevo_d = dict(ajustes or {})
        if esperado:
            nuevo_d['skillOverrides'] = esperado
        else:
            nuevo_d.pop('skillOverrides', None)
        texto = json.dumps(nuevo_d, indent=2, ensure_ascii=not (raw and any(b > 127 for b in raw)))
        if raw is None or raw.endswith(b'\n'):
            texto += '\n'
        if raw and b'\r\n' in raw:
            texto = texto.replace('\n', '\r\n')
        nuevo = texto.encode('utf-8')
        if raw != nuevo and (raw is not None or esperado):
            cambios.append((_rel(SETTINGS), raw, nuevo))
            if escribir:
                os.makedirs(os.path.dirname(os.path.join(raiz, SETTINGS)), exist_ok=True)
                with open(os.path.join(raiz, SETTINGS), 'wb') as h:
                    h.write(nuevo)
    return [], cambios


def _diferencia(antes, despues):
    a = (antes or b'').decode('utf-8', errors='replace').splitlines()
    d = (despues or b'').decode('utf-8', errors='replace').splitlines()
    return [l for l in difflib.unified_diff(a, d, lineterm='', n=0) if not l.startswith(('---', '+++', '@@'))]


NO_MIRA = ('  Lo que este script NO mira: si la seccion asignada a cada skill es la correcta, ni si la descripcion de '
           'cada puerta alcanza para rutear su seccion; que el listado real de Claude Code respete skillOverrides lo '
           'mide --medir.')


def main_verificar(raiz):
    if not os.path.isdir(os.path.join(raiz, SKILLS)):
        print('SIN DATOS -- no hay fuente de skills (%s) en %s' % (_rel(SKILLS), raiz))
        return SIN_DATOS
    if not adoptada(raiz):
        print('OK -- sin secciones: la Puerta no est\u00e1 adoptada (ninguna skill declara metadata.seccion); nada que '
              'verificar')
        print(NO_MIRA)
        return OK
    probs = problemas(raiz)
    secs = secciones(raiz)
    print('%s -- Puerta de Skills: %d secciones, %d skills, %d problema(s)'
          % ('HALLAZGO' if probs else 'OK', len(secs), len(propias(raiz)), len(probs)))
    for c, t in probs:
        print('  HALLAZGO %s: %s' % (c, t))
    for n in notas(raiz):
        print('  AVISO    %s' % n)
    print(NO_MIRA)
    return HALLAZGO if probs else OK


def main_generar(raiz, seco):
    if not os.path.isdir(os.path.join(raiz, SKILLS)):
        print('SIN DATOS -- no hay fuente de skills (%s) en %s' % (_rel(SKILLS), raiz))
        return SIN_DATOS
    if not adoptada(raiz):
        print('OK -- sin secciones: la Puerta no est\u00e1 adoptada (ninguna skill declara metadata.seccion); nada que '
              'generar')
        return OK
    bloqueos, cambios = generar(raiz, escribir=not seco)
    if bloqueos:
        print('HALLAZGO -- no gener\u00e9 nada: la estructura de secciones no cierra')
        for c, t in bloqueos:
            print('  HALLAZGO %s: %s' % (c, t))
        return HALLAZGO
    if not cambios:
        print('OK -- nada que cambiar: los \u00edndices de las puertas y skillOverrides est\u00e1n al d\u00eda')
        return OK
    if seco:
        print('OK -- --dry-run: cambiar\u00eda %d archivo(s); no escrib\u00ed nada' % len(cambios))
    else:
        print('OK -- escrib\u00ed %d archivo(s); los espejos se regeneran con python -I bin/sync-espejos.py skills' % len(cambios))
    for rel, antes, despues in cambios:
        if despues is None:
            print('  %s %s' % ('borraria ' if seco else 'borrado  ', rel))
            continue
        print('  %s %s' % ('cambiaria' if seco else 'escrito  ', rel))
        if seco:
            for linea in _diferencia(antes, despues):
                print('      ' + linea)
    return OK


def leer_medicion(ruta, prop, puert):
    """Cuenta lo que el modelo dijo ver. None si no hay respuesta legible (SIN DATOS, nunca cero)."""
    resultado = None
    for linea in open(ruta, encoding='utf-8', errors='replace'):
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        if isinstance(d, dict) and 'result' in d:
            resultado = d.get('result') or ''
    if not resultado:
        return None
    m = re.search(r'\{.*\}', resultado, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
        con, solo = set(j.get('con_descripcion') or []), set(j.get('solo_nombre') or [])
    except (ValueError, AttributeError, TypeError):
        return None
    return {'total': len(con | solo), 'con_descripcion': len(con), 'solo_nombre': len(solo),
            'propias_solo_nombre': sorted(solo & prop), 'puertas_solo_nombre': sorted(solo & puert)}


def veredicto(mediciones):
    a = mediciones.get('aislada')
    if a is None:
        return SIN_DATOS
    return HALLAZGO if a['puertas_solo_nombre'] else OK


def _sesion_proyecto():
    spec = importlib.util.spec_from_file_location('sesion_proyecto', os.path.join(RAIZ, 'bin', 'sesion-proyecto.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def medir(raiz):
    exe = shutil.which('claude')
    if not exe:
        return None
    prop = propias(raiz)
    puert = puertas(raiz) or (PUERTAS_ANTES & prop)
    aislada = _sesion_proyecto().comando(raiz, [])
    out = {}
    carpeta = tempfile.mkdtemp(prefix='puerta-medir-')
    for nombre, extra in (('normal', []), ('aislada', aislada)):
        ruta = os.path.join(carpeta, nombre + '.json')
        with open(ruta, 'w', encoding='utf-8') as h:
            try:
                subprocess.run([exe, '-p', PEDIDO, '--output-format', 'json', '--max-turns', '1'] + extra, cwd=raiz,
                               stdout=h, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=300)
            except (OSError, subprocess.TimeoutExpired):
                pass
        out[nombre] = leer_medicion(ruta, prop, puert)
    out['puertas'] = sorted(puert)
    out['propias'] = len(prop)
    return out


def main():
    args = sys.argv[1:]
    try:
        sys.stdout.reconfigure(errors='backslashreplace')
    except (AttributeError, ValueError):
        pass
    raiz = RAIZ
    if '--raiz' in args:
        i = args.index('--raiz')
        if i + 1 >= len(args):
            print('SIN DATOS -- --raiz sin carpeta')
            return SIN_DATOS
        raiz = os.path.abspath(args[i + 1])
    if '--verificar' in args:
        return main_verificar(raiz)
    if '--generar' in args:
        return main_generar(raiz, '--dry-run' in args)
    if '--medir' not in args:
        print(__doc__)
        return SIN_DATOS
    m = medir(RAIZ)
    if m is None:
        print('SIN DATOS -- no se encontro el comando claude en el PATH')
        return SIN_DATOS
    rc = veredicto(m)
    if '--json' in args:
        print(json.dumps(dict(m, veredicto=['OK', 'HALLAZGO', 'SIN DATOS'][rc]), ensure_ascii=False, indent=2))
        return rc
    print('%s -- puertas con descripcion visible (%d puertas, %d skills del proyecto)'
          % (['OK', 'HALLAZGO', 'SIN DATOS'][rc], len(m['puertas']), m['propias']))
    for nombre in ('aislada', 'normal'):
        x = m.get(nombre)
        if x is None:
            print('  %-8s SIN DATOS (la respuesta no se pudo leer)' % nombre)
            continue
        print('  %-8s %d skills: %d con descripcion, %d solo nombre. Del proyecto solo nombre: %d. Puertas solo nombre: %s'
              % (nombre, x['total'], x['con_descripcion'], x['solo_nombre'], len(x['propias_solo_nombre']),
                 ', '.join(x['puertas_solo_nombre']) or 'ninguna'))
    print('  Lo que este script NO mira: es el reporte del modelo sobre su listado, no un conteo de Claude Code; la '
          'sesion normal depende de los plugins de cada maquina y no frena.')
    return rc


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
