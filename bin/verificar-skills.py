#!/usr/bin/env python3
"""Verifica cada SKILL.md contra la especificacion abierta de Agent Skills y los limites de Claude Code.

    python -I bin/verificar-skills.py [raiz] [--json]

Tres salidas, nunca dos:  0 = OK   1 = HALLAZGO (algo fuera de la especificacion)   2 = SIN DATOS (no hay skills)

POR QUE EXISTE. Las cuatro herramientas (Claude Code, opencode, Antigravity, Gemini CLI) leen el mismo
SKILL.md, y la especificacion que comparten (agentskills.io/specification) pone limites que ninguna
avisa al romperse: el nombre tiene que ser igual a la carpeta, en minusculas con guiones y de hasta 64
caracteres; la descripcion no puede estar vacia ni pasar de 1024 caracteres (Claude Code la corta en
1536; Gemini CLI y opencode siguen la especificacion). Una descripcion cortada es una skill que deja de
dispararse cuando corresponde, y nadie se entera. Esto lo cuenta un script, siempre igual.

QUE MIRA, por cada SKILL.md de las raices conocidas (la fuente canonica, los dos espejos y las skills
scoped de back/ y front/, las que existan):
  - frontmatter YAML presente y cerrado;
  - name: obligatorio, 1..64, ^[a-z0-9]+(-[a-z0-9]+)*$, igual al nombre de la carpeta;
  - description: obligatoria, 1..1024 caracteres (el texto ya plegado, como lo lee la herramienta);
  - sin BOM (rompe el frontmatter);
  - AVISO (no frena) si el cuerpo pasa de 500 lineas: la especificacion recomienda mover detalle a references/;
  - el TAMANO frente a la compactacion: Claude Code re-inyecta cada skill usada hasta ~5.000 tokens y corta el final;
    mas de 12500 caracteres (~5.000 tokens medidos) es HALLAZGO y mas de 12000, AVISO (salvo las VENDIDAS).
Y una vez, sobre la fuente: que el numero de skills que anuncian AGENTS.md, README.md e INSTALACION.md sea el real,
y que README.md y cerebro-digital/index.md las nombren a todas (CONTEOS y LISTAS). Un numero afirmado que nadie
verifica envejece en silencio. Antes este control estaba copiado en el hook, los dos CI y el Doctor; ahora lo
hace esto, y el Doctor toma de aca sus patrones.
Y el RUTEO ESCRITO: que cada skill de la fuente este nombrada (entre acentos graves o doble corchete) en un
texto que se carga siempre: AGENTS.md o la skill del orquestador. Claude Code lista las skills con un cupo (el
1% del contexto) y, cuando se desborda, saca las DESCRIPCIONES de las menos usadas y deja solo el nombre: una
skill que depende solo de su descripcion deja de dispararse, y nadie se entera (code.claude.com/docs, skills).
Con la Puerta de Skills adoptada, una skill que declara metadata.seccion (o esta en ASIGNADAS) tambien pasa si
la PUERTA de su seccion esta nombrada ahi: la puerta la rutea por su indice generado.
Y la PUERTA DE SKILLS (bin/puerta-skills.py, cargado como modulo): cada skill con su seccion, una puerta por
seccion, el indice de cada puerta y skillOverrides de .claude/settings.json al dia. Sus problemas son HALLAZGO; si
ninguna skill declara metadata.seccion, la Puerta no esta adoptada y no frena; si el modulo no se puede cargar, esa
parte es SIN DATOS (2), nunca OK.

QUE NO HACE. No lee el cuerpo ni juzga si la skill esta bien escrita. No modifica nada. Solo biblioteca
estandar. ASCII puro.
"""

import argparse
import json
import os
import re
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAICES = ('cerebro-digital/configuracion-ia/skills', '.agents/skills', '.claude/skills',
          'back/.claude/skills', 'back/.agents/skills', 'front/.claude/skills', 'front/.agents/skills')
NOMBRE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
MAX_NOMBRE, MAX_DESC, MAX_LINEAS = 64, 1024, 500
# Compactacion: Claude Code re-inyecta cada skill usada hasta 5.000 tokens (25.000 entre todas; la mas vieja se cae
# primero) y corta el FINAL (code.claude.com/docs, context-window). Sin tokenizador se mide en caracteres. Medido el
# 2026-11-25 con el modelo (uso de tokens de claude -p con y sin el archivo): nuestras skills, en castellano con
# markdown, dan ~2,6 caracteres por token (cerebro-orquestador: 21.354 car. = ~8.350 tokens; 14.990 = ~5.690).
# 5.000 tokens son ~12.800 caracteres con la peor relacion medida (2,56): mas de 12500 es HALLAZGO (se pierde el
# final); mas de 12000, AVISO (margen).
MAX_CARACTERES, AVISO_CARACTERES = 12500, 12000
# Frases que quedaron de una fusion a medias o del proyecto de origen. Si una skill las dice, manda a un
# flujo que ya no existe o contradice a DEC-005/DEC-006. Se buscan en todos los .md de la skill (SKILL.md
# y references/), salvo en las skills vendidas de terceros (VENDIDAS), que no se editan.
FRASES_MUERTAS = ('solo para Orca', 'Solo en Orca', 'trabajar-con-intellij', 'Tarea de Azure',
                  'verifica siempre el otro', 'exclusiva de su entorno', 'Sin el otro motor')
VENDIDAS = {'archify'}
CONTEOS = (('AGENTS.md', r'\*\*([0-9]+) habilidades\*\*'),
           ('README.md', r'Skills del Ecosistema \(([0-9]+) habilid'),
           ('INSTALACION.md', r'[Ll]as \*\*([0-9]+) skills\*\*'))
LISTAS = ('README.md', 'cerebro-digital/index.md')
ORQUESTADOR = 'cerebro-orquestador'
RUTEO = ('AGENTS.md', RAICES[0] + '/' + ORQUESTADOR + '/SKILL.md')


def documentos_de_conteo(raiz):
    """Los documentos de CONTEOS y LISTAS que existen en esta raiz (los que se pueden verificar)."""
    return [a for a in dict.fromkeys([c[0] for c in CONTEOS] + list(LISTAS)) if os.path.isfile(os.path.join(raiz, a))]


def conteo(raiz):
    """Lo que no cierra entre las skills de la fuente y lo que anuncian los documentos (lista vacia = todo bien)."""
    fuente = os.path.join(raiz, RAICES[0])
    if not os.path.isdir(fuente):
        return []
    nombres = sorted(d for d in os.listdir(fuente) if os.path.isdir(os.path.join(fuente, d)) and not d.startswith('.'))
    res = []
    for arch, patron in CONTEOS:
        ruta = os.path.join(raiz, arch)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding='utf-8', errors='replace') as h:
            m = re.search(patron, h.read())
        if not m:
            res.append('%s: no encontre el conteo de skills (si cambio la redaccion, actualizar CONTEOS en '
                       'bin/verificar-skills.py)' % arch)
        elif int(m.group(1)) != len(nombres):
            res.append('%s dice %s skills y en la fuente hay %d' % (arch, m.group(1), len(nombres)))
    for arch in LISTAS:
        ruta = os.path.join(raiz, arch)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding='utf-8', errors='replace') as h:
            texto = h.read()
        faltan = [n for n in nombres if n not in texto]
        if faltan:
            res.append('%s no nombra estas skills: %s (va el nombre en la lista, no solo el numero)' % (arch, ' '.join(faltan)))
    return res


def ruteo(raiz, puerta_de=None):
    """Skills de la fuente que ningun texto de RUTEO nombra, o None si no hay orquestador (nada que verificar).
    puerta_de = {skill: la puerta de su seccion}: una skill tambien pasa si su puerta esta nombrada."""
    fuente = os.path.join(raiz, RAICES[0])
    if not os.path.isfile(os.path.join(fuente, ORQUESTADOR, 'SKILL.md')):
        return None
    texto = ''
    for arch in RUTEO:
        ruta = os.path.join(raiz, arch)
        if os.path.isfile(ruta):
            with open(ruta, encoding='utf-8', errors='replace') as h:
                texto += h.read() + ' '
    nombres = sorted(d for d in os.listdir(fuente) if os.path.isdir(os.path.join(fuente, d)) and not d.startswith('.'))

    def nombrada(n):
        return bool(n) and re.search(r'`%s`|\[\[%s(\]\]|[|#])' % (re.escape(n), re.escape(n)), texto) is not None
    puerta_de = puerta_de or {}
    return [n for n in nombres if not nombrada(n) and not nombrada(puerta_de.get(n))]


def puerta(raiz):
    """La Puerta de Skills (bin/puerta-skills.py, cargado como modulo, como hace el Doctor con este script):
    {'adoptada', 'problemas', 'notas', 'puerta_de'}, o {'error'} si no se pudo cargar o fallo (SIN DATOS, nunca OK)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'puerta_skills_para_verificar', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'puerta-skills.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        secs = mod.secciones(raiz)
        return {'adoptada': mod.adoptada(raiz), 'problemas': [list(p) for p in mod.problemas(raiz)],
                'notas': mod.notas(raiz),
                'puerta_de': {n: e['puerta'] for e in secs.values() if e['puerta'] for n in e['skills']}}
    except Exception as e:  # noqa: BLE001 -- cualquier falla de esta parte es SIN DATOS de esta parte
        return {'error': '%s: %s' % (type(e).__name__, e)}


def frontmatter(texto):
    """Devuelve (dict, cuerpo) con un YAML minimo: claves de primer nivel, escalares de una linea o
    bloques > / | con sus lineas indentadas. Alcanza para name y description; lo demas se ignora."""
    if not texto.startswith('---\n'):
        return None, texto
    fin = texto.find('\n---', 4)
    if fin < 0:
        return None, texto
    bloque = texto[4:fin]
    cuerpo = texto[fin + 4:]
    datos = {}
    lineas = bloque.split('\n')
    i = 0
    while i < len(lineas):
        m = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', lineas[i])
        if not m:
            i += 1
            continue
        clave, valor = m.group(1), m.group(2).strip()
        if valor in ('>', '>-', '|', '|-', '>+', '|+'):
            partes = []
            i += 1
            while i < len(lineas) and (lineas[i].startswith(' ') or lineas[i].strip() == ''):
                partes.append(lineas[i].strip())
                i += 1
            if valor.startswith('>'):
                # plegado: las lineas se unen con espacio, una linea vacia es un salto
                texto_v, parrafos, actual = '', [], []
                for p in partes:
                    if p == '':
                        parrafos.append(' '.join(actual))
                        actual = []
                    else:
                        actual.append(p)
                parrafos.append(' '.join(actual))
                texto_v = '\n'.join(parrafos).strip()
            else:
                texto_v = '\n'.join(partes).strip()
            datos[clave] = texto_v
            continue
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in '"\'':
            valor = valor[1:-1]
        datos[clave] = valor
        i += 1
    return datos, cuerpo


def revisar(carpeta, raiz_rel):
    nombre_carpeta = os.path.basename(carpeta)
    ruta = os.path.join(carpeta, 'SKILL.md')
    rel = (raiz_rel + '/' + nombre_carpeta + '/SKILL.md').replace('\\', '/')
    hallazgos, avisos = [], []
    if not os.path.isfile(ruta):
        return {'skill': rel, 'hallazgos': ['no tiene SKILL.md'], 'avisos': []}
    raw = open(ruta, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        hallazgos.append('tiene BOM UTF-8 (rompe el frontmatter)')
        raw = raw[3:]
    texto = raw.decode('utf-8', errors='replace').replace('\r\n', '\n')
    datos, cuerpo = frontmatter(texto)
    if datos is None:
        hallazgos.append('sin frontmatter YAML (--- ... ---) al inicio')
        return {'skill': rel, 'hallazgos': hallazgos, 'avisos': avisos}
    nombre = datos.get('name', '')
    if not nombre:
        hallazgos.append('falta name')
    else:
        if len(nombre) > MAX_NOMBRE:
            hallazgos.append('name de %d caracteres (maximo %d)' % (len(nombre), MAX_NOMBRE))
        if not NOMBRE.match(nombre):
            hallazgos.append('name "%s" no es minusculas/digitos/guiones simples' % nombre)
        if nombre != nombre_carpeta:
            hallazgos.append('name "%s" distinto de la carpeta "%s"' % (nombre, nombre_carpeta))
    desc = datos.get('description', '')
    if not desc.strip():
        hallazgos.append('falta description')
    elif len(desc) > MAX_DESC:
        hallazgos.append('description de %d caracteres (maximo %d): Gemini CLI y opencode la rechazan o la cortan' % (len(desc), MAX_DESC))
    if nombre_carpeta not in VENDIDAS:
        for base, _dirs, files in os.walk(carpeta):
            for f in sorted(files):
                if not f.endswith('.md'):
                    continue
                cuerpo_md = open(os.path.join(base, f), 'rb').read().decode('utf-8', errors='replace')
                for n_linea, linea in enumerate(cuerpo_md.split('\n'), 1):
                    for frase in FRASES_MUERTAS:
                        if frase in linea:
                            rel_md = os.path.relpath(os.path.join(base, f), carpeta).replace(os.sep, '/')
                            hallazgos.append('frase muerta "%s" en %s:%d (manda a un flujo que ya no existe)' % (frase, rel_md, n_linea))
    lineas = texto.count('\n') + 1
    if lineas > MAX_LINEAS:
        avisos.append('SKILL.md de %d lineas (la especificacion recomienda menos de %d; mover detalle a references/)' % (lineas, MAX_LINEAS))
    caracteres = len(texto)
    if nombre_carpeta not in VENDIDAS:
        if caracteres > MAX_CARACTERES:
            hallazgos.append('SKILL.md de %d caracteres (maximo %d, ~5.000 tokens): al compactar, Claude Code la re-inyecta '
                             'cortada y se pierde el final; lo que no se negocia, arriba, y el detalle a references/' % (caracteres, MAX_CARACTERES))
        elif caracteres > AVISO_CARACTERES:
            avisos.append('SKILL.md de %d caracteres (mas de %d): cerca del tope de %d que sobrevive a la compactacion'
                          % (caracteres, AVISO_CARACTERES, MAX_CARACTERES))
    return {'skill': rel, 'name': nombre, 'description_len': len(desc), 'lineas': lineas, 'caracteres': caracteres,
            'hallazgos': hallazgos, 'avisos': avisos}


def main():
    ap = argparse.ArgumentParser(description='Verifica los SKILL.md contra la especificacion de Agent Skills.')
    ap.add_argument('raiz', nargs='?', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    raiz = os.path.abspath(a.raiz)
    resultados = []
    for r in RAICES:
        base = os.path.join(raiz, r)
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            carpeta = os.path.join(base, d)
            if os.path.isdir(carpeta) and not d.startswith('.'):
                resultados.append(revisar(carpeta, r))
    if not resultados:
        print('SIN DATOS -- no hay carpetas de skills debajo de %s' % raiz)
        return SIN_DATOS
    con_hallazgo = [x for x in resultados if x['hallazgos']]
    con_aviso = [x for x in resultados if x['avisos']]
    conteos = conteo(raiz)
    pu = puerta(raiz)
    sin_ruteo = ruteo(raiz, pu.get('puerta_de'))
    probs_puerta = pu.get('problemas') or []
    hay_hallazgo = bool(con_hallazgo or conteos or sin_ruteo or probs_puerta)
    rc = HALLAZGO if hay_hallazgo else (SIN_DATOS if 'error' in pu else OK)
    veredicto = ['OK', 'HALLAZGO', 'SIN DATOS'][rc]
    if a.json:
        print(json.dumps({'veredicto': veredicto, 'skills': len(resultados), 'resultados': resultados, 'conteo': conteos,
                          'ruteo': sin_ruteo, 'puerta': {k: v for k, v in pu.items() if k != 'puerta_de'}},
                         ensure_ascii=True, indent=1))
    else:
        print('%s -- %d SKILL.md revisados, %d con hallazgo, %d con aviso; conteos y listas: %s; ruteo: %s; puerta: %s' % (
            veredicto, len(resultados), len(con_hallazgo), len(con_aviso),
            '%d problema(s)' % len(conteos) if conteos else
            ('al dia' if documentos_de_conteo(raiz) else 'no se verificaron (no hay documentos que los anuncien)'),
            'no se verifico (no hay skill %s)' % ORQUESTADOR if sin_ruteo is None else
            ('%d sin ruteo escrito' % len(sin_ruteo) if sin_ruteo else 'al dia'),
            'SIN DATOS (no se pudo cargar bin/puerta-skills.py: %s)' % pu['error'] if 'error' in pu else
            ('no adoptada (ninguna skill declara metadata.seccion)' if not pu['adoptada'] else
             ('%d problema(s)' % len(probs_puerta) if probs_puerta else 'al dia'))))
        for h in conteos:
            print('  HALLAZGO conteo: %s' % h)
        if sin_ruteo:
            print('  HALLAZGO ruteo: %s no esta(n) nombrada(s) en AGENTS.md ni en la skill %s, ni la puerta de su '
                  'seccion: su unico disparo es la descripcion, que se cae del listado cuando hay muchas skills. Va una '
                  'linea de ruteo, con el nombre entre acentos graves (o el de la puerta, si la skill declara '
                  'metadata.seccion).' % (' '.join(sin_ruteo), ORQUESTADOR))
        for codigo, texto in probs_puerta:
            print('  HALLAZGO puerta %s: %s' % (codigo, texto))
        for n in pu.get('notas') or []:
            print('  AVISO    puerta: %s' % n)
        for x in con_hallazgo:
            for h in x['hallazgos']:
                print('  HALLAZGO %s: %s' % (x['skill'], h))
        for x in con_aviso:
            for v in x['avisos']:
                print('  AVISO    %s: %s' % (x['skill'], v))
        print('  Regla: name == carpeta, [a-z0-9-], <= %d; description 1..%d caracteres; sin BOM; sin frases muertas (%s). Fuente: agentskills.io/specification' % (MAX_NOMBRE, MAX_DESC, ', '.join(FRASES_MUERTAS)))
    return rc


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
