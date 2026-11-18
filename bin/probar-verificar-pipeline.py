#!/usr/bin/env python3
"""Prueba de bin/verificar-pipeline.py sobre pipelines de muestra (GitHub Actions, GitLab CI y Azure Pipelines),
reportes plantados de zizmor, actionlint y poutine, y la raiz de este mismo repositorio.
Se corre:  python -B bin/probar-verificar-pipeline.py   -> OK o FALLA, con el detalle de cada caso.
No necesita red ni ninguna herramienta instalada."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SCRIPT = os.path.join(AQUI, 'verificar-pipeline.py')
ESPERADOS = []
CONFIRMADA = ('--plataforma-confirmada', 'lider tecnico')   # una persona miro a mano aprobaciones y proteccion (P9)
SHA ='11d5960a326750d5838078e36cf38b85af677262'

WF_BUENO = '''name: ci
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@%s # v4.4.0
        with:
          persist-credentials: false
      # - uses: algo/comentado@v1
      - uses: ./.github/actions/propia
      - name: Tests
        env:
          TITULO: ${{ github.event.pull_request.title }}
          API_TOKEN: ${{ secrets.API_TOKEN }}
          TOKEN_URL: https://login.example.com/token
          TOKEN_TTL: 3600
        run: |
          echo "uses: algo/raro@main y permissions: write-all"
          echo "$TITULO" pr ${{ github.event.pull_request.number }}
          # AWS_SECRET_ACCESS_KEY no se usa: comentario
          kubectl get pods
          pytest
''' % SHA

WF_MALO = '''name: malo
on: [push, pull_request_target]
permissions: write-all
jobs:
  build:
    runs-on: ubuntu-latest
    container: node:20
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - name: Saludo
        run: echo "${{ github.event.issue.title }}"
      - name: Tests
        run: npm test
        continue-on-error: true
      - name: Subir
        run: ./subir.sh
        continue-on-error: true
      - uses: actions/github-script@%s # v7
        with:
          script: console.log("${{ github.event.comment.body }}")
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@%s # v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: kubectl apply -f k8s/
  reusa:
    uses: org/plantillas/.github/workflows/deploy.yml@main
    secrets: inherit
''' % (SHA, SHA)

WF_SIN_PERMISOS = '''on: push
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - run: echo a
  b:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - run: echo b
'''
WF_PERMISOS_POR_JOB = WF_SIN_PERMISOS.replace('  a:\n    runs-on: ubuntu-latest\n', '  a:\n    runs-on: ubuntu-latest\n    permissions: {}\n')
WF_ESCRITURA_ARRIBA = 'on: push\npermissions:\n  contents: write\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo a\n'
WF_PRT_SIN_REF = ('on:\n  pull_request_target:\npermissions:\n  contents: read\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n'
                  '      - uses: actions/checkout@%s # v4.4.0\n        with:\n          persist-credentials: false\n      - run: echo hola\n' % SHA)
WF_ENV = '''on: push
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: %s
    concurrency: prod
    steps:
      - run: helm upgrade app ./chart
'''
WF_ANCLAS = 'on: push\npermissions:\n  contents: read\njobs:\n  a: &base\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo a\n  b:\n    <<: *base\n'

GITLAB = '''include:
  - project: 'grupo/plantillas'
    file: '/ci/base.yml'
  - project: 'grupo/plantillas'
    ref: 0123456789abcdef0123456789abcdef01234567
    file: '/ci/otra.yml'
  - template: Security/SAST.gitlab-ci.yml
  - component: $CI_SERVER_FQDN/grupo/comp/lint@~latest
  - component: $CI_SERVER_FQDN/grupo/comp/build@1.4.2
  - remote: 'https://example.com/ci.yml'
  - remote: 'https://example.com/fijo.yml'
    integrity: 'sha256-L3/GAoKaw0Arw6hDCKeKQlV1QPEgHYxGBHsH4zG1IY8='
  - project: 'grupo/otra'
    ref: main
    file: '/ci/x.yml'
  - project: 'grupo/otra'
    ref: v2
    file: '/ci/y.yml'
image: python:3.12-slim
variables:
  DB_PASSWORD: "no-va-aca-1234"
  DEPLOY_TOKEN: $TOKEN_PROTEGIDO
  GIT_DEPTH: "0"
stages: [test, deploy]
.plantilla:
  script:
    - kubectl apply -f k8s/
tests:
  stage: test
  script:
    - pytest
    - echo "deploy: no"
    - for t in a b; do case "$t" in *probar-reglas.py) echo salteado;; esac; done
  allow_failure: true
lint:
  stage: test
  script:
    - ruff check .
  allow_failure: false
desplegar:
  stage: deploy
  script:
    - helm upgrade app ./chart
deploy-prod:
  stage: deploy
  environment:
    name: Produccion
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true"
      when: manual
  script:
    - kubectl apply -f k8s/
'''

GITLAB_PROD = '''workflow:
  rules:
    - if: $CI_COMMIT_BRANCH
prod-manual:
  environment: Produccion
  when: manual
  resource_group: prod
  script:
    - kubectl apply -f k8s/
prod-tier:
  environment:
    name: live
    deployment_tier: production
  resource_group: prod
  script:
    - helm upgrade app ./chart
prod-protegido:
  environment: Produccion
  resource_group: prod
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true"
  script:
    - kubectl apply -f k8s/
prueba-manual:
  environment: Prueba
  when: manual
  resource_group: prueba
  script:
    - kubectl apply -f k8s/
'''

GITLAB_EXTRA = '''workflow:
  rules:
    - if: $CI_COMMIT_BRANCH
image:
  name: $CI_REGISTRY_IMAGE/build:$VERSION
  pull_policy: if-not-present
construir:
  image:
    name: python:3.12
    pull_policy: always
  services:
    - docker:24-dind
    - postgres:16
  script:
    - curl -fsSL https://example.com/instalar.sh | sh
    - curl -s https://example.com/api | jq .
    - docker run -v /var/run/docker.sock:/var/run/docker.sock alpine true
  only:
    - main
abajo:
  trigger:
    project: grupo/otro
    strategy: depend
    forward:
      pipeline_variables: true
abajo-simple:
  trigger:
    project: grupo/otro
publicar:
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  release:
    tag_name: $CI_COMMIT_TAG
    description: version
  script:
    - echo publicar
publicar-otro:
  image: alpine:3.20
  release:
    tag_name: $CI_COMMIT_TAG
    description: version
  rules:
    - if: $CI_COMMIT_TAG
  script:
    - echo publicar
'''

AZURE = '''trigger:
  - main
resources:
  repositories:
    - repository: plantillas
      type: git
      name: proyecto/plantillas
      ref: refs/heads/main
    - repository: fijo
      type: git
      name: proyecto/fijo
      ref: refs/tags/v1.2.0
variables:
  - name: API_KEY
    value: abc123secreto
  - name: ARM_CLIENT_SECRET
    value: $(secreto)
stages:
  - stage: build
    jobs:
      - job: test
        steps:
          - script: dotnet test
            continueOnError: true
          - task: AzureWebApp@1
            inputs:
              appName: app
  - stage: prod
    jobs:
      - deployment: desplegar
        strategy:
          runOnce:
            deploy:
              steps:
                - script: echo hola
      - deployment: con_ambiente
        environment: Produccion.web
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                  persistCredentials: true
'''

CAB_AMB = ('| Ambiente | Para qué es | Protegido | Quién aprueba (rol) | Dónde se aprueba | Qué entra (rama o tag) | '
           'Ventana de observación | Cómo se vuelve atrás | Cuánto tarda en volver |\n|---|---|---|---|---|---|---|---|---|\n')
FILA_PRUEBA = '| `Prueba` | aceptacion | sí | lider | plataforma | tags v* | 30 minutos | volver | 5 minutos |\n'
FILA_PROD = '| `Produccion` | usuarios | sí | dueno | plataforma | tags v* | 30 minutos | volver | 5 minutos |\n'
GITLAB_F1 = '''workflow:
  rules:
    - if: $CI_COMMIT_BRANCH
include:
  - { project: 'grupo/flujo', file: '/ci/a.yml' }
  - { project: 'grupo/fijo', ref: 0123456789abcdef0123456789abcdef01234567, file: ['/ci/b.yml', '/ci/c.yml'] }
  - remote: 'https://usuario:CLAVE-PLANTADA-123@example.com/ci.yml?private_token=TOKEN-PLANTADO-456'
variables:
  STORAGE_ACCOUNT_KEY: "clave-de-cuenta-escrita-1234"
  DB_CONNECTION_STRING: "Server=x;Password=PLANTADA-789"
  CORTA_PASSWORD: "corta1"
prod-ar:
  environment: production-ar
  resource_group: prod
  script:
    - curl -H "PRIVATE-TOKEN: glpat-PLANTADOabcdefghijklmnopq" https://example.com/i.sh | sh
prd-falso:
  environment:
    name: PRD
  resource_group: prod
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "false"
  script:
    - echo $CI_COMMIT_REF_PROTECTED == "true"
    - kubectl apply -f k8s/
'''
PLANTADOS_F1 = ('CLAVE-PLANTADA-123', 'TOKEN-PLANTADO-456', 'glpat-PLANTADO', 'PLANTADA-789', 'clave-de-cuenta-escrita-1234')
GITLAB_FLUJO_ROTO = "include:\n  - { project: 'grupo/x', file: '/a.yml'\ntests:\n  script:\n    - pytest\n"
WF_SERVICIOS = '''on: push
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - run: pytest
'''

FILA_MOLDE = '| `<nombre-exacto-en-la-plataforma>` | `<para qué>` | sí | `<rol>` | `<donde>` | `<rama>` | `<min>` | `<proc>` | `<min>` |\n'


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)) if (detalle and not ok) else ''))


def correr(*args, env=None):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=env)
    return r.returncode, r.stdout + r.stderr


def correr_json(*args, env=None):
    rc, out = correr(*(list(args) + ['--json']), env=env)
    try:
        return rc, json.loads(out), out
    except ValueError:
        return rc, {}, out


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as h:
        h.write(texto.encode('utf-8'))
    return ruta


def repo_con(tmp, nombre, archivos):
    r = os.path.join(tmp, nombre)
    for rel, texto in archivos.items():
        escribir(os.path.join(r, rel), texto)
    os.makedirs(r, exist_ok=True)
    return r


def chk(j, id_):
    for c in j.get('chequeos', []):
        if c.get('id') == id_:
            return c
    return {'estado': 'NO ESTA', 'hallazgos': [], 'avisos': [], 'detalle': ''}


def texto_de(c):
    return ' | '.join(c.get('hallazgos', []) + c.get('avisos', []) + [c.get('detalle', '')])


def herramienta(j, nombre):
    for c in j.get('profundo', []):
        if c.get('herramienta') == nombre:
            return c
    return {'estado': 'NO ESTA', 'hallazgos': [], 'avisos': [], 'detalle': ''}


def main():
    print('== verificar-pipeline')
    tmp = tempfile.mkdtemp(prefix='probar-pipeline-')
    amb_ok = escribir(os.path.join(tmp, 'amb', 'ambientes.md'), CAB_AMB + FILA_PRUEBA + FILA_PROD)
    amb_sin_prod = escribir(os.path.join(tmp, 'amb', 'sin-prod.md'), CAB_AMB + FILA_PRUEBA)
    amb_molde = escribir(os.path.join(tmp, 'amb', 'molde.md'), CAB_AMB + FILA_MOLDE)

    # ---- sin pipeline, y lo que no se puede leer
    vacio = repo_con(tmp, 'sin-pipeline', {'README.md': '# nada\n'})
    rc, out = correr(vacio)
    caso('repositorio sin pipeline: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
    rc, out = correr(os.path.join(tmp, 'no-existe'))
    caso('la ruta no existe: SIN DATOS (2)', rc == 2 and 'SIN DATOS' in out, out[:300])
    r = repo_con(tmp, 'wf-vacio', {'.github/workflows/ci.yml': '\n# solo un comentario\n'})
    rc, j, out = correr_json(r)
    caso('un workflow vacio: SIN DATOS (2), no OK', rc == 2 and j.get('estado') == 'SIN DATOS', out[:300])

    # ---- el camino feliz y sus falsos positivos
    r = repo_con(tmp, 'bueno', {'.github/workflows/ci.yml': WF_BUENO})
    rc, j, out = correr_json(r, *CONFIRMADA)
    caso('workflow sano, con la plataforma confirmada a mano: sale 0 y P1 a P8 sin HALLAZGO', rc == 0 and j.get('estado') == 'OK'
         and all(chk(j, 'P%d' % k)['estado'] in ('OK', 'AVISO', 'NO APLICA') for k in range(1, 9)),
         [(c.get('id'), c.get('estado'), c.get('hallazgos')) for c in j.get('chequeos', [])] or out[:400])
    caso('--plataforma-confirmada: P9 dice quien lo confirmo y que este script no lo miro',
         'lider tecnico' in chk(j, 'P9')['detalle'] and 'a mano' in chk(j, 'P9')['detalle'], chk(j, 'P9'))
    rc, j, out = correr_json(r)
    caso('workflow sano sin --plataforma-confirmada: el total es SIN DATOS (2), nunca OK, porque P9 no se miro',
         rc == 2 and j.get('estado') == 'SIN DATOS' and j.get('estado_yaml') == 'OK', out[:300])
    rc, out = correr(r)
    caso('la primera linea dice "OK en el YAML; P9 SIN DATOS"', 'OK en el YAML; P9 SIN DATOS' in out.splitlines()[0], out[:300])
    rc, j, out = correr_json(r, '--plataforma-confirmada', '  ')
    caso('--plataforma-confirmada vacio no confirma nada: SIN DATOS (2)', rc == 2, out[:300])
    rc, j, out = correr_json(r)
    caso('P9 (lo que vive en la plataforma) es siempre SIN DATOS (no se pudo mirar)',
         chk(j, 'P9')['estado'] == 'SIN DATOS' and 'no se pudo mirar' in chk(j, 'P9')['detalle'], chk(j, 'P9'))
    caso('FP P1/P2: "uses:" y "permissions:" adentro de un run no cuentan',
         chk(j, 'P1')['estado'] == 'OK' and 'algo/raro' not in texto_de(chk(j, 'P2')), texto_de(chk(j, 'P2')))
    caso('FP P2: un uses comentado no cuenta, y una accion local (./) esta fijada por el repo',
         chk(j, 'P2')['estado'] == 'OK', texto_de(chk(j, 'P2')))
    caso('FP P4: un numero de PR en un run, y el titulo pasado por env, no son inyeccion', chk(j, 'P4')['estado'] == 'OK', texto_de(chk(j, 'P4')))
    caso('FP P5: secrets.X, una URL y un numero en una variable con TOKEN no son secretos escritos; un comentario tampoco',
         chk(j, 'P5')['estado'] == 'OK', texto_de(chk(j, 'P5')))
    caso('FP P6: kubectl get (solo lectura) no es un despliegue', chk(j, 'P6')['estado'] == 'OK', texto_de(chk(j, 'P6')))
    caso('FP P8: checkout con persist-credentials: false no avisa', chk(j, 'P8')['estado'] == 'OK', texto_de(chk(j, 'P8')))
    rc, out = correr(r)
    caso('texto: termina con lo que no mira (YAML por lineas, sin anclas)',
         'Lo que este script NO mira:' in out.strip().splitlines()[-1] and 'anclas' in out, out[-300:])

    # ---- GitHub: cada HALLAZGO
    r = repo_con(tmp, 'malo', {'.github/workflows/malo.yml': WF_MALO})
    rc, j, out = correr_json(r)
    caso('workflow con problemas: sale 1 (HALLAZGO)', rc == 1 and j.get('estado') == 'HALLAZGO', out[:300])
    caso('P1: permissions: write-all es HALLAZGO', chk(j, 'P1')['estado'] == 'HALLAZGO' and 'write-all' in texto_de(chk(j, 'P1')))
    p2 = texto_de(chk(j, 'P2'))
    caso('P2: una accion por etiqueta (@v4) es HALLAZGO, con archivo y linea',
         chk(j, 'P2')['estado'] == 'HALLAZGO' and 'actions/checkout@v4' in p2 and 'malo.yml:9' in p2, p2)
    caso('P2: un workflow reutilizable por rama (@main) es HALLAZGO', 'deploy.yml@main' in p2, p2)
    caso('P2: una imagen sin digest es AVISO, no HALLAZGO', any('node:20' in x for x in chk(j, 'P2')['avisos'])
         and not any('node:20' in x for x in chk(j, 'P2')['hallazgos']), chk(j, 'P2'))
    caso('P3: pull_request_target con checkout del codigo del PR es HALLAZGO', chk(j, 'P3')['estado'] == 'HALLAZGO')
    p4 = chk(j, 'P4')
    caso('P4: github.event.issue.title en un run y comment.body en github-script son HALLAZGO',
         p4['estado'] == 'HALLAZGO' and len(p4['hallazgos']) == 2, p4)
    caso('P5: AZURE_CREDENTIALS es HALLAZGO (usar identidad federada)', chk(j, 'P5')['estado'] == 'HALLAZGO'
         and 'AZURE_CREDENTIALS' in texto_de(chk(j, 'P5')))
    caso('P6: un paso de despliegue sin environment es HALLAZGO', chk(j, 'P6')['estado'] == 'HALLAZGO'
         and 'deploy' in texto_de(chk(j, 'P6')), chk(j, 'P6'))
    p7 = chk(j, 'P7')
    caso('P7: continue-on-error en los tests es HALLAZGO; en otro paso, AVISO',
         p7['estado'] == 'HALLAZGO' and len(p7['hallazgos']) == 1 and any('Subir' in x for x in p7['avisos']), p7)
    p8 = texto_de(chk(j, 'P8'))
    caso('P8: secrets: inherit, checkout sin persist-credentials y despliegue sin concurrency son AVISO',
         chk(j, 'P8')['estado'] == 'AVISO' and 'inherit' in p8 and 'persist-credentials' in p8 and 'concurrency' in p8, p8)

    r = repo_con(tmp, 'sin-permisos', {'.github/workflows/a.yml': WF_SIN_PERMISOS})
    rc, j, out = correr_json(r)
    caso('P1: sin permissions arriba y un job sin los suyos: HALLAZGO que nombra el job',
         chk(j, 'P1')['estado'] == 'HALLAZGO' and "'a'" in texto_de(chk(j, 'P1')) and "'b'" not in texto_de(chk(j, 'P1')), chk(j, 'P1'))
    r = repo_con(tmp, 'por-job', {'.github/workflows/a.yml': WF_PERMISOS_POR_JOB})
    rc, j, out = correr_json(r)
    caso('FP P1: sin permissions arriba pero cada job declara los suyos: OK', chk(j, 'P1')['estado'] == 'OK', chk(j, 'P1'))
    r = repo_con(tmp, 'escritura', {'.github/workflows/a.yml': WF_ESCRITURA_ARRIBA})
    rc, j, out = correr_json(r)
    caso('P1: escritura a nivel workflow (contents: write) es HALLAZGO', chk(j, 'P1')['estado'] == 'HALLAZGO'
         and 'contents' in texto_de(chk(j, 'P1')), chk(j, 'P1'))
    r = repo_con(tmp, 'prt', {'.github/workflows/a.yml': WF_PRT_SIN_REF})
    rc, j, out = correr_json(r, *CONFIRMADA)
    caso('FP P3: pull_request_target con el checkout por defecto (la base) es AVISO, no HALLAZGO',
         chk(j, 'P3')['estado'] == 'AVISO' and rc == 0, chk(j, 'P3'))
    r = repo_con(tmp, 'anclas', {'.github/workflows/a.yml': WF_ANCLAS})
    rc, j, out = correr_json(r)
    caso('un workflow con anclas de YAML: AVISO de lo que no se ve', any('ancla' in x for x in j.get('avisos', [])), j.get('avisos'))

    # ---- lockfile
    wf_tag = WF_BUENO.replace('actions/checkout@%s # v4.4.0' % SHA, 'actions/checkout@v4.4.0')
    lock = ("version: 'v0.0.3'\nworkflows:\n  '.github/workflows/ci.yml':\n    - 'actions/checkout@v4.4.0'\ndependencies:\n"
            "  'actions/checkout@v4.4.0':\n    ref: 'v4.4.0'\n    commit: '%s'\n" % SHA)
    r = repo_con(tmp, 'lock', {'.github/workflows/ci.yml': wf_tag, '.github/workflows/actions.lock': lock})
    rc, j, out = correr_json(r)
    caso('P2: una accion por etiqueta cubierta por actions.lock es OK', chk(j, 'P2')['estado'] == 'OK', chk(j, 'P2'))
    r = repo_con(tmp, 'lock-otro', {'.github/workflows/ci.yml': wf_tag, '.github/workflows/actions.lock': lock.replace('ci.yml', 'otro.yml')})
    rc, j, out = correr_json(r)
    caso('P2: con un actions.lock que no incluye ese workflow, la etiqueta sigue siendo HALLAZGO', chk(j, 'P2')['estado'] == 'HALLAZGO', chk(j, 'P2'))

    # ---- P6: los nombres de ambiente contra la ficha
    r = repo_con(tmp, 'env', {'.github/workflows/a.yml': WF_ENV % 'Produccion'})
    rc, j, out = correr_json(r, "--ambientes", amb_ok, *CONFIRMADA)
    caso('P6: despliegue con environment que figura en la ficha: OK', chk(j, 'P6')['estado'] == 'OK' and rc == 0, chk(j, 'P6'))
    rc, j, out = correr_json(r, '--ambientes', amb_sin_prod)
    caso('P6: environment que no figura en la ficha de ambientes: HALLAZGO', chk(j, 'P6')['estado'] == 'HALLAZGO'
         and 'Produccion' in texto_de(chk(j, 'P6')), chk(j, 'P6'))
    rc, j, out = correr_json(r, '--ambientes', amb_molde)
    caso('P6: con la ficha de ambientes en molde, el nombre no se puede comprobar: SIN DATOS (2)',
         chk(j, 'P6')['estado'] == 'SIN DATOS' and rc == 2, chk(j, 'P6'))
    r = repo_con(tmp, 'env-dinamico', {'.github/workflows/a.yml': WF_ENV % '${{ inputs.ambiente }}'})
    rc, j, out = correr_json(r, '--ambientes', amb_ok)
    caso('P6: un environment que se arma en la corrida: AVISO', chk(j, 'P6')['estado'] == 'AVISO', chk(j, 'P6'))

    # ---- GitLab
    r = repo_con(tmp, 'gitlab', {'.gitlab-ci.yml': GITLAB})
    rc, j, out = correr_json(r, '--ambientes', amb_ok)
    p2 = chk(j, 'P2')
    caso('GitLab: detecta la plataforma', 'gitlab' in j.get('plataformas', {}), j.get('plataformas'))
    caso('GitLab P2: include de proyecto sin ref o por rama, componente @~latest y remote sin integrity son HALLAZGO; '
         'con SHA, version completa, plantilla o integrity, no',
         p2['estado'] == 'HALLAZGO' and len(p2['hallazgos']) == 4 and any('~latest' in x for x in p2['hallazgos'])
         and any('ci.yml' in x and 'integrity' in x for x in p2['hallazgos']) and any('ref main' in x for x in p2['hallazgos'])
         and not any('fijo.yml' in x for x in p2['hallazgos']), p2)
    caso('GitLab P2: un include con version parcial (ref v2) es AVISO', any('v2' in x and 'parcial' in x for x in p2['avisos']), p2)
    caso('GitLab: sin workflow:rules es AVISO (en P8)', any('workflow:rules' in x for x in chk(j, 'P8')['avisos']), chk(j, 'P8'))
    caso('FP GitLab P6: la produccion limitada a una ref protegida (aunque tenga when: manual) no es HALLAZGO',
         not any('deploy-prod' in x for x in chk(j, 'P6')['hallazgos']), chk(j, 'P6'))
    caso('GitLab P9: dice que lo que vive en la plataforma lo mide auditar-gitlab.py (sin correrlo)',
         'bin/auditar-gitlab.py proyecto --ruta' in chk(j, 'P9')['detalle'], chk(j, 'P9'))
    caso('GitLab P2: la imagen sin digest es AVISO', any('python:3.12-slim' in x for x in p2['avisos']), p2)
    p5 = chk(j, 'P5')
    caso('GitLab P5: una contrasena escrita en variables es HALLAZGO, sin mostrar el valor; una que viene de otra variable, no',
         p5['estado'] == 'HALLAZGO' and len(p5['hallazgos']) == 1 and 'DB_PASSWORD' in p5['hallazgos'][0]
         and 'no-va-aca' not in out, p5)
    p6 = chk(j, 'P6')
    caso('GitLab P6: un job que despliega sin environment es HALLAZGO; la plantilla oculta (.plantilla) no es un job',
         p6['estado'] == 'HALLAZGO' and any('desplegar' in x for x in p6['hallazgos'])
         and not any('plantilla' in x for x in p6['hallazgos']) and not any('deploy-prod' in x for x in p6['hallazgos']), p6)
    p7 = chk(j, 'P7')
    caso('GitLab P7: allow_failure: true en los tests es HALLAZGO; allow_failure: false no',
         p7['estado'] == 'HALLAZGO' and len(p7['hallazgos']) == 1 and 'tests' in p7['hallazgos'][0], p7)
    caso('GitLab P8: un job con environment sin resource_group es AVISO', any('resource_group' in x for x in chk(j, 'P8')['avisos']), chk(j, 'P8'))
    caso('GitLab P1, P3 y P4 NO APLICAN en el YAML (viven en la plataforma o son de GitHub)',
         all(chk(j, k)['estado'] == 'NO APLICA' for k in ('P1', 'P3', 'P4')), [chk(j, k)['estado'] for k in ('P1', 'P3', 'P4')])
    caso('FP: un * de un patron del shell en un script de GitLab no es un alias de YAML',
         bool(j) and not any('ancla' in x for x in j.get('avisos', [])), j.get('avisos'))
    caso('FP GitLab: una linea de script con "dos puntos" no se toma por una clave',
         p6['estado'] != 'NO ESTA' and 'deploy: no' not in texto_de(p6) and not any('tests' in x for x in p6['hallazgos']), p6)

    r = repo_con(tmp, 'gitlab-prod', {'.gitlab-ci.yml': GITLAB_PROD})
    rc, j, out = correr_json(r, '--ambientes', amb_ok)
    p6 = chk(j, 'P6')
    caso('GitLab P6: produccion cuya unica barrera es when: manual es HALLAZGO ("la barrera va en la plataforma")',
         any('prod-manual' in x and 'when: manual' in x and 'plataforma' in x for x in p6['hallazgos']), p6)
    caso('GitLab P6: produccion por deployment_tier sin limitarse a una ref protegida es HALLAZGO',
         any('prod-tier' in x and 'ref protegida' in x for x in p6['hallazgos']), p6)
    caso('FP GitLab P6: produccion limitada a $CI_COMMIT_REF_PROTECTED, y un ambiente de prueba con when: manual, no son HALLAZGO',
         not any('prod-protegido' in x or 'prueba-manual' in x for x in p6['hallazgos']), p6)
    caso('FP GitLab P8: con workflow:rules no avisa que falta', not any('workflow:rules' in x for x in chk(j, 'P8')['avisos']), chk(j, 'P8'))

    r = repo_con(tmp, 'gitlab-extra', {'.gitlab-ci.yml': GITLAB_EXTRA})
    rc, j, out = correr_json(r)
    p2, p8 = chk(j, 'P2'), chk(j, 'P8')
    caso('GitLab P2: una imagen con una variable en el nombre es AVISO', any('variable' in x and 'CI_REGISTRY_IMAGE' in x for x in p2['avisos']), p2)
    caso('FP GitLab P2: una imagen fija no avisa por variable', not any('variable' in x and 'python:3.12' in x for x in p2['avisos']), p2)
    caso('GitLab P2: pull_policy: if-not-present es AVISO; always no', sum(1 for x in p2['avisos'] if 'pull_policy' in x) == 1, p2)
    caso('GitLab P2: curl ... | sh es HALLAZGO; curl ... | jq no',
         len([x for x in p2['hallazgos'] if 'curl' in x]) == 1 and 'instalar.sh' in ' '.join(p2['hallazgos']), p2)
    caso('GitLab P8: docker:dind y el socket de Docker son AVISO (piden un runner privilegiado); postgres no',
         any('dind' in x for x in p8['avisos']) and any('docker.sock' in x for x in p8['avisos'])
         and not any('postgres' in x for x in p8['avisos']), p8)
    caso('GitLab P8: trigger con forward de pipeline_variables y con strategy: depend son AVISO; un trigger simple no',
         any('pipeline_variables' in x for x in p8['avisos']) and any('strategy: depend' in x for x in p8['avisos'])
         and not any('abajo-simple' in x for x in p8['avisos']), p8)
    caso('GitLab P8: only/except es AVISO; rules no', any('construir' in x and 'only' in x for x in p8['avisos'])
         and not any('publicar-otro' in x for x in p8['avisos']), p8)
    caso('GitLab P8: release con la imagen de release-cli es AVISO; release con otra imagen no',
         any("'publicar'" in x and 'release-cli' in x for x in p8['avisos']), p8)
    rc, j, out = correr_json(os.path.join(tmp, 'bueno'))
    caso('las reglas propias de GitLab no se aplican a un repo sin GitLab: su P9 no nombra auditar-gitlab.py',
         bool(j) and 'auditar-gitlab' not in chk(j, 'P9')['detalle'], chk(j, 'P9'))

    # ---- CI Lint de la instancia (GitLab), por archivo
    r = repo_con(tmp, 'gitlab-lint', {'.gitlab-ci.yml': 'workflow:\n  rules:\n    - if: $CI_COMMIT_BRANCH\ntests:\n  script:\n    - pytest\n'})
    rc, j, out = correr_json(r, *CONFIRMADA)
    caso('sin --lint-json: P10 es SIN DATOS y no cambia la salida', chk(j, 'P10')['estado'] == 'SIN DATOS' and rc == 0, (rc, chk(j, 'P10')))
    lint_ok = escribir(os.path.join(tmp, 'rep', 'lint-ok.json'), json.dumps({'valid': True, 'errors': [], 'warnings': [], 'includes': [
        {'type': 'local', 'location': 'ci/a.yml', 'extra': {}},
        {'type': 'file', 'location': '/ci/b.yml', 'extra': {'project': 'grupo/p', 'ref': SHA}},
        {'type': 'remote', 'location': 'https://example.com/raw/%s/c.yml' % SHA, 'extra': {}}]}))
    rc, j, out = correr_json(r, "--lint-json", lint_ok, *CONFIRMADA)
    caso('FP P10: CI Lint valido, con includes de otro proyecto y remotos por SHA: OK', chk(j, 'P10')['estado'] == 'OK' and rc == 0, chk(j, 'P10'))
    lint_mal = escribir(os.path.join(tmp, 'rep', 'lint-mal.json'), json.dumps({'valid': 'false', 'errors': ['jobs config should contain at least one visible job'],
        'includes': [{'type': 'file', 'location': '/ci/b.yml', 'extra': {'project': 'grupo/p', 'ref': 'main'}},
                     {'type': 'remote', 'location': 'https://example.com/c.yml', 'extra': {}}]}))
    rc, j, out = correr_json(r, '--lint-json', lint_mal)
    p10 = chk(j, 'P10')
    caso('P10: valid en falso (aunque venga como texto) y dos includes sin SHA: tres HALLAZGO, sale 1',
         p10['estado'] == 'HALLAZGO' and len(p10['hallazgos']) == 3 and rc == 1, p10)
    lint_roto = escribir(os.path.join(tmp, 'rep', 'lint-roto.json'), '{"errors": []}')
    rc, j, out = correr_json(r, '--lint-json', lint_roto)
    caso('P10: una respuesta de CI Lint sin "valid": SIN DATOS y sale 2 (se pidio y no se pudo mirar)',
         chk(j, 'P10')['estado'] == 'SIN DATOS' and rc == 2, chk(j, 'P10'))
    rc, j, out = correr_json(os.path.join(tmp, 'bueno'), '--lint-json', lint_ok)
    caso('P10 sin GitLab: NO APLICA', chk(j, 'P10')['estado'] == 'NO APLICA', chk(j, 'P10'))

    # ---- Azure Pipelines
    r = repo_con(tmp, 'azure', {'azure-pipelines.yml': AZURE})
    rc, j, out = correr_json(r, '--ambientes', amb_ok)
    p2 = chk(j, 'P2')
    caso('Azure: detecta la plataforma', 'azure' in j.get('plataformas', {}), j.get('plataformas'))
    caso('Azure P2: un repositorio de plantillas por rama es HALLAZGO; por tag, no',
         p2['estado'] == 'HALLAZGO' and len(p2['hallazgos']) == 1 and 'plantillas' in p2['hallazgos'][0], p2)
    p5 = chk(j, 'P5')
    caso('Azure P5: API_KEY escrita y el nombre ARM_CLIENT_SECRET son HALLAZGO, sin mostrar el valor',
         p5['estado'] == 'HALLAZGO' and len(p5['hallazgos']) == 2 and 'abc123secreto' not in out, p5)
    p6 = chk(j, 'P6')
    caso('Azure P6: una tarea de despliegue en un job comun y un deployment sin environment son HALLAZGO',
         p6['estado'] == 'HALLAZGO' and len(p6['hallazgos']) == 2 and any('desplegar' in x for x in p6['hallazgos'])
         and any('test' in x for x in p6['hallazgos']), p6)
    caso('Azure P7: continueOnError en dotnet test es HALLAZGO', chk(j, 'P7')['estado'] == 'HALLAZGO', chk(j, 'P7'))
    caso('Azure P8: persistCredentials: true es AVISO', any('persistCredentials' in x for x in chk(j, 'P8')['avisos']), chk(j, 'P8'))

    # ---- analisis profundo (herramientas externas): solo si se pide
    r = repo_con(tmp, 'profundo', {'.github/workflows/ci.yml': WF_BUENO})
    rc, j, out = correr_json(r, *CONFIRMADA)
    caso('sin --profundo: el analisis profundo es SIN DATOS (no se pidio) y no cambia la salida',
         rc == 0 and all('no se pidio' in c.get('detalle', '') for c in j.get('profundo', [])) and j.get('profundo'), j.get('profundo'))
    sin_path = dict(os.environ, PATH=os.path.join(tmp, 'path-vacio'))
    os.makedirs(sin_path['PATH'], exist_ok=True)
    rc, j, out = correr_json(r, '--profundo', env=sin_path)
    caso('--profundo sin las herramientas instaladas: esa parte es SIN DATOS y sale 2, nunca 0',
         rc == 2 and herramienta(j, 'zizmor')['estado'] == 'SIN DATOS' and 'no esta instalada' in herramienta(j, 'zizmor')['detalle'], j.get('profundo'))
    zz = escribir(os.path.join(tmp, 'rep', 'zizmor.json'), json.dumps([
        {'ident': 'template-injection', 'desc': 'code injection via template expansion',
         'determinations': {'confidence': 'High', 'severity': 'High', 'persona': 'Regular'},
         'locations': [{'symbolic': {'key': {'Local': {'given_path': '.github/workflows/ci.yml'}}},
                        'concrete': {'location': {'start_point': {'row': 6, 'column': 8}}}}]},
        {'ident': 'artipacked', 'desc': 'credential persistence', 'determinations': {'severity': 'Low'},
         'locations': [{'symbolic': {'key': {'Local': {'given_path': '.github/workflows/ci.yml'}}},
                        'concrete': {'location': {'start_point': {'row': 11, 'column': 8}}}}]}]))
    al = escribir(os.path.join(tmp, 'rep', 'actionlint.json'), json.dumps([
        {'message': 'shellcheck reported issue', 'filepath': '.github/workflows/ci.yml', 'line': 20, 'column': 9, 'kind': 'shellcheck'},
        {'message': '"github.event.issue.title" is potentially untrusted', 'filepath': '.github/workflows/ci.yml', 'line': 9,
         'column': 3, 'kind': 'expression'}]))
    po = escribir(os.path.join(tmp, 'rep', 'poutine.json'), json.dumps({
        'rules': {'untrusted_checkout_exec': {'id': 'untrusted_checkout_exec', 'level': 'error', 'title': 'x'},
                  'pr_runs_on_self_hosted': {'id': 'pr_runs_on_self_hosted', 'level': 'warning', 'title': 'y'}},
        'findings': [{'rule_id': 'untrusted_checkout_exec', 'purl': 'pkg:github/x/y', 'meta': {'path': '.github/workflows/ci.yml', 'line': 12}},
                     {'rule_id': 'pr_runs_on_self_hosted', 'purl': 'pkg:github/x/y', 'meta': {'path': '.github/workflows/ci.yml', 'line': 3}}]}))
    rc, j, out = correr_json(r, '--reporte-zizmor', zz, '--reporte-actionlint', al, '--reporte-poutine', po)
    z, a, p = herramienta(j, 'zizmor'), herramienta(j, 'actionlint'), herramienta(j, 'poutine')
    caso('reporte de zizmor: severidad alta es HALLAZGO, baja es AVISO, con archivo y linea (la fila 0 es la linea 1)',
         z['estado'] == 'HALLAZGO' and len(z['hallazgos']) == 1 and 'ci.yml:7' in z['hallazgos'][0] and len(z['avisos']) == 1, z)
    caso('reporte de actionlint: shellcheck es AVISO, una expresion no confiable es HALLAZGO',
         a['estado'] == 'HALLAZGO' and len(a['hallazgos']) == 1 and len(a['avisos']) == 1, a)
    caso('reporte de poutine: nivel error es HALLAZGO, warning es AVISO', p['estado'] == 'HALLAZGO' and len(p['hallazgos']) == 1
         and len(p['avisos']) == 1, p)
    caso('con un reporte externo con hallazgos, la salida es 1', rc == 1 and j.get('estado') == 'HALLAZGO', out[:300])
    vacio_rep = escribir(os.path.join(tmp, 'rep', 'vacio.json'), '')
    rc, j, out = correr_json(r, '--reporte-zizmor', vacio_rep)
    caso('un reporte vacio no es "cero hallazgos": SIN DATOS (2)', herramienta(j, 'zizmor')['estado'] == 'SIN DATOS' and rc == 2,
         herramienta(j, 'zizmor'))
    roto = escribir(os.path.join(tmp, 'rep', 'roto.json'), '{esto no es json')
    rc, j, out = correr_json(r, '--reporte-poutine', roto)
    caso('un reporte que no se puede leer: SIN DATOS (2)', herramienta(j, 'poutine')['estado'] == 'SIN DATOS' and rc == 2, herramienta(j, 'poutine'))
    cero = escribir(os.path.join(tmp, 'rep', 'cero.json'), '[]')
    rc, j, out = correr_json(r, "--reporte-zizmor", cero, *CONFIRMADA)
    caso('un reporte de zizmor que corrio y no encontro nada: OK', herramienta(j, 'zizmor')['estado'] == 'OK' and rc == 0, herramienta(j, 'zizmor'))
    r_gl = repo_con(tmp, 'solo-gitlab', {'.gitlab-ci.yml': 'tests:\n  script:\n    - pytest\n'})
    rc, j, out = correr_json(r_gl, '--profundo', env=sin_path)
    caso('--profundo sin workflows de GitHub: zizmor y actionlint NO APLICAN; poutine (las tres plataformas) si',
         herramienta(j, 'zizmor')['estado'] == 'NO APLICA' and herramienta(j, 'actionlint')['estado'] == 'NO APLICA'
         and herramienta(j, 'poutine')['estado'] == 'SIN DATOS', j.get('profundo'))

    try:
        spec = importlib.util.spec_from_file_location('verificar_pipeline_prueba', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        comandos = [mod.comando(h, r) for h in ('zizmor', 'actionlint', 'poutine')]
        caso('los comandos de las herramientas no llevan ninguna opcion que cambie algo (lista negra)',
             all(mod.seguro(c) for c in comandos) and not mod.seguro(['zizmor', '--fix', r]) and not mod.seguro(['poutine', 'analyze_org', 'x'])
             and '--offline' in comandos[0], comandos)
    except Exception as e:  # noqa: BLE001
        caso('los comandos de las herramientas no llevan ninguna opcion que cambie algo (lista negra)', False, e)

    # ---- arreglos F1
    r = repo_con(tmp, 'gitlab-f1', {'.gitlab-ci.yml': GITLAB_F1})
    rc, j, out = correr_json(r, '--ambientes', amb_ok)
    rc_t, out_t = correr(r, '--ambientes', amb_ok)
    p2, p5, p6 = chk(j, 'P2'), chk(j, 'P5'), chk(j, 'P6')
    caso('ningun token, clave ni parametro plantado aparece en la salida (texto y JSON)',
         bool(j) and not any(x in out or x in out_t for x in PLANTADOS_F1), [x for x in PLANTADOS_F1 if x in out or x in out_t])
    caso('include remote: se muestra solo esquema, host y ruta (sin usuario, clave ni query)',
         any('https://example.com/ci.yml' in x and 'integrity' in x for x in p2['hallazgos']) and 'private_token' not in out, p2)
    caso('include en estilo flujo ({ project: ..., file: ... }) se mira: sin ref es HALLAZGO; con SHA y file en lista, no',
         any('grupo/flujo' in x and 'sin ref' in x for x in p2['hallazgos']) and not any('grupo/fijo' in x for x in p2['hallazgos']), p2)
    caso('P5: STORAGE_ACCOUNT_KEY y DB_CONNECTION_STRING escritos en variables son HALLAZGO (secretos.sensible)',
         any('STORAGE_ACCOUNT_KEY' in x for x in p5['hallazgos']) and any('DB_CONNECTION_STRING' in x for x in p5['hallazgos']), p5)
    caso('P5: un token con formato conocido en un script es HALLAZGO, sin el valor',
         any('token de GitLab' in x for x in p5['hallazgos']), p5)
    caso('P5: de un valor de menos de 16 caracteres no se muestra huella; de uno largo, si',
         any('CORTA_PASSWORD' in x and 'huella' not in x for x in p5['hallazgos'])
         and any('STORAGE_ACCOUNT_KEY' in x and 'huella' in x for x in p5['hallazgos']), p5)
    caso('GitLab P6: produccion por patron del nombre (production-ar, PRD) sin ref protegida es HALLAZGO',
         any("'prod-ar'" in x and 'produccion' in x for x in p6['hallazgos'])
         and any("'prd-falso'" in x and 'produccion' in x for x in p6['hallazgos']), p6)
    caso('GitLab P6: $CI_COMMIT_REF_PROTECTED == "false", o nombrado en un echo, no limita a una ref protegida',
         any("'prd-falso'" in x and 'ref protegida' in x for x in p6['hallazgos']), p6)
    r = repo_con(tmp, 'gitlab-flujo-roto', {'.gitlab-ci.yml': GITLAB_FLUJO_ROTO})
    rc, j, out = correr_json(r, *CONFIRMADA)
    caso('un include en estilo flujo que no se puede partir: P2 SIN DATOS (2), nunca OK',
         chk(j, 'P2')['estado'] == 'SIN DATOS' and rc == 2, chk(j, 'P2'))
    r = repo_con(tmp, 'gh-servicios', {'.github/workflows/ci.yml': WF_SERVICIOS})
    rc, j, out = correr_json(r)
    caso('FP P5: POSTGRES_PASSWORD de un contenedor de servicio de la prueba es AVISO, no HALLAZGO',
         chk(j, 'P5')['estado'] == 'AVISO' and any('POSTGRES_PASSWORD' in x for x in chk(j, 'P5')['avisos']), chk(j, 'P5'))

    # ---- el propio template
    rc, j, out = correr_json(RAIZ)
    caso('sobre la raiz de este repositorio: ningun HALLAZGO (el template pasa su propia verificacion)',
         bool(j.get('chequeos')) and rc != 1 and j.get('estado') != 'HALLAZGO' and not any(c.get('hallazgos') for c in j.get('chequeos', [])),
         [(c.get('id'), c.get('hallazgos')) for c in j.get('chequeos', []) if c.get('hallazgos')] or out[:300])
    caso('sobre la raiz: ve los dos pipelines del template (GitHub y GitLab)', set(j.get('plataformas', {})) >= {'github', 'gitlab'},
         j.get('plataformas'))
    caso('--json: sale en ASCII puro', bool(j) and all(ord(ch) < 128 for ch in out))

    try:
        with open(SCRIPT, 'rb') as h:
            datos = h.read()
        caso('verificar-pipeline.py es ASCII puro', bool(datos) and all(b < 128 for b in datos))
    except OSError as e:
        caso('verificar-pipeline.py es ASCII puro', False, e)

    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
