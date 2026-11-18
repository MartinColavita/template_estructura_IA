#!/usr/bin/env python3
"""Verificacion estatica del pipeline de un repositorio (GitHub Actions, GitLab CI, Azure Pipelines). SOLO LECTURA.

    python -I bin/verificar-pipeline.py <repo> [--ambientes <ruta> | --modulo <slug>] [--json]
    python -I bin/verificar-pipeline.py <repo> --profundo         (ademas corre zizmor, actionlint y poutine, si estan instalados)
    python -I bin/verificar-pipeline.py <repo> --reporte-zizmor <json> --reporte-actionlint <json> --reporte-poutine <json>
    python -I bin/verificar-pipeline.py <repo> --lint-json <archivo>   (GitLab: la respuesta de CI Lint de la instancia)
    python -I bin/verificar-pipeline.py <repo> --plataforma-confirmada <persona>   (quien confirmo P9 a mano)

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS
  Sin --plataforma-confirmada el total nunca es OK: si el YAML esta bien, sale SIN DATOS ("OK en el YAML; P9 SIN
  DATOS"), porque aprobaciones, ambientes protegidos y reglas de rama viven en la plataforma y no se miraron.

QUE MIRA. Detecta la plataforma (.github/workflows/*.yml, .gitlab-ci.yml, azure-pipelines*.yml en la raiz) y
hace, archivo por archivo, los chequeos de M-048:
  P1  permisos minimos del token (GitHub): permissions arriba o en cada job; sin write-all ni escritura arriba
  P2  dependencias fijadas: acciones y workflows reutilizables por SHA de 40 (o cubiertas por actions.lock);
      include y componentes de GitLab por SHA o version completa, sin ~latest ni remote; repositorios de
      plantillas de Azure por tag o SHA. Una imagen sin digest es AVISO, no HALLAZGO
  P3  pull_request_target o workflow_run con checkout del codigo del PR (GitHub)
  P4  datos del evento que controla un tercero (titulo, cuerpo, rama...) adentro de un script (GitHub)
  P5  credenciales de larga vida de una nube, un secreto escrito en env o variables (el nombre, con el criterio comun de
      auditoria/secretos.py; en un contenedor de servicio de la prueba es AVISO), o un formato conocido de token en
      cualquier linea. Se muestra la huella solo de un valor de 16 caracteres o mas, nunca el valor; toda linea o URL
      del YAML que se imprime pasa antes por el tapado comun, y de un include remote se muestra esquema, host y ruta
  P6  un paso de despliegue sin su ambiente; un ambiente que no figura en la ficha de ambientes
  P7  continue-on-error, allow_failure o continueOnError en tests, cobertura, lint o seguridad
  P8  AVISO: secrets: inherit, checkout que deja la credencial, despliegue sin concurrency o resource_group
  P9  lo que vive en la plataforma (aprobaciones, ambientes protegidos, reglas de rama): SIN DATOS (no se pudo mirar),
      salvo que una persona lo confirme a mano (--plataforma-confirmada). Este script no llama a ninguna API. En
      GitLab lo mide bin/auditar-gitlab.py (no se corre desde aca).
  P10 GitLab: la respuesta de CI Lint de la instancia, si se la pasan (--lint-json): valid en falso, o un include
      remoto o de otro proyecto sin SHA, es HALLAZGO. Sin el archivo es SIN DATOS y no cambia la salida.
Lo propio de GitLab (pedido de gestion-de-gitlab): include remote sin integrity, de proyecto por rama y version
parcial (AVISO); un include en estilo flujo ({ project: ... }) se parte en clave y valor (si no se puede, P2 SIN DATOS);
produccion (deployment_tier: production, o un nombre que empieza con prod, produc, live o prd) sin una regla
if: $CI_COMMIT_REF_PROTECTED == "true", o con when:
manual como unica barrera (P6, HALLAZGO); curl o wget a un shell (P2, HALLAZGO); imagen con variable y pull_policy
if-not-present (P2, AVISO); docker:dind o docker.sock, trigger con strategy: depend o forward de variables,
only/except, sin workflow:rules, release con release-cli (P8, AVISO).
Con --profundo (o con un reporte ya generado) suma el analisis de zizmor y actionlint (GitHub) y de poutine (las
tres): lee su reporte JSON, nunca su codigo de salida. Si no se pide, esa parte es SIN DATOS (no se pidio) y no
cambia la salida; si se pide y la herramienta no esta, es SIN DATOS y la salida es 2.

LIMITE DECLARADO. La biblioteca estandar no lee YAML: este script lee por lineas y por sangria. No expande anclas
ni alias (avisa si los ve), no lee varios documentos en un archivo, no resuelve include, extends ni plantillas, ni
lo que se arma en la corrida. Para eso esta el analisis profundo.

POR QUE EXISTE. La IA escribe pipelines; lo que el YAML aporta a la seguridad (permisos, fijado, ambientes, lo
que frena) tiene que poder auditarse siempre igual, y sacarlo es edicion destructiva. El modelo leyendo YAML se
saltea una linea; esto no.

QUE NO HACE. No modifica nada, no corre el pipeline, no se conecta a ninguna plataforma, no baja nada. A una
herramienta externa nunca le pasa una opcion que cambie algo (LISTA_NEGRA). Solo biblioteca estandar. ASCII puro.
"""

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from auditoria import secretos as criterio  # noqa: E402  el criterio de secretos comun (y el tapado antes de imprimir)
MIN_HUELLA = 16            # de un valor mas corto no se imprime la huella: con un diccionario se revierte
NOMBRES = (('P1', 'Permisos minimos del token'),
           ('P2', 'Dependencias fijadas (acciones, include, plantillas, imagenes)'),
           ('P3', 'Disparador privilegiado con el codigo del PR'),
           ('P4', 'Datos del evento adentro de un script'),
           ('P5', 'Secretos de larga vida o escritos en el YAML'),
           ('P6', 'Despliegue con su ambiente, y el ambiente en la ficha'),
           ('P7', 'Lo que tiene que frenar, frena'),
           ('P8', 'Credencial persistente, secretos heredados, concurrencia'),
           ('P9', 'Lo que vive en la plataforma (aprobaciones, ambientes protegidos, reglas de rama)'))
NO_MIRA = ('el YAML se lee por lineas y por sangria: no se expanden anclas ni alias, no se leen varios documentos en un '
           'archivo, no se resuelven include, extends ni plantillas, ni lo que se arma en la corrida',
           'si una accion o una imagen fijada es segura (fijar no es auditar)',
           'la logica del build y si cada etapa frena de verdad al fallar',
           'la inyeccion por macros $(...) de Azure ni la de variables de GitLab (las mira poutine con --profundo)',
           'un pipeline con otro nombre o en otra carpeta que las de la plataforma',
           'aprobaciones, chequeos, ambientes protegidos, reglas de rama y credenciales de la plataforma (P9)')

NOMBRE_P10 = 'CI Lint de la instancia (GitLab), leido de un archivo'
SHA40 = re.compile(r'^[0-9a-f]{40}$')
VERSION_COMPLETA = re.compile(r'^v?\d+\.\d+\.\d+$')
PARCIAL = re.compile(r'^v?\d+(\.\d+)?$')
# Produccion por el comienzo del nombre (Produccion, production-ar, PRD, live), ademas de deployment_tier: production.
PRODUCCION = re.compile(r'(?i)^(prod|production|produccion|produc|live|prd)')
# Limitarse a una ref protegida es una regla "if" que la exige en verdadero; nombrarla en un echo o compararla con
# "false" no limita nada.
REF_PROTEGIDA = re.compile(r'''\$\{?CI_COMMIT_REF_PROTECTED\}?\s*==\s*["']?true["']?''')
BAJA_Y_CORRE = re.compile(r'\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba|z|da)?sh\b')
CLAVE = re.compile(r'''^(?P<k>"[^"]*"|'[^']*'|[^\s"'#\-\[\]{}|>][^:]*?)\s*:(?:\s+(?P<v>.*)|\s*$)''')
BLOQUE = re.compile(r'^[|>][-+0-9]*$')
ANCLA = re.compile(r'^[&*][\w-]+(\s|$)')   # una ancla o un alias va al principio del valor, no adentro de un script
CRUDAS = ('script', 'before_script', 'after_script')   # GitLab: cada item es una linea de shell, no una clave
LARGA_VIDA = re.compile(r'\b(AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|AZURE_CREDENTIALS|AZURE_CLIENT_SECRET|ARM_CLIENT_SECRET|'
                        r'GOOGLE_CREDENTIALS|GCP_SA_KEY|GCP_CREDENTIALS|GOOGLE_APPLICATION_CREDENTIALS_JSON)\b')
NOMBRE_SECRETO = re.compile(r'(?i)(password|passwd|pwd|secret|token|api[_-]?key|apikey|private[_-]?key|access[_-]?key)')
NO_ES_SECRETO = re.compile(r'(?i)(_url|_uri|_path|_file|_name|_id|_endpoint|_type|_header|_user|_username|_ttl)$')
DESPLIEGUE_USES = re.compile(r'(?i)^(azure/(login|webapps-deploy|functions-action|k8s-deploy|aks-set-context|arm-deploy|'
                             r'container-apps-deploy-action|static-web-apps-deploy)|aws-actions/(configure-aws-credentials|'
                             r'amazon-ecs-deploy-task-definition)|google-github-actions/(auth|deploy-[\w-]+|get-gke-credentials))@')
DESPLIEGUE_RUN = re.compile(r'(?i)\b(kubectl\s+(apply|rollout|set\s+image|replace|patch|delete|create)|helm\s+(upgrade|install|'
                            r'rollback|uninstall)|az\s+(webapp|functionapp|containerapp|deployment|aks|staticwebapp|spring)\b|'
                            r'terraform\s+apply|tofu\s+apply|pulumi\s+up|aws\s+(ecs\s+update-service|deploy\b|lambda\s+'
                            r'update-function-code|cloudformation\s+deploy)|gcloud\s+(run|app|functions)\s+deploy|ansible-playbook|'
                            r'cf\s+push|flyctl\s+deploy|serverless\s+deploy)')
DESPLIEGUE_TAREAS = re.compile(r'(?i)^(AzureWebApp|AzureRmWebAppDeployment|AzureFunctionApp|AzureContainerApps|KubernetesManifest|'
                               r'Kubernetes|HelmDeploy|AzureResourceManagerTemplateDeployment|AzureResourceGroupDeployment|'
                               r'SqlAzureDacpacDeployment|IISWebAppDeploymentOnMachineGroup|AzureStaticWebApp)@')
CRITICOS = re.compile(r'(?i)(test|pytest|jest|junit|mocha|vitest|coverage|cobertura|lint|eslint|ruff|flake8|checkstyle|sonar|'
                      r'security|seguridad|sast|dast|scan|audit|trivy|grype|snyk|semgrep|codeql|bandit|gitleaks|zizmor|'
                      r'dependency-check)')
RIESGOSOS = ('body', 'default_branch', 'email', 'head_ref', 'label', 'message', 'name', 'page_name', 'ref', 'title', 'head_branch')
PR_HEAD = re.compile(r'github\.event\.pull_request\.head\.|github\.head_ref|github\.event\.workflow_run\.head_|refs/pull/|'
                     r'github\.event\.pull_request\.merge_commit_sha')
RESERVADAS_GITLAB = ('stages', 'variables', 'image', 'services', 'include', 'default', 'workflow', 'before_script',
                     'after_script', 'cache', 'spec', 'types')
SCRIPTS_AZURE = ('script', 'bash', 'pwsh', 'powershell', 'inlineScript')
HERRAMIENTAS = ('zizmor', 'actionlint', 'poutine')
LISTA_NEGRA = ('--fix', '-fix', 'analyze_org', 'analyze_repo', '--token', '--gh-token', '--github-token', '--write', '-w',
               '--scm-base-url')


# ---------------------------------------------------------------------------------------------------------
# YAML por lineas
# ---------------------------------------------------------------------------------------------------------

def quitar_comentario(s):
    q = None
    for k, c in enumerate(s):
        if q:
            if c == q:
                q = None
        elif c in '"\'':
            q = c
        elif c == '#' and (k == 0 or s[k - 1] in ' \t'):
            return s[:k].rstrip()
    return s.rstrip()


def sin_comillas(v):
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'' else v


def ultima_clave(ruta):
    for x in reversed(ruta):
        if not isinstance(x, tuple):
            return x
    return None


def leer_yaml(texto):
    """[{linea, clave, valor, ruta, bloque, item}] de cada clave o item de lista. La ruta lleva las claves de arriba
    y, por cada item de lista, una tupla ('-', n). bloque: las lineas de un texto | o >, con su numero."""
    nodos, pila, cont, bloque = [], [], 0, None
    for n, raw in enumerate(texto.replace('\r\n', '\n').replace('\r', '\n').split('\n'), 1):
        raw = raw.replace('\t', ' ')
        if bloque is not None:
            if not raw.strip() or (len(raw) - len(raw.lstrip(' '))) > bloque[1]:
                if raw.strip():
                    bloque[0]['bloque'].append((n, raw.strip()))
                continue
            bloque = None
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        if s in ('---', '...'):
            pila = []
            continue
        ind = len(raw) - len(raw.lstrip(' '))
        resto = raw[ind:]
        es_item = False
        while resto == '-' or resto.startswith('- '):
            while pila and (pila[-1][0] > ind or (pila[-1][0] == ind and isinstance(pila[-1][1], tuple))):
                pila.pop()
            cont += 1
            pila.append((ind, ('-', cont)))
            despues = resto[1:]
            ind = ind + 1 + (len(despues) - len(despues.lstrip(' ')))
            resto = despues.lstrip(' ')
            es_item = True
        if not resto:
            continue
        padre = tuple(x for _, x in pila)
        crudo = es_item and ultima_clave(padre) in CRUDAS
        m = None if crudo else CLAVE.match(resto)
        if m:
            clave = sin_comillas(m.group('k'))
            valor = quitar_comentario(m.group('v') or '').strip()
            while pila and pila[-1][0] >= ind:
                pila.pop()
            pila.append((ind, clave))
            nodo = {'linea': n, 'clave': clave, 'valor': sin_comillas(valor), 'ruta': tuple(x for _, x in pila),
                    'bloque': [], 'item': es_item}
            nodos.append(nodo)
            if BLOQUE.match(valor):
                nodo['valor'] = ''
                bloque = (nodo, ind)
        elif es_item:
            valor = quitar_comentario(resto).strip()
            nodo = {'linea': n, 'clave': None, 'valor': sin_comillas(valor), 'ruta': padre, 'bloque': [], 'item': True}
            nodos.append(nodo)
            if BLOQUE.match(valor):
                nodo['valor'] = ''
                bloque = (nodo, pila[-1][0])
        elif nodos:
            nodos[-1]['valor'] = (nodos[-1]['valor'] + ' ' + quitar_comentario(resto).strip()).strip()
    return nodos


def hijo(nodos, prefijo, clave):
    r = tuple(prefijo) + (clave,)
    for x in nodos:
        if x['ruta'] == r:
            return x
    return None


def valor(nodos, prefijo, clave):
    x = hijo(nodos, prefijo, clave)
    return x['valor'] if x else ''


def bajo(nodos, prefijo):
    k = len(prefijo)
    return [x for x in nodos if x['ruta'][:k] == tuple(prefijo)]


def items(nodos, prefijo):
    """Las rutas de los items de la lista que cuelga de prefijo, en orden."""
    k, vistos = len(prefijo), []
    for x in nodos:
        if len(x['ruta']) > k and x['ruta'][:k] == tuple(prefijo) and isinstance(x['ruta'][k], tuple) and x['ruta'][k] not in vistos:
            vistos.append(x['ruta'][k])
    return [tuple(prefijo) + (t,) for t in vistos]


def escalar(nodos, ruta):
    for x in nodos:
        if x['ruta'] == ruta and x['clave'] is None:
            return x
    return None


def lineas_de(x):
    """[(linea, texto)] de un nodo: su valor y su bloque."""
    res = [(x['linea'], x['valor'])] if x['valor'] else []
    return res + list(x['bloque'])


def texto(nodos):
    return '\n'.join(t for x in nodos for _, t in lineas_de(x))


# ---------------------------------------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------------------------------------

class Resultado(object):
    def __init__(self):
        self.c = dict((i, {'h': [], 'a': [], 's': [], 'mirado': False, 'na': []}) for i, _ in NOMBRES)
        self.avisos, self.sin_datos = [], []

    def mirado(self, i):
        self.c[i]['mirado'] = True

    def na(self, i, motivo):
        if motivo not in self.c[i]['na']:
            self.c[i]['na'].append(motivo)

    def poner(self, i, tipo, archivo, linea, que):
        t = '%s:%d: %s' % (archivo, linea, criterio.tapar(que))   # lo que sale del YAML se tapa antes de imprimirlo
        if t not in self.c[i][tipo]:
            self.c[i][tipo].append(t)

    def estado(self, i):
        c = self.c[i]
        return ('HALLAZGO' if c['h'] else 'SIN DATOS' if c['s'] else 'AVISO' if c['a'] else 'OK' if c['mirado'] else 'NO APLICA')


def imagen(R, rel, linea, img):
    if '@sha256:' in img:
        return
    R.poner('P2', 'a', rel, linea, '%s: imagen sin digest (@sha256:...): la etiqueta se puede mover' % img)


def secretos(R, rel, nodos):
    """P5, comun a las tres: nombres de credenciales de larga vida, y secretos escritos en env o variables."""
    R.mirado('P5')
    for x in nodos:
        for linea, t in [(x['linea'], x['clave'] or '')] + lineas_de(x):
            m = LARGA_VIDA.search(quitar_comentario(t))
            if m:
                R.poner('P5', 'h', rel, linea, '%s: credencial de larga vida de una nube; va con identidad federada (OIDC)' % m.group(1))
    for x in nodos:
        r = x['ruta']
        nombre, val = None, None
        if x['clave'] and len(r) >= 2 and r[-2] in ('env', 'variables'):
            nombre, val = x['clave'], x['valor'] or valor(nodos, r, 'value')
        elif x['clave'] == 'name' and len(r) >= 3 and isinstance(r[-2], tuple) and r[-3] == 'variables':
            nombre, val = x['valor'], valor(nodos, r[:-1], 'value')
        if not nombre or not (NOMBRE_SECRETO.search(nombre) or criterio.sensible(nombre)) or NO_ES_SECRETO.search(nombre):
            continue
        v = (val or '').strip()
        if (not v or v.startswith('$') or re.match(r'(?i)^(true|false|yes|no|on|off|null|~|\d+(\.\d+)?)$', v)
                or re.match(r'^https?://[^@\s]*$', v)):
            continue
        huella = ' (huella %s)' % hashlib.sha256(v.encode('utf-8')).hexdigest()[:12] if len(v) >= MIN_HUELLA else ''
        if 'services' in [c for c in r if not isinstance(c, tuple)]:
            # el contenedor de servicio de una prueba (una base de datos descartable) suele llevar una clave de juguete
            R.poner('P5', 'a', rel, x['linea'], '%s: clave escrita en un contenedor de servicio%s: si es una base descartable '
                                                'de la prueba, esta bien; si no, va como secreto de la plataforma' % (nombre, huella))
            continue
        R.poner('P5', 'h', rel, x['linea'], '%s: secreto escrito en el YAML%s: va como secreto de la plataforma' % (nombre, huella))
    # un formato conocido (token, clave privada, URL con usuario y clave) en cualquier linea, aun en un script
    for x in nodos:
        for linea, t in [(x['linea'], x['clave'] or '')] + lineas_de(x):
            for que, ini, fin in criterio.formatos(t):
                if '$' not in t[ini:fin] and '<' not in t[ini:fin]:
                    R.poner('P5', 'h', rel, linea, '%s escrito en el YAML: va como secreto de la plataforma (si es real, se '
                                                   'revoca: borrarlo no alcanza)' % que)


class Ambientes(object):
    """La ficha de ambientes, cargada la primera vez que hace falta (con el lector de gate-despliegue.py)."""
    def __init__(self, ruta, modulo):
        self.ruta, self.modulo, self.lista, self.motivo, self.cargada = ruta, modulo, None, '', False

    def nombres(self):
        if not self.cargada:
            self.cargada = True
            try:
                spec = importlib.util.spec_from_file_location('gate_despliegue', os.path.join(AQUI, 'gate-despliegue.py'))
                gate = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gate)
                ruta, motivo = (self.ruta, '') if self.ruta else gate.ubicar_ambientes(RAIZ, self.modulo)
                lista, _, motivo2 = gate.cargar_ambientes(ruta) if ruta else (None, [], motivo)
                self.lista = None if lista is None else [a['nombre'] for a in lista]
                self.motivo = motivo2 or motivo
            except Exception as e:  # noqa: BLE001
                self.motivo = 'no se pudo leer la ficha de ambientes: %s' % e
        return self.lista


def ambiente(R, AMB, rel, linea, nombre):
    nombre = nombre.strip()
    if not nombre:
        return
    if '$' in nombre:
        R.poner('P6', 'a', rel, linea, 'el ambiente "%s" se arma en la corrida: no se puede comprobar contra la ficha' % nombre)
        return
    lista = AMB.nombres()
    if lista is None:
        R.poner('P6', 's', rel, linea, 'no se puede comprobar el ambiente "%s": %s' % (nombre, AMB.motivo))
    elif nombre not in lista:
        R.poner('P6', 'h', rel, linea, 'el ambiente "%s" no figura en la ficha de ambientes: en algunas plataformas un nombre '
                                       'nuevo crea un ambiente sin aprobaciones' % nombre)


def nombre_ambiente(nodos, prefijo, nodo):
    if nodo['valor']:
        m = re.search(r'name\s*:\s*([^,}]+)', nodo['valor']) if nodo['valor'].startswith('{') else None
        return sin_comillas(m.group(1)) if m else nodo['valor']
    return valor(nodos, tuple(prefijo) + ('environment',), 'name')


# ---------------------------------------------------------------------------------------------------------
# GitHub Actions
# ---------------------------------------------------------------------------------------------------------

def leer_lock(repo):
    """{workflow: set(dependencias)} cubiertas por .github/workflows/actions.lock (con su commit), o {}."""
    ruta = os.path.join(repo, '.github', 'workflows', 'actions.lock')
    if not os.path.isfile(ruta):
        return {}
    with open(ruta, 'rb') as h:
        nodos = leer_yaml(h.read().decode('utf-8', 'replace'))
    fijas = set(x['ruta'][1] for x in nodos if len(x['ruta']) == 3 and x['ruta'][0] == 'dependencies' and x['clave'] == 'commit'
                and re.match(r'^(sha1-)?[0-9a-f]{40}$', x['valor']))
    res = {}
    for x in nodos:
        if len(x['ruta']) == 3 and x['ruta'][0] == 'workflows' and x['clave'] is None and x['valor'] in fijas:
            res.setdefault(x['ruta'][1], set()).add(x['valor'])
    return res


def github(R, AMB, rel, nodos, lock):
    arriba = dict((x['clave'], x) for x in nodos if len(x['ruta']) == 1)
    jobs = []
    for x in nodos:
        if len(x['ruta']) == 2 and x['ruta'][0] == 'jobs' and x['clave'] and x['ruta'][1] not in jobs:
            jobs.append(x['ruta'][1])
    if not jobs:
        R.sin_datos.append('%s: no tiene jobs que se puedan leer' % rel)
        return
    for i in ('P1', 'P2', 'P3', 'P4', 'P6', 'P7', 'P8'):
        R.mirado(i)
    secretos(R, rel, nodos)
    # P1
    perm = arriba.get('permissions')
    sin = [J for J in jobs if hijo(nodos, ('jobs', J), 'permissions') is None]
    if perm is None and sin:
        R.poner('P1', 'h', rel, arriba['jobs']['linea'], 'sin permissions arriba, y %s no declara(n) los suyos: el token toma los '
                'permisos por defecto del repositorio' % ', '.join("'%s'" % J for J in sin))
    for p in [perm] + [hijo(nodos, ('jobs', J), 'permissions') for J in jobs]:
        if p is None:
            continue
        if p['valor'].lower() == 'write-all':
            R.poner('P1', 'h', rel, p['linea'], 'permissions: write-all')
        elif p['valor'].lower() == 'read-all':
            R.poner('P1', 'a', rel, p['linea'], 'permissions: read-all (lectura de todo): alcanza con lo que se usa')
    for x in nodos:
        if len(x['ruta']) == 2 and x['ruta'][0] == 'permissions' and x['valor'].lower() == 'write':
            R.poner('P1', 'h', rel, x['linea'], 'escritura a nivel workflow (%s: write): va solo en el job que la necesita' % x['clave'])
    # disparadores
    on = arriba.get('on') or arriba.get('true')
    disparadores = set(re.findall(r'[\w-]+', on['valor'])) if on else set()
    # los hijos directos de on: claves (push:) o items de una lista (- push)
    disparadores |= set(x['clave'] or x['valor'] for x in nodos if len(x['ruta']) == 2 and x['ruta'][0] in ('on', 'true'))
    privilegiados = sorted(disparadores & {'pull_request_target', 'workflow_run'})
    concurrencia_arriba = 'concurrency' in arriba
    checkout_pr = False
    for J in jobs:
        pj = ('jobs', J)
        linea_job = hijo(nodos, ('jobs',), J)['linea']
        pasos = items(nodos, pj + ('steps',))
        despliega = ''
        uses_job = hijo(nodos, pj, 'uses')
        for u in [uses_job] + [hijo(nodos, p, 'uses') for p in pasos]:
            if u is None:
                continue
            v = u['valor']
            if v.startswith('./') or v.startswith('.\\'):
                continue
            if v.startswith('docker://'):
                imagen(R, rel, u['linea'], v[len('docker://'):])
            elif '@' not in v:
                R.poner('P2', 'h', rel, u['linea'], '%s: sin version' % v)
            elif not SHA40.match(v.rsplit('@', 1)[1]) and not (u is not uses_job and v in lock.get(rel, set())):
                R.poner('P2', 'h', rel, u['linea'], '%s: referencia movible (etiqueta o rama); va fijada por SHA completo%s' % (
                    v, '' if u is uses_job else ' o en actions.lock'))
            if DESPLIEGUE_USES.match(v):
                despliega = despliega or v.split('@')[0]
        cont = hijo(nodos, pj, 'container')
        if cont is not None:
            img = cont['valor'] or valor(nodos, pj + ('container',), 'image')
            if img:
                imagen(R, rel, cont['linea'], img)
        for x in nodos:
            if x['ruta'][:3] == pj + ('services',) and len(x['ruta']) == 5 and x['clave'] == 'image':
                imagen(R, rel, x['linea'], x['valor'])
        for p in pasos:
            uses = valor(nodos, p, 'uses')
            run = hijo(nodos, p, 'run')
            nombre = valor(nodos, p, 'name') or uses or (run['valor'][:40] if run else '')
            fuentes = [run] if run else []
            if uses.startswith('actions/github-script@'):
                s = hijo(nodos, p + ('with',), 'script')
                fuentes += [s] if s else []
            for f in fuentes:
                for linea, t in lineas_de(f):
                    for expr in re.findall(r'\$\{\{(.*?)\}\}', t):
                        if riesgoso(expr):
                            R.poner('P4', 'h', rel, linea, '${{%s}} en un script: ese texto lo escribe quien abre el PR o el issue; '
                                                          'va por una variable de entorno' % expr)
            if run:
                t = texto([run])
                m = DESPLIEGUE_RUN.search(t)
                despliega = despliega or (m.group(0) if m else '')
                if re.search(r'gh\s+pr\s+checkout|git\s+fetch[^\n]*pull/', t):
                    checkout_pr = checkout_pr or (privilegiados and (rel, run['linea']))
            if uses.startswith('actions/checkout@'):
                ref = valor(nodos, p + ('with',), 'ref')
                if privilegiados and PR_HEAD.search(ref):
                    checkout_pr = True
                    R.poner('P3', 'h', rel, hijo(nodos, p, 'uses')['linea'], '%s con checkout del codigo del PR (ref: %s): corre '
                            'codigo ajeno con permisos y secretos' % ('/'.join(privilegiados), ref))
                if valor(nodos, p + ('with',), 'persist-credentials').lower() != 'false':
                    R.poner('P8', 'a', rel, hijo(nodos, p, 'uses')['linea'], 'checkout sin persist-credentials: false: el token '
                                                                             'queda guardado en el disco del runner')
            coe = hijo(nodos, p, 'continue-on-error')
            if coe is not None:
                no_frena(R, rel, coe, 'paso', nombre, ' '.join([nombre, uses, texto([run]) if run else '']))
        coe = hijo(nodos, pj, 'continue-on-error')
        if coe is not None:
            no_frena(R, rel, coe, 'job', J, J + ' ' + texto(bajo(nodos, pj)))
        sec = hijo(nodos, pj, 'secrets')
        if sec is not None and sec['valor'] == 'inherit':
            R.poner('P8', 'a', rel, sec['linea'], "job '%s' con secrets: inherit: recibe todos los secretos, no los que usa" % J)
        env = hijo(nodos, pj, 'environment')
        if despliega and env is None:
            R.poner('P6', 'h', rel, linea_job, "job '%s' despliega (%s) sin environment: no hay aprobacion ni ambiente donde "
                                              "colgarla" % (J, despliega))
        if env is not None:
            ambiente(R, AMB, rel, env['linea'], nombre_ambiente(nodos, pj, env))
        if despliega and not concurrencia_arriba and hijo(nodos, pj, 'concurrency') is None:
            R.poner('P8', 'a', rel, linea_job, "job '%s' despliega sin concurrency: dos corridas pueden desplegar a la vez" % J)
    if privilegiados and not checkout_pr:
        R.poner('P3', 'a', rel, on['linea'] if on else 1, 'disparador privilegiado (%s) sin checkout visible del PR: revisarlo a '
                'mano o con zizmor (--profundo)' % ', '.join(privilegiados))


def riesgoso(expr):
    if 'github.head_ref' in expr:
        return True
    for m in re.finditer(r'github\.event((?:\.[A-Za-z_][\w-]*|\[[^\]]*\]|\.\*)+)', expr):
        partes = re.findall(r'[A-Za-z_][\w-]*', m.group(1))
        if partes and partes[-1] in RIESGOSOS:
            return True
    return False


def no_frena(R, rel, nodo, que, nombre, contexto):
    v = nodo['valor'].lower()
    hijos_af = v == '' and nodo['clave'] == 'allow_failure'
    if v == 'true' or hijos_af:
        if CRITICOS.search(contexto):
            R.poner('P7', 'h', rel, nodo['linea'], "%s '%s' con %s: %s: si el build no lo exige, no existe" % (
                que, nombre, nodo['clave'], v or 'exit_codes'))
        else:
            R.poner('P7', 'a', rel, nodo['linea'], "%s '%s' con %s: %s: no frena si falla" % (que, nombre, nodo['clave'], v or 'exit_codes'))
    elif '$' in v:
        R.poner('P7', 'a', rel, nodo['linea'], "%s '%s' con %s segun una expresion: revisar si puede dejar de frenar" % (
            que, nombre, nodo['clave']))


# ---------------------------------------------------------------------------------------------------------
# GitLab CI
# ---------------------------------------------------------------------------------------------------------

def flujo(t):
    """Los elementos de primer nivel de una lista o un mapa en estilo flujo de YAML ([a, b] o {k: v, ...}), o None si
    no cierra (comillas o corchetes sin cerrar)."""
    t = t.strip()
    if len(t) < 2 or t[0] not in '[{' or t[-1] != {'[': ']', '{': '}'}[t[0]]:
        return None
    partes, actual, prof, q = [], '', 0, None
    for c in t[1:-1]:
        if q:
            q = None if c == q else q
        elif c in '"\'':
            q = c
        elif c in '[{':
            prof += 1
        elif c in ']}':
            prof -= 1
            if prof < 0:
                return None
        elif c == ',' and prof == 0:
            partes.append(actual.strip())
            actual = ''
            continue
        actual += c
    if q or prof:
        return None
    return partes + ([actual.strip()] if actual.strip() else [])


def mapa_flujo(t):
    """{clave: valor} de un mapa en estilo flujo ({ project: 'g/p', file: '/a.yml' }), o None si no se puede partir."""
    partes = flujo(t) if t.strip().startswith('{') else None
    if partes is None:
        return None
    d = {}
    for p in partes:
        k, sep, v = p.partition(':')
        if not sep or not k.strip():
            return None
        d[sin_comillas(k)] = sin_comillas(v)
    return d


def url_visible(url):
    """Esquema, host y ruta de una URL: sin usuario, clave ni query (ahi suelen viajar los tokens)."""
    try:
        p = urllib.parse.urlsplit(url.strip())
        if p.scheme and p.hostname:
            return '%s://%s%s%s' % (p.scheme, p.hostname, ':%d' % p.port if p.port else '', p.path)
    except ValueError:
        pass
    return criterio.tapar(url.split('?', 1)[0])


def gitlab(R, AMB, rel, nodos):
    for i in ('P2', 'P6', 'P7', 'P8'):
        R.mirado(i)
    R.na('P1', 'GitLab no declara los permisos del token en el YAML: su alcance se configura en el proyecto (P9)')
    R.na('P3', 'el disparador privilegiado con el codigo del PR es de GitHub')
    R.na('P4', 'en GitLab el shell expande las variables (no se pega texto en el script); lo profundo, con poutine')
    arriba = dict((x['clave'], x) for x in nodos if len(x['ruta']) == 1)
    # include
    inc = arriba.get('include')
    entradas = []
    def de_flujo(linea, v):
        """Una entrada de include escrita en estilo flujo: se parte en clave y valor; si no se puede, P2 SIN DATOS."""
        if not v.startswith(('{', '[')):
            entradas.append((linea, {'str': sin_comillas(v)}))
            return
        partes = flujo(v) if v.startswith('[') else [v]
        for p in partes or [None]:
            d = None if p is None else (mapa_flujo(p) if p.startswith('{') else {'str': sin_comillas(p)})
            if d is None:
                R.poner('P2', 's', rel, linea, 'un include en estilo flujo que no se pudo partir (%s): no se sabe que trae' % v[:80])
            else:
                entradas.append((linea, d))
    if inc is not None:
        if inc['valor']:
            de_flujo(inc['linea'], inc['valor'].strip())
        for it in items(nodos, ('include',)):
            esc = escalar(nodos, it)
            if esc is not None:
                de_flujo(esc['linea'], esc['valor'].strip())
            else:
                hs = [x for x in nodos if len(x['ruta']) == len(it) + 1 and x['ruta'][:len(it)] == it]
                if hs:
                    entradas.append((hs[0]['linea'], dict((x['clave'], x['valor']) for x in hs)))
        directos = [x for x in nodos if len(x['ruta']) == 2 and x['ruta'][0] == 'include' and x['clave']]
        if directos:
            entradas.append((directos[0]['linea'], dict((x['clave'], x['valor']) for x in directos)))
    for linea, d in entradas:
        s = d.get('str', '')
        if s.startswith('http') or 'remote' in d:
            url = url_visible(s or d['remote'])
            if not d.get('integrity'):
                R.poner('P2', 'h', rel, linea, 'include remote %s sin integrity: se baja lo que haya en esa URL en cada corrida' % url)
        elif 'project' in d:
            ref = d.get('ref', '')
            if not ref:
                R.poner('P2', 'h', rel, linea, 'include del proyecto %s sin ref: trae lo que haya en su rama por defecto' % d['project'])
            elif SHA40.match(ref) or VERSION_COMPLETA.match(ref):
                pass
            elif PARCIAL.match(ref):
                R.poner('P2', 'a', rel, linea, 'include del proyecto %s con ref %s: version parcial, resuelve a la ultima que '
                                               'coincida' % (d['project'], ref))
            else:
                R.poner('P2', 'h', rel, linea, 'include del proyecto %s con ref %s: una rama se mueve; va por SHA o por una '
                                               'version completa' % (d['project'], ref))
        elif 'component' in d:
            ver = d['component'].rsplit('@', 1)[1] if '@' in d['component'] else ''
            if ver == '~latest' or not ver:
                R.poner('P2', 'h', rel, linea, 'componente %s: ~latest (o sin version) trae cambios que rompen' % d['component'])
            elif SHA40.match(ver) or VERSION_COMPLETA.match(ver):
                pass
            elif PARCIAL.match(ver):
                R.poner('P2', 'a', rel, linea, 'componente %s: version parcial, resuelve a la ultima que coincida' % d['component'])
            else:
                R.poner('P2', 'h', rel, linea, 'componente %s: una rama se mueve; va por SHA o por una version completa' % d['component'])
    # imagenes y servicios
    for x in nodos:
        r = x['ruta']
        es_imagen = x['clave'] == 'image' and (len(r) == 1 or len(r) == 2)
        es_nombre = x['clave'] == 'name' and len(r) >= 2 and r[-2] == 'image'
        es_servicio = (x['clave'] is None and len(r) >= 2 and isinstance(r[-1], tuple) and r[-2] == 'services') or \
                      (x['clave'] == 'name' and len(r) >= 3 and isinstance(r[-2], tuple) and r[-3] == 'services')
        if (es_imagen and x['valor']) or es_nombre or es_servicio:
            if '$' in x['valor']:
                R.poner('P2', 'a', rel, x['linea'], 'imagen con una variable en el nombre (%s): no se sabe cual corre' % x['valor'])
            else:
                imagen(R, rel, x['linea'], x['valor'])
        if es_servicio and 'dind' in x['valor']:
            R.poner('P8', 'a', rel, x['linea'], 'servicio %s (Docker adentro de Docker): pide un runner privilegiado' % x['valor'])
        if (x['clave'] == 'pull_policy' or (x['clave'] is None and ultima_clave(r) == 'pull_policy')) and 'if-not-present' in x['valor']:
            R.poner('P2', 'a', rel, x['linea'], 'pull_policy: if-not-present: el runner puede usar una imagen vieja que ya tenia')
        for linea, t in lineas_de(x):
            if 'docker.sock' in t:
                R.poner('P8', 'a', rel, linea, 'usa el socket de Docker (docker.sock): pide un runner privilegiado (es como darle la maquina)')
            m = BAJA_Y_CORRE.search(t)
            if m:
                cmd = re.sub(r'\?\S*', '?<...>', re.sub(r'://[^/@\s]+@', '://<credencial>@', m.group(0)))
                R.poner('P2', 'h', rel, linea, 'baja y ejecuta un script sin fijar (%s): corre lo que haya en esa URL' % cmd[:100])
    secretos(R, rel, nodos)
    if 'workflow' not in arriba or hijo(nodos, ('workflow',), 'rules') is None:
        R.poner('P8', 'a', rel, 1, 'sin workflow:rules: el pipeline corre en cada evento (ramas, tags y merge requests) y se puede duplicar')
    # jobs
    jobs = [k for k, x in arriba.items() if k not in RESERVADAS_GITLAB and not k.startswith('.')
            and any(len(y['ruta']) > 1 and y['ruta'][0] == k for y in nodos)]
    for J in jobs:
        pj = (J,)
        lj = arriba[J]['linea']
        sub = bajo(nodos, pj)
        guion = texto([x for x in sub if any(c in CRUDAS for c in x['ruta'] if not isinstance(c, tuple))])
        env = hijo(nodos, pj, 'environment')
        m = DESPLIEGUE_RUN.search(guion)
        if m and env is None:
            R.poner('P6', 'h', rel, lj, "job '%s' despliega (%s) sin environment" % (J, m.group(0)))
        if env is not None:
            nombre = nombre_ambiente(nodos, pj, env)
            ambiente(R, AMB, rel, env['linea'], nombre)
            if hijo(nodos, pj, 'resource_group') is None:
                R.poner('P8', 'a', rel, lj, "job '%s' despliega sin resource_group: dos despliegues pueden pisarse" % J)
            tier = valor(nodos, pj + ('environment',), 'deployment_tier')
            protegida = any(x['clave'] == 'if' and REF_PROTEGIDA.search(x['valor']) for x in sub)
            if (tier == 'production' or PRODUCCION.match(nombre)) and not protegida:
                manual = any(x['clave'] == 'when' and x['valor'] == 'manual' for x in sub)
                R.poner('P6', 'h', rel, lj, "job '%s' despliega a produccion (%s) %s: la barrera va en la plataforma (ambiente protegido "
                        'con aprobacion) y el job se limita a una ref protegida (rules: if: $CI_COMMIT_REF_PROTECTED == "true")' % (
                            J, nombre or tier, 'y su unica barrera es when: manual' if manual else 'sin limitarse a una ref protegida'))
        af = hijo(nodos, pj, 'allow_failure')
        if af is not None:
            no_frena(R, rel, af, 'job', J, ' '.join([J, valor(nodos, pj, 'stage'), guion]))
        for clave in ('only', 'except'):
            x = hijo(nodos, pj, clave)
            if x is not None:
                R.poner('P8', 'a', rel, x['linea'], "job '%s' usa %s: se reemplaza por rules" % (J, clave))
        if valor(nodos, pj + ('trigger',), 'strategy') == 'depend':
            R.poner('P8', 'a', rel, lj, "job '%s' con trigger y strategy: depend: su resultado depende de un pipeline que este script no "
                                        'mira' % J)
        if valor(nodos, pj + ('trigger', 'forward'), 'pipeline_variables') == 'true':
            R.poner('P8', 'a', rel, lj, "job '%s' pasa sus variables al pipeline de abajo (forward: pipeline_variables: true)" % J)
        img = valor(nodos, pj, 'image') or valor(nodos, pj + ('image',), 'name')
        if hijo(nodos, pj, 'release') is not None and 'release-cli' in img:
            R.poner('P8', 'a', rel, lj, "job '%s' publica (release) con la imagen de release-cli: revisar en la documentacion de "
                                        'GitLab si sigue siendo la herramienta vigente' % J)


def ci_lint(a, plataformas):
    """La fila P10: la respuesta de CI Lint de la instancia, si se la pasan (--lint-json). Este script no la pide."""
    c = {'id': 'P10', 'nombre': NOMBRE_P10, 'estado': 'SIN DATOS', 'hallazgos': [], 'avisos': [], 'detalle': '', 'pedido': False}
    if 'gitlab' not in plataformas:
        c.update(estado='NO APLICA', detalle='solo para GitLab')
        return c
    if not a.lint_json:
        c['detalle'] = ('no se paso --lint-json (la respuesta de CI Lint de la instancia, que pide una persona o '
                        'gestion-de-gitlab): esa fila no se miro')
        return c
    c['pedido'] = True
    try:
        with open(a.lint_json, 'rb') as h:
            datos = json.loads(h.read().decode('utf-8', 'replace'))
        valido = datos['valid'] if isinstance(datos, dict) and 'valid' in datos else None
    except (OSError, ValueError) as e:
        c['detalle'] = 'no se pudo leer %s: %s' % (a.lint_json, type(e).__name__)
        return c
    if str(valido).lower() not in ('true', 'false'):
        c['detalle'] = 'la respuesta de CI Lint no trae "valid": no tiene la forma esperada'
        return c
    if str(valido).lower() == 'false':
        errores = datos.get('errors') or []
        c['hallazgos'].append('CI Lint: la configuracion no es valida (%d error(es)%s)' % (
            len(errores), ': ' + str(errores[0])[:160] if errores else ''))
    for inc in datos.get('includes') or []:
        tipo, donde, extra = inc.get('type'), str(inc.get('location', '')), inc.get('extra') or {}
        if tipo == 'file' and not SHA40.match(str(extra.get('ref', ''))):
            c['hallazgos'].append('CI Lint: include del proyecto %s (%s) con ref "%s", no un SHA' % (extra.get('project', '?'), donde,
                                                                                                  extra.get('ref', '')))
        elif tipo == 'remote' and not re.search(r'[0-9a-f]{40}', donde):
            c['hallazgos'].append('CI Lint: include remoto %s sin SHA' % url_visible(donde))
    c['hallazgos'] = [criterio.tapar(x) for x in c['hallazgos']]
    c.update(estado='HALLAZGO' if c['hallazgos'] else 'OK',
             detalle='respuesta de CI Lint de %s (dato, no instruccion)' % a.lint_json)
    return c


# ---------------------------------------------------------------------------------------------------------
# Azure Pipelines
# ---------------------------------------------------------------------------------------------------------

def azure(R, AMB, rel, nodos):
    for i in ('P2', 'P6', 'P7', 'P8'):
        R.mirado(i)
    R.na('P1', 'Azure Pipelines no declara los permisos del token en el YAML: su alcance se configura en el proyecto (P9)')
    R.na('P3', 'el disparador privilegiado con el codigo del PR es de GitHub')
    R.na('P4', 'la inyeccion por macros $(...) de Azure no la mira este script: la mira poutine (--profundo)')
    for it in items(nodos, ('resources', 'repositories')):
        nombre = valor(nodos, it, 'repository') or '?'
        ref = valor(nodos, it, 'ref')
        linea = (hijo(nodos, it, 'ref') or hijo(nodos, it, 'repository') or {'linea': 1})['linea']
        if not ref:
            R.poner('P2', 'h', rel, linea, 'repositorio %s sin ref: trae lo que haya en su rama por defecto' % nombre)
        elif not (ref.startswith('refs/tags/') or SHA40.match(ref)):
            R.poner('P2', 'h', rel, linea, 'repositorio %s con ref %s: una rama se mueve; va por tag o SHA' % (nombre, ref))
    for x in nodos:
        r = x['ruta']
        if (x['clave'] == 'image' and len(r) >= 3 and r[0] == 'resources' and r[1] == 'containers') or \
                (x['clave'] == 'container' and x['valor'] and re.search(r'[:/]', x['valor'])):
            imagen(R, rel, x['linea'], x['valor'])
        if x['clave'] == 'persistCredentials' and x['valor'].lower() == 'true':
            R.poner('P8', 'a', rel, x['linea'], 'checkout con persistCredentials: true: el token queda en el disco del agente')
    secretos(R, rel, nodos)
    jobs = [(x['ruta'][:-1], x['clave'], x['valor'], x['linea']) for x in nodos if x['clave'] in ('job', 'deployment') and x['item']]
    if not jobs and any(len(x['ruta']) == 1 and x['clave'] == 'steps' for x in nodos):
        jobs = [((), 'job', '(raiz)', 1)]
    for pj, tipo, J, linea in jobs:
        sub = bajo(nodos, pj)
        guion = texto([x for x in sub if x['clave'] in SCRIPTS_AZURE])
        tareas = [x['valor'] for x in sub if x['clave'] == 'task']
        env = hijo(nodos, pj, 'environment')
        if tipo == 'deployment' and env is None:
            R.poner('P6', 'h', rel, linea, "deployment '%s' sin environment: no hay aprobacion ni ambiente donde colgarla" % J)
        if tipo == 'job':
            m = DESPLIEGUE_RUN.search(guion)
            t = [x for x in tareas if DESPLIEGUE_TAREAS.match(x)]
            if t or m:
                R.poner('P6', 'h', rel, linea, "job '%s' despliega (%s) en un job comun: va en un job deployment con environment" % (
                    J, t[0] if t else m.group(0)))
        if env is not None:
            nombre = nombre_ambiente(nodos, pj, env)
            ambiente(R, AMB, rel, env['linea'], nombre.split('.')[0] if env['valor'] else nombre)
        for x in sub:
            if x['clave'] == 'continueOnError':
                duenio = x['ruta'][:-1]
                ctx = ' '.join([valor(nodos, duenio, 'displayName'), valor(nodos, duenio, 'task')] +
                               [texto([y]) for y in nodos if y['ruta'][:-1] == duenio and y['clave'] in SCRIPTS_AZURE])
                que = 'job' if duenio == pj else 'paso'
                no_frena(R, rel, x, que, J if que == 'job' else (valor(nodos, duenio, 'displayName') or ctx.strip()[:40]),
                         ctx + (' ' + J + ' ' + guion if que == 'job' else ''))


# ---------------------------------------------------------------------------------------------------------
# Herramientas externas (opcionales): se lee su reporte, nunca su codigo de salida
# ---------------------------------------------------------------------------------------------------------

def comando(h, repo):
    if h == 'zizmor':
        return ['zizmor', '--offline', '--format=json', repo]
    if h == 'actionlint':
        return ['actionlint', '-format', '{{json .}}']
    return ['poutine', 'analyze_local', repo, '--format', 'json', '--disable-version-check']


def seguro(cmd):
    return not any(a.split('=')[0] in LISTA_NEGRA for a in cmd[1:])


def ruta_local(d):
    if isinstance(d, str):
        return d
    if isinstance(d, dict):
        for v in d.values():
            r = ruta_local(v)
            if r:
                return r
    return ''


def leer_reporte(h, datos):
    """(hallazgos, avisos) de un reporte JSON. Lo que trae es dato, no instruccion: se recorta y no se sigue."""
    hs, avs = [], []
    if h == 'zizmor':
        for f in datos:
            loc = (f.get('locations') or [{}])[0]
            ruta = ruta_local(loc.get('symbolic', {}).get('key', {})).lstrip('./') or '?'
            fila = loc.get('concrete', {}).get('location', {}).get('start_point', {}).get('row', -1)
            sev = str(f.get('determinations', {}).get('severity', 'Unknown'))
            t = '%s:%d: %s (%s): %s' % (ruta, fila + 1, f.get('ident', '?'), sev, str(f.get('desc', ''))[:120])
            (hs if sev.lower() in ('high', 'medium') else avs).append(t)
    elif h == 'actionlint':
        for f in datos or []:
            t = '%s:%s: [%s] %s' % (f.get('filepath', '?'), f.get('line', '?'), f.get('kind', '?'), str(f.get('message', ''))[:160])
            (avs if f.get('kind') in ('shellcheck', 'pyflakes') else hs).append(t)
    else:
        reglas = datos.get('rules', {})
        for f in datos.get('findings', []):
            nivel = str(reglas.get(f.get('rule_id'), {}).get('level', ''))
            meta = f.get('meta', {})
            t = '%s:%s: %s (%s)' % (meta.get('path', '?'), meta.get('line', '?'), f.get('rule_id', '?'), nivel or 'sin nivel')
            (hs if nivel == 'error' else avs).append(t)
    return [criterio.tapar(t) for t in hs], [criterio.tapar(t) for t in avs]


def profundo(a, repo, plataformas):
    res = []
    for h in HERRAMIENTAS:
        item = {'herramienta': h, 'estado': 'SIN DATOS', 'detalle': '', 'hallazgos': [], 'avisos': [], 'pedido': False}
        res.append(item)
        archivo = getattr(a, 'reporte_' + h)
        if h != 'poutine' and 'github' not in plataformas:
            item.update(estado='NO APLICA', detalle='solo mira GitHub Actions')
            continue
        if not archivo and not a.profundo:
            item['detalle'] = 'no se pidio (--profundo o --reporte-%s): esa parte no se miro' % h
            continue
        item['pedido'] = True
        if archivo:
            try:
                with open(archivo, 'rb') as f:
                    crudo = f.read().decode('utf-8', 'replace')
            except OSError as e:
                item['detalle'] = 'no se pudo leer el reporte %s: %s' % (archivo, e)
                continue
            origen = 'reporte %s' % archivo
        else:
            if shutil.which(h) is None:
                item['detalle'] = '%s no esta instalada en esta maquina: esa parte es SIN DATOS, no OK' % h
                continue
            cmd = comando(h, repo)
            if not seguro(cmd):
                item['detalle'] = 'el comando lleva una opcion de la lista negra: no se corre'
                continue
            r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=repo, timeout=600)
            crudo = r.stdout
            origen = 'corrida de %s' % h
            if not crudo.strip():
                item['detalle'] = '%s no devolvio reporte (%s)' % (h, (r.stderr.strip().splitlines() or ['sin mensaje'])[0][:160])
                continue
        if not crudo.strip():
            item['detalle'] = 'el %s esta vacio: un reporte vacio no es "cero hallazgos"' % origen
            continue
        try:
            datos = json.loads(crudo)
            hs, avs = leer_reporte(h, datos)
        except (ValueError, AttributeError, TypeError) as e:
            item['detalle'] = 'el %s no tiene la forma esperada: %s' % (origen, type(e).__name__)
            continue
        item.update(hallazgos=hs, avisos=avs, estado='HALLAZGO' if hs else 'AVISO' if avs else 'OK',
                    detalle='%s: %d hallazgo(s), %d aviso(s)' % (origen, len(hs), len(avs)))
    return res


# ---------------------------------------------------------------------------------------------------------

def encontrar(repo):
    pl = {}
    wf = sorted(glob.glob(os.path.join(repo, '.github', 'workflows', '*.yml')) + glob.glob(os.path.join(repo, '.github', 'workflows', '*.yaml')))
    if wf:
        pl['github'] = wf
    if os.path.isfile(os.path.join(repo, '.gitlab-ci.yml')):
        pl['gitlab'] = [os.path.join(repo, '.gitlab-ci.yml')]
    az = sorted(glob.glob(os.path.join(repo, 'azure-pipelines*.yml')) + glob.glob(os.path.join(repo, 'azure-pipelines*.yaml')))
    if az:
        pl['azure'] = az
    return pl


def main():
    ap = argparse.ArgumentParser(description='Verificacion estatica del pipeline de un repositorio (solo lectura).')
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--ambientes', default='', help='ficha de ambientes (por defecto, la del unico modulo de cerebro-digital/)')
    ap.add_argument('--modulo', default='')
    ap.add_argument('--profundo', action='store_true', help='correr zizmor, actionlint y poutine si estan instalados')
    for h in HERRAMIENTAS:
        ap.add_argument('--reporte-' + h, default='', help='un reporte JSON de %s ya generado' % h)
    ap.add_argument('--lint-json', default='', help='GitLab: la respuesta de CI Lint de la instancia, guardada en un archivo')
    ap.add_argument('--plataforma-confirmada', default='', metavar='PERSONA',
                    help='quien confirmo a mano, en la plataforma, aprobaciones, ambientes protegidos y reglas de rama (P9)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    confirmada = re.sub(r'\s+', ' ', a.plataforma_confirmada).strip()[:80].encode('ascii', 'replace').decode('ascii')
    repo = os.path.abspath(a.repo)
    if not os.path.isdir(repo):
        print('SIN DATOS -- %s no existe o no es una carpeta.' % repo)
        return SIN_DATOS
    plataformas = encontrar(repo)
    if not plataformas:
        print('SIN DATOS -- no hay ningun pipeline en %s (.github/workflows/*.yml, .gitlab-ci.yml, azure-pipelines*.yml): '
              'no hay nada que verificar.' % repo)
        return SIN_DATOS
    R, AMB = Resultado(), Ambientes(a.ambientes, a.modulo)
    lock = leer_lock(repo)
    for pl, archivos in plataformas.items():
        for ruta in archivos:
            rel = os.path.relpath(ruta, repo).replace(os.sep, '/')
            try:
                with open(ruta, 'rb') as h:
                    nodos = leer_yaml(h.read().decode('utf-8', 'replace'))
            except OSError as e:
                R.sin_datos.append('%s: no se pudo leer (%s)' % (rel, e))
                continue
            if not nodos:
                R.sin_datos.append('%s: esta vacio o no tiene claves que se puedan leer' % rel)
                continue
            if any(x['clave'] == '<<' or (ANCLA.match(x['valor']) and not (x['clave'] is None and ultima_clave(x['ruta']) in CRUDAS))
                   for x in nodos):
                R.avisos.append('%s: usa anclas o alias de YAML (&, *, <<): lo que llega por un alias no se mira' % rel)
            {'github': lambda: github(R, AMB, rel, nodos, lock), 'gitlab': lambda: gitlab(R, AMB, rel, nodos),
             'azure': lambda: azure(R, AMB, rel, nodos)}[pl]()
    chequeos = []
    for i, nombre in NOMBRES:
        c = R.c[i]
        if i == 'P9' and confirmada:
            chequeos.append({'id': i, 'nombre': nombre, 'estado': 'OK', 'hallazgos': [], 'avisos': [],
                             'detalle': 'este script no lo miro: lo confirmo a mano %s en la plataforma (--plataforma-confirmada)'
                                        % confirmada})
            continue
        if i == 'P9':
            chequeos.append({'id': i, 'nombre': nombre, 'estado': 'SIN DATOS', 'hallazgos': [], 'avisos': [],
                             'detalle': 'SIN DATOS (no se pudo mirar): vive en la plataforma y este script no llama a ninguna API; '
                                        'se mira a mano en la plataforma' + (
                                            '. En GitLab lo mide python -I bin/auditar-gitlab.py proyecto --ruta <grupo>/<proyecto> '
                                            '(este script no lo corre)' if 'gitlab' in plataformas else '')})
            continue
        est = R.estado(i)
        detalle = '; '.join(c['na']) if est == 'NO APLICA' else '; '.join(c['s'] + ['no aplica en parte: ' + x for x in c['na']])
        chequeos.append({'id': i, 'nombre': nombre, 'estado': est, 'hallazgos': c['h'], 'avisos': c['a'], 'sin_datos': c['s'],
                         'detalle': detalle})
    lint = ci_lint(a, plataformas)
    chequeos.append(lint)
    prof = profundo(a, repo, plataformas)
    estados = [c['estado'] for c in chequeos if c['id'] not in ('P9', 'P10')]
    if 'HALLAZGO' in estados or lint['estado'] == 'HALLAZGO' or any(p['estado'] == 'HALLAZGO' for p in prof):
        estado = 'HALLAZGO'
    elif (R.sin_datos or 'SIN DATOS' in estados or (lint['pedido'] and lint['estado'] == 'SIN DATOS')
          or any(p['pedido'] and p['estado'] == 'SIN DATOS' for p in prof)):
        estado = 'SIN DATOS'
    else:
        estado = 'OK'
    # lo que vive en la plataforma (P9) no se miro: sin una persona que lo confirme, el total no puede ser OK
    estado_yaml = estado
    if estado == 'OK' and not confirmada:
        estado = 'SIN DATOS'
    rels = dict((pl, [os.path.relpath(r, repo).replace(os.sep, '/') for r in ars]) for pl, ars in plataformas.items())
    if a.json:
        print(json.dumps({'estado': estado, 'estado_yaml': estado_yaml, 'plataforma_confirmada': confirmada or None,
                          'repo': repo, 'plataformas': rels, 'chequeos': chequeos, 'profundo': prof,
                          'archivos_sin_datos': R.sin_datos, 'avisos': R.avisos, 'no_mira': list(NO_MIRA)},
                         ensure_ascii=True, indent=1))
    else:
        nombres_pl = {'github': 'GitHub Actions', 'gitlab': 'GitLab CI', 'azure': 'Azure Pipelines'}
        print('VERIFICAR PIPELINE -- %s%s  [%s: %s]' % (
            estado, ' (OK en el YAML; P9 SIN DATOS: lo que vive en la plataforma se confirma a mano, --plataforma-confirmada)'
            if estado_yaml == 'OK' and estado != 'OK' else '',
            repo, ', '.join('%s (%d)' % (nombres_pl[p], len(v)) for p, v in rels.items())))
        for c in chequeos:
            print('  %-3s %-62s: %s%s' % (c['id'], c['nombre'], c['estado'], ('  -- ' + c['detalle']) if c['detalle'] else ''))
            for t in c['hallazgos']:
                print('      HALLAZGO: ' + t)
            for t in c['avisos']:
                print('      aviso: ' + t)
        print('  Analisis profundo (herramientas externas):')
        for p in prof:
            print('    %-10s: %-9s  %s' % (p['herramienta'], p['estado'], p['detalle']))
            for t in p['hallazgos']:
                print('      HALLAZGO: ' + t)
            for t in p['avisos'][:20]:
                print('      aviso: ' + t)
        for t in R.sin_datos:
            print('  SIN DATOS: ' + t)
        for t in R.avisos:
            print('  aviso: ' + t)
        print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return {'OK': OK, 'HALLAZGO': HALLAZGO}.get(estado, SIN_DATOS)


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
