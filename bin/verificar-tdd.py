#!/usr/bin/env python3
"""La parte MECANICA de verificar-tdd: lee el historial de git y dice, por item, si hubo rojo antes
del codigo. SOLO LECTURA.

    python bin/verificar-tdd.py --repo <worktree> --base <sha-o-ref-de-la-base> [--items N] [--id 1234]
    python bin/verificar-tdd.py --repo <worktree> --base <sha> --items 5 --id 1234 --json
    python bin/verificar-tdd.py ... --tests-regex '<regex de rutas de test del stack>'
    python bin/verificar-tdd.py ... --modo test-despues --motivo 'esqueleto del repo'   (el Modo de pruebas de la Tarea)

Tres estados, nunca dos:  0 = todos los items cumplen   1 = hay hallazgos   2 = SIN DATOS

QUE MIDE (lo que no depende de criterio):
  - cada commit 'test(rojo): <n> ...' trae SOLO archivos de test (si trae produccion, la evidencia
    es invalida: el rojo y el verde quedaron en el mismo commit);
  - despues de cada rojo hay al menos un commit que toca produccion (el verde existe);
  - si se pasa --items N, cada item 1..N tiene su commit de rojo (el que falta, falta);
  - un commit de produccion ANTES del primer rojo de la rama es codigo sin test previo (aviso);
  - en modo tdd, cambios de produccion sin NINGUN commit 'test(rojo)' es SIN DATOS: no hay evidencia del rojo
    guardada (no hubo ciclo, o la rama se reorganizo sin evidencia/<ID>; el historial no lo distingue);
  - los 'test(guardarrail): ...' estan exentos del rojo, como dice guiar-tdd; un 'chore(firma): ...' (solo firmas vacias
    para que el rojo llegue a la asercion) no cuenta como produccion antes del rojo; un 'test(verde-de-entrada): <n>'
    (el item nacio verde porque un verde anterior ya lo cubria) cumple sin rojo y queda como pendiente a confirmar;
  - si se pasa --id, existe la rama evidencia/<ID> (local u origin) y 'git diff evidencia/<ID> HEAD'
    esta vacio; si la rama de la Tarea ya se reorganizo (no quedan commits de rojo), se audita
    evidencia/<ID> en su lugar.

MODO DE PRUEBAS (--modo, textual del campo de la Tarea; sin declarar es tdd):
  tdd              lo de arriba, entero;
  test-despues     no exige el rojo por item: exige la RED MINIMA (al menos un commit que toque tests y
                   uno que toque produccion en el rango) y un --motivo; sin motivo, es tdd y se audita como tal;
  caracterizacion  exige un commit 'test(caracterizacion): ...' o 'test(rojo): ...' ANTES del primer commit
                   de produccion: primero se congela lo que hace hoy, despues se toca;
  sin-tests        SIN DATOS declarado, con su motivo: no hay ciclo que auditar (la red minima es que no
                   entre a una rama de entrega, y eso lo mira el Merge Request, no este script).

QUE NO MIDE (lo hace la skill, con criterio): que la ASERCION de cada test diga lo mismo que el item
(literal), que el verde pase HOY (hay que correr la suite), el cierre BDD<->TDD contra el Gherkin de
la Historia y si un test puede fallar. Un OK de este script no es el veredicto: es su mitad dura.

Que es un archivo de test lo decide --tests-regex (por defecto: carpetas test/tests/spec/__tests__,
sufijos _test/.test/.spec y nombres *Test.* / *IT.*). Si el stack usa otra convencion, se pasa la
suya y se anota en tdd-stack-*.md. Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import json
import re
import subprocess
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
TESTS_DEFAULT = (r'(^|/)(test|tests|spec|specs|__tests__|testing)(/|$)'
                 r'|(\.|_)(test|spec|tests)\.[A-Za-z0-9]+$'
                 r'|(^|/)[A-Za-z0-9_]+(Test|Tests|IT|Spec)\.[A-Za-z0-9]+$')
ROJO = re.compile(r'^test\(rojo\):\s*(\d+)')
GUARDARRAIL = re.compile(r'^test\(guardarrail\)')
CARACTERIZACION = re.compile(r'^test\(caracterizacion\)')
FIRMA = re.compile(r'^chore\(firma\)')
VERDE_ENTRADA = re.compile(r'^test\(verde-de-entrada\):\s*(\d+)')
MODOS = ('tdd', 'test-despues', 'caracterizacion', 'sin-tests')


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout


def commits(repo, rango):
    rc, out = git(repo, 'log', '--reverse', '--format=%H%x1f%s', rango)
    if rc != 0:
        return None
    res = []
    for linea in out.splitlines():
        if '\x1f' not in linea:
            continue
        sha, asunto = linea.split('\x1f', 1)
        rc2, archivos = git(repo, 'show', '--pretty=', '--name-only', sha)
        res.append({'sha': sha[:10], 'asunto': asunto.strip(),
                    'archivos': [x for x in archivos.splitlines() if x.strip()]})
    return res


def main():
    ap = argparse.ArgumentParser(description='Evidencia del rojo, leida del historial de git.')
    ap.add_argument('--repo', required=True)
    ap.add_argument('--base', required=True, help='sha o ref de la base anotada al abrir el worktree')
    ap.add_argument('--rama', default='HEAD')
    ap.add_argument('--items', type=int, default=0, help='cuantos items tiene la lista "Tests a escribir PRIMERO"')
    ap.add_argument('--id', default='', help='ID de la Tarea, para buscar evidencia/<ID>')
    ap.add_argument('--tests-regex', default=TESTS_DEFAULT)
    ap.add_argument('--modo', choices=MODOS, default='tdd', help='el Modo de pruebas que declara la Tarea')
    ap.add_argument('--motivo', default='', help='el motivo escrito en la Tarea si el modo no es tdd')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    modo = a.modo
    aviso_modo = None
    if modo in ('test-despues', 'sin-tests') and not a.motivo.strip():
        aviso_modo = 'modo %s declarado SIN motivo: se audita como tdd (un test-despues sin motivo es HALLAZGO)' % modo
        modo = 'tdd'
    if modo == 'sin-tests':
        print('SIN DATOS -- modo sin-tests declarado (motivo: %s): no hay ciclo que auditar; que no entre a una rama de entrega lo mira el Merge Request.' % a.motivo.strip())
        return SIN_DATOS
    es_test = re.compile(a.tests_regex)

    rc, _ = git(a.repo, 'rev-parse', '--verify', '--quiet', a.base)
    if rc != 0:
        print('SIN DATOS -- la base %s no existe en %s.' % (a.base, a.repo))
        return SIN_DATOS

    evidencia = None
    if a.id:
        for ref in ('evidencia/' + a.id, 'origin/evidencia/' + a.id):
            rc, _ = git(a.repo, 'rev-parse', '--verify', '--quiet', ref)
            if rc == 0:
                evidencia = ref
                break

    rango = '%s..%s' % (a.base, a.rama)
    lista = commits(a.repo, rango)
    if lista is None:
        print('SIN DATOS -- no pude leer el historial %s.' % rango)
        return SIN_DATOS
    fuente = rango
    if not any(ROJO.match(c['asunto']) for c in lista) and evidencia:
        fuente = '%s..%s' % (a.base, evidencia)
        lista = commits(a.repo, fuente) or []
    if not lista:
        print('SIN DATOS -- no hay commits en %s: no hay ciclo que auditar.' % fuente)
        return SIN_DATOS

    hallazgos, avisos, items = [], [], {}
    if aviso_modo:
        hallazgos.append(aviso_modo)
    primer_rojo_visto = False
    toca_tests = any(any(es_test.search(f) for f in c['archivos']) for c in lista)
    toca_produccion = any(any(not es_test.search(f) for f in c['archivos']) for c in lista)
    for i, c in enumerate(lista):
        m = ROJO.match(c['asunto'])
        if m:
            primer_rojo_visto = True
            n = int(m.group(1))
            produccion = [f for f in c['archivos'] if not es_test.search(f)]
            verde = any(any(not es_test.search(f) for f in d['archivos']) for d in lista[i + 1:])
            if produccion:
                items[n] = ('evidencia invalida', 'el commit %s trae produccion: %s' % (c['sha'], ', '.join(produccion[:3])))
            elif not verde:
                items[n] = ('evidencia invalida', 'despues del rojo %s no hay ningun commit que toque produccion' % c['sha'])
            else:
                items.setdefault(n, ('cumple', 'rojo en %s, verde despues' % c['sha']))
            continue
        if GUARDARRAIL.match(c['asunto']) or FIRMA.match(c['asunto']):
            continue
        mv = VERDE_ENTRADA.match(c['asunto'])
        if mv:
            n = int(mv.group(1))
            produccion = [f for f in c['archivos'] if not es_test.search(f)]
            items[n] = ('evidencia invalida', 'el commit %s de verde-de-entrada trae produccion' % c['sha']) if produccion else ('cumple (verde de entrada)', 'nacio verde en %s: lo cubria un verde anterior; queda como pendiente a confirmar' % c['sha'])
            continue
        if CARACTERIZACION.match(c['asunto']):
            primer_rojo_visto = True
            continue
        if not primer_rojo_visto and any(not es_test.search(f) for f in c['archivos']):
            texto = 'commit de produccion antes del primer rojo de la rama: %s "%s"' % (c['sha'], c['asunto'][:60])
            if modo == 'caracterizacion':
                hallazgos.append('se toco produccion antes de congelar con test(caracterizacion): ' + texto)
            elif modo == 'tdd':
                avisos.append(texto)
    if modo == 'test-despues':
        if a.items:
            avisos.append('modo test-despues: la lista de %d items no se exige como rojo por item, se exige la red minima' % a.items)
        if not toca_tests:
            hallazgos.append('modo test-despues sin ningun commit que toque tests: no hay red minima')
        if not toca_produccion:
            avisos.append('modo test-despues sin commits de produccion en el rango')
    elif modo == 'caracterizacion':
        if not any(CARACTERIZACION.match(c['asunto']) or ROJO.match(c['asunto']) for c in lista):
            hallazgos.append('modo caracterizacion sin ningun commit test(caracterizacion) ni test(rojo): nada congelo lo que hace hoy')
    else:
        for n in range(1, a.items + 1):
            items.setdefault(n, ('falta', 'ningun commit test(rojo): %d' % n))
    for n, (v, d) in sorted(items.items()):
        if not v.startswith('cumple') and modo != 'test-despues':
            hallazgos.append('item %d: %s -- %s' % (n, v, d))

    diff_evidencia = None
    if evidencia and fuente == rango:
        rc, out = git(a.repo, 'diff', '--stat', evidencia, a.rama)
        diff_evidencia = 'vacio' if not out.strip() else 'DIFIERE'
        if diff_evidencia == 'DIFIERE':
            hallazgos.append('git diff %s %s no esta vacio: al reorganizar se perdio o se agrego algo' % (evidencia, a.rama))
    if a.id and not evidencia:
        avisos.append('no existe evidencia/%s: el rojo se verifico sobre la rama de trabajo (vale); crear evidencia/%s ANTES de reorganizar los commits, o el rojo deja de ser verificable' % (a.id, a.id))

    sin_datos = []
    if modo == 'tdd' and toca_produccion and not any(ROJO.match(c['asunto']) for c in lista):
        sin_datos.append('cambios de produccion y ningun commit test(rojo): no hay evidencia del rojo guardada '
                         '(no hubo ciclo, o la rama se reorganizo sin evidencia/<ID>)')
    estado = HALLAZGO if hallazgos else (SIN_DATOS if sin_datos else OK)
    salida = {'estado': {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}[estado], 'sin_datos': sin_datos, 'fuente': fuente, 'commits': len(lista), 'modo': modo, 'motivo': a.motivo.strip(),
              'items': {str(n): {'veredicto': v, 'detalle': d} for n, (v, d) in sorted(items.items())},
              'evidencia': evidencia, 'diff_evidencia_vs_rama': diff_evidencia,
              'hallazgos': hallazgos, 'avisos': avisos,
              'no_mira': ['la asercion literal de cada test', 'que el verde pase hoy (correr la suite)',
                          'el cierre BDD<->TDD contra la Historia', 'si cada test puede fallar (en test-despues sobre logica: la mutacion del verificador)']}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('VERIFICAR TDD (mecanico) -- %s  [%s, %d commits, modo %s%s]' % (salida['estado'], fuente, len(lista), modo, (': ' + a.motivo.strip()) if a.motivo.strip() else ''))
        for n, (v, d) in sorted(items.items()):
            print('  item %d: %s -- %s' % (n, v, d))
        for h in hallazgos:
            if not h.startswith('item '):
                print('  hallazgo: ' + h)
        for s in sin_datos:
            print('  sin datos: ' + s)
        if evidencia:
            print('  evidencia: %s (diff contra la rama: %s)' % (evidencia, diff_evidencia or 'no aplica'))
        for v in avisos:
            print('  aviso: ' + v)
        print('  Lo que este script NO mira: ' + '; '.join(salida['no_mira']) + '.')
    return estado


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
