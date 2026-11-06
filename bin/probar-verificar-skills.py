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

    solo_bien = tempfile.mkdtemp(prefix='probar-skills-ok-')
    skill(solo_bien, 'bien', '---\nname: bien\ndescription: "Hace algo util."\n---\n')
    rc, out = correr(solo_bien)
    caso('solo skills bien formadas: 0 y OK', rc == 0 and out.startswith('OK'), out[:200])

    vacio = tempfile.mkdtemp(prefix='probar-skills-vacio-')
    rc, out = correr(vacio)
    caso('sin skills: SIN DATOS (2)', rc == 2)

    rc, out = correr(os.path.dirname(AQUI))
    caso('las skills de ESTE repositorio cumplen la especificacion', rc == 0, out[:600])

    for d_ in (tmp, solo_bien, vacio):
        shutil.rmtree(d_, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
