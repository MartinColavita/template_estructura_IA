#!/usr/bin/env python3
"""Priorizar los hallazgos de un informe normalizado: P1 a P4 con KEV, EPSS, la severidad y el activo. SOLO LECTURA.

    python -I bin/priorizar-vulnerabilidades.py --informe <json normalizado> [--epss-csv <f>] [--kev-json <f>] [--inventario <ruta>] [--json]
    opciones: --percentil <0..1> (umbral de EPSS para P2; 0.90 por defecto)   --max-dias <n> (antiguedad maxima de KEV y
              EPSS; 7 por defecto). Los dos numeros los fija DEC-009; mientras este en duda, son los de aca.

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS
  1 si hay alguna P1 o P2 (no suprimida); si no, 2 si alguna prioridad quedo SIN DATOS o el informe no midio todo
  (SIN DATOS o FRENA); 0 solo si todo esta priorizado y nada es P1 ni P2.

LA MATRIZ (los numeros se calibran en DEC-009; no es un estandar):
  P1  un secreto en el repositorio; o esta en KEV (la estan explotando); o CRITICA (se toma alcanzable)
  P2  ALTA. Con EPSS en el percentil del umbral o mas, o en un activo expuesto a internet o de criticidad alta, es
      P2 firme; si no, P2 "bajable" a P3, y bajarla exige la evidencia archivo:linea del VERIFICADOR de que no es
      alcanzable (nunca la del que produjo el cambio)
  P3  MEDIA; con EPSS en el percentil del umbral o mas, sube a P2 (DEC-009)      P4  BAJA o informativa
  Una severidad fuera del esquema (HIGH, critical, vacia) vale ALTA, como en el normalizador: nunca P4 por no
  entenderla.
  Linea de base: un hallazgo "en-linea-base" no frena el Merge Request (lo decide el escaneo), pero aca no es una
  amnistia: si es P1 o P2, este informe sigue saliendo HALLAZGO. Solo una supresion vigente lo saca.
  Una vulnerabilidad con CVE sin el catalogo KEV (o con uno viejo) queda SIN DATOS (podria estar siendo explotada),
  salvo la CRITICA, que ya es P1. Sin EPSS ni KEV, entonces, la prioridad es SIN DATOS: el hallazgo sigue siendo
  hallazgo. EPSS solo afina. Un hallazgo sin CVE (codigo, configuracion, prueba dinamica) va por su severidad.

POR QUE EXISTE. CVSS solo dice que tan grave es en teoria; KEV dice que ya la estan explotando y EPSS que tan probable
es que la exploten en 30 dias. Cruzarlos a mano con la exposicion de cada activo es un conteo, y lo hace un script.

QUE NO HACE. No baja nada: KEV y EPSS los baja una persona (el archivo diario completo, no CVE por CVE: asi no se le
cuenta a nadie que vulnerabilidades tenemos) y se los pasa por archivo. No fija plazos ni escribe el registro V-nnn
(eso es gestionar-vulnerabilidades). No decide si el codigo vulnerable se alcanza. Solo biblioteca estandar. ASCII puro.
"""

import argparse
import csv
import datetime
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario autorizado

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
ESTADOS = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
PRIORIDADES = ('P1', 'P2', 'P3', 'P4', 'SIN DATOS')
SEVERIDADES = ('CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO')
FECHA = re.compile(r'(\d{4}-\d{2}-\d{2})')
NO_MIRA = ('si el codigo vulnerable se alcanza: lo dice el verificador, con archivo:linea; sin esa evidencia ninguna ALTA baja a P3',
           'los plazos de cada prioridad y el registro V-nnn: DEC-009 y gestionar-vulnerabilidades',
           'si el parche rompe algo',
           'la exposicion real cuando el inventario esta mal o incompleto')


def fecha_de(texto):
    m = FECHA.search(str(texto or ''))
    try:
        return datetime.date(*[int(x) for x in m.group(1).split('-')]) if m else None
    except ValueError:
        return None


def fecha_archivo(ruta):
    return datetime.date.fromtimestamp(os.path.getmtime(ruta))


def fuente(ruta):
    return {'archivo': ruta or '', 'estado': 'SIN DATOS', 'fecha': '', 'motivo': ''}


def vigente(f, fecha, ruta, hoy, max_dias):
    """Pone la fecha del archivo y dice si esta dentro de la antiguedad maxima."""
    fecha = fecha or fecha_archivo(ruta)
    f['fecha'] = fecha.isoformat()
    dias = (hoy - fecha).days
    if dias > max_dias:
        f['motivo'] = 'tiene %d dias (maximo %d, DEC-009): vale como ausente' % (dias, max_dias)
        return False
    return True


def leer_kev(ruta, hoy, max_dias):
    """({cve: uso en ransomware}, fuente) o (None, fuente) si no hay catalogo vigente."""
    f = fuente(ruta)
    if not ruta:
        f['motivo'] = 'no se paso --kev-json'
        return None, f
    try:
        with open(ruta, 'rb') as h:
            d = json.loads(h.read().decode('utf-8', 'replace').lstrip(chr(0xFEFF)))
    except (OSError, ValueError) as e:
        f['motivo'] = 'no se pudo leer (%s)' % type(e).__name__
        return None, f
    vulns = d.get('vulnerabilities') if isinstance(d, dict) else None
    if not isinstance(vulns, list) or not vulns:
        f['motivo'] = 'no trae ninguna vulnerabilidad: no es el catalogo KEV'
        return None, f
    if not vigente(f, fecha_de(d.get('dateReleased')), ruta, hoy, max_dias):
        return None, f
    f['estado'] = 'OK'
    return dict((str(v.get('cveID', '')).upper(), str(v.get('knownRansomwareCampaignUse', '')).lower())
                for v in vulns if isinstance(v, dict) and v.get('cveID')), f


def leer_epss(ruta, hoy, max_dias):
    """({cve: (epss, percentil)}, fuente) o (None, fuente). Acepta el CSV diario, comprimido o no."""
    f = fuente(ruta)
    if not ruta:
        f['motivo'] = 'no se paso --epss-csv'
        return None, f
    try:
        with open(ruta, 'rb') as h:
            crudo = h.read()
        if crudo[:2] == b'\x1f\x8b':
            crudo = gzip.decompress(crudo)
    except (OSError, EOFError) as e:
        f['motivo'] = 'no se pudo leer (%s)' % type(e).__name__
        return None, f
    texto = crudo.decode('utf-8', 'replace').lstrip(chr(0xFEFF))
    m = re.search(r'score_date:(\d{4}-\d{2}-\d{2})', texto[:500])
    filas = list(csv.reader(x for x in texto.splitlines() if x.strip() and not x.startswith('#')))
    if not filas:
        f['motivo'] = 'esta vacio'
        return None, f
    cab = [c.strip().lower() for c in filas[0]]
    if not all(c in cab for c in ('cve', 'epss', 'percentile')):
        f['motivo'] = 'no tiene las columnas cve, epss y percentile'
        return None, f
    i, j, k = cab.index('cve'), cab.index('epss'), cab.index('percentile')
    datos = {}
    for fila in filas[1:]:
        try:
            datos[fila[i].strip().upper()] = (float(fila[j]), float(fila[k]))
        except (IndexError, ValueError):
            continue
    if not datos:
        f['motivo'] = 'no trae ninguna fila legible'
        return None, f
    if not vigente(f, fecha_de(m.group(1)) if m else None, ruta, hoy, max_dias):
        return None, f
    f['estado'] = 'OK'
    return datos, f


def leer_inventario(ruta):
    f = {'archivo': ruta or '', 'estado': 'SIN DATOS', 'motivo': ''}
    if not ruta:
        f['motivo'] = 'no se paso --inventario: la exposicion de cada activo queda SIN DATOS'
        return None, f
    activos, motivo = inventario.cargar(ruta)
    if activos is None:
        f['motivo'] = motivo
        return None, f
    f['estado'] = 'OK'
    return dict((x['alias'], x) for x in activos), f


def priorizar(h, kev, epss, activos, umbral):
    v = dict((k, h.get(k, '')) for k in ('huella', 'herramienta', 'categoria', 'regla', 'cve', 'severidad', 'estado',
                                          'activo', 'paquete', 'version', 'archivo'))
    v['linea'] = h.get('linea', 0)
    cve = str(h.get('cve') or '').upper()
    sev = h.get('severidad') if h.get('severidad') in SEVERIDADES else 'ALTA'
    v['severidad'] = sev
    v.update({'cve': cve, 'epss': None, 'percentil': None, 'kev': '', 'expuesto': '', 'criticidad': '', 'bajable': False})
    if cve:
        v['kev'] = 'SIN DATOS' if kev is None else 'si' if cve in kev else 'no'
        if epss is not None and cve in epss:
            v['epss'], v['percentil'] = epss[cve]
    nota = ''
    if h.get('activo'):
        a = (activos or {}).get(h['activo'])
        if a is None:
            v['expuesto'] = 'SIN DATOS'
            nota = '; el activo %s no esta en el inventario: su exposicion es SIN DATOS' % h['activo'] if activos is not None else ''
        else:
            v['expuesto'] = 'si' if a['expuesto'] is True else 'no' if a['expuesto'] is False else 'SIN DATOS'
            v['criticidad'] = a['criticidad']
    if h.get('categoria') == 'secretos':
        p, m = 'P1', 'un secreto en el repositorio: se rota, borrarlo no alcanza'
    elif cve and kev is not None and cve in kev:
        p, m = 'P1', 'esta en KEV: la estan explotando' + (' (usada en ransomware)' if kev[cve] == 'known' else '')
    elif sev == 'CRITICA':
        p, m = 'P1', 'CRITICA: se toma alcanzable hasta que el verificador muestre lo contrario' + (
            ' (falta KEV, que no podria subirla mas)' if cve and kev is None else '')
    elif cve and kev is None:
        p, m = 'SIN DATOS', 'falta el catalogo KEV vigente: podria estar siendo explotada'
    elif sev == 'ALTA':
        razones = []
        if v['percentil'] is not None and v['percentil'] >= umbral:
            razones.append('EPSS en el percentil %.2f (umbral %.2f)' % (v['percentil'], umbral))
        if v['expuesto'] == 'si':
            razones.append('el activo esta expuesto a internet')
        if v['criticidad'] == 'alta':
            razones.append('el activo es de criticidad alta')
        v['bajable'] = not razones and bool(cve) and v['percentil'] is not None and v['expuesto'] == 'no'
        p = 'P2'
        m = ('ALTA; ' + '; '.join(razones) if razones else
             'ALTA; bajable a P3 solo con la evidencia escrita del verificador de que no es alcanzable (EPSS bajo y activo no expuesto)'
             if v['bajable'] else 'ALTA; sin datos para bajarla (falta el EPSS o la exposicion del activo)' if cve
             else 'ALTA: frena; bajarla exige la evidencia escrita del verificador')
    elif sev == 'MEDIA' and v['percentil'] is not None and v['percentil'] >= umbral:
        p, m = 'P2', 'MEDIA con EPSS en el percentil %.2f (umbral %.2f): sube a P2 (DEC-009)' % (v['percentil'], umbral)
    elif sev == 'MEDIA':
        p, m = 'P3', 'MEDIA: no frena; plazo y registro'
    else:
        p, m = 'P4', 'BAJA o informativa: registro'
    if not cve and h.get('categoria') != 'secretos' and p != 'SIN DATOS':
        m += ' (sin CVE: KEV y EPSS no aplican, va por su severidad)'
    v['prioridad'], v['motivo'] = p, m + nota
    return v


def main():
    ap = argparse.ArgumentParser(description='Prioridad P1 a P4 de los hallazgos de un informe normalizado (solo lectura).', allow_abbrev=False)
    ap.add_argument('--informe', default='')
    ap.add_argument('--epss-csv', default='')
    ap.add_argument('--kev-json', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--percentil', type=float, default=0.90)
    ap.add_argument('--max-dias', type=int, default=7)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not a.informe:
        print('SIN DATOS -- falta --informe <json normalizado> (el que escriben escanear-seguridad.py, escanear-ambiente.py o escanear-imagenes.py).')
        return SIN_DATOS
    try:
        with open(a.informe, 'rb') as h:
            inf = json.loads(h.read().decode('utf-8', 'replace').lstrip(chr(0xFEFF)))
    except (OSError, ValueError) as e:
        print('SIN DATOS -- no se pudo leer el informe %s (%s).' % (a.informe, type(e).__name__))
        return SIN_DATOS
    if not isinstance(inf, dict) or not isinstance(inf.get('hallazgos'), list) or 'veredicto' not in inf:
        print('SIN DATOS -- %s no es un informe normalizado (le faltan "veredicto" o "hallazgos").' % a.informe)
        return SIN_DATOS
    hoy = datetime.date.today()
    kev, f_kev = leer_kev(a.kev_json, hoy, a.max_dias)
    epss, f_epss = leer_epss(a.epss_csv, hoy, a.max_dias)
    activos, f_inv = leer_inventario(a.inventario)
    vulns = [priorizar(h, kev, epss, activos, a.percentil) for h in inf['hallazgos'] if isinstance(h, dict)]
    vulns.sort(key=lambda v: (PRIORIDADES.index(v['prioridad']), v['cve'] or v['regla']))
    resumen = dict((p, sum(1 for v in vulns if v['prioridad'] == p)) for p in PRIORIDADES)
    frenan = [v for v in vulns if v['prioridad'] in ('P1', 'P2') and v['estado'] != 'suprimido']
    no_midio = inf.get('veredicto') in ('SIN DATOS', 'FRENA')
    codigo = HALLAZGO if frenan else SIN_DATOS if (resumen['SIN DATOS'] or no_midio) else OK
    aviso = ''
    if inf.get('veredicto') == 'FRENA':
        aviso = 'el informe es FRENA: el inventario no autorizo el activo y no hubo escaneo (%s)' % inf.get('motivo', '')
    elif inf.get('veredicto') == 'SIN DATOS':
        aviso = 'el informe es SIN DATOS: no midio todo, y lo que no midio no tiene prioridad'
    if a.json:
        print(json.dumps({'estado': ESTADOS[codigo], 'informe': a.informe, 'veredicto_del_informe': inf.get('veredicto'),
                          'aviso': aviso, 'fuentes': {'kev': f_kev, 'epss': f_epss, 'inventario': f_inv},
                          'vulnerabilidades': vulns, 'resumen': resumen, 'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        return codigo
    print('PRIORIZAR VULNERABILIDADES -- %s  [%d hallazgo(s) de %s; KEV: %s; EPSS: %s; inventario: %s]' % (
        ESTADOS[codigo], len(vulns), os.path.basename(a.informe),
        *['%s%s' % (f['estado'], (' ' + f['fecha']) if f.get('fecha') else (' (%s)' % f['motivo']) if f['motivo'] else '')
          for f in (f_kev, f_epss, f_inv)]))
    if aviso:
        print('  aviso: ' + aviso)
    for v in vulns[:60]:
        print('  %-9s %-7s %-8s %s %s%s -- %s%s' % (
            v['prioridad'], v['severidad'], v['categoria'], v['cve'] or v['regla'],
            (v['paquete'] + ' ' + v['version']).strip() or v['archivo'], (' [' + v['activo'] + ']') if v['activo'] else '',
            v['motivo'], ' (suprimido)' if v['estado'] == 'suprimido' else ''))
    print('  Resumen: ' + '; '.join('%s %d' % (p, resumen[p]) for p in PRIORIDADES))
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
