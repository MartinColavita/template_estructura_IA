#!/usr/bin/env python3
"""Prueba de bin/salud-host.py sobre reportes del colector plantados, y del colector como texto.
Se corre:  python -B bin/probar-salud-host.py   -> OK o FALLA, con el detalle de cada caso.
No usa la red ni un servidor: lo de --ssh se prueba reemplazando la funcion que trae el reporte."""

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SCRIPT = os.path.join(AQUI, 'salud-host.py')
COLECTOR = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'operacion-de-servidores',
                        'assets', 'colector-salud.sh')
ESPERADOS = []
AHORA = int(time.time())
DIA = 86400
FECHA = AHORA - 60                # cuando el colector armo el reporte de muestra
SECCIONES = ('sistema', 'disco', 'inodos', 'memoria', 'carga', 'servicios', 'reinicio', 'reloj', 'journal')
CABECERA = ('| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel maximo para la IA | '
            'Pruebas dinamicas | Ventana de cambios | Duenio (rol) |\n|---|---|---|---|---|---|---|---|---|---|\n')
FILAS = ('| `web-prueba-1` | servidor | prueba | `lectura-web-prueba-1` | no | media | N1 | no | martes 22 a 24 | operaciones |\n'
         '| `sin-nivel` | servidor | prueba | `lectura-sin-nivel` | no | baja | nada | no | | operaciones |\n'
         '| `app-prueba` | url | prueba | https://prueba.example.com | si | media | N0 | pasivo | | producto |\n'
         '| `con-opcion` | servidor | prueba | `-oProxyCommand=malo` | no | baja | N0 | no | | operaciones |\n'
         '| `con-usuario` | servidor | prueba | `root@web-prueba-9` | no | baja | N0 | no | | operaciones |\n'
         '| `sin-destino` | servidor | prueba | | no | baja | N0 | no | | operaciones |\n')


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:400]) if (detalle and not ok) else ''))


def escribir(ruta, texto, crudo=False):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto if crudo else texto.encode('utf-8'))
    return ruta


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def reporte(encabezado='colector-salud formato=1', fin=True, antes='', **cambia):
    """Un reporte sano del colector. seccion='texto' reemplaza su contenido; seccion=None la saca."""
    base = {
        'sistema': 'fecha_epoch=%d\narranque_epoch=%d\nso=debian 12\nnucleo=6.1.0-18-amd64\ncpus=4' % (FECHA, FECHA - 31 * DIA),
        'disco': 'ext4|41152736|20576368|50|/\next4|10288448|4114379|40|/var\ntmpfs|813104|1024|1|/run',
        'inodos': 'ext4|2621440|131072|5|/\next4|655360|65536|10|/var\ntmpfs|203276|900|1|/run',
        'memoria': 'total_kb=8131044\ndisponible_kb=4960000\nswap_total_kb=2097148\nswap_libre_kb=2097148',
        'carga': 'uno=0.42\ncinco=0.31\nquince=0.20',
        'servicios': 'estado=running\ncaidas=0',
        'reinicio': 'pendiente=no\nmetodo=archivo',
        'reloj': 'sincronizado=si',
        'journal': 'uso=1.2G',
    }
    base.update(cambia)
    cuerpo = ''.join('[%s]\n%s\n' % (s, base[s]) for s in SECCIONES if base.get(s) is not None)
    for extra in sorted(set(base) - set(SECCIONES)):
        cuerpo += '[%s]\n%s\n' % (extra, base[extra])
    return antes + (encabezado + '\n' if encabezado else '') + cuerpo + ('[fin]\n' if fin else '')


def cargar_modulo():
    spec = importlib.util.spec_from_file_location('salud_host_en_prueba', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def adentro(mod, *args):
    """Corre main() del script dentro de este proceso (para poder reemplazarle la funcion que usa ssh)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = mod.main(list(args))
        except SystemExit as e:
            rc = e.code
    return rc, buf.getvalue()


def main():
    print('== salud-host')
    tmp = tempfile.mkdtemp(prefix='probar-salud-')

    def arch(nombre, texto, crudo=False):
        return escribir(os.path.join(tmp, nombre), texto, crudo)

    # --- el camino feliz
    rc, out = correr('--archivo', arch('sano.txt', reporte()))
    caso('reporte sano: OK (0), con los cinco chequeos y lo que NO mira',
         rc == 0 and out.startswith('SALUD de ') and ' -- OK' in out.splitlines()[0] and 'NO mira' in out
         and all(c in out for c in ('disco', 'inodos', 'servicios', 'reinicio', 'reloj')), out)
    caso('reporte sano: muestra memoria, carga y journal como dato, sin veredicto',
         'memoria' in out and 'carga' in out and 'journal' in out and 'sin veredicto' in out.lower(), out)

    # --- cada HALLAZGO
    rc, out = correr('--archivo', arch('disco.txt', reporte(disco='ext4|41152736|20576368|50|/\next4|10288448|9362488|91|/var')))
    caso('disco sobre el umbral: HALLAZGO (1), nombra el montaje y el porcentaje', rc == 1 and 'HALLAZGO' in out and '/var' in out and '91' in out, out)
    rc, out = correr('--archivo', arch('disco90.txt', reporte(disco='ext4|100|90|90|/')))
    caso('disco justo en el umbral por defecto (90): HALLAZGO', rc == 1, out)
    rc, out = correr('--archivo', arch('disco89.txt', reporte(disco='ext4|100|89|89|/')))
    caso('disco un punto por debajo del umbral: OK', rc == 0, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'disco.txt'), '--disco', '95')
    caso('el umbral de disco va por argumento: con --disco 95, un 91 es OK', rc == 0, out)
    rc, out = correr('--archivo', arch('inodos.txt', reporte(inodos='ext4|2621440|2569011|98|/\next4|655360|65536|10|/var')))
    caso('inodos sobre el umbral: HALLAZGO (1)', rc == 1 and 'inodos' in out and '98' in out, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'inodos.txt'), '--inodos', '99')
    caso('el umbral de inodos va por argumento', rc == 0, out)
    rc, out = correr('--archivo', arch('caido.txt', reporte(servicios='estado=degraded\ncaidas=2\ncaida=respaldo.service\ncaida=cola@pagos.service')))
    caso('un servicio caido: HALLAZGO (1), nombra las unidades', rc == 1 and 'respaldo.service' in out and 'cola@pagos.service' in out, out)
    def pendiente_hace(dias):
        return reporte(reinicio='pendiente=si\ndesde_epoch=%d\nmetodo=archivo' % (FECHA - dias * DIA))

    rc, out = correr('--archivo', arch('reinicio10.txt', pendiente_hace(10)))
    caso('reinicio pendiente hace 10 dias (umbral 7): HALLAZGO (1)', rc == 1 and 'hace 10 dias' in out, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'reinicio10.txt'), '--dias-reinicio', '30')
    caso('el umbral de dias de reinicio va por argumento', rc == 0 and 'hace 10 dia' in out, out)
    rc, out = correr('--archivo', arch('reinicio2.txt', pendiente_hace(2)))
    caso('reinicio pendiente hace 2 dias: OK, pero lo dice', rc == 0 and 'hace 2 dia' in out, out)
    rc, out = correr('--archivo', arch('reinicio7.txt', pendiente_hace(7)))
    caso('reinicio pendiente hace justo 7 dias (umbral 7): todavia OK, es "mas de"', rc == 0 and 'hace 7 dia' in out, out)
    rc, out = correr('--archivo', arch('reinicio8.txt', pendiente_hace(8)))
    caso('reinicio pendiente hace 8 dias (umbral 7): HALLAZGO (1)', rc == 1 and 'hace 8 dias' in out, out)
    rc, out = correr('--archivo', arch('reinicio-no.txt', reporte(reinicio='pendiente=no\nmetodo=nucleo')))
    caso('sin reinicio pendiente: OK y dice con que metodo lo supo el colector', rc == 0 and 'metodo: nucleo' in out, out)
    rc, out = correr('--archivo', arch('reloj.txt', reporte(reloj='sincronizado=no')))
    caso('reloj sin sincronizar: HALLAZGO (1)', rc == 1 and 'reloj' in out and 'HALLAZGO' in out, out)

    # --- los falsos positivos mas probables
    rc, out = correr('--archivo', arch('pseudo.txt', reporte(
        disco='ext4|100|50|50|/\ntmpfs|100|100|100|/run/lock\nsquashfs|100|100|100|/snap/core/1\niso9660|100|100|100|/media/cd\noverlay|100|99|99|/var/lib/x/merged',
        inodos='ext4|100|5|5|/\nsquashfs|100|100|100|/snap/core/1')))
    caso('tmpfs, squashfs, iso9660 y overlay al 100 %: no son disco que se llena, OK y dice cuantos saltea',
         rc == 0 and 'salte' in out.lower(), out)
    rc, out = correr('--archivo', arch('red.txt', reporte(
        disco='ext4|100|50|50|/\nnfs4|100|99|99|/compartido\n9p|956447724|611242516|97|/mnt/c\nrootfs|100|99|99|/init',
        inodos='ext4|100|5|5|/\n9p|999|-999001|-|/mnt/c\ncifs|100|100|100|/red')))
    caso('montajes de red o virtuales (nfs, 9p, cifs, rootfs), aun con cifras rotas: se saltean, no son HALLAZGO ni falta de dato',
         rc == 0 and 'salte' in out.lower(), out)
    rc, out = correr('--archivo', arch('btrfs.txt', reporte(disco='btrfs|100|50|50|/', inodos='btrfs|0|0|-|/')))
    caso('un sistema de archivos sin cuenta de inodos (btrfs): no es hallazgo ni falta de dato', rc == 0, out)
    rc, out = correr('--archivo', arch('ruido.txt', reporte(antes='Bienvenido al servidor\nUltimo acceso: ayer\n')))
    caso('lineas de cartel antes del encabezado: se ignoran', rc == 0, out)
    rc, out = correr('--archivo', arch('crlf.txt', reporte().replace('\n', '\r\n')))
    caso('reporte con saltos de Windows: se lee igual', rc == 0, out)
    rc, out = correr('--archivo', arch('espacio.txt', reporte(disco='ext4|100|95|95|/srv/datos de prueba')))
    caso('un montaje con espacios en el nombre: se lee entero', rc == 1 and '/srv/datos de prueba' in out, out)
    rc, out = correr('--archivo', arch('extra.txt', reporte(novedad='algo=1')))
    caso('una seccion que este script no conoce: se ignora, no rompe', rc == 0, out)

    # --- cada SIN DATOS
    rc, out = correr('--archivo', os.path.join(tmp, 'no-existe.txt'))
    caso('archivo ausente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('vacio.txt', ''))
    caso('archivo vacio: SIN DATOS (2), nunca OK', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('binario.bin', bytes(bytearray(range(256))) * 4, crudo=True))
    caso('archivo ilegible (binario): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('otra-cosa.txt', 'sh: 1: colector-salud: not found\n'))
    caso('una salida que no es del colector: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('formato2.txt', reporte(encabezado='colector-salud formato=2')))
    caso('otro formato del colector: SIN DATOS (2), dice cual lee', rc == 2 and 'formato' in out, out)
    rc, out = correr('--archivo', arch('sin-reloj.txt', reporte(reloj=None)))
    caso('falta una seccion: SIN DATOS (2) y la nombra', rc == 2 and 'reloj' in out and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('cortado.txt', reporte(fin=False)))
    caso('reporte cortado (sin la marca de fin): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('sin-fecha.txt', reporte(sistema='so=debian 12\ncpus=4')))
    caso('reporte sin fecha: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('doble.txt', reporte() + '[reloj]\nsincronizado=si\n'))
    caso('lo que viene despues de la marca de fin no cuenta', rc == 0, out)
    doble = reporte().replace('[reloj]\n', '[reloj]\nsincronizado=si\n[reloj]\n')
    rc, out = correr('--archivo', arch('repetida.txt', doble))
    caso('una seccion repetida: SIN DATOS (2), no gana ninguna', rc == 2 and 'reloj' in out, out)
    viejo = reporte(sistema='fecha_epoch=%d\narranque_epoch=%d\nso=debian 12\nnucleo=x\ncpus=4' % (AHORA - 3 * DIA, AHORA - 40 * DIA))
    rc, out = correr('--archivo', arch('viejo.txt', viejo))
    caso('un reporte de hace tres dias no dice como esta hoy: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'viejo.txt'), '--horas-reporte', '0')
    caso('con --horas-reporte 0 se lee un reporte viejo a proposito, y dice su edad', rc == 0 and 'hace 3 dias' in out, out)
    rc, out = correr('--archivo', arch('sd-servicios.txt', reporte(servicios='sin_dato=no hay systemctl')))
    caso('el colector no pudo medir los servicios: ese chequeo es SIN DATOS (2), no OK', rc == 2 and 'servicios' in out and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('sd-reloj.txt', reporte(reloj='sincronizado=desconocido')))
    caso('reloj desconocido: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('sd-reinicio.txt', reporte(reinicio='pendiente=desconocido\nmetodo=ninguno')))
    caso('reinicio desconocido: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('sd-reinicio2.txt', reporte(reinicio='pendiente=si\ndesde_epoch=desconocido\nmetodo=needs-restarting')))
    caso('reinicio pendiente sin fecha: no se puede comparar con el umbral, SIN DATOS (2)', rc == 2 and 'reinicio' in out, out)
    rc, out = correr('--archivo', arch('cuenta.txt', reporte(servicios='estado=degraded\ncaidas=2\ncaida=uno.service')))
    caso('la lista de caidos no coincide con su cuenta (salida cortada): SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('sin-cuenta.txt', reporte(servicios='estado=running')))
    caso('sin la cuenta de caidos no se sabe si la lista corrio: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('fila-mala.txt', reporte(disco='ext4|100|50|/')))
    caso('una fila de disco mal formada: SIN DATOS (2)', rc == 2 and 'disco' in out, out)
    rc, out = correr('--archivo', arch('solo-tmpfs.txt', reporte(disco='tmpfs|100|1|1|/run')))
    caso('si no queda ningun sistema de archivos contable, disco es SIN DATOS (Regla del cero)', rc == 2 and 'disco' in out, out)
    rc, out = correr('--archivo', arch('disco-vacio.txt', reporte(disco='')))
    caso('seccion de disco vacia: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', arch('mixto.txt', reporte(disco='ext4|100|97|97|/', reloj='sincronizado=desconocido')))
    caso('un HALLAZGO y un chequeo sin datos a la vez: sale 1 y el otro chequeo dice SIN DATOS',
         rc == 1 and 'HALLAZGO' in out and 'SIN DATOS' in out, out)
    rc, out = correr()
    caso('sin --archivo ni --ssh: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--archivo', os.path.join(tmp, 'sano.txt'), '--ssh', 'web-prueba-1')
    caso('--archivo y --ssh juntos: SIN DATOS (2), no elige', rc == 2 and 'SIN DATOS' in out, out)

    # --- lo que devuelve un servidor es dato, no instruccion: no se pasa crudo a la pantalla
    escape = chr(27) + '[2J' + chr(7)
    rc, out = correr('--archivo', arch('escape.txt', reporte(servicios='estado=degraded\ncaidas=1\ncaida=mala%s.service' % escape)))
    caso('caracteres de control en un nombre que viene del servidor: no llegan a la salida', rc == 1 and chr(27) not in out and chr(7) not in out, repr(out[:300]))

    # --- --json
    rc, out = correr('--archivo', os.path.join(tmp, 'disco.txt'), '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    caso('--json: estado, los cinco chequeos con su estado, los umbrales y lo que no mira',
         rc == 1 and d.get('estado') == 'HALLAZGO' and [c['chequeo'] for c in d.get('chequeos', [])] == ['disco', 'inodos', 'servicios', 'reinicio', 'reloj']
         and d['umbrales']['disco'] == 90 and d.get('no_mira') and all(ord(ch) < 128 for ch in out), out[:400])
    rc, out = correr('--archivo', os.path.join(tmp, 'vacio.txt'), '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    caso('--json con un reporte ilegible: estado SIN DATOS y su motivo', rc == 2 and d.get('estado') == 'SIN DATOS' and d.get('motivo'), out[:300])

    # --- --ssh: pasa por el inventario ANTES de conectarse (la funcion que usa ssh se reemplaza)
    inv = escribir(os.path.join(tmp, 'repo', 'cerebro-digital', 'modulo-a', 'operacion', 'inventario.md'), '# Inventario\n\n' + CABECERA + FILAS)
    repo = os.path.join(tmp, 'repo')
    try:
        mod = cargar_modulo()
    except Exception as e:                                      # el script no existe o no carga
        mod = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    if mod is not None:
        llamadas = []

        def falso_ssh(respuesta):
            def traer(destino, tope):
                llamadas.append(destino)
                return respuesta
            return traer

        mod.traer_por_ssh = falso_ssh((0, reporte(), ''))
        rc, out = adentro(mod, '--ssh', 'web-prueba-2', '--raiz', repo)
        caso('--ssh con un alias que no esta en el inventario: FRENA (1) y NO se conecta',
             rc == 1 and 'FRENA' in out and 'no esta en el inventario' in out and llamadas == [], out)
        rc, out = adentro(mod, '--ssh', 'sin-nivel', '--raiz', repo)
        caso('--ssh con un alias sin nivel para la IA: FRENA (1) y NO se conecta', rc == 1 and 'FRENA' in out and llamadas == [], out)
        rc, out = adentro(mod, '--ssh', 'app-prueba', '--raiz', repo)
        caso('--ssh contra un activo que no es un servidor: FRENA (1) y NO se conecta', rc == 1 and 'FRENA' in out and llamadas == [], out)
        rc, out = adentro(mod, '--ssh', 'web-prueba-1', '--raiz', os.path.join(tmp, 'sin-repo'))
        caso('--ssh sin inventario: SIN DATOS (2) y NO se conecta', rc == 2 and 'SIN DATOS' in out and llamadas == [], out)
        for alias, que in (('con-opcion', 'empieza con un guion'), ('con-usuario', 'trae un usuario'), ('sin-destino', 'esta vacio')):
            rc, out = adentro(mod, '--ssh', alias, '--raiz', repo)
            caso('--ssh cuando el Destino del inventario %s: SIN DATOS (2) y NO se conecta' % que, rc == 2 and 'SIN DATOS' in out and llamadas == [], out)
        rc, out = adentro(mod, '--ssh', 'web-prueba-1', '--raiz', repo)
        caso('--ssh con un alias autorizado: se conecta UNA vez, al Destino del inventario (no al alias), y da OK',
             rc == 0 and llamadas == ['lectura-web-prueba-1'] and out.startswith('SALUD de web-prueba-1'), (llamadas, out))
        del llamadas[:]
        rc, out = adentro(mod, '--ssh', 'web-prueba-1', '--raiz', repo, '--guardar')
        guardados = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(repo, 'borrador')) for f in fs]
        caso('--guardar deja el reporte crudo en borrador/operacion/<fecha>/ y dice donde',
             rc == 0 and len(guardados) == 1 and os.sep + os.path.join('borrador', 'operacion') + os.sep in guardados[0]
             and 'salud-web-prueba-1' in os.path.basename(guardados[0]) and 'borrador' in out, (guardados, out))
        if guardados:
            rc2, out2 = correr('--archivo', guardados[0])
            caso('el reporte guardado se vuelve a leer con --archivo y da lo mismo (lo usa quien verifica)', rc2 == 0, out2)
        for respuesta, que in (((255, '', 'no se pudo conectar'), 'ssh no conecta (255)'),
                               ((127, '', 'el colector no esta instalado'), 'el colector no esta (127)'),
                               ((None, '', 'no hay ssh en esta maquina'), 'no hay ssh'),
                               ((0, 'Bienvenido\n', ''), 'ssh entra pero no devuelve un reporte (la clave no tiene el comando forzado)'),
                               ((1, reporte(), 'el colector salio con 1'), 'el colector termino con error aunque imprimio un reporte'),
                               ((0, '', ''), 'ssh no devuelve nada')):
            mod.traer_por_ssh = falso_ssh(respuesta)
            rc, out = adentro(mod, '--ssh', 'web-prueba-1', '--raiz', repo)
            caso('--ssh cuando %s: SIN DATOS (2), nunca OK' % que, rc == 2 and 'SIN DATOS' in out, out)
        orden = mod.orden_ssh('lectura-web-prueba-1', 60)
        caso('la orden de ssh: sin preguntar nada (BatchMode), sin terminal (-T), sin aceptar claves nuevas, y SIN comando remoto',
             orden[0] == 'ssh' and 'BatchMode=yes' in orden and '-T' in orden and 'StrictHostKeyChecking=yes' in orden
             and orden[-2:] == ['--', 'lectura-web-prueba-1'], orden)
        mot = mod.motivo_ssh(255, 'ssh: connect to host 10.1.2.3 port 22: Connection timed out')
        caso('el motivo de una falla de ssh no repite la direccion del servidor', '10.1.2.3' not in mot and mot, mot)

    # --- el colector, como texto: es lo unico que corre en el servidor
    if os.path.isfile(COLECTOR):
        with open(COLECTOR, 'rb') as h:
            crudo = h.read()
        texto = crudo.decode('utf-8', errors='replace')
        codigo = [l for l in texto.split('\n') if l.strip() and not l.strip().startswith('#')]
        caso('el colector es ASCII puro y sin saltos de Windows (corre con sh en el servidor)', all(b < 128 for b in crudo) and b'\r' not in crudo)
        caso('el colector declara el formato que este script lee', "colector-salud formato=1" in texto)
        marcas = re.findall(r"^\s*echo '\[([a-z]+)\]'", texto, re.M)
        caso('el colector imprime las secciones que este script exige, en orden, y la marca de fin',
             marcas == list(SECCIONES) + ['fin'], marcas)
        salidas = [m for l in codigo for m in re.findall(r'>+\s*([^\s;|)]+)', l)]
        caso('el colector no escribe en ningun archivo: solo redirige a /dev/null o a otra salida',
             salidas and all(s == '/dev/null' or s.startswith('&') for s in salidas), sorted(set(salidas)))
        prohibidas = ('env', 'printenv', 'ps', 'rm', 'mv', 'dd', 'tee', 'sudo', 'curl', 'wget', 'eval', 'kill', 'chmod', 'chown',
                      'touch', 'mkdir', 'reboot', 'shutdown')
        usadas = sorted(set(p for l in codigo for p in re.findall(r'[A-Za-z_][A-Za-z0-9_-]*', l) if p in prohibidas))
        caso('el colector no usa ordenes que cambian algo ni que muestran el entorno o los procesos', usadas == [] and '/environ' not in texto, usadas)
        verbos = re.findall(r'systemctl\s+([a-z-]+)', '\n'.join(codigo))
        caso('el colector solo le pide a systemctl que liste o informe', verbos and all(v in ('is-system-running', 'list-units') for v in verbos), verbos)
        caso('el colector no acepta argumentos ni lee el comando que mando el cliente', '"$#"' in texto and 'SSH_ORIGINAL_COMMAND' not in '\n'.join(codigo))
    else:
        caso('existe el colector en assets/ de la skill', False, COLECTOR)

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('salud-host.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
