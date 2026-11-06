#!/usr/bin/env python3
"""Arma el ESQUELETO de las pruebas de punta a punta de UNA Historia, a partir de su Gherkin. No inventa pasos.

    python bin/armar-e2e.py <#id del tablero local | archivo.md de la Historia> --motor playwright|proceso|http
                            [--salida qa/<app>-e2e/tests] [--nucleo <raiz>] [--url <base de la app>]

Tres estados, nunca dos:  0 = esqueleto armado (o ya existia y esta completo)   1 = HALLAZGO (el archivo existe y le faltan Escenarios)
                          2 = SIN DATOS (la Historia no tiene Gherkin, no existe, o el motor no se reconoce)

POR QUE EXISTE. La prueba de aceptacion de una Historia es su Gherkin ejecutado de afuera, con el titulo textual de cada
Escenario y el #ID de la Historia como traza. Si el esqueleto lo arma un script, no se olvida ningun Escenario, la traza
queda escrita con un formato fijo (la lee bin/cobertura-e2e.py) y los pasos del Gherkin viajan como comentarios, para
que quien automatiza no los reescriba de memoria. Cada Escenario nace MARCADO como sin automatizar (fixme/skip): el
esqueleto no es verde falso.

EL MOTOR lo fija DEC-003 segun el tipo de aplicacion:
  playwright  app web, Electron, o el front de una app de escritorio con webview probado en navegador -> <slug>.spec.ts
  proceso     app de linea de comandos o de escritorio sin navegador (se ejecuta y se observa salida/archivos) -> <slug>.test.py (unittest)
  http        API sin pantalla -> <slug>.test.py (unittest + urllib contra E2E_BASE_URL)
Para escritorio nativo (WinAppDriver), Tauri por WebDriver o movil (Appium, Maestro) no hay esqueleto propio: se usa
"proceso" como molde y la skill automatizar-e2e dice como se adapta.

LA TRAZA, en todos los motores, es una linea por Escenario:   Historia #<id> · Escenario: <titulo textual>

QUE NO HACE. No escribe pasos ejecutables, no instala nada, no corre nada, no pisa un archivo que ya existe (lo compara
y dice que Escenarios le faltan). Solo biblioteca estandar. ASCII en el codigo.
"""

import argparse
import glob
import os
import re
import sys
import unicodedata

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIO = '·'
PASO = re.compile(r'^\s*(Dado|Cuando|Entonces|Y|Pero|Dados|Dada|Dadas)\b', re.I)
ESC = re.compile(r'^\s*(?:Escenario|Esquema del escenario)\s*:\s*(.+?)\s*$', re.I)


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60] or 'historia'


def leer(p):
    with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def buscar_historia(ref, nucleo):
    """#id -> archivo del tablero local (cerebro-digital/<modulo>/backlog/); ruta -> tal cual."""
    if os.path.isfile(ref):
        return ref
    m = re.match(r'^#?(\d+)$', ref.strip())
    if not m:
        return None
    for p in glob.glob(os.path.join(nucleo, 'cerebro-digital', '*', 'backlog', '*.md')):
        t = leer(p)
        fm = re.match(r'---\n(.*?)\n---', t, re.S)
        if fm and re.search(r'^id:\s*%s\s*$' % m.group(1), fm.group(1), re.M):
            return p
    return None


def parsear(texto):
    """Devuelve (id, titulo, [(titulo_escenario, [pasos])])."""
    fm = re.match(r'---\n(.*?)\n---', texto, re.S)
    hid, titulo = '', ''
    if fm:
        mi = re.search(r'^id:\s*(\d+)\s*$', fm.group(1), re.M)
        mt = re.search(r'^(?:titulo|title):\s*"?(.+?)"?\s*$', fm.group(1), re.M)
        hid, titulo = (mi.group(1) if mi else ''), (mt.group(1) if mt else '')
    if not titulo:
        mh = re.search(r'^#\s+(.+?)\s*$', texto, re.M)
        titulo = re.sub(r'^(Historia|HU)\s*#?\d*\s*[:\-]?\s*', '', mh.group(1)) if mh else 'Historia'
    if not hid:
        mh = re.search(r'#(\d+)', texto)
        hid = mh.group(1) if mh else ''
    escenarios, actual = [], None
    for linea in texto.split('\n'):
        me = ESC.match(linea)
        if me:
            actual = (me.group(1), [])
            escenarios.append(actual)
            continue
        if actual is not None:
            if PASO.match(linea):
                actual[1].append(linea.strip())
            elif linea.strip() == '' or linea.startswith('#') or linea.startswith('|'):
                if actual[1]:
                    actual = None
    return hid, titulo, escenarios


NOTAS_QA = (('pantalla', r'pantalla\s*/\s*ruta'), ('rol', r'rol\s*/?\s*usuario'), ('datos', r'datos iniciales'), ('identificadores', r'identificadores'), ('ambiente', r'ambiente'))


def notas_qa(texto):
    """Las cinco lineas fijas de 'Notas para QA' de la Historia: {clave: valor} (solo las que tienen valor real)."""
    m = re.search(r'^##\s*Notas para QA\s*$(.*?)(?=^##\s|\Z)', texto, re.M | re.S)
    out = {}
    if not m:
        return out
    for linea in m.group(1).split('\n'):
        ml = re.match(r'^\s*-\s*\*\*([^*]+)\*\*\s*:?\s*(.*)$', linea)
        if not ml:
            continue
        rotulo, valor = ml.group(1).strip().lower(), ml.group(2).strip().strip('`')
        for clave, patron in NOTAS_QA:
            if re.search(patron, rotulo) and valor and not valor.startswith('<') and '\u26a0' not in valor:
                out[clave] = valor
    return out


def ruta_de(notas):
    m = re.search(r'(/[\w./{}\-]*)', notas.get('pantalla', ''))
    return m.group(1) if m else ''


def traza(hid, esc):
    return 'Historia #%s %s Escenario: %s' % (hid, MEDIO, esc)


def comentarios_qa(notas, pref):
    L = []
    for clave, rotulo in (('pantalla', 'Pantalla / ruta'), ('rol', 'Rol / usuario de prueba'), ('datos', 'Datos iniciales'), ('identificadores', 'Identificadores'), ('ambiente', 'Ambiente')):
        if clave in notas:
            L.append('%s %s: %s' % (pref, rotulo, notas[clave]))
    return L


def playwright(hid, titulo, escenarios, url, notas=None):
    notas = notas or {}
    L = ["import { test, expect } from '@playwright/test';", '',
         '// Historia #%s %s %s' % (hid, MEDIO, titulo),
         '// Esqueleto de bin/armar-e2e.py: cada Escenario nace marcado como sin automatizar hasta que se escriba; los pasos del Gherkin',
         '// son la fuente (no se inventan otros). Identificadores: los que fija DEC-003 (data-testid o automation-id).',
         "const BASE = process.env.E2E_BASE_URL ?? '%s';" % (url or 'http://127.0.0.1:3000'),
         "const RUTA = '%s';   // de las Notas para QA de la Historia" % ruta_de(notas)] + comentarios_qa(notas, '//') + ['',
         "test.describe('Historia #%s %s %s', () => {" % (hid, MEDIO, titulo.replace("'", "\\'"))]
    for esc, pasos in escenarios:
        L.append('  // %s' % traza(hid, esc))
        L.append("  test('Escenario: %s', async ({ page }) => {" % esc.replace("'", "\\'"))
        for p in pasos:
            L.append('    // %s' % p)
        L.append("    test.fixme(true, 'sin automatizar todavia: escribir los pasos de arriba');")
        L.append('    await page.goto(BASE + RUTA);')
        L.append('    await expect(page).toHaveTitle(/.+/);')
        L.append('  });')
        L.append('')
    L.append('});')
    return '\n'.join(L) + '\n'


def unittest_py(hid, titulo, escenarios, motor, url, notas=None):
    notas = notas or {}
    L = ['"""Historia #%s %s %s' % (hid, MEDIO, titulo)] + comentarios_qa(notas, '') + [
         'Esqueleto de bin/armar-e2e.py (motor %s): cada Escenario nace con unittest.skip hasta que se automatice.' % motor,
         'Los pasos del Gherkin son la fuente; no se inventan otros."""',
         'import os', 'import unittest']
    if motor == 'proceso':
        L += ['import subprocess', '', "COMANDO = os.environ.get('E2E_COMANDO', '<completar: ejecutable de la aplicacion>')", '']
    else:
        L += ['import json', 'import urllib.request', '', "BASE = os.environ.get('E2E_BASE_URL', '%s')" % (url or 'http://127.0.0.1:8000'), '',
              'def pedir(metodo, ruta, cuerpo=None):',
              "    datos = json.dumps(cuerpo).encode('utf-8') if cuerpo is not None else None",
              "    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo, headers={'Content-Type': 'application/json'})",
              '    with urllib.request.urlopen(req, timeout=15) as r:',
              "        return r.status, json.loads(r.read().decode('utf-8') or 'null')", '']
    L += ['', 'class Historia%s(unittest.TestCase):' % (hid or 'X'), '    """%s"""' % titulo, '']
    for i, (esc, pasos) in enumerate(escenarios, 1):
        L.append('    # %s' % traza(hid, esc))
        L.append("    @unittest.skip('sin automatizar todavia: escribir los pasos del docstring')")
        L.append('    def test_%02d_%s(self):' % (i, slug(esc).replace('-', '_')[:50]))
        L.append('        """%s' % esc)
        for p in pasos:
            L.append('        %s' % p)
        L.append('        """')
        if motor == 'proceso':
            L.append("        r = subprocess.run([COMANDO], capture_output=True, text=True, timeout=60)")
            L.append('        self.assertEqual(r.returncode, 0)')
        else:
            L.append("        estado, cuerpo = pedir('GET', '/')")
            L.append('        self.assertEqual(estado, 200)')
        L.append('')
    L += ['', "if __name__ == '__main__':", '    unittest.main()']
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description='Esqueleto de pruebas de punta a punta desde el Gherkin de una Historia.')
    ap.add_argument('historia', help='#id del tablero local o archivo .md con la Historia')
    ap.add_argument('--motor', choices=['playwright', 'proceso', 'http'], required=True)
    ap.add_argument('--salida', default='', help='carpeta de las pruebas (por defecto qa/e2e/tests)')
    ap.add_argument('--nucleo', default=RAIZ)
    ap.add_argument('--url', default='', help='URL base de la app (queda como valor por defecto en el archivo)')
    a = ap.parse_args()
    p = buscar_historia(a.historia, a.nucleo)
    if not p:
        print('SIN DATOS -- no encontre la Historia %s (ni como archivo ni como #id del tablero local bajo %s)' % (a.historia, a.nucleo)); return SIN_DATOS
    texto_h = leer(p)
    hid, titulo, escenarios = parsear(texto_h)
    notas = notas_qa(texto_h)
    faltan_qa = [r for c, r in (('pantalla', 'pantalla / ruta'), ('rol', 'rol / usuario de prueba'), ('datos', 'datos iniciales'), ('identificadores', 'identificadores estables'), ('ambiente', 'ambiente')) if c not in notas]
    if not escenarios:
        print('SIN DATOS -- la Historia %s no tiene Escenarios en Gherkin (Escenario: ... con Dado/Cuando/Entonces): redactar los Criterios de aceptacion primero (redactar-tarea)' % (hid or p)); return SIN_DATOS
    sin_pasos = [e for e, pasos in escenarios if not pasos]
    salida = a.salida or os.path.join(a.nucleo, 'qa', 'e2e', 'tests')
    nombre = ('historia-%s-%s' % (hid, slug(titulo))) if hid else slug(titulo)
    archivo = os.path.join(salida, nombre + ('.spec.ts' if a.motor == 'playwright' else '.test.py'))
    if os.path.isfile(archivo):
        existente = leer(archivo)
        faltan = [e for e, _ in escenarios if traza(hid, e) not in existente]
        if faltan:
            print('HALLAZGO -- %s ya existe y le faltan %d Escenario(s) de la Historia (no se pisa):' % (archivo, len(faltan)))
            for e in faltan:
                print('  FALTA  %s' % traza(hid, e))
            return HALLAZGO
        print('OK -- %s ya existe y tiene los %d Escenarios de la Historia #%s (no se toca)' % (archivo, len(escenarios), hid)); return OK
    contenido = playwright(hid, titulo, escenarios, a.url, notas) if a.motor == 'playwright' else unittest_py(hid, titulo, escenarios, a.motor, a.url, notas)
    os.makedirs(salida, exist_ok=True)
    with open(archivo, 'w', encoding='utf-8', newline='\n') as h:
        h.write(contenido)
    print('OK -- esqueleto de la Historia #%s (%s) en %s: %d Escenario(s), todos marcados sin automatizar%s' % (
        hid, titulo, archivo, len(escenarios), ('; %d sin pasos en el Gherkin (hueco de la Historia, no de la prueba): %s' % (len(sin_pasos), ', '.join(sin_pasos))) if sin_pasos else ''))
    if faltan_qa:
        print('  AVISO la Historia no trae en sus Notas para QA: %s. Son datos de la prueba de punta a punta: se piden a la Historia (comentar-tarea), no se inventan.' % ', '.join(faltan_qa))
    print('  Lo que este script NO hace: no escribe pasos ejecutables ni inventa datos; lo que el Gherkin no dice vuelve como pregunta a la Historia.')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
