#!/usr/bin/env python3
"""Arnes de PARIDAD: graba lo que contesta la aplicacion VIEJA (el oraculo) y lo compara con lo que contesta la NUEVA.

    python bin/paridad.py grabar   --corpus <corpus.json> --oraculo <http://127.0.0.1:8080 | cmd:<comando>> --salida <golden.json>
    python bin/paridad.py comparar --corpus <corpus.json> --golden <golden.json> --nuevo <http://127.0.0.1:9090 | cmd:<comando>>
                                   [--volatil <camino> ...] [--aceptadas <aceptadas.json>] [--json] [--informe <salida.md>]
    python bin/paridad.py verificar --golden <golden.json> [--corpus <corpus.json>]
    python bin/paridad.py verificar --resultado <resultado.json>        (el JSON que escribio `comparar --json`)

Tres estados, nunca dos:  0 = OK (paridad: ninguna diferencia sin aceptar)   1 = HALLAZGO (hay diferencias)   2 = SIN DATOS

POR QUE EXISTE. En un refactor o una migracion, "quedo igual" es una opinion hasta que algo lo mide. Esto fija
el comportamiento de la aplicacion vieja (test de caracterizacion: el golden) y lo reproduce contra la nueva,
caso por caso, con la diferencia exacta (camino JSON, valor viejo, valor nuevo). Es la red que exige
refactor-y-migracion.md antes de tocar nada, y la prueba que pide mapa-modernizacion.py antes de cortar trafico.

EL CORPUS (lo escribe la skill con una persona; bin/armar-corpus.py arma el esqueleto desde la radiografia):
  {"slice": "reservas", "casos": [
     {"id": "RC-01", "nombre": "listar reservas", "regla": "RN-RES-003", "tipo": "http",
      "metodo": "GET", "ruta": "/reservas?desde=2026-01-01", "cabeceras": {}, "cuerpo": null, "muta": false},
     {"id": "RC-02", "nombre": "cli calcula precio", "tipo": "cmd", "args": ["precio", "--dias", "3"], "entrada": ""}
  ]}
  Un caso "muta": true (POST/PUT/PATCH/DELETE o un comando que escribe) NO se corre salvo --permitir-mutaciones:
  la grabacion tiene que hacerse sobre datos de prueba recien sembrados, y eso lo decide una persona.
  Sin PHI: los casos y las respuestas grabadas se versionan; si una respuesta trae algo que parece un dato de
  persona (correo, documento largo), el script lo AVISA y no lo tapa: se arregla el caso o los datos de prueba.

EL GOLDEN lo escribe SOLO este script y lo firma (sha256 del contenido). Un golden editado a mano, o escrito por
un modelo, no verifica: la evidencia no se fabrica. `verificar` lo comprueba y `comparar` frena si no verifica.
EL RESULTADO de `comparar --json` tambien va firmado y guarda que se ignoro (--volatil) y quien acepto que: es lo
que mapa-modernizacion.py corte verifica antes de dejar cortar trafico. Un resultado escrito a mano no verifica.

LAS DIFERENCIAS se clasifican fuera del script: un campo VOLATIL (fecha, id generado) se declara con --volatil
(el camino JSON completo, tipo /0/fecha; un nombre de campo suelto tapa ese campo a cualquier profundidad y se
registra igual en el resultado); un cambio INTENCIONAL se acepta en aceptadas.json, con quien lo
aprobo:  {"RC-01": [{"camino": "/precio", "aprobado_por": "<persona>", "fecha": "2026-11-03", "motivo": "..."}]}
Una aceptada sin "aprobado_por", o aprobada por un agente (Claude, Gemini, "modelo", "IA"), no vale: es HALLAZGO igual
(nadie se aprueba a si mismo, y un modelo tampoco).

QUE NO HACE. No arranca ni para ninguna aplicacion, no siembra datos, no habla con hosts que no sean locales
salvo --permitir-remoto, no toca la aplicacion vieja. Solo biblioteca estandar. ASCII en el codigo.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
FIRMA_SAL = 'paridad.py/v1'
AGENTE = re.compile(r'(?i)\bclaude\b|\bgemini\b|\bagente\b|\bmodelo\b|\bia\b|\bllm\b|\bgpt\b|\bcodex\b|\bcopilot\b')
SOSPECHA_PHI = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+|\b\d{7,11}\b')


def leer_json(p):
    with open(p, 'r', encoding='utf-8-sig') as h:
        return json.load(h)


def escribir_json(p, d):
    os.makedirs(os.path.dirname(os.path.abspath(p)) or '.', exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        json.dump(d, h, ensure_ascii=False, indent=1, sort_keys=True)
        h.write('\n')


def canonico(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def firmar(casos, oraculo, corpus_hash):
    return hashlib.sha256((FIRMA_SAL + canonico(casos) + oraculo + corpus_hash).encode('utf-8')).hexdigest()


def firmar_resultado(d):
    sin = {k: v for k, v in d.items() if k != 'firma'}
    return hashlib.sha256((FIRMA_SAL + '/resultado' + canonico(sin)).encode('utf-8')).hexdigest()


def hash_corpus(corpus):
    return hashlib.sha256(canonico(corpus).encode('utf-8')).hexdigest()


def es_local(url):
    m = re.match(r'https?://([^/:]+)', url)
    return bool(m) and m.group(1) in ('127.0.0.1', 'localhost', '::1', '[::1]')


def correr_caso(destino, caso, permitir_remoto):
    """Devuelve (respuesta, error). respuesta = {estado, tipo, cuerpo}."""
    tipo = caso.get('tipo', 'http')
    if destino.startswith('cmd:'):
        # en Windows las barras de las rutas no son escapes: se doblan antes de partir
        base = shlex.split(destino[4:].replace('\\', '\\' + '\\') if os.name == 'nt' else destino[4:])
        if tipo != 'cmd':
            return None, 'el caso %s es http y el destino es un comando' % caso.get('id')
        try:
            r = subprocess.run(base + [str(x) for x in caso.get('args', [])], input=caso.get('entrada', '') or '',
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            return None, 'no pude correr el comando: %s' % e
        salida = (r.stdout or '').rstrip()
        try:
            cuerpo, t = json.loads(salida), 'json'
        except ValueError:
            cuerpo, t = salida, 'text'
        return {'estado': r.returncode, 'tipo': t, 'cuerpo': cuerpo}, None
    if tipo != 'http':
        return None, 'el caso %s es cmd y el destino es http' % caso.get('id')
    if not es_local(destino) and not permitir_remoto:
        return None, 'el destino %s no es local; para hablar con otro host hace falta --permitir-remoto' % destino
    url = destino.rstrip('/') + caso.get('ruta', '/')
    datos = caso.get('cuerpo')
    cab = {'Accept': 'application/json'}
    cab.update(caso.get('cabeceras') or {})
    cuerpo_bytes = None
    if datos is not None:
        cuerpo_bytes = (datos if isinstance(datos, str) else json.dumps(datos)).encode('utf-8')
        cab.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(url, data=cuerpo_bytes, method=caso.get('metodo', 'GET').upper(), headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            estado, ctype, raw = resp.status, resp.headers.get('Content-Type', ''), resp.read()
    except urllib.error.HTTPError as e:
        estado, ctype, raw = e.code, e.headers.get('Content-Type', '') if e.headers else '', e.read()
    except (urllib.error.URLError, OSError) as e:
        return None, 'no pude hablar con %s: %s' % (url, e)
    texto = raw.decode('utf-8', errors='replace')
    tipo_corto = (ctype.split(';')[0].strip().lower() or 'text')
    if 'json' in tipo_corto:
        try:
            cuerpo = json.loads(texto) if texto.strip() else None
        except ValueError:
            cuerpo = texto
    else:
        cuerpo = texto.rstrip()
    return {'estado': estado, 'tipo': tipo_corto, 'cuerpo': cuerpo}, None


def diferencias(viejo, nuevo, camino, volatiles, salida):
    """Diff recursivo con tipos estrictos (1982 != "1982"). Camino tipo JSON Pointer."""
    nombre = camino.rsplit('/', 1)[-1]
    if camino in volatiles or (nombre and nombre in volatiles):
        return
    if type(viejo) != type(nuevo):
        salida.append({'camino': camino or '/', 'viejo': viejo, 'nuevo': nuevo, 'que': 'tipo distinto'})
        return
    if isinstance(viejo, dict):
        for k in sorted(set(viejo) | set(nuevo)):
            if k not in nuevo:
                salida.append({'camino': camino + '/' + k, 'viejo': viejo[k], 'nuevo': None, 'que': 'falta en la nueva'})
            elif k not in viejo:
                salida.append({'camino': camino + '/' + k, 'viejo': None, 'nuevo': nuevo[k], 'que': 'sobra en la nueva'})
            else:
                diferencias(viejo[k], nuevo[k], camino + '/' + k, volatiles, salida)
    elif isinstance(viejo, list):
        if len(viejo) != len(nuevo):
            salida.append({'camino': camino or '/', 'viejo': len(viejo), 'nuevo': len(nuevo), 'que': 'largo distinto'})
        for i, (a, b) in enumerate(zip(viejo, nuevo)):
            diferencias(a, b, camino + '/' + str(i), volatiles, salida)
    elif viejo != nuevo:
        salida.append({'camino': camino or '/', 'viejo': viejo, 'nuevo': nuevo, 'que': 'valor distinto'})


def avisos_phi(resp):
    texto = canonico(resp.get('cuerpo'))
    return sorted(set(m.group(0)[:6] + '...' for m in SOSPECHA_PHI.finditer(texto)))[:5]


def cargar_corpus(p):
    c = leer_json(p)
    casos = c.get('casos') or []
    ids = [x.get('id') for x in casos]
    if not casos:
        return None, 'el corpus no tiene casos'
    if len(set(ids)) != len(ids) or not all(ids):
        return None, 'los ids del corpus tienen que ser unicos y no vacios'
    return c, None


def grabar(a):
    corpus, err = cargar_corpus(a.corpus)
    if err:
        print('SIN DATOS -- ' + err); return SIN_DATOS
    casos, saltados, avisos = {}, [], []
    for caso in corpus['casos']:
        if caso.get('muta') and not a.permitir_mutaciones:
            saltados.append(caso['id']); continue
        resp, e = correr_caso(a.oraculo, caso, a.permitir_remoto)
        if e:
            print('SIN DATOS -- caso %s: %s' % (caso['id'], e)); return SIN_DATOS
        casos[caso['id']] = resp
        for s in avisos_phi(resp):
            avisos.append('%s: la respuesta trae algo que parece un dato de persona (%s)' % (caso['id'], s))
    if not casos:
        print('SIN DATOS -- no se grabo ningun caso (todos mutan y no se paso --permitir-mutaciones)'); return SIN_DATOS
    ch = hash_corpus(corpus)
    golden = {'grabado_por': 'bin/paridad.py', 'version': 1, 'fecha': datetime.date.today().isoformat(),
              'oraculo': a.oraculo, 'slice': corpus.get('slice', ''), 'corpus_sha256': ch, 'casos': casos,
              'firma': firmar(casos, a.oraculo, ch)}
    escribir_json(a.salida, golden)
    print('OK -- golden grabado en %s: %d caso(s) del oraculo %s%s' % (a.salida, len(casos), a.oraculo,
          ('; %d saltado(s) porque mutan: %s' % (len(saltados), ', '.join(saltados))) if saltados else ''))
    for v in avisos:
        print('  AVISO ' + v)
    return OK


def verificar_golden(p, corpus_path=None):
    try:
        g = leer_json(p)
    except (OSError, ValueError) as e:
        return None, 'no pude leer el golden: %s' % e
    if g.get('grabado_por') != 'bin/paridad.py' or 'firma' not in g:
        return None, 'el golden no lo escribio bin/paridad.py (sin firma): no es evidencia'
    if g['firma'] != firmar(g.get('casos', {}), g.get('oraculo', ''), g.get('corpus_sha256', '')):
        return None, 'la firma del golden NO verifica: fue editado despues de grabarlo'
    if corpus_path:
        corpus, err = cargar_corpus(corpus_path)
        if err:
            return None, err
        if hash_corpus(corpus) != g.get('corpus_sha256'):
            return None, 'el golden se grabo con OTRO corpus (cambio el corpus despues): hay que volver a grabar'
    return g, None


def comparar(a):
    corpus, err = cargar_corpus(a.corpus)
    if err:
        print('SIN DATOS -- ' + err); return SIN_DATOS
    golden, err = verificar_golden(a.golden, a.corpus)
    if err:
        print('SIN DATOS -- ' + err); return SIN_DATOS
    aceptadas = {}
    if a.aceptadas:
        try:
            aceptadas = leer_json(a.aceptadas)
        except (OSError, ValueError) as e:
            print('SIN DATOS -- no pude leer las aceptadas: %s' % e); return SIN_DATOS
    volatiles = set(a.volatil or [])
    if any(not v.strip() for v in volatiles):
        print('SIN DATOS -- un --volatil vacio taparia el cuerpo entero: se declara el camino completo (/0/fecha)'); return SIN_DATOS
    filas, hallazgos, iguales, sin_aprobar = [], 0, 0, []
    for caso in corpus['casos']:
        cid = caso['id']
        if cid not in golden['casos']:
            filas.append({'id': cid, 'resultado': 'SIN DATOS', 'detalle': 'no esta en el golden (muta y no se grabo)'}); continue
        resp, e = correr_caso(a.nuevo, caso, a.permitir_remoto)
        if e:
            print('SIN DATOS -- caso %s contra la nueva: %s' % (cid, e)); return SIN_DATOS
        viejo = golden['casos'][cid]
        difs = []
        if viejo['estado'] != resp['estado']:
            difs.append({'camino': '/estado', 'viejo': viejo['estado'], 'nuevo': resp['estado'], 'que': 'estado distinto'})
        if viejo['tipo'] != resp['tipo']:
            difs.append({'camino': '/tipo', 'viejo': viejo['tipo'], 'nuevo': resp['tipo'], 'que': 'tipo de contenido distinto'})
        diferencias(viejo['cuerpo'], resp['cuerpo'], '', volatiles, difs)
        acept = {x.get('camino'): x for x in (aceptadas.get(cid) or []) if isinstance(x, dict)}
        pendientes = []
        for d in difs:
            ac = acept.get(d['camino'])
            quien = (ac or {}).get('aprobado_por', '').strip()
            if ac and quien and not AGENTE.search(quien):
                d['aceptada_por'] = quien
            else:
                if ac:
                    sin_aprobar.append('%s %s%s' % (cid, d['camino'], ' (aprobado por un agente no vale)' if quien else ''))
                pendientes.append(d)
        if not difs:
            iguales += 1; filas.append({'id': cid, 'resultado': 'igual', 'diferencias': []})
        elif not pendientes:
            filas.append({'id': cid, 'resultado': 'distinto, aceptado', 'diferencias': difs})
        else:
            hallazgos += 1; filas.append({'id': cid, 'resultado': 'HALLAZGO', 'diferencias': difs})
    veredicto = 'HALLAZGO' if hallazgos or sin_aprobar else 'OK'
    resumen = {'veredicto': veredicto, 'slice': corpus.get('slice', ''), 'fecha': datetime.date.today().isoformat(),
               'golden': os.path.abspath(a.golden), 'golden_firma': golden['firma'], 'nuevo': a.nuevo,
               'casos': len(corpus['casos']), 'iguales': iguales, 'con_hallazgo': hallazgos,
               'volatiles': sorted(volatiles), 'aceptadas_archivo': os.path.abspath(a.aceptadas) if a.aceptadas else '',
               'aceptadas_detalle': [{'caso': f['id'], 'camino': d['camino'], 'aprobado_por': d['aceptada_por']} for f in filas for d in f.get('diferencias', []) if d.get('aceptada_por')],
               'aceptadas_sin_aprobar': sin_aprobar, 'filas': filas, 'escrito_por': 'bin/paridad.py'}
    resumen['firma'] = firmar_resultado(resumen)
    if a.informe:
        L = ['# Paridad del slice %s — %s' % (resumen['slice'], veredicto), '',
             'Golden `%s` (firma `%s…`), nueva `%s`, %d caso(s): %d iguales, %d con hallazgo.' % (
                 a.golden, golden['firma'][:12], a.nuevo, len(corpus['casos']), iguales, hallazgos), '',
             '| Caso | Resultado | Camino | Viejo | Nuevo | Qué |', '|---|---|---|---|---|---|']
        for f in filas:
            if not f.get('diferencias'):
                L.append('| %s | %s | | | | %s |' % (f['id'], f['resultado'], f.get('detalle', '')))
            for d in f.get('diferencias', []):
                L.append('| %s | %s | `%s` | `%s` | `%s` | %s%s |' % (f['id'], f['resultado'], d['camino'], canonico(d['viejo'])[:60],
                         canonico(d['nuevo'])[:60], d['que'], (' (aceptada por %s)' % d['aceptada_por']) if d.get('aceptada_por') else ''))
        os.makedirs(os.path.dirname(os.path.abspath(a.informe)) or '.', exist_ok=True)
        with open(a.informe, 'w', encoding='utf-8', newline='\n') as h:
            h.write('\n'.join(L) + '\n')
    if a.json:
        print(json.dumps(resumen, ensure_ascii=False, indent=1))
    else:
        print('%s -- paridad del slice %s: %d caso(s), %d iguales, %d con hallazgo%s%s' % (
            veredicto, resumen['slice'] or '?', len(corpus['casos']), iguales, hallazgos,
            ('; volatiles ignorados: ' + ', '.join(sorted(volatiles))) if volatiles else '',
            ('; aceptadas SIN aprobar: ' + ', '.join(sin_aprobar)) if sin_aprobar else ''))
        for f in filas:
            if f['resultado'] in ('HALLAZGO', 'SIN DATOS'):
                for d in f.get('diferencias', []) or [{'camino': '', 'que': f.get('detalle', ''), 'viejo': '', 'nuevo': ''}]:
                    print('  %-8s %-10s %-30s viejo=%s nuevo=%s  %s' % (f['resultado'], f['id'], d['camino'], canonico(d['viejo'])[:40], canonico(d['nuevo'])[:40], d['que']))
        print('  Lo que este script NO mira: si una diferencia es un bug del port, un cambio intencional o un campo volatil. Eso lo decide una persona (aceptadas.json con aprobado_por; --volatil).')
    return HALLAZGO if veredicto == 'HALLAZGO' else OK


def main():
    ap = argparse.ArgumentParser(description='Graba el oraculo y compara la nueva implementacion.')
    sub = ap.add_subparsers(dest='accion', required=True)
    g = sub.add_parser('grabar'); g.add_argument('--corpus', required=True); g.add_argument('--oraculo', required=True); g.add_argument('--salida', required=True)
    g.add_argument('--permitir-mutaciones', action='store_true'); g.add_argument('--permitir-remoto', action='store_true')
    c = sub.add_parser('comparar'); c.add_argument('--corpus', required=True); c.add_argument('--golden', required=True); c.add_argument('--nuevo', required=True)
    c.add_argument('--volatil', action='append', default=[]); c.add_argument('--aceptadas', default=''); c.add_argument('--json', action='store_true')
    c.add_argument('--informe', default=''); c.add_argument('--permitir-remoto', action='store_true')
    v = sub.add_parser('verificar'); v.add_argument('--golden', default=''); v.add_argument('--corpus', default=''); v.add_argument('--resultado', default='')
    a = ap.parse_args()
    if a.accion == 'grabar':
        return grabar(a)
    if a.accion == 'comparar':
        return comparar(a)
    if a.resultado:
        try:
            d = leer_json(a.resultado)
        except (OSError, ValueError) as e:
            print('SIN DATOS -- no pude leer el resultado: %s' % e); return SIN_DATOS
        if d.get('escrito_por') != 'bin/paridad.py' or d.get('firma') != firmar_resultado(d):
            print('SIN DATOS -- el resultado NO verifica: no lo escribio bin/paridad.py o fue editado despues'); return SIN_DATOS
        print('OK -- el resultado verifica: %s del slice %s (%s), %d caso(s), volatiles %s' % (d.get('veredicto'), d.get('slice'), d.get('fecha'), d.get('casos', 0), ', '.join(d.get('volatiles') or []) or 'ninguno'))
        return OK
    if not a.golden:
        print('SIN DATOS -- verificar necesita --golden o --resultado'); return SIN_DATOS
    g_, err = verificar_golden(a.golden, a.corpus or None)
    if err:
        print('SIN DATOS -- ' + err); return SIN_DATOS
    print('OK -- el golden verifica: %d caso(s) grabados el %s contra %s por bin/paridad.py' % (len(g_['casos']), g_['fecha'], g_['oraculo']))
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
