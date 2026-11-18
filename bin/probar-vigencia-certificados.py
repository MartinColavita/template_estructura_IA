#!/usr/bin/env python3
"""Prueba de bin/vigencia-certificados.py con certificados plantados (el diccionario de getpeercert() en JSON).
Se corre:  python -B bin/probar-vigencia-certificados.py   -> OK o FALLA, con el detalle de cada caso.
No usa la red: la funcion que hace el saludo TLS se reemplaza; el unico socket real va a un puerto cerrado de
esta misma maquina."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'vigencia-certificados.py')
ESPERADOS = []
AHORA = int(time.time())
DIA = 86400
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `app-prueba` | url | prueba | https://app.prueba.example.com | si | media | N0 | no | | producto |\n'
         '| `app-puerto` | url | prueba | https://otra.prueba.example.com:8443/inicio | no | media | N1 | no | | producto |\n'
         '| `app-dos-niveles` | url | prueba | https://a.b.example.com | no | baja | N0 | no | | producto |\n'
         '| `app-nada` | url | prueba | https://cerrada.example.com | no | baja | nada | pasivo | | producto |\n'
         '| `app-http` | url | prueba | http://plano.example.com | no | baja | N0 | no | | producto |\n'
         '| `app-sin-url` | url | prueba | `pendiente` | no | baja | N0 | no | | producto |\n'
         '| `web-1` | servidor | prueba | `web-1` | no | media | N1 | no | martes 22 | operaciones |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:400]) if (detalle and not ok) else ''))


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def fecha(epoch):
    return time.strftime('%b %d %H:%M:%S %Y GMT', time.gmtime(epoch))


def cert(desde_dias, hasta_dias, nombres=('app.prueba.example.com',), cn='app.prueba.example.com', san=True):
    """El diccionario de getpeercert(): fechas relativas a hoy, en dias."""
    d = {'subject': [[['commonName', cn]]], 'issuer': [[['organizationName', 'CA de prueba']], [['commonName', 'CA de prueba R1']]],
         'notBefore': fecha(AHORA + desde_dias * DIA), 'notAfter': fecha(AHORA + hasta_dias * DIA), 'serialNumber': '0A1B', 'version': 3}
    if san:
        d['subjectAltName'] = [['DNS', n] for n in nombres]
    return d


def cargar_modulo():
    spec = importlib.util.spec_from_file_location('vigencia_en_prueba', SCRIPT)
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
    print('== vigencia-certificados')
    tmp = tempfile.mkdtemp(prefix='probar-cert-')
    inv = escribir(os.path.join(tmp, 'repo', 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)
    repo = os.path.join(tmp, 'repo')

    def correr(*args):
        r = subprocess.run([sys.executable, '-I', SCRIPT, '--raiz', repo] + list(args), capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        return r.returncode, r.stdout + r.stderr

    def plantado(nombre, dato):
        return escribir(os.path.join(tmp, nombre), dato if isinstance(dato, str) else json.dumps(dato))

    # --- el camino feliz (sin red: --archivo con el certificado)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('sano.json', cert(-30, 60)))
    caso('certificado sano: OK (0), con dias, fraccion de vida, vencimiento, nombre y lo que NO mira',
         rc == 0 and out.startswith('VIGENCIA') and 'quedan 60 dias' in out and '67 %' in out and 'coincide' in out and 'NO mira' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('comodin.json', cert(-30, 60, nombres=('*.prueba.example.com',))))
    caso('un comodin cubre una etiqueta: *.prueba.example.com vale para app.prueba.example.com', rc == 0, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('mayus.json', cert(-30, 60, nombres=('APP.Prueba.Example.com',))))
    caso('el nombre se compara sin mayusculas', rc == 0, out)

    # --- cada HALLAZGO
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('tercio.json', cert(-70, 20)))
    caso('queda menos de un tercio de la vida (22 %): HALLAZGO (1)', rc == 1 and 'HALLAZGO' in out and 'tercio' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', os.path.join(tmp, 'tercio.json'), '--fraccion', '0.2')
    caso('la fraccion va por argumento: con --fraccion 0.2, un 22 % es OK', rc == 0, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('dias.json', cert(-18, 12)))
    caso('quedan 12 dias con 40 % de la vida: HALLAZGO por dias (umbral 14)', rc == 1 and '12 dias' in out and 'umbral 14' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', os.path.join(tmp, 'dias.json'), '--dias', '10')
    caso('los dias van por argumento: con --dias 10, quedan 12 es OK', rc == 0, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('vencido.json', cert(-92, -2)))
    caso('certificado vencido: HALLAZGO (1) y lo dice', rc == 1 and 'vencio' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('futuro.json', cert(1, 91)))
    caso('certificado que todavia no es valido: HALLAZGO (1)', rc == 1 and 'todavia no es valido' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('otro-nombre.json', cert(-30, 60, nombres=('otra.example.com',))))
    caso('el nombre no coincide: HALLAZGO (1), dice que nombre se busco', rc == 1 and 'no coincide' in out and 'app.prueba.example.com' in out, out)
    rc, out = correr('--alias', 'app-dos-niveles', '--archivo', plantado('dos.json', cert(-30, 60, nombres=('*.example.com',))))
    caso('un comodin no cubre dos etiquetas: *.example.com no vale para a.b.example.com', rc == 1 and 'no coincide' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('sin-san.json', cert(-30, 60, san=False)))
    caso('sin nombres alternativos (solo el CN): HALLAZGO, el nombre no se da por bueno', rc == 1 and 'no coincide' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('dos-cosas.json', cert(-70, 20, nombres=('otra.example.com',))))
    caso('vida corta y nombre que no coincide: los dos problemas en la misma linea', rc == 1 and 'tercio' in out and 'no coincide' in out, out)

    # --- cada SIN DATOS
    rc, out = correr('--alias', 'app-prueba', '--archivo', os.path.join(tmp, 'no-existe.json'))
    caso('archivo ausente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('vacio.json', ''))
    caso('archivo vacio: SIN DATOS (2), nunca OK', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('roto.json', '{"notAfter": '))
    caso('JSON roto: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('dict-vacio.json', {}))
    caso('el diccionario vacio de un certificado que no se valido: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('lista.json', [cert(-30, 60)]))
    caso('una lista en vez del diccionario: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    malo = cert(-30, 60)
    malo['notAfter'] = '2027-01-01'
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('fecha-mala.json', malo))
    caso('una fecha en otro formato: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'sano.json'))
    caso('--archivo sin --alias: SIN DATOS (2), el nombre a comparar sale del inventario', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-http', '--archivo', os.path.join(tmp, 'sano.json'))
    caso('una URL sin TLS (http): SIN DATOS (2), no hay certificado que mirar', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--alias', 'app-sin-url', '--archivo', os.path.join(tmp, 'sano.json'))
    caso('un Destino que no es una URL: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    r = subprocess.run([sys.executable, '-I', SCRIPT, '--raiz', os.path.join(tmp, 'sin-repo'), '--alias', 'app-prueba'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('sin inventario: SIN DATOS (2), no "sin restricciones"', r.returncode == 2 and 'SIN DATOS' in r.stdout, r.stdout)

    # --- el inventario manda (FRENA), tambien con --archivo
    rc, out = correr('--alias', 'app-otra', '--archivo', os.path.join(tmp, 'sano.json'))
    caso('un alias que no esta en el inventario: FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--alias', 'app-nada', '--archivo', os.path.join(tmp, 'sano.json'))
    caso('una URL con nivel nada para la IA: FRENA (1), ni para leer su certificado', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--alias', 'web-1', '--archivo', os.path.join(tmp, 'sano.json'))
    caso('un activo que no es una url: FRENA (1)', rc == 1 and 'FRENA' in out and 'url' in out, out)

    # --- lo que viene de afuera es dato: sin caracteres de control en la salida
    raro = cert(-30, 60, nombres=('otra' + chr(27) + '[2J.example.com',))
    rc, out = correr('--alias', 'app-prueba', '--archivo', plantado('raro.json', raro))
    caso('caracteres de control en un nombre del certificado: no llegan a la salida', rc == 1 and chr(27) not in out, repr(out[:300]))

    # --- --json
    rc, out = correr('--alias', 'app-prueba', '--archivo', os.path.join(tmp, 'tercio.json'), '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    r0 = (d.get('resultados') or [{}])[0]
    caso('--json: estado, un resultado con dias, fraccion, vencimiento y nombre, umbrales y lo que no mira',
         rc == 1 and d.get('estado') == 'HALLAZGO' and r0.get('alias') == 'app-prueba' and r0.get('dias') == 20
         and abs(r0.get('fraccion', 0) - 0.222) < 0.01 and r0.get('nombre_coincide') is True and d.get('umbrales', {}).get('dias') == 14
         and d.get('no_mira') and all(ord(c) < 128 for c in out), out[:500])

    # --- con conexion: la funcion del saludo TLS se reemplaza
    try:
        mod = cargar_modulo()
    except Exception as e:
        mod = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    if mod is not None:
        llamadas = []

        def falso(respuestas):
            def traer(host, puerto, tope, ca):
                llamadas.append((host, puerto))
                return respuestas.get(host, (None, 'conexion', 'no contesto a tiempo'))
            return traer

        sano = cert(-30, 60)
        mod.traer_certificado = falso({'app.prueba.example.com': (sano, None, '')})
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-otra')
        caso('con conexion, un alias fuera del inventario: FRENA y NO se conecta', rc == 1 and llamadas == [], (llamadas, out))
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-nada')
        caso('con conexion, una URL con nivel nada: FRENA y NO se conecta', rc == 1 and llamadas == [], (llamadas, out))
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-prueba')
        caso('con conexion, una URL autorizada: se conecta una vez al host y puerto de su Destino y da OK',
             rc == 0 and llamadas == [('app.prueba.example.com', 443)], (llamadas, out))
        del llamadas[:]
        mod.traer_certificado = falso({'otra.prueba.example.com': (cert(-30, 60, nombres=('otra.prueba.example.com',)), None, '')})
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-puerto')
        caso('el puerto sale de la URL del inventario (8443)', rc == 0 and llamadas == [('otra.prueba.example.com', 8443)], (llamadas, out))
        del llamadas[:]
        mod.traer_certificado = falso({'app.prueba.example.com': (None, 'cadena', 'certificate has expired')})
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-prueba')
        caso('la cadena no valida: HALLAZGO (1) con el motivo del error', rc == 1 and 'certificate has expired' in out, out)
        mod.traer_certificado = falso({})
        rc, out = adentro(mod, '--raiz', repo, '--alias', 'app-prueba')
        caso('no conecta: SIN DATOS (2), nunca OK', rc == 2 and 'SIN DATOS' in out, out)
        del llamadas[:]
        mod.traer_certificado = falso({'app.prueba.example.com': (sano, None, ''),
                                       'a.b.example.com': (cert(-30, 60, nombres=('a.b.example.com',)), None, ''),
                                       'otra.prueba.example.com': (cert(-70, 20, nombres=('otra.prueba.example.com',)), None, '')})
        rc, out = adentro(mod, '--raiz', repo)
        hosts = sorted(h for h, _ in llamadas)
        caso('sin --alias: mira todas las URL autorizadas, saltea la de nivel nada sin conectarse, y una vida corta da HALLAZGO',
             rc == 1 and hosts == ['a.b.example.com', 'app.prueba.example.com', 'otra.prueba.example.com']
             and 'app-nada' in out and 'salteada' in out, (hosts, out))
        caso('sin --alias: la URL sin TLS y la que no tiene direccion figuran, no se callan', 'app-http' in out and 'app-sin-url' in out, out)
        mod.traer_certificado = falso({'app.prueba.example.com': (sano, None, ''),
                                       'a.b.example.com': (cert(-30, 60, nombres=('a.b.example.com',)), None, ''),
                                       'otra.prueba.example.com': (cert(-30, 60, nombres=('otra.prueba.example.com',)), None, '')})
        rc, out = adentro(mod, '--raiz', repo)
        caso('sin --alias, todas sanas pero una URL sin direccion: SIN DATOS (2), no OK', rc == 2, out)
        solo = escribir(os.path.join(tmp, 'solo', 'cerebro-digital', 'm', 'operacion', 'inventario.md'), CABECERA + FILAS.split('\n')[0] + '\n')
        rc, out = adentro(mod, '--inventario', solo)
        caso('sin --alias, con una sola URL sana: OK (0)', rc == 0, out)
        sin_url = escribir(os.path.join(tmp, 'sin-url.md'), CABECERA + FILAS.split('\n')[6] + '\n')
        rc, out = adentro(mod, '--inventario', sin_url)
        caso('un inventario sin ninguna URL: SIN DATOS (2), cero certificados mirados no es OK', rc == 2 and 'SIN DATOS' in out, out)
        lineas = FILAS.split('\n')
        doble = escribir(os.path.join(tmp, 'doble.md'), CABECERA + lineas[0] + '\n' + lineas[0] + '\n' + lineas[2] + '\n')
        mod.traer_certificado = falso({'app.prueba.example.com': (sano, None, ''),
                                       'a.b.example.com': (cert(-30, 60, nombres=('a.b.example.com',)), None, '')})
        rc, out = adentro(mod, '--inventario', doble, '--json')
        try:
            d = json.loads(out)
        except ValueError:
            d = {}
        estados = [r.get('estado') for r in d.get('resultados', []) if r.get('alias') == 'app-prueba']
        caso('todas las URL, con un alias repetido en el inventario: ese alias es SIN DATOS (no "salteada") y el total SIN DATOS (2)',
             rc == 2 and estados and all(e == 'SIN DATOS' for e in estados), out[:600])

    # --- un socket de verdad, a un puerto cerrado de esta maquina
    s = socket.socket()
    s.bind(('localhost', 0))
    puerto = s.getsockname()[1]
    s.close()
    cerrado = escribir(os.path.join(tmp, 'cerrado.md'), CABECERA +
                       '| `local` | url | prueba | https://localhost:%d | no | baja | N0 | no | | producto |\n' % puerto)
    r = subprocess.run([sys.executable, '-I', SCRIPT, '--inventario', cerrado, '--alias', 'local', '--tope', '3'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('un puerto cerrado de verdad: SIN DATOS (2), no se pudo conectar', r.returncode == 2 and 'SIN DATOS' in r.stdout, r.stdout + r.stderr)

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('vigencia-certificados.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
