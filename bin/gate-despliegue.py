#!/usr/bin/env python3
"""GATE de DESPLIEGUE, en datos duros: lo que hay que mostrar ANTES de promover una version a un ambiente. SOLO LECTURA.

    python -I bin/gate-despliegue.py --ambiente <nombre-exacto> --version <ref-candidata>
           [--repo <repo-de-la-app> --desde <ref-que-esta-en-el-ambiente> [--carpeta <migraciones>] [--sin-uso-desplegado <ref>]]
           [--pipeline verde|rojo] [--artefacto <digest-o-id> --en-el-anterior <digest-o-id>]
           [--modulo <slug> | --ambientes <ruta-de-ambientes.md> | --raiz <raiz-del-cerebro>] [--json]

    Lo que vive en la plataforma no lo mira este script: se lo pasa quien lo corre, leido de la plataforma.
      --pipeline         como termino el pipeline de ese commit (verde o rojo).
      --artefacto        el digest o identificador de lo que se promueve; --en-el-anterior, el que esta desplegado en
                         el ambiente anterior de la ficha. Tienen que ser iguales: se promueve lo mismo que ya se probo.
      --sin-uso-desplegado  si el rango CONTRAE: la version que dejo de usar lo que se borra. Tiene que estar ya en el
                         ambiente (ser ancestro de --desde, o la misma).

Tres estados, nunca dos:  0 = OK, se puede preparar   1 = FRENA (hay algo que decidir)   2 = SIN DATOS

LOS CHEQUEOS, uno por linea:
  Ambiente           figura, por su nombre exacto, en cerebro-digital/<modulo>/arquitectura/ambientes.md
  Proteccion         si es protegido, quien aprueba (rol) y donde (la plataforma); sin decidir es SIN DATOS
  Pipeline en verde  lo que dice --pipeline; sin el, SIN DATOS
  Mismo artefacto    --artefacto igual a --en-el-anterior, los dos como digest (sha256:<64 hex> o imagen@sha256:...;
                     una etiqueta como :latest es SIN DATOS); el primer ambiente de la ficha NO APLICA
  La ficha vale solo adentro de <raiz>/cerebro-digital/: una --ambientes de otro lado es SIN DATOS.
  Migraciones        las del rango --desde...--version, con la logica de clasificar-migraciones.py (lo importa):
                     MIXTA o una columna obligatoria sin valor por defecto FRENA; CONTRAER frena salvo que
                     --sin-uso-desplegado ya este en el ambiente
  Vuelta atras       procedimiento y tiempo declarados en la ficha, y la version a la que se vuelve (--desde)
  Que mirar despues  la ventana de observacion de la ficha; sin ella, AVISO (no frena)

POR QUE EXISTE. AGENTS.md (GATE de DESPLIEGUE) dice que la IA prepara y despliega una persona, con su aprobacion
en la plataforma. Para que esa persona apruebe sabiendo que aprueba, el plan tiene que mostrar siempre los mismos
datos: a donde va, quien aprueba, si el pipeline esta en verde, si es lo mismo que se probo, que le hace a la base
y como se vuelve. Esos datos los juntaba el modelo y a veces faltaba uno. Este script los junta siempre igual.

QUE NO HACE. No despliega, no aprueba, no dispara pipelines, no llama a ninguna API ni se conecta a nada; con
--repo solo lee git. No reemplaza la aprobacion en la plataforma: un OK dice que el plan esta completo, no que haya
que desplegar. Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys

OK, FRENA, SIN_DATOS = 0, 1, 2
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from operacion import inventario  # noqa: E402  el lector de tablas markdown comun (plano, celdas, es_separador)
from operacion.inventario import BOM, RAYAS, plano, celdas  # noqa: E402
# Lo que se promueve se identifica por su digest, no por una etiqueta: una etiqueta (:latest, :v2) se mueve.
DIGEST = re.compile(r'(?i)(?:^|@)(sha256:[0-9a-f]{64})$')
COLUMNAS = (('ambiente', 'nombre'), ('para', 'proposito'), ('protegido', 'protegido'), ('quien aprueba', 'aprueba'),
            ('donde', 'donde'), ('que entra', 'entra'), ('ventana', 'ventana'), ('como se vuelve', 'vuelta'),
            ('cuanto tarda', 'tarda'))
CHEQUEOS = ('Ambiente', 'Proteccion', 'Pipeline en verde', 'Mismo artefacto', 'Migraciones', 'Vuelta atras',
            'Que mirar despues')
NO_MIRA = ('si conviene desplegar: lo decide la persona que aprueba en la plataforma',
           'si la aprobacion, el ambiente protegido y las reglas de rama siguen configurados en la plataforma '
           '(verificar-pipeline.py los marca SIN DATOS: se miran a mano)',
           'el volumen, los bloqueos y la duracion de las migraciones (clasificar-migraciones.py tampoco)',
           'la firma, la atestacion o el SBOM del artefacto (cadena-de-suministro.md de despliegue-continuo)')


# ---------------------------------------------------------------------------------------------------------
# La ficha de ambientes (la lee tambien verificar-pipeline.py)
# ---------------------------------------------------------------------------------------------------------

def limpio(valor):
    """Sin acentos graves ni negrita. A diferencia del de inventario.py, un asterisco suelto queda: en "tags v*" es
    parte del dato."""
    return re.sub(r'\*\*(.*?)\*\*', r'\1', valor.replace('`', '')).strip()


def vacio(valor):
    """Una celda sin dato: vacia, una raya, una marca de pendiente o un molde entre <...>."""
    v = limpio(valor)
    return not v.strip(RAYAS + ' ') or '<' in v or chr(0x26A0) in v


def leer_ambientes(ruta):
    """(ambientes, problemas) de la ficha, en el orden de la tabla. Lanza OSError si no se puede abrir.

    Una tabla cuenta solo si su ENCABEZADO (la fila de antes de la linea de guiones) tiene la columna Ambiente:
    la tabla de ayuda, que nombra las columnas en sus filas, no agrega ambientes. Las filas de molde (nombre
    vacio, con '<' o con una raya) se saltean."""
    with open(ruta, 'rb') as h:
        texto = h.read().decode('utf-8', errors='replace').replace('\r\n', '\n')
    if texto.startswith(BOM):
        texto = texto[1:]
    filas = [celdas(l) for l in texto.split('\n')]
    ambientes, problemas, orden, en_tabla = [], [], None, False
    for i, fila in enumerate(filas):
        if fila is None:
            orden, en_tabla = None, False
            continue
        if not en_tabla:
            en_tabla, orden = True, None
            siguiente = filas[i + 1] if i + 1 < len(filas) else None
            encabezado = [plano(c) for c in fila]
            if (siguiente is not None and inventario.es_separador(siguiente)
                    and any(e.startswith('ambiente') for e in encabezado)):
                orden = {}
                for j, e in enumerate(encabezado):
                    for palabra, clave in COLUMNAS:
                        if palabra in e and clave not in orden.values():
                            orden[j] = clave
                            break
            continue
        if orden is None or inventario.es_separador(fila):
            continue
        dato = dict((clave, '') for _, clave in COLUMNAS)
        for j, c in enumerate(fila):
            if j in orden:
                dato[orden[j]] = c
        nombre = limpio(dato['nombre'])
        if vacio(nombre):
            continue
        prot = plano(dato['protegido'])
        amb = dict((k, '' if vacio(v) else limpio(v)) for k, v in dato.items())
        amb.update(nombre=nombre, protegido=True if prot == 'si' else False if prot == 'no' else None, linea=i + 1)
        ambientes.append(amb)
    vistos = {}
    for a in ambientes:
        vistos.setdefault(a['nombre'], []).append(a['linea'])
    for nombre, donde in sorted(vistos.items()):
        if len(donde) > 1:
            problemas.append('el ambiente %s figura %d veces (lineas %s): no se puede saber cual vale' % (
                nombre, len(donde), ', '.join(str(x) for x in donde)))
    return ambientes, problemas


def ubicar_ambientes(raiz, modulo=''):
    """(ruta, motivo) de la ficha de ambientes del modulo, o (None, motivo)."""
    base = os.path.join(raiz, 'cerebro-digital')
    if modulo:
        ruta = os.path.join(base, modulo, 'arquitectura', 'ambientes.md')
        return (ruta, '') if os.path.isfile(ruta) else (None, 'no existe %s' % os.path.relpath(ruta, raiz))
    rutas = sorted(r for r in glob.glob(os.path.join(base, '*', 'arquitectura', 'ambientes.md'))
                   if os.path.basename(os.path.dirname(os.path.dirname(r))) != 'configuracion-ia')
    if not rutas:
        return None, 'ningun modulo de cerebro-digital/ tiene arquitectura/ambientes.md: sin ficha, no se prepara ninguna promocion'
    if len(rutas) > 1:
        return None, 'hay %d fichas de ambientes (%s): hay que decir de cual modulo (--modulo)' % (
            len(rutas), ', '.join(os.path.basename(os.path.dirname(os.path.dirname(r))) for r in rutas))
    return rutas[0], ''


def cargar_ambientes(ruta):
    """(ambientes, problemas, motivo). ambientes es None cuando no hay de donde decidir (SIN DATOS)."""
    if not ruta or not os.path.isfile(ruta):
        return None, [], 'no hay ficha de ambientes (%s): sin ficha, no se prepara ninguna promocion' % (ruta or 'sin ruta')
    try:
        ambientes, problemas = leer_ambientes(ruta)
    except OSError as e:
        return None, [], 'no se pudo leer la ficha de ambientes: %s' % e
    if not ambientes:
        return None, [], 'la ficha de ambientes no tiene ningun ambiente cargado (solo la fila de molde): no se promueve nada'
    return ambientes, problemas, ''


# ---------------------------------------------------------------------------------------------------------
# Los chequeos
# ---------------------------------------------------------------------------------------------------------

def clasificador():
    """El modulo bin/clasificar-migraciones.py: las migraciones se clasifican con el mismo codigo, no con otro."""
    spec = importlib.util.spec_from_file_location('clasificar_migraciones', os.path.join(AQUI, 'clasificar-migraciones.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def es_ancestro(repo, anterior, posterior):
    """True si anterior es ancestro de posterior (o el mismo commit), False si no, None si git no pudo decir."""
    r = subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', anterior, posterior], capture_output=True)
    return True if r.returncode == 0 else False if r.returncode == 1 else None


def chequear_migraciones(a):
    """(estado, detalle, resultado) del chequeo de migraciones."""
    if not a.repo or not a.desde:
        return 'SIN DATOS', ('falta --repo y --desde (la version que esta hoy en el ambiente): no se sabe que migraciones '
                             'trae el rango'), None
    repo = os.path.abspath(a.repo)
    res = clasificador().desde_repo(repo, a.desde, a.version, a.carpeta)
    if res['estado'] == 'SIN DATOS':
        return 'SIN DATOS', res['motivo'] or 'no se pudo clasificar el rango', res
    resumen = ', '.join('%d %s' % (n, c) for c, n in res['resumen'].items() if n) or 'ninguna migracion nueva'
    rango = '%s...%s: %s' % (a.desde, a.version, resumen)
    if res['estado'] == 'HALLAZGO':
        return 'FRENA', '%s. %s' % (rango, res['hallazgos'][0]), res
    contraen = [m['ruta'] for m in res['migraciones'] if m['clase'] in ('CONTRAER', 'MIXTA')]
    if not contraen:
        return 'OK', rango, res
    if not a.sin_uso_desplegado:
        return 'FRENA', ('%s. Trae CONTRAER (%s): falta declarar que version dejo de usar lo que se borra y ya esta en el '
                         'ambiente (--sin-uso-desplegado)' % (rango, ', '.join(contraen))), res
    anc = es_ancestro(repo, a.sin_uso_desplegado, a.desde)
    if anc is None:
        return 'SIN DATOS', '%s. git no pudo comparar %s con %s' % (rango, a.sin_uso_desplegado, a.desde), res
    if not anc:
        return 'FRENA', ('%s. Trae CONTRAER, y %s (la que dejo de usarlo) no esta en el ambiente: el ambiente tiene %s'
                         % (rango, a.sin_uso_desplegado, a.desde)), res
    return 'OK', ('%s. Trae CONTRAER y %s, que dejo de usarlo, ya esta en el ambiente. Contraer lleva dos "si" en turnos '
                  'distintos y los datos borrados no vuelven' % (rango, a.sin_uso_desplegado)), res


def evaluar(a, ruta):
    """(estado global, chequeos, ambiente, migraciones, motivo_ficha)."""
    chequeos = []

    def poner(nombre, estado, detalle):
        chequeos.append({'chequeo': nombre, 'estado': estado, 'detalle': detalle})

    ambientes, problemas, motivo = cargar_ambientes(ruta) if ruta else (None, [], a._motivo_ruta)
    amb, previo = None, None
    if ambientes is None:
        poner('Ambiente', 'SIN DATOS', motivo)
    else:
        iguales = [x for x in ambientes if x['nombre'] == a.ambiente]
        parecidos = [x['nombre'] for x in ambientes if x['nombre'].lower() == a.ambiente.lower() and x['nombre'] != a.ambiente]
        if len(iguales) > 1:
            poner('Ambiente', 'SIN DATOS', [p for p in problemas if a.ambiente in p][0])
        elif not iguales:
            poner('Ambiente', 'FRENA', '%s no figura en la ficha de ambientes%s: no se le prepara ninguna promocion' % (
                a.ambiente, ' (figura como "%s": en algunas plataformas un nombre distinto es otro ambiente, sin '
                            'aprobaciones)' % parecidos[0] if parecidos else ''))
        else:
            amb = iguales[0]
            k = ambientes.index(amb)
            previo = ambientes[k - 1] if k > 0 else None
            poner('Ambiente', 'OK', '%s figura en %s:%d (%s; entra: %s)' % (
                amb['nombre'], os.path.relpath(ruta, RAIZ) if ruta.startswith(RAIZ) else ruta, amb['linea'],
                amb['proposito'] or 'sin proposito declarado', amb['entra'] or 'sin rama o tag declarado'))
    if amb is None:
        for c in ('Proteccion', 'Mismo artefacto', 'Vuelta atras', 'Que mirar despues'):
            poner(c, 'SIN DATOS', 'depende de la fila del ambiente en la ficha')
    else:
        if amb['protegido'] is None:
            poner('Proteccion', 'SIN DATOS', 'la columna Protegido de %s esta sin decidir: vale como protegido' % amb['nombre'])
        elif amb['protegido']:
            faltan = [x for x, v in (('quien aprueba (rol)', amb['aprueba']), ('donde se aprueba', amb['donde'])) if not v]
            if faltan:
                poner('Proteccion', 'FRENA', '%s es protegido y la ficha no dice %s' % (amb['nombre'], ' ni '.join(faltan)))
            else:
                poner('Proteccion', 'OK', 'protegido: aprueba %s, en %s. La IA no aprueba ni toca esa proteccion' % (
                    amb['aprueba'], amb['donde']))
        else:
            poner('Proteccion', 'OK', '%s es no protegido: la plataforma no pide aprobacion (lo que la ficha diga, decide '
                                     'una persona)' % amb['nombre'])
    # lo que viene de la plataforma
    if a.pipeline == 'verde':
        poner('Pipeline en verde', 'OK', 'segun quien corre el gate (--pipeline verde)')
    elif a.pipeline == 'rojo':
        poner('Pipeline en verde', 'FRENA', 'el pipeline de esa version esta en rojo')
    else:
        poner('Pipeline en verde', 'SIN DATOS', 'no se paso --pipeline: lo mira una persona en la plataforma (este script no '
                                                'llama a ninguna API)')
    if amb is not None:
        if previo is None:
            poner('Mismo artefacto', 'NO APLICA', '%s es el primer ambiente de la ficha' % amb['nombre'])
        elif not a.artefacto or not a.en_el_anterior:
            poner('Mismo artefacto', 'SIN DATOS', 'falta --artefacto y --en-el-anterior (el que esta en %s, leido de la '
                                                  'plataforma)' % previo['nombre'])
        elif not DIGEST.search(a.artefacto.strip()) or not DIGEST.search(a.en_el_anterior.strip()):
            poner('Mismo artefacto', 'SIN DATOS', 'hace falta el digest de los dos (sha256:<64 hexadecimales>, o '
                                                  'imagen@sha256:<...>): una etiqueta como :latest se mueve y no prueba '
                                                  'que sea lo mismo que esta en %s' % previo['nombre'])
        elif DIGEST.search(a.artefacto.strip()).group(1).lower() == DIGEST.search(a.en_el_anterior.strip()).group(1).lower():
            poner('Mismo artefacto', 'OK', 'se promueve %s, el mismo que esta en %s' % (a.artefacto, previo['nombre']))
        else:
            poner('Mismo artefacto', 'FRENA', '%s no es el que esta en %s (%s): se promueve lo mismo que ya se probo' % (
                a.artefacto, previo['nombre'], a.en_el_anterior))
    estado_m, detalle_m, migr = chequear_migraciones(a)
    poner('Migraciones', estado_m, detalle_m)
    if amb is not None:
        faltan = [x for x, v in (('como se vuelve', amb['vuelta']), ('cuanto tarda', amb['tarda'])) if not v]
        if faltan:
            poner('Vuelta atras', 'FRENA', 'la ficha no dice %s para %s: la vuelta atras se decide antes' % (
                ' ni '.join(faltan), amb['nombre']))
        elif not a.desde:
            poner('Vuelta atras', 'SIN DATOS', '%s, en %s; falta --desde: no se sabe a que version se vuelve' % (
                amb['vuelta'], amb['tarda']))
        else:
            nota = ''
            if migr and any(m['clase'] in ('CONTRAER', 'MIXTA') for m in migr.get('migraciones', [])):
                nota = '. Lo que se contrae no vuelve con la version'
            elif migr and any(m['clase'] == 'EXPANDIR' for m in migr.get('migraciones', [])):
                nota = '. Lo que se agrego a la base queda: la version anterior lo ignora'
            poner('Vuelta atras', 'OK', 'volver a %s: %s, en %s%s' % (a.desde, amb['vuelta'], amb['tarda'], nota))
        if amb['ventana']:
            poner('Que mirar despues', 'OK', 'alguien mira %s despues de desplegar (observabilidad.md)' % amb['ventana'])
        else:
            poner('Que mirar despues', 'AVISO', 'la ficha no dice la ventana de observacion de %s' % amb['nombre'])
    orden = dict((c, i) for i, c in enumerate(CHEQUEOS))
    chequeos.sort(key=lambda c: orden[c['chequeo']])
    estados = [c['estado'] for c in chequeos]
    estado = 'FRENA' if 'FRENA' in estados else 'SIN DATOS' if 'SIN DATOS' in estados else 'OK'
    return estado, chequeos, amb, migr


def main():
    ap = argparse.ArgumentParser(description='Datos duros del GATE de DESPLIEGUE (solo lectura; no despliega ni aprueba).')
    ap.add_argument('--ambiente', default='')
    ap.add_argument('--version', default='', help='la version candidata (tag o commit)')
    ap.add_argument('--repo', default='', help='repositorio de la aplicacion, para leer las migraciones del rango')
    ap.add_argument('--desde', default='', help='la version que esta hoy en el ambiente (tag o commit)')
    ap.add_argument('--carpeta', default='', help='donde viven las migraciones (si no es una carpeta reconocible)')
    ap.add_argument('--sin-uso-desplegado', default='', help='la version que dejo de usar lo que se contrae')
    ap.add_argument('--pipeline', default='', choices=('', 'verde', 'rojo'))
    ap.add_argument('--artefacto', default='')
    ap.add_argument('--en-el-anterior', default='')
    ap.add_argument('--ambientes', default='', help='ruta de la ficha de ambientes')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--raiz', default=RAIZ)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not a.ambiente or not a.version:
        print('SIN DATOS -- falta --ambiente <nombre exacto> y --version <tag o commit>.')
        return SIN_DATOS
    if a.ambientes and not inventario.en_el_cerebro(a.ambientes, os.path.abspath(a.raiz)):
        ruta, a._motivo_ruta = None, ('la ficha %s no esta adentro de %s: una ficha armada en otro lado (borrador/, '
                                      'una carpeta temporal) no autoriza ninguna promocion' % (
                                          a.ambientes, os.path.join(os.path.abspath(a.raiz), 'cerebro-digital')))
    elif a.ambientes:
        ruta, a._motivo_ruta = a.ambientes, ''
    else:
        ruta, a._motivo_ruta = ubicar_ambientes(os.path.abspath(a.raiz), a.modulo)
    estado, chequeos, amb, migr = evaluar(a, ruta)
    codigo = {'OK': OK, 'FRENA': FRENA}.get(estado, SIN_DATOS)
    if a.json:
        print(json.dumps({'estado': estado, 'ambiente': amb or {'nombre': a.ambiente}, 'version': a.version, 'desde': a.desde or None,
                          'ficha': ruta, 'chequeos': chequeos,
                          'migraciones': migr and {'estado': migr['estado'], 'resumen': migr['resumen'],
                                                   'migraciones': [{'ruta': m['ruta'], 'clase': m['clase']} for m in migr['migraciones']],
                                                   'avisos': migr['avisos']},
                          'no_mira': list(NO_MIRA)}, ensure_ascii=True, indent=1))
        return codigo
    print('GATE de DESPLIEGUE -- %s: %s, version %s%s' % (estado, a.ambiente, a.version, ' (hoy tiene %s)' % a.desde if a.desde else ''))
    for c in chequeos:
        print('  %-18s: %-10s %s' % (c['chequeo'], c['estado'], c['detalle']))
    if migr:
        for m in migr['migraciones']:
            print('      %-15s %s' % (m['clase'], m['ruta']))
        for v in migr['avisos'][:20]:
            print('      aviso: ' + v)
    print('  Lo que este script NO decide: si se despliega. La IA prepara; despliega una persona, con su aprobacion en la '
          'plataforma.')
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
