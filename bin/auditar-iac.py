#!/usr/bin/env python3
"""Lo ESTATICO de la infraestructura como codigo de un repositorio: Terraform u OpenTofu, Bicep, Dockerfile, Compose
y manifiestos de Kubernetes. SOLO LECTURA.

    python -I bin/auditar-iac.py --repo <ruta>                                  (las reglas propias, sin herramientas)
    python -I bin/auditar-iac.py --repo <ruta> --herramientas                   (ademas, las externas instaladas que apliquen)
    python -I bin/auditar-iac.py --repo <ruta> --herramientas tflint,hadolint   (solo esas)
    python -I bin/auditar-iac.py --repo <ruta> --reporte tflint=tflint.json     (lee un reporte ya corrido; se repite)
    opciones: --binario terraform|tofu   --esquemas-k8s <ubicacion local de los esquemas>   --json

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO   2 = SIN DATOS
  0 = cada regla que aplica miro y dio cero, y cada herramienta pedida corrio y leyo limpio
  1 = alguna regla o alguna herramienta encontro algo (se lista con archivo:linea)
  2 = no hay infraestructura como codigo en la ruta, o algo pedido no se pudo mirar (herramienta ausente, reporte
      vacio o ilegible, sin git para saber que se versiona). Nunca se toma como OK.

LAS REGLAS (expresiones acotadas, no un analizador de HCL completo: cada una tiene su falso positivo en la prueba):
  TF-NO-VERSIONAR        estado (*.tfstate), planes guardados (*.tfplan, *.plan, tfplan, plan.out) o .terraform/
                         versionados, o sin ignorar
  TF-LOCK                una raiz (con backend o con bloque provider) sin .terraform.lock.hcl, o con el lock ignorado
  TF-REQUIRED-VERSION    una carpeta de Terraform sin required_version
  TF-PROVIDER-VERSION    un proveedor de required_providers sin version
  TF-MODULO-VERSION      un modulo de registro sin version, o de git sin ref= (una etiqueta en vez de un SHA: aviso)
  TF-VARIABLE            una variable sin type o sin description
  TF-OUTPUT              una salida sin description
  TF-PROVIDER-EN-MODULO  un bloque provider adentro de modules/
  TF-BACKEND-COMPARTIDO  dos carpetas con el mismo backend (el mismo estado)
  SECRETO-LITERAL        una clave, un token o una contrasena escritos tal cual (en todos los tipos)
  SECRETO-FORMATO        una clave con formato conocido (privada, de proveedor, de repositorio), aun en un comentario
  BICEP-OUTPUT-SEGURO    una salida de Bicep con nombre sensible sin @secure()
  DOCKER-FROM            FROM sin etiqueta o con latest
  DOCKER-USER            la etapa final corre como root (sin USER, o USER root)
  DOCKER-IGNORE          un Dockerfile sin .dockerignore
  IMAGEN-LATEST          una imagen de Compose o de Kubernetes sin etiqueta o con latest
  K8S-SECRET             un Secret de Kubernetes con data o stringData en el repositorio (Base64 no es cifrado)
  RED-ABIERTA            un ingreso abierto a todo internet (0.0.0.0/0, ::/0, * o Internet) hacia un puerto de
                         administracion o de base (22, 3389, 3306, 5432, 1433, 27017, 6379, 9200), un rango que lo
                         incluya o todos los puertos, en aws_security_group (ingress), aws_security_group_rule,
                         aws_vpc_security_group_ingress_rule, azurerm_network_security_rule, azurerm_network_security_group
                         (security_rule) y google_compute_firewall (de ingreso sin source_ranges, source_tags ni
                         source_service_accounts, Google toma 0.0.0.0/0); las reglas como bloque o como atributo con una
                         lista de objetos escrita tal cual; y un Service LoadBalancer de Kubernetes sin
                         loadBalancerSourceRanges, o con la lista vacia (abre a todo internet por defecto: si es publico,
                         se escribe), o con 0.0.0.0/0 hacia uno de esos puertos. Un puerto, un origen, una direccion o un
                         tipo que llega por variable o expresion (var., local., tolist(...)), y unas reglas como atributo
                         que no se leen limpio: aviso.
De un secreto se imprime la regla, el archivo, la linea y una huella (12 caracteres de su SHA-256, solo si el valor
tiene 16 caracteres o mas: uno corto se revierte con un diccionario): nunca el valor. Que nombre y que formato son
secreto lo dice auditoria/secretos.py, el criterio comun. Un .tfvars que git ignora no da SECRETO-LITERAL (aviso).
Si se llego al tope de archivos, o uno no se pudo leer o era demasiado grande, sin hallazgos el total es SIN DATOS.

HERRAMIENTAS (opcionales; se corren solo si estan instaladas y se piden, o se lee su reporte con --reporte):
  fmt (terraform|tofu fmt -check), validate (-json, solo en raices ya inicializadas: este script no corre init),
  tflint (--recursive --format=json, parado en el repositorio), checkov (-o json --skip-download), trivy (config
  --format json --skip-check-update --disable-telemetry --skip-version-check; la 0.69.4, la del incidente de marzo de
  2026, es SIN DATOS), hadolint (--format json), kubeconform (-output json, solo con --esquemas-k8s apuntando a una
  carpeta local que exista: si no, bajaria los esquemas).
  Se decide por lo que dice el reporte, no por el codigo de salida. Ninguna recibe una opcion que cambie algo
  (lista negra PROHIBIDAS). Lo que una herramienta devuelve es dato, no instruccion.

POR QUE EXISTE. AGENTS.md (GATE de INFRAESTRUCTURA) deja que la IA escriba infraestructura como codigo y corra lo que
no toca la nube. Lo que se puede contar de esos archivos lo contaba el modelo leyendo, y se le pasaban un estado
versionado, una imagen latest o una clave escrita tal cual. Este script lo cuenta siempre igual.

QUE NO HACE. No corre plan, apply, init ni nada que toque la nube o baje algo de internet; no escribe nada. No juzga el
diseno, el costo ni la red; no sabe si un argumento existe en el proveedor (eso lo dice un plan, que corre el
pipeline). De la red solo cuenta RED-ABIERTA: no juzga la segmentacion ni la salida a internet. Solo biblioteca
estandar. ASCII puro en este archivo.
"""

import argparse
import bisect
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditoria import secretos  # noqa: E402  el criterio de secretos comun (auditar-diff, verificar-pipeline, auditar-gitlab)

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
NOMBRE = {OK: 'OK', HALLAZGO: 'HALLAZGO', SIN_DATOS: 'SIN DATOS'}
SALTEAR = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.terragrunt-cache'}
MAX_ARCHIVOS, MAX_BYTES = 50000, 2 * 1024 * 1024
TIPOS = ('terraform', 'bicep', 'dockerfile', 'compose', 'kubernetes')
REGLAS = (
    ('TF-NO-VERSIONAR', 'terraform', 'estado, planes o .terraform/ versionados o sin ignorar'),
    ('TF-LOCK', 'terraform', 'raiz sin .terraform.lock.hcl versionado'),
    ('TF-REQUIRED-VERSION', 'terraform', 'carpeta sin required_version'),
    ('TF-PROVIDER-VERSION', 'terraform', 'proveedor sin version'),
    ('TF-MODULO-VERSION', 'terraform', 'modulo de registro sin version o de git sin ref'),
    ('TF-VARIABLE', 'terraform', 'variable sin type o sin description'),
    ('TF-OUTPUT', 'terraform', 'salida sin description'),
    ('TF-PROVIDER-EN-MODULO', 'terraform', 'bloque provider adentro de modules/'),
    ('TF-BACKEND-COMPARTIDO', 'terraform', 'dos carpetas con el mismo backend'),
    ('SECRETO-LITERAL', None, 'clave, token o contrasena escritos tal cual'),
    ('SECRETO-FORMATO', None, 'clave con formato conocido'),
    ('BICEP-OUTPUT-SEGURO', 'bicep', 'salida sensible sin @secure()'),
    ('DOCKER-FROM', 'dockerfile', 'FROM sin etiqueta o con latest'),
    ('DOCKER-USER', 'dockerfile', 'la etapa final corre como root'),
    ('DOCKER-IGNORE', 'dockerfile', 'Dockerfile sin .dockerignore'),
    ('IMAGEN-LATEST', ('compose', 'kubernetes'), 'imagen sin etiqueta o con latest'),
    ('K8S-SECRET', 'kubernetes', 'Secret con data o stringData en el repositorio'),
    ('RED-ABIERTA', ('terraform', 'kubernetes'), 'ingreso abierto a todo internet a un puerto de administracion o de base'),
)
# RED-ABIERTA: los puertos que nunca se abren a todo internet, y los origenes que son "todo internet".
PUERTOS_SENSIBLES = {22: 'SSH', 3389: 'RDP', 3306: 'MySQL', 5432: 'PostgreSQL', 1433: 'SQL Server',
                     27017: 'MongoDB', 6379: 'Redis', 9200: 'Elasticsearch'}
ORIGEN_ABIERTO = {'0.0.0.0/0', '::/0', '*', 'internet'}
TODOS_LOS_PUERTOS = (0, 65535)
# Que nombre guarda un secreto y que formatos lo son: auditoria/secretos.py (secret_name, *_FILE o password_length
# nombran algo, no lo guardan).
FORMATOS = secretos.FORMATOS
sensible = secretos.sensible
MIN_HUELLA = 16            # de un valor mas corto no se imprime la huella: con un diccionario se revierte
# Trivy 0.69.4 es la version del incidente de marzo de 2026: con ella instalada, lo que diga no cuenta.
TRIVY_COMPROMETIDAS = ('0.69.4',)
HERRAMIENTAS = ('fmt', 'validate', 'tflint', 'checkov', 'trivy', 'hadolint', 'kubeconform')
APLICA = {'fmt': ('terraform',), 'validate': ('terraform',), 'tflint': ('terraform',), 'checkov': TIPOS, 'trivy': TIPOS,
          'hadolint': ('dockerfile',), 'kubeconform': ('kubernetes',)}
PROHIBIDAS = {'apply', 'destroy', 'import', 'init', 'plan', 'refresh', 'state', 'taint', 'untaint', 'force-unlock', 'test',
              'login', 'logout', 'push', 'get', 'console', 'workspace', '-write', '-write=true', '--fix', '--init', 'install'}
NO_MIRA = ('si el diseno es bueno y el costo; de la red, solo RED-ABIERTA (no la segmentacion ni la salida a internet)',
           'reglas de red armadas con dynamic, for_each o pasadas a un modulo por variable, reglas escritas como atributo '
           '(ingress = [...], security_rule = [...]) que no son una lista de objetos escrita tal cual (avisa), un protocolo '
           'de AWS por numero fuera de 6 (tcp), 17 (udp), 1 y 58 (ICMP) (avisa), las NACL, los NSG de Bicep, las NetworkPolicy y los '
           'puertos que publica Compose',
           'si los argumentos y los valores existen en el proveedor: eso lo dice un plan, que corre el pipeline',
           'HCL completo (son expresiones acotadas), Terraform escrito en JSON (.tf.json), charts de Helm, Kustomize y Ansible',
           'secretos fuera de estos archivos y en el historial de git (en el diff los mira auditar-diff.py)',
           'las imagenes y las vulnerabilidades de lo que corre (son de la funcion de seguridad)',
           'el pipeline (despliegue-continuo)',
           'la configuracion parcial del backend (-backend-config)')


def limpio(valor, tope=160):
    t = ''.join(c if c.isprintable() else ' ' for c in str(valor))
    t = re.sub(r'\s+', ' ', t).strip()
    t = t[:tope] + ('...' if len(t) > tope else '')
    return t.encode('ascii', 'backslashreplace').decode('ascii')


def huella(valor):
    return hashlib.sha256(valor.encode('utf-8', 'replace')).hexdigest()[:12]


def es_literal(valor):
    v = valor.strip()
    if not v or '${' in v or '%{' in v or '{{' in v or v.startswith(('$', 'ENC[', '/run/secrets/')):
        return False
    return not re.match(r'^<[^<>]+>$', v)


def leer_texto(ruta):
    with open(ruta, 'rb') as h:
        crudo = h.read(MAX_BYTES + 1)
    if crudo[:2] in (b'\xff\xfe', b'\xfe\xff'):
        t = crudo.decode('utf-16', errors='replace')
    else:
        t = crudo.decode('utf-8-sig', errors='replace')
    return t.replace('\r\n', '\n').replace('\r', '\n')


class Lineas(object):
    def __init__(self, texto):
        self.nl = [i for i, c in enumerate(texto) if c == '\n']

    def de(self, pos):
        return bisect.bisect_left(self.nl, pos) + 1


class Informe(object):
    def __init__(self):
        self.hallazgos, self.avisos, self.sin_datos, self.sin_mirar = [], [], {}, []

    def h(self, regla, archivo, linea, detalle, valor=None):
        x = {'regla': regla, 'archivo': limpio(archivo, 200), 'linea': linea, 'detalle': limpio(detalle, 240)}
        if valor is not None and len(valor) >= MIN_HUELLA:
            x['huella'] = huella(valor)
        self.hallazgos.append(x)

    def aviso(self, texto):
        texto = limpio(texto, 300)
        if texto not in self.avisos:
            self.avisos.append(texto)

    def no_mirado(self, texto):
        """Algo que no se miro (el tope de archivos, uno ilegible o muy grande): sin hallazgos, el total no es OK."""
        self.aviso(texto)
        self.sin_mirar.append(limpio(texto, 300))


# ---------------------------------------------------------------- HCL (Terraform u OpenTofu)

RX_HEREDOC = re.compile(r'<<-?\s*([A-Za-z_][\w-]*)[ \t]*\n')


def escanear_hcl(texto):
    """(codigo, esqueleto), del mismo largo que texto. codigo: sin comentarios. esqueleto: ademas sin el contenido de
    los strings, de las interpolaciones y de los heredocs (quedan las comillas que abren y cierran)."""
    n = len(texto)
    cod, esq = list(texto), list(texto)

    def blanco(lst, a, b):
        for k in range(a, min(b, n)):
            if lst[k] != '\n':
                lst[k] = ' '

    pila, prof, i = ['c'], [], 0
    while i < n:
        c, est = texto[i], pila[-1]
        if est == 's':
            adentro = len(pila) > 2 and pila[-2] == 'i'
            if c == '\\':
                blanco(esq, i, i + 2)
                i += 2
                continue
            if c == '"':
                if adentro:
                    blanco(esq, i, i + 1)
                pila.pop()
                i += 1
                continue
            if texto.startswith('${', i) or texto.startswith('%{', i):
                blanco(esq, i, i + 2)
                pila.append('i')
                prof.append(0)
                i += 2
                continue
            blanco(esq, i, i + 1)
            i += 1
            continue
        if est == 'i':
            blanco(esq, i, i + 1)
            if c == '"':
                pila.append('s')
            elif c == '{':
                prof[-1] += 1
            elif c == '}':
                if prof[-1] == 0:
                    pila.pop()
                    prof.pop()
                else:
                    prof[-1] -= 1
            i += 1
            continue
        if c == '#' or texto.startswith('//', i):
            fin = texto.find('\n', i)
            fin = n if fin < 0 else fin
            blanco(cod, i, fin)
            blanco(esq, i, fin)
            i = fin
            continue
        if texto.startswith('/*', i):
            fin = texto.find('*/', i + 2)
            fin = n if fin < 0 else fin + 2
            blanco(cod, i, fin)
            blanco(esq, i, fin)
            i = fin
            continue
        if c == '"':
            pila.append('s')
            i += 1
            continue
        m = RX_HEREDOC.match(texto, i) if c == '<' else None
        if m:
            fin = re.compile(r'(?m)^[ \t]*' + re.escape(m.group(1)) + r'[ \t]*$').search(texto, m.end())
            hasta = fin.start() if fin else n
            blanco(esq, m.end(), hasta)
            i = fin.end() if fin else n
            continue
        i += 1
    return ''.join(cod), ''.join(esq)


RX_BLQ = re.compile(r'[ \t]*([A-Za-z_][\w-]*)((?:[ \t]+(?:"[^"\n]*"|[A-Za-z_][\w-]*))*)[ \t]*\{')
RX_ATTR = re.compile(r'[ \t]*([A-Za-z_][\w-]*)[ \t]*=(?!=)')


def cerrar(esq, abre, fin):
    prof = 0
    for k in range(abre, fin):
        if esq[k] == '{':
            prof += 1
        elif esq[k] == '}':
            prof -= 1
            if prof == 0:
                return k
    return fin


def items(esq, cod, ini, fin):
    """Lo que hay en el primer nivel de [ini, fin): ('bloque', tipo, etiquetas, pos, cuerpo_ini, cuerpo_fin) y
    ('attr', nombre, pos, valor_ini, fin_de_linea)."""
    res, i, prof = [], ini, 0
    while i < fin:
        j = esq.find('\n', i, fin)
        j = fin if j < 0 else j
        if prof == 0:
            m = RX_BLQ.match(esq, i, j)
            if m and m.group(1) not in ('for', 'if'):
                abre = m.end() - 1
                cierra = cerrar(esq, abre, fin)
                res.append(('bloque', m.group(1), re.findall(r'"([^"\n]*)"', cod[m.start(2):m.end(2)]), i, abre + 1, cierra))
                k = esq.find('\n', cierra, fin) if cierra < fin else -1
                i = fin if k < 0 else k + 1
                continue
            m = RX_ATTR.match(esq, i, j)
            if m:
                res.append(('attr', m.group(1), i, m.end(), j))
        for ch in esq[i:j]:
            if ch in '{[(':
                prof += 1
            elif ch in '}])':
                prof = max(0, prof - 1)
        i = j + 1
    return res


def valor_str(esq, cod, ini, fin):
    k = ini
    while k < fin and esq[k] in ' \t':
        k += 1
    if k < fin and esq[k] == '"':
        cierra = esq.find('"', k + 1)
        if cierra > 0:
            return cod[k + 1:cierra]
    return None


def atributos(esq, cod, ini, fin):
    return dict((x[1], x) for x in items(esq, cod, ini, fin) if x[0] == 'attr')


def componentes(rel):
    return rel.split('/')


def analizar_tf(rel, texto, inf, carpetas):
    cod, esq = escanear_hcl(texto)
    lin = Lineas(texto)
    carpeta = os.path.dirname(rel) or '.'
    c = carpetas.setdefault(carpeta, {'required_version': False, 'backends': [], 'raiz': False, 'tf': 0})
    if rel.endswith('.tfvars'):
        secretos_hcl(rel, cod, esq, lin, inf)
        return
    c['tf'] += 1
    partes = componentes(rel)
    en_modulo = 'modules' in partes[:-1] and not set(partes[partes.index('modules'):-1]) & {'examples', 'example', 'tests', 'test'}
    for it in items(esq, cod, 0, len(esq)):
        if it[0] != 'bloque':
            continue
        _, tipo, etiquetas, pos, b0, b1 = it
        nombre = etiquetas[0] if etiquetas else '?'
        if tipo == 'terraform':
            for sub in items(esq, cod, b0, b1):
                if sub[0] == 'attr' and sub[1] == 'required_version':
                    c['required_version'] = True
                elif sub[0] == 'bloque' and sub[1] == 'required_providers':
                    for prov in items(esq, cod, sub[4], sub[5]):
                        if prov[0] != 'attr':
                            continue
                        k = prov[3]
                        while k < sub[5] and esq[k] in ' \t\n':
                            k += 1
                        if k < sub[5] and esq[k] == '{':
                            if 'version' not in atributos(esq, cod, k + 1, cerrar(esq, k, sub[5])):
                                inf.h('TF-PROVIDER-VERSION', rel, lin.de(prov[2]), 'el proveedor %s no fija version' % prov[1])
                elif sub[0] == 'bloque' and sub[1] in ('backend', 'cloud'):
                    c['raiz'] = True
                    attrs = {}
                    for a in items(esq, cod, sub[4], sub[5]):
                        if a[0] == 'attr':
                            v = valor_str(esq, cod, a[3], a[4])
                            if v is not None:
                                attrs[a[1]] = v
                    if attrs:
                        clave = (sub[1], tuple(sub[2]), tuple(sorted(attrs.items())))
                        c['backends'].append((clave, rel, lin.de(sub[3])))
        elif tipo == 'provider':
            c['raiz'] = True
            if en_modulo:
                inf.h('TF-PROVIDER-EN-MODULO', rel, lin.de(pos), 'bloque provider "%s" adentro de un modulo: lo configura la raiz' % nombre)
        elif tipo == 'module':
            attrs = atributos(esq, cod, b0, b1)
            fuente = valor_str(esq, cod, attrs['source'][3], attrs['source'][4]) if 'source' in attrs else None
            if fuente:
                revisar_fuente(rel, lin.de(pos), nombre, fuente, 'version' in attrs, inf)
        elif tipo == 'variable':
            attrs = atributos(esq, cod, b0, b1)
            faltan = [x for x in ('type', 'description') if x not in attrs]
            if faltan:
                inf.h('TF-VARIABLE', rel, lin.de(pos), 'la variable %s no tiene %s' % (nombre, ' ni '.join(faltan)))
            if sensible(nombre) and 'default' in attrs:
                v = valor_str(esq, cod, attrs['default'][3], attrs['default'][4])
                if v is not None and es_literal(v):
                    inf.h('SECRETO-LITERAL', rel, lin.de(attrs['default'][2]), 'la variable %s tiene un valor por defecto escrito tal cual' % nombre, v)
        elif tipo == 'output':
            if 'description' not in atributos(esq, cod, b0, b1):
                inf.h('TF-OUTPUT', rel, lin.de(pos), 'la salida %s no tiene description' % nombre)
        elif tipo == 'resource' and nombre in REGLAS_DE_RED:
            red_tf(rel, nombre, etiquetas[1] if len(etiquetas) > 1 else '?', pos, b0, b1, esq, cod, lin, inf)
    secretos_hcl(rel, cod, esq, lin, inf)


RX_ASIG = re.compile(r'(?<![\w.\-])([A-Za-z_][\w-]*)[ \t]*=(?!=)[ \t]*"')
# Una clave entre comillas de un mapa (tags = { "db_password" = "..." }, o con dos puntos). En el esqueleto el
# contenido de la clave esta en blanco: el nombre se lee del codigo, en las mismas posiciones.
RX_ASIG_COMILLAS = re.compile(r'"([^"\n]*)"[ \t]*(?:=(?!=)|:)[ \t]*"')


def secretos_hcl(rel, cod, esq, lin, inf):
    vistos = [(m.start(1), m.end(1), m.group(1), m.end()) for m in RX_ASIG.finditer(esq)]
    vistos += [(m.start(1), m.end(1), cod[m.start(1):m.end(1)], m.end()) for m in RX_ASIG_COMILLAS.finditer(esq)]
    for ini, _, nombre, desde in sorted(vistos):
        if not sensible(nombre):
            continue
        cierra = esq.find('"', desde)
        valor = cod[desde:cierra] if cierra > 0 else ''
        if es_literal(valor):
            inf.h('SECRETO-LITERAL', rel, lin.de(ini), '%s con valor escrito tal cual' % limpio(nombre, 60), valor)


def revisar_fuente(rel, linea, nombre, fuente, con_version, inf):
    if fuente.startswith(('./', '../')):
        return
    if fuente.startswith(('git::', 'git@', 'github.com/', 'bitbucket.org/')) or '.git' in fuente.split('?')[0].split('//')[-1]:
        ref = re.search(r'[?&]ref=([^&]+)', fuente)
        if not ref:
            inf.h('TF-MODULO-VERSION', rel, linea, 'el modulo %s sale de git sin ref=: trae lo ultimo de la rama' % nombre)
        elif not re.match(r'^[0-9a-f]{40}([0-9a-f]{24})?$', ref.group(1)):
            inf.aviso('%s:%d: el modulo %s se fija por ref=%s: una etiqueta o una rama se pueden mover; lo fijo es el SHA' % (
                rel, linea, nombre, ref.group(1)))
        return
    if re.match(r'^([\w.-]+\.[\w.-]+/)?[\w-]+/[\w-]+/[\w-]+(//.*)?$', fuente) and not con_version:
        inf.h('TF-MODULO-VERSION', rel, linea, 'el modulo %s sale del registro sin version' % nombre)


# ---------------------------------------------------------------- RED-ABIERTA (Terraform u OpenTofu y Kubernetes)

REGLAS_DE_RED = ('aws_security_group', 'aws_security_group_rule', 'aws_vpc_security_group_ingress_rule',
                 'azurerm_network_security_rule', 'azurerm_network_security_group', 'google_compute_firewall')


def valor_crudo(esq, cod, ini, fin):
    """El texto (sin comentarios) del valor de un atributo; una lista entera aunque ocupe varias lineas."""
    k = ini
    while k < fin and esq[k] in ' \t':
        k += 1
    if k < fin and esq[k] == '[':
        prof = 0
        for j in range(k, fin):
            if esq[j] == '[':
                prof += 1
            elif esq[j] == ']':
                prof -= 1
                if prof == 0:
                    return cod[k:j + 1]
        return cod[k:fin]
    j = esq.find('\n', k, fin)
    return cod[k:(fin if j < 0 else j)].strip()


def elementos(crudo):
    """Los elementos de un valor (una lista o uno solo): el texto sin comillas, o None si no es un literal."""
    t = crudo.strip()
    partes = [p.strip() for p in t[1:-1].split(',')] if t.startswith('[') and t.endswith(']') else [t]
    res = []
    for p in partes:
        if not p:
            continue
        if len(p) >= 2 and p[0] == '"' and p[-1] == '"' and '${' not in p:
            res.append(p[1:-1].strip())
        elif re.match(r'^-?\d+$', p):
            res.append(p)
        else:
            res.append(None)
    return res


def rango_puertos(texto):
    """'22' -> (22, 22); '1000-2000' -> (1000, 2000); '*' -> todos; None si no se entiende (una variable)."""
    if texto is None:
        return None
    t = str(texto).strip()
    if t == '*':
        return TODOS_LOS_PUERTOS
    m = re.match(r'^(\d+)(?:\s*-\s*(\d+))?$', t)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    return (min(a, b), max(a, b))


def informar_red(inf, rel, linea, que, origenes, rangos, desconocido, dudoso=None):
    """HALLAZGO si un origen abierto llega a un puerto sensible o a todos; aviso si el puerto no se puede saber, si el
    origen llega por variable o expresion (None en origenes), o si dudoso dice que la direccion o el tipo no se leen."""
    abiertos = sorted(set(o for o in origenes if o is not None and o.lower() in ORIGEN_ABIERTO))
    por_variable = any(o is None for o in origenes)
    if not abiertos and not por_variable:
        return
    todos = any(r[0] <= 1 and r[1] >= 65535 for r in rangos)
    sens = sorted(set(p for p in PUERTOS_SENSIBLES for r in rangos if r[0] <= p <= r[1]))
    destino = 'todos los puertos' if todos else ', '.join('%d (%s)' % (p, PUERTOS_SENSIBLES[p]) for p in sens)
    if (todos or sens) and abiertos and not dudoso:
        inf.h('RED-ABIERTA', rel, linea, '%s: ingreso desde %s hacia %s (la administracion entra por bastion, VPN o un '
                                         'acceso sin puerto abierto; una base no se expone)' % (que, ', '.join(abiertos), destino))
    elif todos or sens:
        inf.aviso('%s:%d: RED-ABIERTA: %s hacia %s, pero %s: no se sabe si abre a todo internet (revisarlo a mano)' % (
            rel, linea, que, destino, dudoso or 'el origen llega por variable o expresion'))
    elif desconocido and abiertos:
        inf.aviso('%s:%d: RED-ABIERTA: %s abre a %s un puerto que llega por variable o un protocolo que no se lee: '
                  'no se sabe cual (revisarlo a mano)' % (rel, linea, que, ', '.join(abiertos)))


def objetos_lista(esq, ini, fin):
    """Los cuerpos (desde, hasta) de una lista de objetos escrita tal cual (ingress = [{ ... }, { ... }]), cada objeto
    en varias lineas; None si el valor no se lee limpio (una variable, un for, una funcion, un objeto en una linea)."""
    k = ini
    while k < fin and esq[k] in ' \t':
        k += 1
    if k >= fin or esq[k] != '[':
        return None
    prof, cierra = 0, None
    for j in range(k, fin):
        if esq[j] == '[':
            prof += 1
        elif esq[j] == ']':
            prof -= 1
            if prof == 0:
                cierra = j
                break
    if cierra is None:
        return None
    res, j = [], k + 1
    while j < cierra:
        if esq[j] in ' \t\n,':
            j += 1
            continue
        if esq[j] != '{':
            return None
        f = cerrar(esq, j, cierra)
        if f >= cierra or '\n' not in esq[j:f]:
            return None
        res.append((j, f))
        j = f + 1
    return res


def red_tf(rel, tipo, nombre, pos, b0, b1, esq, cod, lin, inf):
    """Las reglas de ingreso de un recurso de red de Terraform u OpenTofu, contra RED-ABIERTA."""
    que = '%s "%s"' % (tipo, nombre)

    def lista(attrs, campo, fin):
        return elementos(valor_crudo(esq, cod, attrs[campo][3], fin)) if campo in attrs else []

    def uno(attrs, campo, fin):
        """(esta, valor): valor None si no es un literal."""
        if campo not in attrs:
            return False, None
        v = lista(attrs, campo, fin)
        return True, (v[0] if len(v) == 1 else None)

    def regla_aws(ini, fin, linea, campos_origen, campo_proto, dudoso=None):
        attrs = atributos(esq, cod, ini, fin)
        origenes = sum((lista(attrs, c, fin) for c in campos_origen), [])
        proto = uno(attrs, campo_proto, fin)[1]
        desde, hasta = uno(attrs, 'from_port', fin)[1], uno(attrs, 'to_port', fin)[1]
        rangos, desconocido = [], False
        p = proto.lower() if proto is not None else None
        if p in ('icmp', 'icmpv6', '1', '58'):
            return
        if p in ('-1', 'all'):
            rangos = [TODOS_LOS_PUERTOS]
        elif p in ('tcp', 'udp', '6', '17'):
            r = rango_puertos('%s-%s' % (desde, hasta)) if desde is not None and hasta is not None else None
            rangos, desconocido = ([r], False) if r else ([], True)
        else:
            desconocido = True      # por variable, o un protocolo por numero que este script no lee
        informar_red(inf, rel, linea, que, origenes, rangos, desconocido, dudoso)

    def regla_azure(ini, fin, linea):
        attrs = atributos(esq, cod, ini, fin)
        direccion, acceso = uno(attrs, 'direction', fin)[1], uno(attrs, 'access', fin)[1]
        if (direccion is not None and direccion.lower() != 'inbound') or (acceso is not None and acceso.lower() != 'allow'):
            return
        dudoso = None if direccion is not None and acceso is not None else 'la direccion o el acceso llegan por variable'
        proto = uno(attrs, 'protocol', fin)[1]
        if proto is not None and proto.lower() in ('icmp', 'esp', 'ah'):
            return
        origenes = lista(attrs, 'source_address_prefix', fin) + lista(attrs, 'source_address_prefixes', fin)
        puertos = [rango_puertos(x) for x in lista(attrs, 'destination_port_range', fin) + lista(attrs, 'destination_port_ranges', fin)]
        informar_red(inf, rel, linea, que, origenes, [r for r in puertos if r], not puertos or any(r is None for r in puertos), dudoso)

    if tipo == 'aws_security_group' or tipo == 'azurerm_network_security_group':
        bloque = 'ingress' if tipo == 'aws_security_group' else 'security_rule'

        def una_regla(ini, fin, linea):
            if tipo == 'aws_security_group':
                regla_aws(ini, fin, linea, ('cidr_blocks', 'ipv6_cidr_blocks'), 'protocol')
            else:
                regla_azure(ini, fin, linea)

        for sub in items(esq, cod, b0, b1):
            if sub[0] == 'attr' and sub[1] == bloque:
                objetos = objetos_lista(esq, sub[3], b1)
                if objetos is None:
                    inf.aviso('%s:%d: RED-ABIERTA: %s escribe %s como atributo y no se lee limpio: no se miran (revisarlas a mano)' % (
                        rel, lin.de(sub[2]), que, bloque))
                for desde, hasta in objetos or ():
                    una_regla(desde + 1, hasta, lin.de(desde))
            elif sub[0] != 'bloque':
                continue
            elif sub[1] == bloque:
                una_regla(sub[4], sub[5], lin.de(sub[3]))
            elif sub[1] == 'dynamic' and sub[2][:1] == [bloque]:
                inf.aviso('%s:%d: RED-ABIERTA: %s arma sus reglas con dynamic: no se miran (revisarlas a mano)' % (rel, lin.de(sub[3]), que))
    elif tipo == 'aws_security_group_rule':
        esta, tipo_regla = uno(atributos(esq, cod, b0, b1), 'type', b1)
        if esta and tipo_regla is None:
            regla_aws(b0, b1, lin.de(pos), ('cidr_blocks', 'ipv6_cidr_blocks'), 'protocol', 'el tipo (type) llega por variable')
        elif (tipo_regla or '').lower() == 'ingress':
            regla_aws(b0, b1, lin.de(pos), ('cidr_blocks', 'ipv6_cidr_blocks'), 'protocol')
    elif tipo == 'aws_vpc_security_group_ingress_rule':
        regla_aws(b0, b1, lin.de(pos), ('cidr_ipv4', 'cidr_ipv6'), 'ip_protocol')
    elif tipo == 'azurerm_network_security_rule':
        regla_azure(b0, b1, lin.de(pos))
    elif tipo == 'google_compute_firewall':
        attrs = atributos(esq, cod, b0, b1)
        esta, direccion = uno(attrs, 'direction', b1)
        if (esta and direccion is not None and direccion.upper() != 'INGRESS') or (
                'disabled' in attrs and valor_crudo(esq, cod, attrs['disabled'][3], b1) == 'true'):
            return
        dudoso = 'la direccion llega por variable' if esta and direccion is None else None
        origenes = lista(attrs, 'source_ranges', b1)
        if not any(c in attrs for c in ('source_ranges', 'source_tags', 'source_service_accounts')):
            # El proveedor pide uno de los tres para INGRESS; sin ninguno, Google Cloud toma 0.0.0.0/0.
            origenes = ['0.0.0.0/0']
            que = '%s (sin source_ranges, source_tags ni source_service_accounts: Google toma 0.0.0.0/0)' % que
        for sub in items(esq, cod, b0, b1):
            if sub[0] != 'bloque' or sub[1] != 'allow':
                continue
            a2 = atributos(esq, cod, sub[4], sub[5])
            proto = uno(a2, 'protocol', sub[5])[1]
            p = proto.lower() if proto is not None else None
            p = {'6': 'tcp', '17': 'udp', '132': 'sctp'}.get(p, p)
            rangos, desconocido = [], p is None
            if p == 'all' or (p in ('tcp', 'udp', 'sctp') and 'ports' not in a2):
                rangos = [TODOS_LOS_PUERTOS]
            elif p in ('tcp', 'udp', 'sctp'):
                puertos = [rango_puertos(x) for x in lista(a2, 'ports', sub[5])]
                rangos, desconocido = [r for r in puertos if r], any(r is None for r in puertos)
            informar_red(inf, rel, lin.de(sub[3]), que, origenes, rangos, desconocido, dudoso)


RX_LB_INTERNO = re.compile(r'(?i)^\s+\S*(load-balancer-internal|load-balancer-type|aws-load-balancer-scheme)\S*:\s*["\']?(true|internal)["\']?\s*(#.*)?$')


def hijos_de(lineas, a, b, clave):
    """Los indices de los hijos directos de una clave de primer nivel del documento (spec:, metadata:)."""
    ini = next((i for i in range(a, b) if re.match(r'^%s:\s*(#.*)?$' % clave, lineas[i])), None)
    if ini is None:
        return []
    res, ind = [], None
    for i in range(ini + 1, b):
        l = lineas[i]
        if not l.strip() or l.lstrip().startswith('#'):
            continue
        if sangria(l) == 0:
            break
        ind = sangria(l) if ind is None else ind
        if sangria(l) == ind:
            res.append(i)
    return res


def red_k8s(rel, lineas, a, b, inf):
    """Un Service LoadBalancer: sin rango de origen (o con uno vacio) abre a todo internet por defecto; con 0.0.0.0/0, no
    a un puerto sensible. El type se busca solo en spec (no en metadata.labels)."""
    tipo = next((i for i in hijos_de(lineas, a, b, 'spec') if re.match(r'^\s+type:\s*["\']?LoadBalancer["\']?\s*(#.*)?$', lineas[i])), None)
    if tipo is None or any(RX_LB_INTERNO.match(lineas[i]) for i in range(a, b)):
        return
    origenes = []
    for k in range(a, b):
        m = re.match(r'^(\s*)loadBalancerSourceRanges:\s*(.*)$', lineas[k])
        if m:
            enlinea = re.sub(r'\s+#.*$', '', m.group(2)).strip()
            if enlinea:
                origenes += [x.strip().strip('"\'') for x in enlinea.strip('[]').split(',') if x.strip()]
            else:
                for j in range(k + 1, b):
                    if not lineas[j].strip():
                        continue
                    mm = re.match(r'^\s*-\s*["\']?([^"\'\s#]+)', lineas[j])
                    if not mm or sangria(lineas[j]) < len(m.group(1)):
                        break
                    origenes.append(mm.group(1))
        m = re.match(r'^\s+\S*load-balancer-source-ranges:\s*(.*)$', lineas[k])
        if m:
            origenes += [x.strip() for x in valor_yaml(m.group(1)).split(',') if x.strip()]
    origenes = [o for o in origenes if o.lower() not in ('null', '~')]
    if not origenes:
        inf.h('RED-ABIERTA', rel, tipo + 1, 'Service LoadBalancer sin loadBalancerSourceRanges (o con la lista vacia): abre a todo '
                                          'internet por defecto (si es publico, el rango se escribe, aunque sea 0.0.0.0/0; si no, '
                                          'el balanceador va interno)')
        return
    abiertos = sorted(set(o for o in origenes if o in ('0.0.0.0/0', '::/0')))
    # port: en bloque (- port: 22) o en flujo (ports: [{port: 22}]); targetPort y nodePort no cuentan.
    puertos = set(int(p) for k in range(a, b) for p in re.findall(r'(?<![\w.-])port:\s*["\']?(\d+)', re.sub(r'\s#.*$', '', lineas[k])))
    sens = sorted(p for p in puertos if p in PUERTOS_SENSIBLES)
    if abiertos and sens:
        inf.h('RED-ABIERTA', rel, tipo + 1, 'Service LoadBalancer abierto a %s hacia %s' % (
            ', '.join(abiertos), ', '.join('%d (%s)' % (p, PUERTOS_SENSIBLES[p]) for p in sens)))


# ---------------------------------------------------------------- Bicep

def analizar_bicep(rel, texto, inf):
    lineas = texto.split('\n')
    en_multi = False
    for i, crudo in enumerate(lineas):
        if crudo.count("'''") % 2 == 1:
            en_multi = not en_multi
            continue
        if en_multi:
            continue
        l = crudo
        k = l.find('//')
        if k >= 0 and l[:k].count("'") % 2 == 0:
            l = l[:k]
        m = re.match(r"^\s*param\s+([A-Za-z_]\w*)(?:\s+[A-Za-z_][\w.\[\]]*)?\s*=\s*'((?:[^'\\]|\\.)*)'\s*$", l)
        if m:
            if sensible(m.group(1)) and es_literal(m.group(2)):
                inf.h('SECRETO-LITERAL', rel, i + 1, 'el parametro %s tiene un valor por defecto escrito tal cual' % m.group(1), m.group(2))
            continue
        for p in re.finditer(r"(?<![\w.])([A-Za-z_]\w*)\s*:\s*'((?:[^'\\]|\\.)*)'", l):
            if sensible(p.group(1)) and es_literal(p.group(2)):
                inf.h('SECRETO-LITERAL', rel, i + 1, '%s con valor escrito tal cual' % p.group(1), p.group(2))
        m = re.match(r'^\s*output\s+([A-Za-z_]\w*)\s', l)
        if m and sensible(m.group(1)):
            k, seguro = i - 1, False
            while k >= 0 and (lineas[k].strip().startswith('@') or not lineas[k].strip()):
                seguro = seguro or re.search(r'@(sys\.)?secure\(\)', lineas[k]) is not None
                k -= 1
            if not seguro:
                inf.h('BICEP-OUTPUT-SEGURO', rel, i + 1, 'la salida %s no lleva @secure(): queda en el historial del despliegue' % m.group(1))


# ---------------------------------------------------------------- Dockerfile

def etiqueta(imagen):
    """'digest', la etiqueta, o None si no tiene."""
    if '@' in imagen:
        return 'digest'
    ultimo = imagen.rsplit('/', 1)[-1]
    return (ultimo.split(':', 1)[1] or None) if ':' in ultimo else None


def instrucciones(texto):
    res, lineas, i = [], texto.split('\n'), 0
    while i < len(lineas):
        s = lineas[i].strip()
        if not s or s.startswith('#'):
            i += 1
            continue
        inicio, partes = i + 1, [s]
        while partes[-1].endswith('\\') and i + 1 < len(lineas):
            partes[-1] = partes[-1][:-1]
            i += 1
            sig = lineas[i].strip()
            if not sig.startswith('#'):
                partes.append(sig)
        m = re.match(r'([A-Za-z]+)\s*(.*)$', ' '.join(partes), re.S)
        if m:
            res.append((inicio, m.group(1).upper(), m.group(2).strip()))
            hd = re.search(r'<<-?["\']?([A-Za-z_]\w*)["\']?', m.group(2))
            if hd and m.group(1).upper() in ('RUN', 'COPY'):
                while i + 1 < len(lineas) and lineas[i + 1].strip() != hd.group(1):
                    i += 1
                i += 1
        i += 1
    return res


def partir(args):
    try:
        return shlex.split(args, posix=True)
    except ValueError:
        return args.split()


def es_root(usuario):
    return usuario.split(':', 1)[0].strip().lower() in ('root', '0')


def analizar_dockerfile(rel, texto, inf, raiz_repo, ruta, contador):
    args_globales, etapas = {}, []
    for linea, ins, args in instrucciones(texto):
        if ins == 'ARG' and not etapas:
            for tok in partir(args):
                if '=' in tok:
                    k, v = tok.split('=', 1)
                    args_globales[k] = v
        if ins == 'FROM':
            toks = [t for t in partir(args) if not t.startswith('--')]
            if not toks:
                continue
            imagen = re.sub(r'\$\{(\w+)\}|\$(\w+)', lambda m: args_globales.get(m.group(1) or m.group(2), m.group(0)), toks[0])
            alias = toks[2].lower() if len(toks) >= 3 and toks[1].lower() == 'as' else None
            previas = dict((e['alias'], e) for e in etapas if e['alias'])
            etapa = {'alias': alias, 'imagen': imagen, 'base': previas.get(imagen.lower()), 'usuario': None, 'linea': linea}
            etapas.append(etapa)
            if etapa['base'] is not None or imagen.lower() == 'scratch':
                continue
            if '$' in imagen:
                inf.aviso('%s:%d: FROM con una variable sin valor por defecto: no se puede saber la etiqueta' % (rel, linea))
                continue
            tag = etiqueta(imagen)
            if tag is None or tag == 'latest':
                inf.h('DOCKER-FROM', rel, linea, 'la imagen %s %s' % (imagen, 'no tiene etiqueta' if tag is None else 'usa latest'))
            elif tag != 'digest':
                contador[0] += 1
        elif ins == 'USER' and etapas:
            toks = partir(args)
            etapas[-1]['usuario'] = toks[0] if toks else args
        elif ins in ('ENV', 'ARG'):
            toks = partir(args)
            pares = [t.split('=', 1) for t in toks if '=' in t] if (toks and '=' in toks[0]) else (
                [[toks[0], ' '.join(toks[1:])]] if ins == 'ENV' and len(toks) > 1 else [])
            for k, v in pares:
                if sensible(k) and es_literal(v):
                    inf.h('SECRETO-LITERAL', rel, linea, '%s %s con valor escrito tal cual: queda en la imagen' % (ins, k), v)
    if etapas:
        final, usuario = etapas[-1], None
        e = final
        while e is not None and usuario is None:
            usuario = e['usuario']
            if usuario is None and e['base'] is None and 'nonroot' in (etiqueta(e['imagen']) or ''):
                usuario = 'nonroot'
            e = e['base']
        if usuario is None or es_root(usuario):
            inf.h('DOCKER-USER', rel, final['linea'], 'la etapa final corre como root (%s)' % ('sin USER' if usuario is None else 'USER ' + usuario))
    carpeta = os.path.dirname(ruta)
    if not (os.path.isfile(os.path.join(carpeta, '.dockerignore')) or os.path.isfile(ruta + '.dockerignore')
            or os.path.isfile(os.path.join(raiz_repo, '.dockerignore'))):
        inf.h('DOCKER-IGNORE', rel, None, 'no hay .dockerignore al lado ni en la raiz: el contexto de build lleva todo')


# ---------------------------------------------------------------- YAML (Compose y Kubernetes)

def sangria(l):
    return len(l) - len(l.lstrip(' '))


def valor_yaml(v):
    v = v.strip()
    if v[:1] in ('"', "'"):
        k = v.find(v[0], 1)
        return v[1:k] if k > 0 else v[1:]
    return re.sub(r'\s+#.*$', '', v).strip()


def literal_yaml(crudo):
    c = crudo.strip()
    if not c or c[0] in '|>&*{[' or c.lower() in ('true', 'false', 'yes', 'no', 'null', '~'):
        return None
    v = valor_yaml(c)
    return v if es_literal(v) else None


RX_MAPA = re.compile(r'^\s*(?:-\s+)?([A-Za-z_][\w.-]*)\s*:\s+(\S.*)$')
RX_LISTA = re.compile(r'^\s*-\s+([A-Za-z_][\w.-]*)=(.*)$')
RX_NOMBRE = re.compile(r'^(\s*)-\s+name:\s*(\S.*)$')


def secretos_yaml(rel, lineas, desde, hasta, inf):
    for i in range(desde, hasta):
        l = lineas[i]
        if l.lstrip().startswith('#'):
            continue
        m = RX_MAPA.match(l) or RX_LISTA.match(l)
        if m and sensible(m.group(1)):
            v = literal_yaml(m.group(2))
            if v:
                inf.h('SECRETO-LITERAL', rel, i + 1, '%s con valor escrito tal cual' % m.group(1), v)
        m = RX_NOMBRE.match(l)
        if m and sensible(valor_yaml(m.group(2))):
            for k in range(i + 1, min(i + 8, hasta)):
                if not lineas[k].strip():
                    continue
                if sangria(lineas[k]) <= len(m.group(1)):
                    break
                mv = re.match(r'^\s*value:\s*(.*)$', lineas[k])
                if mv:
                    v = literal_yaml(mv.group(1))
                    if v:
                        inf.h('SECRETO-LITERAL', rel, k + 1, 'la variable %s con valor escrito tal cual' % valor_yaml(m.group(2)), v)
                    break


def revisar_imagen(rel, linea, imagen, inf, contador):
    if not imagen or '$' in imagen or '{{' in imagen:
        return
    tag = etiqueta(imagen)
    if tag is None or tag == 'latest':
        inf.h('IMAGEN-LATEST', rel, linea, 'la imagen %s %s' % (imagen, 'no tiene etiqueta' if tag is None else 'usa latest'))
    elif tag != 'digest':
        contador[0] += 1


def analizar_compose(rel, texto, inf, contador):
    lineas = texto.split('\n')
    inicio = next((i for i, l in enumerate(lineas) if re.match(r'^services:\s*(#.*)?$', l)), None)
    if inicio is not None:
        servicios, ind_srv, actual = [], None, None
        for j in range(inicio + 1, len(lineas)):
            l = lineas[j]
            if not l.strip() or l.lstrip().startswith('#'):
                continue
            ind = sangria(l)
            if ind == 0:
                break
            if ind_srv is None:
                ind_srv = ind
            if ind == ind_srv:
                actual = {'build': False, 'imagen': None, 'hijo': None}
                servicios.append(actual)
            elif actual is not None:
                actual['hijo'] = actual['hijo'] or ind
                m = re.match(r'^\s*(build|image)\s*:\s*(.*)$', l)
                if m and ind == actual['hijo']:
                    if m.group(1) == 'build':
                        actual['build'] = True
                    else:
                        actual['imagen'] = (valor_yaml(m.group(2)), j + 1)
        for s in servicios:
            if s['imagen'] and not s['build']:
                revisar_imagen(rel, s['imagen'][1], s['imagen'][0], inf, contador)
    secretos_yaml(rel, lineas, 0, len(lineas), inf)


def documentos(lineas):
    docs, ini = [], 0
    for i, l in enumerate(lineas):
        if re.match(r'^---(\s|$)', l):
            docs.append((ini, i))
            ini = i + 1
    docs.append((ini, len(lineas)))
    return docs


def es_kubernetes(texto):
    return re.search(r'(?m)^apiVersion:\s*\S', texto) is not None and re.search(r'(?m)^kind:\s*\S', texto) is not None


def analizar_kubernetes(rel, texto, inf, contador, plantillas):
    lineas = texto.split('\n')
    for a, b in documentos(lineas):
        doc = '\n'.join(lineas[a:b])
        kind = re.search(r'(?m)^kind:\s*(\S+)', doc)
        if not kind or not re.search(r'(?m)^apiVersion:\s*\S', doc):
            continue
        if '{{' in doc:
            plantillas.add(rel)
            continue
        kind = kind.group(1).strip('"\'')          # kind: "Service" es el mismo kind
        if kind == 'Secret':
            if re.search(r'(?m)^sops:', doc):
                continue
            for i in range(a, b):
                m = re.match(r'^(data|stringData):\s*(.*)$', lineas[i])
                if not m or m.group(2).strip() not in ('', '{}'):
                    continue
                valores = 0
                for k in range(i + 1, b):
                    if lineas[k].strip() and sangria(lineas[k]) == 0:
                        break
                    mv = re.match(r'^\s+[^\s#][^:]*:\s*(.*)$', lineas[k])
                    if mv and mv.group(1).strip() and not mv.group(1).strip().startswith('ENC['):
                        valores += 1
                if valores:
                    inf.h('K8S-SECRET', rel, i + 1, 'un Secret con %d valor(es) en %s: Base64 no es cifrado' % (valores, m.group(1)))
            continue
        if kind == 'Service':
            red_k8s(rel, lineas, a, b, inf)
        for i in range(a, b):
            m = re.match(r'^\s*(?:-\s+)?image:\s*(\S.*)$', lineas[i])
            if m:
                revisar_imagen(rel, i + 1, valor_yaml(m.group(1)), inf, contador)
        secretos_yaml(rel, lineas, a, b, inf)


# ---------------------------------------------------------------- recorrido y reglas de repositorio

def tipo_de(nombre):
    n = nombre.lower()
    if n.endswith(('.tf', '.tofu', '.tfvars')):
        return 'terraform'
    if n.endswith(('.bicep', '.bicepparam')):
        return 'bicep'
    if (n in ('dockerfile', 'containerfile') or n.startswith('dockerfile.') or n.endswith('.dockerfile')) and not n.endswith('.dockerignore'):
        return 'dockerfile'
    if re.match(r'^(docker-)?compose([.-][\w.-]+)?\.ya?ml$', n):
        return 'compose'
    if n.endswith(('.yaml', '.yml')):
        return 'yaml'
    return None


def es_no_versionable(rel):
    """Estado o plan guardado. Un plan se guarda con el nombre que se le de a -out: tfplan, plan.out o *.plan son los
    de la documentacion y los mas usados, ademas de *.tfplan."""
    n = rel.rsplit('/', 1)[-1].lower()
    return (n.endswith(('.tfstate', '.tfplan', '.plan')) or '.tfstate.' in n
            or n in ('tfplan', 'plan.out', 'tfplan.out'))


def recorrer(repo, inf):
    archivos, dot_terraform, vistos = [], [], 0
    for raiz, dirs, nombres in os.walk(repo):
        base = os.path.relpath(raiz, repo).replace(os.sep, '/')
        base = '' if base == '.' else base + '/'
        quedan = []
        for d in sorted(dirs):
            if d == '.terraform':
                dot_terraform.append(base + d)
            elif d not in SALTEAR:
                quedan.append(d)
        dirs[:] = quedan
        for n in sorted(nombres):
            vistos += 1
            if vistos > MAX_ARCHIVOS:
                inf.no_mirado('el repositorio tiene mas de %d archivos: se miraron los primeros' % MAX_ARCHIVOS)
                return archivos, dot_terraform
            archivos.append(base + n)
    return archivos, dot_terraform


def git(repo, args, entrada=None):
    try:
        r = subprocess.run(['git', '-C', repo] + args, capture_output=True, input=entrada)
    except OSError:
        return None, b''
    return r.returncode, r.stdout


def una_muestra(ruta):
    for raiz, _, nombres in os.walk(ruta):
        for n in nombres:
            return os.path.join(raiz, n)
    return None


def revisar_versionado(repo, archivos, dot_terraform, inf):
    """Estado de TF-NO-VERSIONAR: OK, HALLAZGO o SIN DATOS."""
    rc, sale = git(repo, ['rev-parse', '--is-inside-work-tree'])
    candidatos = [a for a in archivos if es_no_versionable(a)]
    if rc != 0 or sale.strip() != b'true':
        if candidatos or dot_terraform:
            inf.sin_datos['TF-NO-VERSIONAR'] = 'no es un repositorio git (o git no esta): no se sabe si %d archivo(s) de estado, plan o .terraform/ se versionan' % (
                len(candidatos) + len(dot_terraform))
            return SIN_DATOS
        return OK
    rc, sale = git(repo, ['ls-files', '-z'])
    if rc != 0:
        inf.sin_datos['TF-NO-VERSIONAR'] = 'git no pudo listar los archivos versionados'
        return SIN_DATOS
    versionados = [p for p in sale.decode('utf-8', 'replace').split('\0') if p]
    total = 0
    for p in sorted(set(p for p in versionados if es_no_versionable(p) and '.terraform/' not in p) | set(candidatos)):
        if p in versionados:
            inf.h('TF-NO-VERSIONAR', p, None, 'versionado: el estado y los planes pueden tener secretos en texto plano')
            total += 1
        elif not ignorado(repo, p):
            inf.h('TF-NO-VERSIONAR', p, None, 'ni versionado ni ignorado: un git add lo sube (falta en .gitignore)')
            total += 1
    for d in dot_terraform:
        if any(p.startswith(d + '/') for p in versionados):
            inf.h('TF-NO-VERSIONAR', d, None, '.terraform/ versionado: son binarios y modulos bajados por init')
            total += 1
        else:
            muestra = una_muestra(os.path.join(repo, d))
            if muestra and not ignorado(repo, os.path.relpath(muestra, repo).replace(os.sep, '/')):
                inf.h('TF-NO-VERSIONAR', d, None, '.terraform/ ni versionado ni ignorado: un git add lo sube (falta en .gitignore)')
                total += 1
    return HALLAZGO if total else OK


def ignorado(repo, rel):
    rc, _ = git(repo, ['check-ignore', '-q', '--', rel])
    return rc == 0


def reglas_de_carpetas(repo, carpetas, archivos, inf, hay_git):
    versionados = None
    if hay_git:
        rc, sale = git(repo, ['ls-files', '-z'])
        versionados = set(p for p in sale.decode('utf-8', 'replace').split('\0') if p) if rc == 0 else None
    backends = {}
    for carpeta in sorted(carpetas):
        c = carpetas[carpeta]
        if not c['tf']:
            continue
        prefijo = '' if carpeta == '.' else carpeta + '/'
        if not c['required_version']:
            inf.h('TF-REQUIRED-VERSION', prefijo or './', None, 'ninguna configuracion de esta carpeta fija required_version')
        partes = carpeta.split('/')
        if c['raiz'] and not set(partes) & {'modules', 'examples', 'example', 'tests', 'test'}:
            lock = prefijo + '.terraform.lock.hcl'
            if lock not in archivos:
                inf.h('TF-LOCK', prefijo or './', None, 'la raiz no tiene .terraform.lock.hcl: las versiones de los proveedores no quedan fijas')
            elif versionados is not None and lock not in versionados and ignorado(repo, lock):
                inf.h('TF-LOCK', lock, None, 'el lock existe pero git lo ignora: no viaja con el codigo')
        for clave, rel, linea in c['backends']:
            backends.setdefault(clave, []).append((carpeta, rel, linea))
    for clave, donde in backends.items():
        carpetas_distintas = sorted(set(x[0] for x in donde))
        if len(carpetas_distintas) > 1:
            inf.h('TF-BACKEND-COMPARTIDO', donde[1][1], donde[1][2], 'el mismo backend en %s: comparten el estado' % ', '.join(carpetas_distintas))


def secretos_formato(rel, texto, inf):
    for i, l in enumerate(texto.split('\n')):
        for nombre, rx in FORMATOS:
            m = rx.search(l)
            if m and '<' not in m.group(0):
                inf.h('SECRETO-FORMATO', rel, i + 1, nombre, m.group(0))


# ---------------------------------------------------------------- herramientas externas

def correr(cmd, cwd=None):
    if any(t.lower() in PROHIBIDAS for t in cmd[1:]):
        raise RuntimeError('opcion prohibida en %s' % ' '.join(cmd))
    if len(cmd) > 1 and cmd[1] == 'fmt' and '-check' not in cmd:
        raise RuntimeError('fmt sin -check escribiria')
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout, r.stderr


def version_de(binario):
    try:
        _, out, err = correr([binario, '-v' if os.path.basename(binario).lower().startswith('kubeconform') else '--version'])
    except Exception:
        return '?'
    primera = next((l for l in (out + '\n' + err).splitlines() if l.strip()), '?')
    return limpio(primera, 60)


def cargar_json(texto):
    if not texto.strip():
        raise ValueError('reporte vacio')
    return json.loads(texto)


def leer_fmt(texto, err='', rc=None):
    sin_formato = [l.strip() for l in texto.splitlines() if l.strip()]
    if sin_formato:
        return HALLAZGO, '%d archivo(s) sin formato' % len(sin_formato), ['%s: sin formato (fmt -check)' % limpio(f) for f in sin_formato], []
    if rc is None:
        return SIN_DATOS, 'reporte vacio: no se distingue "todo formateado" de "no corrio"', [], []
    if rc == 0 and not err.strip():
        return OK, 'todo formateado', [], []
    return SIN_DATOS, 'fmt fallo: %s' % limpio((err.strip().splitlines() or ['sin mensaje'])[0]), [], []


def leer_validate(texto):
    d = cargar_json(texto)
    v = str(d.get('format_version', ''))
    if not re.match(r'^1\.\d+$', v):
        return SIN_DATOS, 'formato de validate desconocido (%s): se rechaza una version mayor que no se conoce' % limpio(v, 20), [], []
    diags = d.get('diagnostics') or []
    hall, avis = [], []
    for g in diags:
        rg = g.get('range') or {}
        donde = '%s:%s' % (rg.get('filename', '?'), (rg.get('start') or {}).get('line', '?'))
        texto_g = '%s: %s' % (limpio(donde, 120), limpio(g.get('summary', ''), 160))
        (hall if g.get('severity') == 'error' else avis).append(texto_g)
    if d.get('error_count', 0) or hall:
        return HALLAZGO, '%d error(es)' % max(len(hall), d.get('error_count', 0)), hall, avis
    if d.get('valid') is True:
        return OK, 'configuracion valida', [], avis
    return SIN_DATOS, 'validate no dijo si es valida', [], avis


def leer_tflint(texto):
    d = cargar_json(texto)
    if not isinstance(d, dict) or 'issues' not in d:
        return SIN_DATOS, 'no es un reporte de tflint', [], []
    hall, avis = [], []
    for x in d.get('issues') or []:
        rg = x.get('range') or {}
        regla = (x.get('rule') or {})
        t = '%s:%s: tflint %s -- %s' % (limpio(rg.get('filename', '?'), 120), (rg.get('start') or {}).get('line', '?'),
                                         limpio(regla.get('name', '?'), 60), limpio(x.get('message', ''), 160))
        (hall if regla.get('severity') in ('error', 'warning') else avis).append(t)
    errores = d.get('errors') or []
    if hall:
        return HALLAZGO, '%d issue(s)' % len(hall), hall, avis + (['tflint ademas informo %d error(es)' % len(errores)] if errores else [])
    if errores:
        return SIN_DATOS, 'tflint no termino de mirar: %s' % limpio(errores[0].get('message', ''), 160), [], avis
    return OK, 'sin issues', [], avis


def leer_checkov(texto):
    d = cargar_json(texto)
    reportes = d if isinstance(d, list) else [d]
    hall, avis, mirado = [], [], 0
    for r in reportes:
        if not isinstance(r, dict):
            continue
        resumen = r.get('summary') if 'summary' in r else r
        mirado += sum(int(resumen.get(k) or 0) for k in ('passed', 'failed', 'skipped'))
        if int(resumen.get('parsing_errors') or 0):
            avis.append('checkov no pudo leer %s archivo(s)' % resumen.get('parsing_errors'))
        for f in (r.get('results') or {}).get('failed_checks') or []:
            rango = f.get('file_line_range') or ['?']
            hall.append('%s:%s: checkov %s -- %s (%s)' % (limpio(str(f.get('file_path', '?')).lstrip('/'), 120), rango[0],
                                                          limpio(f.get('check_id', '?'), 30), limpio(f.get('check_name', ''), 120),
                                                          limpio(f.get('resource', ''), 80)))
    if hall:
        return HALLAZGO, '%d chequeo(s) fallido(s)' % len(hall), hall, avis
    if not mirado:
        return SIN_DATOS, 'checkov no analizo nada (cero chequeos): regla del cero', [], avis
    return OK, '%d chequeo(s), ninguno fallido' % mirado, [], avis


def leer_trivy(texto):
    d = cargar_json(texto)
    if not isinstance(d, dict):
        return SIN_DATOS, 'no es un reporte de trivy', [], []
    hall, mirado = [], 0
    for r in d.get('Results') or []:
        resumen = r.get('MisconfSummary') or {}
        mirado += int(resumen.get('Successes') or 0) + int(resumen.get('Failures') or 0)
        for m in r.get('Misconfigurations') or []:
            mirado += 1 if not resumen else 0
            if m.get('Status') == 'FAIL':
                hall.append('%s:%s: trivy %s -- %s (%s)' % (limpio(r.get('Target', '?'), 120), (m.get('CauseMetadata') or {}).get('StartLine', '?'),
                                                           limpio(m.get('ID', '?'), 30), limpio(m.get('Title', ''), 120), limpio(m.get('Severity', ''), 12)))
    if hall:
        return HALLAZGO, '%d mala(s) configuracion(es)' % len(hall), hall, []
    if not mirado:
        return SIN_DATOS, 'trivy no analizo nada (sin resultados): regla del cero', [], []
    return OK, '%d chequeo(s), ninguno fallido' % mirado, [], []


def leer_hadolint(texto):
    d = cargar_json(texto)
    if not isinstance(d, list):
        return SIN_DATOS, 'no es un reporte de hadolint', [], []
    hall, avis = [], []
    for x in d:
        t = '%s:%s: hadolint %s -- %s' % (limpio(x.get('file', '?'), 120), x.get('line', '?'), limpio(x.get('code', '?'), 12), limpio(x.get('message', ''), 160))
        (hall if x.get('level') in ('error', 'warning') else avis).append(t)
    if hall:
        return HALLAZGO, '%d regla(s) rota(s)' % len(hall), hall, avis
    return OK, 'sin errores ni advertencias', [], avis


def leer_kubeconform(texto):
    d = cargar_json(texto)
    if not isinstance(d, dict):
        return SIN_DATOS, 'no es un reporte de kubeconform', [], []
    hall = ['%s: kubeconform %s %s -- %s' % (limpio(r.get('filename', '?'), 120), limpio(r.get('kind', '?'), 40), limpio(r.get('name', '?'), 60), limpio(r.get('msg', ''), 160))
            for r in d.get('resources') or [] if r.get('status') == 'statusInvalid']
    s = d.get('summary') or {}
    if hall or int(s.get('invalid') or 0):
        return HALLAZGO, '%d recurso(s) invalido(s)' % max(len(hall), int(s.get('invalid') or 0)), hall, []
    if int(s.get('errors') or 0):
        return SIN_DATOS, 'kubeconform no pudo validar %s recurso(s)' % s.get('errors'), [], []
    if not int(s.get('valid') or 0):
        return SIN_DATOS, 'kubeconform no valido ningun recurso: regla del cero', [], []
    return OK, '%s recurso(s) validos' % s.get('valid'), [], []


LECTORES = {'fmt': leer_fmt, 'validate': leer_validate, 'tflint': leer_tflint, 'checkov': leer_checkov,
            'trivy': leer_trivy, 'hadolint': leer_hadolint, 'kubeconform': leer_kubeconform}


def combinar(partes):
    """Varios (estado, detalle, hallazgos, avisos) en uno: HALLAZGO pesa mas que SIN DATOS, y SIN DATOS mas que OK."""
    estado = HALLAZGO if any(p[0] == HALLAZGO for p in partes) else SIN_DATOS if any(p[0] == SIN_DATOS for p in partes) else OK
    return (estado, '; '.join(p[1] for p in partes), sum((p[2] for p in partes), []), sum((p[3] for p in partes), []))


def binario_iac(a):
    if a.binario:
        ruta = shutil.which(a.binario)
        return (ruta, '') if ruta else (None, '%s no esta instalada' % a.binario)
    hay = [b for b in ('terraform', 'tofu') if shutil.which(b)]
    if len(hay) == 2:
        return None, 'estan terraform y tofu: elegir con --binario (lo fija DEC-007)'
    return (shutil.which(hay[0]), '') if hay else (None, 'ni terraform ni tofu estan instaladas')


def esquemas_locales(ubicacion):
    """True si la ubicacion de los esquemas es una carpeta local que existe (con o sin una plantilla {{...}} al final)."""
    if '://' in ubicacion:
        return False
    base = ubicacion.split('{{', 1)[0]
    if '{{' in ubicacion:
        base = os.path.dirname(base)   # la carpeta donde empieza la plantilla
    return bool(base) and os.path.isdir(base)


def version_trivy(binario):
    """(version, motivo): la version instalada, de 'trivy version --format json'. motivo no vacio si no se la puede
    leer o si es una version comprometida: lo que diga esa herramienta no cuenta."""
    try:
        _, out, _ = correr([binario, 'version', '--format', 'json'])
        version = str((json.loads(out) or {}).get('Version') or '').strip().lstrip('v')
    except (ValueError, AttributeError, OSError):
        version = ''
    if not version:
        return '?', 'no se pudo leer la version de trivy (trivy version --format json): no se sabe si es una comprometida'
    if version in TRIVY_COMPROMETIDAS:
        return limpio(version, 30), ('trivy %s es la version del incidente de marzo de 2026: no se corre y lo que diga no '
                                     'cuenta; hay que instalar otra verificada' % limpio(version, 30))
    return limpio(version, 30), ''


def ejecutar(nombre, a, repo, ctx):
    """(estado, detalle, hallazgos, avisos, version) corriendo la herramienta instalada."""
    if nombre in ('fmt', 'validate'):
        binario, motivo = binario_iac(a)
        if not binario:
            return SIN_DATOS, motivo, [], [], ''
        if nombre == 'fmt':
            rc, out, err = correr([binario, 'fmt', '-check', '-recursive', '-no-color', repo])
            return leer_fmt(out, err, rc) + (version_de(binario),)
        if not ctx['raices']:
            return SIN_DATOS, 'no hay raices de Terraform donde validar', [], [], version_de(binario)
        partes = []
        for raiz in ctx['raices']:
            ruta = os.path.join(repo, raiz)
            if not os.path.isdir(os.path.join(ruta, '.terraform')):
                partes.append((SIN_DATOS, '%s sin init (este script no lo corre: init baja proveedores)' % raiz, [], []))
                continue
            rc, out, err = correr([binario, 'validate', '-json', '-no-color'], cwd=ruta)
            partes.append(leer_validate(out))
        return combinar(partes) + (version_de(binario),)
    binario = shutil.which(nombre)
    if not binario:
        return SIN_DATOS, '%s no esta instalada' % nombre, [], [], ''
    version = version_de(binario)
    if nombre == 'tflint':
        # --recursive recorre desde la carpeta actual: se corre parado en el repositorio. La documentacion presenta
        # --chdir y --recursive como alternativas ("--chdir=DIR/--recursive"); asi anda en cualquier version.
        rc, out, err = correr([binario, '--recursive', '--format=json'], cwd=repo)
    elif nombre == 'checkov':
        rc, out, err = correr([binario, '-d', repo, '-o', 'json', '--quiet', '--compact', '--skip-download'])
    elif nombre == 'trivy':
        version, motivo = version_trivy(binario)
        if motivo:
            return SIN_DATOS, motivo, [], [], version
        rc, out, err = correr([binario, 'config', '--format', 'json', '--quiet', '--skip-check-update',
                               '--disable-telemetry', '--skip-version-check', repo])
    elif nombre == 'hadolint':
        partes = []
        for f in ctx['dockerfiles']:
            rc, out, err = correr([binario, '--format', 'json', os.path.join(repo, f)])
            partes.append(leer_hadolint(out))
        return combinar(partes) + (version,)
    else:
        if not a.esquemas_k8s:
            return SIN_DATOS, 'sin --esquemas-k8s kubeconform bajaria los esquemas de internet: no se corre', [], [], version
        if not esquemas_locales(a.esquemas_k8s):
            return SIN_DATOS, ('--esquemas-k8s tiene que ser una carpeta local que exista (una URL o una carpeta que no esta '
                               'haria que kubeconform baje los esquemas): no se corre'), [], [], version
        rc, out, err = correr([binario, '-output', 'json', '-summary', '-schema-location', a.esquemas_k8s] + [os.path.join(repo, f) for f in ctx['k8s']])
    return LECTORES[nombre](out) + (version,)


def herramientas(a, repo, tipos, ctx):
    reportes, res = {}, []
    for r in a.reporte:
        nombre, _, ruta = r.partition('=')
        reportes.setdefault(nombre.strip().lower(), []).append(ruta.strip())
    desconocidas = sorted(set(reportes) - set(HERRAMIENTAS))
    pedidas = set(reportes)
    if a.herramientas:
        pedido = [x.strip().lower() for x in a.herramientas.split(',') if x.strip()]
        pedidas |= set(HERRAMIENTAS) if 'todas' in pedido else set(pedido)
        desconocidas += sorted(set(pedido) - set(HERRAMIENTAS) - {'todas'})
    for nombre in desconocidas:
        res.append({'nombre': limpio(nombre, 40), 'estado': 'SIN DATOS', 'version': '', 'detalle': 'herramienta que este script no conoce (sabe: %s)' % ', '.join(HERRAMIENTAS),
                    'hallazgos': [], 'avisos': []})
    todas = bool(a.herramientas) and 'todas' in a.herramientas.lower()
    for nombre in HERRAMIENTAS:
        if nombre not in pedidas:
            continue
        if not any(t in tipos for t in APLICA[nombre]):
            res.append({'nombre': nombre, 'estado': 'N/A', 'version': '', 'detalle': 'no hay archivos a los que aplique', 'hallazgos': [], 'avisos': []})
            continue
        if nombre in reportes:
            partes = []
            for ruta in reportes[nombre]:
                try:
                    with open(ruta, 'rb') as h:
                        texto = h.read().decode('utf-8-sig', 'replace')
                    partes.append(LECTORES[nombre](texto))
                except (OSError, ValueError, AttributeError, TypeError) as e:
                    partes.append((SIN_DATOS, 'reporte %s ilegible o ausente: %s' % (limpio(ruta, 120), limpio(e, 120)), [], []))
            estado, detalle, hall, avis = combinar(partes)
            version = 'la del reporte'
        else:
            try:
                estado, detalle, hall, avis, version = ejecutar(nombre, a, repo, ctx)
            except (OSError, ValueError, RuntimeError, AttributeError, TypeError) as e:
                estado, detalle, hall, avis, version = SIN_DATOS, 'no se pudo correr o leer: %s' % limpio(e, 160), [], [], ''
        res.append({'nombre': nombre, 'estado': NOMBRE[estado], 'version': version, 'detalle': detalle, 'hallazgos': hall[:200], 'avisos': avis[:50]})
    if todas:
        escaneres = [r for r in res if r['nombre'] in ('checkov', 'trivy')]
        if any(r['estado'] != 'SIN DATOS' for r in escaneres):
            for r in escaneres:
                if r['estado'] == 'SIN DATOS' and 'no esta instalada' in r['detalle']:
                    r['estado'], r['detalle'] = 'N/A', r['detalle'] + ' (alcanza con el otro escaner)'
        if 'bicep' in tipos:
            res.append({'nombre': 'bicep lint', 'estado': 'SIN DATOS', 'version': '', 'hallazgos': [], 'avisos': [],
                        'detalle': 'este script todavia no lo corre: correrlo a mano (bicep lint) y mirar su salida'})
    return res


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(description='Lo estatico de la infraestructura como codigo de un repositorio (solo lectura).')
    ap.add_argument('--repo', default='')
    ap.add_argument('--herramientas', nargs='?', const='todas', default='', help='todas (por defecto) o una lista separada por coma')
    ap.add_argument('--reporte', action='append', default=[], help='herramienta=archivo: lee ese reporte en vez de correrla')
    ap.add_argument('--binario', default='', help='terraform o tofu, si estan las dos')
    ap.add_argument('--esquemas-k8s', dest='esquemas_k8s', default='', help='ubicacion local de los esquemas para kubeconform')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if not a.repo:
        print('SIN DATOS -- falta --repo <ruta del repositorio a mirar>')
        return SIN_DATOS
    repo = os.path.abspath(a.repo)
    if not os.path.isdir(repo):
        print('SIN DATOS -- la carpeta no existe: %s' % limpio(repo, 200))
        return SIN_DATOS

    inf = Informe()
    archivos, dot_terraform = recorrer(repo, inf)
    tipos, carpetas, plantillas, por_etiqueta = {}, {}, set(), [0]
    ctx = {'dockerfiles': [], 'k8s': [], 'raices': []}
    for rel in archivos:
        tipo = tipo_de(rel.rsplit('/', 1)[-1])
        if tipo is None:
            continue
        ruta = os.path.join(repo, *rel.split('/'))
        try:
            if os.path.getsize(ruta) > MAX_BYTES:
                inf.no_mirado('%s pesa mas de %d MB: no se miro' % (rel, MAX_BYTES // (1024 * 1024)))
                continue
            texto = leer_texto(ruta)
        except OSError as e:
            inf.no_mirado('%s no se pudo leer: %s' % (rel, e))
            continue
        if tipo == 'yaml':
            if not es_kubernetes(texto):
                continue
            tipo = 'kubernetes'
        tipos[tipo] = tipos.get(tipo, 0) + 1
        if tipo == 'terraform':
            analizar_tf(rel, texto, inf, carpetas)
        elif tipo == 'bicep':
            analizar_bicep(rel, texto, inf)
        elif tipo == 'dockerfile':
            ctx['dockerfiles'].append(rel)
            analizar_dockerfile(rel, texto, inf, repo, ruta, por_etiqueta)
        elif tipo == 'compose':
            analizar_compose(rel, texto, inf, por_etiqueta)
        else:
            ctx['k8s'].append(rel)
            analizar_kubernetes(rel, texto, inf, por_etiqueta, plantillas)
        secretos_formato(rel, texto, inf)
    if any(es_no_versionable(x) for x in archivos) or dot_terraform:
        tipos.setdefault('terraform', 0)
    if not tipos:
        msg = 'no hay infraestructura como codigo en %s (Terraform u OpenTofu, Bicep, Dockerfile, Compose o Kubernetes)' % limpio(repo, 200)
        if a.json:
            print(json.dumps({'estado': 'SIN DATOS', 'repo': repo, 'motivo': msg}, ensure_ascii=True, indent=1))
        else:
            print('SIN DATOS -- ' + msg)
        return SIN_DATOS

    estados = {}
    if 'terraform' in tipos:
        estados['TF-NO-VERSIONAR'] = revisar_versionado(repo, archivos, dot_terraform, inf)
        rc, sale = git(repo, ['rev-parse', '--is-inside-work-tree'])
        reglas_de_carpetas(repo, carpetas, set(archivos), inf, rc == 0 and sale.strip() == b'true')
        # un .tfvars que git ignora (el de valores locales) no viaja con el codigo: su clave no es SECRETO-LITERAL
        tfvars = set(h['archivo'] for h in inf.hallazgos if h['regla'] == 'SECRETO-LITERAL' and h['archivo'].endswith('.tfvars'))
        ignorados = set(f for f in tfvars if ignorado(repo, f))
        if ignorados:
            inf.hallazgos = [h for h in inf.hallazgos if not (h['regla'] == 'SECRETO-LITERAL' and h['archivo'] in ignorados)]
            for f in sorted(ignorados):
                inf.aviso('%s tiene valores sensibles y git lo ignora: no viaja con el codigo (que no se versione nunca, '
                          'y mejor que la clave entre por el pipeline)' % f)
        ctx['raices'] = sorted(c for c, v in carpetas.items() if v['raiz'] and v['tf'] and not set(c.split('/')) & {'modules', 'examples', 'example', 'tests', 'test'})
    if por_etiqueta[0]:
        inf.aviso('%d imagen(es) fijada(s) por etiqueta y no por digest: una etiqueta se puede mover' % por_etiqueta[0])
    if plantillas:
        inf.aviso('%d plantilla(s) de Helm no se miraron como manifiestos (%s): las mira helm lint' % (len(plantillas), ', '.join(sorted(plantillas)[:5])))

    reglas = []
    for rid, aplica, que in REGLAS:
        aplica = TIPOS if aplica is None else (aplica if isinstance(aplica, tuple) else (aplica,))
        cuenta = sum(1 for h in inf.hallazgos if h['regla'] == rid)
        if not any(t in tipos for t in aplica):
            estado = 'N/A'
        elif rid in inf.sin_datos and not cuenta:
            estado = 'SIN DATOS'
        else:
            estado = 'HALLAZGO' if cuenta else 'OK'
        reglas.append({'id': rid, 'que': que, 'estado': estado, 'cuenta': cuenta, 'motivo': inf.sin_datos.get(rid, '')})
    herr = herramientas(a, repo, tipos, ctx) if (a.herramientas or a.reporte) else []

    if any(r['estado'] == 'HALLAZGO' for r in reglas) or any(h['estado'] == 'HALLAZGO' for h in herr):
        total = HALLAZGO
    elif (any(r['estado'] == 'SIN DATOS' for r in reglas) or any(h['estado'] == 'SIN DATOS' for h in herr)
          or inf.sin_mirar):
        total = SIN_DATOS
    else:
        total = OK
    salida = {'estado': NOMBRE[total], 'repo': repo, 'tipos': tipos, 'reglas': reglas, 'hallazgos': inf.hallazgos[:500],
              'herramientas': herr, 'sin_mirar': inf.sin_mirar[:50], 'avisos': inf.avisos[:50], 'no_mira': list(NO_MIRA)}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
        return total

    print('AUDITAR IaC -- %s   [%s; %s]' % (NOMBRE[total], limpio(repo, 120), ', '.join('%s: %d archivo(s)' % (t, tipos[t]) for t in TIPOS if t in tipos)))
    cuentas = dict((e, sum(1 for r in reglas if r['estado'] == e)) for e in ('OK', 'HALLAZGO', 'SIN DATOS', 'N/A'))
    print('  Reglas (%d): %d OK, %d HALLAZGO, %d SIN DATOS, %d N/A' % (len(reglas), cuentas['OK'], cuentas['HALLAZGO'], cuentas['SIN DATOS'], cuentas['N/A']))
    for s in inf.sin_mirar[:10]:
        print('  SIN DATOS: no se miro todo: ' + s)
    for r in reglas:
        if r['estado'] != 'N/A':
            print('    %-9s %-22s %s%s' % (r['estado'], r['id'], r['que'], (' (%d)' % r['cuenta']) if r['cuenta'] else (' -- ' + r['motivo'] if r['motivo'] else '')))
    for h in inf.hallazgos[:500]:
        print('  HALLAZGO: %s%s -- %s: %s%s' % (h['archivo'], ':%d' % h['linea'] if h['linea'] else '', h['regla'], h['detalle'],
                                              ' (huella %s)' % h['huella'] if 'huella' in h else ''))
    if herr:
        print('  Herramientas:')
        for x in herr:
            print('    %-9s %-12s %s%s' % (x['estado'], x['nombre'], x['detalle'], ' [version: %s]' % x['version'] if x['version'] else ''))
            for t in x['hallazgos']:
                print('  HALLAZGO: ' + t)
            for t in x['avisos'][:10]:
                print('  aviso: ' + t)
    else:
        print('  Herramientas externas: no se pidieron (--herramientas o --reporte).')
    for v in inf.avisos[:50]:
        print('  aviso: ' + v)
    print('  Lo que este script NO mira: ' + '; '.join(NO_MIRA) + '.')
    return total


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
