#!/usr/bin/env python3
"""Prueba de bin/verificar-skills.py sobre skills de mentira en una carpeta temporal, y sobre este repo.
Se corre:  python -B bin/probar-verificar-skills.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'verificar-skills.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def skill(raiz, carpeta, texto, bom=False):
    d = os.path.join(raiz, 'cerebro-digital', 'configuracion-ia', 'skills', carpeta)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'SKILL.md'), 'wb') as h:
        h.write((b'\xef\xbb\xbf' if bom else b'') + texto.encode('utf-8'))


def main():
    tmp = tempfile.mkdtemp(prefix='probar-skills-')
    print('== verificar-skills')
    skill(tmp, 'bien', '---\nname: bien\ndescription: >-\n  Hace algo util.\n  Usar cuando se pida.\n---\n\n# Bien\n')
    skill(tmp, 'otro-nombre', '---\nname: nombre-distinto\ndescription: x\n---\n')
    skill(tmp, 'larga', '---\nname: larga\ndescription: ' + ('a' * 1100) + '\n---\n')
    skill(tmp, 'Mayus', '---\nname: Mayus\ndescription: x\n---\n')
    skill(tmp, 'sin-frontmatter', '# Solo cuerpo\n')
    skill(tmp, 'sin-descripcion', '---\nname: sin-descripcion\n---\n')
    skill(tmp, 'con-bom', '---\nname: con-bom\ndescription: x\n---\n', bom=True)
    skill(tmp, 'con-frase-muerta', '---\nname: con-frase-muerta\ndescription: x\n---\n\nEsta skill es solo para Orca.\n')
    d_ref = os.path.join(tmp, 'cerebro-digital', 'configuracion-ia', 'skills', 'con-frase-muerta', 'references')
    os.makedirs(d_ref)
    open(os.path.join(d_ref, 'nota.md'), 'w', encoding='utf-8').write('Fuera de Orca se usa trabajar-con-intellij.\n')
    skill(tmp, 'muy-larga', '---\nname: muy-larga\ndescription: x\n---\n' + ('linea\n' * 520))
    # Tamano frente a la compactacion: Claude Code re-inyecta cada skill usada hasta ~5.000 tokens.
    # Los bordes, exactos (un mutante > por >= tiene que caer): el archivo entero, frontmatter incluido.
    def de_tamano(nombre, total, crlf=False):
        cab = '---\nname: %s\ndescription: x\n---\n' % nombre
        texto = cab + 'a' * (total - len(cab))
        skill(tmp, nombre, texto.replace('\n', '\r\n') if crlf else texto)
    de_tamano('pesada', 12501)
    de_tamano('tope-justo', 12500)
    de_tamano('gorda', 12001)
    de_tamano('justa', 12000)
    de_tamano('archify', 20000)
    de_tamano('con-crlf', 12000, crlf=True)   # 12000 contando \n: con \r\n pesaria mas, y no tiene que avisar
    rc, out = correr(tmp, '--json')
    d = json.loads(out)
    por = {x['skill'].split('/')[-2]: x for x in d['resultados']}
    caso('con hallazgos devuelve 1 y HALLAZGO', rc == 1 and d['veredicto'] == 'HALLAZGO', out[:200])
    caso('la skill bien formada no tiene hallazgos', por['bien']['hallazgos'] == [] and por['bien']['description_len'] == len('Hace algo util. Usar cuando se pida.'))
    caso('name distinto de la carpeta', any('distinto de la carpeta' in h for h in por['otro-nombre']['hallazgos']))
    caso('description de mas de 1024', any('1024' in h for h in por['larga']['hallazgos']))
    caso('name con mayusculas', any('minusculas' in h for h in por['Mayus']['hallazgos']))
    caso('sin frontmatter', any('frontmatter' in h for h in por['sin-frontmatter']['hallazgos']))
    caso('sin description', any('description' in h for h in por['sin-descripcion']['hallazgos']))
    caso('con BOM', any('BOM' in h for h in por['con-bom']['hallazgos']))
    caso('frase muerta en SKILL.md y en references/: dos hallazgos con archivo y linea', sorted(h.split(' en ')[1].split(':')[0] for h in por['con-frase-muerta']['hallazgos'] if 'frase muerta' in h) == ['SKILL.md', 'references/nota.md'], str(por['con-frase-muerta']['hallazgos']))
    caso('mas de 500 lineas es AVISO, no hallazgo', por['muy-larga']['hallazgos'] == [] and any('500' in v for v in por['muy-larga']['avisos']))
    caso('12501 caracteres es HALLAZGO y dice que se corta al compactar', any('12500' in h and 'compact' in h for h in por['pesada']['hallazgos']), str(por['pesada']))
    caso('12500 justos no es hallazgo (es AVISO)', por['tope-justo']['hallazgos'] == [] and any('12000' in v for v in por['tope-justo']['avisos']), str(por['tope-justo']))
    caso('12001 caracteres es AVISO, no hallazgo', por['gorda']['hallazgos'] == [] and any('12000' in v for v in por['gorda']['avisos']), str(por['gorda']))
    caso('12000 justos no dice nada del tamano', por['justa']['hallazgos'] == [] and por['justa']['avisos'] == [], str(por['justa']))
    caso('con CRLF se mide como LF (12000 no avisa)', por['con-crlf']['avisos'] == [] and por['con-crlf'].get('caracteres') == 12000, str(por['con-crlf']))
    caso('una skill vendida no se mide por tamano (no se edita)', not any('compact' in h for h in por['archify']['hallazgos'] + por['archify']['avisos']), str(por['archify']))
    caso('el reporte trae los caracteres de cada SKILL.md', por['pesada'].get('caracteres') == 12501)

    solo_bien = tempfile.mkdtemp(prefix='probar-skills-ok-')
    skill(solo_bien, 'bien', '---\nname: bien\ndescription: "Hace algo util."\n---\n')
    rc, out = correr(solo_bien)
    caso('solo skills bien formadas: 0 y OK', rc == 0 and out.startswith('OK'), out[:200])

    vacio = tempfile.mkdtemp(prefix='probar-skills-vacio-')
    rc, out = correr(vacio)
    caso('sin skills: SIN DATOS (2)', rc == 2)

    rc, out = correr(os.path.dirname(AQUI))
    caso('las skills de ESTE repositorio cumplen la especificacion', rc == 0, out[:600])

    cuenta = tempfile.mkdtemp(prefix='probar-skills-conteo-')
    for n in ('una', 'otra'):
        skill(cuenta, n, '---\nname: %s\ndescription: x\n---\n' % n)
    docs = {'AGENTS.md': '**2 habilidades**\n', 'README.md': 'Skills del Ecosistema (2 habilidades): una, otra\n',
            'INSTALACION.md': 'Las **2 skills**\n', os.path.join('cerebro-digital', 'index.md'): 'una y otra\n'}
    for rel, texto in docs.items():
        with open(os.path.join(cuenta, rel), 'w', encoding='utf-8', newline='\n') as h:
            h.write(texto)
    rc, out = correr(cuenta)
    caso('conteos y listas al dia: OK', rc == 0, out[:300])
    skill(cuenta, 'tercera', '---\nname: tercera\ndescription: x\n---\n')
    rc, out = correr(cuenta, '--json')
    conteo = json.loads(out).get('conteo', [])
    caso('una skill nueva sin actualizar los documentos: HALLAZGO por cada numero y cada lista que no cierran',
         rc == 1 and json.loads(out).get('veredicto') == 'HALLAZGO' and len(conteo) == 5
         and all('tercera' in c for c in conteo if 'no nombra' in c), str(conteo))
    with open(os.path.join(cuenta, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('Son tres habilidades.\n')
    rc, out = correr(cuenta, '--json')
    caso('si cambio la redaccion y el patron no aparece: HALLAZGO, no OK', any('no encontre el conteo' in c for c in json.loads(out).get('conteo', [])),
         out[:300])
    shutil.rmtree(cuenta, ignore_errors=True)

    # Ruteo escrito: cada skill tiene que estar nombrada en un texto que se carga siempre (AGENTS.md o la skill del
    # orquestador). La descripcion sola no alcanza: Claude Code la saca del listado cuando hay muchas skills.
    rut = tempfile.mkdtemp(prefix='probar-skills-ruteo-')
    skill(rut, 'cerebro-orquestador', '---\nname: cerebro-orquestador\ndescription: x\n---\n\nUn diagrama va a `una`. Lo otro, a `una-mas-larga`.\n')
    for n in ('una', 'otra'):
        skill(rut, n, '---\nname: %s\ndescription: x\n---\n' % n)
    with open(os.path.join(rut, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**3 habilidades**\n\nToda solicitud pasa por `cerebro-orquestador`. Lo de tickets, por [[otra]].\n')
    rc, out = correr(rut, '--json')
    d = json.loads(out)
    caso('ruteo al dia: cada skill nombrada en AGENTS.md o en el orquestador (con acentos graves o doble corchete)',
         rc == 0 and d.get('ruteo') == [], out[:300])
    rc, out = correr(rut)
    caso('ruteo al dia: lo dice el resumen', rc == 0 and 'ruteo: al dia' in out, out[:300])
    skill(rut, 'una-mas', '---\nname: una-mas\ndescription: x\n---\n')
    skill(rut, 'tercera', '---\nname: tercera\ndescription: x\n---\n')
    with open(os.path.join(rut, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**5 habilidades**\n\nToda solicitud pasa por `cerebro-orquestador`. Lo de tickets, por [[otra]]. La tercera no se nombra entre marcas.\n')
    rc, out = correr(rut, '--json')
    d = json.loads(out)
    caso('una skill que ningun texto fijo nombra: HALLAZGO, con su nombre',
         rc == 1 and d.get('veredicto') == 'HALLAZGO' and 'tercera' in d.get('ruteo', []), out[:300])
    caso('un nombre que solo aparece adentro de otro mas largo no cuenta como ruteo',
         'una-mas' in d.get('ruteo', []) and 'una' not in d.get('ruteo', []), str(d.get('ruteo')))
    rc, out = correr(rut)
    caso('sin ruteo: el texto dice cuales y por que importa', rc == 1 and 'HALLAZGO ruteo' in out and 'tercera' in out and 'listado' in out, out[:500])
    shutil.rmtree(os.path.join(rut, 'cerebro-digital', 'configuracion-ia', 'skills', 'cerebro-orquestador'))
    with open(os.path.join(rut, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**4 habilidades**\n')
    rc, out = correr(rut)
    caso('sin la skill del orquestador no hay ruteo que verificar: lo dice y no frena', rc == 0 and 'ruteo: no se verifico' in out, out[:300])
    shutil.rmtree(rut, ignore_errors=True)

    # Puerta de Skills: una skill con metadata.seccion se rutea por la puerta de su seccion (la puerta la conoce por su
    # indice generado); y los problemas de la Puerta (bin/puerta-skills.py) llegan aca como HALLAZGO.
    pu = tempfile.mkdtemp(prefix='probar-skills-puerta-')

    def con_seccion(n, seccion, puerta=False, apunta=True):
        # la puerta de una seccion de varias skills apunta a su indice (si no, HALLAZGO puerta-sin-indice)
        skill(pu, n, '---\nname: %s\ndescription: Hace %s.\nmetadata:\n  seccion: %s\n%s---\n%s'
              % (n, n, seccion, '  rol: puerta\n' if puerta else '',
                 '\nLas otras skills: `references/indice-seccion.md`.\n' if (puerta and apunta) else ''))

    def generar():
        r = subprocess.run([sys.executable, '-I', os.path.join(AQUI, 'puerta-skills.py'), '--generar', '--raiz', pu],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        return r.returncode

    con_seccion('cerebro-orquestador', 'conocimiento', puerta=True)
    con_seccion('una', 'conocimiento')
    con_seccion('otra', 'tickets', puerta=True)
    con_seccion('tercera', 'tickets')
    with open(os.path.join(pu, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**4 habilidades**\n\nToda solicitud pasa por `cerebro-orquestador`. Lo de tickets, por [[otra]].\n')
    os.makedirs(os.path.join(pu, '.claude'))
    with open(os.path.join(pu, '.claude', 'settings.json'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('{\n  "hooks": {}\n}\n')
    caso('puerta: el repo de mentira se genera', generar() == 0)
    rc, out = correr(pu, '--json')
    d = json.loads(out)
    caso('ruteo por la puerta: una skill no nombrada pasa si la puerta de su seccion esta nombrada',
         rc == 0 and d.get('ruteo') == [] and d.get('puerta', {}).get('problemas') == [], out[:400])
    rc, out = correr(pu)
    caso('puerta al dia: lo dice el resumen', rc == 0 and 'puerta: al dia' in out, out[:300])
    con_seccion('cuarta', 'diseno', puerta=True)
    con_seccion('quinta', 'diseno')
    with open(os.path.join(pu, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**6 habilidades**\n\nToda solicitud pasa por `cerebro-orquestador`. Lo de tickets, por [[otra]].\n')
    generar()
    rc, out = correr(pu, '--json')
    d = json.loads(out)
    caso('ruteo por la puerta: ni la skill ni su puerta nombradas: HALLAZGO, las dos',
         rc == 1 and 'quinta' in d.get('ruteo', []) and 'cuarta' in d.get('ruteo', []) and 'tercera' not in d.get('ruteo', []),
         out[:400])
    with open(os.path.join(pu, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**6 habilidades**\n\nToda solicitud pasa por `cerebro-orquestador`. Tickets, [[otra]]. Diseno, `cuarta`.\n')
    os.remove(os.path.join(pu, 'cerebro-digital', 'configuracion-ia', 'skills', 'otra', 'references', 'indice-seccion.md'))
    rc, out = correr(pu, '--json')
    d = json.loads(out)
    caso('un problema de la Puerta (indice ausente) llega como HALLAZGO',
         rc == 1 and d.get('veredicto') == 'HALLAZGO' and d.get('ruteo') == []
         and [p[0] for p in d.get('puerta', {}).get('problemas', [])] == ['indice'], out[:400])
    rc, out = correr(pu)
    caso('el problema de la Puerta se lee en el texto, con como arreglarlo',
         rc == 1 and 'HALLAZGO puerta' in out and '--generar' in out, out[:600])
    generar()
    con_seccion('otra', 'tickets', puerta=True, apunta=False)
    rc, out = correr(pu, '--json')
    d = json.loads(out)
    caso('una puerta que no apunta a su indice llega como HALLAZGO (el ruteo por la puerta no vale sin eso)',
         rc == 1 and [p[0] for p in d.get('puerta', {}).get('problemas', [])] == ['puerta-sin-indice'], out[:400])
    con_seccion('otra', 'tickets', puerta=True)
    con_seccion('sin-puerta-escrita', 'modernizacion')
    with open(os.path.join(pu, 'AGENTS.md'), 'w', encoding='utf-8', newline='\n') as h:
        h.write('**7 habilidades**\n\n`cerebro-orquestador`, [[otra]], `cuarta`, `sin-puerta-escrita`.\n')
    rc, out = correr(pu, '--json')
    d = json.loads(out)
    caso('una seccion sin puerta llega como HALLAZGO aunque la skill este nombrada',
         rc == 1 and 'sin-puerta' in [p[0] for p in d.get('puerta', {}).get('problemas', [])], out[:400])
    shutil.rmtree(pu, ignore_errors=True)

    rc, out = correr(solo_bien)
    caso('la Puerta no adoptada (ninguna metadata.seccion): no frena y lo dice', rc == 0 and 'puerta: no adoptada' in out,
         out[:300])

    # Si bin/puerta-skills.py no se puede cargar, esa parte es SIN DATOS: nunca OK.
    sin_mod = tempfile.mkdtemp(prefix='probar-skills-sin-puerta-')
    shutil.copy(SCRIPT, os.path.join(sin_mod, 'verificar-skills.py'))
    r = subprocess.run([sys.executable, '-I', os.path.join(sin_mod, 'verificar-skills.py'), solo_bien],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('sin bin/puerta-skills.py al lado: SIN DATOS (2), no OK', r.returncode == 2 and 'puerta' in r.stdout,
         r.stdout[:300])
    shutil.rmtree(sin_mod, ignore_errors=True)

    for d_ in (tmp, solo_bien, vacio):
        shutil.rmtree(d_, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
