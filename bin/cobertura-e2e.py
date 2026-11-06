#!/usr/bin/env python3
"""Matriz Historia -> Escenario -> prueba de punta a punta: que Escenarios tienen prueba automatizada, cuales solo
esqueleto (fixme/skip) y cuales ninguna. SOLO LECTURA.

    python bin/cobertura-e2e.py <carpeta de pruebas e2e> --historias <cerebro-digital/<modulo>/backlog | archivo.md ...> [--json] [--mermaid]

Tres estados, nunca dos:  0 = OK (todos los Escenarios automatizados)   1 = HALLAZGO (hay Escenarios sin prueba o solo esqueleto)
                          2 = SIN DATOS (no hay Historias con Gherkin, o la carpeta no existe)

POR QUE EXISTE. "Tiene pruebas de punta a punta" es una opinion hasta que alguien cuenta Escenario por Escenario. Esto lo
cuenta: lee las Historias (del tablero local o de archivos), saca sus Escenarios, y busca en las pruebas la traza fija
`Historia #<id> · Escenario: <titulo>` que escribe bin/armar-e2e.py (y que una prueba hecha a mano tambien puede llevar).
Una traza seguida de test.fixme / unittest.skip / test.skip es ESQUELETO, no prueba. Vale para cualquier motor
(Playwright, unittest, lo que sea): mira texto, no ejecuta nada.

QUE NO HACE. No corre las pruebas (si pasan contra el ambiente lo dice el runner, no esto), no juzga si los pasos
siguen al Gherkin (eso es criterio). Solo biblioteca estandar.
"""

import argparse
import glob
import json
import os
import re
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
MEDIO = '·'
ESC = re.compile(r'^\s*(?:Escenario|Esquema del escenario)\s*:\s*(.+?)\s*$', re.I)
PASO = re.compile(r'^\s*(Dado|Cuando|Entonces|Y|Pero|Dados|Dada|Dadas)\b', re.I)
TRAZA = re.compile(r'Historia\s*#(\d+)\s*[%s·\-|]\s*Escenario\s*:\s*(.+?)\s*$' % MEDIO, re.I)
MARCA_ESQUELETO = re.compile(r'test\.fixme|test\.skip|unittest\.skip|@skip|pytest\.mark\.skip|it\.skip|xit\(|xtest\(')
EXT = ('.spec.ts', '.test.ts', '.spec.js', '.test.js', '.py', '.feature', '.cs', '.java', '.kt')


def leer(p):
    with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def escenarios_de(texto):
    fm = re.match(r'---\n(.*?)\n---', texto, re.S)
    hid, titulo, tipo = '', '', ''
    if fm:
        mi = re.search(r'^id:\s*(\d+)\s*$', fm.group(1), re.M); hid = mi.group(1) if mi else ''
        mt = re.search(r'^(?:titulo|title):\s*"?(.+?)"?\s*$', fm.group(1), re.M); titulo = mt.group(1) if mt else ''
        mk = re.search(r'^tipo:\s*(.+?)\s*$', fm.group(1), re.M); tipo = mk.group(1) if mk else ''
    if not titulo:
        mh = re.search(r'^#\s+(.+?)\s*$', texto, re.M); titulo = mh.group(1) if mh else ''
    escs = [m.group(1) for m in (ESC.match(l) for l in texto.split('\n')) if m]
    return hid, titulo, tipo, escs


def historias(fuentes):
    out = []
    for f in fuentes:
        archivos = sorted(glob.glob(os.path.join(f, '*.md'))) if os.path.isdir(f) else [f]
        for p in archivos:
            hid, titulo, tipo, escs = escenarios_de(leer(p))
            if tipo and tipo.lower() not in ('historia', 'historia de usuario', 'user story'):
                continue
            if escs:
                out.append({'id': hid, 'titulo': titulo, 'archivo': p, 'escenarios': escs})
    return out


def trazas(carpeta):
    """{(id, titulo_escenario_normalizado): 'automatizada' | 'esqueleto'}"""
    out = {}
    for base, dirs, files in os.walk(carpeta):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', 'test-results', 'playwright-report')]
        for f in files:
            if not f.endswith(EXT):
                continue
            lineas = leer(os.path.join(base, f)).split('\n')
            for i, l in enumerate(lineas):
                m = TRAZA.search(l)
                if not m:
                    continue
                # la ventana del Escenario termina en la proxima traza (o a las 12 lineas): el fixme de otro test no cuenta
                fin = i + 1
                while fin < len(lineas) and fin < i + 12 and not TRAZA.search(lineas[fin]):
                    fin += 1
                ventana = '\n'.join(lineas[i:fin])
                estado = 'esqueleto' if MARCA_ESQUELETO.search(ventana) else 'automatizada'
                clave = (m.group(1), norm(m.group(2)))
                if out.get(clave) != 'automatizada':
                    out[clave] = estado
    return out


def norm(s):
    return re.sub(r'\s+', ' ', s.strip().strip('"\'`')).lower()


def main():
    ap = argparse.ArgumentParser(description='Cobertura de punta a punta por Historia y Escenario.')
    ap.add_argument('carpeta')
    ap.add_argument('--historias', nargs='+', required=True, help='carpeta backlog/ del tablero local, o archivos .md de Historias')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--mermaid', action='store_true')
    a = ap.parse_args()
    if not os.path.isdir(a.carpeta):
        print('SIN DATOS -- no existe la carpeta de pruebas %s' % a.carpeta); return SIN_DATOS
    hs = historias(a.historias)
    if not hs:
        print('SIN DATOS -- ninguna Historia con Escenarios en Gherkin en %s' % ', '.join(a.historias)); return SIN_DATOS
    tz = trazas(a.carpeta)
    filas, totales = [], {'automatizada': 0, 'esqueleto': 0, 'sin prueba': 0}
    for h in hs:
        for e in h['escenarios']:
            estado = tz.get((h['id'], norm(e)), 'sin prueba')
            totales[estado] += 1
            filas.append({'historia': h['id'], 'titulo': h['titulo'], 'escenario': e, 'estado': estado})
    veredicto = 'OK' if totales['esqueleto'] == 0 and totales['sin prueba'] == 0 else 'HALLAZGO'
    if a.json:
        print(json.dumps({'veredicto': veredicto, 'totales': totales, 'filas': filas}, ensure_ascii=False, indent=1)); return OK if veredicto == 'OK' else HALLAZGO
    print('%s -- %d Historia(s), %d Escenario(s): %d automatizado(s), %d solo esqueleto, %d sin prueba' % (
        veredicto, len(hs), len(filas), totales['automatizada'], totales['esqueleto'], totales['sin prueba']))
    for f in filas:
        print('  %-13s #%-4s %s' % (f['estado'], f['historia'], f['escenario'][:90]))
    if a.mermaid:
        print('\n```mermaid\npie title Escenarios de punta a punta')
        for k, v in totales.items():
            print('  "%s" : %d' % (k, v))
        print('```')
    print('  Lo que este script NO mira: si las pruebas pasan contra el ambiente (eso lo dice el runner) ni si sus pasos siguen al Gherkin (criterio).')
    return OK if veredicto == 'OK' else HALLAZGO


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
