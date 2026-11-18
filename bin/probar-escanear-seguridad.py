#!/usr/bin/env python3
"""Prueba de bin/escanear-seguridad.py y del normalizador de bin/seguridad/ sobre reportes plantados.
Se corre:  python -B bin/probar-escanear-seguridad.py   -> OK o FALLA, con el detalle de cada caso.

Sin red y sin ningun escaner instalado: los reportes los arma la prueba, y la unica herramienta
'instalada' es un falso que copia un reporte plantado donde el script se lo pide."""

import datetime
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'escanear-seguridad.py')
ESPERADOS = []
SECRETO = 'AKIA' + 'PLANTADO' + '7Q3XZ9W2'          # nunca tiene que aparecer en la salida
HOY = datetime.date.today()
FUTURO = (HOY + datetime.timedelta(days=60)).isoformat()
PASADO = (HOY - datetime.timedelta(days=10)).isoformat()
CLAVES = ['veredicto', 'origen', 'generado', 'categorias', 'hallazgos', 'sin_datos', 'no_mira']
CLAVES_H = ['herramienta', 'categoria', 'regla', 'titulo', 'cwe', 'cve', 'severidad', 'archivo', 'linea', 'paquete',
            'version', 'arreglo', 'activo', 'huella', 'estado', 'motivo_supresion', 'vence']
NUNCA = ('--autofix', '-a', 'fix', '--fix', '--download-offline-databases', '--validate', '--metrics=on',
         '--metrics=auto', '--config=auto', 'auto', '-u', '-z', '--hook')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:600]) if (detalle and not ok) else ''))


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def escribir_json(ruta, datos):
    return escribir(ruta, json.dumps(datos, indent=1))


def correr(*args, **kw):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=kw.get('env'))
    return r.returncode, r.stdout + r.stderr


def json_de(texto):
    try:
        return json.loads(texto)
    except ValueError:
        return {}


def sarif(nombre, resultados, reglas=(), exito=True, props=None):
    run = {'tool': {'driver': {'name': nombre, 'rules': list(reglas)}}, 'results': list(resultados)}
    if exito is not None:
        run['invocations'] = [{'executionSuccessful': exito}]
    if props:
        run['properties'] = props
    return {'version': '2.1.0', '$schema': 'https://json.schemastore.org/sarif-2.1.0.json', 'runs': [run]}


def res(regla, uri, linea, nivel=None, props=None, mensaje='mensaje', snippet=None, supresiones=None, huella=None):
    r = {'ruleId': regla, 'message': {'text': mensaje},
         'locations': [{'physicalLocation': {'artifactLocation': {'uri': uri}, 'region': {'startLine': linea}}}]}
    if nivel:
        r['level'] = nivel
    if props:
        r['properties'] = props
    if snippet:
        r['locations'][0]['physicalLocation']['region']['snippet'] = {'text': snippet}
    if supresiones is not None:
        r['suppressions'] = supresiones
    if huella:
        r['partialFingerprints'] = {'primaryLocationLineHash': huella}
    return r


def regla(rid, puntaje=None, nivel=None, tags=(), nombre=None):
    r = {'id': rid, 'shortDescription': {'text': nombre or ('descripcion de ' + rid)}, 'properties': {'tags': list(tags)}}
    if puntaje is not None:
        r['properties']['security-severity'] = puntaje
    if nivel:
        r['defaultConfiguration'] = {'level': nivel}
    return r


def osv(paquetes):
    return {'results': [{'source': {'path': '/repo/requirements.txt', 'type': 'lockfile'}, 'packages': paquetes}]}


def falso(tmp, nombre):
    """Una herramienta de mentira: copia el reporte de FALSO_REPORTE donde el script le pide y anota los argumentos."""
    carpeta = os.path.join(tmp, 'falsos')
    os.makedirs(carpeta, exist_ok=True)
    py = escribir(os.path.join(carpeta, 'falso.py'), (
        'import os, shutil, sys\n'
        'args = sys.argv[1:]\n'
        'with open(os.environ["FALSO_REGISTRO"], "a") as h:\n'
        '    h.write(" ".join(args) + "\\n")\n'
        'if "--report-path" in args:\n'
        '    shutil.copy(os.environ["FALSO_REPORTE"], args[args.index("--report-path") + 1])\n'
        'sys.exit(int(os.environ.get("FALSO_RC", "0")))\n'))
    if os.name == 'nt':
        escribir(os.path.join(carpeta, nombre + '.cmd'), '@"%s" "%s" %%*\r\n' % (sys.executable, py))
    else:
        envoltorio = escribir(os.path.join(carpeta, nombre), '#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, py))
        os.chmod(envoltorio, os.stat(envoltorio).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return carpeta


def main():
    print('== escanear-seguridad (y el normalizador de bin/seguridad/)')
    tmp = tempfile.mkdtemp(prefix='probar-esc-seg-')
    vacio = os.path.join(tmp, 'path-vacio')
    os.makedirs(vacio)
    sin_herramientas = dict(os.environ, PATH=vacio)

    # --- insumos ausentes, vacios o ilegibles: nunca 0
    rc, out = correr()
    caso('sin --repo ni --reporte: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--repo', os.path.join(tmp, 'no-existe'))
    caso('un --repo que no existe: SIN DATOS (2)', rc == 2, out[:200])
    rc, out = correr('--reporte', os.path.join(tmp, 'no.sarif'), '--solo', 'sast')
    caso('un reporte que no existe: SIN DATOS (2)', rc == 2 and 'no.sarif' in out, out[:300])
    rc, out = correr('--reporte', escribir(os.path.join(tmp, 'vacio.sarif'), ''), '--solo', 'sast')
    caso('un reporte vacio: SIN DATOS (2)', rc == 2 and 'vacio' in out, out[:300])
    rc, out = correr('--reporte', escribir(os.path.join(tmp, 'basura.sarif'), 'esto no es json {'), '--solo', 'sast')
    caso('un reporte ilegible: SIN DATOS (2)', rc == 2, out[:300])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'raro.json'), {'cosa': 1}), '--solo', 'sast')
    caso('un JSON de formato desconocido: SIN DATOS (2), dice que no lo reconoce', rc == 2 and 'desconocido' in out, out[:300])
    rc, out = correr('--reporte', os.path.join(tmp, 'x.sarif'), '--solo', 'sast,dast')
    caso('--solo con una categoria que no es de este script: SIN DATOS (2)', rc == 2 and 'dast' in out, out[:300])

    # --- SAST en SARIF: severidad, HALLAZGO, aviso, regla del cero
    alta = escribir_json(os.path.join(tmp, 'semgrep-alta.sarif'), sarif('Semgrep OSS', [
        res('py.eval', 'src/app.py', 12, nivel='warning')], [regla('py.eval', puntaje='8.1', tags=['CWE-95: eval'])]))
    rc, out = correr('--reporte', alta, '--solo', 'sast')
    caso('SAST con una ALTA nueva: HALLAZGO (1)', rc == 1 and out.startswith('ESCANEAR SEGURIDAD -- HALLAZGO'), out[:300])
    caso('el texto termina con lo que NO mira', 'Lo que este script NO mira' in out)
    rc, out = correr('--reporte', alta, '--solo', 'sast', '--json')
    d = json_de(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('--json: las claves del esquema comun, ni una mas ni una menos', sorted(d) == sorted(CLAVES) and sorted(h) == sorted(CLAVES_H), sorted(d))
    caso('--json: severidad por security-severity (8,1 -> ALTA), CWE, archivo y linea',
         h.get('severidad') == 'ALTA' and h.get('cwe') == 'CWE-95' and h.get('archivo') == 'src/app.py' and h.get('linea') == 12
         and h.get('categoria') == 'sast' and h.get('herramienta') == 'semgrep' and h.get('estado') == 'nuevo', h)
    caso('--json: veredicto y categoria', d.get('veredicto') == 'HALLAZGO' and d['categorias']['sast']['estado'] == 'HALLAZGO'
         and d.get('origen') == 'escanear-seguridad', d.get('categorias'))
    caso('--json es ASCII', all(ord(c) < 128 for c in out))

    media = escribir_json(os.path.join(tmp, 'semgrep-media.sarif'), sarif('semgrep', [
        res('py.debug', 'src/app.py', 3)], [regla('py.debug', nivel='warning')]))
    rc, out = correr('--reporte', media, '--solo', 'sast')
    caso('SAST con solo una MEDIA (level warning): OK (0) y la MEDIA queda como aviso', rc == 0 and 'MEDIA' in out and 'aviso' in out, out[:400])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'limpio-sin-evidencia.sarif'), sarif('semgrep', [], exito=None)), '--solo', 'sast')
    caso('SARIF sin resultados y sin nada que diga que analizo algo: SIN DATOS (regla del cero)', rc == 2 and 'regla del cero' in out, out[:400])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'fallo.sarif'), sarif('semgrep', [], exito=False)), '--solo', 'sast')
    caso('SARIF con executionSuccessful false: SIN DATOS', rc == 2 and 'no termino bien' in out, out[:400])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'bandit-cero.sarif'), sarif('Bandit', [], props={'metrics': {'_totals': {'loc': 0}}})), '--solo', 'sast')
    caso('Bandit con 0 lineas analizadas: SIN DATOS aunque diga que termino bien', rc == 2, out[:400])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'limpio.sarif'), sarif('semgrep', [])), '--solo', 'sast')
    caso('SARIF limpio que dice que termino bien: OK (0)', rc == 0 and out.startswith('ESCANEAR SEGURIDAD -- OK'), out[:300])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'v1.sarif'), dict(sarif('semgrep', []), version='1.0.0')), '--solo', 'sast')
    caso('una version de SARIF que no es 2.1: SIN DATOS', rc == 2 and 'version' in out, out[:300])

    orden = escribir_json(os.path.join(tmp, 'orden.sarif'), sarif('CodeQL', [
        res('r-nota', 'a.py', 1, nivel='note', props={'security-severity': '9.5'}),
        res('r-bandit', 'b.py', 2, nivel='note', props={'issue_severity': 'HIGH'}),
        res('r-error', 'c.py', 3, nivel='error'),
        res('r-regla', 'd.py', 4)], [regla('r-regla', nivel='note')]))
    d = json_de(correr('--reporte', orden, '--solo', 'sast', '--json')[1])
    sev = dict((x['regla'], x['severidad']) for x in d.get('hallazgos', []))
    caso('orden de la severidad: security-severity > la de la herramienta > level de SARIF',
         sev == {'r-nota': 'CRITICA', 'r-bandit': 'ALTA', 'r-error': 'ALTA', 'r-regla': 'BAJA'}, sev)

    # --- secretos: siempre ALTA, nunca el valor
    gl = escribir_json(os.path.join(tmp, 'gitleaks.sarif'), sarif('gitleaks', [
        res('aws-access-token', 'config/app.env', 4, mensaje='aws-access-token has detected secret ' + SECRETO, snippet='KEY=' + SECRETO)],
        [regla('aws-access-token', nombre='AWS ' + 'access token')]))
    rc, out = correr('--reporte', gl, '--solo', 'secretos')
    rc2, out2 = correr('--reporte', gl, '--solo', 'secretos', '--json')
    d = json_de(out2)
    h = (d.get('hallazgos') or [{}])[0]
    caso('un secreto (sin level): siempre ALTA y HALLAZGO', rc == 1 and h.get('severidad') == 'ALTA' and h.get('categoria') == 'secretos', h)
    caso('el valor del secreto no aparece ni en el texto ni en el JSON', SECRETO not in out and SECRETO not in out2, out[:300])
    th = escribir(os.path.join(tmp, 'trufflehog.jsonl'), json.dumps({
        'SourceMetadata': {'Data': {'Filesystem': {'file': 'src/conf.py', 'line': 7}}}, 'DetectorName': 'AWS', 'Verified': False,
        'Raw': SECRETO, 'RawV2': SECRETO + 'x', 'Redacted': SECRETO[:6]}) + '\n')
    rc, out = correr('--reporte', th, '--solo', 'secretos', '--json')
    d = json_de(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('TruffleHog (JSONL): un hallazgo de secretos, ALTA, con archivo y linea, sin el valor',
         rc == 1 and h.get('herramienta') == 'trufflehog' and h.get('archivo') == 'src/conf.py' and h.get('linea') == 7 and SECRETO not in out, out[:400])

    # --- SCA: OSV-Scanner, pip-audit, npm audit
    vuln = {'id': 'GHSA-aaaa-bbbb-cccc', 'aliases': ['CVE-2026-1234'], 'summary': 'ejecucion remota',
            'database_specific': {'severity': 'HIGH', 'cwe_ids': ['CWE-502']},
            'affected': [{'package': {'name': 'libx', 'ecosystem': 'PyPI'}, 'ranges': [{'type': 'ECOSYSTEM', 'events': [{'introduced': '0'}, {'fixed': '2.4.1'}]}]}]}
    o = escribir_json(os.path.join(tmp, 'osv.json'), osv([{'package': {'name': 'libx', 'version': '2.3.0', 'ecosystem': 'PyPI'},
                                                          'vulnerabilities': [vuln], 'groups': [{'ids': ['GHSA-aaaa-bbbb-cccc'], 'aliases': ['GHSA-aaaa-bbbb-cccc', 'CVE-2026-1234'], 'max_severity': '9.8'}]}]))
    rc, out = correr('--reporte', o, '--solo', 'sca', '--json')
    d = json_de(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('OSV-Scanner (JSON): CRITICA por max_severity, con CVE, paquete, version, arreglo y CWE',
         rc == 1 and h.get('severidad') == 'CRITICA' and h.get('cve') == 'CVE-2026-1234' and h.get('paquete') == 'libx'
         and h.get('version') == '2.3.0' and h.get('arreglo') == '2.4.1' and h.get('cwe') == 'CWE-502' and h.get('categoria') == 'sca', h)
    sin_sev = dict(vuln, database_specific={})
    o2 = escribir_json(os.path.join(tmp, 'osv-sin-sev.json'), osv([{'package': {'name': 'libx', 'version': '2.3.0', 'ecosystem': 'PyPI'},
                                                                  'vulnerabilities': [sin_sev], 'groups': [{'ids': ['GHSA-aaaa-bbbb-cccc']}]}]))
    d = json_de(correr('--reporte', o2, '--solo', 'sca', '--json')[1])
    h = (d.get('hallazgos') or [{}])[0]
    caso('una vulnerabilidad sin severidad informada se toma ALTA (conservador) y lo dice', h.get('severidad') == 'ALTA' and 'severidad' in h.get('titulo', ''), h)
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'osv-limpio.json'), {'results': []}), '--solo', 'sca')
    caso('OSV limpio sin paquetes listados: SIN DATOS (no dice cuantos paquetes miro)', rc == 2, out[:300])
    pa = escribir_json(os.path.join(tmp, 'pip-audit.json'), {'dependencies': [
        {'name': 'flask', 'version': '0.5', 'vulns': [{'id': 'PYSEC-2019-179', 'fix_versions': ['1.0'], 'aliases': ['CVE-2019-1010083']}]},
        {'name': 'requests', 'version': '2.31.0', 'vulns': []}], 'fixes': []})
    d = json_de(correr('--reporte', pa, '--solo', 'sca', '--json')[1])
    h = (d.get('hallazgos') or [{}])[0]
    caso('pip-audit (JSON): paquete, CVE por alias, arreglo; sin severidad -> ALTA',
         h.get('herramienta') == 'pip-audit' and h.get('cve') == 'CVE-2019-1010083' and h.get('arreglo') == '1.0' and h.get('severidad') == 'ALTA', h)
    npm = {'auditReportVersion': 2, 'vulnerabilities': {'minimist': {
        'name': 'minimist', 'severity': 'moderate', 'isDirect': False, 'nodes': ['node_modules/minimist'],
        'via': [{'source': 1097678, 'name': 'minimist', 'title': 'Prototype Pollution', 'url': 'https://github.com/advisories/GHSA-xvch-5gv4-984h',
                 'severity': 'moderate', 'cwe': ['CWE-1321'], 'range': '<0.2.4'}], 'fixAvailable': True}},
        'metadata': {'vulnerabilities': {'moderate': 1, 'total': 1}, 'dependencies': {'prod': 40, 'total': 40}}}
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'npm.json'), npm), '--solo', 'sca', '--json')
    d = json_de(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('npm audit (JSON): moderate -> MEDIA, regla GHSA, no frena (0)',
         rc == 0 and h.get('severidad') == 'MEDIA' and h.get('regla') == 'GHSA-xvch-5gv4-984h' and h.get('cwe') == 'CWE-1321', out[:400])
    npm['vulnerabilities']['minimist']['via'][0]['severity'] = 'high'
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'npm-alta.json'), npm), '--solo', 'sca')
    caso('npm audit con una high: HALLAZGO (1)', rc == 1, out[:300])

    # --- configuracion (Trivy): la categoria sale de las etiquetas de la regla
    tv = escribir_json(os.path.join(tmp, 'trivy.sarif'), sarif('Trivy', [
        res('AVD-DS-0002', 'Dockerfile', 1, nivel='error'),
        res('CVE-2026-9999', 'requirements.txt', 1, nivel='error', mensaje='Package: libz\nInstalled Version: 1.0\nVulnerability CVE-2026-9999\nSeverity: HIGH\nFixed Version: 1.1\nLink: [x](y)')],
        [regla('AVD-DS-0002', puntaje='8.0', tags=['misconfiguration', 'security', 'HIGH']),
         regla('CVE-2026-9999', puntaje='7.5', tags=['vulnerability', 'security', 'HIGH'])]))
    d = json_de(correr('--reporte', tv, '--solo', 'sca', '--json')[1])
    cats = dict((x['regla'], (x['categoria'], x['paquete'], x['version'], x['arreglo'], x['cve'])) for x in d.get('hallazgos', []))
    caso('Trivy: vulnerability -> sca con paquete, version y arreglo leidos del mensaje; la misconfiguration no es de este script',
         'AVD-DS-0002' not in cats and cats.get('CVE-2026-9999') == ('sca', 'libz', '1.0', '1.1', 'CVE-2026-9999'), cats)
    rc, out = correr('--reporte', tv, '--solo', 'config')
    caso('--solo config: SIN DATOS (2); la configuracion de infraestructura la mira auditar-iac.py', rc == 2 and 'config' in out, out[:300])
    rc, out = correr('--reporte', tv, '--solo', 'sca')
    caso('lo que NO mira nombra a auditar-iac.py para Dockerfile, Compose, Terraform y Kubernetes',
         'auditar-iac.py' in out.split('NO mira')[-1] and 'Dockerfile' in out.split('NO mira')[-1], out[-500:])

    # --- supresiones dentro del SARIF: con motivo y vencimiento vigentes, o no vale
    def con_sup(sup):
        return escribir_json(os.path.join(tmp, 'sup-%d.sarif' % len(ESPERADOS)), sarif('semgrep', [
            res('py.eval', 'src/app.py', 12, supresiones=sup)], [regla('py.eval', puntaje='8.0')]))
    rc, out = correr('--reporte', con_sup([{'kind': 'external', 'status': 'accepted', 'justification': 'entrada fija, no la controla nadie',
                                            'properties': {'vence': FUTURO}}]), '--solo', 'sast', '--json')
    d = json_de(out)
    caso('supresion con motivo y vencimiento vigente: suprimido, no frena (0)',
         rc == 0 and (d.get('hallazgos') or [{}])[0].get('estado') == 'suprimido', out[:300])
    rc, out = correr('--reporte', con_sup([{'kind': 'inSource', 'properties': {'vence': FUTURO}}]), '--solo', 'sast')
    caso('supresion sin motivo: HALLAZGO (1)', rc == 1, out[:300])
    rc, out = correr('--reporte', con_sup([{'kind': 'external', 'justification': 'ya lo vimos con el equipo', 'properties': {'vence': PASADO}}]), '--solo', 'sast')
    caso('supresion vencida: HALLAZGO (1)', rc == 1, out[:300])
    rc, out = correr('--reporte', con_sup([{'kind': 'external', 'justification': 'ya lo vimos con el equipo'}]), '--solo', 'sast')
    caso('supresion sin vencimiento: HALLAZGO (1)', rc == 1, out[:300])
    rc, out = correr('--reporte', con_sup([{'kind': 'external', 'status': 'rejected', 'justification': 'no aplica aca', 'properties': {'vence': FUTURO}}]), '--solo', 'sast')
    caso('supresion rechazada no suprime: HALLAZGO (1)', rc == 1, out[:300])

    # --- linea de base: lo heredado no frena, pero sigue en el informe
    base = escribir(os.path.join(tmp, 'linea-base.json'), correr('--reporte', alta, '--solo', 'sast', '--json')[1])
    rc, out = correr('--reporte', alta, '--solo', 'sast', '--linea-base', base, '--json')
    d = json_de(out)
    caso('una ALTA que esta en la linea de base: no frena (0) y sigue listada como en-linea-base',
         rc == 0 and len(d.get('hallazgos', [])) == 1 and d['hallazgos'][0]['estado'] == 'en-linea-base', out[:300])
    con_mas = json_de(open(base, encoding='utf-8').read())
    con_mas.update({'chequeos': [], 'motivo': '', 'crudo': 'x', 'indice_lynis': 70})
    rc, out = correr('--reporte', alta, '--solo', 'sast', '--json', '--linea-base', escribir(os.path.join(tmp, 'base-mas.json'), json.dumps(con_mas)))
    caso('una linea de base con claves de mas en la raiz se lee igual', rc == 0 and json_de(out).get('hallazgos', [{}])[0].get('estado') == 'en-linea-base', out[:300])
    rc, out = correr('--reporte', alta, '--solo', 'sast', '--linea-base', escribir(os.path.join(tmp, 'base-rota.json'), 'nada'))
    caso('una linea de base ilegible: SIN DATOS (2), no se escanea como si no hubiera', rc == 2 and 'linea de base' in out, out[:300])

    # --- huella: resiste que el codigo se corra unas lineas
    r1, r2 = os.path.join(tmp, 'repo-h1'), os.path.join(tmp, 'repo-h2')
    escribir(os.path.join(r1, 'src', 'app.py'), 'import os\n    resultado = eval(dato)\n')
    escribir(os.path.join(r2, 'src', 'app.py'), 'import os\n# uno\n# dos\n# tres\n    resultado   =   eval(dato)\n')
    s1 = escribir_json(os.path.join(tmp, 'h1.sarif'), sarif('semgrep', [res('py.eval', 'src/app.py', 2)], [regla('py.eval', puntaje='8.0')]))
    s2 = escribir_json(os.path.join(tmp, 'h2.sarif'), sarif('semgrep', [res('py.eval', 'src/app.py', 5)], [regla('py.eval', puntaje='8.0')]))
    s3 = escribir_json(os.path.join(tmp, 'h3.sarif'), sarif('semgrep', [res('py.eval', 'src/app.py', 1)], [regla('py.eval', puntaje='8.0')]))
    hu = [json_de(correr('--reporte', s, '--repo', r, '--solo', 'sast', '--json')[1]).get('hallazgos', [{}])[0].get('huella')
          for s, r in ((s1, r1), (s2, r2), (s3, r1))]
    caso('la huella no cambia si el codigo se corre unas lineas (misma linea sin espacios)', hu[0] and hu[0] == hu[1], hu)
    caso('la huella cambia si la linea es otra', hu[0] != hu[2], hu)
    s4 = escribir_json(os.path.join(tmp, 'h4.sarif'), sarif('semgrep', [res('py.eval', 'src/app.py', 2, huella='abc123:1')], [regla('py.eval', puntaje='8.0')]))
    h = json_de(correr('--reporte', s4, '--solo', 'sast', '--json')[1]).get('hallazgos', [{}])[0]
    caso('si el SARIF trae primaryLocationLineHash, esa es la huella', h.get('huella') == 'abc123:1', h)

    # --- supresiones en el repositorio: motivo y vencimiento
    rs = os.path.join(tmp, 'repo-sup')
    escribir(os.path.join(rs, 'src', 'a.py'), 'x = 1  # nosec\n'
             'y = eval(z)  # nosec B307 -- motivo: entrada fija de la prueba -- vence: %s\n'
             'w = 2  # nosec B101 -- motivo: assert de prueba heredado -- vence: %s\n' % (FUTURO, PASADO))
    escribir(os.path.join(rs, 'README.md'), 'Se puede usar # nosec en el codigo.\n')
    escribir(os.path.join(rs, 'osv-scanner.toml'), '[[IgnoredVulns]]\nid = "GHSA-aaaa-bbbb-cccc"\nreason = "No se usa la funcion afectada"\n'
             'effectiveUntil = %s\n\n[[IgnoredVulns]]\nid = "GHSA-dddd-eeee-ffff"\nreason = "Sin parche todavia"\n' % FUTURO)
    escribir(os.path.join(rs, '.trivyignore'), '# Aceptado: la imagen base no expone ese puerto\nAVD-DS-0002 exp:%s\n\nAVD-DS-0026\n\n'
             '# Aceptado: la funcion vulnerable no se llama nunca\nCVE-2026-0007 exp:%s\n\nCVE-2026-0008\n' % (FUTURO, FUTURO))
    escribir(os.path.join(rs, '.gitleaksignore'), '# motivo: clave de ejemplo de la documentacion, no es real -- vence: %s\n'
             'abc123:docs/ejemplo.md:generic-api-key:4\n' % FUTURO)
    limpios = ['--reporte', 'sast:' + escribir_json(os.path.join(tmp, 'l-sast.sarif'), sarif('semgrep', [])),
               '--reporte', 'secretos:' + escribir_json(os.path.join(tmp, 'l-sec.sarif'), sarif('gitleaks', [])),
               '--reporte', escribir_json(os.path.join(tmp, 'l-osv.json'), osv([{'package': {'name': 'libx', 'version': '1', 'ecosystem': 'PyPI'}}]))]
    rc, out = correr('--repo', rs, '--json', *limpios)
    d = json_de(out)
    sup = [(x['categoria'], x['regla'], x['archivo'], x['linea']) for x in d.get('hallazgos', [])]
    caso('# nosec sin motivo: HALLAZGO sast en su linea', ('sast', 'supresion-sin-motivo', 'src/a.py', 1) in sup, sup)
    caso('# nosec con motivo y vencimiento vigente: no es hallazgo', not any(x[2] == 'src/a.py' and x[3] == 2 for x in sup), sup)
    caso('# nosec vencido: HALLAZGO', ('sast', 'supresion-vencida', 'src/a.py', 3) in sup, sup)
    caso('osv-scanner.toml sin effectiveUntil: HALLAZGO sca; el que lo tiene, no',
         [x for x in sup if x[2] == 'osv-scanner.toml'] == [('sca', 'supresion-sin-vencimiento', 'osv-scanner.toml', 6)], sup)
    caso('.trivyignore: la CVE sin comentario arriba es HALLAZGO sca; la comentada y con exp: no; las de configuracion son de auditar-iac',
         [x for x in sup if x[2] == '.trivyignore'] == [('sca', 'supresion-sin-motivo', '.trivyignore', 9)], sup)
    caso('.gitleaksignore con motivo y vencimiento: no es hallazgo; un README que nombra nosec, tampoco',
         not any(x[2] in ('.gitleaksignore', 'README.md') for x in sup), sup)
    caso('con supresiones sin motivo el script sale HALLAZGO (1)', rc == 1 and d.get('veredicto') == 'HALLAZGO', out[:200])

    # --- la evidencia es por categoria, no por reporte (F2 3b)
    fusion = sarif('gitleaks', [], exito=None)
    fusion['runs'].append(sarif('semgrep', [])['runs'][0])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'fusion.sarif'), fusion), '--solo', 'sast,secretos', '--json')
    d = json_de(out)
    caso('un SARIF de gitleaks sin evidencia fusionado con uno de Semgrep que si la tiene: secretos SIN DATOS, sast OK',
         rc == 2 and d.get('categorias', {}).get('secretos', {}).get('estado') == 'SIN DATOS'
         and d.get('categorias', {}).get('sast', {}).get('estado') == 'OK', out[:500])

    # --- SARIF con direcciones http(s): sin query y con el alcance (F2 4)
    nmod = None
    try:
        sys.path.insert(0, AQUI)
        from seguridad import normalizar as nmod
    except Exception as e:
        caso('el normalizador se puede importar', False, '%s: %s' % (type(e).__name__, e))
    if nmod is not None:
        web = escribir_json(os.path.join(tmp, 'nuclei-web.sarif'), sarif('nuclei', [
            res('xss', 'https://app.example.com/buscar?token=' + SECRETO, 0, nivel='error'),
            res('xss', 'https://otro.example.net/x?token=' + SECRETO, 0, nivel='error')]))
        r = nmod.leer(web, 'dast', '', 'https://app.example.com')
        archivos = [x['archivo'] for x in r['hallazgos']]
        caso('SARIF: una URI http(s) se guarda sin la query y lo de fuera del alcance no se cuenta',
             archivos == ['https://app.example.com/buscar'] and r['fuera'] == ['https://otro.example.net'], (archivos, r['fuera']))
        caso('SARIF: el token de la query no llega al JSON', SECRETO not in json.dumps(r), json.dumps(r)[:300])
        r = nmod.leer(web, 'dast', '', 'https://tercero.example.org')
        caso('SARIF de prueba dinamica sin ninguna URI en el alcance: sin evidencia (regla del cero)',
             not r['evidencia'] and not r['hallazgos'], r)
        sec = nmod.hallazgo(categoria='secretos', severidad='MEDIA', titulo='x' + chr(27) + '[2J')
        caso('hallazgo(): un secreto MEDIA sube a ALTA y el titulo sale sin caracteres de control',
             sec['severidad'] == 'ALTA' and chr(27) not in sec['titulo'], sec)
        caso('suprimir(): con motivo y sin vencimiento no suprime', nmod.suprimir('falso positivo revisado', '', HOY.isoformat())[0] == 'nuevo')
        caso('suprimir(): con motivo y vencimiento vigente suprime',
             nmod.suprimir('falso positivo revisado', FUTURO, HOY.isoformat())[0] == 'suprimido')
        caso('vence_de(): lee "vence: AAAA-MM-DD" de un texto libre', nmod.vence_de('no aplica -- vence: %s' % FUTURO) == FUTURO)

    # --- varias categorias: HALLAZGO gana a SIN DATOS, y una que no midio no es OK
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'gl-limpio.sarif'), sarif('gitleaks', [])))
    caso('solo un reporte limpio de secretos y las otras categorias sin medir: SIN DATOS (2), no 0',
         rc == 2 and 'no se paso ningun reporte' in out, out[:400])
    rc, out = correr('--reporte', gl)
    caso('HALLAZGO en una categoria y SIN DATOS en otras: sale 1', rc == 1, out[:200])
    rc, out = correr('--reporte', 'sast:' + escribir_json(os.path.join(tmp, 'otra.sarif'), sarif('HerramientaRara', [
        res('r1', 'a.py', 1)], [regla('r1', puntaje='7.0')])), '--solo', 'sast', '--json')
    d = json_de(out)
    caso('categoria:archivo fija la categoria de una herramienta que no se conoce', rc == 1 and d['hallazgos'][0]['categoria'] == 'sast', out[:300])
    rc, out = correr('--reporte', escribir_json(os.path.join(tmp, 'otra2.sarif'), sarif('HerramientaRara', [])), '--solo', 'sast')
    caso('una herramienta que no se conoce, sin categoria: SIN DATOS y lo dice', rc == 2 and 'categoria' in out, out[:300])

    # --- correr de verdad: lo que no esta instalado es SIN DATOS
    rr = os.path.join(tmp, 'repo-real')
    escribir(os.path.join(rr, 'src', 'app.py'), 'print(1)\n')
    escribir(os.path.join(rr, 'requirements.txt'), 'flask==3.0.0\n')
    escribir(os.path.join(rr, 'Dockerfile'), 'FROM python:3.12\n')
    reglas = escribir(os.path.join(tmp, 'reglas', 'r.yaml'), 'rules: []\n')
    rc, out = correr('--repo', rr, '--reglas', reglas, '--salida', os.path.join(tmp, 'salida-vacia'), env=sin_herramientas)
    caso('sin ninguna herramienta instalada: SIN DATOS (2) en las tres categorias, y lo dice',
         rc == 2 and out.count('no esta instalad') >= 4, out[:600])

    # --- el plan: opciones sin red, ninguna opcion que cambie algo
    os.makedirs(os.path.join(rr, '.git'), exist_ok=True)
    cache = os.path.join(tmp, 'osv-cache')
    zipviejo = escribir(os.path.join(cache, 'osv-scanner', 'PyPI', 'all.zip'), 'zip')
    viejo = time.time() - 30 * 86400
    os.utime(zipviejo, (viejo, viejo))
    env_plan = dict(sin_herramientas, OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY=cache)
    rc, out = correr('--repo', rr, '--reglas', reglas, '--base', 'abc1234', '--plan', '--json', env=env_plan)
    d = json_de(out)
    pasos = dict((p.get('herramienta'), p) for p in d.get('plan', []))
    todos = [t for p in d.get('plan', []) for t in p.get('comando', [])]
    caso('--plan: no corre nada y no es OK (2); trivy de configuracion ya no esta (lo hace auditar-iac.py)',
         rc == 2 and set(pasos) == {'semgrep', 'bandit', 'osv-scanner', 'gitleaks'}, sorted(pasos))
    caso('--plan: ninguna opcion de la lista negra (autofix, fix, bajar bases, validar secretos, metricas, config auto)',
         todos and not any(t in NUNCA or t.startswith('--config=auto') for t in todos), [t for t in todos if t in NUNCA])
    c = pasos.get('semgrep', {}).get('comando', [])
    caso('--plan: SAST con reglas locales, sin metricas y con --baseline-commit',
         '--metrics=off' in c and reglas in c and '--baseline-commit' in c and 'abc1234' in c, c)
    c = pasos.get('gitleaks', {}).get('comando', [])
    caso('--plan: secretos con --redact y solo el rango de la Tarea', '--redact' in c and '--log-opts=abc1234..HEAD' in c and 'git' in c, c)
    c = pasos.get('osv-scanner', {}).get('comando', [])
    caso('--plan: dependencias con --offline', '--offline' in c and '--format' in c, c)
    caso('--plan: la base offline de OSV vieja (30 dias) es SIN DATOS, no se corre', 'vieja' in pasos.get('osv-scanner', {}).get('motivo', ''), pasos.get('osv-scanner'))
    os.utime(zipviejo, None)
    d = json_de(correr('--repo', rr, '--reglas', reglas, '--plan', '--json', env=env_plan)[1])
    m = dict((p.get('herramienta'), p) for p in d.get('plan', [])).get('osv-scanner', {}).get('motivo', '')
    caso('--plan: con la base de OSV de hoy no se queja de la base', 'vieja' not in m and 'ausente' not in m, m)
    d = json_de(correr('--repo', rr, '--plan', '--json', env=dict(sin_herramientas, OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY=os.path.join(tmp, 'nada')))[1])
    pasos = dict((p.get('herramienta'), p) for p in d.get('plan', []))
    caso('--plan: sin base de OSV es SIN DATOS (ausente); sin --reglas el SAST de semgrep no corre',
         'ausente' in pasos.get('osv-scanner', {}).get('motivo', '') and 'reglas' in pasos.get('semgrep', {}).get('motivo', ''), pasos)

    # --- correr de verdad con una herramienta falsa: guarda lo crudo, normaliza, no muestra el secreto
    carpeta = falso(tmp, 'gitleaks')
    registro = os.path.join(tmp, 'registro.txt')
    salida = os.path.join(tmp, 'salida')
    env_falso = dict(os.environ, PATH=carpeta, FALSO_REPORTE=gl, FALSO_REGISTRO=registro)
    rc, out = correr('--repo', rr, '--solo', 'secretos', '--salida', salida, env=env_falso)
    guardados = sorted(os.listdir(salida)) if os.path.isdir(salida) else []
    llamado = open(registro).read() if os.path.isfile(registro) else ''
    caso('con gitleaks (falso) instalado: corre, normaliza y da HALLAZGO (1)', rc == 1 and 'HALLAZGO' in out, out[:500])
    caso('lo crudo y el informe normalizado quedan en la carpeta de salida', any(g.endswith('.sarif') for g in guardados)
         and any(g.endswith('informe.json') for g in guardados), guardados)
    args = llamado.split()
    caso('gitleaks se llamo con --redact sobre el historial entero (repo git, sin --base: modo git y sin --log-opts)',
         '--redact' in args and '--no-banner' in args and args[:1] == ['git'] and not any(x.startswith('--log-opts') for x in args), llamado)
    caso('el secreto no aparece en la salida aunque el crudo lo traiga', SECRETO not in out, out[:300])
    rc, out = correr('--repo', rr, '--solo', 'secretos', '--salida', salida, env=dict(env_falso, FALSO_RC='3'))
    caso('si la herramienta sale con error: SIN DATOS (2), aunque haya dejado un reporte', rc == 2, out[:300])
    sin_ev = escribir_json(os.path.join(tmp, 'gl-sin-evidencia.sarif'), sarif('gitleaks', [], exito=None))
    rc, out = correr('--repo', rr, '--solo', 'secretos', '--salida', salida, env=dict(env_falso, FALSO_REPORTE=sin_ev))
    caso('corriendo de verdad, un reporte limpio que no muestra haber analizado algo: SIN DATOS (regla del cero)',
         rc == 2 and 'regla del cero' in out, out[:400])
    for mala in ('-x', '--output=/tmp/x', 'abc;rm', 'a b', 'HEAD~1'):
        rc, out = correr('--repo', rr, '--solo', 'secretos', '--base', mala, '--salida', salida, env=env_falso)
        caso('--base %r no se acepta: SIN DATOS (2) y no corre nada' % mala, rc == 2 and '--base' in out, out[:300])
    rc, out = correr('--reporte', gl, '--solo', 'secretos')
    caso('el siguiente paso nombra la puerta seguridad, no atender-hallazgos (que es del Doctor)',
         'puerta `seguridad`' in out and 'atender-hallazgos' not in out, out[-600:])

    for f in ('escanear-seguridad.py', os.path.join('seguridad', 'normalizar.py'), os.path.join('seguridad', '__init__.py')):
        ruta = os.path.join(AQUI, f)
        datos = open(ruta, 'rb').read() if os.path.isfile(ruta) else b'\xff'
        caso('%s es ASCII puro' % f.replace(os.sep, '/'), all(b < 128 for b in datos))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
