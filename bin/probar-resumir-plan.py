#!/usr/bin/env python3
"""Prueba de bin/resumir-plan.py con planes de mentira (el JSON de 'show -json', armado a mano por esta prueba).
Se corre:  python -B bin/probar-resumir-plan.py   -> OK o FALLA, con el detalle de cada caso.
No necesita Terraform ni OpenTofu instalados, ni red."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'resumir-plan.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def cambio(direccion, acciones, tipo='ejemplo_red', modo='managed', **extra):
    """Un elemento de resource_changes, con la forma de la documentacion oficial."""
    c = {'actions': list(acciones), 'before': None, 'after': {'nombre': 'x'}, 'after_unknown': {}}
    for clave in ('replace_paths', 'importing', 'before', 'after'):
        if clave in extra:
            c[clave] = extra.pop(clave)
    r = {'address': direccion, 'mode': modo, 'type': tipo, 'name': direccion.split('.')[-1], 'change': c}
    r.update(extra)
    return r


def plan(cambios, **extra):
    p = {'format_version': '1.2', 'terraform_version': '1.9.5', 'planned_values': {'root_module': {}},
         'resource_changes': cambios, 'configuration': {'root_module': {}}, 'errored': False}
    p.update(extra)
    return p


def guardar(tmp, nombre, contenido, codificacion='utf-8'):
    ruta = os.path.join(tmp, nombre)
    if isinstance(contenido, (dict, list)):
        contenido = json.dumps(contenido)
    if isinstance(contenido, bytes):
        with open(ruta, 'wb') as h:
            h.write(contenido)
    else:
        with open(ruta, 'w', encoding=codificacion, newline='') as h:
            h.write(contenido)
    return ruta


def lineas_con(out, prefijo):
    return [l for l in out.splitlines() if l.strip().startswith(prefijo)]


def main():
    print('== resumir-plan')
    tmp = tempfile.mkdtemp(prefix='probar-plan-')

    # ---------- SIN DATOS: no hay de donde resumir ----------
    rc, out = correr()
    caso('sin --plan: SIN DATOS (2) y lo dice', rc == 2 and out.startswith('SIN DATOS') and '--plan' in out, out[:200])
    rc, out = correr('--plan', os.path.join(tmp, 'no-existe.json'))
    caso('el archivo no existe: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'no existe' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'vacio.json', ''))
    caso('archivo vacio: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'vacio' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'blancos.json', '  \n\n '))
    caso('archivo con solo espacios: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'vacio' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'binario.tfplan', b'PK\x03\x04\x14\x00\x08\x00tfplan\x00\xff\xfe\x00'))
    caso('el archivo binario del plan en vez del JSON: SIN DATOS (2), y dice como convertirlo',
         rc == 2 and out.startswith('SIN DATOS') and 'show -json' in out, out[:300])
    rc, out = correr('--plan', guardar(tmp, 'roto.json', '{"format_version": "1.2", "resource_changes": ['))
    caso('JSON cortado: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'JSON' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'lista.json', [1, 2]))
    caso('JSON que no es un objeto: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS'), out[:200])
    sin_version = plan([cambio('ejemplo_red.a', ['create'])])
    del sin_version['format_version']
    rc, out = correr('--plan', guardar(tmp, 'sin-version.json', sin_version))
    caso('sin format_version: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'format_version' in out, out[:200])
    for version in ('2.0', '0.2', 'uno'):
        rc, out = correr('--plan', guardar(tmp, 'v.json', plan([cambio('ejemplo_red.a', ['create'])], format_version=version)))
        caso('version de formato %s desconocida: SIN DATOS (2)' % version,
             rc == 2 and out.startswith('SIN DATOS') and 'desconocida' in out and version in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'estado.json', {'format_version': '1.0', 'terraform_version': '1.9.5',
                                                           'values': {'root_module': {'resources': []}}}))
    caso('le pasaron un estado y no un plan: SIN DATOS (2), y lo dice', rc == 2 and out.startswith('SIN DATOS') and 'estado' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'error.json', plan([cambio('ejemplo_red.a', ['create'])], errored=True)))
    caso('plan que termino con error: SIN DATOS (2), no un resumen a medias', rc == 2 and out.startswith('SIN DATOS') and 'error' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'cero.json', plan([])))
    caso('plan sin ningun recurso: SIN DATOS (2) (regla del cero)', rc == 2 and out.startswith('SIN DATOS') and 'ningun recurso' in out, out[:200])
    sin_lista = plan([])
    del sin_lista['resource_changes']
    rc, out = correr('--plan', guardar(tmp, 'sin-lista.json', sin_lista))
    caso('plan sin resource_changes: SIN DATOS (2) (regla del cero)', rc == 2 and out.startswith('SIN DATOS'), out[:200])
    rc, out = correr('--plan', guardar(tmp, 'no-lista.json', plan({'a': 1})))
    caso('resource_changes que no es una lista: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS'), out[:200])
    roto = cambio('ejemplo_red.a', ['create'])
    del roto['change']['actions']
    rc, out = correr('--plan', guardar(tmp, 'sin-acciones.json', plan([roto])))
    caso('un recurso sin acciones: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'ejemplo_red.a' in out, out[:200])
    rc, out = correr('--plan', guardar(tmp, 'rara.json', plan([cambio('ejemplo_red.a', ['create']), cambio('ejemplo_red.b', ['teleport'])])))
    caso('una accion que el script no conoce: SIN DATOS (2), con la direccion (no la adivina)',
         rc == 2 and out.startswith('SIN DATOS') and 'teleport' in out and 'ejemplo_red.b' in out, out[:300])

    # ---------- camino feliz ----------
    feliz = plan([cambio('ejemplo_red.principal', ['create']),
                  cambio('module.app.ejemplo_servicio.web[0]', ['create'], tipo='ejemplo_servicio', module_address='module.app', index=0),
                  cambio('ejemplo_regla.entrada', ['update'], tipo='ejemplo_regla', before={'puerto': 80}, after={'puerto': 443}),
                  cambio('ejemplo_red.vieja', ['no-op'])])
    ruta_feliz = guardar(tmp, 'feliz.json', feliz)
    rc, out = correr('--plan', ruta_feliz, '--ambiente', 'prueba')
    caso('crea y cambia, no borra: OK (0)', rc == 0 and out.startswith('RESUMEN DEL PLAN -- OK'), out[:300])
    caso('cuenta por accion', 'crear 2' in out and 'cambiar 1' in out and 'reemplazar 0' in out and 'borrar 0' in out
         and 'sin cambios 1' in out, out[:600])
    caso('la frase para la pregunta, en criollo y con el ambiente',
         'El plan de prueba crea 2 recursos, cambia 1 y no borra nada.' in out, out[:600])
    caso('la tabla por tipo de recurso', '| ejemplo_red | 1 | 0 | 0 | 0 | 0 |' in out and '| ejemplo_servicio | 1 | 0 | 0 | 0 | 0 |' in out
         and '| ejemplo_regla | 0 | 1 | 0 | 0 | 0 |' in out, out[:900])
    caso('termina diciendo lo que NO mira', (out.rstrip().splitlines() or [''])[-1].strip().startswith('Lo que este script NO mira:'), out[-300:])
    rc, out = correr('--plan', guardar(tmp, 'quieto.json', plan([cambio('ejemplo_red.a', ['no-op']), cambio('ejemplo_red.b', ['no-op'])])))
    caso('todo sin cambios: OK (0) y dice que no cambia nada', rc == 0 and 'no cambia nada' in out and 'sin cambios 2' in out, out[:400])

    # ---------- HALLAZGO: lo que una persona tiene que mirar ----------
    borra = plan([cambio('ejemplo_red.a', ['create']), cambio('ejemplo_dns.viejo', ['delete'], tipo='ejemplo_dns',
                                                             action_reason='delete_because_no_resource_config')])
    rc, out = correr('--plan', guardar(tmp, 'borra.json', borra))
    caso('un borrado: HALLAZGO (1), con la direccion y el motivo',
         rc == 1 and out.startswith('RESUMEN DEL PLAN -- HALLAZGO') and 'borrar 1' in out
         and any('ejemplo_dns.viejo' in l and 'delete_because_no_resource_config' in l for l in lineas_con(out, 'HALLAZGO:')), out[:700])
    caso('la frase nombra el borrado', 'crea 1 recurso y borra 1.' in out, out[:400])
    reemplaza = plan([cambio('ejemplo_servicio.web', ['delete', 'create'], tipo='ejemplo_servicio', action_reason='replace_because_cannot_update',
                             replace_paths=[['imagen'], ['red', 0, 'subred']]),
                      cambio('ejemplo_servicio.api', ['create', 'delete'], tipo='ejemplo_servicio')])
    rc, out = correr('--plan', guardar(tmp, 'reemplaza.json', reemplaza))
    caso('reemplazos en los dos ordenes (borrar y crear, crear y borrar): HALLAZGO (1), cuenta 2',
         rc == 1 and 'reemplazar 2' in out and len(lineas_con(out, 'HALLAZGO:')) == 2, out[:700])
    caso('el reemplazo dice por que atributos, sin valores', 'imagen' in out and 'red.0.subred' in out and 'replace_because_cannot_update' in out, out[:700])
    caso('la frase aclara que reemplazar es borrar y volver a crear', 'El plan reemplaza 2 recursos (los borra y los vuelve a crear).' in out, out[:400])

    con_estado = plan([cambio('ejemplo_dns.viejo', ['delete'], tipo='ejemplo_dns'),
                       cambio('ejemplo_database.principal', ['delete', 'create'], tipo='ejemplo_database'),
                       cambio('ejemplo_storage_bucket.archivos', ['delete'], tipo='ejemplo_storage_bucket')])
    rc, out = correr('--plan', guardar(tmp, 'con-estado.json', con_estado))
    guardan = [l for l in lineas_con(out, 'HALLAZGO:') if 'GUARDA DATOS' in l]
    caso('lo que guarda datos va aparte y marcado: la base y el bucket si, el DNS no',
         rc == 1 and len(guardan) == 2 and not any('ejemplo_dns' in l for l in guardan)
         and out.index('ejemplo_database.principal') < out.index('ejemplo_dns.viejo'), out[:900])
    caso('la frase dice cuantos guardan datos', '2 guardan datos' in out, out[:500])
    rc, out = correr('--plan', guardar(tmp, 'con-estado2.json', con_estado), '--con-estado', 'ejemplo_dns')
    caso('--con-estado suma un tipo propio del proyecto', rc == 1 and len([l for l in lineas_con(out, 'HALLAZGO:') if 'GUARDA DATOS' in l]) == 3, out[:900])
    tipos = ('aws_rds_cluster', 'aws_redshift_cluster', 'aws_opensearch_domain', 'aws_elasticsearch_domain',
             'aws_neptune_cluster', 'aws_kinesis_stream', 'aws_msk_cluster', 'confluent_kafka_topic_x',
             'google_bigquery_dataset', 'google_bigtable_instance', 'google_spanner_instance', 'aws_ecr_repository')
    rc, out = correr('--plan', guardar(tmp, 'mas-datos.json', plan(
        [cambio('%s.a' % t, ['delete'], tipo=t) for t in tipos] + [cambio('aws_route53_record.a', ['delete'], tipo='aws_route53_record')])))
    marcados = [l for l in lineas_con(out, 'HALLAZGO:') if 'GUARDA DATOS' in l]
    caso('rds, redshift, opensearch, elasticsearch, neptune, kinesis, msk, kafka, bigquery, bigtable, spanner y ecr guardan datos; '
         'un registro DNS no', rc == 1 and len(marcados) == len(tipos) and not any('route53' in l for l in marcados), out[:1500])

    rc, out = correr('--plan', guardar(tmp, 'olvida.json', plan([cambio('ejemplo_database.vieja', ['forget'], tipo='ejemplo_database'),
                                                              cambio('ejemplo_red.b', ['forget', 'create'])])))
    caso('olvidar (sale del estado sin borrarse): HALLAZGO (1), contado aparte del borrado',
         rc == 1 and 'olvidar 2' in out and 'borrar 0' in out and len(lineas_con(out, 'HALLAZGO:')) == 2, out[:700])
    rc, out = correr('--plan', guardar(tmp, 'depuesto.json', plan([cambio('ejemplo_red.a', ['delete'], deposed='abcd1234')])))
    caso('un objeto depuesto que se borra: cuenta como borrado y lo dice', rc == 1 and 'borrar 1' in out and 'depuesto' in out, out[:500])
    rc, out = correr('--plan', guardar(tmp, 'acciones.json', plan([cambio('ejemplo_red.a', ['create'])],
                                                                action_invocations=[{'address': 'action.ejemplo.reiniciar'}])))
    caso('acciones del proveedor que el script no sabe resumir: HALLAZGO (1), no OK',
         rc == 1 and 'accion' in out.lower() and 'del proveedor' in out, out[:500])

    # ---------- falsos positivos ----------
    datos = plan([cambio('ejemplo_red.a', ['create']), cambio('data.ejemplo_imagen.base', ['read'], tipo='ejemplo_imagen', modo='data')])
    rc, out = correr('--plan', guardar(tmp, 'datos.json', datos))
    caso('falso positivo: leer una fuente de datos no es un cambio (OK, y la cuenta aparte)',
         rc == 0 and 'crear 1' in out and 'leer 1' in out and 'crea 1 recurso y no borra nada' in out, out[:500])
    mueve = plan([cambio('ejemplo_red.nueva', ['no-op'], previous_address='ejemplo_red.vieja'),
                  cambio('ejemplo_database.adoptada', ['no-op'], tipo='ejemplo_database', importing={'id': 'id-de-afuera-123'})])
    rc, out = correr('--plan', guardar(tmp, 'mueve.json', mueve))
    caso('falso positivo: mover e importar no borran nada (OK), y se cuentan', rc == 0 and 'mover 1' in out and 'importar 1' in out, out[:500])
    caso('el identificador importado no se imprime', rc == 0 and 'importar 1' in out and 'id-de-afuera-123' not in out, out[:500])
    rc, out = correr('--plan', guardar(tmp, 'storage-crea.json', plan([cambio('ejemplo_database.nueva', ['create'], tipo='ejemplo_database')])))
    caso('falso positivo: CREAR algo que guarda datos no es hallazgo', rc == 0 and 'crear 1' in out and 'GUARDA DATOS' not in out, out[:400])
    deriva = plan([cambio('ejemplo_red.a', ['update'])], resource_drift=[cambio('ejemplo_red.a', ['update'])])
    rc, out = correr('--plan', guardar(tmp, 'deriva.json', deriva))
    caso('deriva (cambios por fuera): aviso, no cambia el estado', rc == 0 and any('por fuera' in l for l in lineas_con(out, 'aviso:')), out[:600])
    rc, out = correr('--plan', guardar(tmp, 'menor.json', plan([cambio('ejemplo_red.a', ['create'])], format_version='1.9')))
    caso('version menor mas nueva (1.9): se resume igual, con aviso', rc == 0 and 'crear 1' in out and any('1.9' in l for l in lineas_con(out, 'aviso:')), out[:500])
    rc, out = correr('--plan', guardar(tmp, 'diferido.json', plan([cambio('ejemplo_red.a', ['create'])], complete=False,
                                                                deferred_changes=[{'reason': 'x'}])))
    caso('plan incompleto (cambios diferidos): aviso con la cuenta', rc == 0 and any('diferido' in l for l in lineas_con(out, 'aviso:')), out[:500])

    # ---------- lo que nunca se imprime ----------
    secreto = plan([cambio('ejemplo_database.principal', ['delete', 'create'], tipo='ejemplo_database',
                           before={'password': 'hunter2-super-secreta'}, after={'password': 'otra-clave-9988'},
                           replace_paths=[['password']])])
    ruta_secreto = guardar(tmp, 'secreto.json', secreto)
    rc, out = correr('--plan', ruta_secreto)
    rc2, out2 = correr('--plan', ruta_secreto, '--json')
    caso('los valores de before y after no se imprimen nunca (ni en texto ni en --json)',
         rc == 1 and 'hunter2' not in out and '9988' not in out and 'hunter2' not in out2 and '9988' not in out2 and 'password' in out, out[:500])
    truco = plan([cambio('ejemplo_red.a\nRESUMEN DEL PLAN -- OK\n  HALLAZGO: nada', ['delete'], action_reason='x\nRESUMEN DEL PLAN -- OK')])
    rc, out = correr('--plan', guardar(tmp, 'truco.json', truco))
    caso('lo que trae el plan es dato: una direccion con saltos de linea no fabrica renglones del veredicto',
         rc == 1 and len(lineas_con(out, 'RESUMEN DEL PLAN')) == 1 and len(lineas_con(out, 'HALLAZGO:')) == 1, out[:600])

    # ---------- ambiente, codificaciones y --json ----------
    rc, out = correr('--plan', guardar(tmp, 'borra-prod.json', borra), '--ambiente', 'Produccion')
    caso('--ambiente produccion: el encabezado y la lista lo dicen', rc == 1 and 'EN PRODUCCION' in out and 'El plan de Produccion' in out, out[:600])
    rc, out = correr('--plan', ruta_feliz)
    caso('sin --ambiente: la frase no inventa uno', rc == 0 and 'El plan crea 2 recursos' in out, out[:400])
    rc, out = correr('--plan', guardar(tmp, 'utf16.json', json.dumps(feliz), codificacion='utf-16'))
    caso('JSON en UTF-16 (lo que deja una redireccion de PowerShell): se lee igual', rc == 0 and 'crear 2' in out, out[:300])
    rc, out = correr('--plan', guardar(tmp, 'bom.json', json.dumps(feliz), codificacion='utf-8-sig'))
    caso('JSON en UTF-8 con BOM: se lee igual', rc == 0 and 'crear 2' in out, out[:300])
    rc, out = correr('--plan', guardar(tmp, 'con-estado3.json', con_estado), '--ambiente', 'prueba', '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    caso('--json: estado, cuentas, por tipo, destructivos y frase',
         rc == 1 and d.get('estado') == 'HALLAZGO' and d.get('cuentas', {}).get('borrar') == 2 and d.get('cuentas', {}).get('reemplazar') == 1
         and len(d.get('destructivos', [])) == 3 and d.get('con_estado') == 2 and d.get('ambiente') == 'prueba'
         and d.get('formato') == '1.2' and 'frase' in d and isinstance(d.get('no_mira'), list) and isinstance(d.get('por_tipo'), list), out[:400])
    caso('--json: los destructivos traen direccion, accion y si guarda datos',
         len(d.get('destructivos', [])) == 3
         and all(set(('direccion', 'tipo', 'accion', 'con_estado', 'motivo', 'por')) <= set(x) for x in d.get('destructivos', [])), out[:400])
    acento = plan([cambio('ejemplo_red.a["caf' + chr(0xE9) + '"]', ['delete'])])
    rc, out = correr('--plan', guardar(tmp, 'acento.json', json.dumps(acento, ensure_ascii=False)), '--json')
    caso('--json sale en ASCII aunque el plan traiga acentos', rc == 1 and all(ord(c) < 128 for c in out), out[:300])
    rc, out = correr('--plan', guardar(tmp, 'sd.json', ''), '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    caso('--json tambien en SIN DATOS: estado y motivo', rc == 2 and d.get('estado') == 'SIN DATOS' and d.get('motivo'), out[:300])

    # ---------- el archivo ----------
    for ruta in (SCRIPT, os.path.abspath(__file__)):
        try:
            with open(ruta, 'rb') as h:
                datos_py = h.read()
        except OSError:
            datos_py = b''
        caso('%s es ASCII puro' % os.path.basename(ruta), bool(datos_py) and all(b < 128 for b in datos_py))

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('OK' if not fallas else 'FALLA', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
