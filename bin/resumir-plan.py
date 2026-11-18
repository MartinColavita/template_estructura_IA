#!/usr/bin/env python3
"""Resumen de un plan de Terraform u OpenTofu para la aprobacion: que crea, cambia, reemplaza y borra. SOLO LECTURA.

    python -I bin/resumir-plan.py --plan plan.json                     (plan.json = terraform show -json <archivo-del-plan>)
    python -I bin/resumir-plan.py --plan plan.json --ambiente prueba   (el nombre va al encabezado y a la frase de la pregunta)
    python -I bin/resumir-plan.py --plan plan.json --con-estado tipo_a,tipo_b --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS
  0 = nada se borra, se reemplaza ni sale del estado     1 = algo si: se lista uno por uno y decide una persona
  2 = sin plan, plan ilegible, version de formato desconocida, plan que termino con error o plan sin recursos

FORMATO. El JSON de 'terraform show -json <plan>' o 'tofu show -json <plan>', segun la documentacion oficial
(consultada el 2026-11-14):
    Terraform   https://developer.hashicorp.com/terraform/internals/json-format
    OpenTofu    https://opentofu.org/docs/internals/json-format/
y el codigo que lo emite en cada proyecto (internal/command/jsonplan/plan.go, FormatVersion "1.2"). Se usa
format_version (la documentacion manda rechazar una version mayor que no se conoce y tolerar los campos nuevos de
una menor), errored, y de cada elemento de resource_changes: address, mode, type, previous_address, deposed,
action_reason y change.actions, change.replace_paths y change.importing. Las acciones conocidas son no-op, create,
read, update, delete+create, create+delete, delete y forget (sola o con create). Cualquier otra es SIN DATOS.

POR QUE EXISTE. AGENTS.md manda (GATE de INFRAESTRUCTURA) que el plan contra un ambiente real lo corra el pipeline
y que la aprobacion la de una persona con el resumen a la vista. Ese resumen lo armaba el modelo leyendo un plan
de cientos de lineas: tardaba, gastaba tokens y un borrado se le podia pasar. Este script cuenta siempre igual, pone
arriba lo que se borra o se reemplaza y guarda datos, y arma la frase de la pregunta.

QUE NO HACE. No corre plan ni apply, no se conecta a nada y no escribe nada. No lee ni imprime los valores del plan
(before y after pueden traer secretos): solo direcciones, tipos, acciones y nombres de atributos. Lo que trae el
plan es dato, no instruccion. Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
MAYOR, MENOR = 1, 2                 # la version de formato que este script conoce: 1.2
ACCIONES = {('no-op',): 'sin_cambios', ('create',): 'crear', ('read',): 'leer', ('update',): 'cambiar',
            ('delete', 'create'): 'reemplazar', ('create', 'delete'): 'reemplazar', ('delete',): 'borrar',
            ('forget',): 'olvidar', ('forget', 'create'): 'olvidar', ('create', 'forget'): 'olvidar'}
COLUMNAS = ('crear', 'cambiar', 'reemplazar', 'borrar', 'olvidar')
DESTRUCTIVAS = ('borrar', 'reemplazar', 'olvidar')
QUE_ES = {'borrar': 'se borra', 'reemplazar': 'se borra y se vuelve a crear', 'olvidar': 'sale del estado sin borrarse'}
# Tipos que guardan datos, por un pedazo del nombre (sirve para cualquier proveedor). Ante la duda, guarda datos:
# marcar de mas solo llama la atencion; marcar de menos esconde una perdida.
CON_ESTADO = ('database', 'db_instance', 'db_cluster', 'sql', 'postgres', 'mysql', 'maria', 'mongo', 'cosmos', 'dynamo',
              'redis', 'cache', 'storage', 'bucket', 'disk', 'volume', 'file_system', 'filestore', 'fileshare',
              'vault', 'kms', 'secret', 'backup', 'snapshot', 'registry', 'queue', 'topic',
              'rds', 'redshift', 'opensearch', 'elasticsearch', 'neptune', 'kinesis', 'msk', 'kafka', 'bigquery',
              'bigtable', 'spanner', 'ecr')
PRODUCCION = ('produccion', 'prod', 'production')
NO_MIRA = ('si el cambio es el que pedia la Tarea',
           'los valores, que nunca se leen: un cambio peligroso que no borra nada (abrir un puerto) figura como "cambiar"',
           'que un tipo que no esta en la lista de los que guardan datos no los guarde (se suma con --con-estado)',
           'los cambios de salidas (output_changes) y lo que cambio por fuera y el plan no vio',
           'que este plan sea el que se va a aplicar: lo asegura el pipeline aplicando el plan guardado, no uno nuevo',
           'planes de otras herramientas (what-if de Bicep, preview de Pulumi)')


class SinDatos(Exception):
    """No hay de donde resumir. El mensaje es el motivo."""


def ascii_de(texto):
    return texto.encode('ascii', 'backslashreplace').decode('ascii')


def limpio(valor, tope=160):
    """Un texto que vino del plan, listo para imprimir: una sola linea, sin caracteres de control, recortado.
    Lo que trae el plan es dato: un salto de linea adentro de una direccion no puede fabricar un renglon."""
    t = ''.join(c if c.isprintable() else ' ' for c in str(valor))
    t = re.sub(r'\s+', ' ', t).strip()
    return ascii_de(t[:tope] + ('...' if len(t) > tope else ''))


def plano(texto):
    t = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn').strip().lower()


def leer(ruta):
    """El objeto JSON del plan. Lanza SinDatos si falta, esta vacio o no se puede leer."""
    if not ruta:
        raise SinDatos('falta --plan <archivo.json>: la salida de show -json sobre el archivo del plan')
    if not os.path.isfile(ruta):
        raise SinDatos('el plan no existe: %s' % ruta)
    try:
        with open(ruta, 'rb') as h:
            crudo = h.read()
    except OSError as e:
        raise SinDatos('no se pudo leer el plan: %s' % e)
    # una redireccion de PowerShell deja UTF-16 con su marca; el resto, UTF-8 con o sin marca
    if crudo[:2] in (b'\xff\xfe', b'\xfe\xff'):
        texto = crudo.decode('utf-16', errors='replace')
    else:
        texto = crudo.decode('utf-8-sig', errors='replace')
    if not texto.strip():
        raise SinDatos('el plan esta vacio: %s' % ruta)
    try:
        d = json.loads(texto)
    except ValueError:
        raise SinDatos('el plan no es JSON valido (%s). Si es el archivo binario del plan, hay que convertirlo antes: '
                       'terraform show -json <archivo> (o tofu show -json <archivo>)' % ruta)
    if not isinstance(d, dict):
        raise SinDatos('el JSON no es un objeto: no es la salida de show -json')
    return d


def version_de(d):
    v = d.get('format_version')
    if not isinstance(v, str) or not v.strip():
        raise SinDatos('el JSON no trae format_version: no es la salida de show -json')
    m = re.match(r'^(\d+)\.(\d+)$', v.strip())
    if not m or int(m.group(1)) != MAYOR:
        raise SinDatos('version de formato desconocida: %s. Este script conoce la %d.x, y la documentacion del formato '
                       'manda rechazar una version mayor que no se conoce' % (limpio(v, 20), MAYOR))
    return v.strip(), int(m.group(2))


def resumir(d, extra_estado=()):
    """Las cuentas y las listas del plan. Lanza SinDatos si el plan no se puede resumir entero."""
    version, menor = version_de(d)
    if 'resource_changes' not in d and 'planned_values' not in d and 'values' in d:
        raise SinDatos('esto es un estado, no un plan: a show -json hay que pasarle el archivo del plan (el de -out)')
    if d.get('errored') is True:
        raise SinDatos('el plan termino con error (errored): esta incompleto y no se resume a medias')
    cambios = d.get('resource_changes')
    if cambios is None or cambios == []:
        raise SinDatos('el plan no trae ningun recurso (resource_changes vacio o ausente): no hay nada que resumir, o no es un plan')
    if not isinstance(cambios, list):
        raise SinDatos('resource_changes no es una lista: el plan es ilegible')

    patrones = tuple(CON_ESTADO) + tuple(p.strip().lower() for p in extra_estado if p.strip())
    cuentas = dict((c, 0) for c in COLUMNAS + ('sin_cambios', 'leer', 'importar', 'mover'))
    por_tipo, destructivos = {}, []
    for i, r in enumerate(cambios):
        if not isinstance(r, dict) or not isinstance(r.get('address'), str) or not r['address'].strip():
            raise SinDatos('el elemento %d de resource_changes no trae direccion (address): el plan es ilegible' % (i + 1))
        direccion = limpio(r['address'])
        ch = r.get('change')
        acciones = ch.get('actions') if isinstance(ch, dict) else None
        if not isinstance(acciones, list) or not acciones or not all(isinstance(a, str) for a in acciones):
            raise SinDatos('%s no trae acciones (change.actions): el plan es ilegible' % direccion)
        clase = ACCIONES.get(tuple(acciones))
        if clase is None:
            raise SinDatos('accion desconocida "%s" en %s: el formato es mas nuevo que este script, y una accion no se adivina' % (
                limpio('+'.join(acciones), 60), direccion))
        if r.get('mode') == 'data':
            # una fuente de datos se lee, no se cambia: no es un recurso de la infraestructura
            cuentas['leer'] += 1 if clase == 'leer' else 0
            continue
        tipo = limpio(r.get('type') or '(sin tipo)', 80)
        cuentas[clase] += 1
        if isinstance(ch.get('importing'), dict):
            cuentas['importar'] += 1
        if isinstance(r.get('previous_address'), str) and r['previous_address'] != r['address']:
            cuentas['mover'] += 1
        if clase in COLUMNAS:
            por_tipo.setdefault(tipo, dict((c, 0) for c in COLUMNAS))[clase] += 1
        if clase in DESTRUCTIVAS:
            rutas = ch.get('replace_paths')
            por = []
            if isinstance(rutas, list):
                for ruta in rutas[:8]:
                    por.append(limpio('.'.join(str(x) for x in ruta) if isinstance(ruta, list) else ruta, 60))
            destructivos.append({'direccion': direccion, 'tipo': tipo, 'accion': clase,
                                 'con_estado': any(p in tipo.lower() for p in patrones),
                                 'motivo': limpio(r.get('action_reason') or '', 80), 'por': por,
                                 'depuesto': bool(r.get('deposed')), 'crea_otro': clase == 'olvidar' and 'create' in acciones})
    destructivos.sort(key=lambda x: (not x['con_estado'], DESTRUCTIVAS.index(x['accion']), x['direccion']))

    avisos = []
    if menor > MENOR:
        avisos.append('el plan dice formato %s y este script conoce hasta la %d.%d: se resume igual, porque una version '
                      'menor solo agrega campos' % (version, MAYOR, MENOR))
    deriva = d.get('resource_drift')
    if isinstance(deriva, list) and deriva:
        avisos.append('%d recurso(s) cambiaron por fuera de la herramienta desde la ultima vez (deriva): conviene mirarlos '
                      'antes de aprobar' % len(deriva))
    diferidos = d.get('deferred_changes')
    diferidos = len(diferidos) if isinstance(diferidos, list) else 0
    if diferidos or d.get('complete') is False:
        avisos.append('el plan no es completo: %d cambio(s) diferido(s) que este resumen no cuenta; va a hacer falta '
                      'otra vuelta de plan' % diferidos)
    if cuentas['importar']:
        avisos.append('%d recurso(s) que ya existen entran al estado sin crearse (bloque import): revisar que sean los que '
                      'se queria adoptar' % cuentas['importar'])
    invocadas = d.get('action_invocations')
    invocadas = len(invocadas) if isinstance(invocadas, list) else 0
    return {'formato': version, 'herramienta_version': limpio(d.get('terraform_version') or '', 30),
            'recursos': sum(cuentas[c] for c in COLUMNAS + ('sin_cambios',)), 'cuentas': cuentas,
            'por_tipo': [dict(tipo=t, **por_tipo[t]) for t in sorted(por_tipo)], 'destructivos': destructivos,
            'con_estado': sum(1 for x in destructivos if x['con_estado']), 'acciones_del_proveedor': invocadas,
            'avisos': avisos}


def frase(r, ambiente):
    """La oracion para la pregunta de aprobacion, en criollo y con las cuentas del script."""
    c = r['cuentas']
    sujeto = 'El plan de %s' % ambiente if ambiente else 'El plan'
    partes = []

    def parte(verbo, n, cola=''):
        sustantivo = '' if partes else ' recurso' + ('' if n == 1 else 's')   # el primer numero lleva el sustantivo
        partes.append('%s %d%s%s' % (verbo, n, sustantivo, cola))

    if c['crear']:
        parte('crea', c['crear'])
    if c['cambiar']:
        parte('cambia', c['cambiar'])
    if c['reemplazar']:
        parte('reemplaza', c['reemplazar'], ' (lo borra y lo vuelve a crear)' if c['reemplazar'] == 1
              else ' (los borra y los vuelve a crear)')
    if c['borrar']:
        parte('borra', c['borrar'])
    if c['olvidar']:
        parte('saca', c['olvidar'], ' del control de la herramienta sin borrarlo' + ('' if c['olvidar'] == 1 else 's'))
    if not partes:
        texto = '%s no cambia nada (%d recurso(s) sin cambios).' % (sujeto, c['sin_cambios'])
    else:
        if not c['reemplazar'] and not c['borrar']:
            partes.append('no borra nada')
        texto = '%s %s.' % (sujeto, partes[0] if len(partes) == 1 else ', '.join(partes[:-1]) + ' y ' + partes[-1])
    guardan = [x['direccion'] for x in r['destructivos'] if x['con_estado']]
    if guardan:
        texto += ' De eso, %d guarda%s datos: %s%s.' % (
            len(guardan), '' if len(guardan) == 1 else 'n', ', '.join(guardan[:5]),
            '' if len(guardan) <= 5 else ' y %d mas' % (len(guardan) - 5))
    if r['acciones_del_proveedor']:
        texto += ' Ademas invoca %d accion(es) del proveedor.' % r['acciones_del_proveedor']
    return texto


def main():
    ap = argparse.ArgumentParser(description='Resumen de un plan de Terraform u OpenTofu para la aprobacion (solo lectura).')
    ap.add_argument('--plan', default='', help='el JSON de show -json sobre el archivo del plan')
    ap.add_argument('--ambiente', default='', help='el nombre del ambiente, para el encabezado y la frase')
    ap.add_argument('--con-estado', default='', help='tipos propios del proyecto que guardan datos, separados por coma')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    try:
        r = resumir(leer(a.plan), a.con_estado.split(','))
    except SinDatos as e:
        if a.json:
            print(json.dumps({'estado': 'SIN DATOS', 'motivo': str(e), 'plan': a.plan}, ensure_ascii=True, indent=1))
        else:
            print(ascii_de('SIN DATOS -- %s' % e))
            print('  Sin un plan legible no hay resumen, y sin resumen no hay pregunta de aprobacion.')
        return SIN_DATOS

    ambiente = limpio(''.join(c for c in unicodedata.normalize('NFD', a.ambiente) if unicodedata.category(c) != 'Mn'), 40)
    produccion = plano(a.ambiente) in PRODUCCION
    hallazgo = bool(r['destructivos'] or r['acciones_del_proveedor'])
    r.update({'estado': 'HALLAZGO' if hallazgo else 'OK', 'plan': a.plan, 'ambiente': ambiente, 'produccion': produccion,
              'no_mira': list(NO_MIRA)})
    r['frase'] = frase(r, ambiente)
    if a.json:
        print(json.dumps(r, ensure_ascii=True, indent=1))
        return HALLAZGO if hallazgo else OK

    c = r['cuentas']
    print('RESUMEN DEL PLAN -- %s   [%sformato %s; herramienta %s; %d recurso(s) en el plan]' % (
        r['estado'], 'ambiente %s; ' % ambiente if ambiente else '', r['formato'], r['herramienta_version'] or '?', r['recursos']))
    print('  ' + r['frase'])
    print('  Cuentas: crear %d, cambiar %d, reemplazar %d, borrar %d, olvidar %d, sin cambios %d  (aparte: leer %d, importar %d, mover %d)' % (
        c['crear'], c['cambiar'], c['reemplazar'], c['borrar'], c['olvidar'], c['sin_cambios'], c['leer'], c['importar'], c['mover']))
    if r['por_tipo']:
        print()
        print('  | Tipo de recurso | crear | cambiar | reemplazar | borrar | olvidar |')
        print('  |---|---|---|---|---|---|')
        for t in r['por_tipo']:
            print('  | %s | %s |' % (t['tipo'], ' | '.join(str(t[col]) for col in COLUMNAS)))
    if r['destructivos']:
        print()
        print('  SE BORRA, SE REEMPLAZA O SALE DEL ESTADO%s (decide una persona; primero lo que guarda datos):' % (
            ' -- EN PRODUCCION' if produccion else ''))
        for x in r['destructivos']:
            print('    HALLAZGO: %-10s %s%s -- %s%s%s%s' % (
                x['accion'], x['direccion'], '  [GUARDA DATOS]' if x['con_estado'] else '', QUE_ES[x['accion']],
                ' (y se crea otro)' if x['crea_otro'] else '', ' (objeto depuesto)' if x['depuesto'] else '',
                ''.join(['; por: ' + ', '.join(x['por']) if x['por'] else '', '; motivo: ' + x['motivo'] if x['motivo'] else ''])))
    if r['acciones_del_proveedor']:
        print('    HALLAZGO: el plan invoca %d accion(es) del proveedor: este script no sabe que hacen; las mira una persona' % r['acciones_del_proveedor'])
    for v in r['avisos']:
        print('  aviso: ' + v)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return HALLAZGO if hallazgo else OK


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
