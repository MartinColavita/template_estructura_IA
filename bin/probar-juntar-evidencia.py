#!/usr/bin/env python3
"""Prueba de bin/juntar-evidencia.py con archivos de mentira y un repositorio de mentira.
Se corre:  python -B bin/probar-juntar-evidencia.py   -> OK o FALLA, con el detalle de cada caso."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'juntar-evidencia.py')
ESPERADOS = []
SECRETO = 'token=VALOR-QUE-NO-SE-MUESTRA-123'


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)[:400]) if (detalle and not ok) else ''))


def escribir(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(contenido if isinstance(contenido, bytes) else contenido.encode('utf-8'))
    return ruta


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def como_json(out):
    try:
        return json.loads(out)
    except ValueError:
        return {}


def sha(ruta):
    try:
        with open(ruta, 'rb') as h:
            return hashlib.sha256(h.read()).hexdigest()
    except OSError:
        return ''


def carpetas(base):
    return sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))) if os.path.isdir(base) else []


def escribible(ruta):
    os.chmod(ruta, stat.S_IREAD | stat.S_IWRITE)


def main():
    print('== juntar-evidencia')
    tmp = tempfile.mkdtemp(prefix='probar-evid-')
    repo = os.path.join(tmp, 'repo')
    os.makedirs(os.path.join(repo, 'borrador'))
    afuera = os.path.join(tmp, 'evidencia')
    log = escribir(os.path.join(tmp, 'origen', 'auth.log'), 'linea 1\n' + SECRETO + '\nlinea 3\n')
    binario = escribir(os.path.join(tmp, 'origen', 'volcado.bin'), bytes(bytearray(range(256))) * 8)
    otro_log = escribir(os.path.join(tmp, 'origen', 'otro', 'auth.log'), 'otro registro con el mismo nombre\n')

    def juntar(*args, destino=afuera):
        return correr('--incidente', 'INC-001', '--destino', destino, '--pedido-por', 'responsable de seguridad (rol)', '--raiz', repo, *args)

    # --- camino feliz
    rc, out = juntar('--fuente', log, '--fuente', binario, '--json')
    d = como_json(out)
    hechas = carpetas(afuera)
    caso('dos fuentes legibles, destino afuera del repositorio: OK (0) y una carpeta nueva', rc == 0 and d.get('estado') == 'OK' and len(hechas) == 1, out[:400])
    carpeta = os.path.join(afuera, hechas[0]) if hechas else ''
    man = os.path.join(carpeta, 'manifiesto-custodia.json')
    try:
        with open(man, encoding='utf-8') as h:
            m = json.load(h)
    except (OSError, ValueError):
        m = {}
    items = m.get('items', [])
    caso('el manifiesto de custodia dice que, de donde, cuando, quien lo pidio y el hash de cada archivo',
         m.get('incidente') == 'INC-001' and m.get('pedido_por') == 'responsable de seguridad (rol)' and m.get('juntado_en')
         and len(items) == 2 and all(k in items[0] for k in ('archivo', 'origen', 'bytes', 'sha256', 'modificado_origen')), m)
    caso('el hash del manifiesto es el SHA-256 del original', len(items) == 2 and items[0]['sha256'] == sha(log) and items[1]['sha256'] == sha(binario), items)
    copias = [os.path.join(carpeta, it['archivo']) for it in items]
    caso('las copias son identicas byte a byte al original', len(copias) == 2 and all(os.path.isfile(c) for c in copias)
         and sha(copias[0]) == sha(log) and sha(copias[1]) == sha(binario), copias)
    caso('las copias quedan de solo lectura', copias and not (os.stat(copias[0]).st_mode & stat.S_IWRITE), copias)
    caso('el original no se toca: sigue igual', sha(log) == hashlib.sha256(('linea 1\n' + SECRETO + '\nlinea 3\n').encode()).hexdigest())
    caso('la salida dice el hash del manifiesto (va al documento del incidente)', d.get('sha256_manifiesto') == sha(man), d.get('sha256_manifiesto'))
    rc, out = juntar('--fuente', log)
    caso('la salida para una persona no muestra el contenido de lo juntado', rc == 0 and SECRETO not in out and 'VALOR-QUE' not in out
         and 'NO mira' in out, out)
    caso('cada corrida va a su propia carpeta, sin pisar la anterior', len(carpetas(afuera)) == 2, carpetas(afuera))
    rc, out = juntar('--fuente', log, '--fuente', otro_log, '--json')
    d = como_json(out)
    nombres = [it['archivo'] for it in d.get('items', [])]
    caso('dos fuentes con el mismo nombre se copian las dos, con nombres distintos', rc == 0 and len(set(nombres)) == 2, nombres)

    # --- FRENA: la evidencia nunca adentro del repositorio
    for destino, que in ((os.path.join(repo, 'borrador', 'evidencia'), 'en borrador/'), (repo, 'en la raiz'),
                         (os.path.join(repo, 'x', '..', 'cerebro-digital'), 'con .. en la ruta')):
        rc, out = juntar('--fuente', log, destino=destino)
        caso('destino adentro del repositorio (%s): FRENA (1) y no copia nada' % que,
             rc == 1 and 'FRENA' in out and not os.path.exists(os.path.join(repo, 'borrador', 'evidencia'))
             and not os.path.exists(os.path.join(repo, 'cerebro-digital')), out)

    # --- FRENA tambien adentro de CUALQUIER repositorio git, no solo el del Cerebro (F2 7)
    otro = os.path.join(tmp, 'otro-repo')
    os.makedirs(os.path.join(otro, '.git'))
    rc, out = juntar('--fuente', log, destino=os.path.join(otro, 'evidencia', 'inc'))
    caso('destino adentro de otro repositorio git (un ancestro con .git): FRENA (1) y no copia nada',
         rc == 1 and 'FRENA' in out and 'git' in out and not os.path.exists(os.path.join(otro, 'evidencia')), out)
    arbol = os.path.join(tmp, 'worktree')
    escribir(os.path.join(arbol, '.git'), 'gitdir: /otra/parte/.git/worktrees/x\n')
    rc, out = juntar('--fuente', log, destino=os.path.join(arbol, 'evidencia'))
    caso('destino adentro de un worktree (.git es un archivo): FRENA (1)', rc == 1 and 'FRENA' in out, out)
    rc, out = correr('--help')
    caso('--raiz queda documentado como solo para las pruebas', '--raiz' in out and 'pruebas' in out.rsplit('--raiz', 1)[-1][:200], out[-600:])
    spec = importlib.util.spec_from_file_location('juntar_evidencia_en_prueba', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        apto = getattr(mod, 'python_apto', None)
    except Exception as e:
        apto = None
        caso('el script se puede cargar como modulo', False, '%s: %s' % (type(e).__name__, e))
    caso('Python 3.7 en Windows (realpath no resuelve junctions): no corre, y lo dice',
         apto is not None and apto((3, 7, 9), 'nt') and '3.8' in apto((3, 7, 9), 'nt'), apto and apto((3, 7, 9), 'nt'))
    caso('Python 3.8 en Windows, o 3.7 fuera de Windows: corre', apto is not None and not apto((3, 8, 0), 'nt') and not apto((3, 7, 0), 'posix'))

    # --- SIN DATOS
    rc, out = juntar('--fuente', log, '--fuente', os.path.join(tmp, 'no-existe.log'), '--json')
    d = como_json(out)
    caso('una fuente que no existe: SIN DATOS (2), las otras se copian igual y queda anotada',
         rc == 2 and d.get('estado') == 'SIN DATOS' and len(d.get('items', [])) == 1 and d.get('sin_datos'), out[:400])
    rc, out = juntar('--fuente', os.path.join(tmp, 'origen'))
    caso('una fuente que es una carpeta: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    vacio = escribir(os.path.join(tmp, 'origen', 'vacio.log'), '')
    rc, out = juntar('--fuente', vacio)
    caso('una fuente vacia: se copia (es evidencia) pero da SIN DATOS (2)', rc == 2 and 'vacio' in out, out)
    rc, out = juntar()
    caso('sin --fuente: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    rc, out = correr('--incidente', 'INC-001', '--destino', afuera, '--raiz', repo, '--fuente', log)
    caso('sin --pedido-por: SIN DATOS (2), la cadena de custodia necesita quien lo pidio', rc == 2 and 'pedido' in out, out)
    rc, out = correr('--incidente', 'incidente-1', '--destino', afuera, '--pedido-por', 'x', '--raiz', repo, '--fuente', log)
    caso('un incidente que no es INC-nnn: SIN DATOS (2)', rc == 2, out)
    rc, out = correr('--incidente', 'INC-001', '--pedido-por', 'x', '--raiz', repo, '--fuente', log)
    caso('sin --destino: SIN DATOS (2)', rc == 2, out)

    # --- --verificar
    rc, out = correr('--verificar', carpeta)
    caso('--verificar sin --hash-manifiesto: SIN DATOS (2), sin el ancla no se sabe si el manifiesto cambio',
         rc == 2 and 'SIN DATOS' in out.splitlines()[0] and '--hash-manifiesto' in out, out)
    rc, out = correr('--verificar', carpeta, '--hash-manifiesto', sha(man))
    caso('--verificar con el hash del manifiesto que quedo en el incidente: OK (0)', rc == 0, out)
    rc, out = correr('--verificar', carpeta, '--hash-manifiesto', '0' * 64)
    caso('--verificar con otro hash de manifiesto: HALLAZGO (1), el manifiesto cambio', rc == 1 and 'manifiesto' in out, out)
    if len(copias) == 2 and all(os.path.isfile(c) for c in copias):
        escribible(copias[0])
        with open(copias[0], 'ab') as h:
            h.write(b'agregado despues\n')
        rc, out = correr('--verificar', carpeta, '--json')
        d = como_json(out)
        caso('--verificar con una copia modificada: HALLAZGO (1) y la nombra',
             rc == 1 and d.get('estado') == 'HALLAZGO' and any(os.path.basename(copias[0]) in x for x in d.get('hallazgos', [])), out[:400])
        escribible(copias[1])
        os.remove(copias[1])
        rc, out = correr('--verificar', carpeta)
        caso('--verificar con una copia borrada: HALLAZGO (1)', rc == 1 and os.path.basename(copias[1]) in out, out)
    else:
        caso('--verificar con una copia modificada o borrada: HALLAZGO (1)', False, 'no hay copias para modificar')
    rc, out = correr('--verificar', os.path.join(tmp, 'no-existe'))
    caso('--verificar sin manifiesto: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out)
    roto = os.path.join(tmp, 'rota')
    escribir(os.path.join(roto, 'manifiesto-custodia.json'), '{esto no es json')
    rc, out = correr('--verificar', roto)
    caso('--verificar con el manifiesto ilegible: SIN DATOS (2)', rc == 2, out)
    escribir(os.path.join(tmp, 'sin-items', 'manifiesto-custodia.json'), json.dumps({'incidente': 'INC-001', 'items': []}))
    rc, out = correr('--verificar', os.path.join(tmp, 'sin-items'))
    caso('--verificar con un manifiesto sin archivos: SIN DATOS (2), nunca OK', rc == 2, out)
    rc, out = correr('--verificar', carpeta, '--json')
    caso('--json es ASCII', all(ord(c) < 128 for c in out))

    with open(SCRIPT, 'rb') if os.path.isfile(SCRIPT) else io.BytesIO(b'\xff') as h:
        caso('juntar-evidencia.py es ASCII puro', all(b < 128 for b in h.read()))

    shutil.rmtree(tmp, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
