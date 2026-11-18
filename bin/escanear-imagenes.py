#!/usr/bin/env python3
"""Escaneo de una imagen de contenedor: el reporte JSON de Trivy o de Grype, normalizado al esquema comun de
hallazgos (bin/seguridad/normalizar.py). SOLO LECTURA.

    python -I bin/escanear-imagenes.py --reporte <trivy.json> --base <metadata.json>   [--imagen <alias>]
    python -I bin/escanear-imagenes.py --reporte <grype.json>                           [--imagen <alias>]
    python -I bin/escanear-imagenes.py --imagen <alias> --correr trivy|grype            (corre el escaner instalado)
    opciones: --umbral ALTA|MEDIA|BAJA (por defecto ALTA)  --max-horas-base 120
              --modulo <slug> | --inventario <ruta>  --raiz <repo>  --json

    --base (solo Trivy, que no trae su base en el reporte): el metadata.json de su cache (<cache>/db/metadata.json)
    o la salida de "trivy version --format json". La edad se mide AL MOMENTO DEL ESCANEO: el CreatedAt del reporte
    menos el UpdatedAt de la base. Sin CreatedAt, o con una base posterior al reporte (no es la que uso), SIN DATOS.
    Grype trae su base en el reporte.

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA: la imagen no esta autorizada)   2 = SIN DATOS
Con un HALLAZGO y un chequeo sin datos a la vez sale 1, y la linea de ese chequeo dice SIN DATOS.

POR QUE EXISTE. El codigo de salida de un escaner engania: Trivy sale 0 aunque encuentre vulnerabilidades y
Grype, con --fail-on, sale 2, que aca quiere decir SIN DATOS. Y un "cero vulnerabilidades" puede ser mentira:
con la base vieja o ausente, sin paquetes analizados, o con un sistema operativo sin soporte, el escaner no
conoce lo nuevo. Este script lee el JSON y decide con las reglas del paquete bin/seguridad/ (hallazgo,
poner_categoria y cerrar): CRITICA y ALTA nuevas frenan (--umbral solo puede sumar MEDIA o BAJA, nunca aflojar);
un secreto es ALTA como minimo; una severidad desconocida es ALTA hasta priorizar; una supresion (de Grype o de
.trivyignore.yaml) vale solo con motivo Y vencimiento vigente ("vence: AAAA-MM-DD" en el motivo). HALLAZGO:
lo anterior, y el sistema operativo base sin soporte. SIN DATOS: el reporte no se puede leer o no es de Trivy ni
de Grype; no trae CreatedAt; no analizo paquetes (ningun resultado os-pkgs ni lang-pkgs); la base es vieja,
invalida, posterior al reporte o no se sabe su edad; Trivy es la 0.69.4 (incidente de marzo de 2026); detecto
el sistema pero no analizo sus paquetes; y, con el sistema sin soporte, su conteo de vulnerabilidades.

QUE NO HACE. No baja nada: ni la base (a Trivy le pide no actualizarla, y a Grype tambien; la actualiza una
persona antes) ni la imagen (Trivy con --image-src docker,containerd,podman, sin remote; Grype con el esquema
docker: y solo si "docker image inspect" la encuentra en la maquina; si no esta, SIN DATOS). Con --correr pasa
antes por el inventario (la imagen, por su alias, de tipo imagen y hasta N0) y escanea su Destino. Nunca le pasa
al escaner una opcion que cambie algo, que haga depender el codigo de salida de los hallazgos o que lo deje ir al
registro (lista negra en el codigo). Nunca imprime el valor de un secreto: regla, archivo y linea. Lo unico que
escribe, y solo con --correr, es el reporte crudo en borrador/seguridad/<fecha>-<alias saneado>/.
Solo biblioteca estandar. ASCII puro.
"""

import argparse
import calendar
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario
from seguridad import normalizar  # noqa: E402  el esquema comun y sus reglas

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
NOMBRE = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = 'escanear-imagenes'
NIVELES = ('INFO', 'BAJA', 'MEDIA', 'ALTA', 'CRITICA')
UMBRALES = ('ALTA', 'MEDIA', 'BAJA')      # CRITICA no: aflojaria la regla del paquete (CRITICA y ALTA frenan)
SEVERIDAD = {'critical': 'CRITICA', 'high': 'ALTA', 'medium': 'MEDIA', 'low': 'BAJA', 'negligible': 'INFO'}
HORAS_BASE = 120          # el tope por defecto de Grype (db.max-allowed-built-age: 120h)
TOPE_SEGUNDOS = 1800
SUPRIMIDOS = ('ignored', 'not_affected', 'fixed')
TRIVY_COMPROMETIDAS = ('0.69.4',)         # incidente de marzo de 2026 (CVE-2026-33634)
FUENTES_LOCALES = 'docker,containerd,podman'
# Lista negra: opciones que cambian algo (el cache, la base, un servidor) o que hacen depender el codigo de
# salida de los hallazgos. Las ordenes de este script son fijas; esto es la red por si alguien las toca.
PROHIBIDAS = {'trivy': ('--exit-code', '--exit-on-eol', '--server', '--token', '--download-db-only', '--download-java-db-only',
                        '--reset', '--clear-cache', 'clean', '--cache-backend'),
              'grype': ('--fail-on', '-f', 'db', 'update', 'delete', '--add-cpes-if-none')}
DESTINO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$')
FECHA = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?$')
CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f]')
NO_MIRA = ('si la vulnerabilidad es alcanzable desde el codigo de la aplicacion: eso es VEX, y lo firma una persona',
           'la prioridad (KEV, EPSS, exposicion del activo) y el plazo: los calcula priorizar-vulnerabilidades.py',
           'la configuracion de la imagen y del Dockerfile: la mira auditar-iac.py',
           'los paquetes que el escaner no reconoce (binarios copiados a mano, sin gestor de paquetes)',
           'que la imagen escaneada sea la que corre en el ambiente: lo dice el inventario, no el reporte',
           'la imagen tal cual esta en el registro: se escanea la que esta en esta maquina, que este script nunca baja',
           'quien aprobo una supresion: lo mira el verificador en el Merge Request')


def limpio(texto, largo=140):
    """Lo que viene de un escaner es dato: a la salida va sin caracteres de control y acotado."""
    t = CONTROL.sub('', str(texto if texto is not None else ''))
    return t if len(t) <= largo else t[:largo - 3] + '...'


def saneado(alias):
    """El alias como nombre de carpeta: sin barras ni nada que no sea letra, numero, punto, guion o guion bajo."""
    return re.sub(r'[^A-Za-z0-9._-]', '_', alias or 'sin-alias')


def a_epoch(texto):
    """Segundos UTC de una fecha RFC 3339 (con o sin fraccion y zona), o None si no es una fecha valida."""
    m = FECHA.match(str(texto or '').strip())
    if not m:
        return None
    a, me, d, h, mi, s, zona = m.groups()
    if int(a) < 2000:                         # la fecha cero de Go (0001-01-01) no es una fecha
        return None
    try:
        t = calendar.timegm((int(a), int(me), int(d), int(h), int(mi), int(s), 0, 0, 0))
    except (ValueError, OverflowError):
        return None
    if zona and zona != 'Z':
        z = zona[1:].replace(':', '')
        t -= (1 if zona[0] == '+' else -1) * (int(z[:2]) * 3600 + int(z[2:]) * 60)
    return t


def leer_json(ruta, que):
    """(datos, motivo). datos es None si no se pudo leer."""
    if not ruta or not os.path.isfile(ruta):
        return None, 'no existe %s (%s)' % (que, ruta or 'sin ruta')
    try:
        with open(ruta, 'rb') as h:
            crudo = h.read()
    except OSError as e:
        return None, 'no se pudo leer %s: %s' % (que, e)
    if not crudo.strip():
        return None, '%s esta vacio' % que
    try:
        return json.loads(crudo.decode('utf-8-sig')), ''
    except (ValueError, UnicodeDecodeError):
        return None, '%s no es un JSON legible' % que


def nuevo(herramienta, categoria, regla, titulo, severidad, activo, archivo='', linea=0, paquete='', version='',
          arreglo='', cve='', cwe='', estado='nuevo', motivo='', vence=''):
    """Un hallazgo del esquema comun (normalizar.hallazgo aplica sus reglas: un secreto sube a ALTA, una severidad
    desconocida es ALTA). La huella, con la funcion del paquete; el activo y la linea entran en la clave."""
    if not severidad:
        titulo = limpio(titulo, 100) + normalizar.SIN_SEVERIDAD
    linea = linea if isinstance(linea, int) else 0
    clave = '%s|%s|%d' % (paquete, activo, linea)
    return normalizar.hallazgo(
        herramienta=herramienta, categoria=categoria, regla=limpio(regla, 80), titulo=limpio(titulo, 160), cwe=limpio(cwe, 20),
        cve=limpio(cve, 30), severidad=severidad, archivo=limpio(archivo, 160), linea=linea, paquete=limpio(paquete, 80),
        version=limpio(version, 60), arreglo=limpio(arreglo, 80), activo=activo, estado=estado, motivo_supresion=limpio(motivo, 200),
        vence=vence, huella=normalizar.huella(herramienta, str(regla), str(archivo), linea, '', categoria, clave))


def severidad_de(texto):
    """La severidad del esquema, o '' si el escaner no la informa o no se la conoce (el paquete la toma ALTA)."""
    return SEVERIDAD.get(str(texto or '').strip().lower(), '')


def supresion(motivo, hoy):
    """(estado, motivo, vence) con la regla 5 del paquete: vale con motivo y con vencimiento vigente en el motivo."""
    return normalizar.suprimir(motivo, normalizar.vence_de(motivo), hoy)


def base_de_trivy(datos):
    """Fecha de la base de Trivy: del metadata.json del cache o de 'trivy version --format json'."""
    if not isinstance(datos, dict):
        return None
    meta = datos.get('VulnerabilityDB') if isinstance(datos.get('VulnerabilityDB'), dict) else datos
    return a_epoch(meta.get('UpdatedAt'))


def version_de_trivy(*fuentes):
    """La version de Trivy que dicen la salida de 'trivy version' o el reporte (campo Trivy.Version), o ''."""
    for d in fuentes:
        if not isinstance(d, dict):
            continue
        if isinstance(d.get('VulnerabilityDB'), dict):          # la salida de 'trivy version' (el metadata.json no la trae)
            v = d.get('Version')
        else:
            v = (d.get('Trivy') or {}).get('Version') if isinstance(d.get('Trivy'), dict) else None
        if v:
            return str(v).strip().lstrip('v')
    return ''


def de_trivy(rep, activo, hoy):
    """(hallazgos, so, paquetes, secretos). so: None si no trae sistema, o (nombre, sin_soporte, analizado)."""
    hall = []
    res = [r for r in rep.get('Results') or [] if isinstance(r, dict)]
    for r in res:
        destino = r.get('Target', '')
        for v in r.get('Vulnerabilities') or []:
            vid = str(v.get('VulnerabilityID', ''))
            hall.append(nuevo('trivy', 'imagen', vid, v.get('Title') or vid, severidad_de(v.get('Severity')), activo,
                              cve=vid if vid.startswith('CVE-') else '', cwe=(v.get('CweIDs') or [''])[0], archivo=destino,
                              paquete=v.get('PkgName', ''), version=v.get('InstalledVersion', ''), arreglo=v.get('FixedVersion', '')))
        for s in r.get('Secrets') or []:
            # El valor (Match, Code) no se lee nunca: regla, archivo y linea alcanzan para ubicarlo.
            hall.append(nuevo('trivy', 'secretos', s.get('RuleID', ''), 'secreto en una capa (%s)' % limpio(s.get('RuleID', ''), 60),
                              severidad_de(s.get('Severity')) or 'ALTA', activo, archivo=destino, linea=s.get('StartLine', 0)))
        for m in r.get('ExperimentalModifiedFindings') or []:
            if not isinstance(m, dict) or m.get('Type') not in ('vulnerability', 'secret'):
                continue
            f = m.get('Finding') or {}
            motivo = str(m.get('Statement') or '').strip()
            estado, motivo, vence = supresion(motivo, hoy) if str(m.get('Status', '')).lower() in SUPRIMIDOS else ('nuevo', motivo, '')
            fuente = (' (%s)' % m['Source']) if m.get('Source') and motivo else ''
            vid = str(f.get('VulnerabilityID') or f.get('RuleID') or '')
            cat = 'imagen' if m['Type'] == 'vulnerability' else 'secretos'
            hall.append(nuevo('trivy', cat, vid, f.get('Title') or vid, severidad_de(f.get('Severity')) or ('ALTA' if cat == 'secretos' else ''),
                              activo, cve=vid if vid.startswith('CVE-') else '', archivo=destino, paquete=f.get('PkgName', ''),
                              version=f.get('InstalledVersion', ''), arreglo=f.get('FixedVersion', ''), estado=estado,
                              motivo=motivo + fuente, vence=vence))
    paquetes = any(r.get('Class') in ('os-pkgs', 'lang-pkgs') for r in res)
    secretos = any(r.get('Class') == 'secret' or r.get('Secrets') for r in res) or any(h['categoria'] == 'secretos' for h in hall)
    so = (rep.get('Metadata') or {}).get('OS')
    if not isinstance(so, dict) or not so.get('Family'):
        return hall, None, paquetes, secretos
    nombre = '%s %s' % (so.get('Family', ''), so.get('Name', ''))
    analizado = any(r.get('Class') == 'os-pkgs' for r in res)
    return hall, (nombre.strip(), bool(so.get('EOSL')), analizado), paquetes, secretos


def de_grype(rep, activo, hoy):
    """(hallazgos, so) de un reporte de Grype."""
    hall = []

    def uno(m, estado='nuevo', motivo='', vence=''):
        v = m.get('vulnerability') or {}
        a = m.get('artifact') or {}
        vid = str(v.get('id', ''))
        cve = vid if vid.startswith('CVE-') else next((str(r.get('id')) for r in m.get('relatedVulnerabilities') or []
                                                       if str(r.get('id', '')).startswith('CVE-')), '')
        fix = v.get('fix') or {}
        lugar = ((a.get('locations') or [{}])[0] or {}).get('path', '')
        return nuevo('grype', 'imagen', vid, '%s en %s' % (vid, a.get('name', '')), severidad_de(v.get('severity')), activo, cve=cve,
                     archivo=lugar, paquete=a.get('name', ''), version=a.get('version', ''), arreglo=', '.join(fix.get('versions') or []),
                     estado=estado, motivo=motivo, vence=vence)

    for m in rep.get('matches') or []:
        if isinstance(m, dict):
            hall.append(uno(m))
    for m in rep.get('ignoredMatches') or []:
        if not isinstance(m, dict):
            continue
        motivos = [str(r.get('reason') or '').strip() for r in m.get('appliedIgnoreRules') or [] if isinstance(r, dict)]
        hall.append(uno(m, *supresion('; '.join(x for x in motivos if x), hoy)))
    distro = rep.get('distro') or {}
    nombre = ('%s %s' % (distro.get('name', ''), distro.get('version', ''))).strip()
    eol = []
    for p in rep.get('alertsByPackage') or []:
        for al in (p or {}).get('alerts') or []:
            if isinstance(al, dict) and al.get('type') == 'distro-eol':
                md = al.get('metadata') or {}
                eol.append(('%s %s' % (md.get('name', ''), md.get('version', ''))).strip())
    if eol:
        return hall, (eol[0] or nombre, True, True)
    return hall, ((nombre, False, True) if nombre else None)


def base_de_grype(rep):
    """(epoch, motivo) de la base que uso Grype, leida de descriptor.db."""
    db = (rep.get('descriptor') or {}).get('db')
    if not isinstance(db, dict):
        return None, 'el reporte de Grype no dice que base uso'
    estado = db.get('status') if isinstance(db.get('status'), dict) else db
    if estado.get('valid') is False or estado.get('error'):
        return None, 'Grype marco su base como invalida'
    t = a_epoch(estado.get('built'))
    return (t, '') if t else (None, 'el reporte de Grype no trae la fecha de su base')


def edad_trivy(rep, base, max_horas, ahora):
    """(estado, motivo) de la base de Trivy, medida al momento del escaneo (CreatedAt del reporte)."""
    creado = a_epoch(rep.get('CreatedAt'))
    if creado is None:
        return SIN_DATOS, 'el reporte de Trivy no trae CreatedAt: no se sabe cuando corrio ni con que base'
    if base is None:
        return SIN_DATOS, 'sin --base no se sabe la edad de la base de Trivy (metadata.json o "trivy version --format json")'
    fecha = base_de_trivy(base)
    if fecha is None:
        return SIN_DATOS, 'el archivo de --base no trae la fecha de la base (UpdatedAt)'
    if fecha > creado:
        return SIN_DATOS, ('la base de --base es de despues del reporte (%s contra %s): no es la que uso ese escaneo' % (
            time.strftime('%Y-%m-%d %H:%M', time.gmtime(fecha)), time.strftime('%Y-%m-%d %H:%M', time.gmtime(creado))))
    horas, viejo = int(round((creado - fecha) / 3600.0)), int(round((ahora - creado) / 3600.0))
    if horas > max_horas:
        return SIN_DATOS, 'al escanear era de hace %d h (tope %d h): no conocia lo nuevo' % (horas, max_horas)
    if viejo > max_horas:
        return SIN_DATOS, 'el reporte es de hace %d h (tope %d h): no dice como esta la imagen hoy' % (viejo, max_horas)
    return OK, 'de hace %d h al momento del escaneo (tope %d h)' % (horas, max_horas)


def evaluar(rep, base, activo, umbral, max_horas, hoy=None, ahora=None):
    """(chequeos, hallazgos, herramienta). Cada chequeo: (nombre, estado, motivo, categoria)."""
    hoy = hoy or datetime.date.today().isoformat()
    ahora = time.time() if ahora is None else ahora
    chequeos, secretos = [], False
    if isinstance(rep, dict) and 'SchemaVersion' in rep and 'ArtifactName' in rep:
        herramienta = 'trivy'
        if rep.get('SchemaVersion') != 2:
            return [('reporte', SIN_DATOS, 'esquema %s de Trivy: este script lee el 2' % limpio(rep.get('SchemaVersion'), 10), 'imagen')], [], herramienta
        if not rep.get('Results'):
            return [('reporte', SIN_DATOS, 'el reporte de Trivy no tiene resultados: no analizo nada', 'imagen')], [], herramienta
        version = version_de_trivy(base, rep)
        if version in TRIVY_COMPROMETIDAS:
            chequeos.append(('version de trivy', SIN_DATOS, 'Trivy %s es la version del incidente de marzo de 2026 (CVE-2026-33634): '
                             'su resultado no vale; la reinstala una persona con una version sana, fijada por hash (DEC-009)' % version, 'imagen'))
        hall, so, paquetes, secretos = de_trivy(rep, activo, hoy)
        chequeos.append(('base de vulnerabilidades',) + edad_trivy(rep, base, max_horas, ahora) + ('imagen',))
        if not paquetes:
            chequeos.append(('paquetes analizados', SIN_DATOS, 'el reporte no trae ningun resultado os-pkgs ni lang-pkgs: no analizo '
                             'paquetes, y cero vulnerabilidades sin paquetes no dice nada', 'imagen'))
    elif isinstance(rep, dict) and isinstance(rep.get('matches'), list) and (rep.get('descriptor') or {}).get('name') == 'grype':
        herramienta = 'grype'
        hall, so = de_grype(rep, activo, hoy)
        fecha, motivo_base = base_de_grype(rep)
        if fecha is None:
            chequeos.append(('base de vulnerabilidades', SIN_DATOS, motivo_base, 'imagen'))
        else:
            horas = int(round((ahora - fecha) / 3600.0))
            chequeos.append(('base de vulnerabilidades', SIN_DATOS, 'es de hace %d h (tope %d h): no conoce lo nuevo' % (horas, max_horas), 'imagen')
                            if horas > max_horas else ('base de vulnerabilidades', OK, 'de hace %d h (tope %d h)' % (max(horas, 0), max_horas), 'imagen'))
    else:
        return [('reporte', SIN_DATOS, 'no es un reporte JSON de Trivy ni de Grype', 'imagen')], [], '?'
    base_ok = all(e == OK for c, e, _, _ in chequeos if c == 'base de vulnerabilidades')

    sin_datos_extra = []
    if so is None:
        chequeos.append(('sistema operativo', OK, 'la imagen no trae sistema operativo detectado (sin sistema operativo: solo bibliotecas)', 'imagen'))
    elif so[1]:
        chequeos.append(('sistema operativo', HALLAZGO, '%s sin soporte: no recibe parches de seguridad' % limpio(so[0], 60), 'imagen'))
        hall.append(nuevo(herramienta, 'imagen', 'so-sin-soporte', 'el sistema operativo base no tiene soporte: %s' % so[0],
                          'ALTA', activo, archivo=so[0]))
        sin_datos_extra.append('el conteo de vulnerabilidades de %s: sin soporte, la base no registra las nuevas' % limpio(so[0], 60))
    elif not so[2]:
        chequeos.append(('sistema operativo', SIN_DATOS, 'detecto %s pero no analizo sus paquetes' % limpio(so[0], 60), 'imagen'))
    else:
        chequeos.append(('sistema operativo', OK, '%s, con soporte' % limpio(so[0], 60), 'imagen'))

    tope = NIVELES.index(umbral)
    vulns = [h for h in hall if h['categoria'] == 'imagen' and h['regla'] != 'so-sin-soporte']
    nuevas = [h for h in vulns if h['estado'] == 'nuevo']
    sobre = [h for h in nuevas if NIVELES.index(h['severidad']) >= tope]
    supr = len(vulns) - len(nuevas)
    caidas = sum(1 for h in hall if h['estado'] == 'nuevo' and h['motivo_supresion'])
    cuenta = '; %d por debajo del umbral' % (len(nuevas) - len(sobre)) + (
        '; %d suprimida(s) con motivo y vencimiento' % supr if supr else '') + (
        '; %d supresion(es) sin vencimiento vigente: no valen y cuentan' % caidas if caidas else '')
    if sobre:
        por = ', '.join('%d %s' % (sum(1 for h in sobre if h['severidad'] == n), n) for n in reversed(NIVELES)
                        if any(h['severidad'] == n for h in sobre))
        chequeos.append(('vulnerabilidades', HALLAZGO, '%d en el umbral %s o por encima (%s)%s' % (len(sobre), umbral, por, cuenta), 'imagen'))
    elif not base_ok:
        chequeos.append(('vulnerabilidades', SIN_DATOS, 'ninguna en el umbral %s, pero con la base sin datos eso no dice nada%s' % (umbral, cuenta), 'imagen'))
    else:
        chequeos.append(('vulnerabilidades', OK, 'ninguna en el umbral %s o por encima%s' % (umbral, cuenta), 'imagen'))
    for s in sin_datos_extra:
        chequeos.append(('conteo del sistema', SIN_DATOS, s, 'imagen'))
    if secretos:
        sec = [h for h in hall if h['categoria'] == 'secretos' and normalizar.bloqueante(h)]
        chequeos.append(('secretos en las capas', HALLAZGO if sec else OK,
                         '%d secreto(s) en las capas (regla, archivo y linea; nunca el valor)' % len(sec) if sec
                         else 'los secretos que encontro estan suprimidos con motivo y vencimiento', 'secretos'))
    return chequeos, hall, herramienta


def informe(chequeos, hall, herramienta):
    """El informe del esquema comun: el estado de cada categoria y el veredicto los decide el paquete."""
    inf = normalizar.nuevo_informe(ORIGEN)
    inf['no_mira'] = list(NO_MIRA)
    inf['hallazgos'] = hall
    for cat in ('imagen', 'secretos'):
        propios = [(c, e, m) for c, e, m, k in chequeos if k == cat]
        if not propios:
            continue
        normalizar.poner_categoria(inf, cat, [herramienta] if any(e != SIN_DATOS for _, e, _ in propios) else [],
                                   [m for _, e, m in propios if e == SIN_DATOS],
                                   '; '.join(m for _, e, m in propios if e == HALLAZGO))
    inf['chequeos'] = [{'chequeo': c, 'estado': NOMBRE[e], 'motivo': m} for c, e, m, _ in chequeos]
    return inf, normalizar.cerrar(inf)


def instalada(nombre):
    return shutil.which(nombre)


def ejecutar(orden, entorno=None):
    """(codigo, salida, error). codigo None si no se pudo ejecutar o no termino."""
    try:
        r = subprocess.run(orden, capture_output=True, text=True, encoding='utf-8', errors='replace', env=entorno, timeout=TOPE_SEGUNDOS)
    except (OSError, subprocess.SubprocessError) as e:
        return None, '', type(e).__name__
    return r.returncode, r.stdout, r.stderr


def revisar_orden(orden):
    """La lista negra: ValueError si la orden lleva una opcion prohibida o si la imagen podria venir del registro."""
    herramienta = os.path.basename(orden[0]).lower().replace('.exe', '')
    malas = [o for o in orden[1:] if o.split('=')[0] in PROHIBIDAS.get(herramienta, ())]
    if herramienta == 'trivy':
        for i, o in enumerate(orden):
            valor = o.split('=', 1)[1] if o.startswith('--image-src=') else orden[i + 1] if o == '--image-src' and i + 1 < len(orden) else None
            if valor is not None and 'remote' in valor.lower().split(','):
                malas.append('--image-src con remote (bajaria la imagen del registro)')
    if herramienta == 'grype' and len(orden) > 1 and not orden[1].startswith('docker:'):
        malas.append('%s (sin el esquema docker:, grype podria bajar la imagen del registro)' % orden[1][:40])
    if malas:
        raise ValueError('opcion prohibida para %s: %s' % (herramienta, ', '.join(malas)))


def correr_escaner(herramienta, destino, alias, raiz):
    """(reporte, base, guardado, motivo). reporte None si no hay reporte usable."""
    if not instalada(herramienta):
        return None, None, '', '%s no esta instalado en esta maquina' % herramienta
    carpeta = os.path.join(raiz, 'borrador', 'seguridad', '%s-%s' % (time.strftime('%Y%m%d'), saneado(alias)))
    base = None
    if herramienta == 'trivy':
        orden_base = ['trivy', 'version', '--format', 'json']
        revisar_orden(orden_base)
        rc, salida, _ = ejecutar(orden_base)
        try:
            base = json.loads(salida) if rc == 0 else None
        except ValueError:
            base = None
        version = version_de_trivy(base)
        if version in TRIVY_COMPROMETIDAS:
            return None, base, '', ('Trivy %s es la version del incidente de marzo de 2026 (CVE-2026-33634): no se escanea con ella; '
                                    'la reinstala una persona con una version sana, fijada por hash (DEC-009)' % version)
        orden = ['trivy', 'image', '--format', 'json', '--scanners', 'vuln,secret', '--image-src', FUENTES_LOCALES, '--skip-db-update',
                 '--skip-java-db-update', '--disable-telemetry', '--skip-version-check', '--quiet', destino]
        entorno = None
    else:
        if not instalada('docker'):
            return None, None, '', 'docker no esta instalado: grype lee la imagen del daemon local y este script no la baja del registro'
        rc, _, _ = ejecutar(['docker', 'image', 'inspect', '--format', '{{.Id}}', destino])
        if rc != 0:
            return None, None, '', ('la imagen de %s no esta en esta maquina (docker image inspect): este script nunca la baja del '
                                    'registro; la trae una persona, fijada por digest' % alias)
        orden = ['grype', 'docker:' + destino, '-o', 'json']
        entorno = dict(os.environ, GRYPE_DB_AUTO_UPDATE='false', GRYPE_CHECK_FOR_APP_UPDATE='false')
    revisar_orden(orden)
    rc, salida, _ = ejecutar(orden, entorno)
    if rc is None:
        return None, base, '', '%s no se pudo ejecutar o no termino' % herramienta
    try:
        rep = json.loads(salida) if salida.strip() else None
    except ValueError:
        rep = None
    if rep is None:
        return None, base, '', ('%s no devolvio un reporte JSON (salio con %s): si la imagen no esta en la maquina (docker, '
                                'containerd o podman), este script no la baja del registro' % (herramienta, rc))
    os.makedirs(carpeta, exist_ok=True)
    guardado = os.path.join(carpeta, '%s-imagen.json' % herramienta)
    with open(guardado, 'w', encoding='utf-8') as h:
        h.write(salida)
    if base is not None:
        with open(os.path.join(carpeta, 'trivy-base.json'), 'w', encoding='utf-8') as h:
            json.dump(base, h)
    return rep, base, guardado, ''


def main(argv=None):
    ap = argparse.ArgumentParser(description='El reporte de Trivy o de Grype de una imagen, normalizado (solo lectura).')
    ap.add_argument('--reporte', default='')
    ap.add_argument('--base', default='', help='Trivy: metadata.json del cache o la salida de "trivy version --format json"')
    ap.add_argument('--imagen', default='', help='alias de la imagen en el inventario')
    ap.add_argument('--correr', default='', choices=('', 'trivy', 'grype'))
    ap.add_argument('--umbral', default='ALTA', choices=UMBRALES)
    ap.add_argument('--max-horas-base', type=int, default=HORAS_BASE)
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    activo, destino = '', ''

    def sin_datos(motivo):
        if a.json:
            inf, _ = informe([('reporte', SIN_DATOS, motivo, 'imagen')], [], a.correr or '?')
            print(normalizar.a_json(inf))
        else:
            print('ESCANEO DE IMAGEN -- SIN DATOS: %s' % motivo)
        return SIN_DATOS

    if not a.reporte and not a.correr:
        return sin_datos('falta --reporte <json> (o --imagen <alias> --correr trivy|grype)')
    if a.reporte and a.correr:
        return sin_datos('--reporte y --correr juntos: se elige uno')
    if a.correr and not a.imagen:
        return sin_datos('--correr necesita --imagen <alias>: lo que se escanea sale del inventario')
    if a.imagen:
        ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
        estado, fila, motivo = (inventario.autorizar(ruta, a.imagen, 'N0') if ruta else (inventario.SIN_DATOS, None, motivo))
        if estado == inventario.OK and fila['tipo'] != 'imagen':
            estado, motivo = inventario.FRENA, '%s es de tipo %s: este script escanea un activo de tipo imagen' % (a.imagen, fila['tipo'] or '?')
        if estado != inventario.OK:
            if estado == inventario.SIN_DATOS:
                return sin_datos(motivo)
            if a.json:
                inf = normalizar.nuevo_informe(ORIGEN)
                inf.update(veredicto=normalizar.FRENA, motivo=motivo, no_mira=list(NO_MIRA))
                print(normalizar.a_json(inf))
            else:
                print('ESCANEO DE IMAGEN %s -- FRENA: %s' % (a.imagen, motivo))
            return HALLAZGO
        activo, destino = a.imagen, fila['destino']

    guardado, base = '', None
    if a.correr:
        if not DESTINO.match(destino):
            return sin_datos('el Destino de %s en el inventario no es una referencia de imagen usable' % activo)
        rep, base, guardado, motivo = correr_escaner(a.correr, destino, activo, os.path.abspath(a.raiz))
        if rep is None:
            return sin_datos(motivo)
    else:
        rep, motivo = leer_json(a.reporte, 'el reporte')
        if rep is None:
            return sin_datos(motivo)
        if a.base:
            base, motivo = leer_json(a.base, 'la base (--base)')
            if base is None:
                base = {}
    chequeos, hall, herramienta = evaluar(rep, base, activo, a.umbral, a.max_horas_base)
    inf, codigo = informe(chequeos, hall, herramienta)
    if guardado:
        inf['crudo'] = guardado
    if a.json:
        print(normalizar.a_json(inf))
        return codigo
    print('ESCANEO DE IMAGEN %s (%s) -- %s' % (activo or '(sin alias)', herramienta, inf['veredicto']))
    for c, e, m, _ in chequeos:
        print('  %-26s %s -- %s' % (c, NOMBRE[e], m))
    for cat in sorted(inf['categorias']):
        x = inf['categorias'][cat]
        print('  categoria %-16s %s%s' % (cat, x['estado'], (' -- ' + x['motivo']) if x['motivo'] else ''))
    tope = NIVELES.index(a.umbral)
    mostrar = sorted((h for h in hall if h['estado'] == 'nuevo' and NIVELES.index(h['severidad']) >= tope and h['regla'] != 'so-sin-soporte'),
                     key=lambda h: -NIVELES.index(h['severidad']))
    for h in mostrar[:25]:
        print('    - %-7s %s %s %s%s  %s' % (h['severidad'], h['regla'], h['paquete'], h['version'],
                                         (' -> ' + h['arreglo']) if h['arreglo'] else '', h['titulo'] if h['categoria'] != 'secretos'
                                         else 'secreto en %s, linea %d' % (h['archivo'], h['linea'])))
    if len(mostrar) > 25:
        print('    ... y %d mas (--json trae todos)' % (len(mostrar) - 25))
    if guardado:
        print('  Reporte crudo (no se versiona): %s' % guardado)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return codigo


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
