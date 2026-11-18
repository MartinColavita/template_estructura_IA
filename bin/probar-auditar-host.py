#!/usr/bin/env python3
"""Prueba de bin/auditar-host.py sobre reportes plantados de ssh-audit y de Lynis, y un inventario de mentira.
Se corre:  python -B bin/probar-auditar-host.py   -> OK o FALLA, con el detalle de cada caso.
No usa la red ni ssh-audit: lo de --correr-ssh-audit se prueba reemplazando las funciones que ejecutan."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'auditar-host.py')
ESPERADOS = []
AHORA = time.time()
DIA = 86400
CLAVES = {'veredicto', 'origen', 'generado', 'categorias', 'hallazgos', 'sin_datos', 'no_mira'}
CLAVES_H = {'herramienta', 'categoria', 'regla', 'titulo', 'cwe', 'cve', 'severidad', 'archivo', 'linea', 'paquete',
            'version', 'arreglo', 'activo', 'huella', 'estado', 'motivo_supresion', 'vence'}
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `web-prueba-1` | servidor | prueba | `lectura-web-prueba-1` | no | media | N0 | no | | operaciones |\n'
         '| `sin-nivel` | servidor | prueba | `lectura-sin-nivel` | no | baja | nada | no | | operaciones |\n'
         '| `app-prueba` | url | prueba | https://prueba.example.com | si | media | N0 | pasivo | | producto |\n'
         '| `con-opcion` | servidor | prueba | `-oProxyCommand=malo` | no | baja | N0 | no | | operaciones |\n'
         '| `con-usuario` | servidor | prueba | `root@web-prueba-9` | no | baja | N0 | no | | operaciones |\n'
         '| `x/../../../../fuera-host` | servidor | prueba | `lectura-x` | no | baja | N0 | no | | operaciones |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:400]) if (detalle and not ok) else ''))


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


def alg(nombre, fail=(), warn=(), info=('disponible desde OpenSSH 6.5',)):
    notas = {'info': list(info)}
    if fail:
        notas['fail'] = list(fail)
    if warn:
        notas['warn'] = list(warn)
    return {'algorithm': nombre, 'notes': notas}


def sshaudit(fallas=False, cves=(), sin_kex=False, viejo=False):
    kex = [alg('curve25519-sha256'), alg('ecdh-sha2-nistp256', warn=('no protege contra ataques post-cuanticos',))]
    if fallas:
        kex.append(alg('diffie-hellman-group1-sha1', fail=('usa el algoritmo de hash SHA-1, roto',)))
    d = {'banner': {'comments': None, 'protocol': '2.0', 'raw': 'SSH-2.0-OpenSSH_9.6', 'software': 'OpenSSH_9.6'},
         'compression': ['none'], 'cves': list(cves), 'enc': [alg('aes256-gcm@openssh.com')],
         'fingerprints': [{'hash': 'x', 'hash_alg': 'SHA256', 'hostkey': 'ssh-ed25519'}],
         'kex': [] if sin_kex else kex, 'key': [] if sin_kex else [dict(alg('ssh-ed25519'), keysize=256)],
         'mac': [alg('hmac-sha2-256-etm@openssh.com')], 'recommendations': {}, 'target': '10.9.8.7:22', 'additional_notes': []}
    if viejo:
        d['enc'] = ['aes256-gcm@openssh.com']
        d['mac'] = ['hmac-sha2-256-etm@openssh.com']
    return d


def politica(pasa=True):
    errores = [] if pasa else [{'mismatched_field': 'MACs', 'actual': ['hmac-sha1', 'umac-64@openssh.com'],
                                'expected_required': ['hmac-sha2-256-etm@openssh.com'], 'expected_optional': ['']}]
    return {'errors': errores, 'host': 'localhost', 'passed': pasa, 'policy': 'Hardened OpenSSH Server v9.6 (version 1)',
            'port': 22, 'warnings': []}


def lynis(warnings=(), sugerencias=(), fin=True, dias=1, excepciones=(), indice=64, cabecera=True):
    fecha = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(AHORA - dias * DIA))
    lineas = ['# Lynis Report'] + (['report_version_major=1', 'report_version_minor=0', 'lynis_version=3.1.7'] if cabecera else [])
    lineas += ['report_datetime_start=' + fecha, 'os=Linux', 'os_name=Debian', 'hostname=srv-real-que-no-se-muestra']
    lineas += ['warning[]=%s|%s|-|-|' % w for w in warnings]
    lineas += ['suggestion[]=%s|%s|-|-|' % s for s in sugerencias]
    lineas += ['exception_event[]=%s|NoInfo|' % e for e in excepciones]
    lineas += ['hardening_index=%d' % indice, 'lynis_tests_done=250', 'report_datetime_end=' + fecha,
               'tests_executed=SSH-7408|AUTH-9228|', 'tests_skipped=KRNL-5677|']
    if fin:
        lineas.append('finish=true')
    return '\n'.join(lineas) + '\n'


def log_lynis(sin_root=0):
    lineas = ['2026-11-14 10:00:00 Starting Lynis 3.1.7', '2026-11-14 10:00:01 Performing test ID SSH-7408']
    for i in range(sin_root):
        lineas += ['2026-11-14 10:00:02 Skipped test FILE-%04d (prueba de permisos)' % i,
                   '2026-11-14 10:00:02 Reason to skip: This test needs root permissions']
    lineas += ['2026-11-14 10:00:02 Reason to skip: Incorrect guest OS (FreeBSD only)', '2026-11-14 10:00:09 Lynis ended successfully.']
    return '\n'.join(lineas) + '\n'


def cargar_modulo():
    spec = importlib.util.spec_from_file_location('auditar_host_en_prueba', SCRIPT)
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
    print('== auditar-host')
    tmp = tempfile.mkdtemp(prefix='probar-host-')
    repo = os.path.join(tmp, 'repo')
    escribir(os.path.join(repo, 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)

    def arch(nombre, contenido):
        return escribir(os.path.join(tmp, nombre), contenido)

    def host(*args):
        return correr('--host', 'web-prueba-1', '--raiz', repo, *args)

    ssh_ok = arch('ssh-ok.json', sshaudit())
    dat_ok = arch('lynis-ok.dat', lynis(sugerencias=[('SSH-7408', 'Considerar cambiar el puerto')]))
    log_ok = arch('lynis-ok.log', log_lynis())

    # --- el GATE de SERVIDOR va antes de todo
    rc, out = correr('--host', 'web-prueba-2', '--raiz', repo, '--ssh-audit', arch('ssh-falla.json', sshaudit(fallas=True)))
    caso('un alias que no esta en el inventario: FRENA (1) y no lee el reporte', rc == 1 and 'FRENA' in out and 'group1' not in out, out)
    rc, out = correr('--host', 'sin-nivel', '--raiz', repo, '--ssh-audit', ssh_ok)
    caso('un alias sin nivel para la IA: FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--host', 'app-prueba', '--raiz', repo, '--ssh-audit', ssh_ok)
    caso('un alias que no es un servidor: FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--host', 'web-prueba-1', '--raiz', os.path.join(tmp, 'sin-repo'), '--ssh-audit', ssh_ok)
    caso('sin inventario: SIN DATOS (2), no "sin restricciones"', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--ssh-audit', ssh_ok, '--raiz', repo)
    caso('sin --host: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = host()
    caso('con el alias autorizado pero sin ningun reporte ni herramienta: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)

    # --- la lista negra: lo que cambia algo o ataca no se corre nunca
    for pedido in (['--dheat', '10'], ['--conn-rate-test', '20'], ['--remediate'], ['remediate'], ['--active'], ['-T', 'lista.txt'],
                   ['--asff'], ['--pgsql'], ['--bc-api-key', 'x']):
        rc, out = host('--ssh-audit', ssh_ok, *pedido)
        caso('pedir %s: FRENA (1), cambia algo o ataca' % pedido[0], rc == 1 and 'FRENA' in out and pedido[0] in out, out)
    rc, out = host('--ssh-audit', ssh_ok, '--dheat=5')
    caso('pedir --dheat=5 (con el valor pegado): FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = host('--ssh-audit', ssh_ok, '--otra-cosa')
    caso('una opcion que este script no conoce: FRENA (1), no se pasa a ninguna herramienta', rc == 1 and 'FRENA' in out, out)

    # --- ssh-audit
    rc, out = host('--ssh-audit', ssh_ok)
    caso('ssh-audit sin fallas (solo avisos): OK (0), con lo que NO mira', rc == 0 and ' -- OK' in out.splitlines()[0] and 'NO mira' in out, out)
    caso('ssh-audit: los avisos (warn) se cuentan por debajo del umbral', '1 por debajo' in out, out)
    caso('ssh-audit: no muestra la direccion del servidor que trae el reporte', '10.9.8.7' not in out, out)
    rc, out = host('--ssh-audit', os.path.join(tmp, 'ssh-falla.json'))
    caso('ssh-audit con un algoritmo con falla: HALLAZGO (1) y lo nombra', rc == 1 and 'diffie-hellman-group1-sha1' in out, out)
    cve = {'name': 'CVE-2026-1111', 'cvssv2': 8.1, 'description': 'ejecucion remota'}
    rc, out = host('--ssh-audit', arch('ssh-cve.json', sshaudit(cves=[cve])), '--json')
    d = como_json(out)
    caso('ssh-audit con un CVE: HALLAZGO (1) con el CVE y la severidad por su puntaje',
         rc == 1 and any(h['cve'] == 'CVE-2026-1111' and h['severidad'] == 'ALTA' for h in d.get('hallazgos', [])), out[:400])
    rc, out = host('--ssh-audit', os.path.join(tmp, 'ssh-ok.json'), '--umbral', 'MEDIA')
    caso('el umbral va por argumento: con --umbral MEDIA, un aviso es HALLAZGO', rc == 1, out)
    rc, out = host('--ssh-audit', arch('pol-ok.json', politica(True)))
    caso('ssh-audit en modo politica, pasa: OK (0)', rc == 0, out)
    rc, out = host('--ssh-audit', arch('pol-no.json', politica(False)))
    caso('ssh-audit en modo politica, no pasa: HALLAZGO (1) y nombra el campo', rc == 1 and 'MACs' in out, out)
    rc, out = host('--ssh-audit', arch('ssh-sin-kex.json', sshaudit(sin_kex=True)))
    caso('ssh-audit sin algoritmos negociados (no conecto): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = host('--ssh-audit', arch('ssh-viejo.json', sshaudit(viejo=True)))
    caso('ssh-audit de un formato anterior (sin notas por algoritmo): SIN DATOS (2)', rc == 2, out)
    for nombre, contenido, que in (('no.json', None, 'ausente'), ('vacio.json', '', 'vacio'), ('roto.json', '{no es json', 'ilegible'),
                                   ('ajeno.json', {'foo': 1}, 'de otra herramienta')):
        ruta = os.path.join(tmp, nombre) if contenido is None else arch(nombre, contenido)
        rc, out = host('--ssh-audit', ruta)
        caso('reporte de ssh-audit %s: SIN DATOS (2)' % que, rc == 2 and 'SIN DATOS' in out, out)

    # --- Lynis
    rc, out = host('--lynis', dat_ok, '--lynis-log', log_ok)
    caso('Lynis sin advertencias, con privilegios y reciente: OK (0)', rc == 0, out)
    caso('Lynis: el indice de endurecimiento va como dato, sin veredicto', '64' in out and 'sin veredicto' in out, out)
    caso('Lynis: no muestra el nombre real del servidor que trae el reporte', 'srv-real-que-no-se-muestra' not in out, out)
    rc, out = host('--lynis', arch('lynis-warn.dat', lynis(warnings=[('AUTH-9308', 'No password set for single mode')])), '--lynis-log', log_ok)
    caso('Lynis con una advertencia: HALLAZGO (1), nombra la prueba', rc == 1 and 'AUTH-9308' in out, out)
    rc, out = host('--lynis', arch('lynis-cortado.dat', lynis(fin=False)), '--lynis-log', log_ok)
    caso('Lynis cortado (sin finish=true): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = host('--lynis', dat_ok, '--lynis-log', arch('lynis-sinroot.log', log_lynis(sin_root=23)))
    caso('Lynis sin privilegios (23 pruebas salteadas por root): SIN DATOS (2) y dice cuantas', rc == 2 and '23' in out and 'privilegios' in out, out)
    rc, out = host('--lynis', dat_ok)
    caso('Lynis sin --lynis-log: no se sabe si corrio con privilegios, SIN DATOS (2)', rc == 2 and 'privilegios' in out, out)
    rc, out = host('--lynis', dat_ok, '--lynis-log', arch('log-vacio.log', ''))
    caso('Lynis con el log vacio: SIN DATOS (2)', rc == 2, out)
    rc, out = host('--lynis', arch('lynis-viejo.dat', lynis(dias=30)), '--lynis-log', log_ok)
    caso('Lynis de hace 30 dias (tope 7): SIN DATOS (2)', rc == 2 and 'dias' in out, out)
    rc, out = host('--lynis', os.path.join(tmp, 'lynis-viejo.dat'), '--lynis-log', log_ok, '--max-dias', '0')
    caso('con --max-dias 0 se lee un reporte viejo a proposito', rc == 0, out)
    rc, out = host('--lynis', arch('lynis-exc.dat', lynis(excepciones=['KRNL-5820'])), '--lynis-log', log_ok)
    caso('Lynis con una excepcion interna: SIN DATOS (2)', rc == 2 and 'excepcion' in out, out)
    rc, out = host('--lynis', arch('lynis-ajeno.dat', lynis(cabecera=False)), '--lynis-log', log_ok)
    caso('un .dat que no dice ser de Lynis: SIN DATOS (2)', rc == 2, out)
    rc, out = host('--lynis', arch('lynis-vacio.dat', ''), '--lynis-log', log_ok)
    caso('reporte de Lynis vacio: SIN DATOS (2)', rc == 2, out)
    rc, out = host('--lynis', arch('lynis-crlf.dat', lynis().replace('\n', '\r\n')), '--lynis-log', log_ok)
    caso('reporte de Lynis con saltos de Windows: se lee igual', rc == 0, out)

    # --- las dos herramientas juntas
    rc, out = host('--ssh-audit', os.path.join(tmp, 'ssh-falla.json'), '--lynis', dat_ok)
    caso('un HALLAZGO y un chequeo sin datos a la vez: sale 1 y el otro dice SIN DATOS', rc == 1 and 'HALLAZGO' in out and 'SIN DATOS' in out, out)
    rc, out = host('--ssh-audit', ssh_ok, '--lynis', dat_ok, '--lynis-log', log_ok)
    caso('ssh-audit y Lynis, los dos bien: OK (0)', rc == 0, out)

    # --- lo que viene del servidor es dato
    sucio = sshaudit()
    sucio['kex'].append(alg('malo' + chr(27) + '[2J', fail=('texto' + chr(7),)))
    rc, out = host('--ssh-audit', arch('ssh-sucio.json', sucio))
    caso('caracteres de control en el reporte: no llegan a la salida', rc == 1 and chr(27) not in out and chr(7) not in out, repr(out[:300]))

    # --- --json: el esquema comun
    rc, out = host('--ssh-audit', os.path.join(tmp, 'ssh-falla.json'), '--lynis', dat_ok, '--lynis-log', log_ok, '--json')
    d = como_json(out)
    caso('--json: las claves del esquema comun, origen auditar-host y categoria host',
         CLAVES <= set(d) and d.get('origen') == 'auditar-host' and 'host' in d.get('categorias', {}) and d.get('veredicto') == 'HALLAZGO', out[:400])
    caso('--json: cada hallazgo con exactamente las claves del esquema y el alias en activo',
         bool(d.get('hallazgos')) and all(set(h) == CLAVES_H and h['activo'] == 'web-prueba-1' and h['categoria'] == 'host' for h in d['hallazgos']),
         (d.get('hallazgos') or [{}])[0])
    caso('--json es ASCII', all(ord(c) < 128 for c in out))
    rc, out = correr('--host', 'web-prueba-2', '--raiz', repo, '--ssh-audit', ssh_ok, '--json')
    d = como_json(out)
    caso('--json con FRENA: veredicto FRENA y el motivo', rc == 1 and d.get('veredicto') == 'FRENA' and d.get('motivo'), out[:300])

    # --- un solo esquema (F2 1): el del paquete, y el veredicto nunca OK con la categoria en HALLAZGO
    incoherentes = []
    for args in (('--ssh-audit', ssh_ok), ('--ssh-audit', os.path.join(tmp, 'ssh-falla.json')), ('--ssh-audit', os.path.join(tmp, 'pol-no.json')),
                 ('--lynis', dat_ok, '--lynis-log', log_ok), ('--lynis', os.path.join(tmp, 'lynis-warn.dat'), '--lynis-log', log_ok),
                 ('--ssh-audit', os.path.join(tmp, 'ssh-ok.json'), '--umbral', 'MEDIA')):
        d = como_json(host(*(args + ('--json',)))[1])
        estados = [c.get('estado') for c in d.get('categorias', {}).values()]
        if not estados or (d.get('veredicto') == 'OK' and 'HALLAZGO' in estados) or d.get('veredicto') != estados[0]:
            incoherentes.append((args[1][-14:], d.get('veredicto'), estados))
    caso('el veredicto es el de la categoria host (lo decide el paquete), nunca OK con la categoria en HALLAZGO', not incoherentes, incoherentes)
    d = como_json(host('--ssh-audit', os.path.join(tmp, 'ssh-falla.json'), '--json')[1])
    caso('--json: la huella sale de la funcion del paquete (normalizar.huella)', bool(d.get('hallazgos')) and all(
        len(h['huella']) == 16 for h in d['hallazgos']), (d.get('hallazgos') or [{}])[0])
    rc, out = host('--ssh-audit', ssh_ok, '--umbral', 'CRITICA')
    caso('--umbral no puede aflojar la regla del paquete (CRITICA y ALTA frenan): --umbral CRITICA no se acepta', rc in (1, 2) and ' -- OK' not in out, out[:300])

    # --- --correr-ssh-audit: la funcion que ejecuta se reemplaza (no hay red ni ssh-audit)
    try:
        mod = cargar_modulo()
    except Exception as e:
        mod = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    if mod is not None:
        llamadas = []

        def falso(respuesta, instalada=True):
            def ejecutar(orden):
                llamadas.append(list(orden))
                return respuesta
            mod.ejecutar = ejecutar
            mod.instalada = lambda nombre: ('/usr/bin/' + nombre) if instalada else None
            mod.resolver = lambda destino: ('srv-resuelto.example', 2222)

        falso((0, json.dumps(sshaudit()), ''), instalada=False)
        rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit')
        caso('--correr-ssh-audit sin ssh-audit instalado: SIN DATOS (2) y no ejecuta nada', rc == 2 and llamadas == [], out)
        falso((0, json.dumps(sshaudit()), ''))
        rc, out = adentro(mod, '--host', 'web-prueba-2', '--raiz', repo, '--correr-ssh-audit')
        caso('--correr-ssh-audit con un alias no autorizado: FRENA (1) y no ejecuta nada', rc == 1 and llamadas == [], out)
        rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit', '--dheat', '3')
        caso('--correr-ssh-audit pidiendo --dheat: FRENA (1) y no ejecuta nada', rc == 1 and llamadas == [], out)
        for alias, que in (('con-opcion', 'empieza con un guion'), ('con-usuario', 'trae un usuario')):
            rc, out = adentro(mod, '--host', alias, '--raiz', repo, '--correr-ssh-audit')
            caso('--correr-ssh-audit cuando el Destino %s: SIN DATOS (2) y no ejecuta nada' % que, rc == 2 and llamadas == [], out)
        rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit', '--politica=-x')
        caso('--politica que empieza con guion: FRENA (1) y no ejecuta nada', rc == 1 and llamadas == [], out)
        rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit')
        orden = llamadas[0] if llamadas else []
        caso('--correr-ssh-audit: una sola corrida desde afuera, JSON, sin la prueba de rafaga, al destino resuelto y su puerto',
             rc == 0 and len(llamadas) == 1 and orden[0] == 'ssh-audit' and '-j' in orden and '--skip-rate-test' in orden
             and orden[-1] == 'srv-resuelto.example' and orden[orden.index('-p') + 1] == '2222', (llamadas, out))
        caso('--correr-ssh-audit: ninguna opcion de la lista negra en la orden',
             not any(o.split('=')[0] in ('--dheat', '--conn-rate-test', '-T', '--targets') for o in orden), orden)
        guardados = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(repo, 'borrador')) for f in fs]
        caso('--correr-ssh-audit deja el reporte crudo en borrador/seguridad/ y dice donde',
             len(guardados) == 1 and os.sep + os.path.join('borrador', 'seguridad') + os.sep in guardados[0] and 'borrador' in out, (guardados, out))
        if guardados:
            rc2, out2 = correr('--host', 'web-prueba-1', '--raiz', repo, '--ssh-audit', guardados[0])
            caso('lo guardado se vuelve a leer con --ssh-audit (lo usa quien verifica)', rc2 == 0, out2)
        del llamadas[:]
        falso((0, json.dumps(sshaudit()), ''))
        rc, out = adentro(mod, '--host', 'x/../../../../fuera-host', '--raiz', repo, '--correr-ssh-audit')
        fuera = [os.path.join(r, f) for r, _, fs in os.walk(tmp) for f in fs if 'fuera-host' in os.path.join(r, f)]
        caso('un alias con / y .. se sanea antes de usarlo como carpeta: lo crudo queda adentro de borrador/seguridad/',
             rc == 0 and fuera and all(os.path.realpath(f).startswith(os.path.realpath(os.path.join(repo, 'borrador', 'seguridad')) + os.sep)
                                       for f in fuera), (fuera, out[:300]))
        del llamadas[:]
        rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit', '--politica', 'Hardened OpenSSH Server v9.6 (version 1)')
        caso('--politica pasa -P con el nombre a ssh-audit', llamadas and '-P' in llamadas[0], llamadas)
        for respuesta, que in (((1, '', 'connection refused to 10.1.2.3'), 'no conecta'), ((None, '', 'no termino'), 'no termina'),
                               ((0, 'texto que no es json', ''), 'no devuelve JSON')):
            del llamadas[:]
            falso(respuesta)
            rc, out = adentro(mod, '--host', 'web-prueba-1', '--raiz', repo, '--correr-ssh-audit')
            caso('--correr-ssh-audit cuando %s: SIN DATOS (2), nunca OK, y sin repetir la direccion' % que,
                 rc == 2 and 'SIN DATOS' in out and '10.1.2.3' not in out, out)
        try:
            mod.revisar_orden(['ssh-audit', '-j', '--dheat', '5', 'x'])
            frenada = False
        except ValueError:
            frenada = True
        caso('la lista negra frena una orden de ssh-audit con --dheat aunque alguien la arme a mano', frenada)

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('auditar-host.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
