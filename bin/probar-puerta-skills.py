#!/usr/bin/env python3
"""Prueba de bin/puerta-skills.py sin abrir Claude: como lee la respuesta de la medicion y que veredicto da, y la
fase 1 sobre un repo de mentira (secciones, indices, skillOverrides, cada HALLAZGO, la Puerta no adoptada).
Se corre:  python -B bin/probar-puerta-skills.py   -> OK o FALLA, con el detalle de cada caso."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def cargar():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('puerta_skills', os.path.join(AQUI, 'puerta-skills.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def salida(ruta, resultado):
    with open(ruta, 'w', encoding='utf-8') as h:
        h.write('Warning: no stdin data received\n')
        h.write(json.dumps({'type': 'result', 'result': resultado}))


SCRIPT = os.path.join(AQUI, 'puerta-skills.py')
INTRO = ('Lo genera `python -I bin/puerta-skills.py --generar` con la primera oraci\u00f3n de cada descripci\u00f3n: '
         'no se edita a mano.')
SETTINGS = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'python -I bin/tendencia.py', 'timeout': 20}]}]},
            'permissions': {'deny': ['Agent(orquestador-seguridad)']}}


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return r.returncode, r.stdout + r.stderr


PUNTERO = 'Las otras skills de la seccion, con para que sirve cada una: `references/indice-seccion.md`.\n'


def skill(raiz, n, seccion=None, rol=None, desc='x', cuerpo=''):
    d = os.path.join(raiz, 'cerebro-digital', 'configuracion-ia', 'skills', n)
    os.makedirs(d, exist_ok=True)
    meta = ''
    if seccion or rol:
        meta = 'metadata:\n' + ('  seccion: %s\n' % seccion if seccion else '') + \
               ('  rol: %s        # solo en la puerta\n' % rol if rol else '')
    with open(os.path.join(d, 'SKILL.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('---\nname: %s\ndescription: %s\n%s---\n\n# %s\n\n%s' % (n, desc, meta, n, cuerpo))


def escribir_settings(raiz, datos, crlf=False):
    os.makedirs(os.path.join(raiz, '.claude'), exist_ok=True)
    texto = json.dumps(datos, indent=2) + '\n'
    with open(os.path.join(raiz, '.claude', 'settings.json'), 'wb') as h:
        h.write((texto.replace('\n', '\r\n') if crlf else texto).encode('utf-8'))


def leer_bytes(raiz, rel):
    ruta = os.path.join(raiz, rel)
    return open(ruta, 'rb').read() if os.path.isfile(ruta) else None


def indice_rel(puerta):
    return os.path.join('cerebro-digital', 'configuracion-ia', 'skills', puerta, 'references', 'indice-seccion.md')


def armar(base, nombre):
    """Un repo de mentira con la Puerta adoptada: cuatro secciones, una con una skill ASIGNADA (archify)."""
    raiz = os.path.join(base, nombre)
    skill(raiz, 'orq', 'conocimiento', 'puerta', 'Coordina todo. Usar siempre.', PUNTERO)
    skill(raiz, 'analista', 'conocimiento', None, '>-\n  Extrae requisitos\n  de documentos. Segunda oracion.')
    skill(raiz, 'citada', 'conocimiento', None, '"Con comillas: y dos puntos. Y mas."')
    skill(raiz, 'justa', 'conocimiento', None, 'b' * 299 + '. Despues.')
    skill(raiz, 'larga', 'conocimiento', None, ('palabra ' * 60).strip())
    skill(raiz, 'pasada', 'conocimiento', None, 'c' * 301 + '. Otra.')
    # bordes del corte en el ultimo espacio antes de 300: una palabra que termina justo en 300, y una que la cruza
    skill(raiz, 'borde-justo', 'conocimiento', None, 'a' * 295 + ' bbbb cccc')
    skill(raiz, 'borde-pasado', 'conocimiento', None, 'a' * 295 + ' bbbbb c')
    skill(raiz, 'tick', 'tickets', 'puerta', 'Puerta de tickets.', PUNTERO)
    skill(raiz, 'redactar', 'tickets', None, 'Redacta tickets. Usar cuando se pida.')
    skill(raiz, 'sola', 'diseno', 'puerta', 'Disena.')
    skill(raiz, 'arq', 'arquitectura', 'puerta', 'Arquitectura.', PUNTERO)
    skill(raiz, 'archify', None, None, 'Create diagrams. Use when asked.')
    escribir_settings(raiz, SETTINGS)
    return raiz


def codigos(ps, raiz):
    return sorted(set(c for c, _ in ps.problemas(raiz)))


def fase1(ps, tmp):
    print('== puerta-skills: secciones, indices y overrides (fase 1)')
    caso('archify es una skill ASIGNADA a arquitectura (vendida: no se edita)', ps.ASIGNADAS.get('archify') == 'arquitectura')
    raiz = armar(tmp, 'repo')
    s = ps.secciones(raiz)
    esperado = {'conocimiento': {'puerta': 'orq', 'puertas': ['orq'],
                                 'skills': ['analista', 'borde-justo', 'borde-pasado', 'citada', 'justa', 'larga',
                                            'orq', 'pasada']},
                'tickets': {'puerta': 'tick', 'puertas': ['tick'], 'skills': ['redactar', 'tick']},
                'diseno': {'puerta': 'sola', 'puertas': ['sola'], 'skills': ['sola']},
                'arquitectura': {'puerta': 'arq', 'puertas': ['arq'], 'skills': ['archify', 'arq']}}
    caso('secciones(): la puerta, las puertas y las skills de cada seccion, ordenadas', s == esperado, str(s))
    caso('la Puerta esta adoptada', ps.adoptada(raiz) is True)

    ind = ps.indice_esperado(raiz, 'conocimiento')
    esperado_ind = ('# \u00cdndice de la secci\u00f3n conocimiento\n\n' + INTRO + '\n\n'
                    '- `analista`: Extrae requisitos de documentos.\n'
                    '- `borde-justo`: ' + 'a' * 295 + ' bbbb...\n'
                    '- `borde-pasado`: ' + 'a' * 295 + '...\n'
                    '- `citada`: Con comillas: y dos puntos.\n'
                    '- `justa`: ' + 'b' * 299 + '.\n'
                    '- `larga`: ' + ' '.join(['palabra'] * 37) + '...\n'
                    '- `pasada`: ' + 'c' * 300 + '...\n')
    caso('indice: encabezado, aviso de generado y una linea por cada OTRA skill, ordenadas', ind == esperado_ind,
         repr(ind)[:600])
    caso('indice: la descripcion plegada se corta en la primera oracion', '`analista`: Extrae requisitos de documentos.\n' in ind)
    caso('indice: una oracion de 300 justos entra entera', '- `justa`: ' + 'b' * 299 + '.\n' in ind)
    caso('indice: de 301 en adelante y sin espacios se corta a 300', '- `pasada`: ' + 'c' * 300 + '...\n' in ind)
    caso('indice: el corte va en el ultimo espacio antes de 300, no a mitad de palabra',
         '- `larga`: ' + ' '.join(['palabra'] * 37) + '...\n' in ind)
    caso('indice: una palabra que termina justo en 300 entra entera', '- `borde-justo`: ' + 'a' * 295 + ' bbbb...\n' in ind)
    caso('indice: una palabra que cruza el 300 queda afuera', '- `borde-pasado`: ' + 'a' * 295 + '...\n' in ind)
    caso('indice: una seccion de una sola skill no tiene indice (None)', ps.indice_esperado(raiz, 'diseno') is None,
         repr(ps.indice_esperado(raiz, 'diseno')))
    caso('indice: la ASIGNADA aparece en el de su seccion', '- `archify`: Create diagrams.\n' in ps.indice_esperado(raiz, 'arquitectura'))

    ov = ps.overrides_esperados(raiz)
    nombres = ['analista', 'archify', 'borde-justo', 'borde-pasado', 'citada', 'justa', 'larga', 'pasada', 'redactar']
    caso('overrides: name-only para cada skill que no es puerta (ASIGNADA incluida), ordenados',
         list(ov.items()) == [(n, 'name-only') for n in nombres], str(ov))

    c = codigos(ps, raiz)
    caso('sin generar: HALLAZGO de indice y de overrides', c == ['indice', 'overrides'], str(ps.problemas(raiz)))
    caso('el hallazgo de indice dice como arreglarlo',
         any('python -I bin/puerta-skills.py --generar' in t for k, t in ps.problemas(raiz) if k == 'indice'))
    rc, out = correr('--verificar', '--raiz', raiz)
    caso('--verificar con problemas: 1, HALLAZGO y lo que no mira', rc == 1 and out.startswith('HALLAZGO')
         and 'NO mira' in out, out[:400])

    antes = leer_bytes(raiz, os.path.join('.claude', 'settings.json'))
    rc, out = correr('--generar', '--dry-run', '--raiz', raiz)
    caso('--generar --dry-run: dice que cambiaria y no escribe nada',
         rc == 0 and 'indice-seccion.md' in out and 'settings.json' in out
         and leer_bytes(raiz, os.path.join('.claude', 'settings.json')) == antes
         and leer_bytes(raiz, indice_rel('orq')) is None, out[:400])

    rc, out = correr('--generar', '--raiz', raiz)
    caso('--generar: 0', rc == 0, out[:400])
    caso('--generar: escribe el indice de cada puerta, con el contenido exacto (UTF-8)',
         all(leer_bytes(raiz, indice_rel(p)) == ps.indice_esperado(raiz, sec).encode('utf-8')
             for p, sec in (('orq', 'conocimiento'), ('tick', 'tickets'), ('arq', 'arquitectura'))))
    caso('--generar: no escribe indice en una skill que no es puerta', leer_bytes(raiz, indice_rel('analista')) is None)
    caso('--generar: no escribe indice en la puerta de una seccion de una sola skill', leer_bytes(raiz, indice_rel('sola')) is None)
    crudo = leer_bytes(raiz, os.path.join('.claude', 'settings.json'))
    d = json.loads(crudo.decode('utf-8'))
    caso('--generar: settings.json con skillOverrides esperados', d.get('skillOverrides') == ov, str(d.get('skillOverrides')))
    caso('--generar: conserva hooks y permissions tal cual, y en su orden',
         list(d) == ['hooks', 'permissions', 'skillOverrides'] and d['hooks'] == SETTINGS['hooks']
         and d['permissions'] == SETTINGS['permissions'], str(list(d)))
    caso('--generar: el formato es indent 2 con LF', crudo == (json.dumps(d, indent=2) + '\n').encode('utf-8'))
    caso('despues de generar: sin problemas', ps.problemas(raiz) == [], str(ps.problemas(raiz)))
    rc, out = correr('--verificar', '--raiz', raiz)
    caso('--verificar al dia: 0 y OK', rc == 0 and out.startswith('OK'), out[:400])

    fotos = {rel: leer_bytes(raiz, rel) for rel in [os.path.join('.claude', 'settings.json')] +
             [indice_rel(p) for p in ('orq', 'tick', 'arq')]}
    rc, out = correr('--generar', '--raiz', raiz)
    caso('--generar dos veces no cambia un byte (idempotente)',
         rc == 0 and all(leer_bytes(raiz, rel) == b for rel, b in fotos.items()), out[:400])
    caso('--generar sin nada que cambiar lo dice', 'nada que cambiar' in out, out[:400])

    crlf = armar(tmp, 'crlf')
    escribir_settings(crlf, SETTINGS, crlf=True)
    correr('--generar', '--raiz', crlf)
    crudo = leer_bytes(crlf, os.path.join('.claude', 'settings.json'))
    caso('--generar: un settings.json con CRLF sigue con CRLF', b'\r\n' in crudo and b'\n' not in crudo.replace(b'\r\n', b''),
         repr(crudo[:80]))

    print('== puerta-skills: cada HALLAZGO')

    def mutado(nombre, cambio):
        r = armar(tmp, nombre)
        correr('--generar', '--raiz', r)
        cambio(r)
        return r

    r = mutado('sin-seccion', lambda r: skill(r, 'analista', None, None, 'Extrae.'))
    caso('una skill de la fuente sin metadata.seccion: HALLAZGO sin-seccion',
         'sin-seccion' in codigos(ps, r) and any('analista' in t for k, t in ps.problemas(r) if k == 'sin-seccion'),
         str(ps.problemas(r)))
    r = mutado('asignada', lambda r: None)
    caso('una ASIGNADA sin metadata no es sin-seccion', 'sin-seccion' not in codigos(ps, r), str(ps.problemas(r)))
    r = mutado('sin-puerta', lambda r: skill(r, 'tick', 'tickets', None, 'Puerta de tickets.'))
    caso('una seccion sin puerta: HALLAZGO sin-puerta',
         'sin-puerta' in codigos(ps, r) and any('tickets' in t for k, t in ps.problemas(r) if k == 'sin-puerta'),
         str(ps.problemas(r)))
    caso('una seccion sin puerta: secciones() da puerta None', ps.secciones(r)['tickets']['puerta'] is None)
    r = mutado('dos-puertas', lambda r: skill(r, 'redactar', 'tickets', 'puerta', 'Redacta.'))
    caso('una seccion con dos puertas: HALLAZGO varias-puertas, con las dos',
         'varias-puertas' in codigos(ps, r) and any('redactar' in t and 'tick' in t for k, t in ps.problemas(r)
                                                    if k == 'varias-puertas'), str(ps.problemas(r)))
    caso('con dos puertas: secciones() da puerta None y las lista', ps.secciones(r)['tickets']['puerta'] is None
         and ps.secciones(r)['tickets']['puertas'] == ['redactar', 'tick'])
    r = mutado('rol-raro', lambda r: skill(r, 'redactar', 'tickets', 'jefa', 'Redacta.'))
    caso('un rol que no es puerta: HALLAZGO rol-invalido', 'rol-invalido' in codigos(ps, r)
         and any('jefa' in t for k, t in ps.problemas(r) if k == 'rol-invalido'), str(ps.problemas(r)))
    r = mutado('sin-indice', lambda r: os.remove(os.path.join(r, indice_rel('orq'))))
    caso('el indice de una puerta ausente: HALLAZGO indice', codigos(ps, r) == ['indice'], str(ps.problemas(r)))

    def tocar_indice(r):
        with open(os.path.join(r, indice_rel('tick')), 'a', encoding='utf-8') as h:
            h.write('- `a-mano`: algo.\n')
    r = mutado('indice-viejo', tocar_indice)
    caso('el indice de una puerta distinto del esperado: HALLAZGO indice', codigos(ps, r) == ['indice']
         and any('tick' in t and '--generar' in t for k, t in ps.problemas(r)), str(ps.problemas(r)))
    r = mutado('skill-nueva', lambda r: skill(r, 'nueva', 'tickets', None, 'Nueva.'))
    caso('una skill nueva sin regenerar: HALLAZGO indice y overrides', codigos(ps, r) == ['indice', 'overrides'],
         str(ps.problemas(r)))

    def sacar_override(r):
        escribir_settings(r, dict(SETTINGS, skillOverrides={n: 'name-only' for n in nombres[1:]}))
    r = mutado('override-falta', sacar_override)
    caso('skillOverrides distinto del esperado: HALLAZGO overrides', codigos(ps, r) == ['overrides']
         and any('analista' in t for k, t in ps.problemas(r)), str(ps.problemas(r)))

    def puerta_con_override(r):
        ov2 = dict(ov)
        ov2['orq'] = 'name-only'
        escribir_settings(r, dict(SETTINGS, skillOverrides=ov2))
    r = mutado('puerta-override', puerta_con_override)
    caso('una puerta con skillOverrides: HALLAZGO puerta-con-override', 'puerta-con-override' in codigos(ps, r)
         and any('orq' in t for k, t in ps.problemas(r) if k == 'puerta-con-override'), str(ps.problemas(r)))

    def indice_en_sola(r):
        os.makedirs(os.path.dirname(os.path.join(r, indice_rel('sola'))), exist_ok=True)
        with open(os.path.join(r, indice_rel('sola')), 'w', encoding='utf-8') as h:
            h.write('viejo\n')
    r = mutado('sobrante-sola', indice_en_sola)
    caso('un indice en la puerta de una seccion de una sola skill: HALLAZGO indice-sobrante',
         codigos(ps, r) == ['indice-sobrante'] and any('sola' in t for k, t in ps.problemas(r)), str(ps.problemas(r)))
    rc, out = correr('--generar', '--raiz', r)
    caso('--generar borra el indice sobrante', rc == 0 and leer_bytes(r, indice_rel('sola')) is None
         and ps.problemas(r) == [], out[:400])

    def cambiar_puerta(r):
        skill(r, 'tick', 'tickets', None, 'Puerta de tickets.')
        skill(r, 'redactar', 'tickets', 'puerta', 'Redacta tickets.', PUNTERO)
    r = mutado('deja-de-ser-puerta', cambiar_puerta)
    caso('una skill que deja de ser puerta: su indice viejo es indice-sobrante',
         {'indice', 'indice-sobrante'} <= set(codigos(ps, r)) and any('tick' in t for k, t in ps.problemas(r)
                                                                if k == 'indice-sobrante'), str(ps.problemas(r)))
    rc, out = correr('--generar', '--raiz', r)
    caso('--generar mueve el indice a la puerta nueva', rc == 0 and leer_bytes(r, indice_rel('tick')) is None
         and leer_bytes(r, indice_rel('redactar')) is not None and ps.problemas(r) == [], out[:400] + str(ps.problemas(r)))

    r = mutado('puerta-muda', lambda r: skill(r, 'tick', 'tickets', 'puerta', 'Puerta de tickets.', 'Cuerpo vacio.\n'))
    caso('la puerta de una seccion de varias skills que no apunta a su indice: HALLAZGO puerta-sin-indice',
         codigos(ps, r) == ['puerta-sin-indice'] and any('tick' in t for k, t in ps.problemas(r)), str(ps.problemas(r)))

    r = mutado('estructura-rota', lambda r: skill(r, 'redactar', 'tickets', 'puerta', 'Redacta.'))
    antes = leer_bytes(r, os.path.join('.claude', 'settings.json'))
    skill(r, 'otra-nueva', 'tickets', None, 'Otra.')
    rc, out = correr('--generar', '--raiz', r)
    caso('--generar con la estructura rota (dos puertas): 1 y no escribe nada',
         rc == 1 and 'varias-puertas' in out and leer_bytes(r, os.path.join('.claude', 'settings.json')) == antes, out[:400])

    print('== puerta-skills: la Puerta no adoptada')
    na = os.path.join(tmp, 'no-adoptada')
    skill(na, 'una', None, None, 'Una.')
    skill(na, 'archify', None, None, 'Diagramas.')
    escribir_settings(na, SETTINGS)
    antes = leer_bytes(na, os.path.join('.claude', 'settings.json'))
    caso('sin ninguna metadata.seccion: no adoptada y sin problemas (no frena)',
         ps.adoptada(na) is False and ps.problemas(na) == [], str(ps.problemas(na)))
    rc, out = correr('--verificar', '--raiz', na)
    caso('--verificar no adoptada: 0 y lo dice', rc == 0 and 'no est' in out and 'adoptada' in out, out[:300])
    rc, out = correr('--generar', '--raiz', na)
    caso('--generar no adoptada: no escribe nada',
         rc == 0 and leer_bytes(na, os.path.join('.claude', 'settings.json')) == antes, out[:300])

    print('== puerta-skills: sin settings.json')
    ss = armar(tmp, 'sin-settings')
    correr('--generar', '--raiz', ss)
    os.remove(os.path.join(ss, '.claude', 'settings.json'))
    caso('sin .claude/settings.json: no es HALLAZGO, queda como nota', ps.problemas(ss) == []
         and any('settings.json' in n for n in ps.notas(ss)), str(ps.problemas(ss)) + str(ps.notas(ss)))


def main():
    try:
        sys.stdout.reconfigure(errors='backslashreplace')
    except (AttributeError, ValueError):
        pass
    ps = cargar()
    tmp = tempfile.mkdtemp(prefix='probar-puerta-')
    try:
        print('== puerta-skills: leer la medicion')
        propias = {'seguridad', 'desarrollo', 'auditar-tarea', 'redactar-tarea'}
        puertas = {'seguridad', 'desarrollo'}
        r = os.path.join(tmp, 'r.json')
        salida(r, 'Aca va:\n```json\n{"con_descripcion": ["desarrollo", "redactar-tarea", "debug"], '
                  '"solo_nombre": ["seguridad", "auditar-tarea", "design:critique"]}\n```')
        m = ps.leer_medicion(r, propias, puertas)
        caso('cuenta el total y los dos grupos', m and m['total'] == 6 and m['con_descripcion'] == 3 and m['solo_nombre'] == 3, str(m))
        caso('separa las del proyecto que quedaron solo por nombre', m and m['propias_solo_nombre'] == ['auditar-tarea', 'seguridad'], str(m))
        caso('separa las puertas que quedaron solo por nombre', m and m['puertas_solo_nombre'] == ['seguridad'], str(m))
        salida(r, 'No pude clasificarlas.')
        caso('sin JSON en la respuesta: None (SIN DATOS), nunca cero', ps.leer_medicion(r, propias, puertas) is None)
        with open(r, 'w', encoding='utf-8') as h:
            h.write('Error: algo fallo\n')
        caso('sin resultado: None (SIN DATOS)', ps.leer_medicion(r, propias, puertas) is None)

        print('== puerta-skills: veredicto')
        ok = {'puertas_solo_nombre': []}
        mal = {'puertas_solo_nombre': ['seguridad']}
        caso('ninguna puerta solo por nombre en la sesion aislada: OK (0)', ps.veredicto({'aislada': ok}) == 0)
        caso('una puerta solo por nombre en la aislada: HALLAZGO (1)', ps.veredicto({'aislada': mal}) == 1)
        caso('la sesion normal informa pero no frena', ps.veredicto({'aislada': ok, 'normal': mal}) == 0)
        caso('sin medicion de la aislada: SIN DATOS (2)', ps.veredicto({'aislada': None, 'normal': ok}) == 2)

        print('== puerta-skills: cuales son las puertas')
        sk = os.path.join(tmp, 'cerebro-digital', 'configuracion-ia', 'skills')
        for n, extra in (('a', 'metadata:\n  seccion: s1\n  rol: puerta\n'), ('b', 'metadata:\n  seccion: s1\n'), ('c', '')):
            os.makedirs(os.path.join(sk, n))
            with open(os.path.join(sk, n, 'SKILL.md'), 'w', encoding='utf-8') as h:
                h.write('---\nname: %s\ndescription: x\n%s---\n' % (n, extra))
        caso('las propias son las carpetas de la fuente', ps.propias(tmp) == {'a', 'b', 'c'}, str(ps.propias(tmp)))
        caso('las puertas salen de metadata.rol', ps.puertas(tmp) == {'a'}, str(ps.puertas(tmp)))

        fase1(ps, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    malos = [e for e in ESPERADOS if not e[1]]
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not malos else 'FALLA', len(ESPERADOS) - len(malos), len(ESPERADOS)))
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
