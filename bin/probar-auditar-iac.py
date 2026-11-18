#!/usr/bin/env python3
"""Prueba de bin/auditar-iac.py sobre repositorios de mentira que arma esta prueba (Terraform, Bicep, Dockerfile,
Compose y Kubernetes). Se corre:  python -B bin/probar-auditar-iac.py   -> OK o FALLA, con el detalle de cada caso.
No necesita ninguna herramienta de infraestructura instalada ni red; usa git para armar los repositorios.
Los valores que parecen secretos se arman por partes: este archivo no tiene que parecer una filtracion."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'auditar-iac.py')
ESPERADOS = []
TMP = tempfile.mkdtemp(prefix='probar-iac-')
CONTADOR = [0]

CS = 'client_' + 'secret'
V1 = 'valor-de-prueba-' + '4711'                    # un "secreto" de mentira: nunca tiene que aparecer en la salida
AKIA = 'AKIA' + 'IOSFODNN7' + 'EJEMPLO'           # formato de clave de acceso de un proveedor, armado por partes
LLAVE = '-----BEGIN ' + 'PRIVATE KEY-----'
SHA = '0123456789abcdef' * 2 + '01234567'
DIGEST = 'sha256:' + '0' * 64


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def sh(cwd, *cmd):
    return subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')


def correr(*args, **kw):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=kw.get('env'))
    return r.returncode, r.stdout + r.stderr


def auditar(raiz, *extra, **kw):
    rc, out = correr('--repo', raiz, '--json', *extra, **kw)
    try:
        d = json.loads(out)
    except ValueError:
        d = {}
    return rc, out, d


def regla(d, rid):
    for r in d.get('reglas', []):
        if r.get('id') == rid:
            return r.get('estado'), r.get('cuenta')
    return None, None


def hall(d, rid):
    return [h for h in d.get('hallazgos', []) if h.get('regla') == rid]


def herramienta(d, nombre):
    for h in d.get('herramientas', []):
        if h.get('nombre') == nombre:
            return h
    return {}


def armar(archivos, git=True, forzar=(), despues=None):
    CONTADOR[0] += 1
    raiz = os.path.join(TMP, 'repo%02d' % CONTADOR[0])
    os.makedirs(raiz)

    def escribir(rel, contenido):
        ruta = os.path.join(raiz, *rel.split('/'))
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, 'w', encoding='utf-8', newline='\n') as h:
            h.write(contenido)

    for rel, contenido in archivos.items():
        if contenido is not None:
            escribir(rel, contenido)
    if git:
        sh(raiz, 'git', 'init', '-q')
        sh(raiz, 'git', 'add', '-A')
        for f in forzar:
            sh(raiz, 'git', 'add', '-f', f)
    for rel, contenido in (despues or {}).items():
        escribir(rel, contenido)
    return raiz


def con(base, **cambios):
    """Una copia de base con cambios: la clave es la ruta con '__' en lugar de '/' y '_P_' en lugar de '.'; None borra."""
    d = dict(base)
    for k, v in cambios.items():
        d[k.replace('__', '/').replace('_P_', '.')] = v
    return d


BACKEND = 'terraform {\n  backend "s3" {\n    bucket = "%s"\n    key    = "%s"\n  }\n}\n'
MAIN = '''terraform {
  required_version = ">= 1.6"
  required_providers {
    ejemplo = {
      source  = "hashicorp/ejemplo"
      version = "~> 5.0"
    }
  }
}

provider "ejemplo" {
  region = var.region
  # ''' + CS + ''' = "valor-comentado-123"
}

module "red" {
  source = "../../modules/red"
  nombre = "red-${var.ambiente}"
  clave  = var.db_password
}

module "comunitario" {
  source  = "ejemplo-org/vpc/ejemplo"
  version = "5.1.2"
}

module "de_git" {
  source = "git::https://git.example.com/infra/modulo.git?ref=''' + SHA + '''"
}
'''
VARIABLES = '''variable "region" {
  type        = string
  description = "Region donde se crean los recursos"
}

variable "ambiente" {
  type        = string
  description = "Nombre del ambiente"
  validation {
    condition     = contains(["dev", "prod"], var.ambiente)
    error_message = "El ambiente tiene que ser dev o prod."
  }
}

variable "db_password" {
  type        = string
  description = "Clave de la base: entra por el pipeline, sin valor por defecto"
  sensitive   = true
}
'''
OUTPUTS = 'output "red_id" {\n  description = "Identificador de la red"\n  value       = module.red.id\n}\n'
MOD_VERSIONES = '''terraform {
  required_version = ">= 1.6"
  required_providers {
    ejemplo = {
      source                = "hashicorp/ejemplo"
      version               = ">= 5.0"
      configuration_aliases = [ejemplo.secundario]
    }
    legado = "~> 2.0"
  }
}
'''
MOD_MAIN = '''resource "ejemplo_red" "this" {
  nombre          = var.nombre
  provider        = ejemplo.secundario
  descripcion     = "la red #1 // no es un comentario"
  password        = var.clave
  password_length = 16
  secret_name     = "db-clave"
  etiquetas = {
    entorno = var.nombre
  }
}

resource "ejemplo_db" "principal" {
  nombre   = "db-${var.nombre}"
  password = "${var.clave}"
  lifecycle {
    prevent_destroy = true
  }
}
'''
MOD_VARIABLES = '''variable "nombre" {
  type        = string
  description = "Nombre de la red"
}

variable "clave" {
  type        = string
  description = "Clave de la base"
  sensitive   = true
}
'''
MOD_OUTPUTS = 'output "id" {\n  description = "Identificador"\n  value       = ejemplo_red.this.id\n}\n'
DOCKERFILE = '''# syntax=docker/dockerfile:1
ARG BASE=node:20.11-alpine
FROM --platform=$BUILDPLATFORM ${BASE} AS build
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM registry.local:5000/base/runtime:1.4.2@''' + DIGEST + ''' AS base
USER app

FROM base AS final
COPY --from=build /app/dist /srv
ENV PASSWORD_FILE=/run/secrets/db \\
    LOG_LEVEL=info
CMD ["node", "/srv/index.js"]
'''
COMPOSE = '''services:
  web:
    build: ./app
    image: miapp
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - LOG_LEVEL=info
    secrets:
      - db_password
  db:
    image: postgres:16.2
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: app   # no es una clave
secrets:
  db_password:
    file: ./db_password.txt
'''
K8S = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      containers:
        - name: web
          image: registry.local:5000/web:1.0.3
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db
                  key: password
            - name: LOG_LEVEL
              value: info
---
apiVersion: v1
kind: Secret
metadata:
  name: db
type: Opaque
stringData:
  password: ENC[AES256_GCM,data:abc,iv:def,tag:ghi,type:str]
sops:
  version: 3.8.1
'''
BICEP = '''@secure()
@description('Clave del administrador: entra por el pipeline')
param adminPassword string

param secretName string = 'clave-db'
param location string = resourceGroup().location

resource cuenta 'Ejemplo.Storage/cuentas@2024-01-01' = {
  name: 'cuenta${uniqueString(resourceGroup().id)}'
  properties: {
    adminPassword: adminPassword
    secretName: secretName
  }
}

@description('Cadena de conexion de la cuenta')
@secure()
output connectionString string = 'cuenta=${cuenta.name}'
output secretName string = secretName
'''
BASE = {
    '.gitignore': '.terraform/\n*.tfstate\n*.tfstate.*\n*.tfplan\n',
    'envs/dev/backend.tf': BACKEND % ('estado-ejemplo', 'dev/terraform.tfstate'),
    'envs/dev/main.tf': MAIN, 'envs/dev/variables.tf': VARIABLES, 'envs/dev/outputs.tf': OUTPUTS,
    'envs/dev/terraform.tfvars': 'region   = "zona-1"\nambiente = "dev"\n# la clave de la base entra por el pipeline\n',
    'envs/dev/.terraform.lock.hcl': '# lock de proveedores\n',
    'envs/dev/.terraform/providers/ejemplo/binario': 'binario descargado por init\n',
    'envs/dev/terraform.tfstate': '{"version": 4}\n',
    'envs/prod/backend.tf': BACKEND % ('estado-ejemplo', 'prod/terraform.tfstate'),
    'envs/prod/main.tf': MAIN, 'envs/prod/variables.tf': VARIABLES, 'envs/prod/outputs.tf': OUTPUTS,
    'envs/prod/.terraform.lock.hcl': '# lock de proveedores\n',
    'modules/red/versions.tf': MOD_VERSIONES, 'modules/red/main.tf': MOD_MAIN,
    'modules/red/variables.tf': MOD_VARIABLES, 'modules/red/outputs.tf': MOD_OUTPUTS,
    'app/Dockerfile': DOCKERFILE, 'app/.dockerignore': 'node_modules\n.git\n',
    'compose.yaml': COMPOSE, 'k8s/app.yaml': K8S, 'infra/main.bicep': BICEP,
    'README.md': 'repositorio de prueba\n',
}


def reportar(nombre, contenido):
    ruta = os.path.join(TMP, nombre)
    with open(ruta, 'w', encoding='utf-8') as h:
        h.write(contenido if isinstance(contenido, str) else json.dumps(contenido))
    return ruta


FALSO_PY = '''import json, os, sys
args = sys.argv[1:]
with open(os.environ["FALSO_REGISTRO"], "a") as h:
    h.write(json.dumps({"herramienta": os.environ.get("FALSO_NOMBRE", ""), "args": args, "cwd": os.getcwd()}) + "\\n")
if args[:1] == ["version"]:
    print(json.dumps({"Version": os.environ.get("FALSO_VERSION", "0.58.0")}))
elif "--version" in args or "-v" in args:
    print("Version: " + os.environ.get("FALSO_VERSION", "0.58.0"))
else:
    sys.stdout.write(open(os.environ["FALSO_REPORTE_" + os.environ["FALSO_NOMBRE"].upper()]).read())
'''


def falsos(*nombres):
    """(carpeta, env): herramientas de mentira en el PATH que anotan argumentos y carpeta, y devuelven un reporte."""
    carpeta = os.path.join(TMP, 'falsos')
    os.makedirs(carpeta, exist_ok=True)
    py = os.path.join(carpeta, 'falso.py')
    with open(py, 'w', encoding='utf-8') as h:
        h.write(FALSO_PY)
    for n in nombres:
        if os.name == 'nt':
            with open(os.path.join(carpeta, n + '.cmd'), 'w') as h:
                h.write('@set FALSO_NOMBRE=%s\r\n@"%s" "%s" %%*\r\n' % (n, sys.executable, py))
        else:
            ruta = os.path.join(carpeta, n)
            with open(ruta, 'w') as h:
                h.write('#!/bin/sh\nFALSO_NOMBRE=%s exec "%s" "%s" "$@"\n' % (n, sys.executable, py))
            os.chmod(ruta, 0o755)
    registro = os.path.join(TMP, 'registro.jsonl')
    git = shutil.which('git')
    env = dict(os.environ, PATH=carpeta + (os.pathsep + os.path.dirname(git) if git else ''), FALSO_REGISTRO=registro)
    return registro, env


def llamadas(registro):
    try:
        with open(registro, encoding='utf-8') as h:
            return [json.loads(l) for l in h if l.strip()]
    except OSError:
        return []


def main():
    print('== auditar-iac')

    # ---------- SIN DATOS ----------
    rc, out = correr()
    caso('sin --repo: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS'), out[:200])
    rc, out = correr('--repo', os.path.join(TMP, 'no-existe'))
    caso('la carpeta no existe: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS'), out[:200])
    rc, out = correr('--repo', armar({'README.md': 'nada\n', 'src/app.py': 'print(1)\n'}))
    caso('repositorio sin infraestructura como codigo: SIN DATOS (2)', rc == 2 and out.startswith('SIN DATOS') and 'infraestructura' in out, out[:300])

    # ---------- camino feliz ----------
    limpio = armar(BASE)
    rc, out, d = auditar(limpio)
    caso('repositorio limpio con los cinco tipos: OK (0)', rc == 0 and d.get('estado') == 'OK', out[:1500])
    caso('reconoce los cinco tipos', all(d.get('tipos', {}).get(t) for t in ('terraform', 'bicep', 'dockerfile', 'compose', 'kubernetes')), str(d.get('tipos')))
    caso('cada regla con su estado y ninguna en blanco', len(d.get('reglas', [])) >= 17
         and all(r.get('estado') in ('OK', 'HALLAZGO', 'SIN DATOS', 'N/A') for r in d.get('reglas', [])), str(d.get('reglas'))[:400])
    caso('aviso: imagenes fijadas por etiqueta y no por digest', any('digest' in a for a in d.get('avisos', [])), str(d.get('avisos'))[:400])
    rc, out = correr('--repo', limpio)
    lineas = out.rstrip().splitlines() or ['']
    caso('texto: encabezado con el estado y termina con lo que NO mira',
         rc == 0 and out.startswith('AUDITAR IaC -- OK') and lineas[-1].strip().startswith('Lo que este script NO mira:'), out[-400:])
    rc, out, d = auditar(armar({'Dockerfile': 'FROM python:3.12-slim\nUSER app\n', '.dockerignore': '.git\n'}, git=False))
    caso('sin git y sin nada que versionar: OK (0); las reglas de Terraform son N/A',
         rc == 0 and regla(d, 'TF-NO-VERSIONAR')[0] == 'N/A' and regla(d, 'DOCKER-USER')[0] == 'OK', out[:600])

    # ---------- TF-NO-VERSIONAR ----------
    rc, out, d = auditar(armar(BASE, forzar=['envs/dev/terraform.tfstate']))
    h = hall(d, 'TF-NO-VERSIONAR')
    caso('estado versionado: HALLAZGO (1)', rc == 1 and len(h) == 1 and h[0]['archivo'] == 'envs/dev/terraform.tfstate', out[:600])
    rc, out, d = auditar(armar(con(BASE, _P_gitignore='.terraform/\n*.tfstate\n*.tfstate.*\n'), despues={'envs/prod/salida.tfplan': 'plan\n'}))
    h = hall(d, 'TF-NO-VERSIONAR')
    caso('plan guardado sin versionar pero sin ignorar: HALLAZGO (un git add lo sube)',
         rc == 1 and len(h) == 1 and h[0]['archivo'] == 'envs/prod/salida.tfplan' and 'ignor' in h[0]['detalle'], out[:600])
    rc, out, d = auditar(armar(con(BASE, _P_gitignore='*.tfstate\n*.tfstate.*\n*.tfplan\n')))
    h = hall(d, 'TF-NO-VERSIONAR')
    caso('.terraform/ sin ignorar: HALLAZGO', rc == 1 and len(h) == 1 and '.terraform' in h[0]['archivo'], out[:600])
    caso('falso positivo: estado y .terraform/ ignorados por git no son hallazgo (repo limpio)', regla(auditar(limpio)[2], 'TF-NO-VERSIONAR') == ('OK', 0))
    rc, out, d = auditar(armar(BASE, git=False))
    caso('sin git y con estado en la carpeta: esa regla es SIN DATOS y el total tambien (2)',
         rc == 2 and regla(d, 'TF-NO-VERSIONAR')[0] == 'SIN DATOS' and d.get('estado') == 'SIN DATOS', out[:600])

    # ---------- TF-LOCK ----------
    rc, out, d = auditar(armar(con(BASE, envs__prod___P_terraform_P_lock_P_hcl=None)))
    h = hall(d, 'TF-LOCK')
    caso('raiz sin .terraform.lock.hcl: HALLAZGO', rc == 1 and len(h) == 1 and h[0]['archivo'].startswith('envs/prod'), out[:600])
    rc, out, d = auditar(armar(con(BASE, _P_gitignore=BASE['.gitignore'] + '.terraform.lock.hcl\n')))
    caso('lock presente pero ignorado por git: HALLAZGO en las dos raices', rc == 1 and len(hall(d, 'TF-LOCK')) == 2, out[:600])
    caso('falso positivo: un modulo reutilizable no necesita lock (modules/red)', regla(d, 'TF-LOCK')[1] == 2 and not any('modules' in x['archivo'] for x in hall(d, 'TF-LOCK')))

    # ---------- TF-REQUIRED-VERSION ----------
    sin_rv = MOD_VERSIONES.replace('  required_version = ">= 1.6"\n', '  # required_version = ">= 1.6"\n')
    rc, out, d = auditar(armar(con(BASE, modules__red__versions_P_tf=sin_rv)))
    h = hall(d, 'TF-REQUIRED-VERSION')
    caso('modulo sin required_version (el comentado no cuenta): HALLAZGO', rc == 1 and len(h) == 1 and h[0]['archivo'].startswith('modules/red'), out[:600])
    caso('falso positivo: required_version en otro archivo de la misma carpeta alcanza', regla(auditar(limpio)[2], 'TF-REQUIRED-VERSION') == ('OK', 0))

    # ---------- TF-PROVIDER-VERSION ----------
    sin_pv = MAIN.replace('      version = "~> 5.0"\n', '')
    rc, out, d = auditar(armar(con(BASE, envs__dev__main_P_tf=sin_pv)))
    h = hall(d, 'TF-PROVIDER-VERSION')
    caso('proveedor sin version: HALLAZGO con archivo y linea', rc == 1 and len(h) == 1 and h[0]['archivo'] == 'envs/dev/main.tf' and h[0]['linea'] == 4, out[:600])
    caso('falso positivo: la forma vieja (nombre = "~> 2.0") tiene version', regla(auditar(limpio)[2], 'TF-PROVIDER-VERSION') == ('OK', 0))

    # ---------- TF-MODULO-VERSION ----------
    sin_mv = MAIN.replace('  version = "5.1.2"\n', '')
    rc, out, d = auditar(armar(con(BASE, envs__dev__main_P_tf=sin_mv)))
    caso('modulo de registro sin version: HALLAZGO', rc == 1 and len(hall(d, 'TF-MODULO-VERSION')) == 1, out[:600])
    sin_ref = MAIN.replace('?ref=' + SHA, '')
    rc, out, d = auditar(armar(con(BASE, envs__dev__main_P_tf=sin_ref)))
    caso('modulo de git sin ref: HALLAZGO', rc == 1 and len(hall(d, 'TF-MODULO-VERSION')) == 1, out[:600])
    con_tag = MAIN.replace('?ref=' + SHA, '?ref=v1.2.0')
    rc, out, d = auditar(armar(con(BASE, envs__dev__main_P_tf=con_tag)))
    caso('falso positivo: ref por etiqueta no es hallazgo, es aviso (una etiqueta se puede mover)',
         rc == 0 and regla(d, 'TF-MODULO-VERSION') == ('OK', 0) and any('v1.2.0' in a for a in d.get('avisos', [])), out[:600])
    caso('falso positivo: un modulo local no lleva version (y una URL con // no es un comentario)', regla(auditar(limpio)[2], 'TF-MODULO-VERSION') == ('OK', 0))

    # ---------- TF-VARIABLE y TF-OUTPUT ----------
    var_mala = VARIABLES + '''
variable "etiquetas" {
  type = object({ description = string })
  validation {
    condition     = true
    error_message = "description adentro de validation no cuenta"
  }
}
'''
    rc, out, d = auditar(armar(con(BASE, envs__dev__variables_P_tf=var_mala)))
    h = hall(d, 'TF-VARIABLE')
    caso('variable sin description (la palabra adentro del tipo no cuenta): HALLAZGO', rc == 1 and len(h) == 1 and 'etiquetas' in h[0]['detalle'], out[:600])
    rc, out, d = auditar(armar(con(BASE, envs__dev__outputs_P_tf='output "red_id" {\n  value = module.red.id\n}\n')))
    caso('output sin description: HALLAZGO', rc == 1 and len(hall(d, 'TF-OUTPUT')) == 1, out[:600])

    # ---------- TF-PROVIDER-EN-MODULO ----------
    rc, out, d = auditar(armar(con(BASE, modules__red__main_P_tf=MOD_MAIN + '\nprovider "ejemplo" {\n  region = "zona-1"\n}\n')))
    caso('bloque provider dentro de modules/: HALLAZGO', rc == 1 and len(hall(d, 'TF-PROVIDER-EN-MODULO')) == 1, out[:600])
    caso('falso positivo: el meta-argumento provider = ... y required_providers no son bloques provider', regla(auditar(limpio)[2], 'TF-PROVIDER-EN-MODULO') == ('OK', 0))

    # ---------- TF-BACKEND-COMPARTIDO ----------
    rc, out, d = auditar(armar(con(BASE, envs__prod__backend_P_tf=BACKEND % ('estado-ejemplo', 'dev/terraform.tfstate'))))
    caso('dos ambientes con el mismo backend: HALLAZGO', rc == 1 and len(hall(d, 'TF-BACKEND-COMPARTIDO')) == 1, out[:600])
    rc, out, d = auditar(armar(con(BASE, envs__prod__backend_P_tf=BACKEND % ('estado-otro', 'dev/terraform.tfstate'))))
    caso('falso positivo: la misma key en otro bucket no es el mismo estado', rc == 0 and regla(d, 'TF-BACKEND-COMPARTIDO') == ('OK', 0), out[:600])

    # ---------- SECRETO-LITERAL ----------
    variantes = [
        ('provider con %s literal' % CS, {'envs/dev/main.tf': MAIN.replace('  region = var.region\n', '  region = var.region\n  %s = "%s"\n' % (CS, V1))}, 'envs/dev/main.tf'),
        ('tfvars con una clave', {'envs/dev/terraform.tfvars': 'region = "zona-1"\ndb_password = "%s"\n' % V1}, 'envs/dev/terraform.tfvars'),
        ('default de una variable sensible', {'envs/dev/variables.tf': VARIABLES + 'variable "api_token" {\n  type        = string\n  description = "x"\n  default     = "%s"\n}\n' % V1}, 'envs/dev/variables.tf'),
        ('compose: clave en environment', {'compose.yaml': COMPOSE.replace('POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}', 'POSTGRES_PASSWORD: %s' % V1)}, 'compose.yaml'),
        ('compose: clave en la lista KEY=valor', {'compose.yaml': COMPOSE.replace('- LOG_LEVEL=info', '- API_TOKEN=%s' % V1)}, 'compose.yaml'),
        ('Dockerfile: ENV con una clave', {'app/Dockerfile': DOCKERFILE.replace('LOG_LEVEL=info', 'LOG_LEVEL=info API_TOKEN=%s' % V1)}, 'app/Dockerfile'),
        ('Kubernetes: env con value literal', {'k8s/app.yaml': K8S.replace('              valueFrom:\n                secretKeyRef:\n                  name: db\n                  key: password\n', '              value: "%s"\n' % V1)}, 'k8s/app.yaml'),
        ('Bicep: param con valor por defecto', {'infra/main.bicep': BICEP.replace('param adminPassword string\n', "param adminPassword string = '%s'\n" % V1)}, 'infra/main.bicep'),
        ('Bicep: propiedad con valor literal', {'infra/main.bicep': BICEP.replace('adminPassword: adminPassword', "adminPassword: '%s'" % V1)}, 'infra/main.bicep'),
    ]
    for nombre, cambios, archivo in variantes:
        datos = dict(BASE)
        datos.update(cambios)
        rc, out, d = auditar(armar(datos))
        h = hall(d, 'SECRETO-LITERAL')
        caso('secreto escrito tal cual (%s): HALLAZGO con archivo, linea y huella, sin el valor' % nombre,
             rc == 1 and len(h) == 1 and h[0]['archivo'] == archivo and h[0].get('linea') and h[0].get('huella') and V1 not in out, out[:700])
    rc, out = correr('--repo', armar(dict(BASE, **{'envs/dev/terraform.tfvars': 'db_password = "%s"\n' % V1})))
    caso('tampoco en el texto aparece el valor', rc == 1 and V1 not in out and 'SECRETO-LITERAL' in out, out[:700])
    fp = dict(BASE)
    fp['envs/dev/terraform.tfvars'] = 'db_password = ""\napi_token = "<completar>"\n# %s = "%s"\n' % (CS, V1)
    rc, out, d = auditar(armar(fp))
    caso('falso positivo: vacio, marcador y comentario no son secretos', rc == 0 and regla(d, 'SECRETO-LITERAL') == ('OK', 0), out[:700])
    caso('falso positivo: var.x, "${var.x}", password_length, secret_name, *_FILE, ${VAR} y valueFrom (repo limpio)',
         regla(auditar(limpio)[2], 'SECRETO-LITERAL') == ('OK', 0))

    # ---------- SECRETO-FORMATO ----------
    rc, out, d = auditar(armar(dict(BASE, **{'envs/dev/terraform.tfvars': 'region = "zona-1"\n# copia: %s\n' % AKIA})))
    h = hall(d, 'SECRETO-FORMATO')
    caso('clave con formato conocido, aunque este en un comentario: HALLAZGO sin el valor', rc == 1 and len(h) == 1 and AKIA not in out, out[:600])
    llave = MOD_MAIN + '\nlocals {\n  certificado = <<EOT\n%s\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\nEOT\n}\n' % LLAVE
    rc, out, d = auditar(armar(dict(BASE, **{'modules/red/main.tf': llave})))
    caso('clave privada en un heredoc: HALLAZGO', rc == 1 and len(hall(d, 'SECRETO-FORMATO')) == 1, out[:600])
    rc, out, d = auditar(armar(dict(BASE, **{'envs/dev/terraform.tfvars': 'conexion = "AccountKey=<completar>"\n'})))
    caso('falso positivo: AccountKey=<completar> es un marcador', rc == 0 and regla(d, 'SECRETO-FORMATO') == ('OK', 0), out[:600])

    # ---------- BICEP-OUTPUT-SEGURO ----------
    rc, out, d = auditar(armar(dict(BASE, **{'infra/main.bicep': BICEP.replace("@secure()\noutput", 'output')})))
    caso('Bicep: salida con nombre sensible sin @secure(): HALLAZGO', rc == 1 and len(hall(d, 'BICEP-OUTPUT-SEGURO')) == 1, out[:600])
    caso('falso positivo: @secure() con otro decorador encima, y una salida que solo nombra el secreto', regla(auditar(limpio)[2], 'BICEP-OUTPUT-SEGURO') == ('OK', 0))

    # ---------- DOCKER-FROM, DOCKER-USER, DOCKER-IGNORE ----------
    malo = 'FROM ubuntu AS build\nRUN make\n\nFROM ubuntu:latest\nUSER app\n'
    rc, out, d = auditar(armar(dict(BASE, **{'app/Dockerfile': malo})))
    caso('FROM sin etiqueta y FROM con latest: HALLAZGO x2', rc == 1 and len(hall(d, 'DOCKER-FROM')) == 2, out[:600])
    caso('falso positivo: etapa interna, registro con puerto, digest y ARG con valor (repo limpio)', regla(auditar(limpio)[2], 'DOCKER-FROM') == ('OK', 0))
    rc, out, d = auditar(armar(dict(BASE, **{'app/Dockerfile': 'FROM python:3.12-slim\nCOPY . /app\n'})))
    caso('la etapa final sin USER: HALLAZGO', rc == 1 and len(hall(d, 'DOCKER-USER')) == 1, out[:600])
    rc, out, d = auditar(armar(dict(BASE, **{'app/Dockerfile': 'FROM python:3.12-slim\nUSER app\nRUN x\nUSER 0:0\n'})))
    caso('la etapa final termina en root (USER 0:0): HALLAZGO', rc == 1 and len(hall(d, 'DOCKER-USER')) == 1, out[:600])
    rc, out, d = auditar(armar(dict(BASE, **{'app/Dockerfile': 'FROM golang:1.22 AS build\nRUN go build\nFROM gcr.io/distroless/static:nonroot\nCOPY --from=build /app /app\n'})))
    caso('falso positivo: imagen nonroot y USER heredado de una etapa interna', rc == 0 and regla(d, 'DOCKER-USER') == ('OK', 0), out[:600])
    rc, out, d = auditar(armar(con(BASE, app___P_dockerignore=None)))
    caso('sin .dockerignore: HALLAZGO', rc == 1 and len(hall(d, 'DOCKER-IGNORE')) == 1, out[:600])
    rc, out, d = auditar(armar(con(BASE, app___P_dockerignore=None, _P_dockerignore='.git\n')))
    caso('falso positivo: .dockerignore en la raiz del repositorio', rc == 0 and regla(d, 'DOCKER-IGNORE') == ('OK', 0), out[:600])
    rc, out, d = auditar(armar(con(BASE, app___P_dockerignore=None, app__Dockerfile_P_dockerignore='.git\n')))
    caso('falso positivo: Dockerfile.dockerignore al lado', rc == 0 and regla(d, 'DOCKER-IGNORE') == ('OK', 0), out[:600])

    # ---------- IMAGEN-LATEST ----------
    rc, out, d = auditar(armar(dict(BASE, **{'compose.yaml': COMPOSE.replace('\nsecrets:\n  db_password:', '\n  cache:\n    image: redis\nsecrets:\n  db_password:')})))
    caso('compose: imagen sin etiqueta y sin build: HALLAZGO', rc == 1 and len(hall(d, 'IMAGEN-LATEST')) == 1, out[:600])
    rc, out, d = auditar(armar(dict(BASE, **{'k8s/app.yaml': K8S.replace('registry.local:5000/web:1.0.3', 'nginx:latest')})))
    caso('Kubernetes: imagen latest: HALLAZGO', rc == 1 and len(hall(d, 'IMAGEN-LATEST')) == 1 and hall(d, 'IMAGEN-LATEST')[0]['archivo'] == 'k8s/app.yaml', out[:600])
    rc, out, d = auditar(armar(dict(BASE, **{'compose.yaml': COMPOSE.replace('image: postgres:16.2', 'image: ${IMAGEN_DB}')})))
    caso('falso positivo: imagen por variable y la imagen de un servicio con build', rc == 0 and regla(d, 'IMAGEN-LATEST') == ('OK', 0), out[:600])

    # ---------- K8S-SECRET ----------
    secreto = K8S.replace('stringData:\n  password: ENC[AES256_GCM,data:abc,iv:def,tag:ghi,type:str]\nsops:\n  version: 3.8.1\n', 'data:\n  password: aGVsbG8tbXVuZG8=\n')
    rc, out, d = auditar(armar(dict(BASE, **{'k8s/app.yaml': secreto})))
    caso('Secret con data en el repo: HALLAZGO (Base64 no es cifrado)', rc == 1 and len(hall(d, 'K8S-SECRET')) == 1, out[:600])
    sellado = K8S.replace('kind: Secret', 'kind: SealedSecret').replace('stringData:', 'spec:\n  encryptedData:').replace('sops:\n  version: 3.8.1\n', '')
    rc, out, d = auditar(armar(dict(BASE, **{'k8s/app.yaml': sellado})))
    caso('falso positivo: un SealedSecret y un Secret cifrado con SOPS no son hallazgo', rc == 0 and regla(d, 'K8S-SECRET') == ('OK', 0), out[:600])
    plantilla = dict(BASE)
    plantilla['chart/templates/deploy.yaml'] = 'apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n        - image: {{ .Values.imagen }}\n'
    rc, out, d = auditar(armar(plantilla))
    caso('una plantilla de Helm no se mira como manifiesto, y se avisa', rc == 0 and any('Helm' in a for a in d.get('avisos', [])), out[:600])

    # ---------- herramientas (reportes plantados: sin instalar nada) ----------
    vacio = os.path.join(TMP, 'path-vacio')
    os.makedirs(vacio)
    env = dict(os.environ)
    env['PATH'] = vacio
    rc, out, d = auditar(limpio, '--herramientas', env=env)
    caso('--herramientas sin ninguna instalada: cada una SIN DATOS y el total SIN DATOS (2)',
         rc == 2 and herramienta(d, 'tflint').get('estado') == 'SIN DATOS' and herramienta(d, 'hadolint').get('estado') == 'SIN DATOS', out[:800])
    tfl = reportar('tflint.json', {'issues': [{'rule': {'name': 'terraform_unused_declarations', 'severity': 'warning', 'link': 'x'},
                                               'message': 'variable "x" is declared but not used',
                                               'range': {'filename': 'envs/dev/variables.tf', 'start': {'line': 3, 'column': 1}, 'end': {'line': 3, 'column': 2}},
                                               'callers': []}], 'errors': []})
    rc, out, d = auditar(limpio, '--reporte', 'tflint=' + tfl)
    t = herramienta(d, 'tflint')
    caso('tflint con un issue: HALLAZGO (1) con archivo:linea', rc == 1 and t.get('estado') == 'HALLAZGO' and any('envs/dev/variables.tf:3' in x for x in t.get('hallazgos', [])), out[:800])
    rc, out, d = auditar(limpio, '--reporte', 'tflint=' + reportar('tflint-ok.json', {'issues': [], 'errors': []}))
    caso('tflint sin issues ni errores: OK (0)', rc == 0 and herramienta(d, 'tflint').get('estado') == 'OK', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'tflint=' + reportar('tflint-err.json', {'issues': [], 'errors': [{'message': 'plugin no instalado', 'severity': 'error'}]}))
    caso('tflint con errores y sin issues: SIN DATOS (no termino de mirar)', rc == 2 and herramienta(d, 'tflint').get('estado') == 'SIN DATOS', out[:600])
    chk = reportar('checkov.json', [{'check_type': 'terraform', 'results': {'failed_checks': [
        {'check_id': 'CKV_X_1', 'check_name': 'cifrado apagado', 'file_path': '/modules/red/main.tf', 'file_line_range': [1, 9], 'resource': 'ejemplo_red.this'}]},
        'summary': {'passed': 10, 'failed': 1, 'skipped': 0, 'parsing_errors': 0, 'resource_count': 3}},
        {'check_type': 'dockerfile', 'results': {'failed_checks': []}, 'summary': {'passed': 4, 'failed': 0, 'skipped': 0, 'parsing_errors': 0, 'resource_count': 1}}])
    rc, out, d = auditar(limpio, '--reporte', 'checkov=' + chk)
    caso('checkov con un check fallido: HALLAZGO (1)', rc == 1 and herramienta(d, 'checkov').get('estado') == 'HALLAZGO'
         and any('CKV_X_1' in x and 'modules/red/main.tf:1' in x for x in herramienta(d, 'checkov').get('hallazgos', [])), out[:800])
    rc, out, d = auditar(limpio, '--reporte', 'checkov=' + reportar('checkov-nada.json', {'passed': 0, 'failed': 0, 'skipped': 0, 'parsing_errors': 0, 'resource_count': 0, 'checkov_version': '3'}))
    caso('checkov que no analizo nada: SIN DATOS (regla del cero)', rc == 2 and herramienta(d, 'checkov').get('estado') == 'SIN DATOS', out[:600])
    tri = reportar('trivy.json', {'SchemaVersion': 2, 'Results': [{'Target': 'app/Dockerfile', 'Class': 'config', 'Type': 'dockerfile',
                                  'MisconfSummary': {'Successes': 20, 'Failures': 1},
                                  'Misconfigurations': [{'ID': 'DS-0002', 'Title': 'usuario root', 'Severity': 'HIGH', 'Status': 'FAIL',
                                                         'CauseMetadata': {'StartLine': 1}}]}]})
    rc, out, d = auditar(limpio, '--reporte', 'trivy=' + tri)
    caso('trivy con una mala configuracion: HALLAZGO (1)', rc == 1 and any('DS-0002' in x for x in herramienta(d, 'trivy').get('hallazgos', [])), out[:800])
    rc, out, d = auditar(limpio, '--reporte', 'trivy=' + reportar('trivy-nada.json', {'SchemaVersion': 2, 'Results': []}))
    caso('trivy sin resultados: SIN DATOS', rc == 2 and herramienta(d, 'trivy').get('estado') == 'SIN DATOS', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'hadolint=' + reportar('hadolint.json', [{'file': 'app/Dockerfile', 'line': 5, 'column': 1, 'level': 'warning', 'code': 'DL3008', 'message': 'fijar versiones'}]))
    caso('hadolint con un warning: HALLAZGO (1)', rc == 1 and herramienta(d, 'hadolint').get('estado') == 'HALLAZGO', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'hadolint=' + reportar('hadolint-estilo.json', [{'file': 'app/Dockerfile', 'line': 5, 'column': 1, 'level': 'style', 'code': 'DL3059', 'message': 'juntar RUN'}]))
    caso('hadolint solo con estilo: OK (0) con aviso', rc == 0 and herramienta(d, 'hadolint').get('estado') == 'OK' and herramienta(d, 'hadolint').get('avisos'), out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'validate=' + reportar('validate.json', {'format_version': '1.0', 'valid': False, 'error_count': 1, 'warning_count': 0,
                                                                                         'diagnostics': [{'severity': 'error', 'summary': 'Unsupported argument',
                                                                                                          'range': {'filename': 'main.tf', 'start': {'line': 7}}}]}))
    caso('validate con un error: HALLAZGO (1)', rc == 1 and herramienta(d, 'validate').get('estado') == 'HALLAZGO', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'validate=' + reportar('validate-v2.json', {'format_version': '2.0', 'valid': True, 'error_count': 0, 'warning_count': 0, 'diagnostics': []}))
    caso('validate con formato de version desconocida: SIN DATOS', rc == 2 and herramienta(d, 'validate').get('estado') == 'SIN DATOS', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'validate=' + reportar('validate-ok.json', {'format_version': '1.0', 'valid': True, 'error_count': 0, 'warning_count': 0, 'diagnostics': []}))
    caso('validate valido: OK (0)', rc == 0 and herramienta(d, 'validate').get('estado') == 'OK', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'kubeconform=' + reportar('kc.json', {'resources': [{'filename': 'k8s/app.yaml', 'kind': 'Deployment', 'name': 'web', 'version': 'apps/v1',
                                                                                                     'status': 'statusInvalid', 'msg': 'falta un campo'}],
                                                                                       'summary': {'valid': 1, 'invalid': 1, 'errors': 0, 'skipped': 0}}))
    caso('kubeconform con un recurso invalido: HALLAZGO (1)', rc == 1 and herramienta(d, 'kubeconform').get('estado') == 'HALLAZGO', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'kubeconform=' + reportar('kc-nada.json', {'resources': [], 'summary': {'valid': 0, 'invalid': 0, 'errors': 0, 'skipped': 2}}))
    caso('kubeconform que no valido nada: SIN DATOS', rc == 2 and herramienta(d, 'kubeconform').get('estado') == 'SIN DATOS', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'fmt=' + reportar('fmt.txt', 'envs/dev/main.tf\n'))
    caso('fmt con un archivo sin formato: HALLAZGO (1)', rc == 1 and herramienta(d, 'fmt').get('estado') == 'HALLAZGO', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'fmt=' + reportar('fmt-vacio.txt', ''))
    caso('reporte de fmt vacio: SIN DATOS (no se distingue de no haber corrido)', rc == 2 and herramienta(d, 'fmt').get('estado') == 'SIN DATOS', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'tflint=' + os.path.join(TMP, 'no-esta.json'))
    caso('reporte que no existe: SIN DATOS', rc == 2 and herramienta(d, 'tflint').get('estado') == 'SIN DATOS', out[:600])
    rc, out, d = auditar(limpio, '--reporte', 'tflint=' + reportar('roto.json', '{"issues": ['))
    caso('reporte ilegible: SIN DATOS', rc == 2 and herramienta(d, 'tflint').get('estado') == 'SIN DATOS', out[:600])
    rc, out = correr('--repo', limpio, '--reporte', 'escaner-magico=' + tfl)
    caso('una herramienta que el script no conoce: SIN DATOS', rc == 2 and 'escaner-magico' in out, out[:400])
    rc, out, d = auditar(limpio, '--reporte', 'hadolint=' + reportar('hadolint2.json', [{'file': 'app/Dockerfile', 'line': 5, 'column': 1, 'level': 'warning', 'code': 'DL3008', 'message': 'x'}]),
                         '--reporte', 'tflint=' + os.path.join(TMP, 'no-esta.json'))
    caso('una herramienta en HALLAZGO pesa mas que el SIN DATOS de otra: HALLAZGO (1)',
         rc == 1 and herramienta(d, 'tflint').get('estado') == 'SIN DATOS' and herramienta(d, 'hadolint').get('estado') == 'HALLAZGO', out[:600])

    # ---------- arreglos F1 ----------
    # (a) los atributos de secreto de un proveedor y las claves entre comillas
    db = ('resource "ejemplo_secreto_version" "db" {\n  secret_id     = "x"\n  secret_string = "%s"\n}\n'
          'resource "ejemplo_base" "db" {\n  password_wo  = "%s"\n  secret_value = "%s"\n  tags = {\n'
          '    "db_password" = "%s"\n    "Name"        = "base"\n  }\n}\n' % (V1, V1, V1, V1))
    rc, out, d = auditar(armar(dict(BASE, **{'envs/dev/db.tf': db})))
    lineas_h = sorted(h['linea'] for h in hall(d, 'SECRETO-LITERAL') if h['archivo'] == 'envs/dev/db.tf')
    caso('secret_string, password_wo, secret_value y "db_password" entre comillas: HALLAZGO cada uno (y "Name" no)',
         rc == 1 and lineas_h == [3, 6, 7, 9] and V1 not in out, out[:900])
    # (b) planes guardados con otros nombres
    rc, out, d = auditar(armar(BASE, despues={'envs/prod/tfplan': 'p\n', 'envs/prod/plan.out': 'p\n', 'envs/prod/salida.plan': 'p\n'}))
    h = sorted(x['archivo'] for x in hall(d, 'TF-NO-VERSIONAR'))
    caso('planes guardados como tfplan, plan.out o *.plan sin ignorar: HALLAZGO cada uno',
         rc == 1 and h == ['envs/prod/plan.out', 'envs/prod/salida.plan', 'envs/prod/tfplan'], out[:700])
    # (c) un archivo que no se miro: el total no puede ser OK
    grande = armar({'Dockerfile': 'FROM python:3.12-slim\nUSER app\n', '.dockerignore': '.git\n',
                    'otro/Dockerfile': 'FROM python:3.12-slim\nUSER app\n' + '# relleno\n' * 240000, 'otro/.dockerignore': '.git\n'}, git=False)
    rc, out, d = auditar(grande)
    caso('un archivo demasiado grande que no se miro: sin hallazgos, el total es SIN DATOS (2), no OK',
         rc == 2 and d.get('estado') == 'SIN DATOS' and any('no se miro' in x for x in d.get('avisos', [])), out[:700])
    try:
        import contextlib
        import importlib.util
        import io
        spec = importlib.util.spec_from_file_location('auditar_iac_prueba', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.MAX_ARCHIVOS = 2
        viejo, buf = sys.argv, io.StringIO()
        sys.argv = ['auditar-iac.py', '--repo', armar({'Dockerfile': 'FROM python:3.12-slim\nUSER app\n', '.dockerignore': '.git\n',
                                                       'z1.txt': 'x', 'z2.txt': 'x'}, git=False), '--json']
        try:
            with contextlib.redirect_stdout(buf):
                rc = mod.main()
        finally:
            sys.argv = viejo
        caso('se llego al tope de archivos: sin hallazgos, el total es SIN DATOS (2)', rc == 2, buf.getvalue()[:500])
    except Exception as e:  # noqa: BLE001
        caso('se llego al tope de archivos: sin hallazgos, el total es SIN DATOS (2)', False, repr(e))
    # (d) un .tfvars que git ignora no viaja con el codigo
    ign = armar(dict(BASE, **{'.gitignore': BASE['.gitignore'] + 'secretos.auto.tfvars\n',
                              'envs/dev/secretos.auto.tfvars': 'db_password = "%s"\n' % V1}))
    rc, out, d = auditar(ign)
    caso('un .tfvars ignorado por git con una clave: no es SECRETO-LITERAL (avisa)',
         rc == 0 and regla(d, 'SECRETO-LITERAL') == ('OK', 0) and any('secretos.auto.tfvars' in x for x in d.get('avisos', [])), out[:700])
    # (g) huella solo de un valor largo
    rc, out, d = auditar(armar(dict(BASE, **{'envs/dev/terraform.tfvars': 'db_password = "corta123"\n'})))
    h = hall(d, 'SECRETO-LITERAL')
    caso('un valor de menos de 16 caracteres: HALLAZGO sin huella (se revertiria con un diccionario)',
         rc == 1 and len(h) == 1 and 'huella' not in h[0], out[:600])
    # herramientas de mentira en el PATH
    registro, env = falsos('trivy', 'tflint', 'kubeconform')
    env['FALSO_REPORTE_TRIVY'] = tri
    env['FALSO_REPORTE_TFLINT'] = reportar('tflint-ok2.json', {'issues': [], 'errors': []})
    env['FALSO_REPORTE_KUBECONFORM'] = reportar('kc-ok.json', {'resources': [], 'summary': {'valid': 1, 'invalid': 0, 'errors': 0, 'skipped': 0}})
    rc, out, d = auditar(limpio, '--herramientas', 'trivy,tflint', env=env)
    tri_llamada = [x for x in llamadas(registro) if x['herramienta'] == 'trivy' and 'config' in x['args']]
    caso('trivy corre con --disable-telemetry y --skip-version-check',
         tri_llamada and '--disable-telemetry' in tri_llamada[0]['args'] and '--skip-version-check' in tri_llamada[0]['args'], str(llamadas(registro))[:600])
    tfl_llamada = [x for x in llamadas(registro) if x['herramienta'] == 'tflint' and '--recursive' in x['args']]
    caso('tflint --recursive corre desde la carpeta del repositorio, sin --chdir',
         tfl_llamada and not any(a.startswith('--chdir') for a in tfl_llamada[0]['args'])
         and os.path.normcase(os.path.realpath(tfl_llamada[0]['cwd'])) == os.path.normcase(os.path.realpath(limpio)), str(tfl_llamada)[:600])
    env['FALSO_VERSION'] = '0.69.4'
    rc, out, d = auditar(limpio, '--herramientas', 'trivy', env=env)
    caso('trivy 0.69.4 (la del incidente de marzo de 2026): SIN DATOS con ese motivo',
         rc == 2 and herramienta(d, 'trivy').get('estado') == 'SIN DATOS' and '0.69.4' in herramienta(d, 'trivy').get('detalle', ''), out[:700])
    del env['FALSO_VERSION']
    n_antes = len(llamadas(registro))
    rc, out, d = auditar(limpio, '--herramientas', 'kubeconform', '--esquemas-k8s', 'https://esquemas.example.com/{{.ResourceKind}}.json', env=env)
    caso('--esquemas-k8s que no es una carpeta local: kubeconform SIN DATOS y no se corre',
         herramienta(d, 'kubeconform').get('estado') == 'SIN DATOS'
         and not any(x['herramienta'] == 'kubeconform' and '-output' in x['args'] for x in llamadas(registro)[n_antes:]), out[:700])
    rc, out, d = auditar(limpio, '--herramientas', 'kubeconform', '--esquemas-k8s', os.path.join(TMP, 'no-existe'), env=env)
    caso('--esquemas-k8s con una carpeta que no existe: SIN DATOS', herramienta(d, 'kubeconform').get('estado') == 'SIN DATOS', out[:700])
    esquemas = os.path.join(TMP, 'esquemas')
    os.makedirs(esquemas, exist_ok=True)
    rc, out, d = auditar(limpio, '--herramientas', 'kubeconform', '--esquemas-k8s', esquemas, env=env)
    caso('--esquemas-k8s con una carpeta local: kubeconform corre y lee su reporte', herramienta(d, 'kubeconform').get('estado') == 'OK', out[:700])

    # ---------- --json y el archivo ----------
    rc, out, d = auditar(armar({'servicio-caf' + chr(0xE9) + '/Dockerfile': 'FROM ubuntu\n'}, git=False))
    caso('--json sale en ASCII aunque una ruta tenga acentos', rc == 1 and bool(d) and all(ord(c) < 128 for c in out), out[:300])
    for ruta in (SCRIPT, os.path.abspath(__file__)):
        try:
            with open(ruta, 'rb') as h:
                datos_py = h.read()
        except OSError:
            datos_py = b''
        caso('%s es ASCII puro' % os.path.basename(ruta), bool(datos_py) and all(b < 128 for b in datos_py))

    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('OK' if not fallas else 'FALLA', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
