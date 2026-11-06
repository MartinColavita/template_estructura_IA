#!/usr/bin/env python3
"""Enchufa un proyecto que YA existe (una carpeta en el Escritorio, con o sin Claude Code) a este nucleo, en un comando.

    python -I bin/adoptar-proyecto.py <ruta-del-proyecto> [--como back|front] [--enlazar|--mover] [--importar-reglas] [--destino <carpeta>] [--dry-run]

Tres estados, nunca dos:  0 = enchufado   1 = FRENA (ya existe el destino, o la ruta no sirve)   2 = SIN DATOS (esto no es un nucleo)

POR QUE EXISTE. "Tengo una carpeta con mi proyecto y quiero sumarle el template" tenia cinco pasos a mano y
dos formas de hacerlo mal (mover el repo adentro del repo del Cerebro y versionarlo, o copiar reglas al
CLAUDE.md del proyecto a ojo). Esto hace lo mecanico, en orden, y deja un informe:
  1. Enlaza (por defecto) o mueve la carpeta del proyecto a back/<nombre> o front/<nombre> del nucleo. Enlazar
     = la carpeta sigue donde estaba (un enlace de directorio: junction en Windows, symlink en el resto); el
     nucleo la ve adentro y .gitignore ya la ignora. Nada del proyecto se versiona en el nucleo.
  2. Corre relevar-config-ia.py (que configuracion de IA trae), inventariar-codigo.py y radiografiar-codigo.py
     (+ --mermaid) y guarda todo en borrador/adopcion/<fecha>/.
  3. Con --importar-reglas, agrega UNA linea al CLAUDE.md del proyecto que importa AGENTS.md del nucleo por
     ruta relativa (si no existe el CLAUDE.md, lo crea con esa linea). Sin la bandera, muestra la linea y no toca.
  4. Dice que sigue: abrir Claude Code en el nucleo y correr absorber-aplicacion (modo documentar), o abrir el
     proyecto con --add-dir <nucleo>.

QUE NO HACE. No modifica el codigo del proyecto, no commitea, no copia reglas al Cerebro (eso es la Consulta
Interactiva, con un "si" por item). Solo biblioteca estandar.
"""

import argparse
import datetime
import os
import subprocess
import sys

OK, FRENA, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def correr(script, *args):
    r = subprocess.run([sys.executable, '-I', os.path.join(RAIZ, 'bin', script)] + list(args),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def enlazar(origen, destino):
    if os.name == 'nt':
        r = subprocess.run(['cmd', '/c', 'mklink', '/J', destino, origen], capture_output=True, text=True, encoding='utf-8', errors='replace')
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    try:
        os.symlink(origen, destino, target_is_directory=True)
        return True, 'symlink'
    except OSError as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser(description='Enchufa un proyecto existente al nucleo.')
    ap.add_argument('ruta')
    ap.add_argument('--como', choices=['back', 'front'], default='back')
    ap.add_argument('--mover', action='store_true', help='mover la carpeta en vez de enlazarla')
    ap.add_argument('--importar-reglas', action='store_true', help='agregar al CLAUDE.md del proyecto la linea que importa AGENTS.md del nucleo')
    ap.add_argument('--destino', default='', help='carpeta destino (por defecto <nucleo>/<como>/<nombre>)')
    ap.add_argument('--salida', default='', help='carpeta del informe (por defecto <nucleo>/borrador/adopcion/<fecha>)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if not os.path.isdir(os.path.join(RAIZ, 'cerebro-digital')) or not os.path.isfile(os.path.join(RAIZ, 'AGENTS.md')):
        print('SIN DATOS -- %s no es un nucleo del template (falta cerebro-digital/ o AGENTS.md).' % RAIZ)
        return SIN_DATOS
    origen = os.path.abspath(a.ruta)
    if not os.path.isdir(origen):
        print('FRENA -- no existe la carpeta %s' % origen)
        return FRENA
    nombre = os.path.basename(origen.rstrip('\\/'))
    destino = os.path.abspath(a.destino) if a.destino else os.path.join(RAIZ, a.como, nombre)
    if os.path.exists(destino) or os.path.islink(destino):
        print('FRENA -- ya existe %s: borra el enlace o elegi otro --destino.' % destino)
        return FRENA
    fecha = datetime.date.today().isoformat()
    salida = os.path.abspath(a.salida) if a.salida else os.path.join(RAIZ, 'borrador', 'adopcion', fecha + '-' + nombre)
    print('ADOPTAR %s -> %s (%s)%s' % (origen, destino, 'mover' if a.mover else 'enlazar', '  (dry-run)' if a.dry_run else ''))

    # 1. enlazar o mover
    if a.dry_run:
        print('[1/4] (dry-run) %s' % ('mover la carpeta' if a.mover else 'crear el enlace de directorio'))
        real = origen
    elif a.mover:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        os.rename(origen, destino)
        real = destino
        print('[1/4] movido a %s' % destino)
    else:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        ok, detalle = enlazar(origen, destino)
        if not ok:
            print('FRENA -- no pude crear el enlace (%s). Alternativa: --mover, o crear el enlace a mano.' % detalle)
            return FRENA
        real = origen
        print('[1/4] enlace creado: %s -> %s (la carpeta sigue en su lugar)' % (destino, origen))

    # 2. relevamiento, inventario, radiografia
    print('[2/4] relevamiento, inventario y radiografia -> %s' % salida)
    if not a.dry_run:
        os.makedirs(salida, exist_ok=True)
    informes = (('01-relevamiento-ia.md', 'relevar-config-ia.py', [real, '--nucleo', RAIZ]),
                ('02-inventario.md', 'inventariar-codigo.py', [real]),
                ('03-radiografia.md', 'radiografiar-codigo.py', [real]),
                ('04-diagramas.md', 'radiografiar-codigo.py', [real, '--mermaid']))
    resumen = {}
    for archivo, script, args in informes:
        if a.dry_run:
            print('  (dry-run) %s %s' % (script, ' '.join(args[1:])))
            continue
        rc, out = correr(script, *args)
        resumen[archivo] = rc
        with open(os.path.join(salida, archivo), 'w', encoding='utf-8', newline='\n') as h:
            h.write('# %s\n\n```\n%s\n```\n' % (archivo, out.strip()))
        print('  %s <- %s (exit %d%s)' % (archivo, script, rc, '; SIN DATOS: el proyecto no tiene configuracion de IA, se absorbe como app comun' if (script == 'relevar-config-ia.py' and rc == 2) else ''))

    sin_codigo = False
    if not a.dry_run:
        rc, out = correr('inventariar-codigo.py', real, '--json')
        try:
            import json as _json
            lenguajes = [x['extension'] for x in _json.loads(out).get('lenguajes', [])]
            sin_codigo = not any(e in ('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.kt', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.dart', '.scala') for e in lenguajes)
        except (ValueError, KeyError):
            pass

    # 3. reglas
    agents = os.path.join(RAIZ, 'AGENTS.md')
    rel = os.path.relpath(agents, real).replace(os.sep, '/')
    linea = '@' + rel
    claude_md = os.path.join(real, 'CLAUDE.md')
    print('[3/4] reglas del nucleo en el proyecto: la linea para su CLAUDE.md es  %s' % linea)
    if a.importar_reglas and not a.dry_run:
        existe = os.path.isfile(claude_md)
        texto = open(claude_md, 'r', encoding='utf-8-sig', errors='replace').read() if existe else ''
        if linea in texto:
            print('  ya estaba importada')
        else:
            encabezado = '' if existe else '# %s\n\nReglas del nucleo (Cerebro Digital) de este proyecto:\n\n' % nombre
            with open(claude_md, 'a', encoding='utf-8', newline='\n') as h:
                h.write(('\n' if existe and not texto.endswith('\n') else '') + encabezado + linea + '\n')
            print('  %s: linea agregada (%s)' % ('CLAUDE.md creado' if not existe else 'CLAUDE.md', claude_md))
    elif not a.importar_reglas:
        print('  (no se toco el CLAUDE.md del proyecto: agregala vos, o volve a correr con --importar-reglas)')

    # 4. que sigue
    print('[4/4] lo que sigue:')
    if sin_codigo:
        print('  - este proyecto todavia NO tiene codigo (solo documentacion): no se absorbe como app. Pedir: "procesa los documentos de %s/%s" (curaduria por cerebro-orquestador; ADR -> DEC heredadas; .feature -> Escenarios); inventario y radiografia recien cuando haya codigo' % (a.como, nombre))
    else:
        print('  - abrir Claude Code parado en el nucleo (%s) y pedir: "absorbe la app de %s/%s en modo documentar"' % (RAIZ, a.como, nombre))
    print('    (lee %s, no todo el repo; cada item entra al Cerebro con tu "si")' % salida)
    print('  - o abrir el proyecto con  claude --add-dir "%s"  para que vea el Cerebro y las reglas' % RAIZ)
    print('  - si el relevamiento marco colisiones de nombre de skills o choque de idioma, se decide antes de programar')
    print('  - metodo completo: cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/adoptar-proyecto-existente.md')
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
