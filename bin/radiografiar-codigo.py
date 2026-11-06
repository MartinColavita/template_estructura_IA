#!/usr/bin/env python3
"""Radiografia DETERMINISTA de una aplicacion existente: los HECHOS del codigo, con archivo:linea. SOLO LECTURA.

    python bin/radiografiar-codigo.py <ruta-de-la-aplicacion> [--json] [--mermaid] [--max-archivos 20000] [--tope 40]

Tres estados, nunca dos:  0 = radiografia lista   1 = (no aplica)   2 = SIN DATOS (ruta vacia o ilegible)

POR QUE EXISTE. Despues del inventario (que dice QUE HAY), la ingenieria inversa necesita saber DONDE
MIRAR: que endpoints expone la aplicacion, que entidades y tablas tiene, que pantallas, que validaciones
y umbrales esconden reglas de negocio, con que sistemas habla, quien puede hacer que, y que modulo
depende de cual. Si lo saca un script, cada hecho viene con su archivo y su linea, dos corridas dan lo
mismo, y el modelo lee lo que la radiografia senala en vez de leer 20.000 archivos a ciegas. Es la
"reconnaissance" de los frameworks de reverse engineering, hecha con biblioteca estandar.

QUE SACA (por familias de stack, por expresiones regulares; lo que no reconoce no lo inventa):
  api            endpoints implementados (Spring, JAX-RS/Quarkus, .NET, Express/Koa/Fastify, NestJS, Flask,
                 FastAPI, Django, Go, Rails, Laravel) y rutas declaradas en un contrato openapi/swagger
  modelo         entidades, tablas (DDL y ORMs), enums, relaciones y campos de estado (candidatos a maquina de estados)
  pantallas      rutas del front (React Router, Angular, Vue, objetos de rutas) y componentes Page/Screen/View
  reglas         CANDIDATAS: validaciones declarativas, condiciones que lanzan un error (con su mensaje),
                 constantes numericas con nombre, cambios de estado y funciones de calculo
  integraciones  clientes HTTP, URLs y conexiones en la configuracion (credenciales enmascaradas),
                 mensajeria, tareas programadas, correo/archivos/almacenamiento, autenticacion
  permisos       anotaciones y chequeos de rol, con los roles literales que aparecen
  dependencias   aristas entre modulos de primer nivel (por imports), ciclos y cruces de capa
                 (un modulo que importa la api o la infra de otro: lo que DEC-002 prohibe)

DIAGRAMAS (--mermaid). Emite, en texto Mermaid (se versiona y lo renderizan GitLab y GitHub), el grafo de
dependencias entre modulos con sus cruces de capa y el diagrama entidad-relacion de las tablas del DDL con
sus FOREIGN KEY. Son los hechos dibujados, no un dibujo a mano: lo que la radiografia no vio, no aparece.

QUE NO HACE. No decide que es una regla de negocio (cada hallazgo de "reglas" es CANDIDATO hasta que
una persona lo confirme), no lee el contenido de datos, no modifica nada, no sale de la ruta dada.
Enmascara lo que parece una credencial en los fragmentos. Solo biblioteca estandar. ASCII en la salida
de texto salvo los fragmentos del propio codigo.
"""

import argparse
import json
import os
import re
import sys

OK, _, SIN_DATOS = 0, 1, 2
BASURA = {'.git', 'node_modules', 'target', 'build', 'out', 'dist', '.gradle', '.idea', '.vscode',
          '__pycache__', '.mvn', 'coverage', '.next', 'vendor', 'bin', 'obj', '.venv', 'venv', '.tox'}
CODIGO = ('.java', '.kt', '.cs', '.py', '.js', '.ts', '.tsx', '.jsx', '.mjs', '.go', '.rs', '.rb', '.php',
          '.scala', '.swift', '.dart', '.vue', '.svelte', '.prisma', '.sql')
CONFIG = ('.yml', '.yaml', '.properties', '.env', '.json', '.toml', '.ini', '.xml', '.cfg', '.conf')
GENERICOS = {'src', 'main', 'java', 'kotlin', 'scala', 'app', 'lib', 'source', 'resources', 'python', 'ts',
             'js', 'web', 'server', 'client', 'packages', 'apps', 'modules', 'internal', 'pkg', 'cmd'}
DOMINIOS = {'com', 'org', 'net', 'io', 'ar', 'es', 'br', 'uk', 'de', 'gov', 'edu', 'co', 'mx', 'cl', 'uy'}
CAPAS_PROHIBIDAS = {'api', 'infra', 'infrastructure', 'controller', 'controllers', 'web', 'rest'}
MAX_FRAG = 140

# --- api ---------------------------------------------------------------------------------------
API = [
    ('spring', re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)"'), 1, 2),
    ('spring', re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)"'), None, 1),
    ('dotnet', re.compile(r'\[Http(Get|Post|Put|Delete|Patch)(?:\s*\(\s*"([^"]*)"\s*\))?\]'), 1, 2),
    ('dotnet', re.compile(r'\[Route\s*\(\s*"([^"]*)"\s*\)\]'), None, 1),
    ('express', re.compile(r'\b(?:app|router|server|fastify|api)\.(get|post|put|delete|patch|all)\s*\(\s*[\'"`]([^\'"`]+)'), 1, 2),
    ('nest', re.compile(r'@(Get|Post|Put|Delete|Patch)\s*\(\s*(?:[\'"`]([^\'"`]*)[\'"`])?\s*\)'), 1, 2),
    ('flask', re.compile(r'@\w+\.route\s*\(\s*[\'"]([^\'"]+)[\'"](?:.*methods\s*=\s*\[([^\]]*)\])?'), 2, 1),
    ('fastapi', re.compile(r'@\w+\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)'), 1, 2),
    ('go', re.compile(r'\.(HandleFunc|Handle|GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"'), 1, 2),
    ('rails', re.compile(r'^\s*(get|post|put|patch|delete|resources?)\s+[\'":]([^\'",\s]+)'), 1, 2),
    ('laravel', re.compile(r'Route::(get|post|put|delete|patch|any|resource)\s*\(\s*[\'"]([^\'"]+)'), 1, 2),
]
DJANGO_PATH = re.compile(r'\b(?:re_)?path\s*\(\s*[\'"]([^\'"]*)[\'"]')
JAXRS_METODO = re.compile(r'@(GET|POST|PUT|DELETE|PATCH)\b')
JAXRS_PATH = re.compile(r'@Path\s*\(\s*(?:value\s*=\s*)?"([^"]*)"')
CONTRATO = re.compile(r'(?i)(^|/)(openapi|swagger|api-spec)[^/]*\.(ya?ml|json)$')
CONTRATO_RUTA = re.compile(r'^\s{2,4}(/[^\s:]*):')

# --- modelo ------------------------------------------------------------------------------------
ENTIDAD = [
    ('jpa', re.compile(r'@Entity\b')), ('typeorm', re.compile(r'@Entity\s*\(')),
    ('django', re.compile(r'class\s+(\w+)\s*\(.*models\.Model')), ('sqlalchemy', re.compile(r'__tablename__\s*=\s*[\'"](\w+)')),
    ('prisma', re.compile(r'^model\s+(\w+)\s*\{')), ('mongoose', re.compile(r'new\s+(?:mongoose\.)?Schema\s*\(')),
    ('efcore', re.compile(r'DbSet<(\w+)>')), ('rails', re.compile(r'create_table\s+[:"\'](\w+)')),
]
TABLA = re.compile(r'@Table\s*\(\s*(?:name\s*=\s*)?"([^"]*)"')
DDL_TABLA = re.compile(r'(?i)\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?([\w.]+)')
DDL_FK = re.compile(r'(?i)\bREFERENCES\s+[`"\[]?([\w.]+)')
CLASE = re.compile(r'\b(?:class|record|interface|type|struct)\s+(\w+)')
ENUM = re.compile(r'\b(?:enum\s+class|enum)\s+(\w+)|class\s+(\w+)\s*\(\s*(?:\w+\.)?(?:Enum|IntEnum|StrEnum)\s*\)')
RELACION = re.compile(r'@(OneToMany|ManyToOne|OneToOne|ManyToMany)\b|\bForeignKey\s*\(|\bbelongs_to\b|\bhas_many\b|\brelationship\s*\(')
CAMPO_ESTADO = re.compile(r'\b(estado|status|state|situacion|etapa)[A-Za-z_]*\b')

# --- pantallas ---------------------------------------------------------------------------------
RUTA_FRONT = re.compile(r'<Route\s+[^>]*path\s*=\s*["\'{]([^"\'}]*)|^\s*(?:path|route)\s*:\s*[\'"`]([^\'"`]*)[\'"`]')
ARCHIVO_RUTAS = re.compile(r'(?i)(routes?|routing|router|navigation)[^/]*\.(tsx?|jsx?|vue|dart|kt|swift)$')
PANTALLA = re.compile(r'(?i)(\w+)(page|screen|view|pantalla|vista)\.(tsx|jsx|vue|svelte|ts|js|dart|kt|swift)$')

# --- reglas candidatas -------------------------------------------------------------------------
VALIDACION = re.compile(r'@(NotNull|NotBlank|NotEmpty|Size|Min|Max|Pattern|Email|Positive|PositiveOrZero|Negative|Digits|DecimalMin|DecimalMax|Past|PastOrPresent|Future|FutureOrPresent|AssertTrue|AssertFalse|Valid|Length|Range|Required|IsString|IsInt|IsEmail|MaxLength|MinLength|StringLength|RegularExpression)\b(\([^)]*\))?')
LANZA = re.compile(r'\b(?:throw\s+new\s+(\w+)\s*\(|raise\s+(\w+)\s*\(|errors\.New\(|fmt\.Errorf\(|throw\s+(?:new\s+)?Error\s*\(|panic\()\s*[\'"`]([^\'"`]{3,140})')
CONDICION = re.compile(r'^\s*(?:}\s*)?(?:if|elif|else if|unless|when|case)\b\s*\(?(.{3,160}?)\)?\s*(?:\{|:|then)?\s*$')
CONSTANTE = re.compile(r'\b([A-Z][A-Z0-9_]{2,})\s*(?::\s*\w+\s*)?=\s*(-?\d[\d_.]*)\b')
CAMBIO_ESTADO = re.compile(r'\.set(?:Estado|Status|State)\w*\s*\(|(?<![\w(,])(?<![(,] )(?:self\.|this\.)?(?:estado|status|state)\w*\s*=\s*(?!=)(?:[\'"][A-Za-z_]+[\'"]|[A-Z][A-Za-z]*\.[A-Z_]+)|\bswitch\s*\(\s*\w*(?:estado|status|state)|\bcase\s+(?:Estado|Status|State)\w*\.|\btransition(?:To)?\s*\(')
CALCULO = re.compile(r'(?i)\b(?:def|function|fun|func|public|private|protected|static|async)\b[^(=]{0,60}?\b((?:calcul|comput|liquid|factur|cotiz|tarif|descuent|interes|precio|importe|monto|total|vencimient|penaliz|redonde)\w*)\s*\(')

# --- integraciones -----------------------------------------------------------------------------
CLIENTE_HTTP = re.compile(r'\b(RestTemplate|WebClient|HttpClient|OkHttpClient|RestClient|FeignClient|RegisterRestClient|axios|fetch|got|ky|superagent|requests\.(?:get|post|put|delete|patch)|httpx|urllib\.request|aiohttp|HttpClientFactory|HttpWebRequest|resty|http\.(?:Get|Post|NewRequest)|Net::HTTP|Faraday|Guzzle|curl_init)\b')
URL_CONFIG = re.compile(r'(https?://[^\s"\'<>,;)]+)')
CONEXION = re.compile(r'(jdbc:[\w:]+//[^\s"\']+|mongodb(?:\+srv)?://[^\s"\']+|postgres(?:ql)?://[^\s"\']+|mysql://[^\s"\']+|redis://[^\s"\']+|amqps?://[^\s"\']+|Server=[^;\s"\']+;[^"\'\n]*Database=[^;\s"\']+|DATABASE_URL\b)')
MENSAJERIA = re.compile(r'(?i)@(KafkaListener|RabbitListener|JmsListener|SqsListener|Incoming|Outgoing|EventListener|StreamListener|MessageMapping)\b|\b(kafka|rabbitmq|amqp|sqs|sns|pubsub|nats|mqtt|eventbridge|servicebus|celery)\b')
PROGRAMADA = re.compile(r'(?i)@Scheduled\b|@Cron\s*\(|\bcron\s*[:=(]|node-cron|setInterval\s*\(|schedule\.every|APScheduler|Quartz|\bcrontab\b|@Schedules?\b')
CORREO_ARCHIVOS = re.compile(r'(?i)\b(sftp|ftps?)://|JavaMailSender|nodemailer|smtplib|sendgrid|SmtpClient|\.sendMail\(|mailer|S3Client|BlobServiceClient|GoogleCloudStorage|boto3\.client\([\'"]s3|MinioClient')
AUTENTICACION = re.compile(r'(?i)\b(oauth2?|openid|oidc|keycloak|saml|jwt|jsonwebtoken|auth0|cognito|ldap|passport|spring-security|nextauth|clerk)\b')
SECRETO = re.compile(r'(?i)((?:token|key|secret|password|passwd|pwd|clave|contrasena|credential)\w*\s*[=:]\s*)[^\s,;]+')
USUARIO_URL = re.compile(r'://[^/\s:@]+:[^/\s@]+@')

# --- permisos ----------------------------------------------------------------------------------
PERMISO = re.compile(r'@(RolesAllowed|PreAuthorize|PostAuthorize|Secured|PermitAll|DenyAll|Authorize|UseGuards|Roles|Permissions?|RequiresRoles?|RequiresPermissions?)\b(\([^)]*\))?|\[Authorize(\([^)]*\))?\]|\b(hasRole|hasAuthority|hasAnyRole|hasAnyAuthority|hasPermission|permission_required|login_required|user_passes_test|requires_auth|authorize|can|cannot|isGranted|is_granted|ensureRole|checkRole)\s*\(')
ROL_LITERAL = re.compile(r'[\'"]([A-Z][A-Z0-9_:]{2,})[\'"]')

# --- dependencias ------------------------------------------------------------------------------
IMPORTS = [
    re.compile(r'^\s*import\s+(?:static\s+)?([\w.]+)'),                 # java, kotlin, python (import a.b)
    re.compile(r'^\s*from\s+([\w.]+)\s+import\b'),                       # python
    re.compile(r'\bfrom\s+[\'"]([^\'"]+)[\'"]'),                         # ts/js
    re.compile(r'\brequire\s*\(\s*[\'"]([^\'"]+)[\'"]'),                  # js
    re.compile(r'^\s*using\s+([\w.]+)\s*;'),                             # c#
    re.compile(r'^\s*use\s+([\w\\]+)'),                                  # php
]


def modulo_de(rel):
    """Modulo de primer nivel de una ruta relativa, saltando carpetas genericas y dominios invertidos."""
    partes = rel.split('/')[:-1]
    while partes and partes[0] in GENERICOS:
        partes = partes[1:]
    if len(partes) >= 3 and partes[0] in DOMINIOS:
        partes = partes[2:]
    return partes[0] if partes else '(raiz)'


def capas_de(rel):
    return set(p.lower() for p in rel.split('/')[:-1])


def enmascarar(frag):
    frag = USUARIO_URL.sub('://<credencial>@', frag)
    frag = SECRETO.sub(r'\1<secreto>', frag)
    return frag.strip()[:MAX_FRAG]


def leer_lineas(p):
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as h:
            return h.read().split('\n')
    except OSError:
        return None


class Radiografia:
    def __init__(self, raiz, max_archivos):
        self.raiz = raiz
        self.max_archivos = max_archivos
        self.archivos = 0
        self.leidos = 0
        self.modulos = {}
        self.api, self.contrato, self.pantallas, self.reglas, self.integraciones, self.permisos = [], [], [], [], [], []
        self.entidades, self.tablas, self.enums, self.relaciones, self.campos_estado = [], [], [], [], []
        self.aristas, self.cruces = {}, []
        self._imports = []           # (modulo_origen, destino, rel, linea)

    def item(self, lista, rel, n, **campos):
        d = {'archivo': rel, 'linea': n, 'modulo': modulo_de(rel)}
        d.update(campos)
        lista.append(d)

    def recorrer(self):
        for base, dirs, files in os.walk(self.raiz):
            dirs[:] = sorted(d for d in dirs if d not in BASURA)
            for f in sorted(files):
                if self.archivos >= self.max_archivos:
                    return
                self.archivos += 1
                p = os.path.join(base, f)
                rel = os.path.relpath(p, self.raiz).replace(os.sep, '/')
                ext = os.path.splitext(f)[1].lower()
                self.modulos[modulo_de(rel)] = self.modulos.get(modulo_de(rel), 0) + 1
                if PANTALLA.search(f):
                    self.item(self.pantallas, rel, 0, tipo='componente', valor=PANTALLA.search(f).group(1) + PANTALLA.search(f).group(2))
                try:
                    if os.path.getsize(p) > 2_000_000:
                        continue
                except OSError:
                    continue
                if CONTRATO.search(rel):
                    self.contrato_de(p, rel)
                if ext in CODIGO:
                    self.codigo(p, rel, ext, f)
                elif ext == '.md':
                    self.documento(p, rel)
                elif ext in CONFIG or f.startswith('.env'):
                    self.configuracion(p, rel)

    def contrato_de(self, p, rel):
        lineas = leer_lineas(p)
        if lineas is None:
            return
        self.leidos += 1
        for n, l in enumerate(lineas, 1):
            m = CONTRATO_RUTA.match(l)
            if m:
                self.item(self.contrato, rel, n, ruta=m.group(1))

    def documento(self, p, rel):
        """Un .md puede traer el DDL en un bloque ```sql y la maquina de estados en un ```mermaid: se leen igual."""
        lineas = leer_lineas(p)
        if lineas is None:
            return
        self.leidos += 1
        bloque = None
        estados = []
        for n, l in enumerate(lineas, 1):
            m = re.match(r'^\s*```\s*(\w+)?', l)
            if m:
                bloque = None if bloque else (m.group(1) or '').lower()
                continue
            if bloque == 'sql':
                mt = DDL_TABLA.search(l)
                if mt:
                    self.item(self.tablas, rel, n, valor=mt.group(1), origen='ddl')
                mf = DDL_FK.search(l)
                if mf:
                    self.item(self.relaciones, rel, n, tipo='FOREIGN KEY', valor='-> ' + mf.group(1))
            elif bloque == 'mermaid':
                ms = re.match(r'^\s*(\[\*\]|\w+)\s*-->\s*(\w+|\[\*\])', l)
                if ms:
                    estados += [x for x in (ms.group(1), ms.group(2)) if x != '[*]' and x not in estados]
        if estados:
            self.item(self.enums, rel, 0, valor='stateDiagram: ' + ', '.join(estados[:12]))

    def configuracion(self, p, rel):
        lineas = leer_lineas(p)
        if lineas is None:
            return
        self.leidos += 1
        for n, l in enumerate(lineas, 1):
            for m in URL_CONFIG.finditer(l):
                url = m.group(1)
                if 'localhost' in url or '127.0.0.1' in url or 'example.com' in url or 'w3.org' in url or 'schemas.' in url:
                    continue
                self.item(self.integraciones, rel, n, tipo='url en configuracion', valor=enmascarar(url))
            m = CONEXION.search(l)
            if m:
                self.item(self.integraciones, rel, n, tipo='conexion a base o broker', valor=enmascarar(m.group(1)))
            if PROGRAMADA.search(l) and 'cron' in l.lower():
                self.item(self.integraciones, rel, n, tipo='tarea programada', valor=enmascarar(l))

    def codigo(self, p, rel, ext, nombre):
        lineas = leer_lineas(p)
        if lineas is None:
            return
        self.leidos += 1
        capas = capas_de(rel)
        es_modelo = False
        clase_actual = None
        path_clase = None
        es_rutas = bool(ARCHIVO_RUTAS.search(nombre))
        es_urls_django = nombre == 'urls.py'
        es_rails_routes = rel.endswith('config/routes.rb')
        for n, l in enumerate(lineas, 1):
            s = l.strip()
            if not s or s.startswith(('//', '#', '*', '/*', '--')) and not s.startswith('#['):
                continue
            mc = CLASE.search(l)
            if mc and clase_actual is None:
                clase_actual = mc.group(1)
            # api
            if ext == '.rs' and '#[tauri::command]' in l:
                for l2 in lineas[n:n + 3]:
                    mf = re.search(r'\bfn\s+(\w+)', l2)
                    if mf:
                        self.item(self.api, rel, n, marco='tauri', metodo='CMD', ruta=mf.group(1))
                        break
            for marco, rx, g_met, g_ruta in API:
                if marco == 'rails' and not es_rails_routes:
                    continue
                m = rx.search(l)
                if not m:
                    continue
                metodo = (m.group(g_met) if g_met and m.group(g_met) else '-')
                ruta = (m.group(g_ruta) if g_ruta and m.group(g_ruta) else '')
                if marco == 'flask':
                    metodo = (metodo or 'GET').replace("'", '').replace('"', '').replace(' ', '')
                self.item(self.api, rel, n, marco=marco, metodo=metodo.upper(), ruta=ruta)
                break
            mp = JAXRS_PATH.search(l)
            if mp and path_clase is None and (ext in ('.java', '.kt')):
                path_clase = mp.group(1)
            mm = JAXRS_METODO.search(l)
            if mm and ext in ('.java', '.kt'):
                sub = ''
                for l2 in lineas[n:n + 3]:
                    m2 = JAXRS_PATH.search(l2)
                    if m2 and m2.group(1) != path_clase:
                        sub = m2.group(1)
                        break
                self.item(self.api, rel, n, marco='jaxrs', metodo=mm.group(1), ruta=((path_clase or '') + sub) or '(sin @Path)')
            if es_urls_django:
                m = DJANGO_PATH.search(l)
                if m:
                    self.item(self.api, rel, n, marco='django', metodo='-', ruta='/' + m.group(1))
            # modelo
            for marco, rx in ENTIDAD:
                m = rx.search(l)
                if m:
                    es_modelo = True
                    nombre_ent = (m.group(1) if m.groups() and m.group(1) else None)
                    if nombre_ent is None:
                        for l2 in lineas[n - 1:n + 6]:
                            mc2 = CLASE.search(l2)
                            if mc2:
                                nombre_ent = mc2.group(1)
                                break
                    self.item(self.entidades, rel, n, marco=marco, valor=nombre_ent or '?')
                    break
            m = TABLA.search(l)
            if m:
                self.item(self.tablas, rel, n, valor=m.group(1), origen='orm')
            if ext == '.sql':
                m = DDL_TABLA.search(l)
                if m:
                    self.item(self.tablas, rel, n, valor=m.group(1), origen='ddl')
                m = DDL_FK.search(l)
                if m:
                    self.item(self.relaciones, rel, n, tipo='FOREIGN KEY', valor='-> ' + m.group(1))
            m = ENUM.search(l)
            if m:
                self.item(self.enums, rel, n, valor=m.group(1) or m.group(2))
            m = RELACION.search(l)
            if m and ext != '.sql':
                self.item(self.relaciones, rel, n, tipo=m.group(0).strip('@ ('), valor=enmascarar(s))
            # pantallas
            if es_rutas or ext in ('.tsx', '.jsx', '.vue'):
                m = RUTA_FRONT.search(l)
                if m and (es_rutas or '<Route' in l):
                    self.item(self.pantallas, rel, n, tipo='ruta', valor=m.group(1) or m.group(2) or '')
            # reglas candidatas
            m = VALIDACION.search(l)
            if m:
                self.item(self.reglas, rel, n, tipo='validacion declarativa', valor=enmascarar(m.group(0)))
            m = LANZA.search(l)
            if m:
                cond = ''
                for l2 in reversed(lineas[max(0, n - 4):n - 1]):
                    mc3 = CONDICION.match(l2)
                    if mc3:
                        cond = mc3.group(1).strip()
                        break
                self.item(self.reglas, rel, n, tipo='condicion que frena', valor=enmascarar(m.group(3)), condicion=enmascarar(cond))
            m = CONSTANTE.search(l)
            if m and ext != '.sql' and not s.startswith(('import', 'from')):
                self.item(self.reglas, rel, n, tipo='constante con nombre', valor='%s = %s' % (m.group(1), m.group(2)))
            if CAMBIO_ESTADO.search(l):
                self.item(self.reglas, rel, n, tipo='cambio de estado', valor=enmascarar(s))
            m = CALCULO.search(l)
            if m:
                self.item(self.reglas, rel, n, tipo='funcion de calculo', valor=m.group(1))
            # integraciones
            m = CLIENTE_HTTP.search(l)
            if m and not s.startswith(('import', 'from', 'using')):
                self.item(self.integraciones, rel, n, tipo='cliente HTTP', valor=m.group(1))
            if MENSAJERIA.search(l) and not s.startswith(('import', 'from', 'using')):
                self.item(self.integraciones, rel, n, tipo='mensajeria', valor=enmascarar(s))
            if PROGRAMADA.search(l) and not s.startswith(('import', 'from', 'using')):
                self.item(self.integraciones, rel, n, tipo='tarea programada', valor=enmascarar(s))
            if CORREO_ARCHIVOS.search(l) and not s.startswith(('import', 'from', 'using')):
                self.item(self.integraciones, rel, n, tipo='correo, archivos o almacenamiento', valor=enmascarar(s))
            if AUTENTICACION.search(l) and not s.startswith(('import', 'from', 'using')) and ('(' in l or '@' in l or '=' in l):
                self.item(self.integraciones, rel, n, tipo='autenticacion', valor=enmascarar(s))
            m = CONEXION.search(l)
            if m:
                self.item(self.integraciones, rel, n, tipo='conexion a base o broker', valor=enmascarar(m.group(1)))
            # permisos
            m = PERMISO.search(l)
            if m:
                roles = ROL_LITERAL.findall(l)
                self.item(self.permisos, rel, n, valor=enmascarar(m.group(0)), roles=roles)
            # dependencias
            for rx in IMPORTS:
                m = rx.search(l)
                if m:
                    self._imports.append((rel, n, m.group(1)))
                    break
        if es_modelo:
            for n, l in enumerate(lineas, 1):
                m = CAMPO_ESTADO.search(l)
                if m and ('private' in l or 'val ' in l or 'var ' in l or ':' in l or '=' in l) and not l.strip().startswith(('import', 'from', '//', '*')):
                    self.item(self.campos_estado, rel, n, valor=m.group(0))
                    break

    def resolver_dependencias(self):
        modulos = set(m for m in self.modulos if m != '(raiz)')
        for rel, n, destino in self._imports:
            origen = modulo_de(rel)
            mod_dest, capa = None, None
            if destino.startswith('.'):
                resuelto = os.path.normpath(os.path.join(os.path.dirname(rel), destino)).replace(os.sep, '/')
                mod_dest = modulo_de(resuelto + '/x')
                partes = resuelto.split('/')
                capa = next((p for p in partes if p.lower() in CAPAS_PROHIBIDAS), None)
            else:
                partes = re.split(r'[./\\]', destino)
                for i, p in enumerate(partes):
                    if p in modulos:
                        mod_dest = p
                        capa = next((q for q in partes[i + 1:] if q.lower() in CAPAS_PROHIBIDAS), None)
                        break
            if not mod_dest or mod_dest == origen or mod_dest not in modulos:
                continue
            clave = (origen, mod_dest)
            self.aristas[clave] = self.aristas.get(clave, 0) + 1
            if capa:
                self.cruces.append({'de': origen, 'a': mod_dest, 'capa': capa, 'archivo': rel, 'linea': n, 'import': destino})
        ciclos = sorted(set(tuple(sorted(k)) for k in self.aristas if (k[1], k[0]) in self.aristas))
        return ciclos

    def salida(self):
        ciclos = self.resolver_dependencias()
        return {
            'ruta': self.raiz, 'archivos': self.archivos, 'archivos_leidos': self.leidos,
            'truncado': self.archivos >= self.max_archivos,
            'modulos': [{'modulo': m, 'archivos': n} for m, n in sorted(self.modulos.items(), key=lambda x: -x[1])],
            'api': self.api, 'contrato': self.contrato,
            'modelo': {'entidades': self.entidades, 'tablas': self.tablas, 'enums': self.enums,
                       'relaciones': self.relaciones, 'campos_estado': self.campos_estado},
            'pantallas': self.pantallas, 'reglas_candidatas': self.reglas, 'integraciones': self.integraciones,
            'permisos': self.permisos,
            'dependencias': {'aristas': [{'de': a, 'a': b, 'imports': n} for (a, b), n in sorted(self.aristas.items())],
                             'ciclos': [list(c) for c in ciclos], 'cruces_de_capa': self.cruces},
            'no_mira': ['que hace el negocio con cada endpoint, entidad o regla candidata: eso lo lee la skill, archivo por archivo',
                        'si una validacion es una regla de negocio o un bug: es CANDIDATA hasta que una persona la confirme',
                        'el contenido de los datos ni el trafico real: eso sale de la base y de los logs, con un "si" y sin PHI',
                        'stacks que no estan en las tablas de expresiones: lo que no reconoce no aparece, y hay que decirlo'],
        }


def _id(s):
    return re.sub(r'[^A-Za-z0-9_]', '_', s) or '_'


def mermaid(d):
    out = ['%% Generado por bin/radiografiar-codigo.py sobre %s: hechos del codigo, no un dibujo a mano' % d['ruta']]
    out.append('%% Modulos de primer nivel y sus imports; CRUCE = importa la api o la infra de otro modulo (DEC-002)')
    out.append('flowchart LR')
    for m in d['modulos']:
        if m['modulo'] != '(raiz)':
            out.append('  %s["%s (%d archivos)"]' % (_id(m['modulo']), m['modulo'], m['archivos']))
    cruces = set((c['de'], c['a']) for c in d['dependencias']['cruces_de_capa'])
    for a in d['dependencias']['aristas']:
        if (a['de'], a['a']) in cruces:
            out.append('  %s -. "%d imports, CRUCE DE CAPA" .-> %s' % (_id(a['de']), a['imports'], _id(a['a'])))
        else:
            out.append('  %s -->|%d imports| %s' % (_id(a['de']), a['imports'], _id(a['a'])))
    for c in d['dependencias']['ciclos']:
        out.append('  %% CICLO: %s <-> %s' % (c[0], c[1]))
    tablas = [t for t in d['modelo']['tablas'] if t['origen'] == 'ddl']
    if tablas:
        out.append('')
        out.append('%% Tablas del DDL y sus FOREIGN KEY (las relaciones de los ORM no se dibujan: la radiografia no lee el tipo del campo)')
        out.append('erDiagram')
        for t in tablas:
            out.append('  %s {}' % _id(t['valor']).upper())
        for r in d['modelo']['relaciones']:
            if r['tipo'] != 'FOREIGN KEY':
                continue
            duenas = [t for t in tablas if t['archivo'] == r['archivo'] and t['linea'] <= r['linea']]
            if not duenas:
                continue
            duena = max(duenas, key=lambda t: t['linea'])['valor']
            out.append('  %s }o--|| %s : "FK"' % (_id(duena).upper(), _id(r['valor'].replace('-> ', '')).upper()))
    return '\n'.join(out)


def imprimir(d, tope):
    def seccion(titulo, items, fmt):
        print('')
        print('%s (%d)' % (titulo, len(items)))
        if not items:
            print('  - ninguno reconocido')
        for it in items[:tope]:
            print('  - ' + fmt(it) + '  (%s:%s)' % (it['archivo'], it['linea']))
        if len(items) > tope:
            print('  ... y %d mas (--json trae todo)' % (len(items) - tope))
    print('RADIOGRAFIA de %s  (%d archivos, %d leidos%s)' % (d['ruta'], d['archivos'], d['archivos_leidos'], ', truncado' if d['truncado'] else ''))
    print('  Modulos de primer nivel: ' + ', '.join('%s (%d)' % (m['modulo'], m['archivos']) for m in d['modulos'][:12]))
    seccion('API implementada', d['api'], lambda it: '%s %s [%s]' % (it['metodo'], it['ruta'], it['marco']))
    seccion('Rutas declaradas en un contrato', d['contrato'], lambda it: it['ruta'])
    mo = d['modelo']
    seccion('Entidades', mo['entidades'], lambda it: '%s [%s]' % (it['valor'], it['marco']))
    seccion('Tablas', mo['tablas'], lambda it: '%s [%s]' % (it['valor'], it['origen']))
    seccion('Enums (candidatos a estados)', mo['enums'], lambda it: it['valor'])
    seccion('Relaciones', mo['relaciones'], lambda it: '%s %s' % (it['tipo'], it['valor']))
    seccion('Campos de estado (candidatos a maquina de estados)', mo['campos_estado'], lambda it: it['valor'])
    seccion('Pantallas y rutas del front', d['pantallas'], lambda it: '%s: %s' % (it['tipo'], it['valor']))
    seccion('Reglas CANDIDATAS (confirmar con una persona)', d['reglas_candidatas'],
            lambda it: '%s: %s%s' % (it['tipo'], it['valor'], ('  <- si ' + it['condicion']) if it.get('condicion') else ''))
    seccion('Integraciones', d['integraciones'], lambda it: '%s: %s' % (it['tipo'], it['valor']))
    seccion('Permisos', d['permisos'], lambda it: '%s%s' % (it['valor'], (' roles ' + ','.join(it['roles'])) if it['roles'] else ''))
    dep = d['dependencias']
    print('')
    print('Dependencias entre modulos (%d aristas, %d ciclos, %d cruces de capa)' % (len(dep['aristas']), len(dep['ciclos']), len(dep['cruces_de_capa'])))
    for a in dep['aristas'][:tope]:
        print('  - %s -> %s (%d imports)' % (a['de'], a['a'], a['imports']))
    for c in dep['ciclos'][:tope]:
        print('  - CICLO %s <-> %s' % (c[0], c[1]))
    for c in dep['cruces_de_capa'][:tope]:
        print('  - CRUCE DE CAPA %s importa %s/%s  (%s:%s)' % (c['de'], c['a'], c['capa'], c['archivo'], c['linea']))
    print('')
    print('Lo que este script NO mira:')
    for x in d['no_mira']:
        print('  - ' + x)


def main():
    ap = argparse.ArgumentParser(description='Radiografia de una aplicacion existente (solo lectura).')
    ap.add_argument('ruta')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--mermaid', action='store_true', help='diagramas Mermaid (modulos y ER) en vez del resumen')
    ap.add_argument('--max-archivos', type=int, default=20000)
    ap.add_argument('--tope', type=int, default=40, help='items por seccion en el texto')
    a = ap.parse_args()
    raiz = os.path.abspath(a.ruta)
    if not os.path.isdir(raiz):
        print('SIN DATOS -- no existe la carpeta %s' % raiz)
        return SIN_DATOS
    r = Radiografia(raiz, a.max_archivos)
    r.recorrer()
    if r.archivos == 0:
        print('SIN DATOS -- la carpeta %s no tiene archivos (fuera de los ignorados).' % raiz)
        return SIN_DATOS
    d = r.salida()
    if a.json:
        print(json.dumps(d, ensure_ascii=True, indent=1))
    elif a.mermaid:
        print(mermaid(d))
    else:
        imprimir(d, a.tope)
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
