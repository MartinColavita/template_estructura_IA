#!/usr/bin/env python3
"""Escanear la seguridad de un repositorio de la aplicacion (back/ o front/), o el diff de una Tarea: analisis
estatico, dependencias vulnerables y secretos, normalizado a OK / HALLAZGO / SIN DATOS por categoria.
SOLO LECTURA sobre el repositorio: escribe solo lo crudo y el informe normalizado en borrador/seguridad/<fecha>/.

    python -I bin/escanear-seguridad.py --repo <dir> [--base <sha>] [--solo sast,sca,secretos] [--reglas <dir>] [--json]
    python -I bin/escanear-seguridad.py --reporte <archivo> [--reporte <categoria>:<archivo> ...] [--repo <dir>] [--json]
    python -I bin/escanear-seguridad.py --repo <dir> --plan [--json]      (que correria y con que opciones; no corre nada)
    opciones: --linea-base <informe.json>   --max-dias-base <n> (base offline de OSV; 7 por defecto, DEC-009)   --salida <dir>

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS
  Sale 1 si alguna categoria tiene HALLAZGO; si no, 2 si alguna es SIN DATOS; 0 solo si todas midieron y estan limpias.

QUE CORRE, solo si esta instalado y siempre sin red y sin metricas (si falta, esa parte es SIN DATOS):
  sast      opengrep o semgrep con reglas LOCALES (--reglas; nunca --config auto ni el registro), y bandit si hay .py
  sca       osv-scanner --offline (la base la baja una persona antes; ausente o mas vieja que --max-dias-base: SIN DATOS)
  secretos  gitleaks --redact (con --base, solo el rango de la Tarea; sin --base, todo el historial)
  La configuracion de infraestructura (Dockerfile, Compose, Terraform, Kubernetes) no es de este script: la mira
  una sola herramienta, bin/auditar-iac.py.
  --base: solo letras, numeros y . _ / - (y no empieza con guion); si no, SIN DATOS y no corre nada.
  Regla del cero, igual corriendo que leyendo: un reporte que no muestra haber analizado algo es SIN DATOS.
  pip-audit y npm audit necesitan red: este script no los corre; sus reportes se leen con --reporte.
Con --repo revisa ademas las supresiones escritas en el repositorio (# nosec, # nosemgrep, gitleaks:allow,
osv-scanner.toml, .trivyignore, .gitleaksignore): sin motivo, sin vencimiento o vencidas, son HALLAZGO.

POR QUE EXISTE. La postura del metodo (desarrollo: seguridad-y-datos-sensibles.md y dependencias-y-config.md) dice
que critica y alta frenan y que sin resultado del analizador la seguridad es SIN DATOS. Faltaba quien corra los
escaneres de la misma forma siempre y lea sus reportes con una sola regla: el normalizador de bin/seguridad/.

QUE NO HACE. No arregla nada (ni autofix, ni 'fix', ni actualiza dependencias), no baja bases ni reglas, no valida
un secreto contra su proveedor, no sube nada. Nunca muestra el valor de un secreto. No decide por el codigo de
salida de la herramienta: lee su reporte. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seguridad import normalizar  # noqa: E402  el lector unico de reportes y el esquema comun

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = ('sast', 'sca', 'secretos')
BASE = re.compile(r'^[0-9A-Za-z._/-]+$')
TOPE = 1800                                      # segundos por herramienta
# Lo que nunca se le pasa a una herramienta: cambia el codigo, baja cosas, usa una credencial o manda datos afuera.
NUNCA = ('--autofix', '-a', 'fix', '--fix', '--dryrun', '--download-offline-databases', '--validate', '--update',
         '--metrics=on', '--metrics=auto', '--config=auto', 'auto', 'login', 'ci', 'publish', '-u', '-z', '--hook')
EXCLUIR_BANDIT = '*/.venv/*,*/venv/*,*/node_modules/*,*/.git/*,*/build/*,*/dist/*,*/target/*'
MANIFIESTOS = ('package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml', 'requirements.txt', 'poetry.lock',
               'Pipfile.lock', 'uv.lock', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'gradle.lockfile', 'go.mod',
               'Cargo.lock', 'composer.lock', 'Gemfile.lock', 'packages.lock.json', 'mix.lock', 'pubspec.lock')
NO_MIRA = ('si un hallazgo es explotable: lo contesta otro agente con contexto limpio (escanear-aplicacion.md)',
           'quien aprobo una supresion y que no sea quien la escribio: lo mira el verificador en el Merge Request',
           'la configuracion de infraestructura (Dockerfile, Compose, Terraform, Kubernetes): la mira una sola '
           'herramienta, auditar-iac.py',
           'la prueba contra una aplicacion que corre (escanear-ambiente.py), las imagenes (escanear-imagenes.py) '
           'y el pipeline (verificar-pipeline.py)',
           'los secretos de lo que se esta por commitear: auditar-diff.py',
           'la edad de la base de OSV de cada ecosistema: se mira la mas nueva',
           'el .trivyignore.yaml: solo el .trivyignore de texto')


def ejecutar(cmd, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=TOPE)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return None, 'tardo mas de %d minutos' % (TOPE // 60)
    except OSError as e:
        return None, str(e)


def contar(repo):
    """Lo que hay para analizar en cada categoria (regla del cero: sin nada que mirar, SIN DATOS)."""
    c = {'archivos': 0, 'codigo': 0, 'py': 0, 'manifiestos': 0}
    for base, dirs, archivos in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in normalizar.BASURA and not d.startswith('.')]
        for f in archivos:
            bajo = f.lower()
            ext = os.path.splitext(bajo)[1]
            c['archivos'] += 1
            c['codigo'] += ext in normalizar.CODIGO_EXT
            c['py'] += ext == '.py'
            c['manifiestos'] += f in MANIFIESTOS or bajo.endswith('.csproj')
    return c


def carpetas_cache():
    propia = os.environ.get('OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY')
    if propia:
        return [propia]
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA', '')
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Caches')
    else:
        base = os.environ.get('XDG_CACHE_HOME') or os.path.expanduser('~/.cache')
    return [x for x in (base, tempfile.gettempdir()) if x]


def edad_base_osv():
    """Dias desde la base offline de OSV mas nueva, o None si no hay ninguna."""
    zips = []
    for c in carpetas_cache():
        for sub in ('osv-scanner', 'osv-scalibr'):
            zips += glob.glob(os.path.join(c, sub, '*', 'all.zip'))
    if not zips:
        return None
    return (time.time() - max(os.path.getmtime(z) for z in zips)) / 86400.0


def paso(cat, herramienta, comando, reporte, motivos, ok, stdout=False):
    prohibidas = [t for t in comando if t in NUNCA or t.startswith('--config=auto')]
    if prohibidas:
        raise ValueError('el comando de %s lleva una opcion prohibida: %s' % (herramienta, ', '.join(prohibidas)))
    binario = shutil.which(comando[0])
    motivos = [m for m in motivos if m]
    if not binario:
        motivos.append('%s no esta instalada' % herramienta)
    return {'categoria': cat, 'herramienta': herramienta, 'comando': comando, 'binario': binario, 'reporte': reporte,
            'motivo': '; '.join(motivos), 'ok': ok, 'stdout': stdout}


def armar_plan(repo, cats, a, salida, hora):
    c = contar(repo)
    pasos = []

    def ruta(nombre):
        return os.path.join(salida, '%s-%s' % (hora, nombre))
    if 'sast' in cats:
        sg = 'opengrep' if shutil.which('opengrep') else 'semgrep'
        out = ruta(sg + '.sarif')
        cmd = [sg, 'scan', '--config', a.reglas or '<reglas>', '--metrics=off', '--sarif-output=' + out, '--quiet']
        if sg == 'semgrep':
            cmd.append('--disable-version-check')
        if a.base:
            cmd += ['--baseline-commit', a.base]
        pasos.append(paso('sast', sg, cmd + [repo], out, [
            '' if c['codigo'] else 'no hay archivos de codigo que analizar (regla del cero)',
            'sin reglas locales (--reglas): --config auto baja reglas del registro y manda metricas' if not a.reglas
            else '' if os.path.exists(a.reglas) else 'las reglas %s no existen' % a.reglas], (0, 1)))
        if c['py']:
            out = ruta('bandit.sarif')
            pasos.append(paso('sast', 'bandit', ['bandit', '-r', repo, '-f', 'sarif', '-o', out, '-q', '-x', EXCLUIR_BANDIT],
                              out, [], (0, 1)))
    if 'sca' in cats:
        edad = edad_base_osv()
        pasos.append(paso('sca', 'osv-scanner', ['osv-scanner', 'scan', 'source', '-r', repo, '--format', 'json', '--offline'],
                          ruta('osv-scanner.json'), [
                              '' if c['manifiestos'] else 'no hay manifiestos ni lockfiles de dependencias (regla del cero)',
                              'la base offline de OSV esta ausente: la baja una persona antes de escanear' if edad is None
                              else 'la base offline de OSV esta vieja (%d dias; maximo %d, DEC-009)' % (edad, a.max_dias_base)
                              if edad > a.max_dias_base else ''], (0, 1), stdout=True))
    if 'secretos' in cats:
        es_git = os.path.exists(os.path.join(repo, '.git'))
        out = ruta('gitleaks.sarif')
        cmd = ['gitleaks', 'git' if es_git else 'dir', '--report-format', 'sarif', '--report-path', out, '--redact',
               '--no-banner', '--exit-code', '0']
        if a.base and es_git:
            cmd.append('--log-opts=%s..HEAD' % a.base)
        pasos.append(paso('secretos', 'gitleaks', cmd + [repo], out,
                          ['' if c['archivos'] else 'el repositorio no tiene archivos (regla del cero)'], (0,)))
    return pasos


def mostrar_plan(pasos, como_json):
    datos = {'estado': 'SIN DATOS', 'motivo': 'es solo el plan: no se corrio nada',
             'plan': [dict((k, p[k]) for k in ('categoria', 'herramienta', 'comando', 'motivo')) for p in pasos]}
    for x, p in zip(datos['plan'], pasos):
        x['instalada'] = bool(p['binario'])
    if como_json:
        print(normalizar.a_json(datos))
    else:
        print('ESCANEAR SEGURIDAD -- PLAN (no se corrio nada: SIN DATOS)')
        for p in datos['plan']:
            print('  %-9s %-12s %s' % (p['categoria'], p['herramienta'], ('NO CORRE: ' + p['motivo']) if p['motivo'] else 'corre'))
            print('      ' + ' '.join(p['comando']))
    return SIN_DATOS


def correr_pasos(pasos, repo, cats, inf, medido, faltan, salida):
    os.makedirs(salida, exist_ok=True)
    env = dict(os.environ, SEMGREP_SEND_METRICS='off', SEMGREP_ENABLE_VERSION_CHECK='0')
    for p in pasos:
        cat, herr = p['categoria'], p['herramienta']
        if p['motivo']:
            faltan[cat].append('%s: %s' % (herr, p['motivo']))
            continue
        rc, salida_std = ejecutar([p['binario']] + p['comando'][1:], env)
        if p['stdout']:
            with open(p['reporte'], 'w', encoding='utf-8') as h:
                h.write(salida_std or '')
        if rc is None or rc not in p['ok']:
            faltan[cat].append('%s salio con %s: no termino bien%s' % (
                herr, rc, ' (128 = no encontro paquetes)' if herr == 'osv-scanner' and rc == 128 else ''))
            continue
        if not os.path.isfile(p['reporte']):
            faltan[cat].append('%s no dejo su reporte' % herr)
            continue
        r = normalizar.leer(p['reporte'], cat, repo)
        if r['error']:
            faltan[cat].append('%s: %s' % (herr, r['error']))
            continue
        inf['hallazgos'] += [h for h in r['hallazgos'] if h['categoria'] in cats]
        anotar(r, cat, os.path.basename(p['reporte']), medido, faltan)


def anotar(r, cat, nombre, medido, faltan):
    """Regla del cero, por categoria: medio solo si el reporte muestra haber analizado algo DE ESA categoria."""
    if cat in r['evidencia'] or any(h['categoria'] == cat for h in r['hallazgos']):
        medido[cat].append(r['herramienta'])
    else:
        faltan[cat].append('%s (%s): el reporte no dice que haya analizado algo de %s (regla del cero)' % (
            r['herramienta'], nombre, cat))


def leer_reportes(reportes, cats, repo, inf, medido, faltan):
    sin_categoria = []
    for item in reportes:
        cat, ruta = '', item
        pre, sep, resto = item.partition(':')
        if sep and pre in normalizar.CATEGORIAS and resto:
            cat, ruta = pre, resto
        r = normalizar.leer(ruta, cat, repo)
        if r['error']:
            if cat and cat in cats:
                faltan[cat].append(r['error'])
            elif not cat:
                sin_categoria.append(r['error'])
            continue
        inf['hallazgos'] += [h for h in r['hallazgos'] if h['categoria'] in cats]
        for c in r['cubre']:
            if c in cats:
                anotar(r, c, os.path.basename(ruta), medido, faltan)
    for c in cats:
        faltan[c] += sin_categoria              # un reporte ilegible sin categoria no deja dar OK a ninguna
        if not medido[c] and not faltan[c]:
            faltan[c].append('no se paso ningun reporte de %s' % c)


def main():
    ap = argparse.ArgumentParser(description='Escaneo de seguridad de un repositorio de la aplicacion, normalizado (solo lectura).', allow_abbrev=False)
    ap.add_argument('--repo', default='')
    ap.add_argument('--reporte', action='append', default=[], help='un reporte ya generado; <categoria>:<archivo> fija la categoria')
    ap.add_argument('--solo', default=','.join(CATS))
    ap.add_argument('--base', default='', help='commit base de la Tarea: SAST diferencial y secretos solo del rango')
    ap.add_argument('--reglas', default='', help='reglas locales de opengrep/semgrep (archivo o carpeta)')
    ap.add_argument('--linea-base', default='')
    ap.add_argument('--max-dias-base', type=int, default=7)
    ap.add_argument('--salida', default='')
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    cats = [c.strip() for c in a.solo.split(',') if c.strip()]
    otras = [c for c in cats if c not in CATS]
    if otras or not cats:
        print('SIN DATOS -- --solo admite %s; no: %s.%s' % (', '.join(CATS), ', '.join(otras) or '(vacio)', (
            ' La configuracion de infraestructura (config) la mira auditar-iac.py.' if 'config' in otras else '')))
        return SIN_DATOS
    if a.base and (not BASE.match(a.base) or a.base.startswith('-')):
        print('SIN DATOS -- --base tiene que ser un commit o una rama: solo letras, numeros y . _ / -, sin empezar '
              'con guion (se pasa a semgrep y a gitleaks). No se corrio nada.')
        return SIN_DATOS
    if not a.repo and not a.reporte:
        print('SIN DATOS -- falta --repo <dir> o --reporte <archivo>.')
        return SIN_DATOS
    repo = os.path.abspath(a.repo) if a.repo else ''
    if repo and not os.path.isdir(repo):
        print('SIN DATOS -- %s no es una carpeta.' % repo)
        return SIN_DATOS
    huellas = None
    if a.linea_base:
        huellas, error = normalizar.cargar_linea_base(a.linea_base)
        if huellas is None:
            print('SIN DATOS -- %s: no se escanea como si no hubiera linea de base.' % error)
            return SIN_DATOS

    inf = normalizar.nuevo_informe('escanear-seguridad')
    inf['no_mira'] = list(NO_MIRA)
    medido, faltan = dict((c, []) for c in cats), dict((c, []) for c in cats)
    hora = time.strftime('%H%M%S')
    salida = ''
    if a.reporte:
        leer_reportes(a.reporte, cats, repo, inf, medido, faltan)
    else:
        destino = os.path.abspath(a.salida) if a.salida else os.path.join(RAIZ, 'borrador', 'seguridad', time.strftime('%Y-%m-%d'))
        pasos = armar_plan(repo, cats, a, destino, hora)
        if a.plan:
            return mostrar_plan(pasos, a.json)
        salida = destino
        correr_pasos(pasos, repo, cats, inf, medido, faltan, salida)
    if repo:
        inf['hallazgos'] += normalizar.revisar_supresiones(repo, cats)
    if huellas:
        normalizar.aplicar_linea_base(inf['hallazgos'], huellas)
    for c in cats:
        normalizar.poner_categoria(inf, c, medido[c], faltan[c])
    codigo = normalizar.cerrar(inf)
    pie = []
    if salida:
        informe = os.path.join(salida, '%s-informe.json' % hora)
        with open(informe, 'w', encoding='utf-8') as h:
            h.write(normalizar.a_json(inf))
        pie.append('Crudo e informe normalizado (locales, nunca se versionan): %s' % salida)
    if a.json:
        print(normalizar.a_json(inf))
    else:
        if any(normalizar.bloqueante(h) for h in inf['hallazgos']):
            pie.append('Siguiente paso: cada CRITICA o ALTA la verifica otro agente con contexto limpio; despues '
                       'recorrelos de a uno con la puerta `seguridad`. Nada se arregla solo ni en lote.')
        print('\n'.join(normalizar.lineas_texto(inf, 'ESCANEAR SEGURIDAD', pie)))
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
