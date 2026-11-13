#!/usr/bin/env python3
"""Mapa de avance de una modernizacion (refactor o migracion) por slice, y la BARRERA del corte de trafico.

    python bin/mapa-modernizacion.py ver   <cerebro-digital/<modulo>/aplicacion/modernizacion.md> [--mermaid] [--json]
    python bin/mapa-modernizacion.py corte <modernizacion.md> --slice <nombre> --paridad <resultado.json> [--max-dias 7]
    python bin/mapa-modernizacion.py corte <modernizacion.md> --slice <nombre> --veredicto <veredicto.md>   (estrategia refactor)
    python bin/mapa-modernizacion.py verificar <modernizacion.md>

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (algo esta fuera de orden, o el corte NO se puede hacer)   2 = SIN DATOS

LA TABLA (la escribe cerebro-curator con el "si" de una persona; este script solo la lee):
  | Slice | Estrategia | Estado | Contrato | Corpus | Golden | Paridad | Corte aprobado por | Notas |
  Estado, en orden: pendiente -> contrato -> red -> construido -> paridad -> cortado -> apagado
  (refactor en el lugar usa los mismos estados: "contrato" = limites del modulo escritos, "cortado" = modulo cumple C1..C8).

POR QUE EXISTE. Una migracion por estrangulador vive meses y el estado de cada slice se pierde en el chat. Aca
esta en el Cerebro, con la secuencia fija y una barrera: `corte` dice OK solo si DEC-004 esta confirmada, el slice
esta en estado "paridad", el resultado de paridad lo escribio paridad.py (firma), es OK, reciente y del golden que
cita la tabla (se abre y se verifica su firma), y una persona dejo escrito que aprueba el corte. Sin eso, HALLAZGO;
sin los archivos, SIN DATOS. En un refactor en el lugar no hay trafico que cortar: "cortado" significa que el
modulo cumple las convenciones, y la prueba es el bloque VEREDICTO del verificador (--veredicto), con verificar-tdd
en OK y en modo caracterizacion. Es la regla "sin prueba no se corta" de los toolkits de estrangulador, hecha con
biblioteca estandar y leyendo el Cerebro.

QUE NO HACE. No escribe la tabla, no corre la paridad, no corta trafico (eso lo hace una persona en el enrutador).
"""

import argparse
import datetime
import importlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
paridad = importlib.import_module('paridad')   # las firmas se verifican con el mismo codigo que las escribe

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
ESTADOS = ['pendiente', 'contrato', 'red', 'construido', 'paridad', 'cortado', 'apagado']
COLS = ['slice', 'estrategia', 'estado', 'contrato', 'corpus', 'golden', 'paridad', 'corte aprobado por', 'notas']


def leer(p):
    with open(p, 'r', encoding='utf-8-sig') as h:
        return h.read()


def tabla(texto):
    filas, cab = [], None
    for l in texto.split('\n'):
        if not l.strip().startswith('|'):
            cab = None if cab and filas else cab
            continue
        celdas = [c.strip() for c in l.strip().strip('|').split('|')]
        bajas = [c.lower().strip('*` ') for c in celdas]
        if cab is None and 'slice' in bajas and 'estado' in bajas:
            cab = bajas; continue
        if cab is None or set(c.strip() for c in celdas) <= {'', '---', ':---', '---:'} or all(re.match(r'^:?-+:?$', c) for c in celdas if c):
            continue
        fila = {cab[i]: celdas[i] for i in range(min(len(cab), len(celdas)))}
        fila['slice'] = (fila.get('slice') or '').strip('*` ')
        if fila['slice'] and not fila['slice'].startswith('<completar'):
            filas.append(fila)
    return filas


def estado_de(f):
    return (f.get('estado') or '').strip('*` ').lower()


def es_refactor(f):
    return 'refactor' in (f.get('estrategia') or '').lower()


def resolver(ruta, archivo_md, slice_):
    """Busca el golden que cita la tabla: tal cual, relativo al .md, o en aplicacion/paridad/<slice>/."""
    base = os.path.dirname(os.path.abspath(archivo_md))
    for c in (ruta, os.path.join(base, ruta), os.path.join(base, 'paridad', slice_, os.path.basename(ruta))):
        if ruta and os.path.isfile(c):
            return os.path.abspath(c)
    return None


def dec004_confirmada(ruta_md):
    carpeta = os.path.dirname(os.path.abspath(ruta_md))
    dec = os.path.join(os.path.dirname(carpeta), 'arquitectura', 'decisiones.md')
    if not os.path.isfile(dec):
        return None, 'no encontre %s' % dec
    t = leer(dec)
    m = re.search(r'## DEC-004[^\n]*\n(.*?)(?=\n## |\Z)', t, re.S)
    if not m:
        return None, 'DEC-004 no esta en decisiones.md'
    bloque = m.group(1)
    return bool(re.search(r'\*\*Estado:\*\*\s*\**\s*Confirmad', bloque)), None


def ver(a, filas):
    problemas = []
    for f in filas:
        e = estado_de(f)
        if e not in ESTADOS:
            problemas.append('%s: estado "%s" no es uno de %s' % (f['slice'], e, ', '.join(ESTADOS)))
            continue
        i = ESTADOS.index(e)
        if es_refactor(f):
            if i >= ESTADOS.index('cortado') and not f.get('corte aprobado por', '').strip('- '):
                problemas.append('%s: esta en "%s" sin "Corte aprobado por"' % (f['slice'], e))
            continue   # refactor en el lugar: la red puede ser solo tests en el repo; corpus y golden no son obligatorios
        if i >= ESTADOS.index('red') and not f.get('corpus', '').strip('- '):
            problemas.append('%s: esta en "%s" pero no cita corpus' % (f['slice'], e))
        if i >= ESTADOS.index('paridad') and not f.get('golden', '').strip('- '):
            problemas.append('%s: esta en "%s" pero no cita golden' % (f['slice'], e))
        if i >= ESTADOS.index('cortado') and not f.get('corte aprobado por', '').strip('- '):
            problemas.append('%s: esta en "%s" sin "Corte aprobado por": un corte sin persona que lo apruebe es HALLAZGO' % (f['slice'], e))
    if a.json:
        print(json.dumps({'veredicto': 'HALLAZGO' if problemas else 'OK', 'slices': filas, 'problemas': problemas}, ensure_ascii=False, indent=1))
    else:
        por = {e: [f['slice'] for f in filas if estado_de(f) == e] for e in ESTADOS}
        print('%s -- %d slice(s): ' % ('HALLAZGO' if problemas else 'OK', len(filas)) + ' | '.join('%s %d' % (e, len(por[e])) for e in ESTADOS))
        for f in filas:
            print('  %-24s %-12s %-10s corpus=%s golden=%s paridad=%s corte=%s' % (f['slice'][:24], f.get('estrategia', '')[:12], estado_de(f), f.get('corpus', '-') or '-', f.get('golden', '-') or '-', f.get('paridad', '-') or '-', f.get('corte aprobado por', '-') or '-'))
        for p in problemas:
            print('  HALLAZGO ' + p)
        if getattr(a, 'mermaid', False):
            print('\n```mermaid\nflowchart LR')
            print('  ' + ' --> '.join(ESTADOS))
            for f in filas:
                print('  %s[%s] -.-> %s' % (re.sub(r'\W', '_', f['slice']), f['slice'], estado_de(f) if estado_de(f) in ESTADOS else 'pendiente'))
            print('```')
    return HALLAZGO if problemas else OK


def corte(a, filas):
    f = next((x for x in filas if x['slice'] == a.slice.strip('`* ')), None)
    if not f:
        print('SIN DATOS -- el slice "%s" no esta en la tabla' % a.slice); return SIN_DATOS
    conf, err = dec004_confirmada(a.archivo)
    if err:
        print('SIN DATOS -- ' + err); return SIN_DATOS
    quien = (f.get('corte aprobado por') or '').strip('- ')
    persona = bool(quien) and not paridad.AGENTE.search(quien)
    checks = [('DEC-004 confirmada', conf), ('el slice esta en estado "paridad"', estado_de(f) == 'paridad')]
    # Solo un refactor en el lugar se prueba con el veredicto; una migracion, siempre con la paridad.
    if es_refactor(f):
        if not a.veredicto:
            print('SIN DATOS -- el slice es un refactor en el lugar: el corte se prueba con --veredicto <bloque VEREDICTO del verificador>'); return SIN_DATOS
        if not os.path.isfile(a.veredicto):
            print('SIN DATOS -- no existe el veredicto %s: una verificacion que no corrio es SIN DATOS, no OK' % a.veredicto); return SIN_DATOS
        with open(a.veredicto, 'r', encoding='utf-8-sig', errors='replace') as h:
            v = h.read()
        dias = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(a.veredicto))).days
        checks.append(('el veredicto tiene el bloque VEREDICTO-INICIO..FIN', 'VEREDICTO-INICIO' in v and 'VEREDICTO-FIN' in v))
        checks.append(('verificar-tdd dio OK', bool(re.search(r'(?im)^\s*5\s+verificar-tdd\s*:\s*OK\b', v))))
        checks.append(('la red fue de caracterizacion (modo caracterizacion citado)', 'caracterizacion' in v.lower()))
        checks.append(('cero bloqueantes', bool(re.search(r'(?i)BLOQUEANTES:\s*0\b', v))))
        checks.append(('el veredicto es reciente (<= %d dias)' % a.max_dias, 0 <= dias <= a.max_dias))
    else:
        if not a.paridad:
            print('SIN DATOS -- el corte de una migracion se prueba con --paridad <resultado.json de paridad.py comparar --json>'); return SIN_DATOS
        try:
            with open(a.paridad, 'r', encoding='utf-8-sig') as h:
                p = json.load(h)
        except (OSError, ValueError) as e:
            print('SIN DATOS -- no pude leer el resultado de paridad (%s): la paridad que no corrio es SIN DATOS, no OK' % e); return SIN_DATOS
        if p.get('escrito_por') != 'bin/paridad.py' or p.get('firma') != paridad.firmar_resultado(p):
            print('SIN DATOS -- el resultado de paridad NO verifica (no lo escribio bin/paridad.py o fue editado): no es evidencia'); return SIN_DATOS
        gf = (f.get('golden') or '').strip('` ')
        ruta_golden = resolver(gf, a.archivo, f['slice'])
        if not ruta_golden:
            print('SIN DATOS -- la tabla cita el golden "%s" y no lo encuentro (tal cual, junto al .md ni en aplicacion/paridad/%s/)' % (gf, f['slice'])); return SIN_DATOS
        g, err = paridad.verificar_golden(ruta_golden)
        if err:
            print('SIN DATOS -- el golden que cita la tabla no verifica: %s' % err); return SIN_DATOS
        checks.append(('la paridad dio OK', p.get('veredicto') == 'OK'))
        checks.append(('la paridad es de este slice', (p.get('slice') or '') == f['slice']))
        try:
            dias = (datetime.date.today() - datetime.date.fromisoformat(p.get('fecha', ''))).days
        except ValueError:
            dias = None
        checks.append(('la paridad es reciente (<= %d dias)' % a.max_dias, dias is not None and 0 <= dias <= a.max_dias))
        checks.append(('la paridad corrio contra el golden que cita la tabla (misma firma)', p.get('golden_firma') == g['firma']))
        checks.append(('la paridad no tiene aceptadas sin aprobar', not p.get('aceptadas_sin_aprobar')))
        checks.append(('ningun caso de la paridad quedo sin comparar', not any(x.get('resultado') == 'SIN DATOS' for x in p.get('filas') or [])))
        aceptados = [x['id'] for x in p.get('filas') or [] if x.get('resultado') == 'sin comparar, aceptado']
        if aceptados:
            print('  AVISO casos sin comparar que acepto una persona: %s' % ', '.join(aceptados))
        if p.get('volatiles'):
            print('  AVISO volatiles ignorados en esa paridad: %s (tienen que estar anotados en la ficha del slice)' % ', '.join(p['volatiles']))
    checks.append(('una persona aprobo el corte (columna "Corte aprobado por")', persona))
    fallan = [n for n, ok in checks if not ok]
    print('%s -- corte del slice %s: %d de %d condiciones' % ('OK' if not fallan else 'HALLAZGO', a.slice, len(checks) - len(fallan), len(checks)))
    for n, ok in checks:
        print('  %s %s' % ('ok  ' if ok else 'FALTA', n))
    if not fallan:
        print('  El corte lo hace una persona (el enrutador en una migracion; en un refactor, dar el modulo por cumplido); despues la tabla pasa a "cortado" con cerebro-curator. Este script no toca nada.')
    return OK if not fallan else HALLAZGO


def main():
    ap = argparse.ArgumentParser(description='Avance de la modernizacion por slice y barrera del corte.')
    sub = ap.add_subparsers(dest='accion', required=True)
    v = sub.add_parser('ver'); v.add_argument('archivo'); v.add_argument('--mermaid', action='store_true'); v.add_argument('--json', action='store_true')
    c = sub.add_parser('corte'); c.add_argument('archivo'); c.add_argument('--slice', required=True); c.add_argument('--paridad', default=''); c.add_argument('--veredicto', default=''); c.add_argument('--max-dias', type=int, default=7)
    w = sub.add_parser('verificar'); w.add_argument('archivo')
    a = ap.parse_args()
    if not os.path.isfile(a.archivo):
        print('SIN DATOS -- no existe %s' % a.archivo); return SIN_DATOS
    filas = tabla(leer(a.archivo))
    if not filas:
        print('SIN DATOS -- %s no tiene la tabla de slices (columnas Slice | Estrategia | Estado | ...)' % a.archivo); return SIN_DATOS
    if a.accion == 'corte':
        return corte(a, filas)
    if a.accion == 'verificar':
        a.json = False; a.mermaid = False
    return ver(a, filas)


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
