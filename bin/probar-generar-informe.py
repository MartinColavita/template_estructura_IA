#!/usr/bin/env python3
"""Prueba de bin/generar-informe.py en modo rapido (sin correr pruebas ni Doctor), sobre este repositorio.
Se corre:  python -B bin/probar-generar-informe.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


class Contador(HTMLParser):
    def __init__(self):
        super().__init__()
        self.abiertos, self.secciones, self.svgs, self.errores = [], 0, 0, 0
        self.vacios = {'meta', 'br', 'hr', 'img', 'input', 'link', 'path', 'line', 'rect', 'polygon', 'circle'}

    def handle_starttag(self, tag, attrs):
        if tag == 'section':
            self.secciones += 1
        if tag == 'svg':
            self.svgs += 1
        if tag not in self.vacios:
            self.abiertos.append(tag)

    def handle_endtag(self, tag):
        if tag in self.vacios:
            return
        if self.abiertos and self.abiertos[-1] == tag:
            self.abiertos.pop()
        else:
            self.errores += 1


def main():
    print('== generar-informe')
    tmp = tempfile.mkdtemp(prefix='probar-informe-')
    salida = os.path.join(tmp, 'informe.html')
    r = subprocess.run([sys.executable, '-B', os.path.join(AQUI, 'generar-informe.py'), '--rapido', '--salida', salida],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('corre en modo rapido (0)', r.returncode == 0 and os.path.isfile(salida), (r.stdout + r.stderr)[:300])
    if os.path.isfile(salida):
        with open(salida, 'r', encoding='utf-8') as h:
            t = h.read()
        c = Contador()
        c.feed(t)
        caso('HTML balanceado (sin cierres huerfanos)', c.errores == 0 and not [x for x in c.abiertos if x not in ('html', 'body')], 'errores=%d abiertos=%s' % (c.errores, c.abiertos[-5:]))
        caso('15 secciones con su indice (el prompt maestro arriba de todo)', c.secciones == 15 and t.count('<nav>') == 1 and t.count('href="#') >= 15)
        caso('el prompt maestro esta antes del indice, con boton de copiar y texto pegable', t.find('id="prompt"') < t.find('<nav>') and 'copiarPrompt' in t and 'Arrancá un proyecto con este template' in t)
        caso('diagramas SVG embebidos (al menos 6)', c.svgs >= 6, str(c.svgs))
        skills = [d for d in os.listdir(os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills')) if os.path.isdir(os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', d))]
        faltan = [s for s in skills if ('<h4>%s' % s) not in t]
        caso('nombra las %d skills canonicas' % len(skills), not faltan, str(faltan))
        caso('nombra los scripts, las sondas y las propuestas', 'bin/radiografiar-codigo.py' in t and 'Autocontrol del informe' in t and 'M-001' in t)
        caso('trae bitacora, pendientes y veredicto canonico', 'Bitácora' in t and 'DEC-003' in t and 'VEREDICTO-INICIO' in t)
        caso('sin dependencias externas (ni http en src/href de recursos)', not re.search(r'(src|href)="https?://', t))
        caso('en modo rapido lo dice y no inventa cifras', 'modo rápido' in t and 'no corrido' in t)
    shutil.rmtree(tmp, ignore_errors=True)

    # Cada fila del Doctor muestra el estado de SU sonda, aunque el README y el Doctor las listen en otro orden.
    import importlib.util
    spec = importlib.util.spec_from_file_location('gi', os.path.join(AQUI, 'generar-informe.py'))
    gi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gi)
    hoy = [{'id': 'repos', 'titulo': 'Repos de codigo conectados', 'estado': 'SIN DATOS'},
           {'id': 'tendencia', 'titulo': 'Como venimos', 'estado': 'OK'},
           {'id': 'seguridad', 'titulo': 'seguridad', 'estado': 'SIN DATOS'},   # una sonda que exploto
           {'id': 'calidad', 'titulo': 'Puerta de calidad', 'estado': 'OK'}]
    caso('cada fila muestra SU sonda, por id (aunque el README y el Doctor las listen en otro orden)',
         [(gi.sonda_de_hoy(i, hoy) or {}).get('id') for i in ('tendencia', 'seguridad', 'calidad')] == ['tendencia', 'seguridad', 'calidad'])
    caso('una sonda que hoy no corrio no toma el estado de otra', gi.sonda_de_hoy('contrato', hoy) is None)
    sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'doctor'))
    import doctor as _doc  # noqa: E402
    import codigo as _cod  # noqa: E402  las sondas de los repos de codigo (doctor/codigo.py)
    validos = {f.__name__.replace('sonda_', '') for f in _doc.SONDAS + _cod.SONDAS} | {'tendencia', 'autocontrol'}
    filas = gi.sondas_readme()
    caso('cada fila del README del Doctor tiene el id de una sonda que existe, y estan todas',
         all(f[3] in validos for f in filas) and {f[3] for f in filas} == validos,
         str(sorted({f[3] for f in filas} ^ validos)))

    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
