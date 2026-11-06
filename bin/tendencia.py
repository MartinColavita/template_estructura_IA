#!/usr/bin/env python3
"""Dice en una frase si el ecosistema viene MEJOR o PEOR, comparando las ultimas sesiones con las anteriores.
Lee cerebro-digital/configuracion-ia/sesiones.jsonl (lo escribe bin/registrar-sesion.py). Lo muestra el hook SessionStart.

    python bin/tendencia.py [--sesiones <sesiones.jsonl>] [--n 5] [--breve] [--json]

Tres estados, nunca dos:  0 = mejor o igual   1 = PEOR (hay algo que mirar)   2 = SIN DATOS (menos de 2 sesiones)

QUE COMPARA (por sesion, promedio; en todos "menos es mejor"): bloqueantes por veredicto, SIN DATOS que frenaron por
veredicto, fricciones, preguntas que frenaron, errores de script, Tareas fallidas. Mejor = mas medidas que mejoran que
las que empeoran; peor = al reves; igual = empate o sin cambios. Con la frase van los numeros, para que no sea una
impresion. Lo que empeora es la senal que mejorar-ecosistema usa para proponer un cambio (de a uno, con el si de la persona).

QUE NO HACE. No cambia nada, no propone nada: mide. Solo biblioteca estandar.
"""

import argparse
import json
import os
import sys

OK, PEOR, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIDAS = (('bloqueantes_por_veredicto', 'bloqueantes por veredicto'), ('sin_datos_por_veredicto', 'SIN DATOS que frenaron por veredicto'),
           ('fricciones', 'fricciones por sesion'), ('preguntas_bloqueantes', 'preguntas que frenaron por sesion'),
           ('errores_de_script', 'errores de script por sesion'), ('tareas_fallidas', 'Tareas fallidas por sesion'))


def leer(p):
    filas = []
    with open(p, 'r', encoding='utf-8', errors='replace') as h:
        for l in h:
            l = l.strip()
            if not l:
                continue
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get('escrito_por') == 'bin/registrar-sesion.py':
                filas.append(d)
    filas.sort(key=lambda d: d.get('fecha', ''))
    return filas


def promedio(filas, clave):
    if not filas:
        return 0.0
    if clave == 'bloqueantes_por_veredicto':
        v = sum(f.get('veredictos', 0) for f in filas)
        return (sum(f.get('bloqueantes', 0) for f in filas) / v) if v else 0.0
    if clave == 'sin_datos_por_veredicto':
        v = sum(f.get('veredictos', 0) for f in filas)
        return (sum(f.get('sin_datos_no_mirado', 0) for f in filas) / v) if v else 0.0
    return sum(f.get(clave, 0) for f in filas) / len(filas)


def fmt(x):
    return ('%.1f' % x).replace('.', ',')


def main():
    ap = argparse.ArgumentParser(description='Mejor o peor: tendencia de las ultimas sesiones.')
    ap.add_argument('--sesiones', default=os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'sesiones.jsonl'))
    ap.add_argument('--n', type=int, default=5)
    ap.add_argument('--breve', action='store_true', help='una sola linea (para el hook de inicio de sesion)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not os.path.isfile(a.sesiones):
        print('SIN DATOS -- todavia no hay sesiones registradas (%s): la primera linea la deja el hook SessionEnd' % a.sesiones); return SIN_DATOS
    filas = leer(a.sesiones)
    if len(filas) < 2:
        print('SIN DATOS -- %d sesion(es) registrada(s); hacen falta al menos 2 para comparar' % len(filas)); return SIN_DATOS
    n = max(1, min(a.n, len(filas) // 2))
    ultimas, anteriores = filas[-n:], filas[:-n][-n:] if len(filas) > n else filas[:-n]
    if not anteriores:
        anteriores = filas[:-n] or filas[:1]
    mejoran, empeoran, detalle = [], [], []
    for clave, nombre in MEDIDAS:
        antes, ahora = promedio(anteriores, clave), promedio(ultimas, clave)
        detalle.append({'medida': nombre, 'antes': round(antes, 2), 'ahora': round(ahora, 2)})
        if ahora < antes - 1e-9:
            mejoran.append('%s %s -> %s' % (nombre, fmt(antes), fmt(ahora)))
        elif ahora > antes + 1e-9:
            empeoran.append('%s %s -> %s' % (nombre, fmt(antes), fmt(ahora)))
    veredicto = 'MEJOR' if len(mejoran) > len(empeoran) else ('PEOR' if len(empeoran) > len(mejoran) else 'IGUAL')
    skills = {}
    for f in ultimas:
        for k, v in (f.get('skills') or {}).items():
            skills[k] = skills.get(k, 0) + v
    frase = 'Ultimas %d sesion(es): %s que las %d anteriores.' % (len(ultimas), veredicto, len(anteriores))
    if mejoran:
        frase += ' Mejora: ' + '; '.join(mejoran) + '.'
    if empeoran:
        frase += ' Empeora: ' + '; '.join(empeoran) + '.'
    if not mejoran and not empeoran:
        frase += ' Sin cambios en las seis medidas.'
    if a.json:
        print(json.dumps({'veredicto': veredicto, 'ultimas': len(ultimas), 'anteriores': len(anteriores), 'detalle': detalle, 'skills_ultimas': skills, 'frase': frase}, ensure_ascii=False, indent=1))
    elif a.breve:
        print('[tendencia] ' + frase)
    else:
        print('%s -- %s' % (veredicto, frase))
        for d in detalle:
            print('  %-42s antes %6s   ahora %6s' % (d['medida'], fmt(d['antes']), fmt(d['ahora'])))
        if skills:
            print('  skills mas usadas en las ultimas: ' + ', '.join('%s (%d)' % (k, v) for k, v in sorted(skills.items(), key=lambda x: -x[1])[:6]))
        if veredicto == 'PEOR':
            print('  Que hacer: mejorar-ecosistema mira que cambio en las sesiones que empeoran y propone UN ajuste; la persona decide.')
        print('  Lo que este script NO mira: por que paso cada cosa; eso es criterio (las fricciones de los agentes y los veredictos lo dicen).')
    return PEOR if veredicto == 'PEOR' else OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
