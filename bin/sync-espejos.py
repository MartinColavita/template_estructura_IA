#!/usr/bin/env python3
"""Regenera los espejos desde su fuente sin dejarlos a medias y sin pisar lo que se edito en el espejo.

    python -I bin/sync-espejos.py skills    (cerebro-digital/configuracion-ia/skills  -> .agents/skills y .claude/skills)
    python -I bin/sync-espejos.py agentes   (cerebro-digital/configuracion-ia/agentes -> .agents/agents y .claude/agents)
    ... [--pisar] [--dry-run]

Tres estados, nunca dos:  0 = espejos regenerados   1 = FRENA (hay algo en el espejo que la fuente no tiene)
                          2 = SIN DATOS (no existe la fuente, o la copia fallo y el espejo anterior quedo como estaba)

COMO. El espejo nuevo se arma en una carpeta temporal al lado; recien con la copia entera se cambia por el viejo. Si la
copia falla a mitad de camino (un archivo bloqueado, el disco lleno), el espejo anterior queda entero. Si el sistema no
deja cambiar la carpeta entera (en Windows, otro proceso la tiene abierta), se actualiza archivo por archivo, cada uno
reemplazado de una.

Antes de tocar nada se compara. Cada sync deja al lado del espejo un manifiesto (<espejo>.sync.json, que git ignora)
con la huella de cada archivo tal como quedo. Un archivo del espejo distinto de la fuente es una edicion hecha en el
espejo si el manifiesto no lo tiene (se agrego a mano) o si cambio desde el ultimo sync; se frena mostrandolo (con
--pisar se regenera igual). Si quedo tal cual lo dejo el sync, el cambio vino de la fuente (lo cambio o lo borro) y se
actualiza sin frenar. Sin manifiesto (un espejo de antes), vale la fecha: lo que solo esta en el espejo, o es distinto
y mas nuevo que la fuente, frena. Un archivo identico a su version en el ultimo commit tampoco frena: lo trajo git (un
pull, un cambio de rama), no es una edicion. Los espejos de agentes no se versionan: sin esto, una edicion ahi se
perdia sin aviso. Antes de decir OK se compara el espejo con la fuente. Lo usan los sync-*.sh/.ps1, instalar.py e
instanciar.py. Solo biblioteca estandar.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid

OK, FRENA, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARES = {
    'skills': (os.path.join('cerebro-digital', 'configuracion-ia', 'skills'), ('.agents/skills', '.claude/skills')),
    'agentes': (os.path.join('cerebro-digital', 'configuracion-ia', 'agentes'), ('.agents/agents', '.claude/agents')),
}
IGNORAR = ('__pycache__',)
TOLERANCIA = 2   # segundos: una copia o un checkout dejan fechas casi iguales
MANIFIESTO = '.sync.json'


def _archivos(base):
    res = {}
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if x not in IGNORAR]
        for f in files:
            p = os.path.join(d, f)
            res[os.path.relpath(p, base).replace(os.sep, '/')] = p
    return res


def _mismo_contenido(a, b):
    """Byte por byte y sin la cache de filecmp, que se fia del tamano y la fecha: en Linux la fecha avanza de a
    tics de milisegundos, y dos escrituras del mismo largo en el mismo tic la enganan."""
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        while True:
            x, y = fa.read(65536), fb.read(65536)
            if x != y:
                return False
            if not x:
                return True


def _huella(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(65536), b''):
            h.update(bloque)
    return h.hexdigest()


def _leer_manifiesto(espejo):
    try:
        with open(espejo + MANIFIESTO, encoding='utf-8') as h:
            datos = json.load(h)
        return datos if isinstance(datos, dict) else None
    except (OSError, ValueError):
        return None


def _guardar_manifiesto(espejo):
    """La huella de cada archivo del espejo tal como lo dejo este sync. Si no se puede escribir, se saca el viejo (que
    ya no dice como quedo el espejo) y el proximo sync usa la fecha, como un espejo de antes."""
    ruta = espejo + MANIFIESTO
    try:
        with open(ruta + '.nuevo', 'w', encoding='utf-8', newline='\n') as h:
            json.dump({rel: _huella(p) for rel, p in sorted(_archivos(espejo).items())}, h, indent=1, sort_keys=True)
        os.replace(ruta + '.nuevo', ruta)
    except OSError:
        for resto in (ruta + '.nuevo', ruta):
            try:
                os.remove(resto)
            except OSError:
                pass


def _iguales_al_ultimo_commit(espejo, rels):
    """De esos archivos del espejo, los identicos a su version en el ultimo commit: los trajo git (un pull, un cambio
    de rama), no son una edicion. Solo pesa en un espejo versionado (las skills); sin git, ninguno."""
    try:
        top = subprocess.run(['git', '-C', espejo, 'rev-parse', '--show-toplevel'], capture_output=True)
        if top.returncode != 0:
            return set()
        raiz = top.stdout.decode('utf-8', 'replace').strip()   # git da la ruta en UTF-8 (una carpeta con acentos)
        base = os.path.relpath(espejo, raiz).replace(os.sep, '/')
        arbol = subprocess.run(['git', '-C', raiz, 'ls-tree', '-r', '-z', 'HEAD', '--', base], capture_output=True)
        if arbol.returncode != 0:
            return set()
        en_head = {}
        for entrada in arbol.stdout.decode('utf-8', 'replace').split('\0'):
            if '\t' in entrada:
                meta, ruta = entrada.split('\t', 1)
                en_head[ruta] = meta.split()[2]
        pedidos = [r for r in rels if base + '/' + r in en_head]
        if not pedidos:
            return set()
        h = subprocess.run(['git', '-C', raiz, 'hash-object', '--stdin-paths'], capture_output=True,
                           input='\n'.join(base + '/' + r for r in pedidos).encode('utf-8') + b'\n')
        ids = h.stdout.decode('ascii', 'replace').split()
        if h.returncode != 0 or len(ids) != len(pedidos):
            return set()
        return {r for r, i in zip(pedidos, ids) if en_head[base + '/' + r] == i}
    except OSError:
        return set()


def editado_en_el_espejo(fuente, espejo):
    """Lo que se edito o se agrego en el espejo desde el ultimo sync (ver el encabezado)."""
    if not os.path.isdir(espejo):
        return []
    f, e = _archivos(fuente), _archivos(espejo)
    manifiesto = _leer_manifiesto(espejo)
    sospechosos = {}
    for rel, pe in sorted(e.items()):
        pf = f.get(rel)
        if pf is not None and _mismo_contenido(pe, pf):
            continue   # igual a la fuente: no hay nada que cuidar
        if manifiesto is not None:
            if rel not in manifiesto:
                sospechosos[rel] = ' (agregado en el espejo)'
            elif _huella(pe) != manifiesto[rel]:
                sospechosos[rel] = ' (editado en el espejo desde el ultimo sync)'
        elif pf is None:
            sospechosos[rel] = ' (solo en el espejo)'
        elif os.path.getmtime(pe) > os.path.getmtime(pf) + TOLERANCIA:
            sospechosos[rel] = ' (editado en el espejo, mas nuevo que la fuente)'
    limpios = _iguales_al_ultimo_commit(espejo, list(sospechosos)) if sospechosos else set()
    return [rel + por_que for rel, por_que in sorted(sospechosos.items()) if rel not in limpios]


def _copiar(fuente, destino):
    shutil.copytree(fuente, destino, ignore=shutil.ignore_patterns(*IGNORAR))


def _en_el_lugar(nuevo, espejo):
    """Plan B cuando no se puede cambiar la carpeta entera: cada archivo se reemplaza de una (nunca queda uno a
    medias); un corte deja el espejo mezclado, y volver a correr lo completa."""
    os.makedirs(espejo, exist_ok=True)
    n, e = _archivos(nuevo), _archivos(espejo)
    # primero se saca lo que la fuente ya no tiene: en un disco que no distingue mayusculas, un Skill.md que pasa a
    # SKILL.md es el mismo archivo, y borrarlo despues de copiar borraria el nuevo
    for rel, pe in e.items():
        if rel not in n:
            os.remove(pe)
    _sacar_carpetas_vacias(espejo)   # una carpeta que solo cambia mayusculas (Foo/ -> foo/) se vuelve a crear bien
    for rel, pn in sorted(n.items()):
        pe = e.get(rel)
        if pe is not None and _mismo_contenido(pn, pe):
            continue
        destino = os.path.join(espejo, *rel.split('/'))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        try:
            shutil.copy2(pn, destino + '.nuevo')
            os.replace(destino + '.nuevo', destino)
        except OSError:
            try:
                os.remove(destino + '.nuevo')   # que no quede adentro del espejo una copia a medio poner
            except OSError:
                pass
            raise
    _sacar_carpetas_vacias(espejo)


def _sacar_carpetas_vacias(espejo):
    for d, _, _ in os.walk(espejo, topdown=False):
        if d != espejo and os.path.basename(d) not in IGNORAR and not os.listdir(d):
            os.rmdir(d)


def regenerar(fuente, espejo, pisar=False, dry_run=False):
    """(ok, mensaje). Nunca deja el espejo a medias."""
    if not os.path.isdir(fuente):
        return False, 'SIN DATOS -- no existe la fuente %s: el espejo no se toco' % fuente
    editados = [] if pisar else editado_en_el_espejo(fuente, espejo)
    if editados:
        que = 'agentes' if os.path.basename(os.path.normpath(fuente)) == 'agentes' else 'skills'
        return False, ('FRENA -- el espejo %s tiene cosas que la fuente no: %s. Si son tuyas, pasalas a la fuente; si no, '
                       'regeneralo igual con  python -I bin/sync-espejos.py %s --pisar' % (espejo, '; '.join(editados[:10]), que))
    if dry_run:
        return True, 'se regeneraria %s (dry-run)' % espejo
    sufijo = uuid.uuid4().hex[:8]
    nuevo, viejo = espejo + '.nuevo-' + sufijo, espejo + '.viejo-' + sufijo
    try:
        _copiar(fuente, nuevo)
    except Exception as e:
        shutil.rmtree(nuevo, ignore_errors=True)
        return False, 'SIN DATOS -- la copia a %s fallo (%s): el espejo anterior quedo como estaba' % (espejo, e)
    como = 'regenerado'
    try:
        if os.path.isdir(espejo):
            os.rename(espejo, viejo)
        os.rename(nuevo, espejo)
    except OSError as e:
        if not os.path.isdir(espejo) and os.path.isdir(viejo):
            try:
                os.rename(viejo, espejo)
            except OSError as e2:
                return False, ('SIN DATOS -- no se pudo reemplazar %s (%s) ni volver a poner el anterior (%s): el anterior '
                               'quedo en %s y el nuevo en %s; renombra uno de los dos a %s' % (espejo, e, e2, viejo, nuevo, espejo))
        try:
            _en_el_lugar(nuevo, espejo)
        except OSError as e3:
            shutil.rmtree(nuevo, ignore_errors=True)
            return False, ('SIN DATOS -- no se pudo reemplazar %s (%s) ni actualizarlo archivo por archivo (%s): '
                           'volve a correrlo cuando nada lo tenga abierto' % (espejo, e, e3))
        shutil.rmtree(nuevo, ignore_errors=True)
        como = 'actualizado archivo por archivo (no se pudo cambiar la carpeta entera: %s)' % e
    shutil.rmtree(viejo, ignore_errors=True)
    _guardar_manifiesto(espejo)   # lo que dejo este sync, aunque abajo no de OK: si no, la proxima corrida frena de mas
    distintos = _distinto_de_la_fuente(fuente, espejo)
    if distintos:
        return False, ('SIN DATOS -- el espejo %s no quedo igual a la fuente (%s): volve a correrlo; si se repite, '
                       'con --pisar' % (espejo, '; '.join(distintos[:10])))
    return True, 'OK: espejo %s en %s (%d elementos)' % (como, espejo, len(os.listdir(espejo)))


def _distinto_de_la_fuente(fuente, espejo):
    """Lo que falta, sobra o difiere: un OK se dice solo despues de mirarlo."""
    f, e = _archivos(fuente), _archivos(espejo)
    res = ['falta ' + r for r in sorted(set(f) - set(e))] + ['sobra ' + r for r in sorted(set(e) - set(f))]
    return res + ['distinto ' + r for r in sorted(set(f) & set(e)) if not _mismo_contenido(f[r], e[r])]


def main():
    ap = argparse.ArgumentParser(description='Regenera los espejos de skills o de agentes desde su fuente.')
    ap.add_argument('que', choices=sorted(PARES))
    ap.add_argument('--pisar', action='store_true', help='regenerar aunque el espejo tenga cosas que la fuente no')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    fuente_rel, destinos = PARES[a.que]
    rc = OK
    for d in destinos:
        ok, msj = regenerar(os.path.join(RAIZ, fuente_rel), os.path.join(RAIZ, d), a.pisar, a.dry_run)
        print(msj.replace(RAIZ + os.sep, ''))
        if not ok:
            rc = max(rc, FRENA if msj.startswith('FRENA') else SIN_DATOS)
    return rc


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
