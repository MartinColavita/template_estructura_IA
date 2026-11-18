#!/usr/bin/env python3
"""Prueba de bin/priorizar-vulnerabilidades.py sobre informes, catalogos KEV y archivos EPSS de mentira.
Se corre:  python -B bin/probar-priorizar-vulnerabilidades.py   -> OK o FALLA, con el detalle de cada caso.
Sin red: el script nunca baja nada, y la prueba le pasa los archivos que bajaria una persona."""

import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'priorizar-vulnerabilidades.py')
ESPERADOS = []
HOY = datetime.date.today()
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `img-expuesta` | imagen | produccion | `registro/app:1` | si | media | N0 | no | | producto |\n'
         '| `img-interna` | imagen | prueba | `registro/app:2` | no | baja | N0 | no | | producto |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:500]) if (detalle and not ok) else ''))


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(datos if isinstance(datos, bytes) else datos.encode('utf-8'))
    return ruta


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def json_de(texto):
    try:
        return json.loads(texto)
    except ValueError:
        return {}


def hallazgo(**kw):
    h = dict((k, '') for k in ('herramienta', 'categoria', 'regla', 'titulo', 'cwe', 'cve', 'severidad', 'archivo', 'paquete',
                               'version', 'arreglo', 'activo', 'huella', 'motivo_supresion', 'vence'))
    h.update({'linea': 0, 'estado': 'nuevo', 'herramienta': 'osv-scanner', 'categoria': 'sca'})
    h.update(kw)
    h['huella'] = h['huella'] or (h['cve'] or h['regla']) + '-' + h['activo']
    return h


def informe(tmp, nombre, hallazgos, veredicto='HALLAZGO'):
    return escribir(os.path.join(tmp, nombre), json.dumps({
        'veredicto': veredicto, 'origen': 'escanear-seguridad', 'generado': HOY.isoformat() + 'T10:00:00',
        'categorias': {'sca': {'estado': veredicto, 'herramienta': 'osv-scanner', 'motivo': ''}},
        'hallazgos': hallazgos, 'sin_datos': [], 'no_mira': []}))


def kev(tmp, nombre, cves, fecha=None):
    return escribir(os.path.join(tmp, nombre), json.dumps({
        'title': 'catalogo de prueba', 'catalogVersion': '2026.11.16', 'dateReleased': (fecha or HOY).isoformat() + 'T12:00:00.000Z',
        'count': len(cves), 'vulnerabilities': [{'cveID': c, 'vendorProject': 'x', 'product': 'y', 'vulnerabilityName': 'z',
                                                 'dateAdded': '2026-01-01', 'shortDescription': 'd', 'requiredAction': 'a',
                                                 'dueDate': '2026-02-01', 'knownRansomwareCampaignUse': 'Unknown'} for c in cves]}))


def epss(tmp, nombre, filas, fecha=None, comprimir=False):
    texto = '#model_version:v2025.03.14,score_date:%sT00:00:00+0000\ncve,epss,percentile\n' % (fecha or HOY).isoformat()
    texto += ''.join('%s,%s,%s\n' % f for f in filas)
    datos = gzip.compress(texto.encode('utf-8')) if comprimir else texto
    return escribir(os.path.join(tmp, nombre), datos)


def prioridades(out):
    d = json_de(out)
    return dict((v.get('cve') or v.get('regla'), v.get('prioridad')) for v in d.get('vulnerabilidades', [])), d


def main():
    print('== priorizar-vulnerabilidades')
    tmp = tempfile.mkdtemp(prefix='probar-prio-')
    k_log4 = kev(tmp, 'kev.json', ['CVE-2021-44228'])
    e = epss(tmp, 'epss.csv', [('CVE-2021-44228', '0.97', '0.99999'), ('CVE-2026-0002', '0.40', '0.95'),
                               ('CVE-2026-0003', '0.001', '0.10'), ('CVE-2026-0004', '0.001', '0.10')])

    rc, out = correr()
    caso('sin --informe: SIN DATOS (2)', rc == 2, out[:200])
    rc, out = correr('--informe', os.path.join(tmp, 'no.json'))
    caso('informe que no existe: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:200])
    rc, out = correr('--informe', escribir(os.path.join(tmp, 'roto.json'), 'no es json'))
    caso('informe ilegible: SIN DATOS (2)', rc == 2, out[:200])
    rc, out = correr('--informe', escribir(os.path.join(tmp, 'otro.json'), '{"cosa": 1}'))
    caso('un JSON que no es un informe normalizado: SIN DATOS (2)', rc == 2, out[:200])

    alta_kev = informe(tmp, 'i1.json', [hallazgo(cve='CVE-2021-44228', severidad='ALTA', paquete='log4j-core', version='2.14.1')])
    rc, out = correr('--informe', alta_kev, '--kev-json', k_log4, '--epss-csv', e)
    caso('una ALTA que esta en KEV: P1 y HALLAZGO (1)', rc == 1 and out.startswith('PRIORIZAR VULNERABILIDADES -- HALLAZGO') and 'P1' in out, out[:400])
    caso('el texto termina con lo que NO mira', 'Lo que este script NO mira' in out)
    rc, out = correr('--informe', alta_kev, '--kev-json', k_log4, '--epss-csv', e, '--json')
    p, d = prioridades(out)
    v = (d.get('vulnerabilidades') or [{}])[0]
    caso('--json: prioridad, KEV si, EPSS y percentil del archivo', p == {'CVE-2021-44228': 'P1'} and v.get('kev') == 'si'
         and abs((v.get('epss') or 0) - 0.97) < 1e-9 and abs((v.get('percentil') or 0) - 0.99999) < 1e-9, v)
    caso('--json: las fuentes con su fecha y estado', d.get('fuentes', {}).get('kev', {}).get('estado') == 'OK'
         and d.get('fuentes', {}).get('epss', {}).get('fecha') == HOY.isoformat(), d.get('fuentes'))
    caso('--json es ASCII', all(ord(c) < 128 for c in out))

    varios = informe(tmp, 'i2.json', [hallazgo(cve='CVE-2026-0002', severidad='ALTA'), hallazgo(cve='CVE-2026-0003', severidad='MEDIA'),
                                      hallazgo(cve='CVE-2026-0004', severidad='BAJA'), hallazgo(cve='CVE-2026-0005', severidad='CRITICA')])
    p, d = prioridades(correr('--informe', varios, '--kev-json', k_log4, '--epss-csv', e, '--json')[1])
    caso('ALTA con EPSS alto -> P2; MEDIA -> P3; BAJA -> P4; CRITICA -> P1',
         p == {'CVE-2026-0002': 'P2', 'CVE-2026-0003': 'P3', 'CVE-2026-0004': 'P4', 'CVE-2026-0005': 'P1'}, p)
    motivo = [x.get('motivo', '') for x in d.get('vulnerabilidades', []) if x.get('cve') == 'CVE-2026-0002']
    caso('el motivo de la P2 nombra el EPSS', motivo and 'EPSS' in motivo[0], motivo)

    bajas = informe(tmp, 'i3.json', [hallazgo(cve='CVE-2026-0003', severidad='MEDIA'), hallazgo(cve='CVE-2026-0004', severidad='BAJA')], 'OK')
    rc, out = correr('--informe', bajas, '--kev-json', k_log4, '--epss-csv', e)
    caso('solo P3 y P4: OK (0)', rc == 0 and out.startswith('PRIORIZAR VULNERABILIDADES -- OK'), out[:300])

    rc, out = correr('--informe', alta_kev, '--json')
    p, d = prioridades(out)
    caso('sin EPSS ni KEV: la prioridad queda SIN DATOS (2) y el hallazgo sigue listado',
         rc == 2 and p == {'CVE-2021-44228': 'SIN DATOS'} and len(d.get('vulnerabilidades', [])) == 1, out[:400])
    p, d = prioridades(correr('--informe', varios, '--epss-csv', e, '--json')[1])
    caso('con EPSS pero sin KEV: la CRITICA es P1 (KEV no puede subirla), el resto SIN DATOS',
         p == {'CVE-2026-0002': 'SIN DATOS', 'CVE-2026-0003': 'SIN DATOS', 'CVE-2026-0004': 'SIN DATOS', 'CVE-2026-0005': 'P1'}, p)
    p, d = prioridades(correr('--informe', bajas, '--kev-json', k_log4, '--json')[1])
    caso('con KEV y sin EPSS: se prioriza igual (EPSS solo afina)', p == {'CVE-2026-0003': 'P3', 'CVE-2026-0004': 'P4'}, p)

    viejo = kev(tmp, 'kev-viejo.json', ['CVE-2021-44228'], HOY - datetime.timedelta(days=30))
    rc, out = correr('--informe', alta_kev, '--kev-json', viejo, '--epss-csv', e, '--json')
    p, d = prioridades(out)
    caso('un KEV de hace 30 dias vale como ausente: SIN DATOS, y dice que es viejo',
         p == {'CVE-2021-44228': 'SIN DATOS'} and 'dias' in d.get('fuentes', {}).get('kev', {}).get('motivo', ''), d.get('fuentes'))
    rc, out = correr('--informe', alta_kev, '--kev-json', viejo, '--epss-csv', e, '--max-dias', '40', '--json')
    caso('--max-dias lo ajusta (el numero lo fija DEC-009)', prioridades(out)[0] == {'CVE-2021-44228': 'P1'}, out[:300])
    rc, out = correr('--informe', alta_kev, '--kev-json', escribir(os.path.join(tmp, 'kev-roto.json'), 'x'), '--json')
    caso('un KEV ilegible vale como ausente: SIN DATOS', prioridades(out)[0] == {'CVE-2021-44228': 'SIN DATOS'}, out[:300])

    gz = epss(tmp, 'epss.csv.gz', [('CVE-2026-0002', '0.40', '0.95')], comprimir=True)
    p, d = prioridades(correr('--informe', varios, '--kev-json', k_log4, '--epss-csv', gz, '--json')[1])
    caso('el EPSS comprimido (.gz, como se publica) se lee igual', p.get('CVE-2026-0002') == 'P2', p)
    vacio = escribir(os.path.join(tmp, 'epss-vacio.csv'), '')
    rc, out = correr('--informe', varios, '--kev-json', k_log4, '--epss-csv', vacio, '--json')
    caso('un EPSS vacio: SIN DATOS en la fuente, no "probabilidad cero"',
         json_de(out).get('fuentes', {}).get('epss', {}).get('estado') == 'SIN DATOS', json_de(out).get('fuentes'))

    sec = informe(tmp, 'i4.json', [hallazgo(categoria='secretos', herramienta='gitleaks', regla='aws-access-token', severidad='ALTA',
                                            archivo='config/app.env', linea=4)])
    rc, out = correr('--informe', sec, '--json')
    p, d = prioridades(out)
    caso('un secreto es P1 aunque no haya KEV ni EPSS (se rota)', rc == 1 and p == {'aws-access-token': 'P1'}, out[:300])
    sast = informe(tmp, 'i5.json', [hallazgo(categoria='sast', herramienta='semgrep', regla='py.eval', severidad='MEDIA')])
    p, d = prioridades(correr('--informe', sast, '--json')[1])
    caso('un hallazgo sin CVE se prioriza por su severidad (KEV y EPSS no aplican)', p == {'py.eval': 'P3'}, p)

    inv = escribir(os.path.join(tmp, 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)
    exp = informe(tmp, 'i6.json', [hallazgo(cve='CVE-2026-0003', severidad='ALTA', activo='img-expuesta', categoria='imagen'),
                                   hallazgo(cve='CVE-2026-0004', severidad='ALTA', activo='img-interna', categoria='imagen'),
                                   hallazgo(cve='CVE-2026-0006', severidad='ALTA', activo='img-fantasma', categoria='imagen')])
    rc, out = correr('--informe', exp, '--kev-json', k_log4, '--epss-csv', e, '--inventario', inv, '--json')
    d = json_de(out)
    por = dict((v.get('activo'), v) for v in d.get('vulnerabilidades', []))
    caso('ALTA en un activo expuesto a internet: P2 y el motivo lo dice',
         por.get('img-expuesta', {}).get('prioridad') == 'P2' and 'expuesto' in por.get('img-expuesta', {}).get('motivo', ''), por.get('img-expuesta'))
    caso('ALTA con EPSS bajo en un activo no expuesto: P2, bajable a P3 solo con evidencia del verificador',
         por.get('img-interna', {}).get('prioridad') == 'P2' and por.get('img-interna', {}).get('bajable') is True, por.get('img-interna'))
    caso('un activo que no esta en el inventario: exposicion SIN DATOS y no se marca bajable',
         por.get('img-fantasma', {}).get('expuesto') == 'SIN DATOS' and por.get('img-fantasma', {}).get('bajable') is False, por.get('img-fantasma'))

    rc, out = correr('--informe', informe(tmp, 'i7.json', [], 'OK'), '--kev-json', k_log4)
    caso('un informe OK sin hallazgos: nada que priorizar, OK (0)', rc == 0, out[:200])
    rc, out = correr('--informe', informe(tmp, 'i8.json', [], 'SIN DATOS'), '--kev-json', k_log4)
    caso('un informe SIN DATOS sin hallazgos: SIN DATOS (2), no OK', rc == 2, out[:200])
    frena = escribir(os.path.join(tmp, 'i10.json'), json.dumps({
        'veredicto': 'FRENA', 'origen': 'escanear-imagenes', 'generado': HOY.isoformat() + 'T10:00:00', 'categorias': {},
        'hallazgos': [], 'sin_datos': [], 'no_mira': [], 'motivo': 'img-x no esta en el inventario autorizado'}))
    rc, out = correr('--informe', frena, '--kev-json', k_log4, '--json')
    caso('un informe FRENA (el inventario no autorizo el activo): SIN DATOS (2), no hubo escaneo',
         rc == 2 and json_de(out).get('estado') == 'SIN DATOS' and 'FRENA' in json.dumps(json_de(out)), out[:300])
    con_mas = json.loads(open(alta_kev, encoding='utf-8').read())
    con_mas.update({'chequeos': [{'x': 1}], 'motivo': '', 'crudo': 'borrador/seguridad/x', 'indice_lynis': 71})
    rc, out = correr('--informe', escribir(os.path.join(tmp, 'i11.json'), json.dumps(con_mas)), '--kev-json', k_log4, '--json')
    caso('claves de mas en la raiz del informe (chequeos, motivo, crudo, indice_lynis): se ignoran sin fallar',
         rc == 1 and prioridades(out)[0] == {'CVE-2021-44228': 'P1'}, out[:300])
    rc, out = correr('--informe', informe(tmp, 'i9.json', [hallazgo(cve='CVE-2021-44228', severidad='ALTA', estado='suprimido')], 'OK'),
                     '--kev-json', k_log4, '--epss-csv', e)
    caso('una P1 suprimida (con motivo y vencimiento vigentes) no frena: OK (0)', rc == 0, out[:300])

    # --- F2: severidad fuera del esquema, linea de base y MEDIA con EPSS alto
    raras = informe(tmp, 'i12.json', [hallazgo(regla='r-high', categoria='sast', herramienta='x', severidad='HIGH'),
                                      hallazgo(regla='r-crit', categoria='sast', herramienta='x', severidad='critical')])
    rc, out = correr('--informe', raras, '--json')
    p, d = prioridades(out)
    caso('una severidad fuera del esquema (HIGH, critical) vale ALTA: P2 y HALLAZGO, no P4',
         rc == 1 and p == {'r-high': 'P2', 'r-crit': 'P2'}, out[:400])
    base = informe(tmp, 'i13.json', [hallazgo(cve='CVE-2021-44228', severidad='ALTA', estado='en-linea-base')], 'OK')
    rc, out = correr('--informe', base, '--kev-json', k_log4, '--epss-csv', e, '--json')
    caso('una P1 en linea de base sigue siendo HALLAZGO en el informe de prioridades (no es una amnistia)',
         rc == 1 and prioridades(out)[0] == {'CVE-2021-44228': 'P1'}, out[:300])
    medias = informe(tmp, 'i14.json', [hallazgo(cve='CVE-2026-0002', severidad='MEDIA'), hallazgo(cve='CVE-2026-0003', severidad='MEDIA')], 'OK')
    rc, out = correr('--informe', medias, '--kev-json', k_log4, '--epss-csv', e, '--json')
    p, d = prioridades(out)
    caso('una MEDIA con EPSS en el percentil del umbral o mas sube a P2 (DEC-009); con EPSS bajo queda P3',
         rc == 1 and p == {'CVE-2026-0002': 'P2', 'CVE-2026-0003': 'P3'}, p)
    rc, out = correr('--informe', medias, '--kev-json', k_log4, '--epss-csv', e, '--percentil', '0.96', '--json')
    caso('el umbral de EPSS va por --percentil: con 0.96, la MEDIA de percentil 0.95 queda P3',
         prioridades(out)[0].get('CVE-2026-0002') == 'P3', out[:300])

    fuente = open(SCRIPT, 'rb').read() if os.path.isfile(SCRIPT) else b'\xff'
    caso('priorizar-vulnerabilidades.py es ASCII puro', all(b < 128 for b in fuente))
    caso('el script no puede bajar nada: no importa urllib, http ni socket',
         not any(x in fuente for x in (b'import urllib', b'from urllib', b'import http', b'from http', b'import socket')))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
