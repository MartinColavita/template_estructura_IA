#!/usr/bin/env python3
"""Vigencia de los certificados TLS de las URL del inventario: cuanto les queda y si el nombre coincide. SOLO LECTURA.

    python -I bin/vigencia-certificados.py                                   (todas las URL del inventario, N0 o mas)
    python -I bin/vigencia-certificados.py --alias app-prueba                (una sola)
    python -I bin/vigencia-certificados.py --alias app-prueba --archivo <certificado.json>   (sin red)
    opciones: --dias 14  --fraccion 0.333  --tope 10  --ca <archivo de autoridades>
              --modulo <slug> | --inventario <ruta>  --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA: el alias no esta autorizado)   2 = SIN DATOS

POR QUE EXISTE. Los avisos de vencimiento por mail ya no llegan (Let's Encrypt los corto en 2025) y la vida de
los certificados se acorta (64 dias desde 2027, 45 desde 2028): un umbral fijo de 30 dias deja de servir. Este
script mide, por cada URL del inventario, los dias que quedan y la FRACCION de vida que queda (renovar a los
dos tercios), y si el certificado nombra al host. HALLAZGO: queda menos de un tercio de la vida o menos de N
dias, ya vencio o todavia no vale, el nombre no coincide, o la cadena no valida (con el motivo del error).
SIN DATOS: no conecta, o el certificado no se puede leer.

QUE NO HACE. Solo se conecta a las URL del inventario autorizadas para leer (nivel N0 o mas), y solo hace el
saludo TLS: no manda ningun pedido a la aplicacion. No renueva nada ni toca el servidor. Con --archivo no se
conecta: lee el diccionario que devuelve getpeercert() de la biblioteca ssl, guardado en JSON.
Solo biblioteca estandar. ASCII puro.
"""

import argparse
import ipaddress
import json
import os
import socket
import ssl
import sys
import time

try:
    from urllib.parse import urlsplit
except ImportError:                                                        # pragma: no cover
    urlsplit = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operacion import inventario  # noqa: E402  el unico lector del inventario

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAS, FRACCION, DIA = 14, 1.0 / 3, 86400
NO_MIRA = ('si la renovacion automatica esta configurada y corre: un certificado al dia hoy no dice que se renueve solo',
           'la revocacion y la configuracion TLS del servidor (protocolos, cifrados): eso es de seguridad',
           'los certificados que no estan detras de una URL del inventario (internos, de la base, de clientes)')


def limpio(texto, largo=100):
    """Lo que viene de afuera es dato: a la pantalla va sin caracteres de control y acotado."""
    return ''.join(c if 32 <= ord(c) < 127 else '?' for c in str(texto))[:largo]


def destino_tls(url):
    """(host, puerto, motivo). host None con el motivo si no hay certificado que mirar."""
    u = urlsplit(url.strip()) if url else None
    if not u or u.scheme not in ('http', 'https') or not u.hostname:
        return None, None, 'el Destino del inventario no es una URL con https://'
    if u.scheme == 'http':
        return None, None, 'la URL es http, sin TLS: no hay certificado que mirar'
    try:
        puerto = u.port or 443
    except ValueError:
        return None, None, 'el puerto de la URL no se entiende'
    return u.hostname.lower(), puerto, ''


def traer_certificado(host, puerto, tope, ca):
    """(certificado, tipo_de_error, motivo). Valida la cadena; el nombre lo compara este script (igual con o sin red).
    tipo_de_error: None, 'cadena' (es un HALLAZGO) o 'conexion' (es SIN DATOS)."""
    ctx = ssl.create_default_context(cafile=ca or None)
    ctx.check_hostname = False
    try:
        with socket.create_connection((host, puerto), timeout=tope) as s:
            with ctx.wrap_socket(s, server_hostname=host) as t:
                return t.getpeercert(), None, ''
    except ssl.SSLCertVerificationError as e:
        return None, 'cadena', getattr(e, 'verify_message', '') or 'la cadena no valida'
    except socket.gaierror:
        return None, 'conexion', 'el nombre no resuelve'
    except socket.timeout:
        return None, 'conexion', 'no contesto en %d segundos' % tope
    except ConnectionRefusedError:
        return None, 'conexion', 'rechazo la conexion'
    except ssl.SSLError as e:
        return None, 'conexion', 'el saludo TLS fallo (%s)' % limpio(getattr(e, 'reason', '') or type(e).__name__, 60)
    except OSError as e:
        return None, 'conexion', 'no se pudo conectar (%s)' % type(e).__name__


def coincide(host, cert):
    """(coincide, nombres). Solo los nombres alternativos (SAN), como los navegadores: el CN no cuenta.
    Un comodin vale solo para la primera etiqueta: *.a.com cubre x.a.com, no x.y.a.com."""
    nombres = [(str(p[0]), str(p[1])) for p in cert.get('subjectAltName') or () if isinstance(p, (list, tuple)) and len(p) == 2]
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    for tipo, valor in nombres:
        v = valor.strip().lower().rstrip('.')
        if ip is not None:
            if tipo == 'IP Address':
                try:
                    if ipaddress.ip_address(v) == ip:
                        return True, nombres
                except ValueError:
                    pass
            continue
        if tipo != 'DNS':
            continue
        if v == host:
            return True, nombres
        if v.startswith('*.') and '.' in host and host.split('.', 1)[1] == v[2:] and host.split('.', 1)[0]:
            return True, nombres
    return False, nombres


def evaluar(alias, host, cert, ahora, dias_min, fraccion_min):
    """El resultado de un certificado ya leido."""
    r = {'alias': alias, 'host': host}
    if not isinstance(cert, dict) or not cert.get('notAfter') or not cert.get('notBefore'):
        r.update(estado='SIN DATOS', detalle='el certificado no trae sus fechas (un getpeercert() vacio es uno que no se valido)')
        return r
    try:
        desde, hasta = ssl.cert_time_to_seconds(str(cert['notBefore'])), ssl.cert_time_to_seconds(str(cert['notAfter']))
    except ValueError:
        r.update(estado='SIN DATOS', detalle='las fechas del certificado no se entienden')
        return r
    if hasta <= desde:
        r.update(estado='SIN DATOS', detalle='el certificado vence antes de empezar a valer')
        return r
    quedan = hasta - ahora
    dias, fraccion = int(round(quedan / float(DIA))), round(quedan / float(hasta - desde), 3)
    nombre_ok, nombres = coincide(host, cert)
    vence = time.strftime('%Y-%m-%d', time.gmtime(hasta))
    r.update(dias=dias, fraccion=fraccion, vence=vence, nombre_coincide=nombre_ok)
    problemas = []
    if ahora < desde:
        problemas.append('todavia no es valido (vale desde %s)' % time.strftime('%Y-%m-%d', time.gmtime(desde)))
    if quedan <= 0:
        problemas.append('vencio hace %d dia(s), el %s' % (-dias, vence))
    elif fraccion < fraccion_min:
        problemas.append('queda el %d %% de su vida, menos de un tercio (umbral %d %%): ya tendria que haberse renovado' % (
            round(fraccion * 100), round(fraccion_min * 100)))
    elif quedan < dias_min * DIA:
        problemas.append('quedan %d dias (umbral %d)' % (dias, dias_min))
    if not nombre_ok:
        problemas.append('el nombre no coincide: se busco %s y el certificado nombra %s' % (
            host, ', '.join(limpio(v, 60) for _, v in nombres[:5]) if nombres else 'ningun nombre alternativo (solo el CN, que no cuenta)'))
    base = 'quedan %d dias (%d %% de la vida), vence %s' % (dias, round(fraccion * 100), vence) if quedan > 0 else 'vencido el %s' % vence
    if problemas:
        r.update(estado='HALLAZGO', detalle='; '.join(problemas) + ('' if quedan <= 0 else ' -- ' + base))
    else:
        r.update(estado='OK', detalle=base + ', el nombre coincide')
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description='Vigencia de los certificados TLS de las URL del inventario (solo lectura).')
    ap.add_argument('--alias', default='')
    ap.add_argument('--archivo', default='', help='el diccionario de getpeercert() en JSON (con --alias); no se conecta')
    ap.add_argument('--dias', type=int, default=DIAS, help='dias que quedan desde los que es HALLAZGO (por defecto %d)' % DIAS)
    ap.add_argument('--fraccion', type=float, default=FRACCION, help='fraccion de vida que queda desde la que es HALLAZGO (por defecto 1/3)')
    ap.add_argument('--tope', type=int, default=10, help='segundos por conexion (por defecto 10)')
    ap.add_argument('--ca', default='', help='archivo de autoridades propias, si la organizacion tiene una')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--inventario', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    umbrales = {'dias': a.dias, 'fraccion': round(a.fraccion, 3)}

    def salir(codigo, estado, motivo):
        if a.json:
            print(json.dumps({'estado': estado, 'alias': a.alias, 'motivo': motivo, 'resultados': [], 'umbrales': umbrales,
                              'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        else:
            print('%s -- %s' % ('GATE de SERVIDOR -- FRENA' if estado == 'FRENA' else estado, motivo))
        return codigo

    if a.archivo and not a.alias:
        return salir(SIN_DATOS, 'SIN DATOS', '--archivo va con --alias: el nombre a comparar sale del inventario')
    ruta, motivo = (a.inventario, '') if a.inventario else inventario.ubicar(os.path.abspath(a.raiz), a.modulo)
    if not ruta:
        return salir(SIN_DATOS, 'SIN DATOS', '%s. Sin inventario nada esta autorizado: no se conecto a nada' % motivo)
    if a.alias:
        estado, activo, motivo = inventario.autorizar(ruta, a.alias, 'N0')
        if estado == inventario.FRENA:
            return salir(HALLAZGO, 'FRENA', '%s. No se conecto a nada' % motivo)
        if estado == inventario.SIN_DATOS:
            return salir(SIN_DATOS, 'SIN DATOS', '%s: no se conecto a nada' % motivo)
        if activo['tipo'] != 'url':
            return salir(HALLAZGO, 'FRENA', '%s es de tipo %s: este script solo mira activos de tipo url' % (a.alias, activo['tipo'] or '?'))
        candidatos = [activo]
    else:
        activos, motivo = inventario.cargar(ruta)
        if activos is None:
            return salir(SIN_DATOS, 'SIN DATOS', '%s: no se conecto a nada' % motivo)
        candidatos = [x for x in activos if x['tipo'] == 'url']
        if not candidatos:
            return salir(SIN_DATOS, 'SIN DATOS', 'el inventario no tiene ningun activo de tipo url: cero certificados mirados no es OK')

    resultados, ahora = [], int(time.time())
    for act in candidatos:
        alias = act['alias']
        if not a.alias:
            estado, _, motivo = inventario.autorizar(ruta, alias, 'N0')
            if estado == inventario.SIN_DATOS:          # p. ej. el alias figura dos veces: no se sabe cual vale
                resultados.append({'alias': alias, 'estado': 'SIN DATOS', 'detalle': '%s: no se conecto' % motivo})
                continue
            if estado != inventario.OK:                 # FRENA: el inventario no la autoriza para leer
                resultados.append({'alias': alias, 'estado': 'salteada', 'detalle': '%s: no se conecto' % motivo})
                continue
        host, puerto, motivo = destino_tls(act['destino'])
        if host is None:
            resultados.append({'alias': alias, 'estado': 'SIN DATOS', 'detalle': motivo})
            continue
        if a.archivo:
            try:
                with open(a.archivo, 'rb') as h:
                    cert = json.loads(h.read().decode('utf-8'))
            except (OSError, ValueError) as e:
                resultados.append({'alias': alias, 'estado': 'SIN DATOS', 'detalle': 'no se pudo leer %s: %s' % (
                    limpio(os.path.basename(a.archivo)), type(e).__name__)})
                continue
        else:
            cert, error, motivo = traer_certificado(host, puerto, a.tope, a.ca)
            if error == 'cadena':
                resultados.append({'alias': alias, 'host': host, 'estado': 'HALLAZGO',
                                   'detalle': 'la cadena no valida: %s' % limpio(motivo)})
                continue
            if error:
                resultados.append({'alias': alias, 'host': host, 'estado': 'SIN DATOS', 'detalle': 'no se pudo leer el certificado: %s' % motivo})
                continue
        resultados.append(evaluar(alias, host, cert, ahora, a.dias, a.fraccion))

    estados = [r['estado'] for r in resultados]
    mirados = [e for e in estados if e != 'salteada']
    estado = 'HALLAZGO' if 'HALLAZGO' in estados else 'SIN DATOS' if ('SIN DATOS' in estados or not mirados) else 'OK'
    codigo = {'OK': OK, 'HALLAZGO': HALLAZGO, 'SIN DATOS': SIN_DATOS}[estado]
    if a.json:
        print(json.dumps({'estado': estado, 'inventario': ruta, 'resultados': resultados, 'umbrales': umbrales,
                          'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        return codigo
    print('VIGENCIA de certificados -- %s   (%d URL mirada(s), %d salteada(s))' % (estado, len(mirados), len(estados) - len(mirados)))
    for r in resultados:
        print('  %-20s %-10s %s' % (r['alias'], r['estado'], r['detalle']))
    if not mirados:
        print('  Ninguna URL se pudo mirar: cero certificados mirados no es OK.')
    print('  Umbrales: menos de %d %% de la vida o menos de %d dias (por defecto un tercio y 14; los fija DEC-008).' % (
        round(a.fraccion * 100), a.dias))
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
