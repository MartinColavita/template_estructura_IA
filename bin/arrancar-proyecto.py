#!/usr/bin/env python3
"""Arranca un proyecto con el template en UN comando, con las respuestas que la skill arrancar-proyecto ya pregunto.

    python -I bin/arrancar-proyecto.py --proyecto "Mi proyecto" --producto "Mi app" --organizacion "Yo" --modulo mi-proyecto \
        --modo solo --tablero local [--autor martin] \
        [--existente <ruta de la carpeta con codigo> --como back [--mover] [--importar-reglas]] \
        [--azure-org X --azure-proyecto Y --azure-team Z] [--sin-informe] [--dry-run]

Tres estados, nunca dos:  0 = proyecto arrancado   1 = FRENA (un paso fallo; se dice cual y como seguir)   2 = SIN DATOS (esto no es un template)

POR QUE EXISTE. Arrancar un proyecto eran seis pasos en tres scripts, y cada sesion los hacia en distinto orden. La
skill arrancar-proyecto pregunta lo basico en un solo mensaje y, con el "si", corre ESTO. Orden fijo:
  1. instanciar.py      placeholders, modulo, modo (DEC-006), stack si se dijo (DEC-003), fechas, espejos
  2. git init           si la carpeta no es un repositorio todavia
  3. instalar.py        hook, agentes, espejos, especificacion de skills
  4. adoptar-proyecto   si ya existe una carpeta con codigo: enlace, relevamiento, inventario, radiografia, reglas
  5. generar-informe    el informe visual, en modo rapido
Para en el primer paso que falla y dice como seguir a mano. Idempotente: si ya esta instanciado, lo dice y sigue.

QUE NO HACE. No pregunta nada (eso es la skill), no toca el codigo del proyecto existente, no commitea, no escribe el
Cerebro con conocimiento (eso es absorber-aplicacion, item por item). Solo biblioteca estandar.
"""

import argparse
import os
import subprocess
import sys

OK, FRENA, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def correr(args, titulo):
    print('--- %s' % titulo)
    print('    $ ' + ' '.join(('"%s"' % a) if ' ' in a else a for a in args))
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=RAIZ)
    salida = (r.stdout or '') + (r.stderr or '')
    for linea in salida.strip().splitlines()[-12:]:
        print('    ' + linea)
    return r.returncode, salida


def main():
    ap = argparse.ArgumentParser(description='Arranca un proyecto con el template en un comando.')
    ap.add_argument('--proyecto', required=True)
    ap.add_argument('--producto', required=True)
    ap.add_argument('--organizacion', required=True)
    ap.add_argument('--modulo', required=True)
    ap.add_argument('--modo', choices=['solo', 'equipo'], required=True)
    ap.add_argument('--tablero', choices=['local', 'azure', 'jira', 'otro'], default='')
    ap.add_argument('--autor', default='')
    ap.add_argument('--stack-back', default=''); ap.add_argument('--stack-front', default=''); ap.add_argument('--stack-base', default=''); ap.add_argument('--stack-build', default='')
    ap.add_argument('--comando-tests-back', default=''); ap.add_argument('--comando-tests-front', default=''); ap.add_argument('--stack-e2e', default='')
    ap.add_argument('--azure-org', default='')
    ap.add_argument('--azure-proyecto', default='')
    ap.add_argument('--azure-team', default='')
    ap.add_argument('--existente', default='', help='carpeta con codigo que ya existe, para enchufarla')
    ap.add_argument('--como', choices=['back', 'front'], default='back')
    ap.add_argument('--mover', action='store_true')
    ap.add_argument('--importar-reglas', action='store_true')
    ap.add_argument('--sin-informe', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if not os.path.isdir(os.path.join(RAIZ, 'cerebro-digital')) or not os.path.isfile(os.path.join(RAIZ, 'bin', 'instanciar.py')):
        print('SIN DATOS -- %s no es una copia del template (falta cerebro-digital/ o bin/instanciar.py).' % RAIZ)
        return SIN_DATOS
    py = sys.executable
    tablero = a.tablero or ('local' if a.modo == 'solo' else 'azure')
    print('ARRANCAR "%s" en %s  (modo %s, tablero %s%s)%s' % (a.proyecto, RAIZ, a.modo, tablero, (', enchufando ' + a.existente) if a.existente else '', '  (dry-run)' if a.dry_run else ''))

    # 1. instanciar (idempotente: si ya esta instanciado, el script lo dice)
    ya = True
    with open(os.path.join(RAIZ, 'AGENTS.md'), 'rb') as h:
        ya = ('{{' + 'PROYECTO' + '}}').encode() not in h.read()   # armado por partes: el instanciador reemplaza el literal
    if ya and os.path.isdir(os.path.join(RAIZ, 'cerebro-digital', a.modulo)):
        print('--- [1/5] instanciar: ya estaba instanciado (modulo %s); se saltea' % a.modulo)
    else:
        args = [py, '-I', os.path.join(RAIZ, 'bin', 'instanciar.py'), '--proyecto', a.proyecto, '--producto', a.producto,
                '--organizacion', a.organizacion, '--modulo', a.modulo, '--modo', a.modo, '--tablero', tablero]
        for k in ('stack_back', 'stack_front', 'stack_base', 'stack_build', 'comando_tests_back', 'comando_tests_front', 'stack_e2e'):
            if getattr(a, k):
                args += ['--' + k.replace('_', '-'), getattr(a, k)]
        if a.autor:
            args += ['--autor', a.autor]
        if tablero == 'azure':
            args += ['--azure-org', a.azure_org, '--azure-proyecto', a.azure_proyecto, '--azure-team', a.azure_team]
        if a.dry_run:
            args.append('--dry-run')
        rc, _ = correr(args, '[1/5] instanciar')
        if rc != 0:
            print('FRENA -- instanciar fallo (codigo %d). Arreglalo y volve a correr: el resto no se ejecuto.' % rc)
            return FRENA

    # 2. git init
    es_repo = subprocess.run(['git', '-C', RAIZ, 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True).stdout.strip() == 'true'
    if es_repo:
        print('--- [2/5] git: ya es un repositorio; se saltea')
    elif a.dry_run:
        print('--- [2/5] git init (dry-run)')
    else:
        rc, _ = correr(['git', 'init', '-q', '-b', 'develop'], '[2/5] git init (rama develop)')
        if rc != 0:
            rc, _ = correr(['git', 'init', '-q'], '[2/5] git init')
            if rc != 0:
                print('FRENA -- no pude hacer git init. Instala git y segui con: python -I bin/instalar.py')
                return FRENA

    # 3. instalar
    args = [py, '-I', os.path.join(RAIZ, 'bin', 'instalar.py')] + (['--dry-run'] if a.dry_run else [])
    rc, salida = correr(args, '[3/5] instalar')
    if rc == 1:
        print('FRENA -- el instalador marco hallazgos (arriba). Resolvelos y volve a correr.')
        return FRENA

    # 4. adoptar
    nombre_existente = os.path.basename(a.existente.rstrip('\\/')) if a.existente else ''
    if a.existente and os.path.exists(os.path.join(RAIZ, a.como, nombre_existente)):
        print('--- [4/5] adoptar: %s/%s ya existe (ya estaba enchufado); se saltea' % (a.como, nombre_existente))
    elif a.existente:
        args = [py, '-I', os.path.join(RAIZ, 'bin', 'adoptar-proyecto.py'), a.existente, '--como', a.como]
        if a.mover:
            args.append('--mover')
        if a.importar_reglas:
            args.append('--importar-reglas')
        if a.dry_run:
            args.append('--dry-run')
        rc, _ = correr(args, '[4/5] adoptar el proyecto existente')
        if rc != 0:
            print('FRENA -- no se pudo enchufar %s (codigo %d). El nucleo quedo instanciado e instalado; corre adoptar-proyecto.py a mano.' % (a.existente, rc))
            return FRENA
    else:
        print('--- [4/5] sin proyecto existente: se arranca de cero')

    # 5. informe
    if a.sin_informe or a.dry_run:
        print('--- [5/5] informe: %s' % ('salteado' if a.sin_informe else '(dry-run)'))
    else:
        correr([py, '-B', os.path.join(RAIZ, 'bin', 'generar-informe.py'), '--rapido'], '[5/5] informe visual (rapido)')

    print('')
    print('LISTO. Lo que sigue (lo decide una persona):')
    if a.existente:
        print('  - "absorbe la app de %s/%s en modo documentar": lee borrador/adopcion/, cada item entra al Cerebro con tu si' % (a.como, os.path.basename(a.existente.rstrip('\\/'))))
    print('  - DEC-003 (el stack) en lo que no se dijo al arrancar, y las guias tdd-stack-*.md')
    print('  - la primera ficha funcional: cerebro-digital/%s/funcional/plantilla-ficha-flujo.md' % a.modulo)
    if tablero == 'local':
        print('  - el tablero es cerebro-digital/%s/backlog/ (bin/tablero-local.py); una ficha validada baja con bin/derivar-a-tablero-local.py' % a.modulo)
    print('  - abrir Claude Code parado aca (%s) para que vea AGENTS.md, el Cerebro y las skills' % RAIZ)
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
