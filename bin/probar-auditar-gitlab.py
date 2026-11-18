#!/usr/bin/env python3
"""Prueba de bin/auditar-gitlab.py sin red: respuestas guardadas (--desde), fichas, config.toml y textos de mentira.
Se corre:  python -B bin/probar-auditar-gitlab.py   -> OK o FALLA, con el detalle de cada caso."""

import copy
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'auditar-gitlab.py')
RAIZ = os.path.dirname(AQUI)
FICHA_REAL = os.path.join(RAIZ, 'cerebro-digital', 'modulo-ejemplo', 'arquitectura', 'gitlab.md')
INST = 'https://gitlab.example.com'
# lo que se planta en las respuestas y no puede aparecer nunca en la salida
PLANTADOS = ('RUNNERS-TOKEN-PLANTADO', 'VALOR-PLANTADO', 'glpat-PLANTADOabcdefghijklmnopq', 'glrt-PLANTADOabcdefghijklmnopq',
             'GR1348941PLANTADOxyz', 'juan.perez@empresa-real.com.ar', 'glrtr-PLANTADOabcdefghijklmnopq',
             'gloas-PLANTADOabcdefghijklmnopq', 'AKIA' + 'PLANTADO' + 'ABCDEFGH', 'Nombre-De-Persona-Plantado')
CASOS = []
RAIZ_PRUEBA = []   # la raiz temporal: la ficha vale solo adentro de <raiz>/cerebro-digital/


def caso(nombre, ok, detalle=''):
    CASOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(args, token=None, prefijo=None):
    env = dict(os.environ)
    env.pop('GITLAB_TOKEN', None)
    if token is not None:
        env['GITLAB_TOKEN'] = token
    cmd = prefijo if prefijo else [sys.executable, '-I', SCRIPT]
    args = list(args)
    if RAIZ_PRUEBA and args and args[0] in ('proyecto', 'grupo', 'instancia') and '--raiz' not in args:
        args += ['--raiz', RAIZ_PRUEBA[0]]
    r = subprocess.run(cmd + args, capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env=env, timeout=120)
    return r.returncode, r.stdout + r.stderr


def limpio(out):
    return not any(p in out for p in PLANTADOS)


def estados(out):
    try:
        d = json.loads(out)
    except ValueError:
        return {}
    return dict((c['id'], c['estado']) for c in d.get('chequeos', []))


def escribir(ruta, texto):
    with open(ruta, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def ficha(tmp, filas, nombre='gitlab.md', afuera=False):
    """La ficha, adentro de <tmp>/cerebro-digital/fichas/ (o directo en tmp con afuera=True)."""
    if not afuera:
        tmp = os.path.join(tmp, 'cerebro-digital', 'fichas')
        os.makedirs(tmp, exist_ok=True)
    lineas = ['---', 'id: gitlab', 'tipo: guia', '---', '', '# GitLab del proyecto', '', '## Destino autorizado', '',
              '| Instancia | Ruta (grupo o proyecto) | Ofrecimiento | Plan | Versi' + chr(0xF3) + 'n | Mirado el |',
              '|---|---|---|---|---|---|']
    for f in filas:
        lineas.append('| ' + ' | '.join(f) + ' |')
    lineas += ['', '## Runners', '', '| Alias | Alcance | Ejecutor |', '|---|---|---|', '| `runner-1` | proyecto | docker |', '']
    ruta = os.path.join(tmp, nombre)
    escribir(ruta, '\n'.join(lineas))
    return ruta


def fila(plan='Premium', ruta='grupo-a', inst=INST, ofrec='propia', version='19.5.4'):
    return ['`%s`' % inst, '`%s`' % ruta, ofrec, plan, version, '2026-11-14']


def carpeta(tmp, nombre, datos, errores=None):
    d = os.path.join(tmp, nombre)
    os.makedirs(d)
    for k, v in datos.items():
        escribir(os.path.join(d, k + '.json'), json.dumps(v))
    for k, codigo in (errores or {}).items():
        escribir(os.path.join(d, k + '.error'), str(codigo))
    return d


def proyecto_bueno():
    return {
        'proyecto': {'id': 7, 'path_with_namespace': 'grupo-a/app', 'default_branch': 'main', 'visibility': 'private',
                     'only_allow_merge_if_pipeline_succeeds': True, 'only_allow_merge_if_all_discussions_are_resolved': True,
                     'autoclose_referenced_issues': False, 'ci_separated_caches': True, 'ci_forward_deployment_enabled': True,
                     'ci_allow_fork_pipelines_to_run_in_parent_project': True,
                     'ci_pipeline_variables_minimum_override_role': 'no_one_allowed',
                     'ci_push_repository_for_job_token_allowed': False, 'shared_runners_enabled': False,
                     'runners_token': 'RUNNERS-TOKEN-PLANTADO', 'ci_config_path': '',
                     'variables': [{'key': 'CLAVE', 'value': 'VALOR-PLANTADO'}]},
        'ramas_protegidas': [{'name': 'main', 'allow_force_push': False, 'code_owner_approval_required': True,
                              'push_access_levels': [{'access_level': 0, 'access_level_description': 'No one'}],
                              'merge_access_levels': [{'access_level': 40, 'access_level_description': 'Maintainers'}]}],
        'tags_protegidos': [{'name': 'v*', 'create_access_levels': [{'access_level': 40}]}],
        'job_token_scope': {'inbound_enabled': True, 'outbound_enabled': False},
        'ambientes': [{'name': 'Produccion', 'tier': 'production', 'value': 'VALOR-PLANTADO'}, {'name': 'prueba', 'tier': 'testing'}],
        'ambientes_protegidos': [{'name': 'Produccion', 'deploy_access_levels': [{'access_level': 40}], 'required_approval_count': 1}],
        'deploy_keys': [{'id': 1, 'title': 'lectura', 'can_push': False, 'key': 'ssh-ed25519 AAAA'}],
        'usuario': {'id': 99, 'username': 'ia-lectura', 'token': 'glpat-PLANTADOabcdefghijklmnopq'},
        'miembro': {'id': 99, 'access_level': 30},
        'aprobaciones': {'merge_requests_author_approval': False, 'merge_requests_disable_committers_approval': True},
        'reglas_de_aprobacion': [{'id': 1, 'name': 'equipo', 'rule_type': 'regular', 'approvals_required': 1}],
        'push_rule': {'prevent_secrets': True},
    }


def proyecto_malo():
    d = proyecto_bueno()
    d['ramas_protegidas'][0].update({'allow_force_push': True, 'code_owner_approval_required': False,
                                     'push_access_levels': [{'access_level': 30}], 'merge_access_levels': [{'access_level': 30}]})
    d['tags_protegidos'][0]['create_access_levels'] = [{'access_level': 30}]
    d['proyecto'].update({'only_allow_merge_if_pipeline_succeeds': False, 'only_allow_merge_if_all_discussions_are_resolved': False,
                          'autoclose_referenced_issues': True, 'ci_separated_caches': False, 'ci_forward_deployment_enabled': False,
                          'visibility': 'public', 'ci_pipeline_variables_minimum_override_role': 'developer',
                          'ci_push_repository_for_job_token_allowed': True, 'shared_runners_enabled': True})
    d['job_token_scope']['inbound_enabled'] = False
    d['deploy_keys'][0]['can_push'] = True
    d['miembro']['access_level'] = 40
    d['aprobaciones']['merge_requests_author_approval'] = True
    d['reglas_de_aprobacion'][0]['approvals_required'] = 0
    d['push_rule'] = {'prevent_secrets': False}
    d['ambientes_protegidos'] = []
    return d


PREMIUM = ('aprobaciones-requeridas', 'autor-no-aprueba', 'codeowners-exigido', 'push-rules-secretos', 'produccion-protegida')
MALOS = ('push-directo', 'merge-a-rama-defecto', 'force-push', 'codeowners-exigido', 'tags-protegidos', 'pipeline-debe-pasar',
         'hilos-resueltos', 'cierre-automatico', 'variables-de-pipeline', 'caches-separadas', 'despliegues-viejos',
         'forks-en-el-padre', 'job-token-lista', 'job-token-push', 'deploy-keys-escritura', 'aprobaciones-requeridas',
         'autor-no-aprueba', 'push-rules-secretos', 'produccion-protegida')


def estaticos():
    print('== estaticos')
    caso('el script existe', os.path.isfile(SCRIPT))
    if not os.path.isfile(SCRIPT):
        return
    with open(SCRIPT, 'rb') as h:
        datos = h.read()
    caso('el script es ASCII puro', all(b < 128 for b in datos))
    with open(os.path.abspath(__file__), 'rb') as h:
        caso('la prueba es ASCII pura', all(b < 128 for b in h.read()))
    codigo = datos.decode('ascii', 'replace')
    verbos = re.findall(r'\b(POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b', codigo)
    caso('el codigo no nombra otro verbo HTTP que GET', not verbos, str(verbos))
    caso('el unico method= es GET', re.findall(r'method\s*=\s*[\'"](\w+)[\'"]', codigo) == ['GET'])
    caso('ningun pedido lleva cuerpo (no hay data=)', 'data=' not in codigo)
    caso('el token no es un argumento de la linea de comandos', not re.search(r'add_argument\([^)]*token', codigo, re.I))
    caso('el token sale de GITLAB_TOKEN', "environ.get('GITLAB_TOKEN'" in codigo)


def destino(tmp):
    print('== destino autorizado (antes de cualquier pedido)')
    bueno = carpeta(tmp, 'bueno-dest', proyecto_bueno())
    f = ficha(tmp, [fila()], 'f-dest.md')
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', os.path.join(tmp, 'no-existe.md'), '--desde', bueno])
    caso('sin ficha: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', FICHA_REAL, '--desde', bueno, '--raiz', RAIZ])
    caso('la ficha del template (solo el molde): SIN DATOS (2)', rc == 2 and 'molde' in out, out[:300])
    afuera = ficha(tmp, [fila()], 'f-afuera.md', afuera=True)
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', afuera, '--desde', bueno])
    caso('una ficha fuera de <raiz>/cerebro-digital/ no autoriza nada: SIN DATOS (2) y lo dice',
         rc == 2 and 'SIN DATOS' in out and 'cerebro-digital' in out, out[:300])
    vacia = ficha(tmp, [['`<https://host-gitlab>`', '`<grupo>`', '`<propia>`', '`<Free>`', '`<19.x.y>`', '`<aaaa-mm-dd>`']], 'f-molde.md')
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', vacia, '--desde', bueno])
    caso('ficha con una fila de molde: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
    for ruta, que in (('grupo-b/app', 'otro grupo'), ('grupo-ab/app', 'un grupo que empieza igual'),
                      ('Grupo-A/app', 'mayusculas distintas')):
        rc, out = correr(['proyecto', '--instancia', INST, '--ruta', ruta, '--ficha', f, '--desde', bueno])
        caso('ruta fuera del destino (%s): FRENA (1)' % que, rc == 1 and 'FRENA' in out, out[:300])
    rc, out = correr(['proyecto', '--instancia', INST + '.evil.test', '--ruta', 'grupo-a/app', '--ficha', f, '--desde', bueno])
    caso('instancia distinta: FRENA (1)', rc == 1 and 'FRENA' in out, out[:300])
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-b/app', '--ficha', f, '--desde', os.path.join(tmp, 'no-hay')])
    caso('FRENA antes de leer nada (la carpeta de respuestas ni existe)', rc == 1 and 'FRENA' in out, out[:300])
    rc, out = correr(['proyecto', '--instancia', 'https://127.0.0.1:9', '--ruta', 'grupo-a/app', '--ficha', f],
                     token='glpat-PLANTADOabcdefghijklmnopq')
    caso('contra la API, con token y destino no autorizado: FRENA sin pedir nada', rc == 1 and 'FRENA' in out and limpio(out), out[:300])
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', f])
    caso('contra la API sin GITLAB_TOKEN: SIN DATOS (2) y lo dice', rc == 2 and 'GITLAB_TOKEN' in out, out[:300])
    local = ficha(tmp, [fila(inst='https://127.0.0.1:9')], 'f-local.md')
    rc, out = correr(['proyecto', '--instancia', 'https://127.0.0.1:9', '--ruta', 'grupo-a/app', '--ficha', local],
                     token='glpat-PLANTADOabcdefghijklmnopq')
    caso('contra la API sin conexion: SIN DATOS (2) y el token no aparece', rc == 2 and 'SIN DATOS' in out and limpio(out), out[:300])
    insegura = ficha(tmp, [fila(inst='http://gitlab.example.com')], 'f-http.md')
    rc, out = correr(['proyecto', '--instancia', 'http://gitlab.example.com', '--ruta', 'grupo-a/app', '--ficha', insegura, '--desde', bueno])
    caso('una fila sin https no autoriza nada (el token viajaria en claro)', rc != 0 and 'https' in out, out[:300])
    doble = ficha(tmp, [fila(), fila(plan='Free')], 'f-doble.md')
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', doble, '--desde', bueno])
    caso('la misma ruta dos veces: SIN DATOS (2)', rc == 2 and 'dos veces' in out, out[:300])
    sub = ficha(tmp, [fila(plan='Free'), fila(plan='Premium', ruta='grupo-a/app')], 'f-sub.md')
    rc, out = correr(['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app', '--ficha', sub, '--desde', bueno, '--json'])
    caso('con grupo y proyecto en la ficha, vale la fila mas especifica', rc == 0 and json.loads(out)['destino']['plan'] == 'Premium', out[:300])


def proyecto(tmp):
    print('== proyecto')
    fp = ficha(tmp, [fila(plan='Premium')], 'f-premium.md')
    ff = ficha(tmp, [fila(plan='Free')], 'f-free.md')
    fs = ficha(tmp, [fila(plan=chr(0x26A0) + ' a decidir')], 'f-sinplan.md')
    bueno = carpeta(tmp, 'p-bueno', proyecto_bueno())
    base = ['proyecto', '--instancia', INST, '--ruta', 'grupo-a/app']
    rc, out = correr(base + ['--ficha', fp, '--desde', bueno])
    caso('camino feliz en Premium: OK (0)', rc == 0 and out.startswith('AUDITAR GITLAB (proyecto) -- OK'), out[:600])
    caso('camino feliz: no aparece ningun secreto plantado (runners_token, value, token)', limpio(out))
    caso('la salida termina con lo que el script NO mira', 'Lo que este script NO mira:' in out.strip().splitlines()[-1])
    rc, out = correr(base + ['--ficha', fp, '--desde', bueno, '--json'])
    e = estados(out)
    caso('--json: un chequeo por fila, todos OK', rc == 0 and e and all(v == 'OK' for v in e.values()), str(e))
    caso('--json: es ASCII y no trae secretos', all(ord(c) < 128 for c in out) and limpio(out))
    malo = carpeta(tmp, 'p-malo', proyecto_malo())
    rc, out = correr(base + ['--ficha', fp, '--desde', malo, '--json'])
    e = estados(out)
    faltan = [x for x in MALOS if e.get(x) != 'HALLAZGO']
    caso('cada barrera rota da su HALLAZGO (1)', rc == 1 and not faltan, 'no dieron HALLAZGO: %s' % faltan)
    caso('rol del token mayor que Developer y runners de instancia en un proyecto que despliega: AVISO',
         e.get('rol-del-token') == 'AVISO' and e.get('runners-de-instancia') == 'AVISO', str(e))
    caso('con todo mal, tampoco aparece ningun secreto', limpio(out))
    sin = proyecto_bueno()
    sin['ramas_protegidas'] = []
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'p-sinrama', sin), '--json'])
    e = estados(out)
    caso('rama por defecto sin proteger: HALLAZGO', rc == 1 and e.get('rama-defecto-protegida') == 'HALLAZGO', str(e))
    caso('lo que depende de la regla de la rama queda SIN DATOS, no OK', e.get('push-directo') == 'SIN DATOS', str(e))
    # un acceso que no es por rol (docs.gitlab.com/api/protected_branches: access_level null con user_id, group_id o
    # deploy_key_id) no es "nadie"
    porid = proyecto_bueno()
    porid['ramas_protegidas'][0]['push_access_levels'] = [
        {'access_level': 0, 'access_level_description': 'No one'},
        {'access_level': None, 'user_id': 5, 'group_id': None, 'access_level_description': 'Nombre-De-Persona-Plantado'},
        {'access_level': None, 'deploy_key_id': 3, 'access_level_description': 'Nombre-De-Persona-Plantado'}]
    porid['ramas_protegidas'][0]['merge_access_levels'] = [
        {'access_level': None, 'group_id': 8, 'user_id': None, 'access_level_description': 'Nombre-De-Persona-Plantado'}]
    porid['tags_protegidos'][0]['create_access_levels'] = [{'access_level': None, 'user_id': 6}]
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'p-porid', porid), '--json'])
    e = estados(out)
    caso('push, merge o tags con acceso de un usuario, grupo o deploy key (access_level nulo): AVISO con los ids, no "nadie"',
         e.get('push-directo') == 'AVISO' and e.get('merge-a-rama-defecto') == 'AVISO' and e.get('tags-protegidos') == 'AVISO'
         and 'usuario 5' in out and 'deploy key 3' in out and 'grupo 8' in out and 'usuario 6' in out and limpio(out), out[:900])
    porid['ramas_protegidas'][0]['push_access_levels'].append({'access_level': 30})
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'p-porid2', porid), '--json'])
    caso('si ademas un Developer puede empujar, sigue siendo HALLAZGO', estados(out).get('push-directo') == 'HALLAZGO', out[:600])
    # en Free lo de Premium no se pide: si se pidiera, estos .error darian SIN DATOS
    datos = proyecto_bueno()
    for k in ('aprobaciones', 'reglas_de_aprobacion', 'push_rule', 'ambientes_protegidos'):
        datos.pop(k)
    free = carpeta(tmp, 'p-free', datos, errores={'aprobaciones': 500, 'reglas_de_aprobacion': 500, 'push_rule': 500,
                                                  'ambientes_protegidos': 500})
    rc, out = correr(base + ['--ficha', ff, '--desde', free, '--json'])
    e = estados(out)
    caso('Free: lo que pide Premium sale NO DISPONIBLE EN EL PLAN y no se pide',
         all(e.get(x) == 'NO DISPONIBLE EN EL PLAN' for x in PREMIUM), str(e))
    d = json.loads(out) if out.strip().startswith('{') else {}
    caso('Free: --json lista las barreras que este plan no da', len(d.get('barreras_que_el_plan_no_da', [])) == len(PREMIUM), out[:300])
    caso('Free: lo que el plan da, bien: sale 0', rc == 0)
    rc, out = correr(base + ['--ficha', ff, '--desde', free])
    caso('Free: el resumen dice que no cuentan como OK y termina con las barreras que este plan no da',
         'no cuentan como OK' in out and 'Barreras que este plan no da' in out, out[-800:])
    rc, out = correr(base + ['--ficha', fs, '--desde', bueno, '--json'])
    e = estados(out)
    caso('plan sin declarar en la ficha: lo de Premium es SIN DATOS (2)',
         rc == 2 and all(e.get(x) == 'SIN DATOS' for x in PREMIUM), str(e))
    j403 = carpeta(tmp, 'p-403', dict((k, v) for k, v in proyecto_bueno().items() if k != 'job_token_scope'),
                   errores={'job_token_scope': 403})
    rc, out = correr(base + ['--ficha', fp, '--desde', j403, '--json'])
    e = estados(out)
    caso('un 403 en un pedido: ese chequeo SIN DATOS y la salida 2', rc == 2 and e.get('job-token-lista') == 'SIN DATOS', str(e))
    sinp = carpeta(tmp, 'p-404', dict((k, v) for k, v in proyecto_bueno().items() if k != 'proyecto'))
    rc, out = correr(base + ['--ficha', fp, '--desde', sinp])
    caso('el proyecto da 404: SIN DATOS (2), y dice por que', rc == 2 and '404' in out, out[:300])
    s401 = carpeta(tmp, 'p-401', {}, errores={'proyecto': 401})
    rc, out = correr(base + ['--ficha', fp, '--desde', s401])
    caso('un 401: SIN DATOS (2), token vencido o revocado', rc == 2 and '401' in out, out[:300])
    sinatr = proyecto_bueno()
    del sinatr['proyecto']['ci_separated_caches']
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'p-sinatr', sinatr), '--json'])
    e = estados(out)
    caso('un atributo que la respuesta no trae: SIN DATOS, no OK', rc == 2 and e.get('caches-separadas') == 'SIN DATOS', str(e))
    nada = proyecto_bueno()
    nada['push_rule'] = None
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'p-sinpush', nada), '--json'])
    caso('sin push rules (la API devuelve null): HALLAZGO', estados(out).get('push-rules-secretos') == 'HALLAZGO', out[:300])


def grupo(tmp):
    print('== grupo')
    fp = ficha(tmp, [fila(plan='Premium')], 'g-premium.md')
    ff = ficha(tmp, [fila(plan='Free')], 'g-free.md')
    bueno = {'grupo': {'id': 3, 'full_path': 'grupo-a', 'visibility': 'private', 'require_two_factor_authentication': True,
                       'project_creation_level': 'maintainer', 'runners_token': 'RUNNERS-TOKEN-PLANTADO',
                       'default_branch_protection_defaults': {'allowed_to_push': [{'access_level': 40}], 'allow_force_push': False,
                                                              'allowed_to_merge': [{'access_level': 40}]}},
             'grupo_push_rule': {'prevent_secrets': True}}
    base = ['grupo', '--instancia', INST, '--ruta', 'grupo-a']
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'g-bueno', bueno)])
    caso('grupo bien configurado, Premium: OK (0) y sin secretos', rc == 0 and limpio(out), out[:500])
    malo = copy.deepcopy(bueno)
    malo['grupo'].update({'require_two_factor_authentication': False, 'project_creation_level': 'developer', 'visibility': 'public',
                          'default_branch_protection_defaults': {'allowed_to_push': [{'access_level': 30}], 'allow_force_push': True,
                                                                 'allowed_to_merge': [{'access_level': 30}]}})
    malo['grupo_push_rule'] = {'prevent_secrets': False}
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'g-malo', malo), '--json'])
    e = estados(out)
    faltan = [x for x in ('2fa-del-grupo', 'crear-proyectos', 'proteccion-por-defecto', 'push-rules-de-grupo') if e.get(x) != 'HALLAZGO']
    caso('grupo mal configurado: HALLAZGO (1) en cada uno', rc == 1 and not faltan and e.get('visibilidad') == 'AVISO', str(e))
    viejo = copy.deepcopy(bueno)
    del viejo['grupo']['default_branch_protection_defaults']
    viejo['grupo']['default_branch_protection'] = 1
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'g-viejo', viejo), '--json'])
    caso('proteccion por defecto con el atributo viejo (1 = Developers empujan): HALLAZGO',
         estados(out).get('proteccion-por-defecto') == 'HALLAZGO', out[:300])
    sinregla = copy.deepcopy(bueno)
    del sinregla['grupo_push_rule']
    rc, out = correr(base + ['--ficha', fp, '--desde', carpeta(tmp, 'g-sinregla', sinregla), '--json'])
    caso('grupo sin push rules (la API da 404 cuando no hay): HALLAZGO', estados(out).get('push-rules-de-grupo') == 'HALLAZGO', out[:300])
    rc, out = correr(base + ['--ficha', ff, '--desde', carpeta(tmp, 'g-free', {'grupo': bueno['grupo']}), '--json'])
    caso('grupo en Free: push rules NO DISPONIBLE EN EL PLAN y sale 0',
         rc == 0 and estados(out).get('push-rules-de-grupo') == 'NO DISPONIBLE EN EL PLAN', out[:300])


def versiones(tmp, nombre, dias=0, **cambios):
    fecha = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    v = {'fecha': fecha, 'fuente': 'https://docs.gitlab.com/policy/maintenance/',
         'vigentes': ['19.5', '19.4', '19.3'],
         'ultimo_parche': {'19.5': '19.5.4', '19.4': '19.4.6', '19.3': '19.3.8', '19.2': '19.2.8', '18.11': '18.11.13'},
         'paradas': ['18.8', '18.11', '19.2', '19.5']}
    v.update(cambios)
    ruta = os.path.join(tmp, nombre)
    escribir(ruta, json.dumps(v))
    return ruta


def instancia(tmp):
    print('== instancia')
    ajustes = {'signup_enabled': False, 'require_admin_approval_after_user_signup': True, 'require_two_factor_authentication': True,
               'admin_mode': True, 'default_project_visibility': 'private', 'require_personal_access_token_expiry': True,
               'allow_runner_registration_token': False, 'allow_local_requests_from_web_hooks_and_services': False,
               'runners_registration_token': 'RUNNERS-TOKEN-PLANTADO'}
    f = ficha(tmp, [fila(plan='Free', version='19.5.4')], 'i-ficha.md')
    base = ['instancia', '--instancia', INST, '--ficha', f]
    al_dia = carpeta(tmp, 'i-aldia', {'metadata': {'version': '19.5.4-ee', 'revision': 'abc', 'enterprise': True}, 'ajustes': ajustes})
    rc, out = correr(base + ['--desde', al_dia, '--versiones', versiones(tmp, 'v1.json')])
    caso('instancia al dia y bien ajustada: OK (0), sin secretos', rc == 0 and 'al dia' in out and limpio(out), out[:800])
    vieja = carpeta(tmp, 'i-vieja', {'metadata': {'version': '19.2.3-ee', 'enterprise': True}, 'ajustes': ajustes})
    rc, out = correr(base + ['--desde', vieja, '--versiones', versiones(tmp, 'v2.json'), '--json'])
    e = estados(out)
    caso('fuera de la ventana y sin el ultimo parche: HALLAZGO (1)',
         rc == 1 and e.get('version-en-ventana') == 'HALLAZGO' and e.get('ultimo-parche') == 'HALLAZGO', str(e))
    d = json.loads(out) if out.strip().startswith('{') else {}
    caso('el camino pasa por las paradas obligatorias, cada una en su ultimo parche',
         d.get('camino_de_actualizacion') == ['19.2.8', '19.5.4'], str(d.get('camino_de_actualizacion')))
    caso('la version de la ficha no coincide con la de la instancia: AVISO', e.get('version-de-la-ficha') == 'AVISO', str(e))
    rc, out = correr(base + ['--desde', vieja, '--versiones', versiones(tmp, 'v3.json'), '--hasta', '19.4', '--json'])
    d = json.loads(out) if out.strip().startswith('{') else {}
    caso('--hasta: el camino termina en esa version', d.get('camino_de_actualizacion') == ['19.2.8', '19.4.6'], out[:300])
    rc, out = correr(base + ['--desde', al_dia, '--json'])
    e = estados(out)
    caso('sin --versiones: la ventana, el parche y el camino son SIN DATOS (2)',
         rc == 2 and all(e.get(x) == 'SIN DATOS' for x in ('version-en-ventana', 'ultimo-parche', 'camino-de-actualizacion')), str(e))
    rc, out = correr(base + ['--desde', al_dia, '--versiones', versiones(tmp, 'v4.json', dias=40)])
    caso('lista de versiones vieja: SIN DATOS (2), no OK', rc == 2 and 'vieja' in out, out[:400])
    rc, out = correr(base + ['--desde', al_dia, '--versiones', versiones(tmp, 'v4b.json', dias=-30)])
    caso('lista de versiones con fecha en el futuro: SIN DATOS (2), no OK', rc == 2 and 'futuro' in out, out[:400])
    muy_vieja = carpeta(tmp, 'i-muyvieja', {'metadata': {'version': '18.10.1'}, 'ajustes': ajustes})
    rc, out = correr(base + ['--desde', muy_vieja, '--versiones', versiones(tmp, 'v5.json'), '--json'])
    d = json.loads(out) if out.strip().startswith('{') else {}
    caso('de 18.10 a 19.5: pasa por 18.11 y 19.2, sin saltear paradas',
         d.get('camino_de_actualizacion') == ['18.11.13', '19.2.8', '19.5.4'], str(d.get('camino_de_actualizacion')))
    sin_parada = {'19.5': '19.5.4', '19.4': '19.4.6', '19.3': '19.3.8', '18.11': '18.11.13'}
    rc, out = correr(base + ['--desde', muy_vieja, '--versiones', versiones(tmp, 'v6.json', ultimo_parche=sin_parada), '--json'])
    caso('una parada intermedia sin su ultimo parche en la lista: el camino es SIN DATOS, no se inventa',
         estados(out).get('camino-de-actualizacion') == 'SIN DATOS' and '19.2' in out, out[:400])
    s403 = carpeta(tmp, 'i-403', {'metadata': {'version': '19.5.4-ee'}}, errores={'ajustes': 403})
    rc, out = correr(base + ['--desde', s403, '--versiones', versiones(tmp, 'v7.json'), '--json'])
    e = estados(out)
    caso('sin token de administrador (403 en los ajustes): esos chequeos SIN DATOS (2)',
         rc == 2 and e.get('registro-abierto') == 'SIN DATOS' and 'administrador' in out, str(e))
    malos = dict(ajustes, signup_enabled=True, require_admin_approval_after_user_signup=False, require_two_factor_authentication=False,
                 admin_mode=False, default_project_visibility='public', require_personal_access_token_expiry=False,
                 allow_runner_registration_token=True, allow_local_requests_from_web_hooks_and_services=True)
    rc, out = correr(base + ['--desde', carpeta(tmp, 'i-malos', {'metadata': {'version': '19.5.4'}, 'ajustes': malos}),
                             '--versiones', versiones(tmp, 'v8.json'), '--json'])
    e = estados(out)
    faltan = [x for x in ('registro-abierto', '2fa-instancia', 'admin-mode', 'visibilidad-por-defecto', 'vencimiento-de-tokens',
                          'registro-viejo-de-runners', 'webhooks-a-la-red-local') if e.get(x) != 'HALLAZGO']
    caso('cada ajuste flojo de la instancia: HALLAZGO (1)', rc == 1 and not faltan and limpio(out), 'faltan: %s' % faltan)
    com = ficha(tmp, [fila(inst='https://gitlab.com', ofrec='GitLab.com', plan='Premium')], 'i-com.md')
    rc, out = correr(['instancia', '--instancia', 'https://gitlab.com', '--ficha', com, '--desde', al_dia])
    caso('GitLab.com: el modo instancia no aplica, SIN DATOS (2)', rc == 2 and 'GitLab.com' in out, out[:300])


TOML_BUENO = '''concurrent = 2
[[runners]]
  name = "host-real-01.interno"
  url = "https://gitlab.example.com"
  token = "glrt-PLANTADOabcdefghijklmnopq"
  executor = "docker"
  [runners.docker]
    image = "alpine:3.20"
    privileged = false
    volumes = ["/cache"]
    pull_policy = ["always"]
    allowed_images = ["registry.example.com/*"]
    allowed_pull_policies = ["always"]
'''

TOML_MALO = '''[[runners]]
  name = "host-real-02.interno"
  token = "GR1348941PLANTADOxyz"
  executor = "shell"
  environment = ["AWS_SECRET_ACCESS_KEY=VALOR-PLANTADO", "LANG=C"]
[[runners]]
  name = "host-real-03.interno"
  token = "glrt-PLANTADOabcdefghijklmnopq"
  executor = "docker"
  [runners.docker]
    privileged = true
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
    pull_policy = "if-not-present"
'''


def runner(tmp):
    print('== runner')
    bueno = os.path.join(tmp, 'config-bueno.toml')
    escribir(bueno, TOML_BUENO)
    malo = os.path.join(tmp, 'config-malo.toml')
    escribir(malo, TOML_MALO)
    if sys.version_info >= (3, 11):
        rc, out = correr(['runner', '--config', bueno])
        caso('config.toml endurecido: OK (0)', rc == 0, out[:500])
        caso('no aparece ni el token ni el nombre real del host', limpio(out) and 'host-real' not in out, out[:500])
        rc, out = correr(['runner', '--config', malo, '--json'])
        e = estados(out)
        caso('privileged y el socket de Docker: HALLAZGO (1)',
             rc == 1 and e.get('runner[2].privileged') == 'HALLAZGO' and e.get('runner[2].socket-docker') == 'HALLAZGO', str(e))
        caso('un secreto en environment: HALLAZGO, con el nombre y sin el valor',
             e.get('runner[1].secretos-en-environment') == 'HALLAZGO' and 'AWS_SECRET_ACCESS_KEY' in out and limpio(out), str(e))
        caso('ejecutor shell, if-not-present, sin listas permitidas y token viejo: AVISO',
             e.get('runner[1].ejecutor') == 'AVISO' and e.get('runner[2].pull-policy') == 'AVISO'
             and e.get('runner[2].listas-permitidas') == 'AVISO' and e.get('runner[1].token-formato') == 'AVISO', str(e))
        caso('con todo mal, ni tokens ni hosts en la salida', limpio(out) and 'host-real' not in out)
        roto = os.path.join(tmp, 'roto.toml')
        escribir(roto, '[[runners]\nexecutor = ')
        rc, out = correr(['runner', '--config', roto])
        caso('config.toml ilegible: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
        vacio = os.path.join(tmp, 'vacio.toml')
        escribir(vacio, 'concurrent = 1\n')
        rc, out = correr(['runner', '--config', vacio])
        caso('config.toml sin [[runners]]: SIN DATOS (2)', rc == 2, out[:300])
    else:
        caso('(Python %d.%d: los casos con tomllib se saltean)' % sys.version_info[:2], True)
    rc, out = correr(['runner', '--config', os.path.join(tmp, 'no-existe.toml')])
    caso('config.toml ausente: SIN DATOS (2)', rc == 2, out[:300])
    rc, out = correr(['runner'])
    caso('sin --config: SIN DATOS (2)', rc == 2, out[:300])
    bloqueo = ("import runpy, sys; sys.modules['tomllib'] = None; sys.argv = [%r] + sys.argv[1:]; "
               "runpy.run_path(%r, run_name='__main__')" % (SCRIPT, SCRIPT))
    rc, out = correr(['runner', '--config', bueno], prefijo=[sys.executable, '-I', '-c', bloqueo])
    caso('sin tomllib (Python anterior a 3.11): SIN DATOS (2) y dice por que', rc == 2 and '3.11' in out, out[:300])


def texto(tmp):
    print('== texto')
    malos = [('Closes #12', 'cierre'), ('Esto fixes grupo/proyecto#3 de paso', 'cierre'),
             ('Resolves https://gitlab.example.com/g/p/-/issues/4', 'cierre'), ('Fixes AB#55', 'cierre'),
             ('/merge', 'acciones-rapidas'), ('  /approve', 'acciones-rapidas'),
             ('token: glpat-PLANTADOabcdefghijklmnopq', 'tokens'), ('runner: glrt-PLANTADOabcdefghijklmnopq', 'tokens'),
             ('runner viejo: glrtr-PLANTADOabcdefghijklmnopq', 'tokens'), ('app: gloas-PLANTADOabcdefghijklmnopq', 'tokens'),
             ('la clave de la nube: ' + 'AKIA' + 'PLANTADO' + 'ABCDEFGH', 'tokens'),
             ('conexion: postgres://admin:VALOR-PLANTADO@db.example.com/app', 'tokens'),
             ('escribile a juan.perez@empresa-real.com.ar', 'datos-personales')]
    for i, (linea, cid) in enumerate(malos):
        ruta = os.path.join(tmp, 't-malo-%d.md' % i)
        escribir(ruta, 'Descripcion del cambio.\n\n%s\n' % linea)
        rc, out = correr(['texto', ruta, '--json'])
        caso('texto con "%s": HALLAZGO en %s' % (linea.strip()[:30], cid), rc == 1 and estados(out).get(cid) == 'HALLAZGO', out[:300])
        caso('  ... y el valor no se repite en la salida', limpio(out))
    bueno = os.path.join(tmp, 't-bueno.md')
    escribir(bueno, 'Related to #12\n\nSe toco /etc/gitlab/gitlab.rb y el prefix #3.\n/etc/gitlab/gitlab.rb\n'
                    'Los tokens empiezan con `glpat-`.\nCualquier duda: contacto@example.com\nCierra #12 (en castellano no cierra).\n')
    rc, out = correr(['texto', bueno])
    caso('texto limpio (Related to, rutas, prefijo suelto, correo de ejemplo): OK (0)', rc == 0, out[:600])
    rc, out = correr(['texto', bueno, '--json'])
    caso('el correo de un dominio de ejemplo es AVISO, no HALLAZGO', estados(out).get('datos-personales') == 'AVISO', out[:300])
    vacio = os.path.join(tmp, 't-vacio.md')
    escribir(vacio, '  \n')
    rc, out = correr(['texto', vacio])
    caso('texto vacio: SIN DATOS (2)', rc == 2, out[:300])
    rc, out = correr(['texto', os.path.join(tmp, 'no-existe.md')])
    caso('texto ausente: SIN DATOS (2)', rc == 2, out[:300])


def main():
    tmp = tempfile.mkdtemp(prefix='probar-gitlab-')
    RAIZ_PRUEBA.append(tmp)
    try:
        estaticos()
        destino(tmp)
        proyecto(tmp)
        grupo(tmp)
        instancia(tmp)
        runner(tmp)
        texto(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in CASOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('OK' if not fallas else 'FALLA', len(CASOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
