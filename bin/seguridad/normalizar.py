"""El normalizador: de SARIF 2.1.0 y de los reportes nativos al esquema comun de hallazgos. SOLO LECTURA.

Lee: SARIF 2.1.0 (Semgrep, Opengrep, Bandit, CodeQL, OSV-Scanner, Gitleaks, Trivy, Nuclei y cualquier otro, con
--reporte <categoria>:<archivo> si no se lo reconoce), y los nativos de OSV-Scanner (JSON), pip-audit (JSON),
npm audit (JSON, auditReportVersion 2), ZAP (JSON tradicional, -J), Nuclei (JSONL) y TruffleHog (JSONL).
El esquema y las reglas estan en __init__.py. No baja nada, no ejecuta nada y nunca copia el valor de un secreto,
un fragmento de codigo, un pedido o una respuesta.
"""

import datetime
import hashlib
import json
import os
import re

OK, HALLAZGO, SIN_DATOS, FRENA = 'OK', 'HALLAZGO', 'SIN DATOS', 'FRENA'
CODIGO = {OK: 0, HALLAZGO: 1, SIN_DATOS: 2, FRENA: 1}
CATEGORIAS = ('sast', 'sca', 'secretos', 'config', 'imagen', 'host', 'dast')
SEVERIDADES = ('CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO')
CLAVES = ('herramienta', 'categoria', 'regla', 'titulo', 'cwe', 'cve', 'severidad', 'archivo', 'linea', 'paquete',
          'version', 'arreglo', 'activo', 'huella', 'estado', 'motivo_supresion', 'vence')
# (lo que aparece en el nombre de la herramienta, nombre canonico, categoria por defecto). El orden importa.
HERRAMIENTAS = (('opengrep', 'opengrep', 'sast'), ('semgrep', 'semgrep', 'sast'), ('bandit', 'bandit', 'sast'),
                ('codeql', 'codeql', 'sast'), ('osv-scanner', 'osv-scanner', 'sca'), ('osv', 'osv-scanner', 'sca'),
                ('pip-audit', 'pip-audit', 'sca'), ('npm', 'npm-audit', 'sca'), ('gitleaks', 'gitleaks', 'secretos'),
                ('betterleaks', 'betterleaks', 'secretos'), ('trufflehog', 'trufflehog', 'secretos'),
                ('trivy', 'trivy', 'config'), ('zap', 'zap', 'dast'), ('nuclei', 'nuclei', 'dast'))
TEXTO_SEV = {'critical': 'CRITICA', 'critica': 'CRITICA', 'high': 'ALTA', 'alta': 'ALTA', 'medium': 'MEDIA',
             'moderate': 'MEDIA', 'media': 'MEDIA', 'low': 'BAJA', 'baja': 'BAJA', 'info': 'INFO',
             'informational': 'INFO', 'informativa': 'INFO'}
NIVEL_SARIF = {'error': 'ALTA', 'warning': 'MEDIA', 'note': 'BAJA', 'none': 'INFO'}
RIESGO_ZAP = {'3': 'ALTA', '2': 'MEDIA', '1': 'BAJA', '0': 'INFO'}
SIN_SEVERIDAD = ' (la herramienta no informa la severidad: se toma ALTA hasta priorizar)'
CVE = re.compile(r'(?i)\bCVE-\d{4}-\d{4,}\b')
CWE = re.compile(r'(?i)\bcwe[-_/: ]*(\d+)')
FECHA = re.compile(r'(\d{4}-\d{2}-\d{2})')
URL = re.compile(r'^([A-Za-z][A-Za-z0-9+.-]*)://([^/?#]*)([^?#]*)')
BOM = chr(0xFEFF)
BASURA = {'.git', 'node_modules', 'target', 'build', 'out', 'dist', '.gradle', '.mvn', 'coverage', '.next', '.nuxt',
          '__pycache__', 'vendor', '.venv', 'venv', 'generated', 'bin', 'obj', '.tox'}
CODIGO_EXT = ('.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.java', '.kt', '.kts', '.go', '.cs', '.rb', '.php',
              '.scala', '.swift', '.c', '.cc', '.cpp', '.h', '.rs', '.vue', '.svelte')
FUENTE_EXT = CODIGO_EXT + ('.yml', '.yaml', '.json', '.toml', '.ini', '.cfg', '.conf', '.properties', '.env', '.xml',
                           '.sh', '.ps1', '.sql', '.tf', '.gradle')
# Un comentario que suprime un hallazgo en el codigo, y lo que viene despues (rule ids, motivo, vencimiento).
MARCA = re.compile(r'(?i)(?:#|//|/\*|<!--|--|;)[^\n]*?(?<![\w:-])(nosec|nosemgrep|nosem|gitleaks:allow)(?![\w-])(.*)$')
VENCE = re.compile(r'(?i)\b(?:vence|exp|expires|effectiveUntil)\s*[:=]\s*"?(\d{4}-\d{2}-\d{2})')
CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f]')
ES_URL = re.compile(r'(?i)^\s*https?://')


class Formato(Exception):
    """El reporte se pudo leer, pero no es lo que dice ser o la herramienta dice que fallo."""


# ------------------------------------------------------------------------------------------- piezas sueltas

def ahora():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def _texto(v, n=160):
    """Lo que viene de un reporte es dato: sin caracteres de control, en una linea y acotado."""
    return re.sub(r'\s+', ' ', CONTROL.sub(' ', str(v if v is not None else ''))).strip()[:n]


def _entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _fecha(v):
    m = FECHA.search(str(v or ''))
    return m.group(1) if m else ''


def _lista(v):
    return ' '.join(str(x) for x in v) if isinstance(v, (list, tuple)) else str(v or '')


def _primero(rx, textos):
    for t in textos:
        m = rx.search(str(t or ''))
        if m:
            return m.group(0).upper()
    return ''


def _cwe(textos):
    for t in textos:
        m = CWE.search(str(t or ''))
        if m and int(m.group(1)) > 0:
            return 'CWE-%d' % int(m.group(1))
    return ''


def _campo(texto, nombre):
    m = re.search(r'(?im)^\s*%s:\s*(.+?)\s*$' % re.escape(nombre), texto)
    return _texto(m.group(1), 80) if m else ''


def de_puntaje(v):
    """Severidad por puntaje CVSS (convencion security-severity). 0, vacio o ilegible -> '' (no informa)."""
    try:
        x = float(str(v).replace(',', '.'))
    except (TypeError, ValueError):
        return ''
    return 'CRITICA' if x >= 9.0 else 'ALTA' if x >= 7.0 else 'MEDIA' if x >= 4.0 else 'BAJA' if x >= 0.1 else ''


def de_texto(v):
    return TEXTO_SEV.get(str(v or '').strip().lower(), '')


def de_nivel(v):
    return NIVEL_SARIF.get(str(v or '').strip().lower(), '')


def herramienta_de(nombre):
    """(nombre canonico, categoria por defecto). Una herramienta que no se conoce no tiene categoria."""
    bajo = (nombre or '').lower()
    for clave, canon, cat in HERRAMIENTAS:
        if clave in bajo:
            return canon, cat
    return re.sub(r'[^a-z0-9._-]+', '-', bajo).strip('-') or 'desconocida', ''


def _desescapar(u):
    return re.sub(r'%([0-9A-Fa-f]{2})', lambda m: chr(int(m.group(1), 16)), u)


def ruta_de(uri, repo=''):
    """La ruta de un archivo, relativa al repositorio si cae adentro, con barras /."""
    u = _desescapar(str(uri or '').strip())
    if u.lower().startswith('file://'):
        u = u[7:]
        if re.match(r'^/[A-Za-z]:[/\\]', u):
            u = u[1:]
    u = u.replace('\\', '/')
    if repo and (u.startswith('/') or re.match(r'^[A-Za-z]:/', u)):
        raiz = os.path.abspath(repo).replace('\\', '/').rstrip('/')
        absoluta = os.path.abspath(u).replace('\\', '/')
        if absoluta.lower().startswith(raiz.lower() + '/'):
            u = absoluta[len(raiz) + 1:]
    while u.startswith('./'):
        u = u[2:]
    return u


def origen(url):
    """esquema://servidor[:puerto] en minusculas, sin el puerto por defecto; '' si no es una URL."""
    m = URL.match(str(url or '').strip())
    if not m:
        return ''
    esquema, servidor = m.group(1).lower(), m.group(2).lower()
    servidor = servidor.rsplit('@', 1)[-1]
    if (esquema, servidor.rsplit(':', 1)[-1]) in (('https', '443'), ('http', '80')):
        servidor = servidor.rsplit(':', 1)[0]
    return '%s://%s' % (esquema, servidor)


def sin_query(url):
    """La direccion sin query ni fragmento (pueden llevar un token o un dato de una persona) ni usuario."""
    m = URL.match(str(url or '').strip())
    if not m:
        return _texto(str(url or '').split('?')[0].split('#')[0], 200)
    return '%s://%s%s' % (m.group(1).lower(), m.group(2).rsplit('@', 1)[-1], m.group(3))


def dentro(url, alcance):
    return bool(alcance) and origen(url) == alcance


def _linea_de(repo, archivo, linea):
    if not (repo and archivo and linea > 0):
        return ''
    ruta = archivo if os.path.isabs(archivo) else os.path.join(repo, archivo)
    try:
        if os.path.getsize(ruta) > 5000000:
            return ''
        with open(ruta, 'rb') as h:
            for i, texto in enumerate(h, 1):
                if i == linea:
                    return texto.decode('utf-8', 'replace')
    except OSError:
        return ''
    return ''


def huella(herramienta, regla, archivo, linea=0, repo='', categoria='', paquete=''):
    """Lo que identifica un hallazgo aunque el codigo se corra unas lineas. En secretos nunca se lee la linea."""
    if paquete:
        clave = paquete
    else:
        contenido = '' if categoria == 'secretos' else _linea_de(repo, archivo, linea)
        clave = re.sub(r'\s+', '', contenido) or str(linea)
    base = '|'.join((herramienta, regla, archivo, clave))
    return hashlib.sha256(base.encode('utf-8', 'replace')).hexdigest()[:16]


def hallazgo(**kw):
    """Un hallazgo con todas las claves del esquema; lo que no aplica, vacio."""
    h = dict((k, 0 if k == 'linea' else '') for k in CLAVES)
    h['estado'] = 'nuevo'
    for k, v in kw.items():
        if k in h:
            h[k] = v
    h['linea'] = _entero(h['linea'])
    for k in CLAVES:
        if k not in ('linea', 'huella'):
            h[k] = _texto(h[k], 200 if k in ('archivo', 'motivo_supresion') else 160)
    if h['severidad'] not in SEVERIDADES:
        h['severidad'] = 'ALTA'
    if h['categoria'] == 'secretos' and SEVERIDADES.index(h['severidad']) > 1:
        h['severidad'] = 'ALTA'
    return h


def bloqueante(h):
    return h.get('estado') == 'nuevo' and h.get('severidad') in ('CRITICA', 'ALTA')


def vence_de(texto):
    """El vencimiento escrito en un texto libre (vence: AAAA-MM-DD, exp:, expires=, effectiveUntil=), o ''."""
    m = VENCE.search(str(texto or ''))
    return m.group(1) if m else ''


def suprimir(motivo, vence, hoy):
    """(estado, motivo, vence) de una supresion (regla 5): vale solo con motivo y con vencimiento sin vencer."""
    motivo, vence = _texto(motivo, 200), _fecha(vence)
    if motivo and vence and vence >= hoy:
        return 'suprimido', motivo, vence
    return 'nuevo', motivo, vence


# ------------------------------------------------------------------------------------------- un reporte

def leer(ruta, categoria='', repo='', alcance='', hoy=None):
    """Lee un reporte. Devuelve {herramienta, hallazgos, evidencia, error, cubre, fuera}.

    error no vacio -> no se pudo leer (SIN DATOS). evidencia -> las categorias en las que el reporte muestra que
    analizo algo, POR CATEGORIA (sin eso, una categoria sin hallazgos es SIN DATOS: regla del cero; un SARIF que
    junta dos corridas no le presta la evidencia de una a la otra). cubre -> las categorias que el reporte mide.
    fuera -> los origenes fuera del alcance (direcciones http/https), que no se cuentan como hallazgos."""
    hoy = (hoy or datetime.date.today()).isoformat()
    r = {'herramienta': '', 'hallazgos': [], 'evidencia': [], 'error': '', 'cubre': [], 'fuera': []}
    nombre = os.path.basename(ruta)
    try:
        with open(ruta, 'rb') as h:
            crudo = h.read()
    except OSError as e:
        r['error'] = 'no se pudo leer %s (%s)' % (nombre, e.strerror or type(e).__name__)
        return r
    texto = crudo.decode('utf-8', 'replace').lstrip(BOM).strip()
    if not texto:
        r['error'] = '%s esta vacio' % nombre
        return r
    datos, filas = None, None
    try:
        datos = json.loads(texto)
    except ValueError:
        try:
            filas = [json.loads(x) for x in texto.splitlines() if x.strip()]
        except ValueError:
            r['error'] = '%s no es JSON ni JSONL: no se pudo leer' % nombre
            return r
    if isinstance(datos, dict) and ('template-id' in datos or 'SourceMetadata' in datos):
        datos, filas = None, [datos]
    try:
        if isinstance(datos, dict) and 'runs' in datos:
            _sarif(datos, r, categoria, repo, hoy, alcance)
        elif isinstance(datos, dict) and isinstance(datos.get('results'), list):
            _osv(datos, r, categoria, repo)
        elif isinstance(datos, dict) and isinstance(datos.get('dependencies'), list):
            _pip_audit(datos, r, categoria)
        elif isinstance(datos, dict) and isinstance(datos.get('vulnerabilities'), dict) and 'auditReportVersion' in datos:
            _npm(datos, r, categoria)
        elif isinstance(datos, dict) and isinstance(datos.get('site'), list):
            _zap(datos, r, categoria, alcance)
        elif filas and all(isinstance(f, dict) and 'template-id' in f for f in filas):
            _nuclei(filas, r, categoria, alcance)
        elif filas and all(isinstance(f, dict) and 'SourceMetadata' in f for f in filas):
            _trufflehog(filas, r, categoria, repo)
        else:
            r['error'] = ('%s tiene un formato desconocido: no es SARIF 2.1.0 ni un reporte nativo que se sepa leer '
                          '(osv-scanner, pip-audit, npm audit, ZAP, Nuclei, TruffleHog)' % nombre)
            return r
    except Formato as e:
        r['error'] = '%s: %s' % (nombre, e)
        return r
    except (AttributeError, TypeError, KeyError, ValueError, IndexError) as e:
        r['error'] = '%s: estructura inesperada (%s: %s)' % (nombre, type(e).__name__, e)
        return r
    r['cubre'] = sorted(set(r['cubre']))
    r['evidencia'] = sorted(set(r['evidencia']))
    if not r['cubre']:
        r['error'] = ('no se sabe de que categoria es %s (herramienta %s): pasalo como <categoria>:<archivo>'
                      % (nombre, r['herramienta'] or 'desconocida'))
    return r


def _supresion(supresiones, hoy):
    """(estado, motivo, vence) de las supresiones SARIF de un resultado: vale solo con motivo y vencimiento vigente."""
    validas = [s for s in (supresiones or []) if isinstance(s, dict) and s.get('status', 'accepted') == 'accepted']
    if not validas:
        return 'nuevo', '', ''
    s = validas[0]
    p = s.get('properties') or {}
    return suprimir(s.get('justification'), p.get('vence') or p.get('expires') or p.get('expiration')
                    or p.get('effectiveUntil') or p.get('expired_at'), hoy)


def _donde(uri, repo, alcance, r, dast):
    """(archivo, adentro). Una direccion http(s) va sin query (puede llevar un token) y con el alcance aplicado: lo
    de otro origen se anota en fuera y no se cuenta (adentro False). En dast con alcance, una URI que no es una
    direccion tampoco esta en el alcance. Una ruta de archivo, relativa al repositorio."""
    uri = str(uri or '')
    if ES_URL.match(uri) or (dast and alcance):
        if alcance and not dentro(uri, alcance):
            r['fuera'].append(origen(uri) or sin_query(uri)[:80])
            return '', False
        return sin_query(uri), True
    return ruta_de(uri, repo), True


def _sarif(d, r, forzada, repo, hoy, alcance=''):
    version = str(d.get('version') or '2.1.0')
    if not version.startswith('2.1'):
        raise Formato('version de SARIF %s no soportada (se lee la 2.1.0)' % version)
    runs = d.get('runs')
    if not isinstance(runs, list) or not runs:
        raise Formato('el SARIF no trae ninguna corrida (runs)')
    nombres = []
    for run in runs:
        driver = ((run.get('tool') or {}).get('driver')) or {}
        canon, cat_def = herramienta_de(driver.get('name', ''))
        nombres.append(canon)
        cat_def = forzada or cat_def
        if cat_def:
            r['cubre'].append(cat_def)
        reglas = [x for x in (driver.get('rules') or []) if isinstance(x, dict)]
        por_id = dict((x.get('id'), x) for x in reglas)
        invs = [i for i in (run.get('invocations') or []) if isinstance(i, dict)]
        if any(i.get('executionSuccessful') is False for i in invs):
            raise Formato('la herramienta dice que no termino bien (executionSuccessful: false)')
        loc = ((((run.get('properties') or {}).get('metrics') or {}).get('_totals')) or {}).get('loc')
        cero = loc is not None and _entero(loc) == 0
        miro = not cero and (any(i.get('executionSuccessful') is True for i in invs) or bool(run.get('artifacts')))
        dast = cat_def == 'dast'
        # Una prueba dinamica muestra que llego a la aplicacion solo con algo adentro del alcance.
        en_alcance = not (dast and alcance) or any(
            isinstance(x, dict) and dentro(str((x.get('location') or {}).get('uri', '')), alcance) for x in run.get('artifacts') or [])
        for res in run.get('results') or []:
            if not isinstance(res, dict) or res.get('baselineState') == 'absent':
                continue
            rid = res.get('ruleId') or ((res.get('rule') or {}).get('id')) or ''
            idx = res.get('ruleIndex')
            regla = por_id.get(rid) or (reglas[idx] if isinstance(idx, int) and 0 <= idx < len(reglas) else {})
            rid = rid or regla.get('id', '') or 'sin-regla'
            pr, pg = res.get('properties') or {}, regla.get('properties') or {}
            tags = _lista(pg.get('tags')).lower()
            cat = cat_def
            if not forzada and canon == 'trivy':
                cat = 'sca' if ('vulnerability' in tags or 'license' in tags) else 'secretos' if 'secret' in tags else 'config'
            if not cat:
                continue
            r['cubre'].append(cat)
            sev = (de_puntaje(pr.get('security-severity')) or de_puntaje(pg.get('security-severity'))
                   or de_texto(pr.get('issue_severity') or pr.get('severity') or pg.get('issue_severity') or pg.get('severity'))
                   or de_nivel(res.get('level') or (regla.get('defaultConfiguration') or {}).get('level')) or 'MEDIA')
            msg = str(((res.get('message') or {}).get('text')) or '')
            locs = res.get('locations') or []
            pl = (locs[0].get('physicalLocation') or {}) if locs and isinstance(locs[0], dict) else {}
            archivo, adentro = _donde((pl.get('artifactLocation') or {}).get('uri', ''), repo, alcance, r, cat == 'dast')
            if not adentro:
                continue
            en_alcance = True
            linea = _entero((pl.get('region') or {}).get('startLine'))
            textos = [rid, regla.get('id', ''), regla.get('name', '')] + [str(x) for x in (regla.get('deprecatedIds') or [])]
            if cat == 'secretos':
                titulo = 'secreto detectado (%s)' % rid            # nunca el mensaje: puede traer el valor
            else:
                textos.append(msg)
                titulo = _texto((regla.get('shortDescription') or {}).get('text')) or _texto(regla.get('name')) or rid
            paquete = version = arreglo = ''
            if cat in ('sca', 'imagen') and 'Package:' in msg:
                paquete, version, arreglo = _campo(msg, 'Package'), _campo(msg, 'Installed Version'), _campo(msg, 'Fixed Version')
            estado, motivo, vence = _supresion(res.get('suppressions'), hoy)
            if estado == 'nuevo' and res.get('baselineState') in ('unchanged', 'updated'):
                estado = 'en-linea-base'
            fp = ((res.get('partialFingerprints') or {}).get('primaryLocationLineHash')) or ''
            r['hallazgos'].append(hallazgo(
                herramienta=canon, categoria=cat, regla=rid, titulo=titulo, cwe=_cwe([tags, pg.get('cwe'), pr.get('cwe')]),
                cve=_primero(CVE, textos), severidad=sev, archivo=archivo, linea=linea, paquete=paquete, version=version,
                arreglo=arreglo, estado=estado, motivo_supresion=motivo, vence=vence,
                huella=str(fp) or huella(canon, rid, archivo, linea, repo, cat, paquete)))
        if miro and cat_def and en_alcance:
            r['evidencia'].append(cat_def)
    r['herramienta'] = ', '.join(dict.fromkeys(nombres))


def _osv(d, r, forzada, repo):
    cat = forzada or 'sca'
    r['herramienta'] = 'osv-scanner'
    r['cubre'].append(cat)
    for fuente in d.get('results') or []:
        archivo = ruta_de(((fuente.get('source') or {}).get('path')) or '', repo)
        for p in fuente.get('packages') or []:
            r['evidencia'].append(cat)
            pkg = p.get('package') or {}
            nombre, version = str(pkg.get('name') or ''), str(pkg.get('version') or '')
            vulns = dict((v.get('id'), v) for v in (p.get('vulnerabilities') or []) if isinstance(v, dict))
            for g in p.get('groups') or [{'ids': [i]} for i in vulns]:
                ids = [str(x) for x in (g.get('ids') or [])]
                v = next((vulns[i] for i in ids if i in vulns), {})
                todos = ids + [str(x) for x in (g.get('aliases') or [])] + [str(x) for x in (v.get('aliases') or [])]
                rid = ids[0] if ids else str(v.get('id') or 'sin-id')
                ds = v.get('database_specific') or {}
                sev = de_puntaje(g.get('max_severity')) or de_texto(ds.get('severity'))
                titulo = _texto(v.get('summary'), 90) or rid
                if not sev:
                    sev, titulo = 'ALTA', titulo + SIN_SEVERIDAD
                fijas = [str(ev['fixed']) for af in (v.get('affected') or [])
                         if ((af.get('package') or {}).get('name')) == nombre
                         for rg in (af.get('ranges') or []) for ev in (rg.get('events') or []) if ev.get('fixed')]
                r['hallazgos'].append(hallazgo(
                    herramienta='osv-scanner', categoria=cat, regla=rid, titulo=titulo, cwe=_cwe([_lista(ds.get('cwe_ids'))]),
                    cve=_primero(CVE, todos), severidad=sev, archivo=archivo, paquete=nombre, version=version,
                    arreglo=', '.join(dict.fromkeys(fijas)), huella=huella('osv-scanner', rid, archivo, 0, '', cat, nombre)))


def _pip_audit(d, r, forzada):
    cat = forzada or 'sca'
    r['herramienta'] = 'pip-audit'
    r['cubre'].append(cat)
    for dep in d.get('dependencies') or []:
        if not isinstance(dep, dict):
            continue
        if dep.get('version') and not dep.get('skip_reason'):
            r['evidencia'].append(cat)
        for v in dep.get('vulns') or []:
            rid = str(v.get('id') or 'sin-id')
            r['hallazgos'].append(hallazgo(
                herramienta='pip-audit', categoria=cat, regla=rid, titulo=(_texto(v.get('description'), 90) or rid) + SIN_SEVERIDAD,
                cve=_primero(CVE, [rid] + [str(x) for x in (v.get('aliases') or [])]), severidad='ALTA',
                paquete=dep.get('name', ''), version=dep.get('version', ''), arreglo=', '.join(str(x) for x in (v.get('fix_versions') or [])),
                huella=huella('pip-audit', rid, '', 0, '', cat, str(dep.get('name', '')))))


def _npm(d, r, forzada):
    cat = forzada or 'sca'
    r['herramienta'] = 'npm-audit'
    r['cubre'].append(cat)
    deps = (d.get('metadata') or {}).get('dependencies')
    if _entero(deps.get('total') if isinstance(deps, dict) else deps) > 0 or d['vulnerabilities']:
        r['evidencia'].append(cat)
    vistos = set()
    for nombre, e in sorted(d['vulnerabilities'].items()):
        if not isinstance(e, dict):
            continue
        for via in e.get('via') or []:
            if not isinstance(via, dict):                   # un nombre suelto: es otro paquete vulnerable, ya listado
                continue
            url = str(via.get('url') or '')
            m = re.search(r'(GHSA(?:-[0-9a-z]{4}){3})', url, re.I)
            rid = m.group(1) if m else str(via.get('source') or 'sin-id')
            if (nombre, rid) in vistos:
                continue
            vistos.add((nombre, rid))
            sev = de_texto(via.get('severity') or e.get('severity'))
            titulo = _texto(via.get('title'), 90) or rid
            if not sev:
                sev, titulo = 'ALTA', titulo + SIN_SEVERIDAD
            fix = e.get('fixAvailable')
            arreglo = ('%s@%s' % (fix.get('name', ''), fix.get('version', '')) if isinstance(fix, dict)
                       else 'hay una version arreglada' if fix is True else '')
            nodos = e.get('nodes') or []
            archivo = str(nodos[0]) if nodos else ''
            r['hallazgos'].append(hallazgo(
                herramienta='npm-audit', categoria=cat, regla=rid, titulo=titulo, cwe=_cwe([_lista(via.get('cwe'))]),
                cve=_primero(CVE, [url, titulo]), severidad=sev, archivo=archivo, paquete=nombre, arreglo=arreglo,
                huella=huella('npm-audit', rid, archivo, 0, '', cat, nombre)))


def _zap(d, r, forzada, alcance):
    cat = forzada or 'dast'
    r['herramienta'] = 'zap'
    r['cubre'].append(cat)
    for sitio in d.get('site') or []:
        if not isinstance(sitio, dict):
            continue
        nombre = str(sitio.get('@name') or '')
        if alcance and not dentro(nombre, alcance):
            r['fuera'].append(origen(nombre) or _texto(nombre, 80))
            continue
        r['evidencia'].append(cat)
        for a in sitio.get('alerts') or []:
            inst = [i for i in (a.get('instances') or []) if isinstance(i, dict)]
            url = str(inst[0].get('uri') or '') if inst else nombre
            if alcance and not dentro(url, alcance):
                r['fuera'].append(origen(url) or _texto(url, 80))
                continue
            rid = str(a.get('pluginid') or a.get('alertRef') or 'sin-regla')
            sev = RIESGO_ZAP.get(str(a.get('riskcode', '')).strip()) or de_texto(str(a.get('riskdesc') or '').split(' ')[0])
            titulo = _texto(a.get('name') or a.get('alert')) or rid
            if not sev:
                sev, titulo = 'ALTA', titulo + SIN_SEVERIDAD
            cwe = _entero(a.get('cweid'))
            archivo = sin_query(url)
            r['hallazgos'].append(hallazgo(herramienta='zap', categoria=cat, regla=rid, titulo=titulo,
                                           cwe='CWE-%d' % cwe if cwe > 0 else '', severidad=sev, archivo=archivo,
                                           huella=huella('zap', rid, archivo, 0, '', cat)))


def _nuclei(filas, r, forzada, alcance):
    cat = forzada or 'dast'
    r['herramienta'] = 'nuclei'
    r['cubre'].append(cat)
    for f in filas:
        url = str(f.get('matched-at') or f.get('url') or f.get('host') or '')
        if alcance and not dentro(url, alcance):
            r['fuera'].append(origen(url) or _texto(url, 80))
            continue
        r['evidencia'].append(cat)
        info = f.get('info') or {}
        cls = info.get('classification') or {}
        rid = str(f.get('template-id') or 'sin-plantilla')
        sev = de_texto(info.get('severity'))
        titulo = _texto(info.get('name')) or rid
        if not sev:
            sev, titulo = 'ALTA', titulo + SIN_SEVERIDAD
        archivo = sin_query(url)
        r['hallazgos'].append(hallazgo(herramienta='nuclei', categoria=cat, regla=rid, titulo=titulo,
                                       cwe=_cwe([_lista(cls.get('cwe-id'))]), cve=_primero(CVE, [_lista(cls.get('cve-id')), rid]),
                                       severidad=sev, archivo=archivo, huella=huella('nuclei', rid, archivo, 0, '', cat)))


def _trufflehog(filas, r, forzada, repo):
    cat = forzada or 'secretos'
    r['herramienta'] = 'trufflehog'
    r['cubre'].append(cat)
    for f in filas:
        r['evidencia'].append(cat)
        datos = ((f.get('SourceMetadata') or {}).get('Data')) or {}
        lugar = next((v for v in datos.values() if isinstance(v, dict)), {})
        archivo = ruta_de(str(lugar.get('file') or ''), repo)
        linea = _entero(lugar.get('line'))
        rid = str(f.get('DetectorName') or f.get('DetectorType') or 'secreto')
        r['hallazgos'].append(hallazgo(herramienta='trufflehog', categoria=cat, regla=rid, titulo='secreto detectado (%s)' % rid,
                                       severidad='ALTA', archivo=archivo, linea=linea,
                                       huella=huella('trufflehog', rid, archivo, linea, '', 'secretos')))


# ------------------------------------------------------------------------------------------- linea de base

def cargar_linea_base(ruta):
    """(huellas, error). La linea de base es un informe normalizado anterior, aceptado por una persona."""
    try:
        with open(ruta, 'rb') as h:
            d = json.loads(h.read().decode('utf-8', 'replace').lstrip(BOM))
    except (OSError, ValueError) as e:
        return None, 'no se pudo leer la linea de base %s (%s)' % (os.path.basename(ruta), type(e).__name__)
    if not isinstance(d, dict) or not isinstance(d.get('hallazgos'), list):
        return None, 'la linea de base %s no es un informe normalizado (le falta "hallazgos")' % os.path.basename(ruta)
    return set(h.get('huella') for h in d['hallazgos'] if isinstance(h, dict) and h.get('huella')), ''


def aplicar_linea_base(hallazgos, huellas):
    n = 0
    for h in hallazgos:
        if h['estado'] == 'nuevo' and h['huella'] in huellas:
            h['estado'] = 'en-linea-base'
            n += 1
    return n


# ------------------------------------------------------------------------------------------- supresiones del repo

def _tiene_motivo(texto):
    """Un motivo son al menos dos palabras de verdad: ni ids de regla, ni la fecha, ni las etiquetas."""
    t = VENCE.sub(' ', texto)
    t = re.sub(r'(?i)\b(?:motivo|reason|aprob\w*|vence|exp)\b\s*[:=]?', ' ', t)
    t = re.sub(r'\b[\w-]+(?:\.[\w-]+)+\b', ' ', t)
    t = re.sub(r'\b[A-Za-z]+[-_]?\d+\w*\b', ' ', t)
    return len(re.findall(r'[^\W\d_]{3,}', t)) >= 2


def _problema(motivo_ok, vence, hoy):
    """(regla, detalle) o ('', '') si la supresion esta en regla."""
    detalle = [x for x, si in (('sin motivo', not motivo_ok), ('sin vencimiento', not vence),
                               ('vencida el %s' % vence, bool(vence) and vence < hoy)) if si]
    if not detalle:
        return '', ''
    regla = ('supresion-sin-motivo' if not motivo_ok else 'supresion-sin-vencimiento' if not vence else 'supresion-vencida')
    return regla, ' y '.join(detalle)


def revisar_supresiones(repo, categorias, hoy=None):
    """Las supresiones escritas en el repositorio sin motivo, sin vencimiento o vencidas: un hallazgo ALTA cada una."""
    hoy = (hoy or datetime.date.today()).isoformat()
    salida = []

    def agregar(cat, marca, rel, linea, motivo_ok, motivo, vence):
        regla, detalle = _problema(motivo_ok, vence, hoy)
        if regla and cat in categorias:
            salida.append(hallazgo(herramienta='supresiones', categoria=cat, regla=regla, titulo='supresion %s %s' % (marca, detalle),
                                   severidad='ALTA', archivo=rel, linea=linea, motivo_supresion=motivo, vence=vence,
                                   huella=huella('supresiones', regla, rel, linea, repo, cat)))

    for base, dirs, archivos in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in BASURA and not d.startswith('.'))
        for f in sorted(archivos):
            ruta = os.path.join(base, f)
            rel = os.path.relpath(ruta, repo).replace('\\', '/')
            bajo = f.lower()
            if f not in ('osv-scanner.toml', '.trivyignore', '.gitleaksignore') and not (
                    os.path.splitext(bajo)[1] in FUENTE_EXT or bajo.startswith('dockerfile')):
                continue
            try:
                if os.path.getsize(ruta) > 2000000:
                    continue
                with open(ruta, 'rb') as h:
                    lineas = h.read().decode('utf-8', 'replace').splitlines()
            except OSError:
                continue
            if f == 'osv-scanner.toml':
                _toml(lineas, rel, agregar)
            elif f in ('.trivyignore', '.gitleaksignore'):
                _ignorar(lineas, rel, f, agregar)
            else:
                for i, linea in enumerate(lineas, 1):
                    m = MARCA.search(linea)
                    if m:
                        resto = m.group(2)
                        cat = 'secretos' if m.group(1).lower() == 'gitleaks:allow' else 'sast'
                        v = VENCE.search(resto)
                        agregar(cat, m.group(1).lower(), rel, i, _tiene_motivo(resto), _texto(resto, 200), v.group(1) if v else '')
    return salida


def _toml(lineas, rel, agregar):
    """[[IgnoredVulns]] y [[PackageOverrides]] que ignoran: reason y effectiveUntil."""
    bloques, actual = [], None
    for i, linea in enumerate(lineas, 1):
        s = linea.strip()
        if s.startswith('['):
            actual = {'tipo': s.strip('[] '), 'linea': i, 'id': '', 'reason': '', 'until': '', 'ignora': False} if s.startswith('[[') else None
            if actual:
                bloques.append(actual)
        elif actual is not None and '=' in s and not s.startswith('#'):
            clave, valor = [x.strip() for x in s.split('=', 1)]
            valor = valor[1:valor.find('"', 1)] if valor.startswith('"') and '"' in valor[1:] else valor.split('#')[0].strip()
            if clave in ('id', 'name'):
                actual['id'] = actual['id'] or valor
            elif clave == 'reason':
                actual['reason'] = valor
            elif clave == 'effectiveUntil':
                actual['until'] = _fecha(valor)
            elif clave in ('ignore', 'vulnerability.ignore') and valor.lower() == 'true':
                actual['ignora'] = True
    for b in bloques:
        if b['tipo'] == 'IgnoredVulns' or (b['tipo'] == 'PackageOverrides' and b['ignora']):
            agregar('sca', '%s %s' % (b['tipo'], b['id']), rel, b['linea'], _tiene_motivo(b['reason']), b['reason'], b['until'])


def _ignorar(lineas, rel, nombre, agregar):
    """.trivyignore y .gitleaksignore: el motivo es el comentario de arriba (vale para el grupo hasta una linea en
    blanco) o el de al lado; el vencimiento, exp:AAAA-MM-DD (nativo de Trivy) o vence: AAAA-MM-DD en el comentario."""
    comentario = []
    for i, linea in enumerate(lineas, 1):
        s = linea.strip()
        if not s:
            comentario = []
            continue
        if s.startswith('#'):
            comentario.append(s.lstrip('#'))
            continue
        entrada, _, cola = s.partition('#')
        texto = ' '.join(comentario + [cola])
        v = VENCE.search(entrada + ' ' + texto)
        ident = entrada.split()[0] if entrada.split() else entrada
        if nombre == '.gitleaksignore':
            cat = 'secretos'
        else:
            cat = 'sca' if ident.upper().startswith(('CVE-', 'GHSA-')) else 'config'
        agregar(cat, ident, rel, i, _tiene_motivo(texto), _texto(texto, 200), v.group(1) if v else '')


# ------------------------------------------------------------------------------------------- informe y veredicto

def nuevo_informe(origen_):
    return {'veredicto': SIN_DATOS, 'origen': origen_, 'generado': ahora(), 'categorias': {}, 'hallazgos': [],
            'sin_datos': [], 'no_mira': []}


def poner_categoria(inf, cat, herramientas, faltan, extra=''):
    """El estado de una categoria: HALLAZGO si hay un bloqueante (o algo grave en extra); si no, SIN DATOS si algo
    no se pudo medir o nadie la midio; OK solo si todo lo que aplicaba midio y esta limpio."""
    faltan = list(faltan)
    bloq = sum(1 for h in inf['hallazgos'] if h['categoria'] == cat and bloqueante(h))
    if bloq or extra:
        estado = HALLAZGO
        partes = (['%d bloqueante(s)' % bloq] if bloq else []) + ([extra] if extra else []) + (
            ['sin medir: ' + '; '.join(faltan)] if faltan else [])
        motivo = '; '.join(partes)
    elif faltan or not herramientas:
        estado = SIN_DATOS
        faltan = faltan or ['nada midio esta categoria']
        motivo = '; '.join(faltan)
    else:
        estado, motivo = OK, ''
    inf['categorias'][cat] = {'estado': estado, 'herramienta': ', '.join(dict.fromkeys(herramientas)), 'motivo': motivo}
    for f in faltan:
        inf['sin_datos'].append('%s: %s' % (cat, f))


def cerrar(inf):
    """El veredicto del informe y el codigo de salida: HALLAZGO gana, despues SIN DATOS, OK solo si todo midio."""
    estados = [c['estado'] for c in inf['categorias'].values()]
    inf['veredicto'] = (SIN_DATOS if not estados else HALLAZGO if HALLAZGO in estados
                        else SIN_DATOS if SIN_DATOS in estados else OK)
    return CODIGO[inf['veredicto']]


def a_json(datos):
    return json.dumps(datos, ensure_ascii=True, indent=1)


def lineas_texto(inf, titulo, pie=()):
    """El resumen para una persona: categorias, bloqueantes, avisos, y lo que el script no mira."""
    hs = inf['hallazgos']
    bloq = [h for h in hs if bloqueante(h)]
    salida = ['%s -- %s  [%d categoria(s); %d hallazgo(s), %d bloqueante(s)]' % (
        titulo, inf['veredicto'], len(inf['categorias']), len(hs), len(bloq))]
    for c in sorted(inf['categorias'], key=lambda x: CATEGORIAS.index(x) if x in CATEGORIAS else 99):
        x = inf['categorias'][c]
        salida.append('  %-9s %-10s %s%s' % (c, x['estado'], x['herramienta'] or '-', (' -- ' + x['motivo']) if x['motivo'] else ''))
    orden = sorted(hs, key=lambda h: (0 if bloqueante(h) else 1, SEVERIDADES.index(h['severidad']), h['categoria'], h['archivo'], h['linea']))
    mostrados = 0
    for h in orden:
        if h['estado'] != 'nuevo' or h['severidad'] in ('BAJA', 'INFO'):
            continue
        if mostrados == 40:
            salida.append('  ... y mas: el detalle completo, con --json')
            break
        donde = h['archivo'] + (':%d' % h['linea'] if h['linea'] else '')
        salida.append('  %-10s %-7s %-8s %s %s %s%s -- %s (huella %s)' % (
            'BLOQUEANTE' if bloqueante(h) else 'aviso', h['severidad'], h['categoria'], h['herramienta'], h['regla'],
            donde or '-', (' ' + h['cve']) if h['cve'] else '', h['titulo'][:70], h['huella']))
        mostrados += 1
    salida.append('  En linea de base: %d; suprimidos: %d; registro (BAJA e INFO): %d' % (
        sum(1 for h in hs if h['estado'] == 'en-linea-base'), sum(1 for h in hs if h['estado'] == 'suprimido'),
        sum(1 for h in hs if h['estado'] == 'nuevo' and h['severidad'] in ('BAJA', 'INFO'))))
    salida += ['  ' + p for p in pie]
    salida.append('  Lo que este script NO mira: ' + '; '.join(inf['no_mira']) + '.')
    return salida
