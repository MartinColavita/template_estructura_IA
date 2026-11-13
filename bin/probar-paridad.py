#!/usr/bin/env python3
"""Prueba de bin/paridad.py con dos servidores HTTP locales de mentira (oraculo y nueva) y un comando.
Se corre:  python -B bin/probar-paridad.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'paridad.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def servidor(respuestas):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self):
            r = respuestas.get(self.path, (404, {'error': 'no existe'}))
            self.send_response(r[0]); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(r[1]).encode('utf-8'))

        do_GET = _responder
        do_POST = _responder
    s = HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, 'http://127.0.0.1:%d' % s.server_address[1]


def escribir(p, d):
    with open(p, 'w', encoding='utf-8') as h:
        json.dump(d, h, ensure_ascii=False)


def main():
    print('== paridad')
    tmp = tempfile.mkdtemp(prefix='probar-paridad-')
    viejo, url_viejo = servidor({'/reservas': (200, [{'id': 1, 'precio': 100, 'fecha': '2026-01-01'}]), '/reservas/1': (200, {'id': 1, 'estado': 'activa'})})
    nuevo, url_nuevo = servidor({'/reservas': (200, [{'id': 1, 'precio': '100', 'fecha': '2026-02-02'}]), '/reservas/1': (200, {'id': 1, 'estado': 'activa'})})
    corpus = os.path.join(tmp, 'corpus.json'); golden = os.path.join(tmp, 'golden.json')
    escribir(corpus, {'slice': 'reservas', 'casos': [
        {'id': 'RC-01', 'tipo': 'http', 'metodo': 'GET', 'ruta': '/reservas', 'muta': False},
        {'id': 'RC-02', 'tipo': 'http', 'metodo': 'GET', 'ruta': '/reservas/1', 'muta': False},
        {'id': 'RC-03', 'tipo': 'http', 'metodo': 'POST', 'ruta': '/reservas', 'cuerpo': {'x': 1}, 'muta': True}]})
    rc, out = correr('grabar', '--corpus', corpus, '--oraculo', url_viejo, '--salida', golden)
    caso('grabar: OK (0), 2 casos y salta el que muta', rc == 0 and '2 caso(s)' in out and 'RC-03' in out, out[:300])
    g = json.load(open(golden, encoding='utf-8'))
    caso('el golden lo firma el script y guarda el hash del corpus', g.get('grabado_por') == 'bin/paridad.py' and len(g.get('firma', '')) == 64 and 'corpus_sha256' in g)
    rc, out = correr('verificar', '--golden', golden, '--corpus', corpus)
    caso('verificar: el golden verifica (0)', rc == 0, out[:200])
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--json')
    d = json.loads(out)
    caso('comparar: HALLAZGO (1) por tipo distinto (100 vs "100") y fecha', rc == 1 and d['veredicto'] == 'HALLAZGO' and d['con_hallazgo'] == 1, out[:300])
    difs = [x for f in d['filas'] if f['id'] == 'RC-01' for x in f['diferencias']]
    caso('las diferencias traen camino JSON, viejo, nuevo y que', any(x['camino'] == '/0/precio' and x['que'] == 'tipo distinto' for x in difs) and any(x['camino'] == '/0/fecha' for x in difs), str(difs))
    caso('RC-03 (muta, no grabado) queda SIN DATOS en su fila, no OK', any(f['id'] == 'RC-03' and f['resultado'] == 'SIN DATOS' for f in d['filas']))
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--json')
    d = json.loads(out)
    caso('--volatil fecha: queda solo la diferencia de precio', rc == 1 and len([x for f in d['filas'] if f['id'] == 'RC-01' for x in f['diferencias']]) == 1)
    acept = os.path.join(tmp, 'aceptadas.json')
    escribir(acept, {'RC-01': [{'camino': '/0/precio', 'motivo': 'ahora es texto'}]})
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept)
    caso('una aceptada SIN aprobado_por no vale: sigue HALLAZGO y lo dice', rc == 1 and 'SIN aprobar' in out, out[:300])
    escribir(acept, {'RC-01': [{'camino': '/0/precio', 'motivo': 'ahora es texto', 'aprobado_por': 'Claude (agente)'}]})
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept)
    caso('una aceptada aprobada por un agente no vale: HALLAZGO y lo dice', rc == 1 and 'un agente no vale' in out, out[:300])
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', '')
    caso('--volatil vacio se rechaza: SIN DATOS (2)', rc == 2 and 'vacio' in out, out[:200])
    escribir(acept, {'RC-01': [{'camino': '/0/precio', 'motivo': 'ahora es texto', 'aprobado_por': 'Persona de prueba', 'fecha': '2026-11-03'}]})
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept)
    caso('el caso que muta y no se grabo deja la paridad en SIN DATOS (2), no OK', rc == 2 and out.startswith('SIN DATOS') and 'RC-03' in out, out[:300])
    escribir(acept, {'RC-01': [{'camino': '/0/precio', 'motivo': 'ahora es texto', 'aprobado_por': 'Persona de prueba', 'fecha': '2026-11-03'}],
                     'RC-03': [{'camino': '(sin comparar)', 'motivo': 'escribe datos', 'aprobado_por': 'Claude (agente)'}]})
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept)
    caso('el caso sin comparar aceptado por un agente no vale: HALLAZGO (1)', rc == 1 and 'un agente no vale' in out, out[:300])
    escribir(acept, {'RC-01': [{'camino': '/0/precio', 'motivo': 'ahora es texto', 'aprobado_por': 'Persona de prueba', 'fecha': '2026-11-03'}],
                     'RC-03': [{'camino': '(sin comparar)', 'motivo': 'escribe datos: se probo a mano contra la copia', 'aprobado_por': 'Persona de prueba'}]})
    informe = os.path.join(tmp, 'paridad.md')
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept, '--informe', informe)
    resultado = os.path.join(tmp, 'resultado.json')
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept, '--json')
    open(resultado, 'w', encoding='utf-8').write(out)
    d = json.loads(out)
    caso('el resultado --json va firmado y registra volatiles y quien acepto que', d.get('escrito_por') == 'bin/paridad.py' and len(d.get('firma', '')) == 64 and d['volatiles'] == ['fecha'] and d['aceptadas_detalle'][0]['aprobado_por'] == 'Persona de prueba', out[:300])
    rc, out = correr('verificar', '--resultado', resultado)
    caso('verificar --resultado: verifica (0)', rc == 0, out[:200])
    d['con_hallazgo'] = 99; d['iguales'] = 99
    json.dump(d, open(resultado, 'w', encoding='utf-8'))
    rc, out = correr('verificar', '--resultado', resultado)
    caso('un resultado editado a mano no verifica: SIN DATOS (2)', rc == 2 and 'NO verifica' in out, out[:200])
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo, '--volatil', 'fecha', '--aceptadas', acept, '--informe', informe)
    caso('con la aceptada aprobada: OK (0) y escribe el informe markdown', rc == 0 and out.startswith('OK') and os.path.isfile(informe) and 'aceptada por Persona de prueba' in open(informe, encoding='utf-8').read(), out[:300])
    # golden editado a mano
    g['casos']['RC-02']['cuerpo']['estado'] = 'cerrada'
    escribir(golden, g)
    rc, out = correr('comparar', '--corpus', corpus, '--golden', golden, '--nuevo', url_nuevo)
    caso('golden editado a mano: la firma no verifica, SIN DATOS (2)', rc == 2 and 'firma' in out, out[:200])
    # corpus cambiado despues de grabar
    correr('grabar', '--corpus', corpus, '--oraculo', url_viejo, '--salida', golden)
    escribir(corpus, {'slice': 'reservas', 'casos': [{'id': 'RC-01', 'tipo': 'http', 'metodo': 'GET', 'ruta': '/reservas', 'muta': False}]})
    rc, out = correr('verificar', '--golden', golden, '--corpus', corpus)
    caso('corpus cambiado despues de grabar: SIN DATOS (2), hay que regrabar', rc == 2 and 'OTRO corpus' in out, out[:200])
    # remoto sin permiso
    rc, out = correr('grabar', '--corpus', corpus, '--oraculo', 'http://ejemplo.invalido:9', '--salida', golden)
    caso('un host que no es local se rechaza sin --permitir-remoto (2)', rc == 2 and 'permitir-remoto' in out, out[:200])
    # modo comando
    cmd_corpus = os.path.join(tmp, 'cmd.json'); cmd_golden = os.path.join(tmp, 'cmd-golden.json')
    escribir(cmd_corpus, {'slice': 'cli', 'casos': [{'id': 'C-01', 'tipo': 'cmd', 'args': ['3'], 'entrada': ''}]})
    oraculo = 'cmd:%s -c "import sys,json;print(json.dumps({\'dias\': int(sys.argv[1]), \'precio\': int(sys.argv[1])*10}))"' % sys.executable
    nueva = 'cmd:%s -c "import sys,json;print(json.dumps({\'dias\': int(sys.argv[1]), \'precio\': int(sys.argv[1])*11}))"' % sys.executable
    rc, out = correr('grabar', '--corpus', cmd_corpus, '--oraculo', oraculo, '--salida', cmd_golden)
    caso('modo comando: graba (0)', rc == 0, out[:300])
    rc, out = correr('comparar', '--corpus', cmd_corpus, '--golden', cmd_golden, '--nuevo', nueva)
    caso('modo comando: HALLAZGO (1) en /precio', rc == 1 and '/precio' in out, out[:300])
    rc, out = correr('comparar', '--corpus', cmd_corpus, '--golden', cmd_golden, '--nuevo', oraculo)
    caso('modo comando: contra el mismo comando, OK (0)', rc == 0, out[:300])
    escribir(corpus, {'slice': 'x', 'casos': []})
    rc, out = correr('grabar', '--corpus', corpus, '--oraculo', url_viejo, '--salida', golden)
    caso('corpus vacio: SIN DATOS (2)', rc == 2)
    viejo.shutdown(); nuevo.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
