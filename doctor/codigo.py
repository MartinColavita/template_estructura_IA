#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CALIBRACION. Las sondas de codigo estan calibradas para repositorios que se reconocen
# por un pom.xml, un build.gradle(.kts) o un package.json (MARCAS), con las extensiones
# de EXTENSIONES y las herramientas de calidad de CALIDAD_JAVA / CALIDAD_NODE. Para otro
# stack hay que ampliar esas tablas -MARCAS, EXTENSIONES, CALIDAD_*- y, si hace falta,
# PRACTICAS. Sin eso el Doctor no encuentra la unidad de codigo y las sondas quedan en
# SIN DATOS, que no es aprobado. Los patrones de deteccion que siguen (pipeline de SAST,
# anotaciones, archivos de build) son eso, deteccion: no prescriben un stack.
"""
Sondas de CODIGO del Doctor de {{PROYECTO}}.

Viven aparte de doctor.py por una razon concreta: aquellas trece miden DOCUMENTACION
y configuracion del proyecto, y corren siempre. Estas miden el codigo de los repos
que se clonan adentro de back/ y front/, y solo tienen sentido cuando ese codigo
esta. Separarlas deja explicito que son dos cosas distintas, y evita que doctor.py
siga creciendo sin control.

CONTRATO con doctor.py: este modulo NO importa nada de aquel — no habria forma sin
un ciclo, y peor: doctor.py corre como __main__, asi que un `import doctor` cargaria
una SEGUNDA copia del modulo con su propio ALCANCE, y las sondas leerian el valor
equivocado. En cambio doctor.py deja en CTX lo que hace falta, justo antes de
correr. Es una linea de acoplamiento, explicita y en un solo lugar.

QUE NO HACE, a proposito:

  - NO reemplaza a SAST ni a un analizador estatico. Esas herramientas hacen
    FALLAR EL BUILD, que es una barrera mucho mas fuerte que un informe que alguien
    tiene que acordarse de leer. Competir con ellas seria escribir peor lo que ya
    esta bien hecho. El Doctor mide lo que ellas NO cubren: las reglas propias de
    este proyecto -los slices, el contrato, la trazabilidad al ticket- y si la
    puerta de calidad esta puesta Y exigida por el build.

  - NO llama a la red, ni a Azure, ni a un modelo. Todo sale de archivos locales.
    Por eso la corrida sigue costando segundos, y no hace falta el aviso de costo
    que el README daba por necesario: lo caro era mandarle codigo a un modelo, y
    estas sondas no lo hacen.

  - NO marca estilo. Indentacion, comillas y punto y coma son del formateador. Una
    sonda que grita lobo es peor que no tenerla: se deja de leer el informe entero.
"""
import hashlib
import os
import re

# ------------------------------------------------------------------- acoplamiento

# doctor.py lo llena antes de correr. Claves: root, alcance, res, leer, rel, git,
# cierre y -opcional- slots, que solo usa la prueba contra el repo de ejemplo.
CTX = {}


def _res(*a, **k):
    return CTX["res"](*a, **k)


def _leer(p):
    return CTX["leer"](p)


def _cierre():
    return CTX.get("cierre", "")


# ------------------------------------------------------------------------- util

# Carpetas que NO son codigo fuente: artefactos de build, dependencias bajadas y
# codigo generado. Recorrerlas no solo es caro, es DANINO: target/ y node_modules/
# tienen miles de archivos ajenos que ensuciarian cada medicion.
BASURA = {".git", "node_modules", "target", "build", "out", "dist", ".gradle",
          ".mvn", "coverage", ".next", ".nuxt", ".vite", "__pycache__", "vendor",
          ".venv", "generated", "generated-sources", "bin", "obj"}

# Como se reconoce la raiz de una unidad de codigo. El primero que aparezca gana.
MARCAS = [("pom.xml", "java-maven"), ("build.gradle", "java-gradle"),
          ("build.gradle.kts", "java-gradle"), ("package.json", "node")]

EXTENSIONES = {"java-maven": (".java",), "java-gradle": (".java", ".kt"),
               "node": (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts")}

# Las capas del monolito modular por modulos de negocio (DEC-002): las cuatro de
# siempre mas `exceptions/`, que vive por fuera de ellas y la usan todas. En el
# codigo se dice "modulo"; en el tablero sigue siendo "slice = Epica" (P-054).
CAPAS = ("api", "application", "domain", "infra", "exceptions")

# Entre modulos se LLAMA solo a la application del otro, y se pueden importar los
# tipos que sus casos de uso devuelven o lanzan: su domain y sus exceptions. La api
# es un adaptador HTTP, no un contrato interno; la infra es un detalle. Esas dos,
# prohibidas desde afuera.
PERMITIDO_ENTRE = ("application", "domain", "exceptions")

# El modulo transversal: no depende de ningun modulo y lo puede usar cualquiera.
SHARED = "shared"

TOPE_ARCHIVOS = 20000


def _dirs(p):
    try:
        return sorted(d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)))
    except Exception:
        return []


def _rel(p):
    return os.path.relpath(p, CTX["root"]).replace("\\", "/")


def slots():
    """Las carpetas preparadas para alojar un repositorio de codigo.

    NO es una lista de nombres. Se detectan por una senal que el propio proyecto ya
    dejo puesta: tienen su espejo de skills scoped -.claude/skills o .agents/skills-,
    que es exactamente como este ecosistema declara "aca va a vivir un repo con sus
    propias reglas de desarrollo". Hoy son back/ y front/; manana pueden ser tres
    fronts, y el Doctor no se entera de nada.

    Con --repo, la carpeta pedida es el slot exista o no el espejo: el humano fue
    explicito, y eso pesa mas que la convencion."""
    if CTX.get("slots") is not None:
        return list(CTX["slots"])
    if CTX.get("alcance"):
        return [CTX["alcance"]]
    root = CTX["root"]
    out = []
    for d in _dirs(root):
        if d in BASURA or d.startswith("."):
            continue
        for conv in (".claude/skills", ".agents/skills"):
            if os.path.isdir(root + "/" + d + "/" + conv):
                out.append(d)
                break
    return out


def _buscar_unidades(p, slot, prof, out):
    if prof > 3 or not os.path.isdir(p):
        return
    try:
        nombres = os.listdir(p)
    except Exception:
        return
    for marca, stack in MARCAS:
        if marca in nombres:
            # El marcador MAS ALTO gana, y no se baja mas: un multi-modulo de Maven
            # es UNA unidad, no una por submodulo.
            out.append({"ruta": _rel(p), "raiz": p.replace("\\", "/"),
                        "stack": stack, "slot": slot})
            return
    for d in sorted(nombres):
        if d in BASURA or d.startswith("."):
            continue
        _buscar_unidades(os.path.join(p, d), slot, prof + 1, out)


def unidades():
    """Las unidades de codigo que hay hoy, dentro de los slots.

    Cada unidad se acuerda de QUE SLOT salio, en vez de que despues se deduzca
    partiendo su ruta por la primera barra. Deducirlo funcionaba mientras los slots
    fueran back/ y front/ y fallaba en silencio con uno anidado -apps/portal,
    equipo/web-: la unidad aparecia y el slot quedaba reportado como vacio."""
    out = []
    for s in slots():
        _buscar_unidades(CTX["root"] + "/" + s, s, 0, out)
    return out


def es_java(u):
    return u["stack"].startswith("java")


def fuentes(u):
    """Los archivos de codigo de una unidad, ya sin artefactos ni dependencias."""
    exts = EXTENSIONES.get(u["stack"], ())
    out = []
    for b, dirs, files in os.walk(u["raiz"]):
        dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
        for fn in files:
            if fn.endswith(exts):
                out.append(os.path.join(b, fn).replace("\\", "/"))
                if len(out) >= TOPE_ARCHIVOS:
                    return out
    return out


def es_test(p):
    """Un archivo de test. Se mira aparte casi siempre, porque las reglas de
    produccion no son las de un test: un test SI puede tocar las entranas de lo
    que prueba, y esa es su gracia."""
    q = p.replace("\\", "/")
    if "/src/test/" in q or "/__tests__/" in q:
        return True
    if re.search(r"\.(test|spec)\.[a-z]+$", q.lower()):
        return True
    # SIN lowercasear y exigiendo el limite de palabra. Antes era
    # q.lower().endswith("it.java"), y eso daba por test a Limit, Unit, Audit,
    # Visit, Deposit, Credit, Permit... nombres perfectamente plausibles en
    # cualquier dominio de negocio. Cada uno de esos archivos quedaba
    # excluido de cuatro sondas sin que nada lo dijera.
    return re.search(r"(?:Test|Tests|IT)\.java$", os.path.basename(q)) is not None


def slices_de(u):
    """Los slices de una unidad: nombre -> ruta absoluta.

    En Java se busca la carpeta que CONTIENE las capas, a cualquier profundidad, y
    no una ruta fija: el layout real de Maven -src/main/java/<paquete>/<slice>/...-
    no es el que dibuja el README de back/, y clavar uno de los dos deja la sonda
    ciega contra el otro.

    En el front no existe esa convencion de capas, asi que el slice es cada carpeta
    bajo features/, modules/ o slices/. Si no hay ninguna, la unidad entera es un
    slice — y entonces "cruzar un limite" pasa a significar que dos aplicaciones
    distintas del front se importan entre si, que es igual de grave."""
    found = {}
    if es_java(u):
        for b, dirs, files in os.walk(u["raiz"]):
            dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
            q = b.replace("\\", "/")
            # El arbol de test es un ESPEJO del de produccion -src/test/java/.../
            # <slice>/{api,domain}- en todo proyecto Maven. Como los slices se
            # indexan por nombre de carpeta, el de test pisaba al de produccion y
            # a partir de ahi slice_de() devolvia None para TODOS los archivos de
            # produccion de ese slice: quedaban fuera de limites y de duplicacion,
            # y el resumen seguia declarando que los habia mirado. No gritaba
            # lobo: hacia lo contrario, que es peor.
            if "/src/test/" in q + "/":
                continue
            # Basta UNA capa. Con dos, un slice que todavia solo tiene api -o un
            # modulo solo de dominio- no se detectaba, y sus archivos quedaban sin
            # slice, o sea sin medir.
            if [d for d in dirs if d in CAPAS]:
                found[os.path.basename(b)] = q
        return found
    for b, dirs, files in os.walk(u["raiz"]):
        dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
        if os.path.basename(b) in ("features", "modules", "slices"):
            for d in dirs:
                found[d] = os.path.join(b, d).replace("\\", "/")
    if not found:
        found[os.path.basename(u["raiz"])] = u["raiz"]
    return found


def slice_de(ruta, slices):
    """A que slice pertenece un archivo. Gana el match MAS LARGO, para que un slice
    anidado no quede absorbido por el que lo contiene."""
    mejor, largo = None, -1
    q = ruta.replace("\\", "/")
    for nombre, base in slices.items():
        if q.startswith(base + "/") and len(base) > largo:
            mejor, largo = nombre, len(base)
    return mejor


def sin_codigo(titulo, que_mide):
    """El resultado uniforme cuando todavia no hay codigo que medir.

    SIN DATOS y nunca OK: la regla del cero de este proyecto dice que un conteo
    vacio sobre una entrada externa es NO AUDITABLE, jamas un aprobado. Un repo que
    no se clono no esta sano — no se miro."""
    return _res(titulo, "SIN DATOS",
                "Todavia no hay codigo en las carpetas de los repos, asi que esta sonda "
                "no midio nada.",
                significa=que_mide + " Mide sobre el codigo de los repositorios que se "
                          "clonan dentro de back/ y front/, y hoy esas carpetas solo "
                          "tienen su README y sus skills.",
                importa="SIN DATOS no es aprobado: quiere decir que este aspecto quedo sin "
                        "revisar, no que este bien. Cuando el codigo este, la sonda empieza "
                        "a medir sola.",
                acciones=[{"paso": "Cloná el repositorio de codigo dentro de la carpeta que le "
                                   "corresponde -back/ para el backend, front/ para cada "
                                   "aplicacion de front- y volve a correr el Doctor. No hay "
                                   "nada que configurar: la sonda lo encuentra.",
                           "comando": "bash doctor/bin/doctor.sh"}])


def nada_medido(titulo, que_mide, cuantos, unidad="archivo(s)"):
    """SIN DATOS cuando no se midio NADA, aunque el repositorio exista.

    La regla del cero de este proyecto: un conteo vacio sobre una entrada externa es
    NO AUDITABLE, nunca un aprobado. Faltaba justo el caso del medio — habia unidad
    de codigo pero estaba vacia, o todavia sin ordenar en capas — y ahi la sonda
    devolvia OK sobre cero mediciones. Un repositorio a medio armar salia en verde."""
    return _res(titulo, "SIN DATOS",
                "No se midio ni un " + unidad.replace("(s)", "") + ": hay repositorio "
                "clonado, pero nada que esta sonda pueda leer todavia.",
                significa=que_mide + " Encontro " + str(cuantos) + " " + unidad + " "
                          "para mirar, asi que no midio nada.",
                importa="SIN DATOS no es aprobado. Un repositorio recien clonado, o "
                        "todavia sin ordenar en slices y capas, no esta sano: esta sin "
                        "revisar. Decir 'cero problemas' sobre cero archivos es mentir "
                        "con verde.",
                acciones=[{"paso": "Verifica que el repositorio clonado tenga su codigo "
                                   "fuente donde se lo espera, y que los modulos tengan "
                                   "sus carpetas de capa (api, application, domain, "
                                   "infra, exceptions)."},
                          {"paso": "Volve a correr el Doctor cuando haya codigo.",
                           "comando": "bash doctor/bin/doctor.sh"}])


def fila_estado(filas, col=-1):
    """HALLAZGO si alguna fila lo dice. Centralizado para que ninguna sonda se
    contradiga con su propia tabla — es lo primero que marca el autocontrol."""
    return "HALLAZGO" if any(f[col] == "HALLAZGO" for f in filas) else "OK"


def recortar(filas, tope=40):
    """El informe no mejora por tener 400 filas iguales: mejora por tener las 40
    que alguien va a mirar. Se prioriza lo que esta en hallazgo."""
    if len(filas) <= tope:
        return filas, 0
    malas = [f for f in filas if f[-1] == "HALLAZGO"]
    resto = [f for f in filas if f[-1] != "HALLAZGO"]
    corte = (malas + resto)[:tope]
    return corte, len(filas) - tope


# ------------------------------------------------------------- 1. repos conectados

def sonda_repos():
    """Que repos de codigo estan enchufados hoy. Corre SIEMPRE: es la que explica
    por que las otras ocho miden o no miden."""
    ss = slots()
    us = unidades()
    por_slot = {}
    for u in us:
        por_slot.setdefault(u["slot"], []).append(u)

    filas = []
    for s in ss:
        mias = por_slot.get(s, [])
        if not mias:
            filas.append([s + "/", "solo el README y las skills", "-",
                          "todavia no se clono el repositorio de codigo aca", "SIN DATOS"])
            continue
        for u in mias:
            arch = fuentes(u)
            sl = slices_de(u)
            # Una unidad VACIA no es una unidad sana. Existia el archivo de build y
            # nada mas -un repositorio recien creado, o uno a medio ordenar- y esta
            # sonda decia OK y "las ocho corren sobre todas", cuando en realidad las
            # ocho no median nada. La regla del cero vale tambien aca.
            if not arch:
                filas.append([u["ruta"] + "/", "0 archivos de codigo", u["stack"],
                              "hay " + ("pom.xml" if es_java(u) else "package.json") +
                              " pero no se encontro codigo fuente adentro", "SIN DATOS"])
            else:
                filas.append([u["ruta"] + "/", str(len(arch)) + " archivo(s) de codigo",
                              u["stack"],
                              str(len(sl)) + " slice(s): " + (", ".join(sorted(sl)) or "-"),
                              "OK"])
    if not ss:
        return _res("Repos de codigo conectados", "SIN DATOS",
                    "No se encontro ninguna carpeta preparada para alojar un repositorio "
                    "de codigo.",
                    significa="El Doctor busca las carpetas que tienen su propio espejo de "
                              "skills -esa es la senal de que ahi va a vivir un repositorio "
                              "con sus reglas de desarrollo- y no encontro ninguna.",
                    importa="SIN DATOS no es aprobado: sin esas carpetas, las otras nueve "
                            "sondas de codigo no tienen donde mirar.",
                    acciones=[{"paso": "Corre el Doctor parado en la raiz del repositorio."},
                              {"paso": "Si queres apuntar a una carpeta puntual, nombrala.",
                               "comando": "bash doctor/bin/doctor.sh --repo back"}])

    # Los nombres en criollo de SOLO_CON_CODIGO, para nombrarlas en el resumen. Si se
    # agrega una sonda alla, va tambien aca: son nueve y el texto lo dice en palabras.
    DORMIDAS = ("limites del diseno, contrato declarado vs implementado, la costura "
                "entre back y front, trazabilidad test-Tarea, duplicacion entre slices, "
                "dependencias sin usar, puerta de seguridad, puerta de calidad y "
                "practicas y patrones")
    con_codigo = [f for f in filas if f[4] == "OK"]
    estado = "OK" if len(con_codigo) == len(filas) else "SIN DATOS"
    resumen = (str(len(con_codigo)) + " de " + str(len(filas)) + " carpeta(s) con codigo. ")
    if estado == "OK":
        resumen += "Las nueve sondas de codigo corren sobre todas."
    else:
        resumen += ("Mientras falte codigo, estas nueve sondas quedan dormidas: " +
                    DORMIDAS + ".")
    return _res("Repos de codigo conectados", estado, resumen,
        (["Carpeta", "Contenido", "Stack", "Detalle", "Estado"], filas),
        significa="El backend y cada front viven en su PROPIO repositorio de git, y se "
                  "clonan adentro de estas carpetas para que las herramientas puedan leer "
                  "todo localmente, de una sola vez, sin saltar entre proyectos. Esta sonda "
                  "dice cuales estan enchufados hoy y con que stack.",
        importa="Es la sonda que explica a las otras nueve. Una carpeta sin codigo no es un "
                "error -nadie clono todavia- pero tampoco es un aprobado: significa que la "
                "mitad del Doctor no esta midiendo, y conviene saberlo antes de leer el "
                "resto del informe como si estuviera completo.",
        acciones=[] if estado == "OK" else [
            {"paso": "Cloná cada repositorio de codigo dentro de su carpeta. El contenido "
                     "clonado NO se versiona en este repositorio: esta ignorado a proposito, "
                     "porque cada uno tiene su propio git."},
            {"paso": "Volve a correr el Doctor. Las nueve sondas se encienden solas.",
             "comando": "bash doctor/bin/doctor.sh"},
            {"paso": "Si solo queres mirar un repositorio, acotá la corrida.",
             "comando": "bash doctor/bin/doctor.sh --repo back"}])


# ------------------------------------------------------------ 2. limites del diseno

# Que puede importar cada capa DENTRO de su propio modulo (DEC-002). La flecha va
# siempre hacia el nucleo: api usa application, application usa domain, e infra
# IMPLEMENTA las interfaces que application declara en gateway/ y repository/ -por
# eso infra si puede importar application-. exceptions la usan todas y no depende
# de ninguna capa. Lo que NO esta listado, esta prohibido.
PERMITIDO_ADENTRO = {
    "api": ("api", "application", "domain", "exceptions"),
    "application": ("application", "domain", "exceptions"),
    "domain": ("domain", "exceptions"),
    "infra": ("infra", "application", "domain", "exceptions"),
    "exceptions": ("exceptions",),
}

MOTIVO_CAPA = {
    ("api", "infra"): "la capa de entrada habla directo con la persistencia o el servicio "
                      "externo, salteando el caso de uso de application",
    ("application", "api"): "la logica depende de como se expone, que es al reves de como "
                            "tiene que ser",
    ("application", "infra"): "el caso de uso depende de un detalle tecnico; lo que hace "
                              "falta es que application declare la interfaz en gateway/ o "
                              "repository/ y que infra la implemente",
    ("domain", "infra"): "el dominio depende de un detalle tecnico; lo que hace falta es "
                         "que application declare la interfaz y que infra la implemente",
    ("domain", "api"): "el dominio depende de como se expone",
    ("domain", "application"): "el dominio depende de quien lo orquesta",
    ("infra", "api"): "la infraestructura depende de la capa de entrada",
    ("exceptions", "api"): "una excepcion depende de una capa; exceptions no depende de "
                           "ninguna, solo de shared.exceptions",
    ("exceptions", "application"): "una excepcion depende de una capa; exceptions no "
                                   "depende de ninguna, solo de shared.exceptions",
    ("exceptions", "domain"): "una excepcion depende de una capa; exceptions no depende "
                              "de ninguna, solo de shared.exceptions",
    ("exceptions", "infra"): "una excepcion depende de una capa; exceptions no depende de "
                             "ninguna, solo de shared.exceptions",
}


def _capa_de(ruta, base_slice):
    resto = ruta[len(base_slice) + 1:].split("/")
    return resto[0] if resto and resto[0] in CAPAS else None


def _limites_java(u, slices, filas):
    for p in fuentes(u):
        if es_test(p):
            continue
        mi_slice = slice_de(p, slices)
        if not mi_slice:
            continue
        mi_capa = _capa_de(p, slices[mi_slice])
        # El `*` del final tiene que entrar en la captura: `import x.y.domain.*;`
        # era invisible, y el wildcard es justamente el import que cruza un limite
        # de a paquetes enteros en vez de de a una clase.
        for imp in re.findall(r"^\s*import\s+(?:static\s+)?([\w.]+\*?)\s*;", _leer(p), re.M):
            partes = imp.split(".")
            # Un import que cruza a otro modulo: el paquete nombra un modulo conocido
            # que NO es el mio, seguido de una capa. Se exigen las DOS cosas para no
            # marcar un `com.ejemplo.<modulo-a>.Utiles` que solo comparte nombre.
            for j, seg in enumerate(partes[:-1]):
                if seg in slices and seg != mi_slice and partes[j + 1] in CAPAS:
                    destino = partes[j + 1]
                    regla = None
                    if mi_slice == SHARED:
                        # shared es transversal: si depende de un modulo, deja de
                        # serlo, y el modulo ya no se puede mover sin arrastrarlo.
                        regla = ("shared depende del modulo " + seg + "; shared no "
                                 "depende de ningun modulo, son los modulos los que "
                                 "usan shared")
                    elif seg == SHARED:
                        # Cualquier modulo puede usar shared. La unica excepcion es
                        # exceptions/, que solo se apoya en shared.exceptions.
                        if mi_capa == "exceptions" and destino != "exceptions":
                            regla = ("exceptions depende de shared." + destino + "; "
                                     "exceptions solo se apoya en shared.exceptions")
                    elif mi_capa == "exceptions":
                        regla = ("exceptions depende del modulo " + seg + "; exceptions "
                                 "no depende de ninguna capa, solo de shared.exceptions")
                    elif destino not in PERMITIDO_ENTRE:
                        regla = ("entra a la capa " + destino + " de " + seg + ", que es "
                                 "privada de ese modulo; entre modulos se llama a su "
                                 "application y se usan sus tipos de domain o exceptions")
                    if regla:
                        filas.append([_rel(p), mi_slice or "-",
                                      seg + "." + destino, regla, "HALLAZGO"])
                    break
                if seg == mi_slice and mi_capa and partes[j + 1] in CAPAS:
                    destino = partes[j + 1]
                    if destino not in PERMITIDO_ADENTRO.get(mi_capa, CAPAS):
                        filas.append([_rel(p), mi_slice, mi_capa + " -> " + destino,
                                      MOTIVO_CAPA.get((mi_capa, destino),
                                                      "la capa " + mi_capa + " no puede "
                                                      "depender de " + destino),
                                      "HALLAZGO"])
                    break


def alias_de(u):
    """Los alias de ruta que declara el tsconfig de la unidad: "@features/*" pasa a
    "src/features/*".

    Se LEEN, en vez de clavar "@/" y "~/" como estaba antes. Con un alias distinto
    -"@features/*" es convencion comun en Vite- la sonda de limites del front no
    resolvia un solo import: no medida nada y reportaba OK. Ciega y en verde, que es
    la peor combinacion posible, porque nadie va a ir a buscar el problema."""
    if u.get("_alias") is not None:
        return u["_alias"]
    mapa = {}
    txt = _leer(u["raiz"] + "/tsconfig.json") or _leer(u["raiz"] + "/jsconfig.json")
    bloque = re.search(r'"paths"\s*:\s*\{(.*?)\n\s*\}', txt, re.S)
    if bloque:
        for k, v in re.findall(r'"([^"]+)"\s*:\s*\[\s*"([^"]+)"', bloque.group(1)):
            mapa[k.rstrip("*")] = v.rstrip("*")
    # Los dos de siempre quedan de respaldo: si el proyecto no declara paths, siguen
    # valiendo porque son la convencion por defecto de muchas plantillas de Vite.
    mapa.setdefault("@/", "src/")
    mapa.setdefault("~/", "src/")
    u["_alias"] = mapa
    return mapa


def _resolver_import(p, spec, u):
    """De un import del front a una ruta de archivo, sin resolver extensiones: solo
    hace falta saber DONDE cae, no cual de los cinco archivos posibles es."""
    if spec.startswith("."):
        return os.path.normpath(os.path.join(os.path.dirname(p), spec)).replace("\\", "/")
    mapa = alias_de(u)
    for pre in sorted(mapa, key=len, reverse=True):
        if spec.startswith(pre):
            destino = mapa[pre] + spec[len(pre):]
            return os.path.normpath(os.path.join(u["raiz"], destino)).replace("\\", "/")
    return None                       # un paquete de node_modules: no es asunto de esta sonda


def _limites_front(u, slices, filas):
    publico = re.compile(r"/(index|api|public)(\.[a-z]+)?$")
    for p in fuentes(u):
        if es_test(p):
            continue
        mi_slice = slice_de(p, slices)
        cuerpo = _leer(p)
        specs = re.findall(r"""(?:from|import|require)\s*\(?\s*["']([^"']+)["']""", cuerpo)
        for spec in specs:
            destino = _resolver_import(p, spec, u)
            if not destino:
                continue
            otro = slice_de(destino, slices)
            if not otro or otro == mi_slice:
                continue
            # Se permite entrar por la puerta: el index del slice o su carpeta api/.
            adentro = destino[len(slices[otro]):]
            if publico.search(destino) or adentro.startswith("/api/") or adentro in ("", "/"):
                continue
            filas.append([_rel(p), mi_slice or "-", spec,
                          "entra a " + otro + " por adentro; la puerta es su index o su "
                          "carpeta api/", "HALLAZGO"])


def sonda_limites():
    us = unidades()
    if not us:
        return sin_codigo("Limites del diseno",
                          "Verifica que ningun modulo entre a la api o la infra de otro, y que "
                          "adentro de cada modulo las capas no se saltean.")
    filas, mirados, total_slices = [], 0, 0
    for u in us:
        slices = slices_de(u)
        total_slices += len(slices)
        # Solo los que CAEN en un slice. Antes se contaban todos los de produccion,
        # asi que el resumen declaraba una cobertura que la sonda no tuvo: los que
        # quedan fuera de todo slice no se miran, y decir que si es peor que no medir.
        mirados += len([p for p in fuentes(u)
                        if not es_test(p) and slice_de(p, slices)])
        (_limites_java if es_java(u) else _limites_front)(u, slices, filas)

    if not mirados or not total_slices:
        return nada_medido("Limites del diseno",
                           "Verifica que ningun modulo entre a la api o la infra de otro, y "
                           "que adentro de cada modulo las capas no se salteen.",
                           mirados, "archivo(s) de produccion en " +
                           str(total_slices) + " modulo(s)")
    filas, ocultas = recortar(filas)
    estado = fila_estado(filas) if filas else "OK"
    resumen = (str(mirados) + " archivo(s) de produccion en " + str(total_slices) +
               " modulo(s). ")
    resumen += ("Ningun import cruza un limite." if estado == "OK" else
                str(len(filas) + ocultas) + " import(s) rompen un limite" +
                ("." if not ocultas else ", se muestran los primeros " + str(len(filas)) + "."))
    return _res("Limites del diseno", estado, resumen,
        (["Archivo", "Modulo", "Import", "Regla que rompe", "Estado"], filas) if filas else None,
        significa="La arquitectura es un monolito modular (DEC-002): cada modulo es dueno "
                  "de un concepto de negocio -<modulo-a>, <modulo-b>- y adentro tiene cuatro "
                  "capas (api, application, domain, infra) mas exceptions/; shared es el "
                  "modulo transversal. Entre modulos se llama a la application del otro y "
                  "se pueden usar sus tipos de domain y exceptions; su api y su infra son "
                  "privadas. Esta sonda lee los imports y marca tres cosas: un modulo que "
                  "entra a la api o la infra de otro, shared dependiendo de un modulo, y "
                  "una capa que se saltea a otra adentro del mismo modulo -por ejemplo la "
                  "capa de entrada hablando directo con la base-. En el front, el slice "
                  "se entra por su index o su carpeta api/.",
        importa="Es el chequeo que el criterio de terminado de CADA Tarea ya declara y que "
                "hoy no verifica nadie. Cuando los limites se filtran, el monolito modular "
                "deja de ser modular sin que nadie tome la decision: un dia no se puede "
                "tocar un slice sin romper otro, y para entonces son cientos de imports. "
                "Marcarlo de a uno, temprano, cuesta minutos.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada cruce entre modulos: mira QUE necesita el que importa. Casi "
                     "siempre alcanza con un caso de uso en la application del modulo de "
                     "destino que devuelva tipos de su domain, y llamar a ese. En el front, "
                     "exponerlo en el index o la api/ del slice."},
            {"paso": "Si lo que necesita no deberia salir de ese modulo, entonces el problema "
                     "es el reparto: esa logica esta en el modulo equivocado, o los dos "
                     "modulos son en realidad uno. Si es shared el que depende de un modulo, "
                     "eso no es transversal: va adentro del modulo."},
            {"paso": "Por cada salto de capa: el caso tipico es la capa de entrada llamando "
                     "a la persistencia. La salida es meter el caso de uso en application, "
                     "con su interfaz en application/repository o application/gateway, y "
                     "que la entrada llame a ese."},
            {"paso": "Cuando el patron se estabilice, mové este chequeo a ArchUnit: ahi hace "
                     "FALLAR EL BUILD, que frena mucho mas que un informe. El Doctor te dice "
                     "cuales son las reglas que valen la pena escribir."}],
        pedido=None if estado == "OK" else (
            "En el codigo hay imports que rompen los limites del monolito modular "
            "(DEC-002). Cada modulo tiene capas api/application/domain/infra mas "
            "exceptions/; adentro, api -> application, domain; application -> domain; "
            "infra -> application, domain; domain -> nada. Entre modulos se llama a la "
            "application del otro y se usan sus tipos de domain y exceptions; su api y su "
            "infra son privadas. shared no depende de ningun modulo.\n\n" +
            "\n".join("- " + f[0] + " (modulo " + f[1] + "): " + f[2] + " — " + f[3]
                      for f in filas[:20]) +
            "\n\nPor cada uno, abri el archivo y decime QUE necesita realmente del otro lado. "
            "Despues proponeme una de estas tres salidas, la que corresponda: un caso de uso "
            "en la application del modulo de destino, mover la logica al modulo que la tiene "
            "que tener, o meter un caso de uso en application si lo que pasa es un salto de "
            "capa. Decime "
            "tambien cuales de estas reglas convendria escribir como test de ArchUnit para "
            "que el build las frene solo." + _cierre()))


# --------------------------------------------------- 3. contrato vs implementacion

VERBOS = ("get", "post", "put", "delete", "patch", "head", "options")


def _ops_del_contrato(txt, es_json=False):
    """Los pares metodo+ruta que declara un contrato OpenAPI.

    Sin libreria de YAML: este proyecto no admite dependencias externas. Pero JSON SI
    entra, porque viene en la biblioteca estandar — y antes el .json se aceptaba como
    archivo y despues se lo intentaba leer como YAML, con lo cual no salia ni una
    operacion y TODOS los endpoints del codigo pasaban a "implementada sin declarar".
    Quarkus sirve /q/openapi y lo que se commitea suele ser .json, asi que el caso es
    de los probables, no de los raros."""
    if es_json:
        return _ops_del_contrato_json(txt)
    ops, dentro, ruta, sangria = set(), False, None, None
    prefijo = _servers_de(txt)
    for linea in txt.splitlines():
        if re.match(r"^paths\s*:", linea):
            dentro = True
            continue
        if dentro and linea.strip() and not linea.startswith((" ", "	")):
            break                     # se termino el bloque paths:
        if not dentro:
            continue
        # La ruta puede venir entrecomillada: "/x": es YAML valido y se perdia.
        m = re.match(r"^(\s+)[\"']?(/[^\s:\"']*)[\"']?\s*:\s*$", linea)
        if m:
            sangria, ruta = len(m.group(1)), m.group(2)
            continue
        m = re.match(r"^(\s+)(" + "|".join(VERBOS) + r")\s*:\s*$", linea)
        # HIJO DIRECTO de la ruta, no "mas adentro que la ruta". Un schema con un
        # campo llamado delete, get u options generaba operaciones fantasma: se probo
        # con un requestBody que tenia `properties: delete: type: boolean` y salia un
        # DELETE que no existe en ningun lado.
        if m and ruta and sangria is not None:
            if len(m.group(1)) == sangria + _paso(txt, sangria):
                ops.add(m.group(2).upper() + " " + normalizar_ruta(prefijo + ruta))
    return ops


def _paso(txt, sangria):
    """Cuantos espacios usa este archivo por nivel de anidado. Casi siempre 2, pero
    se mide en vez de asumirse."""
    for linea in txt.splitlines():
        m = re.match(r"^(\s+)\S", linea)
        if m and 0 < len(m.group(1)) <= 8:
            return len(m.group(1))
    return 2


def _servers_de(txt):
    """El prefijo que declara el bloque servers: del contrato.

    Si el contrato dice /api/recursos y el codigo /recursos, sin esto
    NINGUNA operacion cruza y el informe sale entero en rojo sobre un back correcto."""
    m = re.search(r"^servers\s*:\s*$", txt, re.M)
    if not m:
        return ""
    for linea in txt[m.end():].splitlines():
        if linea.strip() and not linea.startswith((" ", "	", "-")):
            break
        u = re.search(r"url\s*:\s*[\"']?([^\s\"']+)", linea)
        if u:
            ruta = re.sub(r"^https?://[^/]+", "", u.group(1))
            return "" if ruta in ("", "/") else "/" + ruta.strip("/")
    return ""


def _ops_del_contrato_json(txt):
    """Lo mismo, para un contrato en JSON. Aca si se puede parsear de verdad."""
    import json as _json
    try:
        d = _json.loads(txt)
    except Exception:
        return set()
    prefijo = ""
    srv = d.get("servers") or []
    if srv and isinstance(srv, list) and isinstance(srv[0], dict):
        ruta = re.sub(r"^https?://[^/]+", "", str(srv[0].get("url", "")))
        prefijo = "" if ruta in ("", "/") else "/" + ruta.strip("/")
    ops = set()
    for ruta, cuerpo in (d.get("paths") or {}).items():
        if not isinstance(cuerpo, dict):
            continue
        for verbo in cuerpo:
            if verbo.lower() in VERBOS:
                ops.add(verbo.upper() + " " + normalizar_ruta(prefijo + ruta))
    return ops


def normalizar_ruta(r):
    """Los nombres de los parametros no son parte del contrato: /recursos/{id} y
    /recursos/{recursoId} son la MISMA operacion. Compararlos como texto produciria una
    diferencia donde no la hay, que es la peor clase de falso positivo."""
    r = re.sub(r"\{[^}]*\}", "{}", r.strip())
    r = "/" + r.strip("/")
    return r if r != "/" else "/"


RE_VERBO = re.compile(r"@(" + "|".join(v.upper() for v in VERBOS) + r")\b")
RE_SUBPATH = re.compile(r'@Path\s*\(\s*"([^"]*)"')


def _raiz_http(u):
    """El prefijo que Quarkus le antepone a TODOS los endpoints del repositorio.

    Sale de application.properties -quarkus.http.root-path o quarkus.rest.path- o de
    un @ApplicationPath en el codigo. Es una linea de configuracion que no aparece en
    ningun @Path, asi que sin leerla el codigo y el contrato quedan corridos por
    completo: un repositorio con root-path=/api daba el CIEN POR CIENTO de las
    operaciones en hallazgo con el contrato perfecto."""
    if u.get("_raiz_http") is not None:
        return u["_raiz_http"]
    prefijo = ""
    for b, dirs, files in os.walk(u["raiz"]):
        dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
        if "/src/test/" in (b.replace("\\", "/") + "/"):
            continue
        for fn in files:
            if fn == "application.properties" or fn.startswith("application."):
                m = re.search(r"^\s*(?:%[\w-]+\.)?quarkus\.(?:http\.root-path|rest\.path)"
                              r"\s*[:=]\s*(\S+)",
                              _leer(os.path.join(b, fn)), re.M)
                if m and m.group(1) not in ("/", ""):
                    prefijo = "/" + m.group(1).strip("/")
            elif fn.endswith(".java"):
                m = re.search(r'@ApplicationPath\s*\(\s*"([^"]*)"',
                              _leer(os.path.join(b, fn)))
                if m and m.group(1).strip("/"):
                    prefijo = "/" + m.group(1).strip("/")
    u["_raiz_http"] = prefijo
    return prefijo


def _ops_del_codigo(u):
    """Los endpoints JAX-RS que existen de verdad. Quarkus usa las anotaciones
    estandar, asi que alcanza con leerlas.

    Se recorre LINEA POR LINEA acumulando las anotaciones hasta la firma del metodo,
    en vez de buscar hacia adelante con una ventana de texto. La ventana parecia mas
    simple y estaba mal: un @Path("/{id}") tiene una llave adentro, asi que cortar el
    texto en la primera llave se comia justamente las rutas con parametro — que son
    la mitad de los endpoints de cualquier API."""
    ops = {}
    for p in fuentes(u):
        if es_test(p):
            continue
        txt = _leer(p)
        if "@Path" not in txt:
            continue
        base, verbo, sub = "", None, ""
        for linea in txt.splitlines():
            s = linea.strip()
            if not s or s.startswith(("//", "/*", "*")):
                continue

            # Las anotaciones se consumen de a una DEL PRINCIPIO de la linea, en vez
            # de tratar la linea entera como "una anotacion". Antes, con
            # `@GET @Path("/{id}") public Response ver(...)` -todo junto, que es
            # comun- se tomaba el verbo y se descartaba el resto: el endpoint
            # desaparecia o quedaba con la ruta equivocada.
            while s.startswith("@"):
                mv = RE_VERBO.match(s)
                if mv:
                    verbo = mv.group(1)
                    s = s[mv.end():].strip()
                    continue
                mp = RE_SUBPATH.match(s)
                if mp:
                    sub = mp.group(1)
                    s = _saltar_anotacion("@" + s[1:])
                    continue
                # Cualquier otra anotacion: se consume entera, con sus parentesis
                # BALANCEADOS. Esto es lo que arregla el caso que rompia el contrato
                # completo: @RolesAllowed({"administrador"}) o
                # @Produces({MediaType.APPLICATION_JSON}) entre el @Path de la clase
                # y la palabra class. El parseo anterior cortaba en la primera llave,
                # perdia la ruta base, y TODOS los endpoints del archivo quedaban
                # colgando de "/" — el informe los daba a todos por incorrectos
                # aunque el contrato y el codigo coincidieran perfectamente.
                s = _saltar_anotacion(s)

            if not s:
                continue

            # La declaracion del tipo. `interface` cuenta igual que `class`: el @Path
            # sobre una interfaz, con la clase implementandola, es el idiom estandar
            # de MicroProfile Rest Client, y antes se perdia la base entera.
            if re.match(r"(?:public\s+|final\s+|abstract\s+|static\s+)*"
                        r"(?:class|interface|record|enum)\b", s):
                base, verbo, sub = (sub or base), None, ""
                continue

            if verbo and "(" in s:
                ops[verbo + " " + normalizar_ruta(base.rstrip("/") + "/" +
                                                  sub.lstrip("/"))] = _rel(p)
            verbo, sub = None, ""
    return ops


def _saltar_anotacion(s):
    """Consume la anotacion del principio de la linea, con sus parentesis
    BALANCEADOS, y devuelve lo que queda.

    Contar parentesis -y no cortar en la primera llave- es lo unico que aguanta
    @RolesAllowed({"a","b"}) y @Tag(name = "x", description = "a;b")."""
    i = 1
    while i < len(s) and (s[i].isalnum() or s[i] in "._$"):
        i += 1
    if i < len(s) and s[i] == "(":
        prof = 0
        while i < len(s):
            if s[i] == "(":
                prof += 1
            elif s[i] == ")":
                prof -= 1
                if prof == 0:
                    i += 1
                    break
            i += 1
    return s[i:].strip()


def sonda_contrato():
    us = [u for u in unidades() if es_java(u)]
    if not us:
        return sin_codigo("Contrato declarado vs implementado",
                          "Compara los endpoints que declara el openapi.yaml con los que "
                          "existen de verdad en el codigo.")
    filas, alguno_con_contrato = [], False
    for u in us:
        contrato, hubo_contrato = set(), False
        for b, dirs, files in os.walk(u["raiz"]):
            dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
            for fn in files:
                if re.match(r"^(openapi|swagger)\.(ya?ml|json)$", fn):
                    hubo_contrato = alguno_con_contrato = True
                    contrato |= _ops_del_contrato(_leer(os.path.join(b, fn)),
                                                  fn.endswith(".json"))
        codigo = _ops_del_codigo(u)
        # El prefijo que el propio Quarkus le agrega a TODO endpoint. Sin esto, un
        # repositorio con quarkus.http.root-path=/api da el cien por ciento de las
        # operaciones en hallazgo aunque el contrato este perfecto.
        raiz_http = _raiz_http(u)
        if raiz_http:
            con_raiz = {}
            for clave, donde in codigo.items():
                verbo, ruta = clave.split(" ", 1)
                con_raiz[verbo + " " + normalizar_ruta(raiz_http + ruta)] = donde
            codigo = con_raiz
        for op in sorted(contrato | set(codigo)):
            en_c, en_k = op in contrato, op in codigo
            if en_c and en_k:
                filas.append([op, "si", "si", codigo[op], "OK"])
            elif en_c:
                filas.append([op, "si", "NO", "declarado en el contrato y sin implementar",
                              "HALLAZGO"])
            else:
                filas.append([op, "NO", "si", codigo[op] + " — existe y el contrato no lo "
                              "declara", "HALLAZGO"])
    if not filas:
        return _res("Contrato declarado vs implementado", "SIN DATOS",
                    "No se encontro ni un openapi.yaml ni endpoints en el codigo.",
                    significa="Compara los endpoints declarados en el contrato con los que "
                              "existen en el codigo. No encontro ninguno de los dos.",
                    importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar. Con "
                            "codigo de backend pero sin contrato, es un hallazgo real.",
                    acciones=[{"paso": "Si ya hay endpoints, corre armar-swagger para "
                                       "consolidar el openapi.yaml del repositorio."}])
    if not hubo_contrato:
        for f in filas:
            f[1], f[3], f[4] = "no hay contrato", f[3], "HALLAZGO"
    # Los conteos se sacan ANTES de recortar: si no, el resumen decia "3 declaradas
    # sin implementar" sobre un total de 312 y las dos cifras de la misma frase venian
    # de universos distintos.
    faltan = [f[0] for f in filas if f[1] == "si" and f[2] == "NO"]
    sobran = [f[0] for f in filas if f[2] == "si" and f[1] != "si"]
    filas, ocultas = recortar(filas)
    estado = fila_estado(filas)
    resumen = str(len(filas) + ocultas) + " operacion(es). "
    if estado == "OK":
        resumen += "El contrato y el codigo dicen lo mismo."
    else:
        resumen += (str(len(faltan)) + " declarada(s) sin implementar · " +
                    str(len(sobran)) + " implementada(s) sin declarar.")
    return _res("Contrato declarado vs implementado", estado, resumen,
        (["Operacion", "En el contrato", "En el codigo", "Detalle", "Estado"], filas),
        significa="Cada Tarea de capa de entrada declara su contrato -que recibe y que "
                  "devuelve el endpoint- y el criterio de terminado exige que el codigo "
                  "coincida. Esta sonda compara las dos listas: la del openapi.yaml y la de "
                  "las anotaciones del codigo. Los nombres de los parametros se ignoran a "
                  "proposito: /recursos/{id} y /recursos/{recursoId} son la misma operacion.",
        importa="El front desarrolla contra el contrato simulandolo, sin esperar al back. Si "
                "el contrato y el codigo se separan, el front construye contra algo que no "
                "existe y nadie se entera hasta la integracion, que es el momento mas caro "
                "para enterarse. Un endpoint que existe y no esta declarado es el otro lado "
                "del mismo problema: superficie que nadie reviso.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada operacion declarada y sin implementar: o falta escribirla, o "
                     "el contrato quedo con algo que ya no va. Las dos salidas son validas; "
                     "lo que no vale es dejarla ahi."},
            {"paso": "Por cada operacion implementada y sin declarar: agregala al contrato. "
                     "Si no esta en el contrato, para el front no existe."},
            {"paso": "Volve a consolidar el contrato despues de tocarlo.",
             "comando": "usar la skill armar-swagger en el repo de back"}],
        pedido=None if estado == "OK" else (
            "El contrato OpenAPI del backend y los endpoints que existen en el codigo no "
            "coinciden:\n\n" +
            "\n".join("- " + f[0] + ": contrato=" + f[1] + ", codigo=" + f[2] + " (" + f[3] + ")"
                      for f in filas if f[4] == "HALLAZGO") +
            "\n\nPor cada diferencia decime cual de las dos esta bien: si falta implementar "
            "el endpoint, si el contrato quedo viejo, o si el endpoint se escribio sin "
            "declararlo. Mira tambien si alguna Historia o Tarea del backlog cubre esa "
            "operacion, porque eso decide para que lado se corrige." + _cierre()))


# ---------------------------------------------- 4. trazabilidad del test a la Tarea

# Como un test dice a que Tarea pertenece. Se aceptan varias formas porque el equipo
# todavia no eligio una: cuando elija, se deja la suya y se sacan las otras.
# El (?![0-9a-fA-F]) del final saca los colores: #1976d2 capturaba "1976" y el
# archivo quedaba reportado como "trazable a la Tarea #1976". En tests de front con
# colores de marca es completamente realista.
HUELLAS = [re.compile(r"#(\d{4,})(?![0-9a-fA-F])"),
           re.compile(r"[Tt]area\s*#?\s*(\d{4,})"),
           re.compile(r'@Tag\s*\(\s*"[^"]*?(\d{4,})[^"]*"\s*\)'),
           re.compile(r'\bT-(\d+)\b')]


def _cuenta_tests(txt, java):
    if java:
        return len(re.findall(r"@Test\b", txt))
    return len(re.findall(r"^\s*(?:it|test)\s*(?:\.\w+)?\s*\(", txt, re.M))


def sonda_trazabilidad():
    us = unidades()
    if not us:
        return sin_codigo("Trazabilidad del test a la Tarea",
                          "Verifica que cada archivo de test diga a que Tarea del tablero "
                          "pertenece.")
    filas, total_tests, con_prod = [], 0, 0
    for u in us:
        java = es_java(u)
        arch = fuentes(u)
        con_prod += len([p for p in arch if not es_test(p)])
        for p in arch:
            if not es_test(p):
                continue
            txt = _leer(p)
            n = _cuenta_tests(txt, java)
            if n == 0:
                # Dobles y datos de ejemplo (support/), fixtures: no son tests, no
                # tienen una lista de la Tarea contra la cual cruzarse.
                continue
            total_tests += n
            ids = []
            for h in HUELLAS:
                ids += h.findall(txt)
            ids = sorted(set(ids))
            if ids:
                filas.append([_rel(p), ", ".join("#" + i for i in ids), str(n),
                              "trazable", "OK"])
            else:
                filas.append([_rel(p), "-", str(n),
                              "no nombra ninguna Tarea: no se puede cruzar con la lista de "
                              "tests que esa Tarea prometio", "HALLAZGO"])
    if not filas:
        estado = "HALLAZGO" if con_prod else "SIN DATOS"
        return _res("Trazabilidad del test a la Tarea", estado,
            ("Hay " + str(con_prod) + " archivo(s) de produccion y NINGUN archivo de test."
             if con_prod else "No hay tests ni codigo de produccion todavia."),
            significa="Cada Tarea trae una lista de «Tests a escribir PRIMERO» numerada. "
                      "Esta sonda mira, del lado del codigo, si los tests dicen a que Tarea "
                      "pertenecen. No encontro ningun archivo de test.",
            importa=("La regla del proyecto es test-primero: no hay codigo de produccion sin "
                     "un test que haya fallado antes. Codigo sin un solo test no es un "
                     "descuido de forma, es la regla rota."
                     if con_prod else
                     "SIN DATOS no es aprobado: quiere decir que este aspecto quedo sin "
                     "revisar. Cuando haya codigo, la sonda mide sola."),
            acciones=[{"paso": "Si el codigo se escribio sin tests, eso no se arregla "
                               "agregando tests despues: un test escrito despues no prueba "
                               "que el codigo hacia falta. Se revisa Tarea por Tarea con "
                               "verificar-tdd, que audita la evidencia del ciclo."}]
            if con_prod else
            [{"paso": "Cloná el codigo y volve a correr el Doctor.",
              "comando": "bash doctor/bin/doctor.sh"}])

    sueltos = [f for f in filas if f[4] == "HALLAZGO"]
    filas, ocultas = recortar(filas)
    estado = fila_estado(filas)
    return _res("Trazabilidad del test a la Tarea", estado,
        str(len(filas) + ocultas) + " archivo(s) de test · " + str(total_tests) +
        " test(s). " + ("Todos nombran su Tarea." if estado == "OK" else
                        str(len(sueltos)) + " no nombran ninguna Tarea."),
        (["Archivo de test", "Tarea", "Tests", "Detalle", "Estado"], filas),
        significa="Cada Tarea del tablero trae una lista numerada de «Tests a escribir "
                  "PRIMERO». Lo ideal seria comparar esa lista contra los tests que existen, "
                  "pero esa lista vive en Azure y el Doctor no sale de la maquina — asi que "
                  "mide la costura que hace posible esa comparacion: que cada archivo de "
                  "test diga a que Tarea pertenece, con el numero del ticket adentro.",
        importa="Sin esa costura, cruzar lo prometido con lo escrito es imposible para "
                "cualquiera: ni una persona ni un asistente pueden decir que test cubre que "
                "item. Es la diferencia entre poder auditar el acumulado de meses y tener "
                "que confiar. El pedido de abajo hace el cruce completo, porque el asistente "
                "SI puede leer el tablero.",
        acciones=[] if estado == "OK" else [
            {"paso": "En cada archivo de test que no la nombra, agregá el numero de la Tarea. "
                     "En Java, la forma mas limpia es una anotacion de etiqueta en la clase; "
                     "en el front, un comentario arriba del bloque principal."},
            {"paso": "Acordá UNA sola forma de escribirlo y dejala escrita en guiar-tdd de "
                     "cada repositorio. Hoy la sonda acepta cuatro formas justamente porque "
                     "el equipo todavia no eligio; cuando elija, se deja la suya."},
            {"paso": "Para el cruce completo -que ningun item de la lista quedo sin test- "
                     "usá el pedido de abajo: hace falta leer el tablero, y eso el Doctor no "
                     "lo hace."}],
        pedido=None if estado == "OK" else (
            "Estos archivos de test no dicen a que Tarea del tablero pertenecen:\n\n" +
            "\n".join("- " + f[0] + " (" + f[2] + " test(s))" for f in sueltos[:25]) +
            "\n\nHacé dos cosas. Primero: por cada archivo, abrilo y decime a que Tarea "
            "corresponde segun lo que prueba, y proponeme la linea exacta que hay que "
            "agregarle para dejarlo trazado. Segundo, y es lo que mas importa: para las "
            "Tareas que ya estan cerradas en el tablero, trae su lista de «Tests a escribir "
            "PRIMERO» y cruzala contra los tests que existen en el codigo — decime que items "
            "quedaron prometidos y sin escribir. Un item que falta en la lista no se escribe "
            "nunca y el agujero no avisa." + _cierre()))


# ------------------------------------------------ 5. duplicacion entre slices

VENTANA = 10        # lineas significativas consecutivas que forman un bloque


def _significativas(txt, java):
    """Las lineas que cuentan para comparar dos bloques. Se sacan las que no dicen
    nada del QUE hace el codigo: imports, llaves sueltas, comentarios, anotaciones.
    Sin esto, dos clases distintas con los mismos imports se verian duplicadas."""
    out = []
    for i, linea in enumerate(txt.splitlines(), 1):
        s = linea.strip()
        if len(s) < 8:
            continue
        if s.startswith(("import ", "package ", "//", "/*", "*", "#", "@", "}", "{", ")")):
            continue
        # Se normalizan los espacios pero NO los nombres: dos bloques con distintos
        # nombres de variable son parecidos, no duplicados, y confundirlos es ruido.
        out.append((i, re.sub(r"\s+", " ", s)))
    return out


def sonda_duplicacion():
    us = unidades()
    if not us:
        return sin_codigo("Duplicacion entre slices",
                          "Busca bloques de codigo repetidos en dos slices distintos.")
    bloques = {}
    mirados = 0
    for u in us:
        slices = slices_de(u)
        for p in fuentes(u):
            if es_test(p):
                continue
            sl = slice_de(p, slices)
            if not sl:
                continue
            mirados += 1
            rp = _rel(p)          # una vez por archivo, no una por ventana
            lineas = _significativas(_leer(p), es_java(u))
            for k in range(0, len(lineas) - VENTANA + 1):
                trozo = lineas[k:k + VENTANA]
                h = hashlib.md5("\n".join(t[1] for t in trozo).encode("utf-8")).hexdigest()
                    # El slice se califica con SU UNIDAD. Agrupar por nombre pelado
                # dejaba invisible la duplicacion entre dos apps del front: las dos
                # tienen un slice "<modulo-a>", asi que el bloque repetido entre
                # ellas contaba como un solo slice y se descartaba. Con tres fronts
                # -que el diseno declara posibles- el agujero se agranda solo.
                bloques.setdefault(h, []).append(
                    (u["ruta"] + ":" + sl, rp, trozo[0][0], trozo[0][1]))

    filas, vistos = [], set()
    for h, casos in bloques.items():
        ss = sorted(set(c[0] for c in casos))
        if len(ss) < 2:
            continue
        clave = tuple(ss) + (casos[0][3][:60],)
        if clave in vistos:
            continue
        vistos.add(clave)
        filas.append([casos[0][3][:70], " + ".join(ss),
                      "; ".join(c[1] + ":" + str(c[2]) for c in casos[:3]),
                      str(VENTANA) + " lineas repetidas", "HALLAZGO"])
    if not mirados:
        return nada_medido("Duplicacion entre slices",
                           "Busca bloques de codigo repetidos en dos slices distintos.",
                           0, "archivo(s) con slice")
    filas, ocultas = recortar(filas, 20)
    estado = "HALLAZGO" if filas else "OK"
    return _res("Duplicacion entre slices", estado,
        str(mirados) + " archivo(s) comparados. " +
        ("No hay bloques repetidos entre slices distintos." if estado == "OK" else
         str(len(filas) + ocultas) + " bloque(s) de " + str(VENTANA) + " lineas aparecen "
         "en dos slices o mas."),
        (["Primera linea del bloque", "Slices", "Donde", "Detalle", "Estado"], filas)
        if filas else None,
        significa="Compara el codigo de cada slice contra el de los demas buscando bloques "
                  "de " + str(VENTANA) + " lineas identicas. Se ignoran imports, llaves y "
                  "comentarios, que son iguales en todos lados y ensuciarian la medicion. "
                  "Solo se reporta lo que aparece en DOS slices distintos: repetir adentro "
                  "de un mismo slice es asunto de ese slice.",
        importa="En un monolito modular es la senal temprana de dos cosas, y conviene "
                "distinguirlas antes de tocar nada: o falta una abstraccion compartida que "
                "todavia nadie extrajo, o dos slices estan resolviendo lo mismo sin saberlo "
                "-y entonces el problema no es el codigo repetido, es el reparto-. Copiar "
                "una vez es barato; el costo llega cuando hay que corregir un bug y aparece "
                "en tres lugares, y alguien arregla dos.",
        acciones=[] if estado == "OK" else [
            {"paso": "Mira cada bloque y decidí cual de las dos cosas es: falta una "
                     "abstraccion, o dos slices hacen lo mismo. La salida es distinta."},
            {"paso": "Si falta una abstraccion: extraela a un lugar compartido y que los dos "
                     "slices la usen. Ojo con donde la ponés — un cajon de utilidades al que "
                     "todos importan rompe los limites tanto como un import cruzado."},
            {"paso": "Si dos slices hacen lo mismo: eso se resuelve en el reparto, no en el "
                     "codigo. Uno de los dos tiene que ser el dueno y el otro pasar por su "
                     "api."},
            {"paso": "Si la repeticion es a proposito -dos slices que HOY se parecen y van a "
                     "divergir- dejalo escrito. Una duplicacion declarada es una decision; "
                     "una sin declarar es un descuido, y desde afuera se ven iguales."}],
        pedido=None if estado == "OK" else (
            "En el codigo hay bloques de " + str(VENTANA) + " lineas que se repiten en "
            "slices distintos:\n\n" +
            "\n".join("- " + f[1] + " -> " + f[2] + "  (empieza con: " + f[0] + ")"
                      for f in filas[:15]) +
            "\n\nPor cada uno, abri los dos lados y decime cual de estas tres es: falta una "
            "abstraccion compartida, los dos slices estan resolviendo lo mismo -y entonces "
            "hay que decidir cual es el dueno-, o es una repeticion a proposito que van a "
            "divergir. Si proponés extraer algo compartido, decime DONDE lo ponés y por que "
            "eso no rompe los limites entre slices." + _cierre()))


# ------------------------------------------ 6. dependencias declaradas sin usar

# Paquetes que se declaran y legitimamente NO se importan desde el codigo: son
# extensiones de runtime, plugins de build o tipos. Marcarlos seria gritar lobo.
NO_SE_IMPORTAN = {
    # react entra en la lista por React 19: con el JSX transform automatico un
    # componente puramente presentacional no escribe nunca la cadena "react", y la
    # sonda reportaba que react no se usa en TODO front moderno.
    "react", "react-dom", "vite", "typescript", "tailwindcss", "postcss",
    "autoprefixer", "eslint", "prettier", "jsdom", "happy-dom",
    "@vitejs/plugin-react",
}

# Segmentos de groupId o de artifactId que no identifican a nadie: aparecen en la
# mitad de los paquetes de Java y usarlos como pista es decir que si a todo.
SEGMENTOS_GENERICOS = {
    "org", "com", "net", "java", "javax", "jakarta", "core", "api", "util",
    "utils", "common", "commons", "lib", "libs", "base", "main", "impl", "sdk",
}


def _deps_maven(txt):
    """Las dependencias REALES de un pom.

    Se saca antes el bloque <dependencyManagement>, que no declara dependencias
    sino versiones para las que se declaren mas abajo: un BOM entero entraba como
    si fueran del proyecto y cada linea salia como "nadie la importa". Lo mismo
    los <plugins>. Y se ignoran las de scope provided/system y las <optional>: no
    van al artefacto final, asi que no importarlas es lo normal."""
    txt = re.sub(r"<dependencyManagement>.*?</dependencyManagement>", "", txt,
                 flags=re.S)
    txt = re.sub(r"<plugins>.*?</plugins>", "", txt, flags=re.S)
    out = []
    for b in re.findall(r"<dependency>(.*?)</dependency>", txt, re.S):
        g = re.search(r"<groupId>\s*([^<]+?)\s*</groupId>", b)
        a = re.search(r"<artifactId>\s*([^<]+?)\s*</artifactId>", b)
        if not (g and a):
            continue
        sc = re.search(r"<scope>\s*([^<]+?)\s*</scope>", b)
        if sc and sc.group(1).strip() in ("provided", "system", "import"):
            continue
        if re.search(r"<optional>\s*true\s*</optional>", b):
            continue
        out.append((g.group(1).strip(), a.group(1).strip()))
    return out


def _poms_de(u):
    """Todos los pom.xml de la unidad, no solo el de la raiz.

    En un multi-modulo de Maven las dependencias viven en los submodulos, asi que
    leer unicamente el pom de arriba dejaba la sonda mirando un archivo que casi
    no declara nada."""
    out = []
    for b, dirs, files in os.walk(u["raiz"]):
        dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
        for fn in files:
            if fn in ("pom.xml", "build.gradle", "build.gradle.kts"):
                out.append(os.path.join(b, fn))
    return out


def _deps_npm(txt):
    out = []
    for clave in ("dependencies", "devDependencies"):
        m = re.search(r'"' + clave + r'"\s*:\s*\{(.*?)\}', txt, re.S)
        if not m:
            continue
        for nombre in re.findall(r'"([^"]+)"\s*:', m.group(1)):
            out.append((clave, nombre))
    return out


def sonda_dependencias():
    us = unidades()
    if not us:
        return sin_codigo("Dependencias declaradas sin usar",
                          "Busca paquetes declarados en el pom.xml o el package.json que "
                          "ningun archivo importa.")
    filas = []
    for u in us:
        importado = "\n".join(_leer(p) for p in fuentes(u))
        if not es_java(u):
            # Un paquete puede usarse desde una hoja de estilos o desde el
            # index.html, y esos archivos no estan en EXTENSIONES: normalize.css o
            # @fontsource/* salian como "nadie los importa" siempre.
            for b, dirs, files in os.walk(u["raiz"]):
                dirs[:] = [d for d in dirs
                           if d not in BASURA and not d.startswith(".")]
                for fn in files:
                    if fn.endswith((".css", ".scss", ".html")):
                        importado += "\n" + _leer(os.path.join(b, fn))
        if es_java(u):
            txt = "\n".join(_leer(x) for x in _poms_de(u))
            vistas = set()
            for grupo, art in _deps_maven(txt):
                if (grupo, art) in vistas:
                    continue
                vistas.add((grupo, art))
                if grupo.startswith("io.quarkus") and art.startswith("quarkus-"):
                    # Una extension de Quarkus casi nunca se importa: se activa por
                    # estar en el classpath. Decir que "no se usa" seria mentir.
                    filas.append([art, grupo, "extension de Quarkus: se activa por estar "
                                  "declarada, no por un import", "SIN DATOS"])
                    continue
                # Las pistas genericas eran el agujero: con grupo.split(".")[-2:]
                # y len > 2, "org" contaba como pista, y "import org." aparece en
                # cualquier archivo Java del mundo. Resultado: org.projectlombok,
                # org.mapstruct y org.assertj daban "se importa" sin que nadie las
                # importara. CUALQUIER groupId de dos segmentos era indetectable, o
                # sea media tabla.
                pistas = [s for s in grupo.split(".")
                          if len(s) > 3 and s not in SEGMENTOS_GENERICOS]
                pistas += [w for w in re.split(r"[-_.]", art)
                           if len(w) > 3 and w not in SEGMENTOS_GENERICOS]
                # Y el artefacto sin separadores: rest-assured se importa como
                # io.restassured, y ninguna pista lo alcanzaba.
                plano = re.sub(r"[-_.]", "", art)
                if len(plano) > 4:
                    pistas.append(plano)
                usado = any(("import " + p) in importado or ("." + p + ".") in importado
                            for p in pistas)
                filas.append([art, grupo, "se importa" if usado else
                              "ningun archivo importa nada de este grupo",
                              "OK" if usado else "HALLAZGO"])
        else:
            txt = _leer(u["raiz"] + "/package.json")
            for clave, nombre in _deps_npm(txt):
                if nombre in NO_SE_IMPORTAN or nombre.startswith(("@types/", "eslint-",
                                                                  "@typescript-eslint/")):
                    filas.append([nombre, clave, "herramienta o tipos: no se importa desde "
                                  "el codigo, y esta bien asi", "SIN DATOS"])
                    continue
                usado = re.search(r'["\']' + re.escape(nombre) + r'(/[^"\']*)?["\']',
                                  importado) is not None
                estado = "OK" if usado else ("HALLAZGO" if clave == "dependencies"
                                             else "SIN DATOS")
                filas.append([nombre, clave,
                              "se importa" if usado else
                              ("ningun archivo lo importa" if estado == "HALLAZGO" else
                               "no se importa; al ser de desarrollo puede usarse desde la "
                               "configuracion, no se puede decidir por import"),
                              estado])
    if not filas:
        return _res("Dependencias declaradas sin usar", "SIN DATOS",
                    "No se pudo leer ningun pom.xml ni package.json.",
                    significa="Compara los paquetes declarados contra los que el codigo "
                              "realmente importa.",
                    importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar.",
                    acciones=[{"paso": "Verifica que el repositorio clonado tenga su archivo "
                                       "de build en la raiz."}])
    sobran = [f[0] for f in filas if f[3] == "HALLAZGO"]
    filas, ocultas = recortar(filas)
    estado = fila_estado(filas)
    return _res("Dependencias declaradas sin usar", estado,
        str(len(filas) + ocultas) + " dependencia(s) declarada(s). " +
        ("Todas las que se pueden verificar por import estan en uso." if estado == "OK" else
         str(len(sobran)) + " no aparece(n) en ningun import: " + ", ".join(sobran[:6]) +
         ("." if len(sobran) <= 6 else "...")),
        (["Dependencia", "Declarada en", "Detalle", "Estado"], filas),
        significa="Lee los paquetes declarados en el pom.xml o el package.json y busca si "
                  "algun archivo los importa. Las que NO se pueden decidir asi quedan en SIN "
                  "DATOS y no como error: una extension de Quarkus se activa por estar en el "
                  "classpath, y un plugin de build se usa desde la configuracion. Marcarlas "
                  "seria gritar lobo, y una sonda que grita lobo se deja de leer.",
        importa="Una dependencia que nadie usa es superficie que nadie eligio tener: entra "
                "en el analisis de SAST, sube el peso del artefacto, y el dia que tenga "
                "una vulnerabilidad hay que atenderla igual aunque el codigo no la toque. "
                "Sacarlas es de las cosas mas baratas que se pueden hacer por la seguridad "
                "de un repositorio.",
        acciones=[] if estado == "OK" else [
            {"paso": "Antes de sacar ninguna, comprobá que el proyecto sigue compilando y "
                     "que los tests pasan. Algunas se usan por reflexion o por configuracion "
                     "y no aparecen en ningun import.",
             "comando": "mvn -q verify"},
            {"paso": "Las que sobren de verdad, sacalas del archivo de build en un commit "
                     "aparte, para que se pueda revertir solo eso si algo falla."},
            {"paso": "Si una tiene que quedarse aunque no se importe, dejá escrito por que "
                     "en un comentario al lado. Sin eso, la proxima corrida la vuelve a "
                     "marcar y alguien la analiza de cero."}],
        pedido=None if estado == "OK" else (
            "En este repositorio hay dependencias declaradas que ningun archivo importa:\n\n" +
            "\n".join("- " + f[0] + " (" + f[1] + ")" for f in filas if f[3] == "HALLAZGO") +
            "\n\nPor cada una, revisá si se usa de alguna forma que no sea un import "
            "-reflexion, configuracion, un plugin de build, una extension que se activa por "
            "estar en el classpath- y decime cuales se pueden sacar de verdad. Para las que "
            "se quedan, proponeme el comentario que hay que dejarles al lado para que no las "
            "volvamos a analizar la proxima vez. No saques ninguna sin que antes compile y "
            "pasen los tests." + _cierre()))


# ------------------------------------------------ 7. puerta de seguridad (SAST)

ARCHIVOS_PIPELINE = ("azure-pipelines.yml", "azure-pipelines.yaml", ".gitlab-ci.yml",
                     "Jenkinsfile", "bitbucket-pipelines.yml")

# Claves que, con un valor literal al lado, son una credencial en el repositorio.
# El prefijo %perfil. es donde Quarkus deja la configuracion por ambiente, y era
# justamente donde vivia la password de dev: el ancla no lo admitia y esa credencial
# -la unica real del archivo- se escapaba entera.
#
# Y "token" salio de la lista. Parecia obvio incluirla y era lo contrario: en OIDC
# hay una decena de claves con esa palabra que NO son secretos -token.issuer,
# token.lifespan-grace, token.principal-claim, jwt.token.header-, asi que la sonda
# marcaba cuatro lineas inocuas y se perdia las dos que importaban. Una sonda que
# grita lobo Y ademas no ve al lobo es peor que no tenerla.
CLAVE_SECRETA = re.compile(
    r"(?i)^\s*(?:%[\w-]+\.)?[\w.\-]*"
    r"(password|passwd|secret|credential|apikey|api[_.\-]key|private[_.\-]key)"
    r"[\w.\-]*\s*[:=]\s*(.+?)\s*$")

# Un valor que NO es una credencial: viene de afuera, o es un relleno declarado.
VALOR_INOCUO = re.compile(
    r"(?i)^(\$\{.*\}|\$\(.*\)|%.*%|<.*>|\"\"|''|changeme|change_me|placeholder|todo|"
    r"xxx+|\*+|secret|password|null|none|true|false)$")


def _pipelines(u):
    out = []
    for base in (u["raiz"], CTX["root"]):
        for fn in ARCHIVOS_PIPELINE:
            p = base + "/" + fn
            if os.path.isfile(p):
                out.append(p)
        wf = base + "/.github/workflows"
        if os.path.isdir(wf):
            for fn in sorted(os.listdir(wf)):
                if fn.endswith((".yml", ".yaml")):
                    out.append(wf + "/" + fn)
    return out


def sonda_seguridad():
    us = unidades()
    if not us:
        return sin_codigo("Puerta de seguridad (SAST)",
                          "Verifica que el analisis de seguridad este puesto en el pipeline "
                          "y que no haya credenciales escritas en el repositorio.")
    filas = []
    for u in us:
        pre = u["ruta"] + ": "
        pipes = _pipelines(u)
        if not pipes:
            filas.append([pre + "definicion de pipeline", "no", "no se encontro ningun "
                          "archivo de pipeline; sin el, ningun analisis se ejecuta solo",
                          "HALLAZGO"])
        else:
            txt = "\n".join(_leer(p) for p in pipes)
            filas.append([pre + "definicion de pipeline", "si",
                          ", ".join(_rel(p) for p in pipes[:3]), "OK"])
            hay = re.search(r"(?i)veracode|pipeline-scan|srcclr|sourceclear", txt) is not None
            filas.append([pre + "paso de SAST en el pipeline", "si" if hay else "no",
                          "el analisis corre solo en cada entrega" if hay else
                          "el analisis no esta en el pipeline: depende de que alguien se "
                          "acuerde de correrlo", "OK" if hay else "HALLAZGO"])
            frena = re.search(r"(?i)break[_ ]?build|fail[_ ]?on|continueOnError:\s*false",
                              txt) is not None
            filas.append([pre + "el analisis FRENA la entrega", "si" if frena else "no se ve",
                          "un analisis que reporta pero no frena es una sugerencia, no una "
                          "puerta" if not frena else "configurado para cortar",
                          "OK" if frena else "SIN DATOS"])

        # Supresiones: existir esta bien; lo que no puede faltar es el motivo escrito.
        sup = []
        for b, dirs, files in os.walk(u["raiz"]):
            dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
            for fn in files:
                if re.search(r"(?i)(veracode|mitigation|baseline).*\.(json|xml|ya?ml)$", fn):
                    sup.append(os.path.join(b, fn).replace("\\", "/"))
        if sup:
            sin_motivo = [s for s in sup
                          if not re.search(r"(?i)comment|reason|justification|motivo",
                                           _leer(s))]
            filas.append([pre + "supresiones justificadas",
                          str(len(sup) - len(sin_motivo)) + " de " + str(len(sup)),
                          "una supresion sin motivo escrito es un hallazgo tapado"
                          if sin_motivo else "todas traen su motivo",
                          "HALLAZGO" if sin_motivo else "OK"])

        # Credenciales con valor literal. Solo en archivos de configuracion, y solo
        # cuando el valor NO viene de afuera: asi el falso positivo es raro.
        fugas = []
        config_miradas = 0
        for b, dirs, files in os.walk(u["raiz"]):
            dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
            # Los recursos de TEST llevan credenciales de mentira a proposito -una
            # base en memoria, un usuario de prueba- y marcarlas es ruido puro.
            if "/src/test/" in (b.replace("\\", "/") + "/"):
                continue
            for fn in files:
                if not re.search(r"(?i)\.(properties|env|ya?ml|conf|ini)$|^\.env", fn):
                    continue
                p = os.path.join(b, fn).replace("\\", "/")
                config_miradas += 1
                for i, linea in enumerate(_leer(p).splitlines(), 1):
                    if linea.strip().startswith(("#", "//")):
                        continue
                    m = CLAVE_SECRETA.match(linea)
                    if m and m.group(2) and not VALOR_INOCUO.match(m.group(2).strip('"\'')):
                        fugas.append(_rel(p) + ":" + str(i))
        # Sin un solo archivo de configuracion que mirar, esto NO es un aprobado:
        # decir "los valores sensibles vienen de variables de entorno" sobre cero
        # archivos es afirmar algo que no se miro. Le pasaba a cada app del front.
        if fugas:
            filas.append([pre + "credenciales con valor escrito", str(len(fugas)),
                          "; ".join(fugas[:4]), "HALLAZGO"])
        elif config_miradas:
            filas.append([pre + "credenciales con valor escrito", "ninguna",
                          "en " + str(config_miradas) + " archivo(s) de configuracion, "
                          "los valores sensibles vienen de variables de entorno", "OK"])
        else:
            filas.append([pre + "credenciales con valor escrito", "sin revisar",
                          "no se encontro ningun archivo de configuracion que mirar",
                          "SIN DATOS"])

    estado = fila_estado(filas)
    malos = [f for f in filas if f[3] == "HALLAZGO"]
    return _res("Puerta de seguridad (SAST)", estado,
        str(len(filas)) + " chequeo(s). " +
        ("La puerta esta puesta y no hay credenciales escritas." if estado == "OK" else
         str(len(malos)) + " no pasa(n): " + ", ".join(f[0] for f in malos[:4]) + "."),
        (["Chequeo", "Resultado", "Detalle", "Estado"], filas),
        significa="El proyecto exige que un analizador de seguridad (SAST) frene la entrega "
                  "antes de desplegar. Esta sonda "
                  "NO corre SAST ni lo reemplaza: verifica que la PUERTA este puesta "
                  "-que el analisis este en el pipeline, que frene la entrega y no solo "
                  "avise, y que las supresiones traigan su motivo escrito-. Y agrega lo unico "
                  "que si revisa por su cuenta: credenciales con valor escrito en archivos de "
                  "configuracion, que es lo que mas caro sale y lo mas barato de encontrar.",
        importa="SAST hace FALLAR EL BUILD, que frena muchisimo mas que un informe que "
                "alguien tiene que leer. Por eso el Doctor no compite con el: compite con el "
                "olvido de enchufarlo. Un repositorio sin el paso en el pipeline pasa meses "
                "sin analizarse y se entera el dia de la entrega, que es el peor momento. Y "
                "una credencial escrita en el repositorio no se arregla borrandola: queda en "
                "el historial de git y hay que rotarla.",
        acciones=[] if estado == "OK" else [
            {"paso": "Si falta el paso de SAST: pedilo a la gente de Infra con el nombre "
                     "de este repositorio. Es configuracion del pipeline, no del codigo."},
            {"paso": "Si el analisis corre pero no frena: eso es una sugerencia, no una "
                     "puerta. Hay que configurarlo para que corte cuando la politica no se "
                     "cumple, y acordar el umbral con el equipo."},
            {"paso": "Si hay una supresion sin motivo: escribile el motivo AL LADO. Una "
                     "supresion sin justificacion es un hallazgo tapado, y el que la lea "
                     "dentro de seis meses no va a poder decidir si sigue valiendo."},
            {"paso": "Si aparece una credencial escrita: sacala del codigo Y ROTALA. Borrarla "
                     "no alcanza, porque queda en el historial de git."}],
        pedido=None if estado == "OK" else (
            "La puerta de seguridad de este repositorio tiene estos problemas:\n\n" +
            "\n".join("- " + f[0] + ": " + f[2] for f in malos) +
            "\n\nPor cada uno decime si se resuelve en el repositorio o si depende de la "
            "gente de Infra, porque son dos caminos distintos. Para lo que sea del "
            "repositorio, proponeme el cambio concreto. Si aparece alguna credencial "
            "escrita, tratala como comprometida: no alcanza con borrarla del archivo, hay "
            "que rotarla porque queda en el historial de git — decime que hay que rotar y a "
            "quien avisar." + _cierre()))


# --------------------------------------------------------- 8. puerta de calidad

# Que se busca en cada stack: nombre visible, como se reconoce que esta DECLARADA,
# y como se reconoce que el build la EXIGE. La segunda columna es la que importa.
CALIDAD_JAVA = [
    ("Cobertura (JaCoCo)", r"jacoco", r"<goal>\s*check\s*</goal>|<rule>|<limit>"),
    ("Analisis estatico (SpotBugs / PMD / Checkstyle)",
     r"spotbugs|pmd-maven|maven-checkstyle", r"<goal>\s*check\s*</goal>"),
    ("SonarQube", r"sonar", r"sonar\.qualitygate|<goal>\s*sonar\s*</goal>"),
    ("Tests en el build (Surefire / Failsafe)",
     r"surefire|failsafe", r"surefire|failsafe"),
    ("Version de Java y del build fijadas",
     r"<maven\.compiler\.release>|<java\.version>|<maven\.compiler\.source>",
     r"maven-enforcer-plugin|<maven\.compiler\.release>"),
]

CALIDAD_NODE = [
    ("Linter (ESLint)", r"eslint", r'"lint"\s*:'),
    ("Formateador (Prettier)", r"prettier", r'"format"\s*:|"lint"\s*:'),
    ("TypeScript en modo estricto", r'"typescript"', r'"strict"\s*:\s*true'),
    ("Tests (Vitest / Jest)", r"vitest|jest", r'"test"\s*:'),
    ("Umbral de cobertura", r"coverage", r"thresholds?|statements|branches"),
]


def sonda_calidad():
    us = unidades()
    if not us:
        return sin_codigo("Puerta de calidad",
                          "Verifica que el linter, el analisis estatico y el umbral de "
                          "cobertura esten declarados Y exigidos por el build.")
    filas = []
    for u in us:
        pre = u["ruta"] + ": "
        if es_java(u):
            conf = _leer(u["raiz"] + "/pom.xml") + _leer(u["raiz"] + "/build.gradle")
            reglas = CALIDAD_JAVA
        else:
            conf = _leer(u["raiz"] + "/package.json")
            # El patron anterior anclaba al principio del nombre (^), asi que NO leia
            # vite.config.ts -donde en Vite vive la configuracion de cobertura, porque
            # lo normal es no tener un vitest.config.ts aparte- ni .eslintrc.cjs ni
            # .prettierrc, que empiezan con punto. Dos hallazgos falsos garantizados
            # en cada front, imposibles de cerrar haciendo las cosas bien.
            for fn in sorted(os.listdir(u["raiz"])):
                if re.search(r"(?i)(eslint|prettier|tsconfig|vitest|jest|"
                             r"vite\.config|biome)", fn):
                    conf += "\n" + _leer(u["raiz"] + "/" + fn)
            reglas = CALIDAD_NODE
        for nombre, decl, exige in reglas:
            hay = re.search(decl, conf, re.I) is not None
            frena = hay and re.search(exige, conf, re.I) is not None
            if not hay:
                filas.append([pre + nombre, "no", "no", "no esta configurado", "HALLAZGO"])
            elif not frena:
                filas.append([pre + nombre, "si", "no se ve",
                              "esta configurado pero no se ve que el build lo exija: "
                              "configurado y no exigido es decoracion", "HALLAZGO"])
            else:
                filas.append([pre + nombre, "si", "si", "declarado y exigido", "OK"])
    estado = fila_estado(filas)
    malos = [f for f in filas if f[4] == "HALLAZGO"]
    return _res("Puerta de calidad", estado,
        str(len(filas)) + " chequeo(s) sobre la configuracion del build. " +
        ("Todo lo que hace falta esta declarado y exigido." if estado == "OK" else
         str(len(malos)) + " sin cerrar."),
        (["Herramienta", "Declarada", "Exigida por el build", "Detalle", "Estado"], filas),
        significa="Mira la configuracion del build -el pom.xml en el back, el package.json y "
                  "los archivos de configuracion en el front- y para cada herramienta de "
                  "calidad responde DOS preguntas distintas: si esta configurada, y si el "
                  "build la exige. La segunda es la que vale.",
        importa="Un linter configurado que nadie corre, o un umbral de cobertura que no "
                "frena nada, es decoracion: da la sensacion de que la calidad esta cubierta "
                "sin cubrir nada. Lo mismo que pasa con un control que no deja evidencia. La "
                "unica configuracion que cambia el comportamiento del equipo es la que hace "
                "fallar el build, porque es la unica que no se puede ignorar por apuro.",
        acciones=[] if estado == "OK" else [
            {"paso": "Empeza por las que ya estan configuradas y no se exigen: son las mas "
                     "baratas. El trabajo ya esta hecho, falta enchufarlo al build."},
            {"paso": "Para el umbral de cobertura, acordá el numero con el equipo ANTES de "
                     "ponerlo. Un umbral que nadie acordo se termina bajando en la primera "
                     "entrega apurada, y ahi deja de significar algo."},
            {"paso": "Para lo que no esta configurado: ponelo de a uno y con el build en "
                     "verde entre uno y otro. Enchufar cuatro herramientas juntas deja un "
                     "build rojo que nadie sabe por donde empezar a desarmar."},
            {"paso": "Corre el build completo despues de cada cambio.",
             "comando": "mvn -q verify"}],
        pedido=None if estado == "OK" else (
            "La puerta de calidad de este repositorio esta incompleta:\n\n" +
            "\n".join("- " + f[0] + " — declarada: " + f[1] + ", exigida por el build: " +
                      f[2] + " (" + f[3] + ")" for f in malos) +
            "\n\nEmpeza por las que ya estan configuradas y no se exigen, que son las mas "
            "baratas. Por cada una, proponeme el cambio exacto en el archivo de build para "
            "que el build falle cuando no se cumple. Para el umbral de cobertura NO elijas "
            "vos el numero: decime que numero tiene sentido segun lo que hay hoy y dejalo "
            "como propuesta para que lo acuerde el equipo. Y proponeme el orden en que "
            "conviene enchufarlas, de a una, dejando el build en verde entre una y otra." +
            _cierre()))


# ------------------------------------------------------- 9. practicas y patrones

# Cada practica: nombre, stacks donde aplica, expresion, y si se mira en los tests.
# La lista es CORTA a proposito. Todas tienen que cumplir dos condiciones: que casi
# no den falsos positivos, y que el linter no las cubra ya. Lo que el formateador
# arregla solo no entra aca.
PRACTICAS = [
    ("Salida por consola en vez del logger", "java",
     r"System\.(out|err)\.print", False,
     "en produccion esa linea no queda registrada en ningun lado"),
    # El cuerpo del catch se describe como "cero o mas comentarios y como mucho un
    # printStackTrace". Antes se enumeraban tres formas exactas y se escapaban las
    # demas: dos comentarios adentro, o un printStackTrace sobre una variable que no
    # se llamara "e" -el nombre estaba escrito en la expresion- pasaban de largo.
    ("Excepcion tragada", "java",
     r"catch\s*\([^)]*\)\s*\{(?:\s*(?://[^\n]*|/\*.*?\*/))*"
     r"(?:\s*\w+\.printStackTrace\s*\(\s*\)\s*;)?"
     r"(?:\s*(?://[^\n]*|/\*.*?\*/))*\s*\}", False,
     "el error desaparece y el sistema sigue como si nada hubiera pasado"),
    ("Entidad de persistencia expuesta en la capa de entrada", "java",
     r"import\s+(jakarta|javax)\.persistence\.", False,
     "la tabla de la base queda atada al contrato publico: cambiar una columna rompe "
     "a quien consume el endpoint"),
    ("Salida por consola en vez del logger", "node",
     r"\bconsole\.(log|debug)\s*\(", False,
     "queda en la consola del navegador del usuario, y a veces con datos adentro"),
    # Se agrega el any dentro de un generico -Record<string, any>, Array<any>-, que
    # es la forma mas comun en React y no tiene dos puntos delante.
    ("Tipo any", "node", r":\s*any\b|\bas\s+any\b|<[^>\n]*\bany\b[^>\n]*>", False,
     "apaga el chequeo de tipos justo donde mas hace falta"),
    ("Llamada HTTP adentro de un componente", "node",
     r"\b(fetch|axios)\s*[\.\(]", False,
     "mezcla la vista con el acceso a datos: no se puede probar el componente sin red"),
]


def _aplica(practica, u, p):
    _, stack, _, en_tests, _ = practica
    if stack == "java" and not es_java(u):
        return False
    if stack == "node" and es_java(u):
        return False
    if es_test(p) and not en_tests:
        return False
    if practica[0].startswith("Entidad de persistencia") and "/api/" not in p:
        return False
    if practica[0].startswith("Llamada HTTP") and not p.endswith((".tsx", ".jsx")):
        return False
    return True


def sonda_practicas():
    us = unidades()
    if not us:
        return sin_codigo("Practicas y patrones",
                          "Busca un puñado de practicas que el formateador no ve y que "
                          "cuestan caro: errores tragados, salida por consola, tipos "
                          "apagados, llamadas HTTP adentro de un componente.")
    conteo, ejemplos, mirados = {}, {}, 0
    for u in us:
        for p in fuentes(u):
            txt = None
            for pr in PRACTICAS:
                if not _aplica(pr, u, p):
                    continue
                if txt is None:
                    txt = _leer(p)
                    mirados += 1
                hits = re.findall(pr[2], txt)
                if hits:
                    conteo[pr[0]] = conteo.get(pr[0], 0) + len(hits)
                    ejemplos.setdefault(pr[0], []).append(_rel(p))
    if not mirados:
        return nada_medido("Practicas y patrones",
                           "Busca un punado de practicas que el formateador no ve y "
                           "que cuestan caro.", 0)
    filas = []
    for nombre, stack, _, _, porque in PRACTICAS:
        if nombre in conteo:
            continue
        filas.append([nombre, "0", "-", "no aparece", "OK"])
    for nombre in sorted(conteo, key=lambda k: -conteo[k]):
        porque = next(pr[4] for pr in PRACTICAS if pr[0] == nombre)
        filas.append([nombre, str(conteo[nombre]),
                      ", ".join(sorted(set(ejemplos[nombre]))[:3]), porque, "HALLAZGO"])
    # Sin duplicar el nombre cuando la misma practica existe en los dos stacks.
    vistos, limpio = set(), []
    for f in filas:
        clave = (f[0], f[4])
        if f[4] == "OK" and f[0] in [g[0] for g in filas if g[4] == "HALLAZGO"]:
            continue
        if clave in vistos:
            continue
        vistos.add(clave)
        limpio.append(f)
    filas = limpio
    estado = fila_estado(filas)
    total = sum(conteo.values())
    return _res("Practicas y patrones", estado,
        str(mirados) + " archivo(s) revisados. " +
        ("Ninguna de las practicas que se miran aparece en el codigo." if estado == "OK"
         else str(total) + " caso(s) en " + str(len(conteo)) + " practica(s)."),
        (["Practica", "Casos", "Donde", "Por que importa", "Estado"], filas),
        significa="Un puñado corto de practicas que el formateador y el linter basico NO "
                  "miran, elegidas con dos condiciones: que casi no den falsos positivos, y "
                  "que cuando aparecen cuesten caro. No es una revision de estilo: "
                  "indentacion, comillas y punto y coma son del formateador y no aparecen "
                  "aca.",
        importa="Son las que no se ven en una revision rapida y se pagan despues. Un error "
                "tragado convierte una falla en un comportamiento raro que nadie puede "
                "explicar seis meses despues. Un tipo apagado apaga el chequeo justo donde "
                "mas hacia falta. Una entidad de base expuesta en el contrato ata la tabla "
                "al endpoint: cambiar una columna le rompe el front a alguien.",
        acciones=[] if estado == "OK" else [
            {"paso": "Empeza por los errores tragados: son los unicos de esta lista que "
                     "esconden fallas reales en produccion. Los demas son deuda."},
            {"paso": "Por cada caso, arreglalo donde esta y preguntate si es un descuido "
                     "suelto o un patron que se repite. Si se repite, la salida no es "
                     "arreglar veinte lugares: es una regla en el linter."},
            {"paso": "Cuando una de estas se repita, movela al linter o a una regla de "
                     "ArchUnit. Ahi hace fallar el build, que frena mucho mas que este "
                     "informe. El Doctor sirve para descubrir cuales valen la pena."}],
        pedido=None if estado == "OK" else (
            "En el codigo aparecen estas practicas:\n\n" +
            "\n".join("- " + f[0] + ": " + f[1] + " caso(s) en " + f[2] + " — " + f[3]
                      for f in filas if f[4] == "HALLAZGO") +
            "\n\nEmpeza por los errores tragados, si hay, que son los unicos que esconden "
            "fallas reales en produccion. Por cada caso abri el archivo y proponeme el "
            "arreglo concreto. Despues decime cuales de estas practicas se repiten lo "
            "suficiente como para convertirlas en una regla del linter o un test de "
            "ArchUnit, para que el build las frene solo y no dependan de que alguien lea "
            "este informe." + _cierre()))




# --------------------------------------------- 10. la costura entre back y front

# Como se declara un mock en MSW. La v2 usa http.get(...), la v1 usaba rest.get(...):
# se aceptan las dos porque el equipo todavia no eligio version.
RE_MOCK = re.compile(
    r"\b(?:http|rest)\.(" + "|".join(VERBOS) + r")\s*\(\s*[\"'`]([^\"'`]+)[\"'`]")

# Como se ejerce un endpoint desde un test de RestAssured. El verbo y la ruta pueden
# venir en la misma linea o en la siguiente, asi que se busca sobre el texto entero.
RE_RESTASSURED = re.compile(
    r"\.\s*(" + "|".join(VERBOS) + r")\s*\(\s*[\"']([^\"']+)[\"']", re.I)


def _ruta_msw(spec):
    """De la ruta de un mock a la forma normalizada del contrato.

    MSW escribe los parametros con dos puntos -/recursos/:id- y OpenAPI con
    llaves -/recursos/{id}-. Sin traducir esto, NINGUNA ruta con parametro
    cruzaria y la sonda seria ruido puro."""
    spec = re.sub(r"https?://[^/]+", "", spec.split("?")[0])
    spec = re.sub(r":[A-Za-z_][\w]*", "{}", spec)
    spec = re.sub(r"\*", "{}", spec)
    return normalizar_ruta(spec)


def _contrato_del_proyecto():
    """El openapi de los repos de back. Es UNO solo para todos: eso es justamente
    lo que lo vuelve la costura — los dos lados miran el mismo archivo."""
    ops, donde = set(), []
    for u in unidades():
        if not es_java(u):
            continue
        for b, dirs, files in os.walk(u["raiz"]):
            dirs[:] = [d for d in dirs if d not in BASURA and not d.startswith(".")]
            for fn in files:
                if re.match(r"^(openapi|swagger)\.(ya?ml|json)$", fn):
                    p = os.path.join(b, fn)
                    donde.append(_rel(p))
                    ops |= _ops_del_contrato(_leer(p), fn.endswith(".json"))
    return ops, donde


def sonda_costura():
    """Que los dos lados esten hablando del MISMO contrato.

    Es el agujero que el equipo ya tenia identificado y que ninguna herramienta
    miraba: cada lado da verde por separado -el front simula al back con MSW- y el
    escenario queda cerrado en papel sin que nadie haya corrido las dos partes.

    La causa raiz no es que falte un test de integracion: es que el mock del front y
    el contrato del back pueden separarse sin que nada avise. Mientras el mock diga
    lo mismo que el contrato, simular es legitimo y barato. El dia que se separan, el
    front construye contra una mentira y se entera en la integracion, que es el
    momento mas caro.

    Se mira de los dos lados, porque son dos formas del mismo defecto:
      - front: un mock de un endpoint que el contrato no declara
      - back:  una operacion declarada que ningun test de API ejerce
    """
    us = unidades()
    if not us:
        return sin_codigo("La costura entre back y front",
                          "Verifica que los mocks del front y los tests del back "
                          "esten hablando del mismo contrato OpenAPI.")

    contrato, donde = _contrato_del_proyecto()
    if not contrato:
        hay_front = any(not es_java(u) for u in us)
        return _res("La costura entre back y front", "SIN DATOS",
            "No se encontro ningun contrato OpenAPI, asi que no hay contra que "
            "comparar." + (" Y hay front: esta simulando algo que nadie declaro."
                           if hay_front else ""),
            significa="Compara lo que el front simula con MSW y lo que los tests del "
                      "back ejercen, contra el mismo openapi.yaml. Sin ese archivo no "
                      "hay costura que mirar: hay dos lados sueltos.",
            importa="SIN DATOS no es aprobado. Si el front ya simula respuestas y no "
                    "hay contrato, lo que esta simulando salio de una conversacion o "
                    "de una suposicion, y no hay forma de saber si el back lo cumple.",
            acciones=[{"paso": "Consolida el contrato del back. Cada Tarea de capa de "
                               "entrada ya trae su fragmento OpenAPI: falta juntarlos.",
                       "comando": "usar la skill armar-swagger en el repo de back"}])

    filas = []

    # --- mitad del front: los mocks contra el contrato -------------------------
    mocks, con_front = {}, False
    for u in us:
        if es_java(u):
            continue
        con_front = True
        for p in fuentes(u):
            txt = _leer(p)
            if "http." not in txt and "rest." not in txt:
                continue
            for verbo, spec in RE_MOCK.findall(txt):
                if spec.startswith(("http://", "https://")) and "/" not in spec[8:]:
                    continue
                mocks.setdefault(verbo.upper() + " " + _ruta_msw(spec), _rel(p))

    for op in sorted(mocks):
        if op in contrato:
            filas.append(["front simula", op, mocks[op], "coincide con el contrato", "OK"])
        else:
            filas.append(["front simula", op, mocks[op],
                          "el contrato NO declara esta operacion: el front construye "
                          "-y sus tests pasan- contra algo que no existe", "HALLAZGO"])

    # --- mitad del back: los tests de API contra el contrato --------------------
    ejercidas, con_tests = set(), False
    for u in us:
        if not es_java(u):
            continue
        for p in fuentes(u):
            if not es_test(p):
                continue
            txt = _leer(p)
            if "restassured" not in txt.lower() and "given()" not in txt:
                continue
            con_tests = True
            for verbo, ruta in RE_RESTASSURED.findall(txt):
                ejercidas.add(verbo.upper() + " " + normalizar_ruta(
                    re.sub(r"/\d+(?=/|$)", "/{}", ruta)))

    if con_tests:
        for op in sorted(contrato):
            if op in ejercidas:
                filas.append(["back prueba", op, "-", "hay un test que la ejerce", "OK"])
            else:
                filas.append(["back prueba", op, "-",
                              "declarada en el contrato y ningun test de API la "
                              "ejerce: nadie comprobo que el back cumpla lo que promete",
                              "HALLAZGO"])

    if not filas:
        return _res("La costura entre back y front", "SIN DATOS",
            str(len(contrato)) + " operacion(es) en el contrato, pero no se encontro "
            "ni un mock del front ni un test de API del back que comparar.",
            significa="Compara lo que el front simula con MSW y lo que los tests del "
                      "back ejercen, contra el mismo contrato. No encontro ninguno de "
                      "los dos.",
            importa="SIN DATOS no es aprobado: la costura entre los dos lados quedo "
                    "sin revisar, que es justo donde el escenario se cierra en papel.",
            acciones=[{"paso": "Cuando el front tenga sus mocks de MSW y el back sus "
                               "tests de API, esta sonda empieza a cruzarlos sola."}])

    filas, ocultas = recortar(filas)
    estado = fila_estado(filas)
    sin_declarar = [f[1] for f in filas if f[0] == "front simula" and f[4] == "HALLAZGO"]
    sin_probar = [f[1] for f in filas if f[0] == "back prueba" and f[4] == "HALLAZGO"]
    resumen = (str(len(contrato)) + " operacion(es) en el contrato · " +
               str(len(mocks)) + " simulada(s) por el front · " +
               str(len(ejercidas)) + " ejercida(s) por tests del back. ")
    resumen += ("Los dos lados hablan del mismo contrato." if estado == "OK" else
                str(len(sin_declarar)) + " mock(s) fuera del contrato · " +
                str(len(sin_probar)) + " operacion(es) sin test que las ejerza.")

    return _res("La costura entre back y front", estado, resumen,
        (["Lado", "Operacion", "Donde", "Detalle", "Estado"], filas),
        significa="El front no espera al back: simula sus respuestas con MSW a partir "
                  "del openapi.yaml, y asi las dos partes avanzan en paralelo. Esta "
                  "sonda verifica que esa simulacion siga pegada a la realidad, y que "
                  "del otro lado haya un test que compruebe que el back cumple lo que "
                  "el contrato promete. Los dos lados, contra el MISMO archivo.",
        importa="Es el unico punto donde los dos repositorios se tocan, y hoy nadie lo "
                "mira. Cada lado da verde por separado: el front contra su mock, el "
                "back contra sus tests. Si el mock y el contrato se separan, el front "
                "construye pantallas contra respuestas que nunca van a llegar, y todo "
                "sigue en verde hasta la integracion — el momento mas caro para "
                "enterarse, y el unico en que ya no se puede volver atras barato. El "
                "escenario queda cerrado en papel y roto en los hechos.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada mock fuera del contrato: decidi cual de los dos esta "
                     "bien. O el endpoint hace falta y el back tiene que declararlo, o "
                     "el front esta simulando algo que nadie pidio."},
            {"paso": "Si el endpoint hace falta, agregalo al contrato ANTES de "
                     "escribirlo. Ese es el orden que hace que el front pueda avanzar "
                     "sin esperar.",
             "comando": "usar la skill armar-swagger en el repo de back"},
            {"paso": "Por cada operacion sin test que la ejerza: escribi el test de "
                     "API. Que el codigo exista no prueba que responda lo que el "
                     "contrato dice que responde."},
            {"paso": "Cuando esto se estabilice, generá los mocks de MSW DESDE el "
                     "openapi.yaml en vez de escribirlos a mano. Ahi el mock no puede "
                     "separarse del contrato ni queriendo, y esta sonda deja de tener "
                     "algo que encontrar — que es a donde conviene llegar."}],
        pedido=None if estado == "OK" else (
            "El front y el back no estan hablando del mismo contrato OpenAPI.\n\n" +
            ("Mocks del front que el contrato NO declara:\n" +
             "\n".join("- " + f[1] + "  (" + f[2] + ")" for f in filas
                       if f[0] == "front simula" and f[4] == "HALLAZGO") + "\n\n"
             if sin_declarar else "") +
            ("Operaciones del contrato que ningun test del back ejerce:\n" +
             "\n".join("- " + o for o in sin_probar) + "\n\n" if sin_probar else "") +
            "Por cada mock fuera del contrato, decime cual de los dos lados esta bien: "
            "si el endpoint hace falta -y entonces hay que declararlo en el contrato "
            "antes de escribirlo- o si el front esta simulando algo que nadie pidio. "
            "Mira tambien si alguna Historia del backlog cubre esa operacion, porque "
            "eso decide para que lado se corrige. Por cada operacion sin test, "
            "proponeme el test de API que la ejerza contra el contrato." + _cierre()))


# ---------------------------------------------------------------------- registro

# Las diez, en el orden en que conviene leerlas: primero que hay, despues el
# diseno, despues las puertas.
SONDAS = [sonda_repos, sonda_limites, sonda_contrato, sonda_costura,
          sonda_trazabilidad, sonda_duplicacion, sonda_dependencias,
          sonda_seguridad, sonda_calidad, sonda_practicas]

# Las que NO tienen nada que medir mientras no haya codigo clonado. doctor.py las
# saltea en vez de emitir ocho paneles identicos diciendo lo mismo; sonda_repos
# queda afuera de esta lista justamente porque es la que lo explica.
SOLO_CON_CODIGO = {"limites", "contrato", "costura", "trazabilidad", "duplicacion",
                   "dependencias", "seguridad", "calidad", "practicas"}


def hay_codigo():
    return bool(unidades())
