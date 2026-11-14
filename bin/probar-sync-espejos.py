#!/usr/bin/env python3
"""Prueba de bin/sync-espejos.py: regenerar un espejo sin dejarlo a medias y sin pisar lo que se edito en el espejo.
Se corre:  python -B bin/probar-sync-espejos.py   -> OK o FALLA, con el detalle de cada caso."""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('sync', os.path.join(AQUI, 'sync-espejos.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
ESPERADOS = []
SALTEADOS = []   # lo que no corrio se dice en la ultima linea: no es OK


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(p, t, hace=0):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(t)
    if hace:
        viejo = time.time() - hace
        os.utime(p, (viejo, viejo))


def leer(p):
    if not os.path.isfile(p):
        return None
    with open(p, encoding='utf-8') as h:
        return h.read()


def con_rename(falla, accion):
    """Corre accion() con os.rename reemplazado: falla(n) dice si la llamada numero n (desde 1) tira OSError."""
    llamadas, real = [], os.rename

    def rename(a, b):
        llamadas.append((a, b))
        if falla(len(llamadas)):
            raise OSError('otro proceso tiene abierta la carpeta del espejo')
        return real(a, b)
    sync.os.rename = rename
    try:
        return accion()
    finally:
        sync.os.rename = real


def main():
    print('== sync-espejos')
    tmp = tempfile.mkdtemp(prefix='probar-sync-')
    fuente, espejo = os.path.join(tmp, 'fuente'), os.path.join(tmp, 'espejo')
    a_esp, b_esp = os.path.join(espejo, 'a', 'SKILL.md'), os.path.join(espejo, 'b', 'SKILL.md')
    al_lado = lambda: sorted(x for x in os.listdir(tmp) if x not in ('fuente', 'fuente-rota'))
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v1\n')
    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v1\n')

    ok, msj = sync.regenerar(fuente, espejo)
    caso('espejo que no existe: se crea igual a la fuente', ok and leer(a_esp) == 'a v1\n', msj)
    caso('y deja al lado el manifiesto del sync (y nada mas)', al_lado() == ['espejo', 'espejo.sync.json'], str(al_lado()))

    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v2\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('la fuente cambio: el espejo se actualiza', ok and leer(a_esp) == 'a v2\n', msj)
    caso('no quedan carpetas temporales ni copias viejas al lado del espejo', al_lado() == ['espejo', 'espejo.sync.json'],
         str(al_lado()))

    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v1\n', hace=60)
    escribir(b_esp, 'b editado a mano en el espejo\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('un archivo editado en el espejo: FRENA, no lo pisa y dice como regenerar igual',
         not ok and 'b/SKILL.md' in msj and '--pisar' in msj and (leer(b_esp) or '').startswith('b editado'), msj)
    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v2 que llego con un git pull\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('editado en el espejo y despues la fuente mas nueva (un pull): FRENA igual, no se pierde la edicion',
         not ok and (leer(b_esp) or '').startswith('b editado'), msj)
    ok, msj = sync.regenerar(fuente, espejo, pisar=True)
    caso('con pisar=True se regenera igual', ok and leer(b_esp) == 'b v2 que llego con un git pull\n', msj)

    escribir(os.path.join(espejo, 'c', 'SKILL.md'), 'agregado a mano en el espejo\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('un archivo agregado en el espejo: FRENA y no lo borra', not ok and os.path.isfile(os.path.join(espejo, 'c', 'SKILL.md')), msj)
    shutil.rmtree(os.path.join(espejo, 'c'), ignore_errors=True)

    shutil.rmtree(os.path.join(fuente, 'b'))
    ok, msj = sync.regenerar(fuente, espejo)
    caso('la fuente borro (o renombro) uno que el espejo tenia tal cual: se saca sin frenar',
         ok and not os.path.exists(os.path.join(espejo, 'b')), msj)
    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v3\n')
    sync.regenerar(fuente, espejo)
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v2 del pull\n')
    escribir(a_esp, 'a v2 del pull\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('un git pull que trae el mismo cambio a la fuente y al espejo (skills versionadas): no frena',
         ok and leer(a_esp) == 'a v2 del pull\n', msj)
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v2\n')
    sync.regenerar(fuente, espejo)

    if os.path.exists(espejo + '.sync.json'):
        os.remove(espejo + '.sync.json')
    escribir(os.path.join(espejo, 'c', 'SKILL.md'), 'solo en el espejo\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('sin manifiesto (un espejo de antes): lo que solo esta en el espejo FRENA', not ok and 'c/SKILL.md' in msj, msj)
    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v3\n', hace=60)
    escribir(b_esp, 'b editado sin manifiesto\n')
    shutil.rmtree(os.path.join(espejo, 'c'), ignore_errors=True)
    ok, msj = sync.regenerar(fuente, espejo)
    caso('sin manifiesto: distinto y mas nuevo que la fuente FRENA', not ok and 'b/SKILL.md' in msj, msj)
    sync.regenerar(fuente, espejo, pisar=True)

    roto = os.path.join(tmp, 'fuente-rota')
    escribir(os.path.join(roto, 'a', 'SKILL.md'), 'x\n')
    original = sync._copiar

    def copia_que_se_corta(f, d):
        escribir(os.path.join(d, 'a', 'SKILL.md'), 'x\n')
        raise OSError('disco lleno a mitad de la copia')
    sync._copiar = copia_que_se_corta
    try:
        ok, msj = sync.regenerar(roto, espejo, pisar=True)
    finally:
        sync._copiar = original
    caso('si la copia falla a mitad de camino, el espejo anterior queda entero',
         not ok and leer(a_esp) == 'a v2\n' and leer(b_esp) == 'b v3\n', msj)
    caso('y saca la copia a medias', al_lado() == ['espejo', 'espejo.sync.json'], str(al_lado()))

    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v3\n')
    ok, msj = sync.regenerar(fuente, espejo, dry_run=True)
    caso('dry-run: dice que regeneraria y no toca el espejo', ok and 'dry-run' in msj and leer(a_esp) == 'a v2\n', msj)

    escribir(os.path.join(fuente, 'd', 'SKILL.md'), 'd nueva\n')
    shutil.rmtree(os.path.join(fuente, 'b'))
    ok, msj = con_rename(lambda n: True, lambda: sync.regenerar(fuente, espejo))
    caso('si no se puede cambiar la carpeta entera (Windows, otro proceso la tiene abierta): archivo por archivo',
         ok and leer(a_esp) == 'a v3\n' and 'archivo por archivo' in msj, msj)
    caso('archivo por archivo tambien agrega lo nuevo y saca lo que la fuente ya no tiene',
         leer(os.path.join(espejo, 'd', 'SKILL.md')) == 'd nueva\n' and not os.path.exists(os.path.join(espejo, 'b')),
         str(sorted(os.listdir(espejo))))
    caso('y no quedan la copia nueva ni la vieja al lado', al_lado() == ['espejo', 'espejo.sync.json'], str(al_lado()))

    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v4\n')
    ok, msj = con_rename(lambda n: n == 2, lambda: sync.regenerar(fuente, espejo))
    caso('si falla poner el nuevo despues de sacar el viejo: el viejo vuelve y se actualiza archivo por archivo',
         ok and leer(a_esp) == 'a v4\n' and al_lado() == ['espejo', 'espejo.sync.json'], msj + ' ' + str(al_lado()))

    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v5\n')
    ok, msj = con_rename(lambda n: n >= 2, lambda: sync.regenerar(fuente, espejo))
    caso('si tampoco puede volver a poner el viejo: SIN DATOS, dice donde quedo cada copia y no borra ninguna',
         not ok and msj.startswith('SIN DATOS') and len([x for x in os.listdir(tmp) if '.viejo-' in x or '.nuevo-' in x]) == 2,
         msj + ' ' + str(os.listdir(tmp)))

    ok, msj = sync.regenerar(os.path.join(tmp, 'no-existe'), os.path.join(tmp, 'otro-espejo'))
    caso('una fuente que no existe: no toca nada', not ok and msj.startswith('SIN DATOS'), msj)

    probar_plan_b(os.path.join(tmp, 'plan-b'))
    probar_con_git(os.path.join(tmp, 'repo-' + chr(0xd1) + 'and' + chr(0xfa)))   # una carpeta con acentos, como OneDrive

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.%s' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS),
                                                         (' SALTEADOS: ' + '; '.join(SALTEADOS)) if SALTEADOS else ''))
    return 1 if fallas else 0


def probar_plan_b(base):
    fuente, espejo = os.path.join(base, 'fuente'), os.path.join(base, 'espejo')
    escribir(os.path.join(fuente, 'a', 'Skill.md'), 'a\n')
    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v1\n')
    sync.regenerar(fuente, espejo)

    os.rename(os.path.join(fuente, 'a', 'Skill.md'), os.path.join(fuente, 'a', 'SKILL.md.tmp'))
    os.rename(os.path.join(fuente, 'a', 'SKILL.md.tmp'), os.path.join(fuente, 'a', 'SKILL.md'))
    ok, msj = con_rename(lambda n: True, lambda: sync.regenerar(fuente, espejo))
    caso('archivo por archivo, un nombre que solo cambia mayusculas (Skill.md -> SKILL.md) queda, no se borra',
         ok and os.listdir(os.path.join(espejo, 'a')) == ['SKILL.md'] and leer(os.path.join(espejo, 'a', 'SKILL.md')) == 'a\n',
         msj + ' ' + str(os.listdir(espejo)))

    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v2\n')
    reemplazo_real, b_esp = os.replace, os.path.join(espejo, 'b', 'SKILL.md')

    def reemplazo(a, b):
        if os.path.abspath(b) == os.path.abspath(b_esp):
            raise PermissionError(13, 'otro proceso tiene abierto el archivo')
        return reemplazo_real(a, b)
    sync.os.replace = reemplazo
    try:
        ok, msj = con_rename(lambda n: True, lambda: sync.regenerar(fuente, espejo))
    finally:
        sync.os.replace = reemplazo_real
    caso('archivo por archivo con un archivo abierto: SIN DATOS y no deja una copia a medio poner adentro del espejo',
         not ok and msj.startswith('SIN DATOS') and sorted(os.listdir(os.path.join(espejo, 'b'))) == ['SKILL.md'],
         msj + ' ' + str(os.listdir(os.path.join(espejo, 'b'))))
    ok, msj = sync.regenerar(fuente, espejo)
    caso('y la corrida siguiente lo completa, sin frenar', ok and leer(b_esp) == 'b v2\n', msj)

    escribir(os.path.join(fuente, 'b', 'SKILL.md'), 'b v3\n')
    lugar_real = sync._en_el_lugar
    sync._en_el_lugar = lambda n, e: None
    try:
        ok, msj = con_rename(lambda n: True, lambda: sync.regenerar(fuente, espejo))
    finally:
        sync._en_el_lugar = lugar_real
    caso('si el espejo no quedo igual a la fuente, no dice OK: SIN DATOS con lo que difiere',
         not ok and msj.startswith('SIN DATOS') and 'b/SKILL.md' in msj, msj)

    os.rename(os.path.join(fuente, 'b'), os.path.join(fuente, 'b.tmp'))
    os.rename(os.path.join(fuente, 'b.tmp'), os.path.join(fuente, 'B'))
    ok, msj = con_rename(lambda n: True, lambda: sync.regenerar(fuente, espejo, pisar=True))
    caso('archivo por archivo, una carpeta que solo cambia mayusculas (b/ -> B/) queda con el nombre nuevo',
         ok and 'B' in os.listdir(espejo) and 'b' not in os.listdir(espejo), msj + ' ' + str(os.listdir(espejo)))

    escribir(os.path.join(fuente, 'B', 'SKILL.md'), 'b v4\n')
    copiar_real = sync._copiar

    def copia_y_la_fuente_cambia(f, d):
        copiar_real(f, d)
        escribir(os.path.join(f, 'B', 'SKILL.md'), 'b v5, guardada durante el sync\n')
    sync._copiar = copia_y_la_fuente_cambia
    try:
        ok, msj = sync.regenerar(fuente, espejo)
    finally:
        sync._copiar = copiar_real
    ok2, msj2 = sync.regenerar(fuente, espejo)
    caso('si la fuente cambia durante el sync: SIN DATOS, y la corrida siguiente no frena de mas (el manifiesto se renueva)',
         not ok and ok2 and leer(os.path.join(espejo, 'B', 'SKILL.md')) == 'b v5, guardada durante el sync\n', msj + ' / ' + msj2)

    volcar_real = sync.json.dump
    sync.json.dump = lambda *a, **k: (_ for _ in ()).throw(OSError('OneDrive tiene abierto el manifiesto'))
    try:
        ok, msj = sync.regenerar(fuente, espejo, pisar=True)
    finally:
        sync.json.dump = volcar_real
    caso('si no se puede escribir el manifiesto, saca el viejo (que ya no dice como quedo el espejo)',
         ok and not os.path.exists(espejo + '.sync.json'), msj)


def probar_con_git(repo):
    if shutil.which('git') is None:
        SALTEADOS.append('los casos con git (no hay git en el PATH)')
        print('  SALTEADO %s' % SALTEADOS[-1])
        return
    fuente, espejo = os.path.join(repo, 'fuente'), os.path.join(repo, 'espejo')
    git = lambda *a: subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'core.autocrlf=false']
                                    + list(a), capture_output=True)
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v1\n')
    sync.regenerar(fuente, espejo)
    escribir(os.path.join(repo, '.gitignore'), '*.sync.json\n')
    git('init', '-q')
    git('add', '-A')
    git('commit', '-qm', 'base')
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v2\n')
    escribir(os.path.join(espejo, 'a', 'SKILL.md'), 'a v2\n')
    git('commit', '-qam', 'lo que trae un pull: la fuente y el espejo versionado, juntos')
    escribir(os.path.join(fuente, 'a', 'SKILL.md'), 'a v3, editada en la fuente\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('un pull que trajo la fuente y el espejo, y despues una edicion en la fuente: no frena (el espejo es el del commit)',
         ok and leer(os.path.join(espejo, 'a', 'SKILL.md')) == 'a v3, editada en la fuente\n', msj)
    escribir(os.path.join(espejo, 'a', 'SKILL.md'), 'editado a mano en el espejo, sin commitear\n')
    ok, msj = sync.regenerar(fuente, espejo)
    caso('con git, una edicion en el espejo que no esta en el commit sigue frenando', not ok and 'a/SKILL.md' in msj, msj)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
