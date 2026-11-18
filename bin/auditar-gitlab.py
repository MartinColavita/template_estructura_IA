#!/usr/bin/env python3
"""GitLab como plataforma, en datos duros: un proyecto, un grupo, un runner, la instancia, o un texto antes de
escribirlo en GitLab. SOLO LECTURA.

    python -I bin/auditar-gitlab.py proyecto  --instancia https://<host> --ruta <grupo>/<proyecto> [--desde <carpeta>]
    python -I bin/auditar-gitlab.py grupo     --instancia https://<host> --ruta <grupo> [--desde <carpeta>]
    python -I bin/auditar-gitlab.py instancia --instancia https://<host> [--versiones <archivo>] [--hasta 19.5] [--desde <carpeta>]
    python -I bin/auditar-gitlab.py runner    --config <copia-local-de-config.toml>
    python -I bin/auditar-gitlab.py texto     <archivo>
    opciones: --json  |  --ficha <ruta> o --modulo <slug> (por defecto, la unica cerebro-digital/*/arquitectura/gitlab.md;
              una --ficha fuera de <raiz>/cerebro-digital/ no autoriza nada: SIN DATOS)
    El token sale de la variable de entorno GITLAB_TOKEN: nunca de un argumento, y no se imprime nunca.
    --desde <carpeta>: lee respuestas guardadas (<clave>.json, o <clave>.error con el codigo HTTP) en lugar de la API.

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (o FRENA)   2 = SIN DATOS

Cada chequeo declara el plan que necesita (Free, Premium, Ultimate). Lo que el plan de la ficha no da sale
NO DISPONIBLE EN EL PLAN: no se pide, no cuenta como OK ni cambia la salida, y el resumen termina con las
barreras que este plan no da y lo que las reemplaza. Un AVISO pide criterio: tampoco cambia la salida.

POR QUE EXISTE. Las barreras de GitLab viven en su configuracion y dependen del plan: en Free la aprobacion de
un Merge Request no frena el merge, y no hay CODEOWNERS, push rules ni ambientes protegidos. Mirarlo a mano por
la interfaz es lento y se equivoca, y leer no siempre es inocente: la API devuelve valores de variables y tokens
de registro. Este script lee siempre igual, por lista blanca de campos, y dice que barrera da el plan.

QUE NO HACE. Solo pide GET a la API v4, con urllib, y no sigue redirecciones (el token no viaja a otro lado).
Antes de cualquier pedido compara la instancia y la ruta, exacto, con la tabla "Destino autorizado" de la ficha
"GitLab del proyecto": si no estan, FRENA sin pedir nada; sin ficha o con solo el molde, SIN DATOS. Nunca lee
valores de variables, archivos seguros, estado de Terraform ni logs de jobs; nunca guarda la respuesta cruda;
no baja nada de internet (la lista de versiones vigentes la recibe por --versiones). No cambia nada en GitLab.
Solo biblioteca estandar; el modo runner pide Python 3.11 o mas (tomllib). ASCII puro en este archivo.
"""

import argparse
import datetime
import fnmatch
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditoria import cierre, phi, secretos  # noqa: E402  el mismo criterio que auditar-diff.py y auditar-tarea.py
from operacion import inventario  # noqa: E402  el mismo lector de tablas del Cerebro que el GATE de SERVIDOR

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
E_OK, E_HALL, E_SD, E_AVISO, E_PLAN = 'OK', 'HALLAZGO', 'SIN DATOS', 'AVISO', 'NO DISPONIBLE EN EL PLAN'
PLANES = ('free', 'premium', 'ultimate')
NOMBRE_PLAN = {'free': 'Free', 'premium': 'Premium', 'ultimate': 'Ultimate'}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_DIAS_VERSIONES = 15            # hay parches dos veces por mes: una lista mas vieja puede no tener el critico
ROL = {0: 'nadie', 30: 'Developer', 40: 'Maintainer', 50: 'Owner', 60: 'administrador'}
# Un secreto en un texto: los formatos conocidos de auditoria/secretos.py, el criterio comun (los prefijos de token de
# GitLab de la tabla oficial, mas los de otros proveedores, claves privadas y URL con usuario y clave).
COLUMNAS_FICHA = (('instancia', 'instancia'), ('ruta', 'ruta'), ('ofrecimiento', 'ofrecimiento'), ('plan', 'plan'),
                  ('version', 'version'), ('mirado', 'mirado'))

# Lista blanca: de cada respuesta entra al script solo esto. Lo demas (tokens de registro, valores, nombres de
# personas) se descarta al leer y no llega a ninguna salida. (nombre, sub) es un campo anidado.
# Un acceso por rol trae access_level; uno dado a un usuario, un grupo o una deploy key trae access_level null y el id
# (docs.gitlab.com/api/protected_branches). Los ids no son secretos; la descripcion (puede ser un nombre) no entra.
NIVELES = ('access_level', 'user_id', 'group_id', 'deploy_key_id')
LISTA_BLANCA = {
    'proyecto': ('default_branch', 'visibility', 'only_allow_merge_if_pipeline_succeeds',
                 'only_allow_merge_if_all_discussions_are_resolved', 'autoclose_referenced_issues', 'ci_separated_caches',
                 'ci_forward_deployment_enabled', 'ci_allow_fork_pipelines_to_run_in_parent_project',
                 'ci_pipeline_variables_minimum_override_role', 'restrict_user_defined_variables',
                 'ci_push_repository_for_job_token_allowed', 'shared_runners_enabled'),
    'ramas_protegidas': ('name', 'allow_force_push', 'code_owner_approval_required',
                         ('push_access_levels', NIVELES), ('merge_access_levels', NIVELES)),
    'tags_protegidos': ('name', ('create_access_levels', NIVELES)),
    'job_token_scope': ('inbound_enabled',),
    'ambientes': ('name', 'tier'),
    'ambientes_protegidos': ('name', 'required_approval_count', ('approval_rules', ('required_approvals',))),
    'deploy_keys': ('can_push',),
    'usuario': ('id',),
    'miembro': ('access_level',),
    'aprobaciones': ('merge_requests_author_approval', 'merge_requests_disable_committers_approval'),
    'reglas_de_aprobacion': ('rule_type', 'approvals_required'),
    'push_rule': ('prevent_secrets',),
    'grupo': ('visibility', 'require_two_factor_authentication', 'project_creation_level', 'default_branch_protection',
              ('default_branch_protection_defaults',
               ('allow_force_push', ('allowed_to_push', NIVELES), ('allowed_to_merge', NIVELES)))),
    'grupo_push_rule': ('prevent_secrets',),
    'metadata': ('version',),
    'ajustes': ('signup_enabled', 'require_admin_approval_after_user_signup', 'require_two_factor_authentication',
                'admin_mode', 'default_project_visibility', 'require_personal_access_token_expiry',
                'allow_runner_registration_token', 'allow_local_requests_from_web_hooks_and_services'),
}

REEMPLAZO_PUSH = ('bin/auditar-diff.py y el hook local frenan el secreto antes del push (las push rules tampoco ven '
                  'los commits hechos por la interfaz o por la API)')
REEMPLAZO = {
    'aprobaciones-requeridas': 'la aprobacion no frena el merge: la barrera es quien puede mergear a la rama protegida '
                               '(Maintainers) y que la identidad de la IA no pase de Developer',
    'autor-no-aprueba': 'mergea una persona Maintainer, y el verificador distinto del que produjo lo pone el metodo '
                        '(skill desarrollo)',
    'codeowners-exigido': 'quien revisa los cambios de .gitlab-ci.yml lo fija el metodo y lo mira una persona antes de mergear',
    'push-rules-secretos': REEMPLAZO_PUSH,
    'push-rules-de-grupo': REEMPLAZO_PUSH,
    'produccion-protegida': 'la barrera de produccion es la rama o el tag protegido (solo llegan Maintainers), con '
                            'variables y runners protegidos; mejor, id_tokens con un gestor de secretos que exija ref protegida',
}

NO_MIRA = {
    'proyecto': ('el YAML del pipeline (bin/verificar-pipeline.py, de despliegue-continuo)', 'el contenido de CODEOWNERS',
                 'si las reglas le sirven al equipo', 'los tokens del proyecto y su vencimiento',
                 'los runners asignados (modo runner, sobre su config.toml)',
                 'valores de variables, archivos seguros, estado de Terraform ni logs de jobs: no los lee nunca'),
    'grupo': ('los proyectos del grupo uno por uno (modo proyecto)', 'los runners del grupo', 'los miembros y sus roles'),
    'instancia': ('si la version tiene un CVE concreto: mira la ventana de mantenimiento, no una base de vulnerabilidades',
                  'el sistema operativo del host (operacion-de-servidores y seguridad)',
                  'los respaldos ni si se pueden restaurar', 'el ingreso por un proveedor externo (SSO) que exija 2FA'),
    'runner': ('si el runner esta protegido, bloqueado a un proyecto o corre jobs sin etiqueta: eso vive en GitLab, no en '
               'config.toml', 'el host del runner (operacion-de-servidores y seguridad)'),
    'texto': ('si el texto es correcto o le sirve a quien lo lee', 'nombres, direcciones y diagnosticos: los lee el auditor',
              'una clave sin formato conocido (una contrasena suelta): la mira quien escribe'),
}


# ---------------------------------------------------------------- la ficha y el destino autorizado

def leer_ficha(ruta):
    """(filas, problemas) de la tabla "Destino autorizado". Lanza OSError si no se puede abrir. Una tabla cuenta
    solo si su ENCABEZADO tiene las columnas Instancia y Ruta; las filas de molde (con < o vacias) se saltean."""
    with open(ruta, 'rb') as h:
        texto = h.read().decode('utf-8', errors='replace').replace('\r\n', '\n')
    if texto.startswith(inventario.BOM):
        texto = texto[1:]
    filas = [inventario.celdas(l) for l in texto.split('\n')]
    res, problemas = [], []
    orden, en_tabla = None, False
    for i, fila in enumerate(filas):
        if fila is None:
            orden, en_tabla = None, False
            continue
        if not en_tabla:
            en_tabla, orden = True, None
            siguiente = filas[i + 1] if i + 1 < len(filas) else None
            encabezado = [inventario.plano(c) for c in fila]
            if (siguiente is not None and inventario.es_separador(siguiente)
                    and any(e.startswith('instancia') for e in encabezado) and any(e.startswith('ruta') for e in encabezado)):
                orden = {}
                for j, e in enumerate(encabezado):
                    for palabra, clave in COLUMNAS_FICHA:
                        if e.startswith(palabra) and clave not in orden.values():
                            orden[j] = clave
                            break
            continue
        if orden is None or inventario.es_separador(fila):
            continue
        d = dict((clave, '') for _, clave in COLUMNAS_FICHA)
        for j, c in enumerate(fila):
            if j in orden:
                d[orden[j]] = inventario.limpio(c)
        crudo = d['instancia'] + d['ruta']
        if not d['instancia'] or not d['ruta'] or '<' in crudo or '>' in crudo or not crudo.strip(inventario.RAYAS):
            continue
        d['instancia'], d['ruta'], d['linea'] = d['instancia'].rstrip('/'), d['ruta'].strip('/'), i + 1
        if not d['instancia'].startswith('https://'):
            problemas.append('linea %d: la instancia %s no empieza con https://, y no autoriza nada (el token viajaria '
                             'en claro)' % (i + 1, d['instancia']))
            continue
        res.append(d)
    return res, problemas


def ubicar_ficha(raiz, modulo):
    base = os.path.join(raiz, 'cerebro-digital')
    if modulo:
        ruta = os.path.join(base, modulo, 'arquitectura', 'gitlab.md')
        return (ruta, '') if os.path.isfile(ruta) else (None, 'no existe %s' % os.path.relpath(ruta, raiz))
    rutas = sorted(r for r in glob.glob(os.path.join(base, '*', 'arquitectura', 'gitlab.md'))
                   if os.path.basename(os.path.dirname(os.path.dirname(r))) != 'configuracion-ia')
    if not rutas:
        return None, 'ningun modulo de cerebro-digital/ tiene arquitectura/gitlab.md (la ficha "GitLab del proyecto")'
    if len(rutas) > 1:
        return None, 'hay %d fichas de GitLab: hay que decir de cual modulo (--modulo)' % len(rutas)
    return rutas[0], ''


def autorizar(ruta_ficha, instancia, ruta, modo):
    """('OK' | 'FRENA' | 'SIN DATOS', fila, motivo). Exacto: ante la duda, no esta autorizado."""
    if not os.path.isfile(ruta_ficha):
        return E_SD, None, 'no existe la ficha %s: sin ficha, ningun GitLab esta autorizado' % ruta_ficha
    try:
        filas, problemas = leer_ficha(ruta_ficha)
    except OSError as e:
        return E_SD, None, 'no se pudo leer la ficha: %s' % type(e).__name__
    if not filas:
        return E_SD, None, ('la tabla "Destino autorizado" de la ficha no tiene ninguna fila cargada (solo el molde): '
                            'nada esta autorizado' + ''.join('; ' + p for p in problemas))
    inst = (instancia or '').strip().rstrip('/')
    if not inst:
        return E_SD, None, 'falta --instancia https://<host>'
    misma = [f for f in filas if f['instancia'] == inst]
    if modo == 'instancia':
        if not misma:
            return 'FRENA', None, '%s no esta en "Destino autorizado" de la ficha: para la IA no existe, ni para leerla' % inst
        return E_OK, misma[0], ''
    r = (ruta or '').strip()
    if not r or any(s in ('', '.', '..') for s in r.split('/')):
        return E_SD, None, 'falta --ruta <grupo>/<proyecto> (sin barras al principio ni al final, sin . ni ..)'
    cubren = [f for f in misma if r == f['ruta'] or r.startswith(f['ruta'] + '/')]
    if not cubren:
        return 'FRENA', None, ('%s %s no esta en "Destino autorizado" de la ficha (se compara exacto, segmento por '
                               'segmento y con mayusculas): para la IA no existe, ni para leerlo' % (inst, r))
    largo = max(len(f['ruta']) for f in cubren)
    mejores = [f for f in cubren if len(f['ruta']) == largo]
    if len(mejores) > 1:
        return E_SD, None, ('la ruta %s figura dos veces en "Destino autorizado" (lineas %s): no se puede saber cual vale'
                            % (mejores[0]['ruta'], ', '.join(str(f['linea']) for f in mejores)))
    return E_OK, mejores[0], ''


# ---------------------------------------------------------------- de donde salen las respuestas

def filtrar(obj, spec):
    """Deja solo los campos de la lista blanca: un nombre (valor simple) o (nombre, spec) para lo anidado."""
    if isinstance(obj, list):
        return [filtrar(x, spec) for x in obj if isinstance(x, dict)]
    if not isinstance(obj, dict):
        return None
    res = {}
    for s in spec:
        if isinstance(s, tuple):
            if s[0] in obj:
                v = obj[s[0]]
                res[s[0]] = filtrar(v, s[1]) if isinstance(v, (dict, list)) else None
        elif s in obj:
            v = obj[s]
            res[s] = v if (v is None or isinstance(v, (str, int, float, bool))) else None
    return res


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None     # una redireccion no se sigue: queda como error y el token no sale hacia otro lado


class Fuente(object):
    """La API v4 (solo GET) o una carpeta con respuestas guardadas (--desde)."""

    def __init__(self, instancia, desde, token):
        self.instancia, self.desde, self.token = instancia, desde, token
        self.abridor = urllib.request.build_opener(_SinRedirecciones())

    def leer(self, clave, camino):
        """(codigo, cuerpo ya filtrado por la lista blanca, hay_mas). codigo 0: sin conexion; -1: ilegible."""
        codigo, cuerpo, mas = self._desde(clave) if self.desde else self._api(camino)
        if codigo != 200:
            return codigo, None, False
        return 200, (filtrar(cuerpo, LISTA_BLANCA[clave]) if cuerpo is not None else None), mas

    def _desde(self, clave):
        base = os.path.join(self.desde, clave)
        if os.path.isfile(base + '.json'):
            with open(base + '.json', 'r', encoding='utf-8', errors='replace') as h:
                texto = h.read()
            try:
                return 200, (json.loads(texto) if texto.strip() else None), False
            except ValueError:
                return -1, None, False
        if os.path.isfile(base + '.error'):
            with open(base + '.error', 'r', encoding='utf-8', errors='replace') as h:
                t = h.read().strip()
            return (int(t) if t.isdigit() else -1), None, False
        return 404, None, False

    def _api(self, camino):
        pedido = urllib.request.Request(self.instancia + '/api/v4/' + camino, method='GET',
                                        headers={'PRIVATE-TOKEN': self.token, 'Accept': 'application/json'})
        try:
            with self.abridor.open(pedido, timeout=20) as r:
                texto = r.read().decode('utf-8', 'replace')
                mas = bool((r.headers.get('X-Next-Page') or '').strip())
                return 200, (json.loads(texto) if texto.strip() else None), mas
        except urllib.error.HTTPError as e:
            return e.code, None, False
        except ValueError:
            return -1, None, False
        except (urllib.error.URLError, OSError):
            return 0, None, False


def motivo_http(codigo):
    if codigo == 401:
        return 'la API respondio 401: el token falta, vencio o fue revocado'
    if codigo == 403:
        return 'la API respondio 403: el token no tiene permiso para esto'
    if codigo == 404:
        return 'la API respondio 404: no existe o el token no lo ve (GitLab esconde lo privado con un 404)'
    if codigo == 0:
        return 'no se pudo conectar con la instancia (red, VPN o certificado)'
    if codigo == -1:
        return 'la respuesta no se pudo leer'
    if 300 <= codigo < 400:
        return 'la API respondio con una redireccion (%d): no se sigue' % codigo
    return 'la API respondio %d' % codigo


def traer(fuente, clave, camino, tipo, nulo=False):
    """(cuerpo, motivo): motivo vacio si salio bien. nulo: una respuesta null es valida (la push rule que no existe)."""
    codigo, cuerpo, mas = fuente.leer(clave, camino)
    if codigo != 200:
        return None, motivo_http(codigo)
    if mas:
        return None, 'la respuesta trae mas de 100 elementos y se miraron solo los primeros: no se puede decidir sobre todos'
    if cuerpo is None:
        return None, ('' if nulo else 'la respuesta vino vacia')
    if not isinstance(cuerpo, tipo):
        return None, 'la respuesta no tiene la forma esperada'
    return cuerpo, ''


# ---------------------------------------------------------------- el informe

class Informe(object):
    def __init__(self, plan):
        self.plan = plan            # 'free', 'premium', 'ultimate', o None si la ficha no lo declara
        self.chequeos = []
        self.sin_plan = []          # lo que el plan no da, con lo que lo reemplaza
        self.extra = {}

    def anotar(self, cid, estado, detalle, pide='free'):
        self.chequeos.append({'id': cid, 'estado': estado, 'pide': NOMBRE_PLAN[pide], 'detalle': detalle})

    def da(self, cid, pide):
        """True si hay que correr el chequeo. Si el plan no lo da (o no se sabe), lo anota y no se pide nada."""
        if pide == 'free':
            return True
        if self.plan is None:
            self.anotar(cid, E_SD, 'la ficha no declara el plan, y este chequeo pide %s' % NOMBRE_PLAN[pide], pide)
            return False
        if PLANES.index(self.plan) < PLANES.index(pide):
            self.anotar(cid, E_PLAN, 'pide %s y el plan es %s' % (NOMBRE_PLAN[pide], NOMBRE_PLAN[self.plan]), pide)
            self.sin_plan.append({'id': cid, 'pide': NOMBRE_PLAN[pide], 'reemplazo': REEMPLAZO[cid]})
            return False
        return True

    def si(self, cid, malo, si_mal, si_bien, pide='free'):
        self.anotar(cid, E_HALL if malo else E_OK, si_mal if malo else si_bien, pide)

    def booleano(self, cid, obj, campo, bueno, si_bien, si_mal, pide='free'):
        """OK si el atributo vale <bueno>, HALLAZGO si vale lo contrario, SIN DATOS si la respuesta no lo trae."""
        if not isinstance(obj, dict) or not isinstance(obj.get(campo), bool):
            self.anotar(cid, E_SD, '%s: la respuesta no lo trae (version anterior, o el token no lo ve)' % campo, pide)
        else:
            self.si(cid, obj[campo] != bueno, si_mal, si_bien, pide)

    def sd(self, ids, motivo, pide='free'):
        for cid in ids:
            self.anotar(cid, E_SD, motivo, pide)


def niveles(objetos, campo):
    return [x.get('access_level') for o in objetos for x in (o.get(campo) or [])
            if isinstance(x, dict) and isinstance(x.get('access_level'), int)]


def no_por_rol(objetos, campo):
    """Los accesos que no son por rol (access_level null con user_id, group_id o deploy_key_id): 'usuario 5', ..."""
    res = []
    for o in objetos:
        for x in o.get(campo) or []:
            if not isinstance(x, dict) or isinstance(x.get('access_level'), int):
                continue
            for clave, nombre in (('user_id', 'usuario'), ('group_id', 'grupo'), ('deploy_key_id', 'deploy key')):
                if isinstance(x.get(clave), int):
                    res.append('%s %d' % (nombre, x[clave]))
                    break
            else:
                res.append('un acceso sin rol ni id')
    return res


def acceso(inf, cid, nivs, otros, si_mal, si_bien):
    """HALLAZGO si llega un Developer; si no, AVISO si hay accesos que no son por rol (no se sabe que rol tienen);
    si no, OK."""
    if developer(nivs):
        inf.anotar(cid, E_HALL, si_mal)
    elif otros:
        inf.anotar(cid, E_AVISO, '%s; ademas tienen acceso, no por rol: %s (mirar a mano quien es y que rol tiene)' % (
            si_bien, ', '.join(otros[:10])))
    else:
        inf.anotar(cid, E_OK, si_bien)


def roles(nivs):
    return ', '.join(ROL.get(n, str(n)) for n in sorted(set(nivs))) or 'nadie'


def developer(nivs):
    return any(0 < n <= 30 for n in nivs)


# ---------------------------------------------------------------- proyecto

def modo_proyecto(fuente, inf, ruta):
    base = 'projects/' + urllib.parse.quote(ruta, safe='')
    proy, motivo = traer(fuente, 'proyecto', base, dict)
    if motivo:
        return motivo
    rama = proy.get('default_branch') or ''

    ramas, m = traer(fuente, 'ramas_protegidas', base + '/protected_branches?per_page=100', list)
    reglas = [r for r in ramas or [] if isinstance(r.get('name'), str) and fnmatch.fnmatchcase(rama, r['name'])]
    de_la_rama = ('push-directo', 'merge-a-rama-defecto', 'force-push')
    if m or not rama:
        inf.sd(('rama-defecto-protegida',) + de_la_rama, m or 'el proyecto no tiene rama por defecto (repositorio vacio)')
    elif not reglas:
        inf.anotar('rama-defecto-protegida', E_HALL, 'la rama por defecto %s no esta protegida: cualquier Developer empuja y mergea' % rama)
        inf.sd(de_la_rama, 'depende de que %s este protegida (ver rama-defecto-protegida)' % rama)
    else:
        inf.anotar('rama-defecto-protegida', E_OK, '%s esta protegida' % rama)
        push, merge = niveles(reglas, 'push_access_levels'), niveles(reglas, 'merge_access_levels')
        acceso(inf, 'push-directo', push, no_por_rol(reglas, 'push_access_levels'),
               'un Developer puede empujar directo a %s (va "No one", o Maintainers como minimo)' % rama,
               'empujan directo a %s: %s' % (rama, roles(push)))
        acceso(inf, 'merge-a-rama-defecto', merge, no_por_rol(reglas, 'merge_access_levels'),
               'un Developer puede mergear a %s: la identidad de la IA (Developer) tambien' % rama, 'mergean a %s: %s' % (rama, roles(merge)))
        inf.si('force-push', any(r.get('allow_force_push') is True for r in reglas),
               '%s permite force push: se puede reescribir la historia' % rama, '%s no permite force push' % rama)
    if inf.da('codeowners-exigido', 'premium'):
        valores = [r.get('code_owner_approval_required') for r in reglas if isinstance(r.get('code_owner_approval_required'), bool)]
        if not valores:
            inf.anotar('codeowners-exigido', E_SD, m or 'la rama por defecto no tiene una regla que diga si exige CODEOWNERS', 'premium')
        else:
            inf.si('codeowners-exigido', True not in valores, 'la aprobacion de CODEOWNERS no se exige en %s' % rama,
                   'CODEOWNERS exigido en %s' % rama, 'premium')

    tags, m = traer(fuente, 'tags_protegidos', base + '/protected_tags?per_page=100', list)
    if m:
        inf.anotar('tags-protegidos', E_SD, m)
    elif not tags:
        inf.anotar('tags-protegidos', E_AVISO, 'no hay tags protegidos: si se despliega por tag, hace falta protegerlos')
    else:
        crea = niveles(tags, 'create_access_levels')
        nombres = ', '.join(str(t.get('name')) for t in tags)
        acceso(inf, 'tags-protegidos', crea, no_por_rol(tags, 'create_access_levels'),
               'un Developer puede crear tags protegidos (%s): el tag lanza el pipeline con lo protegido' % nombres,
               'tags protegidos %s; los crean: %s' % (nombres, roles(crea)))

    inf.booleano('pipeline-debe-pasar', proy, 'only_allow_merge_if_pipeline_succeeds', True,
                 'para mergear el pipeline tiene que pasar', 'se puede mergear con el pipeline en rojo')
    inf.booleano('hilos-resueltos', proy, 'only_allow_merge_if_all_discussions_are_resolved', True,
                 'para mergear los hilos tienen que estar resueltos', 'se puede mergear con hilos de revision abiertos')
    inf.booleano('cierre-automatico', proy, 'autoclose_referenced_issues', False, 'el cierre automatico de issues esta apagado',
                 'una palabra de cierre (Closes #N) en un commit o un Merge Request cierra el issue al mergear, por afuera '
                 'de los GATEs (y el ajuste no cubre los issues de otros proyectos)')
    rol_v = proy.get('ci_pipeline_variables_minimum_override_role')
    if rol_v in ('no_one_allowed', 'maintainer', 'owner'):
        inf.anotar('variables-de-pipeline', E_OK, 'pasan variables al pipeline: %s' % rol_v)
    elif rol_v == 'developer':
        inf.anotar('variables-de-pipeline', E_HALL, 'un Developer puede pasarle variables al pipeline (pisan las del YAML): '
                   'va no_one_allowed o maintainer')
    else:
        inf.booleano('variables-de-pipeline', proy, 'restrict_user_defined_variables', True,
                     'variables de pipeline restringidas', 'cualquiera que corra el pipeline le pasa variables')
    inf.booleano('caches-separadas', proy, 'ci_separated_caches', True, 'ramas protegidas y no protegidas no comparten cache',
                 'una rama no protegida puede envenenar la cache que usa la protegida')
    inf.booleano('despliegues-viejos', proy, 'ci_forward_deployment_enabled', True, 'un job de despliegue viejo no pisa a uno nuevo',
                 'un job de despliegue viejo puede correr despues de uno nuevo y volver atras sin querer')
    vis = proy.get('visibility')
    if vis == 'private':
        inf.anotar('forks-en-el-padre', E_OK, 'proyecto privado: los forks son de miembros')
    elif vis in ('internal', 'public'):
        inf.booleano('forks-en-el-padre', proy, 'ci_allow_fork_pipelines_to_run_in_parent_project', False,
                     'los pipelines de forks no corren en el proyecto padre',
                     'proyecto %s: el pipeline de un fork puede correr en el padre, y por la API no hay advertencia' % vis)
    else:
        inf.anotar('forks-en-el-padre', E_SD, 'la respuesta no trae visibility')

    jt, m = traer(fuente, 'job_token_scope', base + '/job_token_scope', dict)
    if m:
        inf.anotar('job-token-lista', E_SD, m + (' (pide rol Maintainer: lo corre una persona)' if '403' in m else ''))
    else:
        inf.booleano('job-token-lista', jt, 'inbound_enabled', True, 'la lista de permitidos del job token esta activa',
                     'cualquier proyecto puede usar su job token contra este: falta la lista de permitidos')
    inf.booleano('job-token-push', proy, 'ci_push_repository_for_job_token_allowed', False,
                 'el job token no puede empujar al repositorio', 'el job token puede empujar al repositorio: un job cambia el codigo')
    dk, m = traer(fuente, 'deploy_keys', base + '/deploy_keys?per_page=100', list)
    if m:
        inf.anotar('deploy-keys-escritura', E_SD, m)
    else:
        n = sum(1 for k in dk if k.get('can_push') is True)
        inf.si('deploy-keys-escritura', n > 0, '%d deploy key(s) con escritura: empujan sin pasar por nadie (por decision '
               'escrita, o se sacan)' % n, '%d deploy key(s), ninguna con escritura' % len(dk))

    yo, m = traer(fuente, 'usuario', 'user', dict)
    if not m and not isinstance(yo.get('id'), int):
        m = 'la respuesta no trae el id del usuario del token'
    if not m:
        mi, m = traer(fuente, 'miembro', base + '/members/all/%d' % yo['id'], dict)
        nivel = mi.get('access_level') if mi else None
        if not m and not isinstance(nivel, int):
            m = 'la respuesta no trae el rol'
    if m:
        inf.anotar('rol-del-token', E_SD, m)
    elif nivel > 30:
        inf.anotar('rol-del-token', E_AVISO, 'el token con que corrio este script tiene rol %s en el proyecto: si es el de la '
                   'IA, pasa de Developer (GATE de GITLAB); si es el de una persona, es lo esperable' % ROL.get(nivel, nivel))
    else:
        inf.anotar('rol-del-token', E_OK, 'el token con que corrio tiene rol %s' % ROL.get(nivel, nivel))

    if inf.da('aprobaciones-requeridas', 'premium'):
        ra, m = traer(fuente, 'reglas_de_aprobacion', base + '/approval_rules?per_page=100', list)
        if m:
            inf.anotar('aprobaciones-requeridas', E_SD, m, 'premium')
        else:
            req = max([r['approvals_required'] for r in ra if isinstance(r.get('approvals_required'), int)] or [0])
            inf.si('aprobaciones-requeridas', req < 1, 'ninguna regla exige una aprobacion: se mergea sin que nadie apruebe',
                   'una regla exige %d aprobacion(es)' % req, 'premium')
    if inf.da('autor-no-aprueba', 'premium'):
        ap, m = traer(fuente, 'aprobaciones', base + '/approvals', dict)
        autor, commit = (ap or {}).get('merge_requests_author_approval'), (ap or {}).get('merge_requests_disable_committers_approval')
        if m or not isinstance(autor, bool) or not isinstance(commit, bool):
            inf.anotar('autor-no-aprueba', E_SD, m or 'la respuesta no trae los ajustes de aprobacion', 'premium')
        else:
            problemas = (['el autor puede aprobar su propio Merge Request'] if autor else []) + \
                        (['quien commiteo puede aprobar'] if not commit else [])
            inf.si('autor-no-aprueba', bool(problemas), '; '.join(problemas), 'ni el autor ni quien commiteo aprueban', 'premium')
    if inf.da('push-rules-secretos', 'premium'):
        pr, m = traer(fuente, 'push_rule', base + '/push_rule', dict, nulo=True)
        if m:
            inf.anotar('push-rules-secretos', E_SD, m, 'premium')
        elif pr is None:
            inf.anotar('push-rules-secretos', E_HALL, 'no hay push rules: el servidor no frena un secreto empujado', 'premium')
        else:
            inf.booleano('push-rules-secretos', pr, 'prevent_secrets', True, 'las push rules rechazan archivos con secretos',
                         'las push rules no rechazan archivos con secretos', 'premium')

    amb, m_amb = traer(fuente, 'ambientes', base + '/environments?per_page=100', list)
    prod = [a['name'] for a in amb or [] if a.get('tier') == 'production' and isinstance(a.get('name'), str)]
    if inf.da('produccion-protegida', 'premium'):
        if m_amb:
            inf.anotar('produccion-protegida', E_SD, m_amb, 'premium')
        elif not prod:
            inf.anotar('produccion-protegida', E_AVISO, 'no hay ningun ambiente de nivel production: si el proyecto despliega '
                       'a produccion, la barrera de la plataforma no esta', 'premium')
        else:
            pe, m = traer(fuente, 'ambientes_protegidos', base + '/protected_environments?per_page=100', list)
            if m:
                inf.anotar('produccion-protegida', E_SD, m, 'premium')
            else:
                def aprobaciones(p):
                    reglas_p = [x.get('required_approvals') for x in p.get('approval_rules') or []]
                    return max([p.get('required_approval_count') or 0] + [x for x in reglas_p if isinstance(x, int)])
                bien = set(p.get('name') for p in pe if aprobaciones(p) >= 1)
                faltan = [n for n in prod if n not in bien]
                inf.si('produccion-protegida', bool(faltan), 'sin proteger o sin la aprobacion de una persona: %s' % ', '.join(faltan),
                       'protegidos y con aprobacion: %s' % ', '.join(prod), 'premium')
    sr = proy.get('shared_runners_enabled')
    if m_amb or not isinstance(sr, bool):
        inf.anotar('runners-de-instancia', E_SD, m_amb or 'la respuesta no trae shared_runners_enabled')
    elif sr and prod:
        inf.anotar('runners-de-instancia', E_AVISO, 'runners de instancia habilitados en un proyecto que despliega a produccion: '
                   'un job con secretos de despliegue puede caer en un runner compartido')
    else:
        inf.anotar('runners-de-instancia', E_OK, 'runners de instancia %s' % ('habilitados, sin ambientes de produccion' if sr else 'apagados'))
    return ''


# ---------------------------------------------------------------- grupo

def modo_grupo(fuente, inf, ruta):
    base = 'groups/' + urllib.parse.quote(ruta, safe='')
    g, motivo = traer(fuente, 'grupo', base, dict)
    if motivo:
        return motivo
    inf.booleano('2fa-del-grupo', g, 'require_two_factor_authentication', True, 'el grupo exige 2FA a sus miembros',
                 'el grupo no exige 2FA a sus miembros (salvo que lo exija la instancia: modo instancia)')
    nivel = g.get('project_creation_level')
    if nivel == 'developer':
        inf.anotar('crear-proyectos', E_HALL, 'un Developer puede crear proyectos en el grupo (la identidad de la IA tambien)')
    elif nivel in ('noone', 'maintainer', 'owner', 'administrator'):
        inf.anotar('crear-proyectos', E_OK, 'crean proyectos: %s' % nivel)
    else:
        inf.anotar('crear-proyectos', E_SD, 'la respuesta no trae project_creation_level')
    d, viejo = g.get('default_branch_protection_defaults'), g.get('default_branch_protection')
    if isinstance(d, dict):
        problemas = (['un Developer empuja directo'] if developer(niveles([d], 'allowed_to_push')) else []) + \
                    (['force push permitido'] if d.get('allow_force_push') is True else []) + \
                    (['un Developer mergea'] if developer(niveles([d], 'allowed_to_merge')) else [])
        inf.si('proteccion-por-defecto', bool(problemas), 'la rama por defecto de los proyectos nuevos nace con: ' + '; '.join(problemas),
               'la rama por defecto de los proyectos nuevos nace protegida')
    elif isinstance(viejo, int):
        inf.si('proteccion-por-defecto', viejo in (0, 1, 3), 'default_branch_protection = %d: en los proyectos nuevos un '
               'Developer empuja o mergea a la rama por defecto' % viejo, 'default_branch_protection = %d' % viejo)
    else:
        inf.anotar('proteccion-por-defecto', E_SD, 'la respuesta no trae la proteccion por defecto de la rama')
    vis = g.get('visibility')
    if vis == 'public':
        inf.anotar('visibilidad', E_AVISO, 'el grupo es publico: un proyecto publico adentro se ve desde internet')
    elif vis in ('private', 'internal'):
        inf.anotar('visibilidad', E_OK, 'el grupo es %s' % vis)
    else:
        inf.anotar('visibilidad', E_SD, 'la respuesta no trae visibility')
    if inf.da('push-rules-de-grupo', 'premium'):
        codigo, pr, _ = fuente.leer('grupo_push_rule', base + '/push_rule')
        if codigo == 404:
            inf.anotar('push-rules-de-grupo', E_HALL, 'el grupo no tiene push rules (la API responde 404 cuando no hay)', 'premium')
        elif codigo != 200:
            inf.anotar('push-rules-de-grupo', E_SD, motivo_http(codigo), 'premium')
        else:
            inf.booleano('push-rules-de-grupo', pr, 'prevent_secrets', True, 'las push rules del grupo rechazan archivos con secretos',
                         'las push rules del grupo no rechazan archivos con secretos', 'premium')
    return ''


# ---------------------------------------------------------------- instancia

def version(texto):
    m = re.match(r'^\s*v?(\d+)\.(\d+)\.(\d+)', str(texto or ''))
    return tuple(int(x) for x in m.groups()) if m else None


def menor(texto):
    m = re.match(r'^\s*(\d+)\.(\d+)\s*$', str(texto or ''))
    return tuple(int(x) for x in m.groups()) if m else None


def leer_versiones(ruta):
    """(datos, motivo). La lista de versiones vigentes la arma una persona desde la fuente oficial; aca no se baja nada."""
    if not ruta:
        return None, 'falta --versiones <archivo> con la lista de versiones vigentes (el script no baja nada de internet)'
    try:
        with open(ruta, 'r', encoding='utf-8') as h:
            d = json.load(h)
    except OSError:
        return None, 'no se pudo leer %s' % ruta
    except ValueError:
        return None, '%s no es un JSON valido' % ruta
    if not isinstance(d, dict):
        return None, '%s no tiene la forma esperada' % ruta
    try:
        fecha = datetime.date.fromisoformat(str(d.get('fecha', ''))[:10])
    except ValueError:
        return None, 'la lista de versiones no dice de que fecha es (clave fecha, aaaa-mm-dd)'
    dias = (datetime.date.today() - fecha).days
    if dias < 0:
        return None, ('la lista de versiones dice ser del %s, una fecha en el futuro: la fecha esta mal y no se sabe de '
                      'cuando es la lista' % fecha.isoformat())
    if dias > MAX_DIAS_VERSIONES:
        return None, ('la lista de versiones es del %s (%d dias): vieja, puede faltarle un parche critico (se acepta hasta '
                      '%d dias)' % (fecha.isoformat(), dias, MAX_DIAS_VERSIONES))
    vigentes = [menor(x) for x in d.get('vigentes') or []]
    if not vigentes or None in vigentes:
        return None, 'la lista no trae "vigentes" (las versiones X.Y que reciben arreglos de seguridad)'
    ultimo = d.get('ultimo_parche') if isinstance(d.get('ultimo_parche'), dict) else {}
    paradas = [menor(x) for x in d.get('paradas') or []] if isinstance(d.get('paradas'), list) else None
    if paradas is not None and None in paradas:
        paradas = None
    return {'fecha': fecha.isoformat(), 'vigentes': vigentes, 'ultimo': ultimo, 'paradas': paradas}, ''


def camino(actual, destino, ultimo, paradas):
    """(pasos, motivo): cada version por la que hay que pasar, en su ultimo parche, sin saltear paradas obligatorias."""
    am = actual[:2]
    if destino < am:
        return None, 'la version pedida (%d.%d) es anterior a la que corre: volver atras es restaurar, no actualizar' % destino
    etapas = sorted(set(p for p in paradas if am < p < destino))
    if am in paradas or am == destino:
        etapas = [am] + etapas          # su propia rama primero, si es parada o es el destino
    if destino != am:
        etapas.append(destino)
    pasos = []
    for e in etapas:
        clave = '%d.%d' % e
        v = version(ultimo.get(clave))
        if v is None:
            return None, 'la lista no trae el ultimo parche de la %s, que es parte del camino: no se inventa' % clave
        if v > actual:
            pasos.append('%d.%d.%d' % v)
    return pasos, ''


def modo_instancia(fuente, inf, fila, versiones, hasta):
    meta, m_meta = traer(fuente, 'metadata', 'metadata', dict)
    actual = version(meta.get('version')) if meta else None
    if not m_meta and actual is None:
        m_meta = 'la respuesta no trae la version'
    de_la_version = ('version-en-ventana', 'ultimo-parche', 'camino-de-actualizacion')
    if m_meta:
        inf.sd(('version-de-la-ficha',) + de_la_version, m_meta)
    else:
        txt = '%d.%d.%d' % actual
        en_ficha = version(fila.get('version'))
        if en_ficha is None:
            inf.anotar('version-de-la-ficha', E_AVISO, 'la ficha no anota la version; la instancia responde %s' % txt)
        elif en_ficha != actual:
            inf.anotar('version-de-la-ficha', E_AVISO, 'la ficha dice %d.%d.%d y la instancia responde %s: hay que '
                       'actualizar la ficha' % (en_ficha + (txt,)))
        else:
            inf.anotar('version-de-la-ficha', E_OK, 'la ficha y la instancia dicen %s' % txt)
        datos, m = leer_versiones(versiones)
        if m:
            inf.sd(de_la_version, m)
        else:
            am = actual[:2]
            vig = ', '.join('%d.%d' % v for v in datos['vigentes'])
            inf.si('version-en-ventana', am not in datos['vigentes'], 'la %d.%d esta fuera de la ventana de mantenimiento (%s): '
                   'no recibe arreglos de seguridad' % (am + (vig,)), 'la %d.%d esta dentro de la ventana (%s)' % (am + (vig,)))
            up = version(datos['ultimo'].get('%d.%d' % am))
            if up is None:
                inf.anotar('ultimo-parche', E_SD, 'la lista no trae el ultimo parche de la %d.%d' % am)
            else:
                inf.si('ultimo-parche', actual < up, 'corre %s y el ultimo parche de su rama es %d.%d.%d' % ((txt,) + up),
                       'esta en el ultimo parche de su rama (%s)' % txt)
            destino = menor(hasta) if hasta else max(datos['vigentes'])
            if destino is None:
                inf.anotar('camino-de-actualizacion', E_SD, '--hasta va como X.Y (por ejemplo 19.5)')
            elif datos['paradas'] is None:
                inf.anotar('camino-de-actualizacion', E_SD, 'la lista no trae "paradas" (las paradas obligatorias)')
            else:
                pasos, m = camino(actual, destino, datos['ultimo'], datos['paradas'])
                if m:
                    inf.anotar('camino-de-actualizacion', E_SD, m)
                else:
                    inf.extra['camino_de_actualizacion'] = pasos
                    inf.anotar('camino-de-actualizacion', E_OK, (
                        'camino: %s -> %s (cada paso en su ultimo parche, con las migraciones en segundo plano terminadas; '
                        'lo ejecuta una persona)' % (txt, ' -> '.join(pasos))) if pasos else
                        'al dia con la %d.%d (%s)' % (destino + (txt,)))
    aj, m = traer(fuente, 'ajustes', 'application/settings', dict)
    ids = ('registro-abierto', '2fa-instancia', 'admin-mode', 'visibilidad-por-defecto', 'vencimiento-de-tokens',
           'registro-viejo-de-runners', 'webhooks-a-la-red-local')
    if m:
        extra = ' (los ajustes de la instancia piden un token de administrador: los corre una persona)' if ('403' in m or '401' in m) else ''
        inf.sd(ids, m + extra)
        return ''
    su, apr = aj.get('signup_enabled'), aj.get('require_admin_approval_after_user_signup')
    if not isinstance(su, bool):
        inf.anotar('registro-abierto', E_SD, 'signup_enabled: la respuesta no lo trae')
    else:
        inf.si('registro-abierto', su and apr is not True, 'el registro de cuentas esta abierto y sin aprobacion de un administrador',
               'registro cerrado' if not su else 'registro abierto, con aprobacion de un administrador')
    inf.booleano('2fa-instancia', aj, 'require_two_factor_authentication', True, 'la instancia exige 2FA a todos',
                 'la instancia no exige 2FA (salvo que el ingreso sea por un proveedor externo que lo exija)')
    inf.booleano('admin-mode', aj, 'admin_mode', True, 'Admin Mode activo: un administrador vuelve a autenticarse para administrar',
                 'sin Admin Mode: una sesion o un token de administrador administra sin volver a autenticarse')
    vis = aj.get('default_project_visibility')
    if vis in ('private', 'internal', 'public'):
        inf.si('visibilidad-por-defecto', vis != 'private', 'los proyectos nuevos nacen %s' % vis, 'los proyectos nuevos nacen privados')
    else:
        inf.anotar('visibilidad-por-defecto', E_SD, 'default_project_visibility: la respuesta no lo trae')
    inf.booleano('vencimiento-de-tokens', aj, 'require_personal_access_token_expiry', True, 'los tokens personales vencen',
                 'se pueden crear tokens personales sin vencimiento')
    inf.booleano('registro-viejo-de-runners', aj, 'allow_runner_registration_token', False,
                 'los runners se registran solo con el flujo nuevo (glrt-)', 'se pueden registrar runners con el token de registro viejo')
    inf.booleano('webhooks-a-la-red-local', aj, 'allow_local_requests_from_web_hooks_and_services', False,
                 'webhooks e integraciones no le piden a la red local',
                 'un webhook o una integracion puede hacerle pedidos a la red interna')
    return ''


# ---------------------------------------------------------------- runner (una copia local de config.toml)

SECRETO_EN_NOMBRE = re.compile(r'(?i)(token|secret|passw|pwd|key|credential|auth)')
EJECUTOR_AVISO = {'shell': 'shell: los jobs corren con el usuario del runner y leen el codigo, el token y las caches de otros '
                           'proyectos; si el runner es compartido, es HALLAZGO',
                  'ssh': 'ssh: en mantenimiento, y expuesto a intermediarios',
                  'docker+machine': 'docker+machine: en desuso'}
CONTENEDORES = ('docker', 'docker-windows', 'docker+machine', 'docker-autoscaler', 'kubernetes')


def modo_runner(ruta, inf):
    if not ruta:
        return 'falta --config <copia local de config.toml> (el token que trae adentro no se muestra)'
    if not os.path.isfile(ruta):
        return 'no existe %s' % ruta
    try:
        import tomllib
    except ImportError:
        return 'leer config.toml pide Python 3.11 o mas (tomllib); este es %d.%d' % sys.version_info[:2]
    try:
        with open(ruta, 'rb') as h:
            conf = tomllib.load(h)
    except (OSError, ValueError) as e:
        return 'no se pudo leer %s como TOML (%s)' % (ruta, type(e).__name__)
    runners = [r for r in conf.get('runners') or [] if isinstance(r, dict)] if isinstance(conf.get('runners'), list) else []
    if not runners:
        return 'el archivo no tiene ningun [[runners]]'
    for i, r in enumerate(runners, 1):
        p = 'runner[%d].' % i                     # por posicion: el name suele ser el nombre real del host
        ej = r.get('executor') if isinstance(r.get('executor'), str) else ''
        docker = r.get('docker') if isinstance(r.get('docker'), dict) else {}
        kube = r.get('kubernetes') if isinstance(r.get('kubernetes'), dict) else {}
        if not ej:
            inf.anotar(p + 'ejecutor', E_SD, 'no declara executor')
        elif ej in EJECUTOR_AVISO:
            inf.anotar(p + 'ejecutor', E_AVISO, EJECUTOR_AVISO[ej])
        else:
            inf.anotar(p + 'ejecutor', E_OK, 'ejecutor %s' % ej)
        inf.si(p + 'privileged', docker.get('privileged') is True or kube.get('privileged') is True,
               'privileged = true: el contenedor tiene todas las capacidades de root del host (para construir imagenes '
               'sin privilegio: BuildKit o Buildah)', 'sin privileged')
        vols = [v for v in docker.get('volumes') or [] if isinstance(v, str)]
        kv = kube.get('volumes') if isinstance(kube.get('volumes'), dict) else {}
        hp = [str(x.get('host_path', '')) for x in kv.get('host_path') or [] if isinstance(x, dict)]
        inf.si(p + 'socket-docker', any('docker.sock' in v for v in vols + hp),
               'el socket de Docker esta montado: un job controla el Docker del host', 'sin el socket de Docker montado')
        if ej in CONTENEDORES:
            sec = kube if ej == 'kubernetes' else docker
            pp = sec.get('pull_policy')
            pps = [pp] if isinstance(pp, str) else [x for x in pp or [] if isinstance(x, str)] if isinstance(pp, list) else []
            if 'if-not-present' in pps:
                inf.anotar(p + 'pull-policy', E_AVISO, 'pull_policy if-not-present: en un runner compartido, un job puede usar '
                           'una imagen privada que otro ya bajo')
            else:
                inf.anotar(p + 'pull-policy', E_OK, 'pull_policy %s' % (', '.join(pps) or 'por defecto'))
            faltan = [k for k in ('allowed_images', 'allowed_pull_policies') if not sec.get(k)]
            if faltan:
                inf.anotar(p + 'listas-permitidas', E_AVISO, 'falta %s: si falta, todo esta permitido' % ' y '.join(faltan))
            else:
                inf.anotar(p + 'listas-permitidas', E_OK, 'imagenes y politicas de descarga limitadas')
        env = [e for e in r.get('environment') or [] if isinstance(e, str) and '=' in e] if isinstance(r.get('environment'), list) else []
        nombres = [e.split('=', 1)[0].strip() for e in env if e.split('=', 1)[1].strip() and SECRETO_EN_NOMBRE.search(e.split('=', 1)[0])]
        inf.si(p + 'secretos-en-environment', bool(nombres), 'variables con nombre de secreto en environment (las ve todo job): %s; '
               'el valor no se muestra' % ', '.join(nombres), 'sin secretos en environment')
        tok = r.get('token') if isinstance(r.get('token'), str) else ''
        if not tok.strip():
            inf.anotar(p + 'token-formato', E_SD, 'no hay token (o esta tapado): no se puede saber su formato')
        elif tok.startswith('glrt-'):
            inf.anotar(p + 'token-formato', E_OK, 'token del flujo nuevo (glrt-)')
        else:
            inf.anotar(p + 'token-formato', E_AVISO, 'el token no empieza con glrt-: es del flujo viejo de registro, o esta tapado')
    return ''


# ---------------------------------------------------------------- texto (antes de escribirlo en GitLab)

def modo_texto(ruta, inf):
    if not ruta:
        return 'falta el archivo con el texto'
    if not os.path.isfile(ruta):
        return 'no existe %s' % ruta
    with open(ruta, 'r', encoding='utf-8', errors='replace', newline='') as h:
        t = h.read().replace('\r\n', '\n')
    if not t.strip():
        return 'el texto esta vacio: no hay nada que mirar'
    c = cierre.cierres(t)
    inf.si('cierre', bool(c), '; '.join('linea %d: "%s" cierra al mergear (va "Related to #N")' % x for x in c[:10]),
           'sin palabras de cierre seguidas de un issue o una tarjeta')
    a = cierre.acciones_rapidas(t)
    inf.si('acciones-rapidas', bool(a), '; '.join('linea %d: %s se ejecutaria al guardar' % x for x in a[:10]),
           'ninguna linea empieza con una accion rapida')
    toks = [(n, nombre) for n, linea in enumerate(t.split('\n'), 1) for nombre, _, _ in secretos.formatos(linea)]
    inf.si('tokens', bool(toks), '; '.join('linea %d: %s (el valor no se muestra; si es real, se revoca: borrarlo no '
                                           'alcanza)' % x for x in toks[:10]), 'sin tokens ni claves con formato conocido')
    duros, blandos = [], []
    for n, linea in enumerate(t.split('\n'), 1):
        for _, real in phi.emails(linea):
            (duros if real else blandos).append('linea %d: un correo de un dominio %s' % (n, 'real' if real else 'de ejemplo'))
        for c in phi.cuits(linea):
            m = re.match(r'(\d{2})-?(\d{8})-?(\d)', c)
            persona = bool(m) and '-' in c and m.group(1) in ('20', '23', '24', '27') and phi.cuit_valido(*m.groups())
            (duros if persona else blandos).append('linea %d: %s' % (n, 'un CUIT o CUIL de persona' if persona else 'un numero con forma de CUIT'))
        for nombre, _ in phi.ambiguos(linea):
            blandos.append('linea %d: posible %s' % (n, nombre))
    if duros:
        inf.anotar('datos-personales', E_HALL, '; '.join(duros[:10]) + ' (va un marcador: <persona>, <documento>)')
    elif blandos:
        inf.anotar('datos-personales', E_AVISO, '; '.join(blandos[:10]) + ' (leerlo: si es un dato real, va un marcador)')
    else:
        inf.anotar('datos-personales', E_OK, 'sin correos, CUIT ni numeros con forma de documento o telefono (heuristica)')
    return ''


# ---------------------------------------------------------------- salida

def estado_final(chequeos):
    est = [c['estado'] for c in chequeos]
    if E_HALL in est:
        return HALLAZGO
    if E_SD in est or E_OK not in est:
        return SIN_DATOS
    return OK


def cerrar(a, inf, destino, motivo, frena=False):
    no_mira = NO_MIRA[a.modo]
    if motivo or inf is None:
        nombre = 'FRENA' if frena else 'SIN DATOS'
        if a.json:
            print(json.dumps({'modo': a.modo, 'estado': nombre, 'motivo': motivo, 'destino': destino, 'chequeos': [],
                              'no_mira': list(no_mira)}, ensure_ascii=True, indent=1))
        else:
            print('AUDITAR GITLAB (%s) -- %s' % (a.modo, nombre))
            print('  %s: %s' % (nombre, motivo))
            print('  Lo que este script NO mira: ' + '; '.join(no_mira) + '.')
        return HALLAZGO if frena else SIN_DATOS
    codigo = estado_final(inf.chequeos)
    nombre = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}[codigo]
    cuenta = dict((e, sum(1 for c in inf.chequeos if c['estado'] == e)) for e in (E_OK, E_HALL, E_SD, E_AVISO, E_PLAN))
    if a.json:
        salida = {'modo': a.modo, 'estado': nombre, 'destino': destino, 'chequeos': inf.chequeos, 'cuenta': cuenta,
                  'no_mira': list(no_mira)}
        if destino is not None:
            salida['barreras_que_el_plan_no_da'] = inf.sin_plan
        salida.update(inf.extra)
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return codigo
    print('AUDITAR GITLAB (%s) -- %s' % (a.modo, nombre))
    if destino is not None:
        print('  Destino: %s  %s  (plan %s, segun la ficha %s)' % (destino['instancia'], destino['ruta'] or '',
                                                                  destino['plan'] or 'SIN DECLARAR', destino['ficha']))
    for c in inf.chequeos:
        print('  %-24s %-32s %s' % (c['estado'], c['id'], c['detalle']))
    print('  Resumen: %d OK, %d HALLAZGO, %d SIN DATOS, %d AVISO%s' % (
        cuenta[E_OK], cuenta[E_HALL], cuenta[E_SD], cuenta[E_AVISO],
        '' if destino is None else '; %d no disponibles en el plan (no cuentan como OK)' % cuenta[E_PLAN]))
    if destino is not None:
        if inf.plan is None:
            print('  Barreras que este plan no da: SIN DATOS (la ficha no declara el plan)')
        elif not inf.sin_plan:
            print('  Barreras que este plan no da: ninguna de las que mira este script')
        else:
            print('  Barreras que este plan no da (y lo que las reemplaza):')
            for s in inf.sin_plan:
                print('    - %s (pide %s): %s' % (s['id'], s['pide'], s['reemplazo']))
    print('  Lo que este script NO mira: ' + '; '.join(no_mira) + '.')
    return codigo


def main():
    ap = argparse.ArgumentParser(description='GitLab en datos duros: proyecto, grupo, instancia, runner o un texto (solo lectura).')
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument('--json', action='store_true')
    destino = argparse.ArgumentParser(add_help=False)
    destino.add_argument('--instancia', default='', help='https://<host>, exacta como en la ficha')
    destino.add_argument('--desde', default='', help='carpeta con respuestas guardadas, en lugar de la API')
    destino.add_argument('--ficha', default='')
    destino.add_argument('--modulo', default='')
    destino.add_argument('--raiz', default=RAIZ)
    sub = ap.add_subparsers(dest='modo')
    for nombre in ('proyecto', 'grupo'):
        sub.add_parser(nombre, parents=[comun, destino]).add_argument('--ruta', default='')
    p = sub.add_parser('instancia', parents=[comun, destino])
    p.add_argument('--versiones', default='', help='JSON con la lista de versiones vigentes (fecha, vigentes, ultimo_parche, paradas)')
    p.add_argument('--hasta', default='', help='version X.Y a la que se quiere llegar (por defecto, la ultima vigente)')
    sub.add_parser('runner', parents=[comun]).add_argument('--config', default='')
    sub.add_parser('texto', parents=[comun]).add_argument('archivo', nargs='?', default='')
    a = ap.parse_args()
    if not a.modo:
        print('SIN DATOS -- falta el modo: proyecto, grupo, instancia, runner o texto.')
        return SIN_DATOS
    if a.modo in ('runner', 'texto'):
        inf = Informe(None)
        return cerrar(a, inf, None, modo_runner(a.config, inf) if a.modo == 'runner' else modo_texto(a.archivo, inf))

    ruta_ficha, motivo = (a.ficha, '') if a.ficha else ubicar_ficha(os.path.abspath(a.raiz), a.modulo)
    if ruta_ficha and not inventario.en_el_cerebro(ruta_ficha, os.path.abspath(a.raiz)):
        return cerrar(a, None, None, 'la ficha %s no esta adentro de %s: una ficha armada en otro lado (borrador/, una '
                                     'carpeta temporal) no autoriza ningun GitLab' % (
                                         ruta_ficha, os.path.join(os.path.abspath(a.raiz), 'cerebro-digital')))
    if not ruta_ficha:
        return cerrar(a, None, None, motivo + '. Sin ficha, ningun GitLab esta autorizado')
    estado, fila, motivo = autorizar(ruta_ficha, a.instancia, getattr(a, 'ruta', ''), a.modo)
    if estado != E_OK:
        return cerrar(a, None, None, motivo, frena=(estado == 'FRENA'))
    plan = inventario.plano(fila['plan'])
    plan = plan if plan in PLANES else None
    dest = {'instancia': fila['instancia'], 'ruta': getattr(a, 'ruta', ''), 'plan': NOMBRE_PLAN.get(plan),
            'ofrecimiento': fila['ofrecimiento'], 'ficha': ruta_ficha}
    if a.modo == 'instancia' and (inventario.plano(fila['ofrecimiento']) == 'gitlab.com' or fila['instancia'] == 'https://gitlab.com'):
        return cerrar(a, None, dest, 'la instancia es GitLab.com: la version y los ajustes los administra GitLab; este modo '
                                     'es para una instancia propia')
    if a.desde:
        if not os.path.isdir(a.desde):
            return cerrar(a, None, dest, 'no existe la carpeta de respuestas %s' % a.desde)
        token = ''
    else:
        token = os.environ.get('GITLAB_TOKEN', '').strip()
        if not token:
            return cerrar(a, None, dest, 'falta la variable de entorno GITLAB_TOKEN (el token no se pasa por argumento): sin '
                                         'token no se pide nada')
    fuente = Fuente(fila['instancia'], a.desde, token)
    inf = Informe(plan)
    if a.modo == 'proyecto':
        motivo = modo_proyecto(fuente, inf, a.ruta)
    elif a.modo == 'grupo':
        motivo = modo_grupo(fuente, inf, a.ruta)
    else:
        motivo = modo_instancia(fuente, inf, fila, a.versiones, a.hasta)
    return cerrar(a, inf, dest, motivo)


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
