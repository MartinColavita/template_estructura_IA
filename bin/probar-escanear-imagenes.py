#!/usr/bin/env python3
"""Prueba de bin/escanear-imagenes.py sobre reportes plantados de Trivy y de Grype.
Se corre:  python -B bin/probar-escanear-imagenes.py   -> OK o FALLA, con el detalle de cada caso.
No usa la red ni un escaner: lo de --correr se prueba reemplazando las funciones que lo ejecutan."""

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
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'escanear-imagenes.py')
ESPERADOS = []
AHORA = time.time()
HORA = 3600
CLAVES = {'veredicto', 'origen', 'generado', 'categorias', 'hallazgos', 'sin_datos', 'no_mira'}
CLAVES_H = {'herramienta', 'categoria', 'regla', 'titulo', 'cwe', 'cve', 'severidad', 'archivo', 'linea', 'paquete',
            'version', 'arreglo', 'activo', 'huella', 'estado', 'motivo_supresion', 'vence'}
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `img-app` | imagen | prueba | `registro.example/app:1.0` | no | media | N0 | no | | plataforma |\n'
         '| `img-sin-nivel` | imagen | prueba | `registro.example/x:1.0` | no | baja | nada | no | | plataforma |\n'
         '| `web-prueba-1` | servidor | prueba | `lectura-web-prueba-1` | no | media | N1 | no | | operaciones |\n'
         '| `img-guion` | imagen | prueba | `--exit-code=0` | no | baja | N0 | no | | plataforma |\n'
         '| `x/../../../../fuera-img` | imagen | prueba | `registro.example/app:1.0` | no | baja | N0 | no | | plataforma |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:400]) if (detalle and not ok) else ''))


def iso(t, nano=False):
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(t)) + ('.123456789Z' if nano else 'Z')


def escribir(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(contenido if isinstance(contenido, bytes) else
                (contenido if isinstance(contenido, str) else json.dumps(contenido)).encode('utf-8'))
    return ruta


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def como_json(out):
    try:
        return json.loads(out)
    except ValueError:
        return {}


def vul(id_='CVE-2026-0001', sev='CRITICAL', pkg='openssl', ver='3.0.1', fix='3.0.2', titulo='desborde en openssl', **extra):
    d = {'VulnerabilityID': id_, 'PkgName': pkg, 'InstalledVersion': ver, 'FixedVersion': fix, 'Severity': sev,
         'Title': titulo, 'CweIDs': ['CWE-787'], 'Status': 'fixed'}
    d.update(extra)
    return d


def trivy(vulns=(), eosl=False, so=True, os_result=True, libs=(), modificados=(), secretos=(), esquema=2, resultados=True):
    meta = {'ImageID': 'sha256:abc', 'RepoTags': ['registro.example/app:1.0']}
    if so:
        meta['OS'] = {'Family': 'debian', 'Name': '12.5'}
        if eosl:
            meta['OS'] = {'Family': 'debian', 'Name': '9.13', 'EOSL': True}
    res = []
    if os_result and so:
        r = {'Target': 'registro.example/app:1.0 (debian 12.5)', 'Class': 'os-pkgs', 'Type': 'debian'}
        if vulns:
            r['Vulnerabilities'] = list(vulns)
        if modificados:
            r['ExperimentalModifiedFindings'] = list(modificados)
        res.append(r)
    if libs:
        res.append({'Target': 'app/requirements.txt', 'Class': 'lang-pkgs', 'Type': 'pip', 'Vulnerabilities': list(libs)})
    if secretos:
        res.append({'Target': 'app/config.env', 'Class': 'secret', 'Secrets': list(secretos)})
    d = {'SchemaVersion': esquema, 'CreatedAt': iso(AHORA - 60), 'ArtifactName': 'registro.example/app:1.0',
         'ArtifactType': 'container_image', 'Metadata': meta}
    if resultados:
        d['Results'] = res
    return d


def base_trivy(horas=6, version=False):
    meta = {'Version': 2, 'NextUpdate': iso(AHORA - horas * HORA + 6 * HORA, True), 'UpdatedAt': iso(AHORA - horas * HORA, True),
            'DownloadedAt': iso(AHORA - horas * HORA + 600, True)}
    return {'Version': '0.76.2', 'VulnerabilityDB': meta} if version else meta


def gmatch(id_='CVE-2026-0002', sev='High', pkg='libc6', ver='2.31', fix=('2.32',), relacionadas=()):
    return {'vulnerability': {'id': id_, 'dataSource': 'x', 'namespace': 'ubuntu:distro:ubuntu:22.04', 'severity': sev,
                              'fix': {'versions': list(fix), 'state': 'fixed' if fix else 'not-fixed'}},
            'relatedVulnerabilities': [{'id': r} for r in relacionadas],
            'matchDetails': [{'type': 'exact-direct-match'}],
            'artifact': {'id': 'x', 'name': pkg, 'version': ver, 'type': 'deb', 'locations': [{'path': '/usr/lib/' + pkg}], 'purl': ''}}


def grype(matches=(), ignorados=(), eol=False, horas=6, valida=True, sin_db=False, viejo=False):
    db = {'status': {'schemaVersion': 'v6.0.2', 'from': 'x', 'built': iso(AHORA - horas * HORA), 'path': '/x', 'valid': valida},
          'providers': {}}
    if viejo:
        db = {'built': iso(AHORA - horas * HORA), 'schemaVersion': 5, 'location': '/x', 'checksum': 'x', 'error': None}
    d = {'matches': list(matches), 'source': {'type': 'image', 'target': {'userInput': 'registro.example/app:1.0'}},
         'distro': {'name': 'ubuntu', 'version': '22.04'},
         'descriptor': {'name': 'grype', 'version': '0.121.3', 'timestamp': iso(AHORA - 60)}}
    if not sin_db:
        d['descriptor']['db'] = db
    if ignorados:
        d['ignoredMatches'] = list(ignorados)
    if eol:
        d['alertsByPackage'] = [{'package': {'name': 'tar', 'version': '1.29b', 'type': 'deb'},
                                 'alerts': [{'type': 'distro-eol', 'message': 'Package is from end-of-life distro: ubuntu 18.04',
                                             'metadata': {'name': 'ubuntu', 'version': '18.04'}}]}]
    return d


def cargar_modulo():
    spec = importlib.util.spec_from_file_location('escanear_imagenes_en_prueba', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def adentro(mod, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = mod.main(list(args))
        except SystemExit as e:
            rc = e.code
    return rc, buf.getvalue()


def main():
    print('== escanear-imagenes')
    tmp = tempfile.mkdtemp(prefix='probar-img-')

    def arch(nombre, contenido):
        return escribir(os.path.join(tmp, nombre), contenido)

    base = arch('metadata.json', base_trivy())

    # --- Trivy: camino feliz y cada HALLAZGO
    rc, out = correr('--reporte', arch('t-sano.json', trivy(vulns=[vul(sev='LOW')])), '--base', base)
    caso('trivy con una vulnerabilidad baja y la base fresca: OK (0), con lo que NO mira',
         rc == 0 and ' -- OK' in out.splitlines()[0] and 'NO mira' in out, out)
    rc, out = correr('--reporte', arch('t-critica.json', trivy(vulns=[vul(), vul('CVE-2026-0009', 'LOW', 'zlib')])), '--base', base)
    caso('trivy con una critica: HALLAZGO (1), nombra el CVE y el paquete', rc == 1 and 'CVE-2026-0001' in out and 'openssl' in out, out)
    rc, out = correr('--reporte', arch('t-media.json', trivy(vulns=[vul(sev='MEDIUM')])), '--base', base)
    caso('una media con el umbral por defecto (ALTA): OK, pero la cuenta', rc == 0 and '1 por debajo' in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-media.json'), '--base', base, '--umbral', 'MEDIA')
    caso('el umbral va por argumento: con --umbral MEDIA, una media es HALLAZGO', rc == 1, out)
    rc, out = correr('--reporte', arch('t-lib.json', trivy(libs=[vul('GHSA-xxxx-yyyy-zzzz', 'HIGH', 'requests', '2.0', '2.31')])), '--base', base)
    caso('una vulnerabilidad alta en una biblioteca (no del sistema): HALLAZGO', rc == 1 and 'requests' in out, out)

    # --- sistema operativo sin soporte: HALLAZGO, y su conteo SIN DATOS
    rc, out = correr('--reporte', arch('t-eol.json', trivy(eosl=True)), '--base', base, '--json')
    d = como_json(out)
    caso('trivy con el sistema sin soporte y cero vulnerabilidades: HALLAZGO (1), nunca OK',
         rc == 1 and d.get('veredicto') == 'HALLAZGO' and any('soporte' in h['titulo'] for h in d.get('hallazgos', [])), out[:400])
    caso('sistema sin soporte: el conteo de sus vulnerabilidades queda en sin_datos', any('conteo' in s for s in d.get('sin_datos', [])), d.get('sin_datos'))
    rc, out = correr('--reporte', arch('t-sin-os.json', trivy(os_result=False)), '--base', base)
    caso('detecto el sistema pero no analizo sus paquetes: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', arch('t-scratch.json', trivy(so=False, libs=[vul(sev='LOW')])), '--base', base)
    caso('una imagen sin sistema operativo (solo bibliotecas): OK y lo dice', rc == 0 and 'sin sistema operativo' in out, out)

    # --- la base de vulnerabilidades: vieja o ausente es SIN DATOS, nunca "0 vulnerabilidades"
    rc, out = correr('--reporte', arch('t-limpio.json', trivy()))
    caso('trivy sin --base: SIN DATOS (2), aunque no haya ninguna vulnerabilidad', rc == 2 and 'base' in out and 'SIN DATOS' in out, out)
    vieja = arch('vieja.json', base_trivy(horas=240))
    rc, out = correr('--reporte', os.path.join(tmp, 't-limpio.json'), '--base', vieja)
    caso('base de hace 10 dias (tope 120 h): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-limpio.json'), '--base', vieja, '--max-horas-base', '300')
    caso('el tope de la base va por argumento', rc == 0, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', vieja)
    caso('base vieja y una critica: HALLAZGO (1) y la base dice SIN DATOS', rc == 1 and 'SIN DATOS' in out and 'CVE-2026-0001' in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-limpio.json'), '--base', arch('version.json', base_trivy(version=True)))
    caso('la base tambien se lee de la salida de "trivy version --format json"', rc == 0, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-limpio.json'), '--base', arch('base-rota.json', {'Version': 2}))
    caso('una base sin fecha: SIN DATOS (2)', rc == 2, out)
    cero = base_trivy()
    cero['UpdatedAt'] = '0001-01-01T00:00:00Z'
    rc, out = correr('--reporte', os.path.join(tmp, 't-limpio.json'), '--base', arch('base-cero.json', cero))
    caso('una base con la fecha cero de Go: SIN DATOS (2)', rc == 2, out)

    # --- severidad desconocida y supresiones
    rc, out = correr('--reporte', arch('t-unknown.json', trivy(vulns=[vul(sev='UNKNOWN')])), '--base', base, '--json')
    d = como_json(out)
    caso('una vulnerabilidad sin severidad: ALTA hasta priorizar (regla 1 del paquete), HALLAZGO, y el titulo lo dice',
         rc == 1 and any(h['severidad'] == 'ALTA' and 'severidad' in h['titulo'] for h in d.get('hallazgos', [])), out[:400])
    con_motivo = {'Type': 'vulnerability', 'Status': 'ignored', 'Statement': 'no se usa ese modulo', 'Source': '.trivyignore.yaml',
                  'Finding': vul('CVE-2026-0003', 'CRITICAL', 'curl')}
    rc, out = correr('--reporte', arch('t-supr.json', trivy(vulns=[vul(sev='LOW')], modificados=[con_motivo])), '--base', base, '--json')
    d = como_json(out)
    sup = [h for h in d.get('hallazgos', []) if h.get('cve') == 'CVE-2026-0003']
    caso('una critica "suprimida" con motivo pero SIN vencimiento no suprime (regla 5): cuenta y da HALLAZGO',
         rc == 1 and sup and sup[0]['estado'] == 'nuevo' and d.get('veredicto') == 'HALLAZGO', out[:400])
    con_vence = dict(con_motivo, Statement='no se usa ese modulo -- vence: %s' % time.strftime('%Y-%m-%d', time.gmtime(AHORA + 30 * 86400)))
    rc, out = correr('--reporte', arch('t-supr-v.json', trivy(vulns=[vul(sev='LOW')], modificados=[con_vence])), '--base', base, '--json')
    d = como_json(out)
    sup = [h for h in d.get('hallazgos', []) if h.get('cve') == 'CVE-2026-0003']
    caso('una critica suprimida con motivo y vencimiento vigente: no cuenta (OK) y queda suprimida con su motivo y su vence',
         rc == 0 and sup and sup[0]['estado'] == 'suprimido' and 'no se usa' in sup[0]['motivo_supresion'] and sup[0]['vence'], out[:400])
    sin_motivo = dict(con_motivo, Statement='')
    rc, out = correr('--reporte', arch('t-supr2.json', trivy(modificados=[sin_motivo])), '--base', base)
    caso('una supresion sin motivo no es una supresion: cuenta y da HALLAZGO', rc == 1 and 'CVE-2026-0003' in out, out)

    # --- secretos en las capas: regla, archivo y linea; nunca el valor
    secreto = {'RuleID': 'aws-access-key-id', 'Category': 'AWS', 'Severity': 'CRITICAL', 'Title': 'AWS Access Key ID',
               'StartLine': 3, 'EndLine': 3, 'Code': {'Lines': [{'Content': 'CLAVE=AKIAVALORREALSECRETO1'}]}, 'Match': 'CLAVE=AKIAVALORREALSECRETO1'}
    rc, out = correr('--reporte', arch('t-secreto.json', trivy(secretos=[secreto])), '--base', base, '--json')
    d = como_json(out)
    caso('un secreto en una capa: HALLAZGO con regla, archivo y linea, y el valor NO aparece',
         rc == 1 and 'AKIAVALORREALSECRETO1' not in out and any(h['categoria'] == 'secretos' and h['linea'] == 3 for h in d.get('hallazgos', [])), out[:400])
    rc, out = correr('--reporte', arch('t-secreto-media.json', trivy(vulns=[vul(sev='LOW')], secretos=[dict(secreto, Severity='MEDIUM')])),
                     '--base', base, '--json')
    d = como_json(out)
    caso('un secreto que Trivy marca MEDIUM sube a ALTA y frena: HALLAZGO (1), veredicto y categoria secretos HALLAZGO',
         rc == 1 and d.get('veredicto') == 'HALLAZGO' and d.get('categorias', {}).get('secretos', {}).get('estado') == 'HALLAZGO'
         and any(h['categoria'] == 'secretos' and h['severidad'] == 'ALTA' for h in d.get('hallazgos', [])), out[:500])

    # --- un solo esquema: el veredicto nunca dice OK si una categoria dice HALLAZGO
    incoherentes = []
    for nombre in ('t-sano.json', 't-critica.json', 't-media.json', 't-eol.json', 't-secreto.json', 't-secreto-media.json', 't-supr.json'):
        d = como_json(correr('--reporte', os.path.join(tmp, nombre), '--base', base, '--json')[1])
        estados = [c.get('estado') for c in d.get('categorias', {}).values()]
        if d.get('veredicto') == 'OK' and 'HALLAZGO' in estados or not estados:
            incoherentes.append((nombre, d.get('veredicto'), estados))
    caso('en ningun reporte el veredicto dice OK con una categoria en HALLAZGO', not incoherentes, incoherentes)
    rc, out = correr('--reporte', os.path.join(tmp, 't-media.json'), '--base', base, '--umbral', 'CRITICA')
    caso('--umbral no puede aflojar la regla del paquete (CRITICA y ALTA frenan): --umbral CRITICA no se acepta', rc == 2, out[:300])

    # --- la edad de la base sale del CreatedAt del reporte, y tiene que haber analizado paquetes
    sin_fecha = trivy(vulns=[vul(sev='LOW')])
    del sin_fecha['CreatedAt']
    rc, out = correr('--reporte', arch('t-sin-createdat.json', sin_fecha), '--base', base)
    caso('un reporte de Trivy sin CreatedAt: SIN DATOS (2), no se sabe con que base corrio', rc == 2 and 'CreatedAt' in out, out)
    viejo = trivy(vulns=[vul(sev='LOW')])
    viejo['CreatedAt'] = iso(AHORA - 240 * HORA)
    rc, out = correr('--reporte', arch('t-viejo.json', viejo), '--base', base)
    caso('un reporte de hace 10 dias con una base de hoy pasada por argumento: SIN DATOS (2), esa base no es la que uso',
         rc == 2 and 'SIN DATOS' in out, out)
    viejo_ok = trivy(vulns=[vul(sev='LOW')])
    viejo_ok['CreatedAt'] = iso(AHORA - 100 * HORA)
    rc, out = correr('--reporte', arch('t-base-al-escanear.json', viejo_ok), '--base', vieja, '--max-horas-base', '200')
    caso('la edad de la base se mide al momento del escaneo (CreatedAt - UpdatedAt), no contra el reloj de hoy',
         rc == 0 and 'de hace 140 h' in out, out)
    rc, out = correr('--reporte', arch('t-solo-secretos.json', trivy(so=False, secretos=[secreto])), '--base', base, '--json')
    d = como_json(out)
    caso('un reporte sin ningun resultado os-pkgs ni lang-pkgs: la imagen queda SIN DATOS (no analizo paquetes)',
         d.get('categorias', {}).get('imagen', {}).get('estado') == 'SIN DATOS' and 'paquetes' in json.dumps(d.get('sin_datos')), out[:500])
    rc, out = correr('--reporte', os.path.join(tmp, 't-sano.json'), '--base', arch('version-0694.json', dict(base_trivy(version=True), Version='0.69.4')))
    caso('la base dice que Trivy es la 0.69.4 (incidente de marzo de 2026): SIN DATOS (2) y lo dice', rc == 2 and '0.69.4' in out, out)

    # --- Grype
    rc, out = correr('--reporte', arch('g-sano.json', grype([gmatch(sev='Low')])))
    caso('grype con una baja y la base fresca: OK (0)', rc == 0 and ' -- OK' in out.splitlines()[0], out)
    rc, out = correr('--reporte', arch('g-alta.json', grype([gmatch('GHSA-aaaa-bbbb-cccc', relacionadas=('CVE-2026-0004',))])), '--json')
    d = como_json(out)
    caso('grype con una alta: HALLAZGO (1) y toma el CVE de las relacionadas',
         rc == 1 and any(h['cve'] == 'CVE-2026-0004' and h['regla'] == 'GHSA-aaaa-bbbb-cccc' for h in d.get('hallazgos', [])), out[:400])
    rc, out = correr('--reporte', arch('g-eol.json', grype(eol=True)))
    caso('grype con aviso de distro sin soporte: HALLAZGO (1), aunque no haya matches', rc == 1 and 'soporte' in out, out)
    rc, out = correr('--reporte', arch('g-vieja.json', grype(horas=200)))
    caso('grype con la base de hace 200 h: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', arch('g-invalida.json', grype(valida=False)))
    caso('grype con la base marcada invalida: SIN DATOS (2)', rc == 2, out)
    rc, out = correr('--reporte', arch('g-sin-db.json', grype(sin_db=True)))
    caso('grype sin datos de la base en el reporte: SIN DATOS (2)', rc == 2, out)
    rc, out = correr('--reporte', arch('g-viejo.json', grype(viejo=True)))
    caso('grype con el descriptor de base del formato anterior: se lee igual', rc == 0, out)
    ign = dict(gmatch('CVE-2026-0005', 'Critical'), appliedIgnoreRules=[{'vulnerability': 'CVE-2026-0005', 'reason': 'falso positivo revisado', 'namespace': ''}])
    rc, out = correr('--reporte', arch('g-ign.json', grype(ignorados=[ign])))
    caso('grype con una critica ignorada con motivo pero sin vencimiento: no suprime (regla 5), HALLAZGO', rc == 1, out)
    vence = time.strftime('%Y-%m-%d', time.gmtime(AHORA + 30 * 86400))
    ign_v = dict(gmatch('CVE-2026-0005', 'Critical'), appliedIgnoreRules=[{'vulnerability': 'CVE-2026-0005', 'namespace': '',
                                                                          'reason': 'falso positivo revisado -- vence: ' + vence}])
    rc, out = correr('--reporte', arch('g-ign-v.json', grype(ignorados=[ign_v])))
    caso('grype con una critica ignorada con motivo y vencimiento vigente: OK', rc == 0, out)
    ign_x = dict(gmatch('CVE-2026-0005', 'Critical'), appliedIgnoreRules=[{'vulnerability': 'CVE-2026-0005', 'namespace': '',
                                                                          'reason': 'falso positivo revisado -- vence: 2020-01-01'}])
    rc, out = correr('--reporte', arch('g-ign-x.json', grype(ignorados=[ign_x])))
    caso('grype con una critica ignorada con la supresion vencida: HALLAZGO', rc == 1, out)
    ign2 = dict(gmatch('CVE-2026-0005', 'Critical'), appliedIgnoreRules=[{'vulnerability': 'CVE-2026-0005', 'namespace': ''}])
    rc, out = correr('--reporte', arch('g-ign2.json', grype(ignorados=[ign2])))
    caso('grype con una critica ignorada sin motivo: HALLAZGO', rc == 1, out)
    rc, out = correr('--reporte', arch('g-neg.json', grype([gmatch(sev='Negligible')])))
    caso('una Negligible de grype: no es severidad desconocida, OK', rc == 0, out)

    # --- cada SIN DATOS del reporte
    rc, out = correr('--reporte', os.path.join(tmp, 'no-existe.json'))
    caso('reporte ausente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', arch('vacio.json', ''))
    caso('reporte vacio: SIN DATOS (2), nunca OK', rc == 2, out)
    rc, out = correr('--reporte', arch('binario.json', bytes(bytearray(range(256)))))
    caso('reporte ilegible: SIN DATOS (2)', rc == 2, out)
    rc, out = correr('--reporte', arch('otro.json', {'foo': 1}))
    caso('un JSON que no es de Trivy ni de Grype: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', arch('t-esquema.json', trivy(esquema=3)), '--base', base)
    caso('un esquema de Trivy que este script no conoce: SIN DATOS (2)', rc == 2, out)
    rc, out = correr('--reporte', arch('t-sin-res.json', trivy(resultados=False)), '--base', base)
    caso('un reporte de Trivy sin resultados: no analizo nada, SIN DATOS (2)', rc == 2, out)
    rc, out = correr()
    caso('sin --reporte ni --correr: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)

    # --- lo que viene del escaner es dato: sin caracteres de control
    rc, out = correr('--reporte', arch('t-escape.json', trivy(vulns=[vul(titulo='malo' + chr(27) + '[2J' + chr(7))])), '--base', base)
    caso('caracteres de control en un titulo: no llegan a la salida', rc == 1 and chr(27) not in out and chr(7) not in out, repr(out[:300]))

    # --- --json: el esquema comun de hallazgos
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--json')
    d = como_json(out)
    h = (d.get('hallazgos') or [{}])[0]
    caso('--json: las claves del esquema comun, origen escanear-imagenes y categoria imagen',
         CLAVES <= set(d) and d['origen'] == 'escanear-imagenes' and d['veredicto'] == 'HALLAZGO' and 'imagen' in d['categorias'], out[:400])
    caso('--json: cada hallazgo con exactamente las claves del esquema', bool(d.get('hallazgos')) and all(set(x) == CLAVES_H for x in d['hallazgos']), h)
    caso('--json: la severidad normalizada, el arreglo y una huella', h.get('severidad') == 'CRITICA' and h.get('arreglo') == '3.0.2'
         and len(h.get('huella', '')) >= 12 and h.get('estado') == 'nuevo' and h.get('linea') == 0, h)
    caso('--json es ASCII', all(ord(c) < 128 for c in out))
    rc, out = correr('--reporte', os.path.join(tmp, 'vacio.json'), '--json')
    d = como_json(out)
    caso('--json con un reporte ilegible: veredicto SIN DATOS y el motivo en sin_datos', rc == 2 and d.get('veredicto') == 'SIN DATOS' and d.get('sin_datos'), out[:300])

    # --- --imagen: pasa por el inventario aunque solo se lea un reporte
    repo = os.path.join(tmp, 'repo')
    escribir(os.path.join(repo, 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--imagen', 'img-app', '--raiz', repo, '--json')
    d = como_json(out)
    caso('con --imagen autorizada: cada hallazgo lleva el alias en activo', rc == 1 and all(x['activo'] == 'img-app' for x in d.get('hallazgos', [])), out[:300])
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--imagen', 'img-otra', '--raiz', repo)
    caso('--imagen que no esta en el inventario: FRENA (1) y no informa nada', rc == 1 and 'FRENA' in out and 'CVE-2026-0001' not in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--imagen', 'web-prueba-1', '--raiz', repo)
    caso('--imagen con un alias que es un servidor: FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--imagen', 'img-app', '--raiz', os.path.join(tmp, 'nada'))
    caso('--imagen sin inventario: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--reporte', os.path.join(tmp, 't-critica.json'), '--base', base, '--imagen', 'img-otra', '--raiz', repo, '--json')
    d = como_json(out)
    caso('--json con FRENA: veredicto FRENA, sin hallazgos y con el motivo', rc == 1 and d.get('veredicto') == 'FRENA' and d.get('hallazgos') == [] and d.get('motivo'), out[:300])

    # --- --correr: la funcion que ejecuta se reemplaza (no hay escaner ni red)
    try:
        mod = cargar_modulo()
    except Exception as e:
        mod = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    if mod is not None:
        llamadas = []

        def falso(respuestas, instalada=True):
            def ejecutar(orden, entorno=None):
                llamadas.append((list(orden), entorno))
                return respuestas[len(llamadas) - 1] if len(llamadas) <= len(respuestas) else (0, '', '')
            mod.ejecutar = ejecutar
            mod.instalada = lambda nombre: ('/usr/bin/' + nombre) if instalada else None

        falso([], instalada=False)
        rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'trivy', '--raiz', repo)
        caso('--correr con el escaner sin instalar: SIN DATOS (2) y no ejecuta nada', rc == 2 and 'SIN DATOS' in out and llamadas == [], out)
        falso([])
        rc, out = adentro(mod, '--correr', 'trivy', '--raiz', repo)
        caso('--correr sin --imagen: SIN DATOS (2) y no ejecuta nada', rc == 2 and llamadas == [], out)
        rc, out = adentro(mod, '--imagen', 'img-otra', '--correr', 'trivy', '--raiz', repo)
        caso('--correr con un alias no autorizado: FRENA (1) y no ejecuta nada', rc == 1 and llamadas == [], out)
        rc, out = adentro(mod, '--imagen', 'img-sin-nivel', '--correr', 'grype', '--raiz', repo)
        caso('--correr con un alias sin nivel para la IA: FRENA (1) y no ejecuta nada', rc == 1 and llamadas == [], out)
        rc, out = adentro(mod, '--imagen', 'img-guion', '--correr', 'trivy', '--raiz', repo)
        caso('--correr con un Destino que empieza con guion: SIN DATOS (2) y no ejecuta nada', rc == 2 and llamadas == [], out)
        falso([(0, json.dumps(base_trivy(version=True)), ''), (0, json.dumps(trivy(vulns=[vul(sev='LOW')])), '')])
        rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'trivy', '--raiz', repo)
        ordenes = [o for o, _ in llamadas]
        caso('--correr trivy: lee la base local, escanea el Destino del inventario y da OK',
             rc == 0 and len(ordenes) == 2 and ordenes[0][1] == 'version' and ordenes[1][1] == 'image'
             and ordenes[1][-1] == 'registro.example/app:1.0', (ordenes, out))
        caso('--correr trivy: no baja la base ni usa opciones que cambien el codigo de salida',
             len(ordenes) == 2 and '--skip-db-update' in ordenes[1] and not any(p in o for o in ordenes for p in ('--exit-code', '--exit-on-eol', '--server')), ordenes)
        orden = ordenes[1] if len(ordenes) == 2 else []
        caso('--correr trivy: sin telemetria ni aviso de version, y la imagen solo de la maquina (--image-src sin remote)',
             '--disable-telemetry' in orden and '--skip-version-check' in orden and '--image-src' in orden
             and orden[orden.index('--image-src') + 1] == 'docker,containerd,podman', orden)
        guardados = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(repo, 'borrador')) for f in fs]
        caso('--correr deja el reporte crudo en borrador/seguridad/ y dice donde',
             any(os.sep + os.path.join('borrador', 'seguridad') + os.sep in g for g in guardados) and 'borrador' in out, (guardados, out))
        crudo = [g for g in guardados if 'trivy' in os.path.basename(g) and 'base' not in os.path.basename(g)]
        bases = [g for g in guardados if 'base' in os.path.basename(g)]
        if crudo and bases:
            rc2, out2 = correr('--reporte', crudo[0], '--base', bases[0])
            caso('lo guardado se vuelve a leer con --reporte y --base (lo usa quien verifica)', rc2 == 0, out2)
        else:
            caso('lo guardado se vuelve a leer con --reporte y --base (lo usa quien verifica)', False, guardados)
        del llamadas[:]
        falso([(0, json.dumps(dict(base_trivy(version=True), Version='0.69.4')), ''), (0, json.dumps(trivy()), '')])
        rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'trivy', '--raiz', repo)
        caso('--correr con Trivy 0.69.4 instalado (incidente de marzo de 2026): SIN DATOS (2) y no escanea',
             rc == 2 and '0.69.4' in out and len(llamadas) == 1, ([o for o, _ in llamadas], out))
        del llamadas[:]
        falso([(0, json.dumps(base_trivy(version=True)), ''), (0, json.dumps(trivy(vulns=[vul(sev='LOW')])), '')])
        rc, out = adentro(mod, '--imagen', 'x/../../../../fuera-img', '--correr', 'trivy', '--raiz', repo)
        fuera = [os.path.join(r, f) for r, _, fs in os.walk(tmp) for f in fs if 'fuera-img' in os.path.join(r, f)]
        caso('un alias con / y .. se sanea antes de usarlo como carpeta: lo crudo queda adentro de borrador/seguridad/',
             rc == 0 and fuera and all(os.path.realpath(f).startswith(os.path.realpath(os.path.join(repo, 'borrador', 'seguridad')) + os.sep)
                                       for f in fuera), (fuera, out))
        del llamadas[:]
        falso([(0, '[{"Id": "sha256:abc"}]', ''), (0, json.dumps(grype([gmatch(sev='Critical')])), '')])
        rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'grype', '--raiz', repo)
        inspect = llamadas[0][0] if llamadas else []
        orden, entorno = llamadas[1] if len(llamadas) > 1 else ([], None)
        caso('--correr grype: mira que la imagen este en la maquina y escanea con el esquema docker: (nunca del registro)',
             inspect[:3] == ['docker', 'image', 'inspect'] and orden[:2] == ['grype', 'docker:registro.example/app:1.0'], [o for o, _ in llamadas])
        caso('--correr grype: una sola corrida del escaner, salida json, sin --fail-on, y sin que actualice la base',
             rc == 1 and len(llamadas) == 2 and 'json' in orden
             and '--fail-on' not in orden and '-f' not in orden and (entorno or {}).get('GRYPE_DB_AUTO_UPDATE') == 'false', ([o for o, _ in llamadas], out))
        del llamadas[:]
        falso([(1, '', 'Error: No such image')])
        rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'grype', '--raiz', repo)
        caso('--correr grype con la imagen que no esta en la maquina: SIN DATOS (2) y no la baja (no corre grype)',
             rc == 2 and 'maquina' in out and len(llamadas) == 1, ([o for o, _ in llamadas], out))
        for respuesta, que in (((1, 'error: no se pudo bajar la imagen', ''), 'el escaner falla y no devuelve JSON'),
                               ((None, '', 'no termino'), 'el escaner no termina'),
                               ((0, '', ''), 'el escaner no devuelve nada')):
            del llamadas[:]
            falso([(0, '[{}]', ''), respuesta])
            rc, out = adentro(mod, '--imagen', 'img-app', '--correr', 'grype', '--raiz', repo)
            caso('--correr cuando %s: SIN DATOS (2), nunca OK' % que, rc == 2 and 'SIN DATOS' in out, out)
        for herramienta, mala in (('trivy', ['trivy', 'image', '--image-src', 'docker,remote', 'x']), ('grype', ['grype', 'registry:x', '-o', 'json'])):
            try:
                mod.revisar_orden(mala)
                frenada = False
            except ValueError:
                frenada = True
            caso('la lista negra frena %s si la imagen podria venir del registro' % herramienta, frenada)
        for herramienta, mala in (('trivy', ['trivy', 'image', '--exit-code', '1', 'x']), ('grype', ['grype', 'docker:x', '--fail-on', 'high'])):
            try:
                mod.revisar_orden(mala)
                frenada = False
            except ValueError:
                frenada = True
            caso('la lista negra frena %s con una opcion que hace depender el codigo de salida de los hallazgos' % herramienta, frenada)

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('escanear-imagenes.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
