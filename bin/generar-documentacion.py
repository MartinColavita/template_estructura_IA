#!/usr/bin/env python3
"""Genera la documentacion de la APLICACION (no del esqueleto) a partir del Cerebro: la guia de uso para personas
y la documentacion tecnica y funcional (la bitacora completa). HTML autocontenido, con indice y diagramas SVG.

    python -B bin/generar-documentacion.py --tipo manual  [--modulo <slug>] [--salida borrador/documentacion/guia-de-uso.html]
    python -B bin/generar-documentacion.py --tipo tecnica [--modulo <slug>] [--app <ruta del repo de codigo>] [--salida ...]

Tres estados, nunca dos:  0 = documento escrito   1 = (no aplica)   2 = SIN DATOS (no hay Cerebro o no hay fichas)

POR QUE EXISTE. Al cerrar una aplicacion (o un slice) hacen falta dos cosas que nadie escribe a mano a tiempo: una
guia simple para empezar a usarla, por pasos y con pantallas, y la documentacion tecnica y funcional completa. Las
dos salen de lo que el Cerebro YA tiene: las fichas de flujo (proposito, pasos, reglas, pantalla, glosario), el
contexto, las decisiones, el mapa de la aplicacion, los aprendizajes, la deuda, los pendientes resueltos (las
preguntas frecuentes), la bitacora (log.md y el tablero local) y, si se pasa --app, la radiografia del codigo
(modulos, tablas, endpoints, integraciones). El script arma la estructura, el indice y los diagramas; lo que no
esta en el Cerebro queda marcado <completar>, nunca inventado. La skill documentar-aplicacion pule la prosa.

QUE NO HACE. No lee el codigo salvo por la radiografia; no inventa pasos ni reglas; no escribe en el Cerebro. Las
pantallas son las que cita cada ficha en fuente_maqueta (PNG o HTML en entregables/disenos/); los diagramas
interactivos de Archify se enlazan si estan en borrador/diagramas/. Solo biblioteca estandar.
"""

import argparse
import datetime
import glob
import html
import json
import os
import re
import subprocess
import sys

OK, _, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leer(p):
    with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def frontmatter(texto):
    m = re.match(r'---\n(.*?)\n---\n', texto, re.S)
    if not m:
        return {}, texto
    d = {}
    for l in m.group(1).split('\n'):
        mm = re.match(r'^([A-Za-z_]+):\s*(.*)$', l)
        if mm:
            d[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return d, texto[m.end():]


def secciones(cuerpo):
    """{titulo de seccion ## : texto} en orden."""
    out = {}
    actual = None
    for l in cuerpo.split('\n'):
        m = re.match(r'^## (.+?)\s*$', l)
        if m:
            actual = m.group(1).strip()
            out[actual] = []
        elif actual is not None:
            out[actual].append(l)
    return {k: '\n'.join(v).strip() for k, v in out.items()}


def buscar_seccion(secs, *claves):
    for k, v in secs.items():
        kk = k.lower()
        if any(c in kk for c in claves):
            return v
    return ''


def pasos_de(texto):
    pasos = []
    for l in texto.split('\n'):
        m = re.match(r'^\s*(\d+)[.)]\s+(.*)$', l)
        if m and not m.group(2).strip().startswith('<Paso'):
            pasos.append(m.group(2).strip())
    return pasos


def filas_tabla(texto):
    filas = []
    for l in texto.split('\n'):
        if l.startswith('|') and not re.match(r'^\|\s*-', l):
            celdas = [c.strip() for c in l.strip().strip('|').split('|')]
            filas.append(celdas)
    return filas[1:] if filas else []


def reglas_de(texto):
    out = []
    for m in re.finditer(r'^### (RN-[A-Z0-9-]+)\s*—\s*(.+?)\n(.*?)(?=^### |\Z)', texto, re.S | re.M):
        cuerpo = re.sub(r'_Últ\. modif\..*?_', '', m.group(3), flags=re.S).strip()
        parrafo = next((p.strip() for p in cuerpo.split('\n\n') if p.strip() and not p.strip().startswith('<')), '')
        out.append((m.group(1), m.group(2).strip(), parrafo[:400]))
    return out


def quitar_marcadores(s):
    return re.sub(r'<[^>\n]{2,60}>', lambda m: '<span class="completar">' + html.escape(m.group(0)) + '</span>', html.escape(s)).replace('&lt;span class=&quot;completar&quot;&gt;', '<span class="completar">').replace('&lt;/span&gt;', '</span>')


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[\[([^\]|#]+)(#[^\]]+)?\]\]', r'<i>\1</i>', s)
    s = re.sub(r'&lt;(completar[^&]*|[^&]{2,60})&gt;', r'<span class="completar">&lt;\1&gt;</span>', s)
    return s


def modulo_de(raiz, slug):
    cd = os.path.join(raiz, 'cerebro-digital')
    if slug:
        return os.path.join(cd, slug)
    cands = [d for d in glob.glob(os.path.join(cd, '*')) if os.path.isdir(os.path.join(d, 'funcional'))]
    return cands[0] if len(cands) == 1 else None


def cargar(raiz, mod):
    datos = {'fichas': [], 'contexto': {}, 'decisiones': [], 'mapa': {}, 'aprendizajes': [], 'deuda': [], 'pendientes': {'abiertas': [], 'resueltas': []},
             'log': [], 'backlog': [], 'glosario': [], 'diagramas': [], 'modulo': os.path.basename(mod)}
    for p in sorted(glob.glob(os.path.join(mod, 'funcional', '*.md'))):
        nombre = os.path.basename(p)
        if nombre == 'index.md' or nombre.startswith('plantilla'):
            continue
        fm, cuerpo = frontmatter(leer(p))
        if fm.get('tipo') not in ('flujo', 'funcional', 'reglas-de-negocio'):
            continue
        secs = secciones(cuerpo)
        ficha = {'archivo': nombre, 'titulo': fm.get('title', nombre[:-3]), 'estado': fm.get('estado', ''), 'maqueta': fm.get('fuente_maqueta', ''),
                 'proposito': buscar_seccion(secs, 'propósito', 'proposito'), 'pasos': pasos_de(buscar_seccion(secs, 'flujo')),
                 'reglas': reglas_de(buscar_seccion(secs, 'reglas')), 'pantalla': buscar_seccion(secs, 'pantalla'),
                 'glosario': filas_tabla(buscar_seccion(secs, 'glosario')), 'dudas': buscar_seccion(secs, 'dudas')}
        datos['fichas'].append(ficha)
        datos['glosario'] += [f for f in ficha['glosario'] if len(f) >= 2 and not f[0].startswith('<')]
    ctx = os.path.join(raiz, 'cerebro-digital', 'contexto.md')
    if os.path.isfile(ctx):
        _, cuerpo = frontmatter(leer(ctx))
        secs = secciones(cuerpo)
        datos['contexto'] = {'proposito': buscar_seccion(secs, 'propósito', 'proposito'), 'alcance': buscar_seccion(secs, 'alcance'),
                             'integraciones': filas_tabla(buscar_seccion(secs, 'integraciones')), 'principios': buscar_seccion(secs, 'principios')}
    dec = os.path.join(mod, 'arquitectura', 'decisiones.md')
    if os.path.isfile(dec):
        t = leer(dec)
        for m in re.finditer(r'^## (DEC-\d+) — (.+?)\n(.*?)(?=^## DEC-|\Z)', t, re.S | re.M):
            est = re.search(r'\*\*Estado:\*\*\s*(.+)', m.group(3))
            datos['decisiones'].append((m.group(1), m.group(2).strip(), re.sub(r'\*\*', '', est.group(1)).strip()[:140] if est else '—'))
    for nombre, clave in (('mapa.md', 'mapa'), ('aprendizajes.md', 'aprendizajes'), ('deuda.md', 'deuda')):
        p = os.path.join(mod, 'aplicacion', nombre)
        if os.path.isfile(p):
            _, cuerpo = frontmatter(leer(p))
            if clave == 'mapa':
                secs = secciones(cuerpo)
                datos['mapa'] = {k: [f for f in filas_tabla(v) if f and not f[0].startswith('`<') and not f[0].startswith('<')] for k, v in secs.items()}
            else:
                datos[clave] = [f for f in filas_tabla(cuerpo) if f and re.match(r'(AP|DT)-\d+', f[0])]
    pen = os.path.join(mod, 'pendientes.md')
    if os.path.isfile(pen):
        _, cuerpo = frontmatter(leer(pen))
        secs = secciones(cuerpo)
        datos['pendientes']['abiertas'] = [f for f in filas_tabla(buscar_seccion(secs, 'abiertas')) if f and re.match(r'P-\d+', f[0]) and not f[1].startswith('<')]
        datos['pendientes']['resueltas'] = [f for f in filas_tabla(buscar_seccion(secs, 'resueltas')) if f and re.match(r'P-\d+', f[0])]
    lg = os.path.join(raiz, 'cerebro-digital', 'log.md')
    if os.path.isfile(lg):
        _, cuerpo = frontmatter(leer(lg))
        for m in re.finditer(r'^## (\d{4}-\d{2}-\d{2})\s*\(?(.*?)\)?\s*\n(.*?)(?=^## \d{4}|\Z)', cuerpo, re.S | re.M):
            datos['log'].append((m.group(1), m.group(2).strip(), re.sub(r'\s+', ' ', m.group(3)).strip()[:400]))
    for p in sorted(glob.glob(os.path.join(mod, 'backlog', '[0-9]*.md'))):
        fm, _ = frontmatter(leer(p))
        datos['backlog'].append({'id': fm.get('id', ''), 'tipo': fm.get('tipo', ''), 'estado': fm.get('estado', ''), 'titulo': fm.get('titulo', ''), 'actualizado': fm.get('actualizado', '')})
    datos['diagramas'] = sorted(os.path.relpath(p, raiz).replace(os.sep, '/') for p in glob.glob(os.path.join(raiz, 'borrador', 'diagramas', '*.html')))
    return datos


def radiografia(app):
    if not app:
        return None
    r = subprocess.run([sys.executable, '-I', os.path.join(RAIZ, 'bin', 'radiografiar-codigo.py'), app, '--json'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        return json.loads(r.stdout) if r.returncode == 0 else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------------------------- SVG
def _t(x, y, s, cls='', anchor='middle'):
    return '<text x="%d" y="%d" text-anchor="%s" class="%s">%s</text>' % (x, y, anchor, cls, html.escape(s))


def recortar(s, n):
    return s if len(s) <= n else s[:n - 1] + '…'


def svg_pasos(pasos, por_fila=4):
    if not pasos:
        return ''
    ancho, alto, gap, salto = 220, 70, 30, 100
    filas = [pasos[i:i + por_fila] for i in range(0, len(pasos), por_fila)]
    W = por_fila * ancho + (por_fila - 1) * gap + 20
    H = len(filas) * salto + 10
    out = ['<svg viewBox="0 0 %d %d" class="diagrama" role="img" aria-label="pasos">' % (W, H),
           '<defs><marker id="fp" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="flecha"/></marker></defs>']
    k = 0
    for fi, fila in enumerate(filas):
        y = 10 + fi * salto
        for ci, paso in enumerate(fila):
            k += 1
            x = 10 + ci * (ancho + gap)
            out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" class="caja %s"/>' % (x, y, ancho, alto, 'acento' if k == 1 else ''))
            out.append('<circle cx="%d" cy="%d" r="12" class="num"/>' % (x + 18, y + 20))
            out.append(_t(x + 18, y + 25, str(k), 'num-t'))
            palabras = re.sub(r'\*\*|`', '', paso).split()
            l1, l2 = '', ''
            for p in palabras:
                if len(l1) + len(p) < 26:
                    l1 += p + ' '
                elif len(l2) + len(p) < 26:
                    l2 += p + ' '
                else:
                    l2 = l2.rstrip() + '…'
                    break
            out.append(_t(x + 118, y + 30, l1.strip(), 'caja-s'))
            out.append(_t(x + 118, y + 50, l2.strip(), 'caja-s'))
            if ci < len(fila) - 1:
                out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="linea" marker-end="url(#fp)"/>' % (x + ancho, y + alto // 2, x + ancho + gap - 2, y + alto // 2))
        if fi < len(filas) - 1:
            xe = 10 + (len(fila) - 1) * (ancho + gap) + ancho // 2
            out.append('<path d="M%d,%d V%d H%d V%d" class="linea" fill="none" marker-end="url(#fp)"/>' % (xe, y + alto, y + alto + 15, 10 + ancho // 2, y + salto - 3))
    out.append('</svg>')
    return '\n'.join(out)


def svg_modulos(rad):
    import math
    mods = [m['modulo'] for m in rad.get('modulos', []) if m['modulo'] != '(raiz)'][:14]
    if not mods:
        return ''
    n = len(mods)
    cx, cy, R = 450, 230, 170
    pos = {m: (cx + R * math.cos(2 * math.pi * i / n - math.pi / 2), cy + R * math.sin(2 * math.pi * i / n - math.pi / 2)) for i, m in enumerate(mods)}
    cruces = set((c['de'], c['a']) for c in rad['dependencias']['cruces_de_capa'])
    out = ['<svg viewBox="0 0 900 460" class="diagrama" role="img" aria-label="modulos">',
           '<defs><marker id="fm" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="flecha"/></marker></defs>']
    for a in rad['dependencias']['aristas']:
        if a['de'] in pos and a['a'] in pos:
            (x1, y1), (x2, y2) = pos[a['de']], pos[a['a']]
            dx, dy = x2 - x1, y2 - y1
            d = max(1.0, math.hypot(dx, dy))
            out.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" class="linea%s" marker-end="url(#fm)"/>' % (x1 + dx / d * 70, y1 + dy / d * 24, x2 - dx / d * 70, y2 - dy / d * 24, ' cruce' if (a['de'], a['a']) in cruces else ''))
    for m, (x, y) in pos.items():
        out.append('<rect x="%.0f" y="%.0f" width="140" height="46" rx="10" class="caja suave"/>' % (x - 70, y - 23))
        out.append(_t(int(x), int(y) + 5, recortar(m, 18), 'caja-t'))
    out.append(_t(450, 450, 'flechas: imports entre modulos · punteadas: cruces de capa (DEC-002)', 'caja-s'))
    out.append('</svg>')
    return '\n'.join(out)


def svg_er(rad):
    tablas = [t['valor'] for t in rad['modelo']['tablas'] if t['origen'] == 'ddl']
    tablas = sorted(set(tablas))[:18]
    if not tablas:
        return ''
    por_fila, ancho, alto, gap = 5, 150, 44, 30
    pos = {}
    for i, t in enumerate(tablas):
        pos[t] = (10 + (i % por_fila) * (ancho + gap), 10 + (i // por_fila) * 90)
    W, H = por_fila * (ancho + gap) + 10, ((len(tablas) - 1) // por_fila + 1) * 90 + 20
    out = ['<svg viewBox="0 0 %d %d" class="diagrama" role="img" aria-label="modelo de datos">' % (W, H),
           '<defs><marker id="fe" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="flecha"/></marker></defs>']
    ddl = [t for t in rad['modelo']['tablas'] if t['origen'] == 'ddl']
    for r in rad['modelo']['relaciones']:
        if r['tipo'] != 'FOREIGN KEY':
            continue
        duenas = [t for t in ddl if t['archivo'] == r['archivo'] and t['linea'] <= r['linea']]
        if not duenas:
            continue
        a = max(duenas, key=lambda t: t['linea'])['valor']
        b = r['valor'].replace('-> ', '')
        if a in pos and b in pos:
            (x1, y1), (x2, y2) = pos[a], pos[b]
            out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="linea" marker-end="url(#fe)"/>' % (x1 + ancho // 2, y1 + alto, x2 + ancho // 2, y2))
    for t, (x, y) in pos.items():
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" class="caja"/>' % (x, y, ancho, alto))
        out.append(_t(x + ancho // 2, y + 27, recortar(t, 18), 'caja-t'))
    out.append('</svg>')
    return '\n'.join(out)


# --------------------------------------------------------------------------------------------- HTML
CSS = '''
:root{--ink:#1f2328;--muted:#57606a;--line:#d0d7de;--soft:#f6f8fa;--acento:#0b5fff;--acento-s:#e8f0ff;--ok:#1a7f37;--warn:#9a6700;--mono:ui-monospace,Consolas,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font:15.5px/1.6 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink)}
header.portada{background:linear-gradient(135deg,#0b2a66,#0b5fff);color:#fff;padding:52px 48px 44px}header.portada h1{margin:0 0 8px;font-size:36px;letter-spacing:-.5px}header.portada p{margin:4px 0;opacity:.92;max-width:900px}
.meta{font-family:var(--mono);font-size:12px;opacity:.85;margin-top:16px}
.layout{display:grid;grid-template-columns:280px 1fr}nav{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;border-right:1px solid var(--line);padding:20px 16px;background:var(--soft)}
nav h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:8px 8px 10px}nav a{display:block;padding:6px 10px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:14px}nav a:hover{background:var(--acento-s)}nav a span{display:inline-block;min-width:28px;color:var(--muted);font-family:var(--mono);font-size:12px}
main{padding:28px 48px 80px;max-width:1180px}section{padding:26px 0 10px;border-bottom:1px solid var(--line)}h2{font-size:24px;margin:0 0 6px}h3{font-size:17px;margin:20px 0 8px}
.lead{color:var(--muted);margin:0 0 16px;max-width:900px}table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:14px}th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}th{background:var(--soft)}
code{font-family:var(--mono);font-size:12.5px;background:var(--soft);padding:1px 5px;border-radius:4px}.completar{background:#fff8c5;border:1px dashed #d4a72c;border-radius:4px;padding:0 4px;color:var(--warn)}
.pasos{list-style:none;padding:0;counter-reset:p}.pasos li{position:relative;padding:12px 14px 12px 56px;border:1px solid var(--line);border-radius:12px;margin:8px 0;background:#fff}.pasos li::before{counter-increment:p;content:counter(p);position:absolute;left:14px;top:12px;width:30px;height:30px;border-radius:50%;background:var(--acento);color:#fff;font-weight:700;text-align:center;line-height:30px}
.diagrama{width:100%;height:auto;max-width:1080px;display:block;margin:12px 0 18px}.caja{fill:#fff;stroke:var(--line);stroke-width:1.5}.caja.acento{fill:var(--acento-s);stroke:#b6ccff}.caja.suave{fill:var(--soft)}.caja-t{font-size:13.5px;font-weight:600;fill:var(--ink)}.caja-s{font-size:12px;fill:var(--muted)}.linea{stroke:#8b949e;stroke-width:1.6}.linea.cruce{stroke-dasharray:5 4;stroke:#cf222e}.flecha{fill:#8b949e}.num{fill:var(--acento)}.num-t{fill:#fff;font-size:12px;font-weight:700}
.pantalla{border:1px solid var(--line);border-radius:12px;padding:10px;background:var(--soft);margin:10px 0}.pantalla img{max-width:100%;border-radius:8px;display:block}
.nota{border-left:4px solid var(--acento);background:var(--acento-s);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0}.timeline{list-style:none;padding:0;margin:14px 0;border-left:2px solid var(--line)}.timeline li{position:relative;padding:0 0 16px 22px}.timeline li::before{content:"";position:absolute;left:-7px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--acento);border:2px solid #fff}.timeline time{font-family:var(--mono);font-size:12px;color:var(--muted)}.timeline b{display:block}
.badge{display:inline-block;font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid var(--line);background:var(--soft);margin-left:6px}
@media(max-width:900px){.layout{grid-template-columns:1fr}nav{position:static;height:auto}main{padding:20px}}@media print{nav{display:none}.layout{grid-template-columns:1fr}header.portada{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''


def pantalla_html(raiz, salida_dir, ficha):
    m = ficha['maqueta'].strip().strip('`')
    if not m or m.startswith('<'):
        return '<div class="pantalla"><span class="completar">&lt;pantalla: exportar de Stitch a entregables/disenos/ y citarla en fuente_maqueta&gt;</span></div>'
    ruta = os.path.join(raiz, m)
    rel = os.path.relpath(ruta, salida_dir).replace(os.sep, '/')
    if m.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
        return '<div class="pantalla"><img src="%s" alt="%s"><div class="lead">%s%s</div></div>' % (html.escape(rel), html.escape(ficha['titulo']), html.escape(m), '' if os.path.isfile(ruta) else ' <span class="completar">&lt;el archivo no existe todavía&gt;</span>')
    return '<div class="pantalla">Maqueta: <a href="%s"><code>%s</code></a>%s</div>' % (html.escape(rel), html.escape(m), '' if os.path.isfile(ruta) else ' <span class="completar">&lt;el archivo no existe todavía&gt;</span>')


def documento(tipo, datos, rad, raiz, salida, titulo):
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    salida_dir = os.path.dirname(os.path.abspath(salida))
    H, secs = [], []
    es_manual = tipo == 'manual'
    fichas = datos['fichas']
    # orden de secciones
    if es_manual:
        secs = [('empezar', 'Empezar en pocos pasos')] + [('flujo-%d' % i, f['titulo']) for i, f in enumerate(fichas)] + [('glosario', 'Palabras que vas a ver'), ('faq', 'Preguntas frecuentes'), ('ayuda', 'Si algo no sale')]
    else:
        secs = [('resumen', 'Resumen'), ('arquitectura', 'Módulos y arquitectura'), ('datos', 'Modelo de datos'), ('api', 'API y contratos'), ('flujos', 'Flujos funcionales'),
                ('reglas', 'Catálogo de reglas de negocio'), ('integraciones', 'Integraciones y ambientes'), ('decisiones', 'Decisiones'), ('pruebas', 'Pruebas'),
                ('pendientes', 'Pendientes y deuda'), ('aprendizajes', 'Aprendizajes'), ('bitacora', 'Bitácora'), ('glosario', 'Glosario'), ('diagramas', 'Diagramas interactivos y cómo se regenera')]
    H.append('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body>' % (html.escape(titulo), CSS))
    sub = 'Guía de uso: cómo empezar y qué hace cada parte, paso a paso.' if es_manual else 'Documentación técnica y funcional: qué hace, cómo está construida, qué decidió el equipo y qué queda pendiente.'
    H.append('<header class="portada"><h1>%s</h1><p>%s</p><p class="meta">Generado el %s por bin/generar-documentacion.py --tipo %s · módulo %s%s · lo marcado en amarillo falta en el Cerebro y no se inventa</p></header>' % (html.escape(titulo), sub, ahora, tipo, html.escape(datos['modulo']), (' · radiografía de ' + html.escape(rad['ruta'])) if rad else ''))
    H.append('<div class="layout"><nav><h2>Índice</h2>')
    for i, (anc, tit) in enumerate(secs, 1):
        H.append('<a href="#%s"><span>%02d</span>%s</a>' % (anc, i, html.escape(tit)))
    H.append('</nav><main>')

    if es_manual:
        inicio = next((f for f in fichas if f['pasos']), None)
        H.append('<section id="empezar"><h2>01 · Empezar en pocos pasos</h2>')
        if datos['contexto'].get('proposito') and not datos['contexto']['proposito'].startswith('<'):
            H.append('<p class="lead">%s</p>' % md_inline(datos['contexto']['proposito']))
        if inicio:
            H.append('<p class="lead">Lo primero que vas a hacer: <b>%s</b>.</p>' % html.escape(inicio['titulo']))
            H.append(svg_pasos(inicio['pasos']))
            H.append('<ol class="pasos">' + ''.join('<li>%s</li>' % md_inline(p) for p in inicio['pasos']) + '</ol>')
        else:
            H.append('<p><span class="completar">&lt;no hay ninguna ficha con pasos todavía: completar la sección Flujo de la primera ficha&gt;</span></p>')
        H.append('</section>')
        for i, f in enumerate(fichas):
            H.append('<section id="flujo-%d"><h2>%02d · %s</h2>' % (i, i + 2, html.escape(f['titulo'])))
            if f['proposito']:
                H.append('<p class="lead">%s</p>' % md_inline(f['proposito']))
            H.append(pantalla_html(raiz, salida_dir, f))
            if f['pasos']:
                H.append('<h3>Paso a paso</h3>' + svg_pasos(f['pasos']) + '<ol class="pasos">' + ''.join('<li>%s</li>' % md_inline(p) for p in f['pasos']) + '</ol>')
            else:
                H.append('<p><span class="completar">&lt;esta ficha no tiene pasos en su sección Flujo&gt;</span></p>')
            if f['reglas']:
                H.append('<h3>Lo que el sistema controla</h3><ul>' + ''.join('<li><b>%s.</b> %s</li>' % (html.escape(t), md_inline(p) if p else '<span class="completar">&lt;explicación en criollo&gt;</span>') for _, t, p in f['reglas']) + '</ul>')
            H.append('</section>')
        H.append('<section id="glosario"><h2>%02d · Palabras que vas a ver</h2>' % (len(fichas) + 2))
        H.append(('<table><tr><th>Término</th><th>Qué significa</th></tr>' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % (md_inline(g[0]), md_inline(g[1])) for g in datos['glosario']) + '</table>') if datos['glosario'] else '<p><span class="completar">&lt;sin glosario en las fichas&gt;</span></p>')
        H.append('</section>')
        H.append('<section id="faq"><h2>%02d · Preguntas frecuentes</h2>' % (len(fichas) + 3))
        res = datos['pendientes']['resueltas']
        H.append(('<dl>' + ''.join('<dt><b>%s</b></dt><dd>%s</dd>' % (md_inline(r[1]), md_inline(r[2] if len(r) > 2 else '')) for r in res) + '</dl>') if res else '<p>Las preguntas que el equipo ya respondió aparecen acá (vienen de <code>pendientes.md</code> §Resueltas). <span class="completar">&lt;todavía no hay&gt;</span></p>')
        H.append('</section>')
        H.append('<section id="ayuda"><h2>%02d · Si algo no sale</h2><p><span class="completar">&lt;a quién escribir, qué datos mandar (pantalla, hora, qué estabas haciendo), dónde está el estado del sistema&gt;</span></p><p class="lead">Nunca mandes datos personales de otra persona en un reporte: describí la situación, no el dato.</p></section>' % (len(fichas) + 4))
    else:
        H.append('<section id="resumen"><h2>01 · Resumen</h2>')
        c = datos['contexto']
        for k, et in (('proposito', 'Propósito'), ('alcance', 'Alcance'), ('principios', 'Principios operativos')):
            if c.get(k):
                H.append('<h3>%s</h3><p>%s</p>' % (et, md_inline(c[k]).replace('\n', '<br>')))
        H.append('<p class="lead">%d flujos documentados · %d reglas de negocio · %d decisiones · %d ítems en el tablero local</p></section>' % (len(fichas), sum(len(f['reglas']) for f in fichas), len(datos['decisiones']), len(datos['backlog'])))
        H.append('<section id="arquitectura"><h2>02 · Módulos y arquitectura</h2>')
        if rad:
            H.append('<p class="lead">Radiografía del código (%d archivos): módulos de primer nivel y sus dependencias.</p>' % rad['archivos'] + svg_modulos(rad))
        else:
            H.append('<p><span class="completar">&lt;pasá --app &lt;ruta del repo&gt; para dibujar los módulos desde el código&gt;</span></p>')
        if datos['mapa']:
            for k, filas in datos['mapa'].items():
                if filas:
                    H.append('<h3>%s (de <code>aplicacion/mapa.md</code>)</h3><table>%s</table>' % (html.escape(k), ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % md_inline(c) for c in f) for f in filas)))
        H.append('</section>')
        H.append('<section id="datos"><h2>03 · Modelo de datos</h2>')
        if rad and svg_er(rad):
            H.append(svg_er(rad) + '<p class="lead">Tablas del DDL y sus claves foráneas; entidades del ORM: %s</p>' % html.escape(', '.join(sorted(set(e['valor'] for e in rad['modelo']['entidades']))) or '—'))
        else:
            H.append('<p><span class="completar">&lt;sin --app o sin DDL reconocido; el diagrama ER sale de las migraciones o de Archify&gt;</span></p>')
        H.append('</section>')
        H.append('<section id="api"><h2>04 · API y contratos</h2>')
        if rad and (rad['api'] or rad['contrato']):
            H.append('<table><tr><th>Método</th><th>Ruta</th><th>Dónde</th></tr>' + ''.join('<tr><td>%s</td><td><code>%s</code></td><td><code>%s:%s</code></td></tr>' % (html.escape(e['metodo']), html.escape(e['ruta']), html.escape(e['archivo']), e['linea']) for e in rad['api'][:80]) + '</table>')
            if rad['contrato']:
                H.append('<p class="lead">Rutas declaradas en el contrato: %s</p>' % ', '.join('<code>%s</code>' % html.escape(c['ruta']) for c in rad['contrato'][:40]))
        else:
            H.append('<p><span class="completar">&lt;sin --app: la API sale de la radiografía y del openapi.yaml&gt;</span></p>')
        H.append('</section>')
        H.append('<section id="flujos"><h2>05 · Flujos funcionales</h2>')
        for f in fichas:
            H.append('<h3>%s <span class="badge">%s</span></h3>' % (html.escape(f['titulo']), html.escape(f['estado'] or '—')))
            if f['proposito']:
                H.append('<p>%s</p>' % md_inline(f['proposito']))
            if f['pasos']:
                H.append(svg_pasos(f['pasos']) + '<ol class="pasos">' + ''.join('<li>%s</li>' % md_inline(p) for p in f['pasos']) + '</ol>')
            H.append(pantalla_html(raiz, salida_dir, f))
            if f['reglas']:
                H.append('<p>Reglas: %s</p>' % ', '.join('<code>%s</code>' % html.escape(r[0]) for r in f['reglas']))
        if not fichas:
            H.append('<p><span class="completar">&lt;sin fichas de flujo en funcional/&gt;</span></p>')
        H.append('</section>')
        H.append('<section id="reglas"><h2>06 · Catálogo de reglas de negocio</h2><table><tr><th>Regla</th><th>Título</th><th>Qué dice</th><th>Ficha</th></tr>')
        for f in fichas:
            for cod, t, p in f['reglas']:
                H.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (html.escape(cod), html.escape(t), md_inline(p) if p else '<span class="completar">&lt;enunciado&gt;</span>', html.escape(f['archivo'])))
        H.append('</table></section>')
        H.append('<section id="integraciones"><h2>07 · Integraciones y ambientes</h2>')
        if datos['contexto'].get('integraciones'):
            H.append('<h3>Previstas (contexto.md)</h3><table>' + ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % md_inline(c) for c in f) for f in datos['contexto']['integraciones'] if f and not f[0].startswith('<')) + '</table>')
        if rad and rad['integraciones']:
            tipos = {}
            for i in rad['integraciones']:
                tipos.setdefault(i['tipo'], set()).add(i['valor'][:80])
            H.append('<h3>Detectadas en el código</h3><table><tr><th>Tipo</th><th>Qué</th></tr>' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % (html.escape(k), html.escape(', '.join(sorted(v))[:400])) for k, v in tipos.items()) + '</table>')
        H.append('</section>')
        H.append('<section id="decisiones"><h2>08 · Decisiones</h2><table><tr><th>DEC</th><th>Qué</th><th>Estado</th></tr>' + ''.join('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (c, html.escape(t), html.escape(e)) for c, t, e in datos['decisiones']) + '</table></section>')
        H.append('<section id="pruebas"><h2>09 · Pruebas</h2><p>Tres capas, ninguna redundante: unitaria y de contrato en cada repositorio (TDD con evidencia del rojo por Tarea), integración cuando la Tarea lo declara, y aceptación contra el sistema desplegado trazada a cada Historia (<code>qa/</code>). <span class="completar">&lt;completar con el estado real: suites, cobertura, qué Escenarios tienen prueba de punta a punta&gt;</span></p></section>')
        H.append('<section id="pendientes"><h2>10 · Pendientes y deuda</h2>')
        H.append('<h3>Preguntas abiertas</h3>' + (('<table><tr><th>#</th><th>Pregunta</th><th>Responsable</th></tr>' + ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (html.escape(p[0]), md_inline(p[1]), html.escape(p[2] if len(p) > 2 else '')) for p in datos['pendientes']['abiertas']) + '</table>') if datos['pendientes']['abiertas'] else '<p>Ninguna registrada.</p>'))
        H.append('<h3>Deuda técnica (DT)</h3>' + (('<table>' + ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % md_inline(c) for c in f[:6]) for f in datos['deuda']) + '</table>') if datos['deuda'] else '<p>Ninguna registrada.</p>'))
        H.append('</section>')
        H.append('<section id="aprendizajes"><h2>11 · Aprendizajes (AP)</h2>' + (('<table>' + ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % md_inline(c) for c in f[:7]) for f in datos['aprendizajes']) + '</table>') if datos['aprendizajes'] else '<p>Ninguno registrado todavía.</p>') + '</section>')
        H.append('<section id="bitacora"><h2>12 · Bitácora</h2><ul class="timeline">')
        for fecha, t, d in datos['log']:
            H.append('<li><time>%s</time><b>%s</b>%s</li>' % (fecha, html.escape(t), html.escape(d)))
        H.append('</ul>')
        cerrados = [b for b in datos['backlog'] if b['estado'] in ('Resolved', 'Closed')]
        if datos['backlog']:
            H.append('<h3>Tablero local: %d ítems, %d cerrados</h3><table><tr><th>#</th><th>Tipo</th><th>Estado</th><th>Título</th><th>Actualizado</th></tr>' % (len(datos['backlog']), len(cerrados)) + ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(html.escape(str(b[k])) for k in ('id', 'tipo', 'estado', 'titulo', 'actualizado')) for b in datos['backlog']) + '</table>')
        H.append('</section>')
        H.append('<section id="glosario"><h2>13 · Glosario</h2>' + (('<table><tr><th>Término</th><th>Definición</th></tr>' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % (md_inline(g[0]), md_inline(g[1])) for g in datos['glosario']) + '</table>') if datos['glosario'] else '<p>Sin glosario en las fichas.</p>') + '</section>')
        H.append('<section id="diagramas"><h2>14 · Diagramas interactivos y cómo se regenera</h2>')
        H.append(('<ul>' + ''.join('<li><a href="%s">%s</a></li>' % (html.escape(os.path.relpath(os.path.join(raiz, d), salida_dir).replace(os.sep, '/')), html.escape(d)) for d in datos['diagramas']) + '</ul>') if datos['diagramas'] else '<p>Los diagramas de secuencia y arquitectura interactivos los produce la skill <code>archify</code> en <code>borrador/diagramas/</code>; cuando existan, se enlazan acá.</p>')
        H.append('<pre>python -B bin/generar-documentacion.py --tipo tecnica --app &lt;ruta del repo&gt;\npython -B bin/generar-documentacion.py --tipo manual</pre></section>')
    H.append('</main></div></body></html>')
    return '\n'.join(H)


def main():
    ap = argparse.ArgumentParser(description='Documentacion de la aplicacion desde el Cerebro.')
    ap.add_argument('--tipo', choices=['manual', 'tecnica'], required=True)
    ap.add_argument('--modulo', default='')
    ap.add_argument('--app', default='', help='repo de codigo para la radiografia (solo tecnica)')
    ap.add_argument('--salida', default='')
    ap.add_argument('--titulo', default='')
    ap.add_argument('--raiz', default=RAIZ, help='raiz del nucleo (por defecto, la de este script)')
    a = ap.parse_args()
    raiz = os.path.abspath(a.raiz)
    mod = modulo_de(raiz, a.modulo)
    if not mod or not os.path.isdir(mod):
        print('SIN DATOS -- no encuentro el modulo (pasa --modulo <slug>) debajo de %s/cerebro-digital' % raiz)
        return SIN_DATOS
    datos = cargar(raiz, mod)
    if not datos['fichas'] and a.tipo == 'manual':
        print('SIN DATOS -- no hay fichas de flujo en %s/funcional: la guia sale de ahi.' % mod)
        return SIN_DATOS
    rad = radiografia(a.app) if a.tipo == 'tecnica' else None
    titulo = a.titulo or ('Guía de uso — %s' % datos['modulo'] if a.tipo == 'manual' else 'Documentación técnica y funcional — %s' % datos['modulo'])
    salida = os.path.abspath(a.salida) if a.salida else os.path.join(raiz, 'borrador', 'documentacion', 'guia-de-uso.html' if a.tipo == 'manual' else 'documentacion-tecnica.html')
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    texto = documento(a.tipo, datos, rad, raiz, salida, titulo)
    with open(salida, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)
    faltan = texto.count('class="completar"')
    print('documento escrito en %s (%d KB; %d fichas; %d marca(s) <completar> que el Cerebro no tiene%s)' % (salida, len(texto.encode('utf-8')) // 1024, len(datos['fichas']), faltan, '; sin radiografia' if (a.tipo == 'tecnica' and not rad) else ''))
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
