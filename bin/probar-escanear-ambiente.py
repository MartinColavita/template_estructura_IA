#!/usr/bin/env python3
"""Prueba de bin/escanear-ambiente.py (GATE de PRUEBA ACTIVA) sobre inventarios y reportes de mentira.
Se corre:  python -B bin/probar-escanear-ambiente.py   -> OK o FALLA, con el detalle de cada caso.

Sin red, sin Docker y sin ZAP: los reportes los arma la prueba, y el 'docker' instalado es un falso que
anota con que lo llamaron y deja el reporte plantado donde ZAP lo dejaria."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'escanear-ambiente.py')
ESPERADOS = []
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `app-prueba` | url | prueba | https://prueba.example.com | si | media | N0 | pasivo | | producto |\n'
         '| `app-activa` | url | prueba | https://activa.example.com/ | si | media | nada | activo | | producto |\n'
         '| `app-prod` | url | produccion | https://www.example.com | si | alta | N0 | activo | | producto |\n'
         '| `web-prueba-1` | servidor | prueba | `web-prueba-1` | no | media | N1 | no | | operaciones |\n')
DATO = 'dato-' + 'sensible-7Q3X'                 # viaja en la query, el pedido y la respuesta: nunca en la salida
ZAP = 'ghcr.io/zaproxy/zaproxy@sha256:' + 'a' * 64


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:500]) if (detalle and not ok) else ''))


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def correr(*args, **kw):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=kw.get('env'))
    return r.returncode, r.stdout + r.stderr


def json_de(texto):
    try:
        return json.loads(texto)
    except ValueError:
        return {}


def alerta(plugin, nombre, riesgo, uri, cwe='693'):
    return {'pluginid': plugin, 'alertRef': plugin, 'alert': nombre, 'name': nombre, 'riskcode': riesgo, 'confidence': '2',
            'riskdesc': 'x', 'desc': '<p>d</p>', 'instances': [{'uri': uri, 'method': 'GET', 'param': 'q', 'attack': DATO, 'evidence': DATO}],
            'count': '1', 'solution': 's', 'otherinfo': DATO, 'reference': 'r', 'cweid': cwe, 'wascid': '15', 'sourceid': '1'}


def zap(sitios):
    return json.dumps({'@version': '2.16.0', '@generated': 'hoy', 'site': [
        {'@name': n, '@host': 'h', '@port': '443', '@ssl': 'true', 'alerts': a} for n, a in sitios]})


def sarif_de(nombre, uris):
    return json.dumps({'version': '2.1.0', 'runs': [{
        'tool': {'driver': {'name': nombre, 'rules': [{'id': 'r1', 'properties': {'security-severity': '8.0'}}]}},
        'invocations': [{'executionSuccessful': True}],
        'results': [{'ruleId': 'r1', 'level': 'error', 'locations': [{'physicalLocation': {
            'artifactLocation': {'uri': u}, 'region': {'startLine': 3}}}]} for u in uris]}]})


def docker_falso(tmp):
    carpeta = os.path.join(tmp, 'falsos')
    os.makedirs(carpeta, exist_ok=True)
    py = escribir(os.path.join(carpeta, 'falso.py'), (
        'import os, shutil, sys\n'
        'args = sys.argv[1:]\n'
        'with open(os.environ["FALSO_REGISTRO"], "a") as h:\n'
        '    h.write(" ".join(args) + "\\n")\n'
        'if args[:2] == ["image", "inspect"]:\n'
        '    sys.exit(int(os.environ.get("FALSO_IMAGEN_RC", "0")))\n'
        'if args and args[0] == "run":\n'
        '    carpeta = args[args.index("-v") + 1].rsplit(":/zap/wrk", 1)[0]\n'
        '    shutil.copy(os.environ["FALSO_REPORTE"], os.path.join(carpeta, args[args.index("-J") + 1]))\n'
        '    sys.exit(int(os.environ.get("FALSO_RC", "0")))\n'
        'sys.exit(9)\n'))
    if os.name == 'nt':
        escribir(os.path.join(carpeta, 'docker.cmd'), '@"%s" "%s" %%*\r\n' % (sys.executable, py))
    else:
        envoltorio = escribir(os.path.join(carpeta, 'docker'), '#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, py))
        os.chmod(envoltorio, os.stat(envoltorio).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return carpeta


def main():
    print('== escanear-ambiente (GATE de PRUEBA ACTIVA)')
    tmp = tempfile.mkdtemp(prefix='probar-esc-amb-')
    inv = escribir(os.path.join(tmp, 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)
    alta = escribir(os.path.join(tmp, 'zap-alta.json'), zap([('https://prueba.example.com', [
        alerta('40012', 'Cross Site Scripting (Reflected)', '3', 'https://prueba.example.com/buscar?q=' + DATO, '79'),
        alerta('10038', 'Content Security Policy Header Not Set', '2', 'https://prueba.example.com/')])]))
    media = escribir(os.path.join(tmp, 'zap-media.json'), zap([('https://prueba.example.com', [
        alerta('10038', 'Content Security Policy Header Not Set', '2', 'https://prueba.example.com/'),
        alerta('10021', 'X-Content-Type-Options Header Missing', '1', 'https://prueba.example.com/app.js')])]))
    vacio = os.path.join(tmp, 'path-vacio')
    os.makedirs(vacio)
    sin_docker = dict(os.environ, PATH=vacio)

    rc, out = correr()
    caso('sin --alias: SIN DATOS (2)', rc == 2, out[:200])
    rc, out = correr('--alias', 'app-prueba', '--inventario', os.path.join(tmp, 'no.md'), '--reporte', alta)
    caso('sin inventario: SIN DATOS (2) y no normaliza nada', rc == 2 and 'Cross Site' not in out, out[:300])
    rc, out = correr('--alias', 'otra-app', '--inventario', inv, '--reporte', alta)
    caso('un alias que no esta en el inventario: FRENA (1) y no lee el reporte', rc == 1 and 'FRENA' in out and 'Cross Site' not in out, out[:300])
    rc, out = correr('--alias', 'web-prueba-1', '--inventario', inv, '--reporte', alta)
    caso('un servidor no es una URL: FRENA (1)', rc == 1 and 'FRENA' in out, out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', alta, '--activo')
    caso('--activo contra una URL que solo admite pasivo: FRENA (1), aunque se pase un reporte', rc == 1 and 'FRENA' in out and 'Cross Site' not in out, out[:300])
    rc, out = correr('--alias', 'app-prod', '--inventario', inv, '--reporte', alta, '--activo')
    caso('--activo contra produccion: FRENA (1) aunque la fila diga activo', rc == 1 and 'produccion' in out, out[:300])
    rc, out = correr('--alias', 'otra-app', '--inventario', inv, '--json')
    d = json_de(out)
    caso('el FRENA con --json es un informe del esquema comun: veredicto FRENA, sin hallazgos y con su motivo',
         rc == 1 and d.get('veredicto') == 'FRENA' and d.get('hallazgos') == [] and 'inventario' in d.get('motivo', '')
         and d.get('origen') == 'escanear-ambiente', out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--url', 'https://otra.example.com')
    caso('no acepta una URL por argumento (sale 2 y no corre nada): la URL es la del inventario', rc == 2, out[:200])

    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', alta)
    caso('pasivo autorizado con una alerta de riesgo alto: HALLAZGO (1)', rc == 1 and out.startswith('ESCANEAR AMBIENTE -- HALLAZGO'), out[:400])
    caso('el texto termina con lo que NO mira', 'Lo que este script NO mira' in out)
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', alta, '--json')
    d = json_de(out)
    hs = d.get('hallazgos', [])
    xss = [h for h in hs if h.get('regla') == '40012']
    caso('--json: todo es dast, con el alias del inventario como activo', hs and all(h.get('categoria') == 'dast' and h.get('activo') == 'app-prueba' for h in hs), hs)
    caso('--json: riesgo alto de ZAP -> ALTA, con CWE y la direccion sin la query',
         xss and xss[0].get('severidad') == 'ALTA' and xss[0].get('cwe') == 'CWE-79' and xss[0].get('archivo') == 'https://prueba.example.com/buscar', xss)
    caso('ni la query, ni el ataque, ni la evidencia, ni la respuesta aparecen en la salida', DATO not in out, out[:300])
    caso('--json: el esquema comun y origen escanear-ambiente', d.get('origen') == 'escanear-ambiente'
         and sorted(d) == sorted(['veredicto', 'origen', 'generado', 'categorias', 'hallazgos', 'sin_datos', 'no_mira']), sorted(d))
    caso('--json es ASCII', all(ord(c) < 128 for c in out))
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', media)
    caso('solo riesgos medio y bajo: OK (0), con avisos', rc == 0 and out.startswith('ESCANEAR AMBIENTE -- OK') and 'aviso' in out, out[:300])

    fuera = escribir(os.path.join(tmp, 'zap-fuera.json'), zap([('https://prueba.example.com', [
        alerta('10038', 'CSP', '2', 'https://prueba.example.com/')]), ('https://cdn.otro-dominio.example.net', [
        alerta('40012', 'XSS', '3', 'https://cdn.otro-dominio.example.net/x')])]))
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', fuera, '--json')
    d = json_de(out)
    caso('la herramienta salio del alcance: HALLAZGO (1), lo dice, y lo de afuera no se cuenta como de la aplicacion',
         rc == 1 and 'alcance' in d.get('categorias', {}).get('dast', {}).get('motivo', '')
         and not any('otro-dominio' in h.get('archivo', '') for h in d.get('hallazgos', [])), out[:500])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', escribir(os.path.join(tmp, 'zap-vacio.json'), zap([])))
    caso('un reporte sin ningun sitio: SIN DATOS (2), no llego a la URL', rc == 2, out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', escribir(os.path.join(tmp, 'roto.json'), '{'))
    caso('un reporte ilegible: SIN DATOS (2)', rc == 2, out[:300])

    nu = escribir(os.path.join(tmp, 'nuclei.jsonl'), json.dumps({
        'template-id': 'CVE-2026-1111', 'info': {'name': 'Ejecucion remota de prueba', 'severity': 'high',
                                                 'classification': {'cve-id': ['cve-2026-1111'], 'cwe-id': ['cwe-94']}},
        'type': 'http', 'host': 'https://prueba.example.com', 'matched-at': 'https://prueba.example.com/api?token=' + DATO,
        'request': 'GET ' + DATO, 'response': DATO, 'extracted-results': [DATO], 'curl-command': 'curl ' + DATO,
        'timestamp': '2026-11-17T10:00:00Z', 'matcher-status': True}) + '\n')
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte', nu, '--json')
    d = json_de(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('Nuclei (JSONL): ALTA, CVE y CWE normalizados, sin pedido ni respuesta',
         rc == 1 and h.get('cve') == 'CVE-2026-1111' and h.get('cwe') == 'CWE-94' and h.get('archivo') == 'https://prueba.example.com/api'
         and DATO not in out, out[:400])

    # --- dast acepta solo reportes de prueba dinamica (F2 5)
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte',
                     escribir(os.path.join(tmp, 'semgrep.sarif'), sarif_de('Semgrep OSS', ['src/app.py'])), '--json')
    d = json_de(out)
    caso('--reporte con un SARIF de Semgrep (analisis estatico): SIN DATOS (2), no es una prueba dinamica',
         rc == 2 and d.get('categorias', {}).get('dast', {}).get('estado') == 'SIN DATOS' and not d.get('hallazgos'), out[:400])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte',
                     escribir(os.path.join(tmp, 'nuclei.sarif'), sarif_de('nuclei', ['https://prueba.example.com/api?token=' + DATO])), '--json')
    d = json_de(out)
    caso('--reporte con un SARIF de Nuclei con URIs en el alcance: se lee (HALLAZGO), sin la query',
         rc == 1 and [x.get('archivo') for x in d.get('hallazgos', [])] == ['https://prueba.example.com/api'] and DATO not in out, out[:400])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--reporte',
                     escribir(os.path.join(tmp, 'nuclei-fuera.sarif'), sarif_de('nuclei', ['https://otro.example.net/x'])), '--json')
    d = json_de(out)
    caso('--reporte con un SARIF de Nuclei con URIs fuera del alcance: no cuenta como de la aplicacion y no es OK',
         rc != 0 and not d.get('hallazgos'), out[:400])

    # --- la imagen de ZAP va por digest (DEC-009)
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--salida', os.path.join(tmp, 'salida-vacia'), env=sin_docker)
    caso('sin --imagen (el valor por defecto pide el digest): SIN DATOS (2) y dice que va por digest', rc == 2 and 'digest' in out, out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--imagen', 'ghcr.io/zaproxy/zaproxy:stable',
                     '--salida', os.path.join(tmp, 'salida-vacia'), env=sin_docker)
    caso('--imagen con etiqueta y sin @sha256: SIN DATOS (2), la imagen va por digest', rc == 2 and 'digest' in out, out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--imagen', ZAP, '--salida', os.path.join(tmp, 'salida-vacia'), env=sin_docker)
    caso('sin Docker instalado y sin reporte: SIN DATOS (2), y lo dice', rc == 2 and 'docker' in out.lower(), out[:300])

    carpeta = docker_falso(tmp)
    registro = os.path.join(tmp, 'registro.txt')
    salida = os.path.join(tmp, 'salida con espacios')
    env = dict(os.environ, PATH=carpeta, FALSO_REPORTE=alta, FALSO_REGISTRO=registro)
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--imagen', ZAP, '--salida', salida, env=env)
    llamado = open(registro).read() if os.path.isfile(registro) else ''
    corrida = [l for l in llamado.splitlines() if l.startswith('run ')]
    caso('con docker (falso): pasivo corre zap-baseline contra la URL exacta del inventario',
         rc == 1 and corrida and 'zap-baseline.py' in corrida[0] and '-t https://prueba.example.com ' in corrida[0] + ' '
         and 'zap-full-scan.py' not in llamado, llamado + out[:300])
    caso('nunca baja la imagen (--pull never) ni pasa opciones arbitrarias a ZAP',
         corrida and '--pull never' in corrida[0] and ' -z ' not in corrida[0] + ' ' and ' -u ' not in corrida[0] + ' ', corrida)
    guardados = sorted(os.listdir(salida)) if os.path.isdir(salida) else []
    caso('lo crudo y el informe normalizado quedan en la carpeta de salida', any('zap' in g for g in guardados)
         and any(g.endswith('informe.json') for g in guardados), guardados)
    if os.path.isfile(registro):
        os.remove(registro)
    rc, out = correr('--alias', 'app-activa', '--inventario', inv, '--imagen', ZAP, '--salida', salida, '--activo',
                     env=dict(env, FALSO_REPORTE=escribir(os.path.join(tmp, 'zap-activa.json'), zap([('https://activa.example.com', [])]))))
    llamado = open(registro).read() if os.path.isfile(registro) else ''
    caso('--activo autorizado: corre zap-full-scan contra la URL del inventario',
         'zap-full-scan.py' in llamado and 'https://activa.example.com/' in llamado and rc == 0, llamado + out[:300])
    if os.path.isfile(registro):
        os.remove(registro)
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--imagen', ZAP, '--salida', salida, env=dict(env, FALSO_IMAGEN_RC='1'))
    llamado = open(registro).read() if os.path.isfile(registro) else ''
    caso('la imagen de ZAP no esta en la maquina: SIN DATOS (2) y no se corre nada',
         rc == 2 and 'run ' not in llamado and 'imagen' in out, llamado + out[:300])
    rc, out = correr('--alias', 'app-prueba', '--inventario', inv, '--imagen', ZAP, '--salida', salida, env=dict(env, FALSO_RC='3'))
    caso('ZAP sale con 3 (otra falla): SIN DATOS (2)', rc == 2, out[:300])

    # --- el tope de tiempo: el contenedor se frena por su nombre (la funcion que ejecuta se reemplaza)
    try:
        spec = importlib.util.spec_from_file_location('escanear_ambiente_en_prueba', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        mod = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    if mod is not None:
        llamadas = []

        def ejecutar(cmd, tope=None):
            llamadas.append(list(cmd))
            return getattr(mod, 'VENCIO', None) if 'run' in cmd else 0
        mod.ejecutar = ejecutar
        mod.shutil.which = lambda n: '/usr/bin/' + n
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = mod.main(['--alias', 'app-prueba', '--inventario', inv, '--imagen', ZAP, '--salida', os.path.join(tmp, 'salida-tope')])
        except Exception as e:
            rc = 'exploto: %s: %s' % (type(e).__name__, e)
        finally:
            mod.shutil.which = shutil.which
        out = buf.getvalue()
        corrida = [c for c in llamadas if 'run' in c]
        nombre = corrida[0][corrida[0].index('--name') + 1] if corrida and '--name' in corrida[0] else ''
        caso('ZAP se lanza con --name zap-<marca>', nombre.startswith('zap-'), corrida)
        caso('al vencer el tope: docker kill sobre ese nombre, y SIN DATOS (2)',
             rc == 2 and nombre and any(c[1:] == ['kill', nombre] for c in llamadas) and 'tope' in out, (rc, llamadas, out[:300]))

    fuente = open(SCRIPT, 'rb').read() if os.path.isfile(SCRIPT) else b'\xff'
    caso('escanear-ambiente.py es ASCII puro', all(b < 128 for b in fuente))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
