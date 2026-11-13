#!/usr/bin/env python3
"""Tablero LOCAL: el backlog como archivos markdown en el Cerebro, sin MCP ni servidor. Para trabajar solo.

    python bin/tablero-local.py crear --tipo Historia --titulo "..." [--padre 3] [--etiqueta reservas] [--cuerpo archivo.md] [--asignado yo]
    python bin/tablero-local.py listar [--tipo Tarea] [--estado New] [--asignado yo] [--json]
    python bin/tablero-local.py ver 12 [--json]
    python bin/tablero-local.py tomar 12 --quien yo            (asigna y pasa a Active; frena si ya es de otro y no esta en New)
    python bin/tablero-local.py estado 12 Active|Resolved|Closed|Removed [--confirmado]   (Closed/Removed exigen --confirmado; Resolved tambien, salvo una Tarea con DEC-005 firmada)
    python bin/tablero-local.py comentar 12 --texto "..." [--autor yo]
    python bin/tablero-local.py vincular 12 15 [--relacion Related|Parent]
    python bin/tablero-local.py buscar "texto" [--etiqueta x] [--abiertos] [--json]       (deduplicacion por objetivo)
    python bin/tablero-local.py editar 12 --campo titulo|etiqueta|iteracion --valor "..."

Tres estados, nunca dos:  0 = hecho   1 = FRENA (una barrera; se dice cual)   2 = SIN DATOS (no hay tablero o no existe el item)

POR QUE EXISTE. El template nacio con Azure DevOps por MCP. Para un desarrollo personal, o un equipo chico sin
tablero, el mismo pipeline (redactar -> cargar -> tomar -> comentar -> cerrar) funciona sobre archivos: un
work item por archivo en cerebro-digital/<modulo>/backlog/, con frontmatter y un #ID secuencial. Se versiona,
se busca con grep, no gasta tokens y se exporta a cualquier tablero despues. Las skills del pipeline aplican
los MISMOS GATEs (tablero autorizado, dedup, confirmacion, nivel, borrado, tarjeta congelada); este script
solo ejecuta lo que la skill ya confirmo, y pone dos barreras mecanicas: tomar una tarjeta de otro y cerrar
o borrar sin --confirmado.

QUE NO HACE. No decide el tipo, no redacta, no busca duplicados por su cuenta (buscar es la herramienta; el
veredicto es de la skill), no toca otro tablero. Solo biblioteca estandar.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

OK, FRENA, SIN_DATOS = 0, 1, 2
TIPOS = ('Epica', 'Feature', 'Historia', 'Tarea', 'Bug', 'Habilitador')
ESTADOS = ('New', 'Active', 'Resolved', 'Closed', 'Removed')
TERMINALES = ('Closed', 'Removed')
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hoy():
    return datetime.date.today().isoformat()


def slug(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s.lower().replace('ñ', 'n'))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:50] or 'item'


def tablero(ruta):
    if ruta:
        return os.path.abspath(ruta)
    modulos = [d for d in glob.glob(os.path.join(RAIZ, 'cerebro-digital', '*', 'arquitectura')) if os.path.isdir(d)]
    if len(modulos) != 1:
        return None
    return os.path.join(os.path.dirname(modulos[0]), 'backlog')


def dec005_firmada(dir_tablero):
    """True si DEC-005 (modo desatendido) esta firmada en el decisiones.md del modulo del tablero: es la autorizacion
    escrita que deja pasar a Resolved sin --confirmado. Sin el archivo, o sin firma, False: se pregunta."""
    p = os.path.join(os.path.dirname(dir_tablero), 'arquitectura', 'decisiones.md')
    try:
        with open(p, encoding='utf-8-sig') as h:
            t = h.read()
    except OSError:
        return False
    if re.search(r'Confirmado al instanciar \([^)]*\): modo equipo', t):
        return False   # la columna del modo solo no vale en un proyecto de equipo (DEC-006)
    seccion = t.split('## DEC-005', 1)[1].split('\n## ', 1)[0] if '## DEC-005' in t else ''
    return '**Confirmado para el modo solo (' in seccion


def leer(p):
    with open(p, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def parsear(texto):
    m = re.match(r'---\n(.*?)\n---\n(.*)', texto, re.S)
    if not m:
        return None, texto
    datos = {}
    for l in m.group(1).split('\n'):
        mm = re.match(r'^([a-z_]+):\s*(.*)$', l)
        if mm:
            v = mm.group(2).strip()
            if v.startswith('[') and v.endswith(']'):
                v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
            elif len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
                v = v[1:-1]
            datos[mm.group(1)] = v
    return datos, m.group(2)


def serializar(datos, cuerpo):
    orden = ('id', 'tipo', 'estado', 'titulo', 'padre', 'etiqueta', 'asignado', 'iteracion', 'creado', 'actualizado', 'relaciones')
    lineas = ['---']
    for k in orden:
        v = datos.get(k, '')
        if isinstance(v, list):
            lineas.append('%s: [%s]' % (k, ', '.join(str(x) for x in v)))
        elif k == 'titulo':
            lineas.append('titulo: "%s"' % str(v).replace('"', "'"))
        else:
            lineas.append('%s: %s' % (k, v))
    lineas.append('---')
    return '\n'.join(lineas) + '\n' + cuerpo.lstrip('\n')


def items(dir_):
    out = {}
    for p in sorted(glob.glob(os.path.join(dir_, '[0-9]*.md'))):
        datos, cuerpo = parsear(leer(p))
        if datos and datos.get('id', '').isdigit():
            out[int(datos['id'])] = (p, datos, cuerpo)
    return out


def guardar(p, datos, cuerpo):
    datos['actualizado'] = hoy()
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(serializar(datos, cuerpo))


def salida(a, d, texto):
    if getattr(a, 'json', False):
        print(json.dumps(d, ensure_ascii=True, indent=1))
    else:
        print(texto)


def main():
    ap = argparse.ArgumentParser(description='Tablero local en archivos markdown.')
    ap.add_argument('--tablero', default='', help='carpeta del backlog; por defecto cerebro-digital/<modulo>/backlog')
    sub = ap.add_subparsers(dest='accion', required=True)
    c = sub.add_parser('crear'); c.add_argument('--tipo', choices=TIPOS, required=True); c.add_argument('--titulo', required=True)
    c.add_argument('--padre', type=int, default=0); c.add_argument('--etiqueta', default=''); c.add_argument('--cuerpo', default='')
    c.add_argument('--asignado', default=''); c.add_argument('--iteracion', default=''); c.add_argument('--json', action='store_true')
    l = sub.add_parser('listar'); l.add_argument('--tipo', default=''); l.add_argument('--estado', default=''); l.add_argument('--asignado', default=''); l.add_argument('--json', action='store_true')
    v = sub.add_parser('ver'); v.add_argument('id', type=int); v.add_argument('--json', action='store_true')
    t = sub.add_parser('tomar'); t.add_argument('id', type=int); t.add_argument('--quien', required=True); t.add_argument('--json', action='store_true')
    e = sub.add_parser('estado'); e.add_argument('id', type=int); e.add_argument('nuevo', choices=ESTADOS); e.add_argument('--confirmado', action='store_true'); e.add_argument('--json', action='store_true')
    co = sub.add_parser('comentar'); co.add_argument('id', type=int); co.add_argument('--texto', required=True); co.add_argument('--autor', default='ia'); co.add_argument('--json', action='store_true')
    vi = sub.add_parser('vincular'); vi.add_argument('id', type=int); vi.add_argument('otro', type=int); vi.add_argument('--relacion', choices=('Related', 'Parent'), default='Related'); vi.add_argument('--json', action='store_true')
    b = sub.add_parser('buscar'); b.add_argument('texto'); b.add_argument('--etiqueta', default=''); b.add_argument('--abiertos', action='store_true'); b.add_argument('--json', action='store_true')
    ed = sub.add_parser('editar'); ed.add_argument('id', type=int); ed.add_argument('--campo', choices=('titulo', 'etiqueta', 'iteracion', 'asignado'), required=True); ed.add_argument('--valor', required=True); ed.add_argument('--json', action='store_true')
    a = ap.parse_args()

    dir_ = tablero(a.tablero)
    if dir_ is None:
        print('SIN DATOS -- no puedo ubicar el tablero: pasa --tablero <carpeta> (hay cero o varios modulos en cerebro-digital/).')
        return SIN_DATOS
    if a.accion != 'crear' and not os.path.isdir(dir_):
        print('SIN DATOS -- no existe el tablero %s (se crea con el primer "crear").' % dir_)
        return SIN_DATOS
    todos = items(dir_) if os.path.isdir(dir_) else {}

    if a.accion == 'crear':
        os.makedirs(dir_, exist_ok=True)
        if a.padre and a.padre not in todos:
            print('FRENA -- el padre #%d no existe en el tablero.' % a.padre)
            return FRENA
        nid = (max(todos) + 1) if todos else 1
        cuerpo = leer(a.cuerpo) if a.cuerpo else ''
        if not cuerpo.strip():
            cuerpo = '# #%d %s\n\n<descripcion>\n' % (nid, a.titulo)
        if '## Comentarios' not in cuerpo:
            cuerpo = cuerpo.rstrip('\n') + '\n\n## Comentarios\n'
        datos = {'id': nid, 'tipo': a.tipo, 'estado': 'New', 'titulo': a.titulo, 'padre': a.padre or '', 'etiqueta': a.etiqueta,
                 'asignado': a.asignado, 'iteracion': a.iteracion, 'creado': hoy(), 'actualizado': hoy(), 'relaciones': []}
        p = os.path.join(dir_, '%04d-%s.md' % (nid, slug(a.titulo)))
        guardar(p, datos, cuerpo)
        salida(a, {'id': nid, 'archivo': p}, '#%d creado: %s (%s) -> %s' % (nid, a.titulo, a.tipo, os.path.relpath(p, RAIZ) if p.startswith(RAIZ) else p))
        return OK

    if a.accion == 'listar':
        filas = []
        for i, (p, d, _) in sorted(todos.items()):
            if a.tipo and d.get('tipo') != a.tipo:
                continue
            if a.estado and d.get('estado') != a.estado:
                continue
            if a.asignado and d.get('asignado') != a.asignado:
                continue
            filas.append({'id': i, 'tipo': d.get('tipo'), 'estado': d.get('estado'), 'asignado': d.get('asignado', ''), 'padre': d.get('padre', ''), 'etiqueta': d.get('etiqueta', ''), 'titulo': d.get('titulo', '')})
        texto = '\n'.join('#%-4d %-11s %-9s %-12s %s' % (f['id'], f['tipo'], f['estado'], (f['asignado'] or '-')[:12], f['titulo']) for f in filas) or '(sin items)'
        salida(a, filas, texto)
        return OK

    if a.accion == 'buscar':
        q = a.texto.lower()
        filas = []
        for i, (p, d, cuerpo) in sorted(todos.items()):
            if a.etiqueta and d.get('etiqueta') != a.etiqueta:
                continue
            if a.abiertos and d.get('estado') in TERMINALES:
                continue
            texto = (d.get('titulo', '') + '\n' + cuerpo).lower()
            if q in texto:
                filas.append({'id': i, 'tipo': d.get('tipo'), 'estado': d.get('estado'), 'titulo': d.get('titulo', ''), 'etiqueta': d.get('etiqueta', '')})
        salida(a, filas, ('\n'.join('#%d %s [%s] %s' % (f['id'], f['tipo'], f['estado'], f['titulo']) for f in filas) or 'ningun item contiene "%s"' % a.texto))
        return OK

    if a.id not in todos:
        print('SIN DATOS -- no existe el item #%d.' % a.id)
        return SIN_DATOS
    p, d, cuerpo = todos[a.id]

    if a.accion == 'ver':
        salida(a, {'id': a.id, 'campos': d, 'cuerpo': cuerpo}, serializar(d, cuerpo))
        return OK
    if a.accion == 'tomar':
        if d.get('asignado') and d['asignado'] != a.quien and d.get('estado') != 'New':
            print('FRENA -- #%d ya la tiene %s y esta en %s: coordinar, no reasignar.' % (a.id, d['asignado'], d.get('estado')))
            return FRENA
        d['asignado'] = a.quien
        d['estado'] = 'Active'
        guardar(p, d, cuerpo)
        salida(a, {'id': a.id, 'asignado': a.quien, 'estado': 'Active'}, '#%d tomada por %s, estado Active' % (a.id, a.quien))
        return OK
    if a.accion == 'estado':
        if a.nuevo in TERMINALES and not a.confirmado:
            print('FRENA -- pasar #%d a %s es terminal: exige --confirmado (el segundo "si" de la persona).' % (a.id, a.nuevo))
            return FRENA
        if a.nuevo == 'Resolved' and not a.confirmado and not (d.get('tipo') == 'Tarea' and dec005_firmada(dir_)):
            print('FRENA -- pasar #%d a Resolved es cerrar: exige --confirmado, salvo una Tarea con DEC-005 (modo '
                  'desatendido) firmada en arquitectura/decisiones.md.' % a.id)
            return FRENA
        anterior = d.get('estado')
        d['estado'] = a.nuevo
        guardar(p, d, cuerpo)
        salida(a, {'id': a.id, 'antes': anterior, 'ahora': a.nuevo}, '#%d: %s -> %s' % (a.id, anterior, a.nuevo))
        return OK
    if a.accion == 'comentar':
        linea = '- %s (%s): %s' % (hoy(), a.autor, a.texto.strip().replace('\n', ' '))
        if '## Comentarios' not in cuerpo:
            cuerpo = cuerpo.rstrip('\n') + '\n\n## Comentarios\n'
        cuerpo = cuerpo.rstrip('\n') + '\n' + linea + '\n'
        guardar(p, d, cuerpo)
        salida(a, {'id': a.id, 'comentario': linea}, '#%d comentada: %s' % (a.id, linea))
        return OK
    if a.accion == 'vincular':
        if a.otro not in todos:
            print('SIN DATOS -- no existe el item #%d.' % a.otro)
            return SIN_DATOS
        if a.relacion == 'Parent':
            d['padre'] = a.otro
        else:
            rel = d.get('relaciones') or []
            if str(a.otro) not in [str(x) for x in rel]:
                rel.append(a.otro)
            d['relaciones'] = rel
            p2, d2, c2 = todos[a.otro]
            rel2 = d2.get('relaciones') or []
            if str(a.id) not in [str(x) for x in rel2]:
                rel2.append(a.id)
                d2['relaciones'] = rel2
                guardar(p2, d2, c2)
        guardar(p, d, cuerpo)
        salida(a, {'id': a.id, 'otro': a.otro, 'relacion': a.relacion}, '#%d %s #%d' % (a.id, a.relacion, a.otro))
        return OK
    if a.accion == 'editar':
        anterior = d.get(a.campo, '')
        d[a.campo] = a.valor
        guardar(p, d, cuerpo)
        salida(a, {'id': a.id, 'campo': a.campo, 'antes': anterior, 'ahora': a.valor}, '#%d %s: "%s" -> "%s"' % (a.id, a.campo, anterior, a.valor))
        return OK
    return SIN_DATOS


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
