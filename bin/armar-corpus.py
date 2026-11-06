#!/usr/bin/env python3
"""Arma el ESQUELETO del corpus de paridad de un slice a partir de la radiografia. No inventa valores.

    python bin/armar-corpus.py <radiografia.json> --slice <modulo> [--salida borrador/paridad/<slice>/corpus.json]
    python bin/armar-corpus.py <radiografia.json> --slice <modulo> --verificar <corpus.json>     (que no falte endpoint ni regla)

Tres estados, nunca dos:  0 = esqueleto armado / corpus completo   1 = HALLAZGO (--verificar: hay endpoints o reglas sin caso)   2 = SIN DATOS

POR QUE EXISTE. El corpus de paridad (bin/paridad.py) tiene que cubrir cada endpoint del slice y cada borde que la
radiografia senalo (una constante con nombre es un umbral; una condicion que frena es un caso de error). Si el
esqueleto lo arma un script desde los hechos de la radiografia, no se olvida ningun endpoint y cada caso cita
archivo:linea. Lo que el script no sabe -ids reales, cuerpos, valores en el borde- queda como <completar>, y lo
completa la skill con una persona, con datos de prueba y marcadores: nunca PHI. Los casos se numeran CP-nn (caso de
paridad); RC-nn son las reglas candidatas de la radiografia, otra cosa. Con --verificar, despues de que la persona
completo y borro, cuenta que cada endpoint y cada regla candidata del slice sigan teniendo un caso (por su archivo:linea).

QUE NO HACE. No corre nada, no adivina valores, no decide que regla importa. Solo biblioteca estandar.
"""

import argparse
import json
import os
import re
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
MUTAN = ('POST', 'PUT', 'PATCH', 'DELETE')


def main():
    ap = argparse.ArgumentParser(description='Esqueleto del corpus de paridad desde la radiografia.')
    ap.add_argument('radiografia')
    ap.add_argument('--slice', required=True, help='modulo de la radiografia (carpeta de primer nivel) que forma el slice')
    ap.add_argument('--salida', default='')
    ap.add_argument('--verificar', default='', help='corpus ya completado: lista endpoints y reglas del slice sin caso')
    a = ap.parse_args()
    try:
        with open(a.radiografia, 'r', encoding='utf-8-sig') as h:
            r = json.load(h)
    except (OSError, ValueError) as e:
        print('SIN DATOS -- no pude leer la radiografia: %s' % e); return SIN_DATOS
    modulos = [m.get('modulo') for m in r.get('modulos', [])]
    if a.slice not in modulos:
        print('SIN DATOS -- el modulo "%s" no esta en la radiografia (hay: %s)' % (a.slice, ', '.join(modulos) or 'ninguno')); return SIN_DATOS
    endpoints = [e for e in r.get('api', []) if e.get('modulo') == a.slice]
    reglas = [rc for rc in r.get('reglas_candidatas', []) if rc.get('modulo') == a.slice]
    if a.verificar:
        try:
            with open(a.verificar, 'r', encoding='utf-8-sig') as h:
                c = json.load(h)
        except (OSError, ValueError) as e:
            print('SIN DATOS -- no pude leer el corpus: %s' % e); return SIN_DATOS
        origenes = set(x.get('origen', '') for x in c.get('casos', []))
        faltan = [('endpoint', '%s %s' % (e.get('metodo'), e.get('ruta')), '%s:%s' % (e.get('archivo'), e.get('linea'))) for e in endpoints if '%s:%s' % (e.get('archivo'), e.get('linea')) not in origenes]
        faltan += [('regla', (rc.get('valor') or rc.get('tipo') or '')[:80], '%s:%s' % (rc.get('archivo'), rc.get('linea'))) for rc in reglas if '%s:%s' % (rc.get('archivo'), rc.get('linea')) not in origenes]
        pend = sum(1 for x in c.get('casos', []) if '<completar' in json.dumps(x, ensure_ascii=False))
        print('%s -- corpus del slice %s: %d caso(s), %d endpoint(s) y %d regla(s) en la radiografia, %d sin caso, %d caso(s) con <completar>' % (
            'HALLAZGO' if (faltan or pend) else 'OK', a.slice, len(c.get('casos', [])), len(endpoints), len(reglas), len(faltan), pend))
        for tipo, que, origen in faltan:
            print('  FALTA %-8s %-60s %s' % (tipo, que, origen))
        if not endpoints and not reglas:
            print('SIN DATOS -- la radiografia no tiene endpoints ni reglas de ese modulo: no hay contra que verificar'); return SIN_DATOS
        return HALLAZGO if (faltan or pend) else OK
    casos, n = [], 0
    for e in r.get('api', []):
        if e.get('modulo') != a.slice:
            continue
        n += 1
        metodo = (e.get('metodo') or 'GET').upper()
        ruta = re.sub(r'\{[^}]+\}|:[A-Za-z_]+', '<completar: id de prueba>', e.get('ruta') or '/')
        casos.append({'id': 'CP-%02d' % n, 'nombre': '%s %s' % (metodo, e.get('ruta')), 'origen': '%s:%s' % (e.get('archivo'), e.get('linea')),
                      'tipo': 'http', 'metodo': metodo, 'ruta': ruta, 'cabeceras': {},
                      'cuerpo': None if metodo in ('GET', 'DELETE') else '<completar: cuerpo de prueba con marcadores, sin PHI>',
                      'muta': metodo in MUTAN, 'regla': ''})
    bordes = 0
    for rc in r.get('reglas_candidatas', []):
        if rc.get('modulo') != a.slice:
            continue
        tipo = rc.get('tipo', '')
        if True:   # los cinco tipos de regla candidata de la radiografia: cada uno es un borde a probar
            n += 1; bordes += 1
            casos.append({'id': 'CP-%02d' % n, 'nombre': '<completar: caso en el borde de %s>' % (rc.get('valor') or tipo)[:80],
                          'origen': '%s:%s' % (rc.get('archivo'), rc.get('linea')), 'tipo': 'http',
                          'metodo': '<completar>', 'ruta': '<completar: endpoint que ejercita esta regla>', 'cabeceras': {},
                          'cuerpo': '<completar>', 'muta': False, 'regla': '<completar: la RN-… confirmada, o la RC-nn candidata>', 'tipo_regla': tipo,
                          'borde': (rc.get('valor') or '')[:160]})
    if not casos:
        print('SIN DATOS -- el modulo "%s" no tiene endpoints ni reglas candidatas en la radiografia: el corpus se arma a mano (casos de comando o de pantalla)' % a.slice); return SIN_DATOS
    corpus = {'slice': a.slice, 'radiografia': os.path.abspath(a.radiografia), 'casos': casos,
              'nota': 'Esqueleto de bin/armar-corpus.py: completar cada <completar>, borrar los casos que no apliquen, y grabar con bin/paridad.py. Sin PHI.'}
    salida = a.salida or os.path.join('borrador', 'paridad', a.slice, 'corpus.json')
    os.makedirs(os.path.dirname(os.path.abspath(salida)) or '.', exist_ok=True)
    with open(salida, 'w', encoding='utf-8', newline='\n') as h:
        json.dump(corpus, h, ensure_ascii=False, indent=1)
        h.write('\n')
    pendientes = sum(1 for c in casos if '<completar' in json.dumps(c, ensure_ascii=False))
    print('OK -- corpus del slice %s en %s: %d caso(s) (%d endpoints, %d bordes), %d con <completar>' % (a.slice, salida, len(casos), len(casos) - bordes, bordes, pendientes))
    print('  Lo que este script NO hace: no inventa ids ni cuerpos; un caso con <completar> no se graba hasta que una persona lo complete.')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
