#!/usr/bin/env python3
"""Prueba de bin/relevar-config-ia.py sobre un proyecto de mentira con configuracion de Claude Code.
Se corre:  python -B bin/probar-relevar-config-ia.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SCRIPT = os.path.join(AQUI, 'relevar-config-ia.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    print('== relevar-config-ia')
    app = tempfile.mkdtemp(prefix='probar-relevar-')
    escribir(app, 'CLAUDE.md', '# Proyecto X\n\n## Comandos\n```bash\nnpm run test\nnpm run build\n```\n\nAntes de subir corre `pnpm lint` y `cargo test --workspace`.\n\n## Reglas\n- Always write code comments in English.\n- Never commit secrets.\n- Nunca uses any en TypeScript.\n- **Secretos en el Credential Manager**: nada en archivos.\n')
    escribir(app, '.claude/skills/desarrollo/SKILL.md', '---\nname: desarrollo\ndescription: la skill propia del proyecto\n---\n')
    escribir(app, '.claude/skills/deploy/SKILL.md', '---\nname: deploy\ndescription: despliega a produccion\n---\n')
    escribir(app, '.claude/commands/revisar.md', 'revisa\n')
    escribir(app, '.mcp.json', '{"mcpServers": {"github": {"command": "npx"}}}\n')
    escribir(app, 'src/index.ts', 'export const x = 1;\n')
    rc, out = correr(app, '--nucleo', RAIZ, '--json')
    d = json.loads(out) if rc == 0 else {}
    caso('corre y devuelve JSON (0)', rc == 0 and d, out[:300])
    if d:
        caso('encuentra CLAUDE.md con sus encabezados', any(i['archivo'] == 'CLAUDE.md' and 'Comandos' in i['encabezados'] for i in d['instrucciones']))
        caso('saca los comandos de build/test, tambien los inline', sorted(c['comando'] for c in d['comandos']) == ['cargo test --workspace', 'npm run build', 'npm run test', 'pnpm lint'], str(d['comandos']))
        caso('saca las reglas duras (4, incluida la de negrita)', len(d['reglas_duras']) == 4, str(d['reglas_duras']))
        caso('detecta el choque de idioma', len(d['idioma']) == 1)
        caso('lista las skills propias y la colision con el nucleo (desarrollo)', sorted(s['name'] for s in d['skills']) == ['deploy', 'desarrollo'] and d['colisiones_de_nombre'] == ['desarrollo'])
        caso('comandos de Claude y servidores MCP', d['comandos_claude'] == ['.claude/commands/revisar.md'] and d['mcp'][0]['servidores'] == ['github'])
        caso('propone destinos en el Cerebro', any('tdd-stack' in x['destino'] for x in d['destinos']) and any('CHOQUE' in x['destino'] for x in d['destinos']))
    rc, out = correr(app, '--nucleo', RAIZ)
    caso('en texto imprime el relevamiento y el choque de idioma', rc == 0 and 'RELEVAMIENTO' in out and 'CHOQUE de idioma' in out and 'COLISIONES' in out, out[:300])
    vacio = tempfile.mkdtemp(prefix='probar-relevar-vacio-')
    escribir(vacio, 'src/main.py', 'print(1)\n')
    rc, out = correr(vacio)
    caso('sin configuracion de IA: SIN DATOS (2) y manda a absorber-aplicacion', rc == 2 and 'absorber-aplicacion' in out)
    rc, out = correr(os.path.join(vacio, 'no-existe'))
    caso('ruta inexistente: SIN DATOS (2)', rc == 2)
    for d_ in (app, vacio):
        shutil.rmtree(d_, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
