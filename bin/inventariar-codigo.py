#!/usr/bin/env python3
"""Inventario DETERMINISTA de una aplicacion existente, para absorberla al Cerebro. SOLO LECTURA.

    python bin/inventariar-codigo.py <ruta-de-la-aplicacion> [--json] [--max-archivos 20000]

Tres estados, nunca dos:  0 = inventario listo   1 = (no aplica)   2 = SIN DATOS (ruta vacia o ilegible)

POR QUE EXISTE. El primer paso de absorber-aplicacion es saber QUE HAY: lenguajes, archivos de
build, pipeline, contenedores, contratos de API, migraciones, tests, deuda declarada, archivos que
parecen secretos. Si lo mide un script, el modelo arranca de hechos y no de impresiones, y dos
corridas dan lo mismo. No prescribe stack: detecta por extension y por nombres de archivo conocidos,
y lo que no reconoce lo lista como "otros".

PARA DEC-004. Imprime ademas las filas MEDIBLES de la tabla de estrategias de planificar-modernizacion,
con umbrales fijos y declarados (UMBRAL_RED): red de tests, contrato de API, deuda y secretos. Las filas
que piden lectura (limites de modulo) o encuadre (stack deseado, produccion) quedan marcadas como tales:
la decision no se scriptea, se toma con la tabla a la vista.

QUE NO HACE. No lee el contenido de negocio (eso lo hace la skill, con criterio, archivo por archivo),
no modifica nada, no sale de la ruta dada. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import json
import os
import re
import subprocess
import sys

OK, _, SIN_DATOS = 0, 1, 2
# Proporcion de archivos de test sobre el total: debajo del primero, 'sin red'; debajo del segundo,
# 'escasa'; si no, 'presente'. Son umbrales de LECTURA AUTOMATICA, no de calidad: la calidad de los
# tests la lee la skill. Declarados aca para que dos corridas digan lo mismo.
UMBRAL_RED = (0.05, 0.15)
BASURA = {'.git', 'node_modules', 'target', 'build', 'out', 'dist', '.gradle', '.idea', '.vscode',
          '__pycache__', '.mvn', 'coverage', '.next', 'vendor', 'bin', 'obj', '.venv', 'venv', '.tox'}
BUILD = ('pom.xml', 'build.gradle', 'build.gradle.kts', 'package.json', 'pyproject.toml', 'setup.py',
         'requirements.txt', 'go.mod', 'Cargo.toml', 'composer.json', 'Gemfile', 'Makefile', 'CMakeLists.txt',
         'mix.exs', 'pubspec.yaml', 'build.sbt', 'Package.swift')
BUILD_SUFIJOS = ('.csproj', '.sln', '.fsproj', '.vbproj')
CI = ('.gitlab-ci.yml', 'azure-pipelines.yml', 'azure-pipelines.yaml', 'Jenkinsfile', 'bitbucket-pipelines.yml',
      '.travis.yml', 'cloudbuild.yaml')
CONTENEDOR = re.compile(r'^(Dockerfile(\..+)?|docker-compose.*\.ya?ml|compose\.ya?ml)$')
API = re.compile(r'(?i)(^|/)(openapi|swagger|api-spec|asyncapi)[^/]*\.(ya?ml|json)$|\.proto$|\.graphql$|\.wsdl$')
MIGRACIONES = re.compile(r'(?i)(^|/)(migrations?|flyway|liquibase|alembic|db/migrate|changelog)(/|$)')
TEST = re.compile(r'\.feature$|(^|/)(bdd|features)(/|$)|(^|/)(test|tests|spec|specs|__tests__|testing)(/|$)|(\.|_)(test|spec|tests)\.[A-Za-z0-9]+$|(^|/)[A-Za-z0-9_]+(Test|Tests|IT|Spec)\.[A-Za-z0-9]+$')
SECRETO = re.compile(r'(?i)(^|/)(\.env([.-].*)?|.*\.(pem|key|p12|pfx|jks|keystore)|secrets?\.[a-z]+|credentials?\.[a-z]+|id_rsa.*)$')
DOCS = re.compile(r'(?i)^(readme|contributing|architecture|changelog|docs?)(\..+)?$')
DEUDA = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b')
TEXTO = ('.java', '.kt', '.cs', '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.rb', '.php', '.scala',
         '.swift', '.dart', '.c', '.cpp', '.h', '.sql', '.html', '.css', '.scss', '.vue', '.svelte', '.md',
         '.yml', '.yaml', '.json', '.xml', '.properties', '.toml', '.sh', '.ps1', '.gradle', '.tf', '.feature', '.rs')


def git(ruta, *args):
    r = subprocess.run(['git', '-C', ruta] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser(description='Inventario de una aplicacion existente (solo lectura).')
    ap.add_argument('ruta')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--max-archivos', type=int, default=20000)
    a = ap.parse_args()
    raiz = os.path.abspath(a.ruta)
    if not os.path.isdir(raiz):
        print('SIN DATOS -- no existe la carpeta %s' % raiz)
        return SIN_DATOS

    por_ext, lineas_ext = {}, {}
    build, ci, contenedores, apis, migraciones, secretos, docs = [], [], [], [], [], [], []
    tests, archivos, deuda, grandes = 0, 0, 0, []
    primer_nivel = sorted(d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d)) and d not in BASURA)
    for base, dirs, files in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in BASURA)
        for f in sorted(files):
            if archivos >= a.max_archivos:
                break
            if f.endswith(('.pyc', '.pyo', '.class')):
                continue
            archivos += 1
            p = os.path.join(base, f)
            rel = os.path.relpath(p, raiz).replace(os.sep, '/')
            ext = os.path.splitext(f)[1].lower() or '(sin extension)'
            por_ext[ext] = por_ext.get(ext, 0) + 1
            if f in BUILD or f.endswith(BUILD_SUFIJOS):
                build.append(rel)
            if f in CI or '/.github/workflows/' in '/' + rel:
                ci.append(rel)
            if CONTENEDOR.match(f):
                contenedores.append(rel)
            if API.search(rel):
                apis.append(rel)
            if MIGRACIONES.search(rel):
                migraciones.append(rel.split('/')[0] if '/' not in rel else '/'.join(rel.split('/')[:-1]))
            if SECRETO.search(rel):
                secretos.append(rel)
            if DOCS.match(f) and base == raiz:
                docs.append(rel)
            if TEST.search(rel):
                tests += 1
            try:
                tam = os.path.getsize(p)
            except OSError:
                tam = 0
            grandes.append((tam, rel))
            if ext in TEXTO and tam < 2_000_000:
                try:
                    with open(p, 'r', encoding='utf-8', errors='replace') as h:
                        t = h.read()
                    lineas_ext[ext] = lineas_ext.get(ext, 0) + t.count('\n') + 1
                    deuda += len(DEUDA.findall(t))
                except OSError:
                    pass
    if archivos == 0:
        print('SIN DATOS -- la carpeta %s no tiene archivos (fuera de los ignorados).' % raiz)
        return SIN_DATOS
    grandes.sort(reverse=True)
    migraciones = sorted(set(migraciones))
    lenguajes = sorted(((e, n, lineas_ext.get(e, 0)) for e, n in por_ext.items()), key=lambda x: (-x[2], -x[1]))[:15]
    repo = {}
    if os.path.isdir(os.path.join(raiz, '.git')):
        repo = {'remoto': git(raiz, 'remote', 'get-url', 'origin'), 'rama': git(raiz, 'branch', '--show-current'),
                'commits': git(raiz, 'rev-list', '--count', 'HEAD'), 'ultimo_commit': git(raiz, 'log', '-1', '--format=%cs %s'),
                'autores': len((git(raiz, 'shortlog', '-sn', 'HEAD') or '').splitlines())}
    prop = round(tests / archivos, 3)
    red = 'sin red' if prop < UMBRAL_RED[0] else ('escasa' if prop < UMBRAL_RED[1] else 'presente')
    dec_004 = [
        {'criterio': 'El stack actual es el que el equipo quiere (DEC-003)', 'medido': 'lo decide el equipo; lenguajes vistos: ' + ', '.join(e for e, _, _ in lenguajes[:4]), 'empuja_a': 'encuadre'},
        {'criterio': 'Hay red de tests que proteja un cambio', 'medido': '%d archivos de test de %d (%.0f%%): %s [umbrales %d%%/%d%%]' % (tests, archivos, 100 * prop, red, 100 * UMBRAL_RED[0], 100 * UMBRAL_RED[1]),
         'empuja_a': 'refactor' if red == 'presente' else 'cualquiera, con caracterizacion primero'},
        {'criterio': 'Los limites de modulo se pueden imponer en su lugar (DEC-002)', 'medido': 'pide lectura de la estructura (la skill)', 'empuja_a': 'lectura'},
        {'criterio': 'Hay contrato de API o se puede escribir uno', 'medido': ('hay: ' + ', '.join(apis[:3])) if apis else 'no hay contrato declarado', 'empuja_a': 'migracion por slices viable' if apis else 'primero hay que sacar el contrato del codigo'},
        {'criterio': 'Deuda y riesgos', 'medido': '%d TODO/FIXME/HACK, %d posibles secretos, %s' % (deuda, len(secretos), ('CI presente' if ci else 'sin CI')), 'empuja_a': 'migracion si la deuda es estructural (lo lee la skill)'},
        {'criterio': 'La aplicacion tiene que seguir en produccion mientras se trabaja', 'medido': 'encuadre con el humano', 'empuja_a': 'encuadre'},
    ]
    salida = {
        'ruta': raiz, 'archivos': archivos, 'truncado': archivos >= a.max_archivos,
        'carpetas_primer_nivel': primer_nivel,
        'lenguajes': [{'extension': e, 'archivos': n, 'lineas': l} for e, n, l in lenguajes],
        'build': build, 'ci': ci, 'contenedores': contenedores, 'contratos_api': apis,
        'migraciones': migraciones, 'docs_raiz': docs,
        'tests': {'archivos_de_test': tests, 'proporcion': round(tests / archivos, 3)},
        'deuda_declarada': deuda, 'posibles_secretos': secretos,
        'archivos_mas_grandes': [{'bytes': t, 'ruta': r} for t, r in grandes[:10]],
        'repositorio': repo,
        'dec_004': dec_004,
    }
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('INVENTARIO de %s  (%d archivos%s)' % (raiz, archivos, ', truncado' if salida['truncado'] else ''))
        print('  Carpetas de primer nivel: ' + (', '.join(primer_nivel) or '(ninguna)'))
        print('  Lenguajes (por extension, lineas): ' + ', '.join('%s %d archivos / %d lineas' % (e, n, l) for e, n, l in lenguajes[:8]))
        print('  Build: ' + (', '.join(build[:8]) or 'no se reconocio ninguno'))
        print('  CI: ' + (', '.join(ci[:5]) or 'ninguno'))
        print('  Contenedores: ' + (', '.join(contenedores[:5]) or 'ninguno'))
        print('  Contratos de API: ' + (', '.join(apis[:5]) or 'ninguno (la API, si existe, no esta declarada: es lo primero que falta)'))
        print('  Migraciones de base: ' + (', '.join(migraciones[:5]) or 'no se reconocio una carpeta de migraciones'))
        print('  Tests: %d archivos (%.0f%% del total)' % (tests, 100 * tests / archivos))
        print('  Deuda declarada (TODO/FIXME/HACK): %d' % deuda)
        print('  Posibles secretos en el repo (nombres, no contenido): ' + (', '.join(secretos[:5]) or 'ninguno'))
        print('  Docs en la raiz: ' + (', '.join(docs) or 'ninguno'))
        if repo:
            print('  Repositorio: %s | rama %s | %s commits | %s autores | ultimo: %s' % (repo['remoto'], repo['rama'], repo['commits'], repo['autores'], repo['ultimo_commit']))
        print('  Para DEC-004 (refactor o migracion), lo medible:')
        for fila in dec_004:
            print('    - %s: %s -> %s' % (fila['criterio'], fila['medido'], fila['empuja_a']))
        print('  Lo que este script NO mira: que hace el negocio, que reglas tiene, como esta organizado por dentro. Eso lo lee la skill, archivo por archivo, y lo pasa por la Consulta Interactiva de Decision.')
    return OK


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
