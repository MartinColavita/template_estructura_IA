#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doctor de {{PROYECTO}} — diagnostico de salud del proyecto.

UNA sola implementacion, a proposito: los envoltorios bin/doctor.sh y bin/doctor.ps1
solo llaman a este archivo. Duplicar la logica en dos shells es como se desincronizan
las cosas, y este proyecto ya tiene cicatrices de eso.

No modifica NADA. Solo lee y escribe su informe en doctor/salida/.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

# --------------------------------------------------------------------------- util

def raiz():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().replace("\\", "/")
    except Exception:
        pass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")

ROOT = raiz()

def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")

# ------------------------------------------------- rutas largas (limite de Windows)
#
# Windows corta las rutas en 260 caracteres -el viejo MAX_PATH- y lo hace EN SILENCIO:
# os.path.exists() devuelve False sobre un archivo que existe perfectamente. No hay
# error, no hay aviso; la sonda simplemente dice "rota" sobre una ruta sana, que es
# peor que no tener sonda. Se descubrio de casualidad, probando en una carpeta
# temporal profunda: la sonda de referencias reporto 42 rutas rotas que existian.
#
# Hoy no se dispara porque este clone vive en una raiz de 66 caracteres, pero quien
# lo clone hondo -un OneDrive con nombre largo, una carpeta de usuario con apellido
# compuesto- haria que el Doctor mienta en masa sin una sola senal.
#
# El camino conocido es el prefijo \\?\ sobre la ruta ABSOLUTA y NORMALIZADA, con
# barras invertidas: le dice a Windows que no aplique el limite. Con una ruta
# relativa, o con barras normales, no funciona — por eso pasa por abspath().
#
# Se usa SOLO para preguntarle al sistema de archivos. Lo que se MUESTRA en el
# informe sigue siendo la ruta comun: el prefijo es plomeria, no algo que el lector
# tenga que ver. Fuera de Windows no se toca nada, porque ahi el limite no existe.

def largo(p):
    """La misma ruta, en la forma que Windows acepta sin limite de largo."""
    if os.name != "nt":
        return p
    a = os.path.abspath(p)
    if a.startswith("\\\\?\\"):
        return a
    if a.startswith("\\\\"):
        # Ruta de red: \\servidor\recurso -> \\?\UNC\servidor\recurso
        return "\\\\?\\UNC\\" + a[2:]
    return "\\\\?\\" + a


def corto(p):
    """La inversa de largo(): la ruta como se muestra y como se compara."""
    if p.startswith("\\\\?\\UNC\\"):
        return "\\\\" + p[8:]
    if p.startswith("\\\\?\\"):
        return p[4:]
    return p


def existe(p):
    return os.path.exists(largo(p))


def es_archivo(p):
    return os.path.isfile(largo(p))


def es_dir(p):
    return os.path.isdir(largo(p))


def listar(p):
    return os.listdir(largo(p))


def abrir(p, modo="r"):
    return io.open(largo(p), modo, encoding="utf-8")


def leer(p):
    try:
        with io.open(largo(p), "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                           cwd=ROOT, timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""

IGNORAR = {".git", "node_modules", "borrador", ".idea", "__pycache__", "salida"}


def es_worktree(d):
    """True si la carpeta es un worktree de git: otra copia de trabajo del repo, no parte de el.

    Un worktree se reconoce porque su .git es un ARCHIVO -no una carpeta- que apunta a
    .git/worktrees/ del repo principal. Si el Doctor lo recorre, mide el proyecto dos veces:
    paso con uno abierto en .claude/worktrees/, y los wikilinks y la deuda salieron duplicados.

    No alcanza con "saltear lo que tenga .git": los repos de codigo clonados adentro de
    back/ y front/ tambien lo tienen -como carpeta- y esos SI se miden. Un submodulo tiene
    .git archivo pero apunta a .git/modules/, y tampoco es un worktree."""
    g = os.path.join(d, ".git")
    if not os.path.isfile(g):
        return False
    try:
        with io.open(g, "r", encoding="utf-8", errors="replace") as f:
            primera = f.readline()
    except Exception:
        return False
    return primera.startswith("gitdir:") and "/worktrees/" in primera.replace("\\", "/")

# Alcance de la corrida. None = el proyecto entero. "back" o "front" = un solo repo.
#
# Tres sondas NO tienen sentido acotadas y por eso se EXCLUYEN en vez de devolver
# SIN DATOS: conteos (mide documentos de la raiz), asimetria y gemelas (las dos
# COMPARAN back contra front, asi que con un solo lado no hay nada que comparar).
# La diferencia importa: SIN DATOS significa "no se pudo medir", y eso se lee como
# un pendiente. Estas no es que no se pudieron: es que no aplican.
ALCANCE = None
SOLO_PROYECTO = {"conteos", "asimetria", "gemelas"}


def base():
    """La raiz desde la que mira esta corrida."""
    return ROOT + "/" + ALCANCE if ALCANCE else ROOT


def espejo_de(repo):
    """La carpeta de skills de un repo de codigo, sin atarse a una herramienta.

    Los dos espejos -.agents/ y .claude/- son identicos: lo garantiza el hook. Asi
    que da igual cual se lea, PERO clavar uno solo en el codigo ata el Doctor a la
    convencion de una herramienta puntual, y este ecosistema corre en cuatro. Se
    prueba el que exista; si estan los dos, cualquiera sirve."""
    for conv in (".claude/skills", ".agents/skills"):
        ruta = ROOT + "/" + repo + "/" + conv
        if es_dir(ruta):
            return ruta
    return ROOT + "/" + repo + "/.claude/skills"


def raices_de_skills():
    """Donde viven las skills que le tocan a esta corrida."""
    if ALCANCE:
        return [espejo_de(ALCANCE)]
    return [SRC_SKILLS, espejo_de("back"), espejo_de("front")]

def walk_md():
    # Se recorre con la ruta larga y se devuelve la corta: si el clone vive hondo,
    # os.walk() sobre la ruta comun se queda mudo a partir de los 260 caracteres
    # -no explota, deja de ver archivos- y el Doctor mediria medio proyecto creyendo
    # que lo midio entero. Lo que sale de aca es la ruta de siempre, porque termina
    # impresa en el informe.
    for base, dirs, files in os.walk(largo(globals()["base"]())):
        dirs[:] = [d for d in dirs
                   if d not in IGNORAR and not es_worktree(os.path.join(base, d))]
        for fn in files:
            if fn.endswith(".md"):
                yield corto(os.path.join(base, fn))

def sin_copias(archivos):
    """Un representante por documento: los espejos no se cuentan tres veces.

    Las skills y los agentes viven en una fuente canonica -cerebro-digital/- y se
    copian, byte a byte, a los espejos que clava cada herramienta (.claude/, .agents/).
    Un hook pre-commit verifica que esas copias sean identicas. Contar el mismo
    problema una vez por copia infla el tablero: UN wikilink roto figuraba como
    TRES, y al arreglarlo en la fuente bajaban tres de golpe. Asi el numero deja de
    medir el proyecto y pasa a medir cuantos espejos tiene.

    Se agrupa por CONTENIDO, no por nombre ni por una lista clavada de carpetas
    espejo. Es a proposito: si una copia DERIVA -deja de ser byte identica- vuelve a
    contarse sola, que es justo lo que hay que ver. Nada se silencia por vivir en
    una carpeta con un nombre determinado.

    Gana como representante la ruta que no pasa por carpetas ocultas, que es la
    fuente canonica: el hallazgo se reporta donde hay que arreglarlo.

    Devuelve (representantes, cuantas copias quedaron afuera)."""
    def orden(p):
        r = rel(p)
        return (1 if any(s.startswith(".") for s in r.split("/")) else 0, r)

    vistos, unicos = set(), []
    for p in sorted(archivos, key=orden):
        h = hashlib.sha1(leer(p).encode("utf-8", "replace")).hexdigest()
        if h in vistos:
            continue
        vistos.add(h)
        unicos.append(p)
    return unicos, len(archivos) - len(unicos)


def fechas_git():
    """Ultima fecha de commit de cada archivo, en UNA sola llamada a git.

    Hacer `git log -1` por archivo serian cientos de procesos; esto recorre el log
    una vez y se queda con la primera fecha que ve para cada ruta, que es la mas
    reciente porque el log viene de nuevo a viejo."""
    salida = {}
    txt = git("log", "--format=%cd", "--date=short", "--name-only")
    fecha = None
    for linea in txt.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if len(linea) == 10 and linea[4] == "-" and linea[7] == "-":
            fecha = linea
        elif fecha and linea not in salida:
            salida[linea] = fecha
    return salida


def meses_desde(fecha):
    """Meses aproximados entre una fecha AAAA-MM-DD y hoy. Aproximado a proposito:
    lo que importa es el orden de magnitud, no el dia exacto."""
    import datetime
    try:
        a, m, d = (int(x) for x in fecha.split("-"))
        hoy = datetime.date.today()
        return (hoy.year - a) * 12 + (hoy.month - m)
    except Exception:
        return None


def dirs_de(p):
    return sorted(d for d in listar(p) if es_dir(os.path.join(p, d))) \
        if es_dir(p) else []

# ------------------------------------------------------------------------- sondas
# Cada sonda devuelve: (titulo, estado, resumen, filas)
#   estado: OK | HALLAZGO | SIN DATOS
# Tri-estado a proposito, SIN puntaje unico: un numero resume de mas y esconde
# que hay que arreglar. Un repo vacio NO es un repo sano.

SRC_SKILLS = ROOT + "/cerebro-digital/configuracion-ia/skills"

# Caracteres por token. Es una ESTIMACION, no una medicion: el tokenizador real
# depende del modelo y traerlo seria una dependencia externa, que este proyecto no
# admite. Para prosa en espanol con algo de codigo y markdown, la relacion ronda
# 3,6 caracteres por token. Sirve para COMPARAR skills entre si y para tener un
# orden de magnitud; no para facturar.
CHARS_POR_TOKEN = 3.6
TOPE_AGENTS = 7000   # tokens de AGENTS.md; arriba de esto, la sonda de tamano avisa que volvio a crecer


def tokens_aprox(texto):
    return int(round(len(texto) / CHARS_POR_TOKEN))


def descripcion_de(cuerpo):
    """El frontmatter YAML de una skill: es lo UNICO que el agente ve siempre.
    El resto del archivo pesa solo cuando la skill se invoca."""
    if not cuerpo.startswith("---"):
        return ""
    fin = cuerpo.find("\n---", 3)
    return cuerpo[:fin + 4] if fin > 0 else ""


def res(titulo, estado, resumen, tabla=None, grafico=None,
        significa=None, importa=None, acciones=None, pedido=None, claves=None):
    """El resultado de una sonda.

    Los tres ultimos campos son los que convierten una MEDICION en algo accionable:
      significa  — que quiere decir esto, en criollo, para alguien que no lo escribio
      importa    — que se rompe, o que riesgo hay, si no se arregla
      acciones   — que hacer, concreto, con el comando cuando existe
      pedido     — el texto para copiar y pegarle a un asistente, CON los datos del
                   hallazgo adentro, para que pueda trabajar sin pedir contexto
      claves     — la huella de cada hallazgo, para la sonda que corta su tabla: se calcula
                   sobre la lista completa (comparar.claves_de la usa en vez de la tabla)

    Van ACA y no en la plantilla HTML a proposito: solo la sonda sabe que midio y
    por que. Texto de remediacion escrito en el diseno es decoracion que se despega
    de la realidad — dice una cosa mientras el codigo hace otra.
    """
    return {"titulo": titulo, "estado": estado, "resumen": resumen,
            "tabla": tabla, "grafico": grafico,
            "significa": significa, "importa": importa,
            "acciones": acciones or [], "pedido": pedido, "claves": claves}


# Todo pedido termina igual. No es formalidad: un informe que produce texto para
# pegarle a una IA es tambien una forma comoda de romper cosas rapido. La IA
# propone, la persona decide.
CIERRE = ("\n\nNo edites nada todavia: mostrame los cambios que proponés, uno por uno, "
          "y espero mi confirmacion.")


def sonda_guardarrailes():
    filas = []
    hooks = (git("config", "core.hooksPath") or "").strip()
    filas.append(["core.hooksPath configurado", hooks or "(sin configurar)",
                  "OK" if hooks else "HALLAZGO"])
    hook = ROOT + "/.githooks/pre-commit"
    presente = es_archivo(hook)
    filas.append(["Hook pre-commit presente", "si" if presente else "no",
                  "OK" if presente else "HALLAZGO"])
    if presente:
        cuerpo = leer(hook)
        for fn in ["check_mirror", "check_pair", "check_control_chars", "check_conteo_skills", "check_skills_spec"]:
            hay = fn in cuerpo
            filas.append(["Guarda " + fn, "si" if hay else "no",
                          "OK" if hay else "HALLAZGO"])
        primera = cuerpo.splitlines()[0] if cuerpo else ""
        filas.append(["Shebang", primera, "OK" if "bash" in primera else "HALLAZGO"])
    malas = sum(1 for f in filas if f[2] == "HALLAZGO")
    estado = "OK" if malas == 0 else "HALLAZGO"
    if not hooks:
        resumen = "El hook existe pero NO esta activado en este clone: corre `git config core.hooksPath .githooks`."
    else:
        resumen = "Los guardarrailes del repositorio estan activos." if malas == 0 \
            else str(malas) + " guarda(s) faltante(s) o mal configurada(s)."
    return res("Guardarrailes del repositorio", estado, resumen,
        (["Guarda", "Valor", "Estado"], filas),
        significa="El repositorio trae un control automatico que corre antes de cada commit y "
                  "frena cosas que se rompen en silencio: espejos de skills desincronizados, "
                  "caracteres invisibles pegados en un texto, conteos que dejaron de coincidir.",
        importa="Los hooks NO viajan activados en un clone: cada persona los activa en su maquina. "
                "Si no esta configurado, el control existe en el repositorio y no protege nada aca "
                "— y no te vas a enterar hasta que algo ya se rompio.",
        acciones=[] if estado == "OK" else (
            [{"paso": "Activa el hook en este clone. Se hace UNA sola vez por persona.",
              "comando": "git config core.hooksPath .githooks"}]
            if not hooks else
            [{"paso": "Falta alguna guarda en .githooks/pre-commit. Mira la tabla: la fila que "
                      "dice 'no' te indica cual. Compara contra la version del repositorio."}]),
        pedido=None if estado == "OK" else (
            "En este repositorio el hook de pre-commit no esta bien configurado.\n\n" +
            "\n".join("- " + f[0] + ": " + f[1] for f in filas if f[2] == "HALLAZGO") +
            "\n\nLee .githooks/pre-commit y decime que hace cada guarda que falta y que deja "
            "de estar protegido sin ella. Si el problema es que no esta activado en mi clone, "
            "decimelo asi nomas: es un solo comando." + CIERRE))


def sonda_espejos():
    if not es_dir(SRC_SKILLS):
        return res("Espejos de skills", "SIN DATOS", "No se encontro la carpeta de skills.",
                   significa="Esta sonda mira las skills del Cerebro, y la carpeta que las "
                             "contiene no aparece donde se la espera.",
                   importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar. O el "
                           "Doctor se corrio fuera del repositorio, o la carpeta se movio.",
                   acciones=[{"paso": "Verifica que estas parado en la raiz del repositorio.",
                              "comando": "git rev-parse --show-toplevel"},
                             {"paso": "Si la carpeta se movio, actualiza SRC_SKILLS en "
                                      "doctor/doctor.py — hoy apunta a "
                                      "cerebro-digital/configuracion-ia/skills/."}])
    fuente = dirs_de(SRC_SKILLS)
    filas = []
    espejos = ([ALCANCE + "/.agents/skills", ALCANCE + "/.claude/skills"] if ALCANCE
               else [".agents/skills", ".claude/skills"])
    if ALCANCE:
        # En un repo de codigo no hay "fuente canonica": son dos copias gemelas y
        # ninguna manda. Lo unico exigible es que sean identicas entre si.
        fuente = dirs_de(ROOT + "/" + espejos[1])
        SRC = ROOT + "/" + espejos[1]
    else:
        SRC = SRC_SKILLS
    for espejo in espejos:
        ruta = ROOT + "/" + espejo
        presentes = dirs_de(ruta)
        faltan = [s for s in fuente if s not in presentes]
        sobran = [s for s in presentes if s not in fuente]
        distintas = []
        for s in fuente:
            a, b = SRC + "/" + s + "/SKILL.md", ruta + "/" + s + "/SKILL.md"
            if es_archivo(a) and es_archivo(b):
                if leer(a).replace("\r\n", "\n") != leer(b).replace("\r\n", "\n"):
                    distintas.append(s)
        problema = faltan or sobran or distintas
        detalle = []
        if faltan:
            detalle.append("faltan: " + ", ".join(faltan))
        if sobran:
            detalle.append("sobran: " + ", ".join(sobran))
        if distintas:
            detalle.append("distintas: " + ", ".join(distintas))
        filas.append([espejo, str(len(presentes)) + " skills",
                      "; ".join(detalle) if detalle else "identico a la fuente",
                      "HALLAZGO" if problema else "OK"])
    estado = "HALLAZGO" if any(f[3] == "HALLAZGO" for f in filas) else "OK"
    resumen = "Los dos espejos coinciden con la fuente (" + str(len(fuente)) + " skills)." \
        if estado == "OK" else "Hay drift entre la fuente y algun espejo."
    return res("Espejos de skills", estado, resumen,
        (["Espejo", "Cantidad", "Detalle", "Estado"], filas),
        significa="Las skills viven UNA sola vez, en cerebro-digital/configuracion-ia/skills/, y "
                  "se copian a dos espejos porque cada herramienta las busca en un lugar distinto: "
                  ".agents/skills/ y .claude/skills/. Los tres tienen que decir exactamente lo mismo.",
        importa="Si un espejo se desincroniza, dos personas con herramientas distintas leen "
                "instrucciones distintas y ninguna se entera. El que edito el espejo en vez de la "
                "fuente ve su cambio funcionar, y el del otro lado nunca lo recibe.",
        acciones=[] if estado == "OK" else [
            {"paso": "Sincroniza los espejos desde la fuente. Nunca al reves: la fuente manda.",
             "comando": "bin/sync-skills.sh"},
            {"paso": "Agrega los espejos al commit, si no el commit guarda la version vieja.",
             "comando": "git add .agents/skills .claude/skills"},
            {"paso": "Si editaste un espejo por error, copia tu cambio a la fuente ANTES de "
                     "sincronizar — si no, sincronizar lo pisa y lo perdes."}],
        pedido=None if estado == "OK" else (
            "Los espejos de skills de este repositorio estan desincronizados con la fuente "
            "(cerebro-digital/configuracion-ia/skills/).\n\n" +
            "\n".join("- " + f[0] + ": " + f[2] for f in filas if f[3] == "HALLAZGO") +
            "\n\nAntes de sincronizar, compara los archivos que difieren y decime en cual de "
            "los dos lados esta el cambio bueno. Si alguien edito un espejo en vez de la fuente, "
            "hay que subir ese cambio a la fuente primero o se pierde al sincronizar." + CIERRE))


def sonda_conteos():
    if not es_dir(SRC_SKILLS):
        return res("Conteos declarados", "SIN DATOS", "No se encontro la carpeta de skills.",
                   significa="Esta sonda mira las skills del Cerebro, y la carpeta que las "
                             "contiene no aparece donde se la espera.",
                   importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar. O el "
                           "Doctor se corrio fuera del repositorio, o la carpeta se movio.",
                   acciones=[{"paso": "Verifica que estas parado en la raiz del repositorio.",
                              "comando": "git rev-parse --show-toplevel"},
                             {"paso": "Si la carpeta se movio, actualiza SRC_SKILLS en "
                                      "doctor/doctor.py — hoy apunta a "
                                      "cerebro-digital/configuracion-ia/skills/."}])
    real = len(dirs_de(SRC_SKILLS))
    patrones = [
        ("AGENTS.md", r"\*\*(\d+) habilidades\*\*"),
        ("README.md", r"Skills del Ecosistema \((\d+) habilid"),
        ("INSTALACION.md", r"[Ll]as \*\*(\d+) skills\*\*"),
    ]
    filas = []
    for arch, pat in patrones:
        p = ROOT + "/" + arch
        if not es_archivo(p):
            filas.append([arch, "-", "archivo ausente", "SIN DATOS"]); continue
        m = re.search(pat, leer(p))
        if not m:
            filas.append([arch, "-", "no se encontro el patron (cambio la redaccion)", "HALLAZGO"])
        else:
            d = int(m.group(1))
            filas.append([arch, str(d), "coincide" if d == real else "declara " + str(d) + ", hay " + str(real),
                          "OK" if d == real else "HALLAZGO"])
    # que ademas las LISTEN, no solo el numero
    for arch in ["README.md", "cerebro-digital/index.md"]:
        p = ROOT + "/" + arch
        if not es_archivo(p):
            continue
        cuerpo = leer(p)
        ausentes = [s for s in dirs_de(SRC_SKILLS) if s not in cuerpo]
        filas.append([arch + " (lista completa)", str(real - len(ausentes)) + "/" + str(real),
                      "no nombra: " + ", ".join(ausentes) if ausentes else "las nombra a todas",
                      "HALLAZGO" if ausentes else "OK"])
    estado = "HALLAZGO" if any(f[3] == "HALLAZGO" for f in filas) else "OK"
    return res("Conteos declarados vs. realidad", estado,
        "Hay " + str(real) + " skills en disco." +
        ("" if estado == "OK" else " Algun documento declara otra cosa."),
        (["Documento", "Declara", "Detalle", "Estado"], filas),
        significa="Varios documentos anuncian cuantas skills hay y ademas las listan una por una. "
                  "Esta sonda cuenta las carpetas reales y compara las dos cosas: el numero y la lista.",
        importa="Un numero que nadie verifica envejece en silencio y despues se cita como dato duro. "
                "Y la lista incompleta engana mas que el numero: alguien lee el README, no ve una "
                "skill, y no se entera de que existe.",
        acciones=[] if estado == "OK" else [
            {"paso": "Mira la tabla: la fila que falla te dice el documento y que declara."},
            {"paso": "Corregi el numero Y la lista. Un conteo al dia con una lista incompleta "
                     "engana igual, y encima da confianza."},
            {"paso": "Si cambiaste la redaccion de la frase, actualiza tambien el patron que la "
                     "busca en .githooks/pre-commit — si no, la guarda deja de verificar sin avisar."}],
        pedido=None if estado == "OK" else (
            "En este repositorio hay " + str(real) + " skills en "
            "cerebro-digital/configuracion-ia/skills/, y algunos documentos declaran otra cosa:\n\n" +
            "\n".join("- " + f[0] + ": " + f[2] for f in filas if f[3] == "HALLAZGO") +
            "\n\nCorregi el numero Y la lista en cada uno. Ojo: un conteo al dia con una lista "
            "incompleta engana igual, asi que verifica que cada documento NOMBRE las " + str(real) +
            " skills, no solo que diga el numero correcto." + CIERRE))


def sonda_wikilinks():
    objetivos = set()
    mds = list(walk_md())
    for p in mds:
        r = rel(p)[:-3]
        partes = r.split("/")
        objetivos.add(partes[-1]); objetivos.add(r)
        for i in range(1, len(partes)):
            objetivos.add("/".join(partes[i:]))
        if partes[-1] == "SKILL" and len(partes) >= 2:
            objetivos.add(partes[-2])
            for i in range(1, len(partes) - 1):
                objetivos.add("/".join(partes[i:-1]))
        if partes[-1] in ("00-index", "INDICE", "index") and len(partes) >= 2:
            objetivos.add(partes[-2])
    # placeholders de sintaxis: son ejemplos, no enlaces
    PLACEHOLDER = {"concepto", "archivo", "regla-negocio", "nombre-concepto", "nombre-de-la-skill"}
    # doctor/ documenta la sintaxis [[x]] como ejemplo: contarla seria reportar
    # como roto un enlace que nadie quiso hacer. Se saca ANTES de elegir
    # representante, para que un archivo de doctor/ no represente a otro y se
    # lleve puesto un hallazgo real.
    revisables = [p for p in mds if not rel(p).startswith("doctor/")]
    # Las skills VENDORIZADAS (DEPENDENCIAS-EXTERNAS.md) son de terceros y no se editan: un
    # [[180, 200]] en su contrato es JSON de su propio formato, no un enlace de este Cerebro.
    vendidas = skills_vendidas_declaradas()
    revisables = [p for p in revisables if not es_de_skill_vendida(rel(p), vendidas)]
    # Un documento copiado a los espejos se revisa UNA vez: si no, el mismo enlace
    # roto figura tres veces -fuente, .agents/ y .claude/- y el tablero infla.
    revisables, copias = sin_copias(revisables)
    rotos = []
    for p in revisables:
        for m in re.findall(r"\[\[([^\]|#]+)", leer(p)):
            k = m.strip()
            if k in objetivos or k in PLACEHOLDER:
                continue
            rotos.append([rel(p), k])
    filas = rotos[:40]
    estado = "OK" if not rotos else "HALLAZGO"
    resumen = str(len(mds)) + " archivos .md escaneados" + \
        ("" if not copias else " (" + str(copias) + " son copia byte identica de otro "
         "-los espejos- y se revisaron una sola vez)") + "; " + \
        ("ningun wikilink roto." if not rotos else str(len(rotos)) + " wikilink(s) que no resuelven.")
    return res("Wikilinks que no resuelven", estado, resumen,
        (["Archivo", "Enlace roto"], filas) if filas else None,
        claves=[a + " | " + b for a, b in rotos],
        significa="Un wikilink es un enlace entre documentos, escrito [[asi]]. Esta sonda revisa "
                  "que cada uno llegue a un archivo que realmente existe.",
        importa="El que sigue el enlace no llega a ningun lado. Y peor: hace creer que la "
                "documentacion esta conectada cuando tiene agujeros, asi que nadie sale a buscar "
                "lo que falta.",
        acciones=[] if estado == "OK" else [
            {"paso": "Mira la tabla: cada fila dice el archivo y el enlace que no resuelve."},
            {"paso": "Si el destino se movio o se renombro, corregi el enlace."},
            {"paso": "Si el documento ya no existe, borra el enlace o reemplazalo por el que "
                     "lo sucedio. No lo dejes 'por las dudas'."},
            {"paso": "Si es un ejemplo de sintaxis y no un enlace de verdad, reescribilo para que "
                     "no parezca uno — el escaneo no puede adivinar la intencion."}],
        pedido=None if estado == "OK" else (
            "En este repositorio hay " + str(len(rotos)) + " wikilinks que no resuelven a ningun "
            "archivo. Son enlaces entre documentos escritos [[asi]]. " +
            # El pedido decia "esta es la lista completa" mientras estaba cortado en 40.
            # Con 41 o mas, le mentia al asistente que lo recibe: se pone a trabajar
            # creyendo que cerro el tema y quedan enlaces rotos que nadie volvio a ver.
            ("Esta es la lista completa, con el archivo donde esta cada uno:\n\n"
             if len(rotos) <= 40 else
             "Van los primeros 40 de " + str(len(rotos)) + "; el resto sale de correr "
             "`bash doctor/bin/doctor.sh --solo wikilinks`:\n\n") +
            "\n".join("- " + a + "  ->  [[" + b + "]]" for a, b in rotos[:40]) +
            "\n\nPor cada uno, buscá en el repositorio si existe un archivo con nombre parecido "
            "(puede haberse movido o renombrado) y proponeme el reemplazo. Si el documento ya no "
            "existe, decimelo y proponé si conviene borrar el enlace o apuntarlo a otro lado. Si "
            "alguno es un ejemplo de sintaxis y no un enlace real, marcalo aparte." + CIERRE))


def sonda_estructura():
    """Que existe hoy del arbol que los README prometen.

    Tres cosas de esta sonda estaban mal y se corrigieron juntas, porque las tres
    salian del mismo error: medir la promesa con la vara equivocada.

    1. El resumen era un LITERAL que afirmaba "back/ y front/ todavia no tienen
       codigo". Se imprimia igual con los repos clonados, contradiciendo a la sonda
       de repos DOS RENGLONES mas abajo del mismo informe. Ahora se arma con lo que
       se midio.
    2. Contaba archivos VERSIONADOS (`git ls-files`). El codigo de back/ y front/
       vive en su propio repositorio y esta gitignoreado a proposito, asi que ese
       numero no podia crecer nunca: el veredicto era estructuralmente incapaz de
       cambiar el dia que llegara el codigo.
    3. El umbral -doce archivos- no media codigo: media SKILLS. back/ cruzo a
       "materializado" con cero lineas de codigo, solo porque le agregaron una sexta
       skill a los espejos.

    Ahora la pregunta es la correcta y directa: ¿esta carpeta tiene una unidad de
    codigo adentro? Lo contesta el mismo detector que usan las sondas de codigo, asi
    que las dos no se pueden volver a contradecir."""
    import codigo                                                          # noqa
    con_unidad = set()
    for u in codigo.unidades():
        con_unidad.add(u["slot"])

    filas = []
    objetivo = ([ALCANCE] if ALCANCE else
                ["back", "front", "qa", "cerebro-digital", "tablero", "doctor"])
    for d in objetivo:
        p = ROOT + "/" + d
        if not es_dir(p):
            filas.append([d, "-", "no existe", "HALLAZGO"]); continue
        n = len([x for x in listar(p) if not x.startswith(".")])
        # Una carpeta preparada para alojar un repositorio de codigo y todavia sin el
        # es una PROMESA, no una rotura. Se detecta por el CONTENIDO -tiene su espejo
        # de skills y no tiene unidad de codigo-, nunca por el nombre: asi cualquier
        # repo nuevo califica, no solo los dos que existen hoy.
        es_slot = any(es_dir(p + "/" + c) for c in (".claude/skills", ".agents/skills"))
        if es_slot and d not in con_unidad:
            filas.append([d, str(n) + " entradas", "prometido: todavia sin codigo clonado",
                          "SIN DATOS"])
        elif es_slot:
            filas.append([d, str(n) + " entradas", "materializado: con codigo clonado", "OK"])
        else:
            filas.append([d, str(n) + " entradas", "materializado", "OK"])
    con_datos = [f for f in filas if f[3] != "SIN DATOS"]
    estado = "HALLAZGO" if any(f[3] == "HALLAZGO" for f in con_datos) else "OK"

    vacias = [f[0] for f in filas if f[3] == "SIN DATOS"]
    faltan = [f[0] for f in filas if f[3] == "HALLAZGO"]
    resumen = str(len(filas)) + " carpeta(s) del arbol prometido. "
    if faltan:
        resumen += "No existe(n): " + ", ".join(faltan) + ". "
    if vacias:
        resumen += ("Sin codigo clonado todavia: " + ", ".join(v + "/" for v in vacias) +
                    " — por eso las sondas de codigo no miden sobre esa(s) carpeta(s).")
    elif not faltan:
        resumen += "Todas existen y las que esperan codigo ya lo tienen."
    return res("Estructura del proyecto", estado, resumen,
        (["Carpeta", "Entradas", "Detalle", "Estado"], filas),
        significa="Compara el arbol de carpetas que los README prometen contra lo que existe hoy "
                  "en el repositorio.",
        importa="Una carpeta prometida y todavia vacia NO es un error: es trabajo que no se hizo. "
                "Se marca gris y no rojo justo para no confundir 'falta hacerlo' con 'esta roto' — "
                "si no, la primera corrida sale toda roja y nadie vuelve a abrir el informe.",
        acciones=[] if estado == "OK" else [
            {"paso": "Una carpeta en HALLAZGO es una que el README nombra y que no existe. "
                     "Decidi: crearla, o sacarla del README."}],
        pedido=None if estado == "OK" else (
            "Los README de este repositorio prometen carpetas que hoy no existen:\n\n" +
            "\n".join("- " + f[0] + ": " + f[2] for f in filas if f[3] == "HALLAZGO") +
            "\n\nPor cada una, busca en los README donde se la nombra y decime si es trabajo "
            "que falta hacer o si quedo de una estructura vieja que ya se descarto." + CIERRE))


def sonda_asimetria():
    a, b = dirs_de(espejo_de("back")), dirs_de(espejo_de("front"))
    if not a and not b:
        return res("Asimetria back / front", "SIN DATOS", "No hay skills en los repos de codigo.",
                   significa="Compara las skills de back/ con las de front/. Hoy no hay ninguna "
                             "de los dos lados, asi que no hay nada que comparar.",
                   importa="SIN DATOS no es aprobado, pero aca es esperable: los repos de codigo "
                           "todavia no arrancaron. Cuando tengan sus skills, esta sonda empieza a "
                           "medir sola, sin tocar nada.")
    # Asimetrias DECLARADAS: viven de un solo lado a proposito y esta escrito por que.
    # Una asimetria declarada es una decision; una sin declarar es un descuido, y desde
    # afuera se ven iguales — por eso la lista es explicita y no se infiere.
    ESPERADAS = {"armar-swagger": "solo back: consolida el openapi.yaml, que el front no produce"}
    filas = []
    for s in sorted(set(a) | set(b)):
        en_a, en_b = s in a, s in b
        if en_a == en_b:
            filas.append([s, "si", "si", "en los dos", "OK"])
        elif s in ESPERADAS:
            # Declarada: la fila NO puede decir HALLAZGO. Si lo dijera, el informe se
            # contradiria con su propio veredicto — y el autocontrol lo marca.
            filas.append([s, "si" if en_a else "no", "si" if en_b else "no",
                          "asimetria declarada — " + ESPERADAS[s], "OK"])
        else:
            filas.append([s, "si" if en_a else "no", "si" if en_b else "no",
                          "falta de un lado y no esta declarado", "HALLAZGO"])
    reales = [f[0] for f in filas if f[4] == "HALLAZGO"]
    estado = "OK" if not reales else "HALLAZGO"
    resumen = ("Simetricos, salvo " + str(len(ESPERADAS)) + " asimetria(s) declarada(s)."
               if estado == "OK" else
               "Skills que viven de un lado y no del otro, sin declararlo: " + ", ".join(reales))
    return res("Asimetria back / front", estado, resumen,
        (["Skill", "back", "front", "Detalle", "Estado"], filas),
        significa="back/ y front/ tienen cada uno su propio juego de skills de desarrollo. Esta "
                  "sonda compara las dos listas y marca las que estan de un solo lado.",
        importa="Si una skill vive de un lado y no del otro, el mismo defecto se detecta en un "
                "repositorio y pasa desapercibido en el otro. Nadie lo nota, porque de cada lado "
                "todo parece estar bien.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada skill que falta de un lado, elegi una de dos: copiarla y adaptarla "
                     "al stack de ese repositorio, o dejarla de un solo lado a proposito."},
            {"paso": "Si la dejas de un solo lado, DECLARALO por escrito en su SKILL.md. Una "
                     "asimetria declarada es una decision; una sin declarar es un descuido, y "
                     "desde afuera se ven iguales. (Ejemplo: armar-swagger es solo de back.)"}],
        pedido=None if estado == "OK" else (
            "En este repositorio, back/ y front/ tienen cada uno sus skills de desarrollo, y "
            "estas viven de un solo lado sin que este declarado por que:\n\n" +
            "\n".join("- " + f[0] + " (back: " + f[1] + ", front: " + f[2] + ")"
                       for f in filas if f[4] == "HALLAZGO") +
            "\n\nPor cada una, lee su SKILL.md y decime si tiene sentido en el otro repositorio "
            "-adaptada al stack- o si es genuinamente de un solo lado. Si es de un solo lado, "
            "proponeme la frase que hay que agregarle al SKILL.md para dejarlo declarado." + CIERRE))


def sonda_tamano():
    FUENTE = raices_de_skills()[0]
    if not es_dir(FUENTE):
        return res("Costo de contexto por skill", "SIN DATOS", "No se encontro la carpeta de skills.",
                   significa="Esta sonda mira las skills del Cerebro, y la carpeta que las "
                             "contiene no aparece donde se la espera.",
                   importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar. O el "
                           "Doctor se corrio fuera del repositorio, o la carpeta se movio.",
                   acciones=[{"paso": "Verifica que estas parado en la raiz del repositorio.",
                              "comando": "git rev-parse --show-toplevel"},
                             {"paso": "Si la carpeta se movio, actualiza SRC_SKILLS en "
                                      "doctor/doctor.py — hoy apunta a "
                                      "cerebro-digital/configuracion-ia/skills/."}])
    filas, grafico = [], []
    siempre = 0          # lo que pesa SIEMPRE: las descripciones
    for s in dirs_de(FUENTE):
        p = FUENTE + "/" + s + "/SKILL.md"
        cuerpo = leer(p)
        n = len(cuerpo.splitlines())
        tk = tokens_aprox(cuerpo)
        tk_desc = tokens_aprox(descripcion_de(cuerpo))
        siempre += tk_desc
        grafico.append((s, tk))
        filas.append([s, str(n), "~" + str(tk), "~" + str(tk_desc),
                      "" if n <= 250 else "grande: revisar si conviene partirla",
                      "OK" if n <= 250 else "HALLAZGO"])
    filas.sort(key=lambda f: -int(f[2].lstrip("~")))
    # AGENTS.md se carga ENTERO en cada sesion y en cada subagente: es el costo fijo mas grande, y nadie lo medía.
    # Paso de ~15.000 a ~5.500 tokens (M-030); el tope avisa si vuelve a crecer.
    reglas = leer(ROOT + "/AGENTS.md")
    if reglas:
        tk_reglas = tokens_aprox(reglas)
        siempre += tk_reglas
        filas.insert(0, ["AGENTS.md (reglas)", str(len(reglas.splitlines())), "~" + str(tk_reglas), "~" + str(tk_reglas),
                         "se carga entero en cada sesion y en cada subagente" +
                         ("" if tk_reglas <= TOPE_AGENTS else "; paso el tope de ~" + str(TOPE_AGENTS) + " tokens: volvio a crecer"),
                         "OK" if tk_reglas <= TOPE_AGENTS else "HALLAZGO"])
    grandes = [f[0] for f in filas if f[5] == "HALLAZGO"]
    estado = "OK" if not grandes else "HALLAZGO"
    total = sum(len(leer(FUENTE + "/" + s + "/SKILL.md").splitlines()) for s, _ in grafico)
    tk_total = sum(v for _, v in grafico)
    return res("Costo de contexto por skill", estado,
        str(len(grafico)) + " skills · ~" + str(siempre) + " tokens pesan SIEMPRE (las "
        "descripciones y AGENTS.md) · ~" + str(tk_total) + " tokens si se cargaran todas enteras, que no pasa." +
        ("" if estado == "OK" else " Grandes: " + ", ".join(grandes)),
        (["Skill", "Lineas", "Tokens al invocarla", "Tokens que pesan siempre", "Detalle", "Estado"], filas),
        sorted(grafico, key=lambda x: -x[1])[:15],
        significa="Las skills NO se cargan todas. Lo que el asistente tiene siempre a la vista es "
                  "la DESCRIPCION de cada una, para decidir cual le sirve; el archivo entero pesa "
                  "solo cuando la invoca. Por eso hay dos numeros y no uno: el que pagas siempre "
                  "(~" + str(siempre) + " tokens entre las " + str(len(grafico)) + ") y el que pagas "
                  "al usar esa skill puntual. Los tokens son una ESTIMACION (" +
                  str(CHARS_POR_TOKEN).replace(".", ",") + " caracteres por token): sirven para "
                  "comparar skills entre si, no como medicion exacta.",
        importa="El numero que conviene vigilar es el primero, porque se paga en CADA consulta, "
                "aunque no se use ninguna skill. El segundo se paga una vez y solo si la skill "
                "hace falta. Que una skill sea grande NO es un error si su descripcion es corta y "
                "precisa: se carga poco y cuando se carga, sirve.",
        acciones=[] if estado == "OK" else [
            {"paso": "Mira las que pasan el umbral en el grafico. Preguntate si mezclan dos "
                     "trabajos distintos que en realidad son dos skills."},
            {"paso": "Antes de tocar una skill grande, mira su columna de 'tokens que pesan "
                     "siempre'. Si esa es chica, la skill esta bien: se carga poco."},
            {"paso": "Si es grande porque hace UNA cosa y la hace bien, dejala. Partirla solo para "
                     "bajar el numero deja dos skills que siempre se invocan juntas: mismo costo, "
                     "mas piezas que mantener."},
            {"paso": "Antes de partir, fijate que no haya texto repetido entre skills. Eso se "
                     "extrae a un documento y se referencia, que baja el costo sin partir nada."}],
        pedido=None if estado == "OK" else (
            "Estas skills de cerebro-digital/configuracion-ia/skills/ pasan el umbral de 250 "
            "lineas:\n\n" +
            "\n".join("- " + f[0] + ": " + f[1] + " lineas, ~" + f[2].lstrip("~") +
                       " tokens al invocarla, ~" + f[3].lstrip("~") + " tokens que pesan siempre"
                       for f in filas if f[5] == "HALLAZGO") +
            "\n\nLee cada una entera y decime, para cada una: si mezcla dos trabajos distintos "
            "que podrian ser dos skills, o si es grande porque hace UNA cosa y la hace bien. Si "
            "proponés partir alguna, decime que queda en cada parte y si se invocarian siempre "
            "juntas — en ese caso no conviene, porque el costo es el mismo y quedan mas piezas "
            "que mantener. Busca tambien texto repetido entre skills: eso se extrae a un "
            "documento aparte y baja el costo sin partir nada." + CIERRE))


def sonda_deuda():
    marcas = Counter()
    ejemplos = []
    fechas = fechas_git()
    viejos = []          # archivos con marcas que hace rato nadie toca
    # doctor/ documenta las marcas -⚠, TODO- como ejemplo de lo que cuenta esta
    # sonda: contarlas seria contar el texto que explica el conteo. Se saca ANTES de
    # elegir representante, igual que en wikilinks, para que un archivo de doctor/ no
    # represente a otro y se lleve puesta deuda real.
    revisables = [p for p in walk_md() if not rel(p).startswith("doctor/")]
    # Cada skill vive tres veces -la fuente y los dos espejos byte identicos- y la
    # misma marca de pendiente se contaba una vez por copia: el numero media cuantos
    # espejos tiene el proyecto, no cuanta deuda. Y ese numero alimenta un titular del
    # tablero, asi que la deuda se veia un tercio peor de lo que es.
    # Se agrupa por CONTENIDO, no por una lista de carpetas espejo: si una copia
    # DERIVA -deja de ser identica- vuelve a contarse sola, que es justo lo que hay
    # que ver. La dedup no puede tapar drift.
    revisables, copias = sin_copias(revisables)
    for p in revisables:
        r = rel(p)
        tiene_marca = False
        for linea in leer(p).splitlines():
            for marca in ["⚠", "TODO", "PENDIENTE", "pendiente de decision", "Pendiente de decisión"]:
                if marca in linea:
                    marcas[marca] += 1
                    tiene_marca = True
                    if len(ejemplos) < 30 and marca in ("TODO", "Pendiente de decisión"):
                        ejemplos.append([r, linea.strip()[:110]])
                    break
        if tiene_marca and r in fechas:
            m = meses_desde(fechas[r])
            if m is not None and m >= 3:
                viejos.append((r, fechas[r], m))
    viejos.sort(key=lambda x: -x[2])
    total = sum(marcas.values())
    filas = [[k, str(v), "", "OK"] for k, v in marcas.most_common()]
    for r, f, m in viejos[:12]:
        filas.append(["(sin tocar) " + r, "-", "ultimo cambio " + f + " · hace ~" + str(m) +
                      " mes(es)", "HALLAZGO"])
    return res("Deuda declarada", "OK" if total == 0 else "HALLAZGO",
        str(total) + " marca(s) de pendiente en la documentacion" +
        ("" if not copias else " (" + str(copias) + " archivo(s) son copia byte identica "
         "de otro -los espejos de skills- y se contaron una sola vez)") +
        ("." if not viejos else ", y " + str(len(viejos)) + " archivo(s) con pendientes que "
         "nadie toca hace 3 meses o mas.") +
        " No es un error: es deuda declarada a proposito. Lo que importa es que no crezca sin "
        "que nadie mire.",
        (["Marca", "Cantidad", "Detalle", "Estado"], filas),
        claves=["(sin tocar) " + r for r, _, _ in viejos],
        significa="Cuenta las marcas de pendiente que hay escritas en la documentacion: el simbolo "
                  "de advertencia, los TODO y las decisiones declaradas abiertas. Cada documento "
                  "cuenta UNA sola vez aunque viva copiado en los espejos de skills: si no, el "
                  "mismo pendiente figuraba tres veces y el numero media cuantos espejos hay, no "
                  "cuanta deuda. Ojo: se agrupa por contenido, asi que una copia que DERIVO deja "
                  "de ser copia y su deuda propia vuelve a contarse.",
        importa="Esto NO es una lista de errores. Deuda declarada es mucho mejor que deuda "
                "escondida: alguien se tomo el trabajo de dejar anotado lo que falta. El riesgo no "
                "es que exista, es que crezca sola y que nadie la vuelva a mirar.",
        acciones=[] if total == 0 else [
            {"paso": "Mira el reparto del grafico. Si una categoria crecio mucho desde la ultima "
                     "vez, empeza por esos archivos."},
            {"paso": "Por cada pendiente, elegi una de dos: cerrarlo, o reescribirlo diciendo DE "
                     "QUIEN depende y desde cuando. Un pendiente sin dueno no lo levanta nadie."},
            {"paso": "Los que esperan a otro equipo no son deuda tuya: marcalos como tales para "
                     "que no inflen el numero de lo que si podes resolver."}],
        pedido=None if total == 0 else (
            "En la documentacion de este repositorio hay " + str(total) + " marcas de pendiente, "
            "repartidas asi:\n\n" +
            "\n".join("- " + f[0] + ": " + f[1] for f in filas) +
            "\n\nRecorre los archivos .md y armame una lista de los pendientes AGRUPADA por "
            "quien los tiene que resolver: los que dependen de nosotros, los que esperan al "
            "equipo funcional, y los que dependen de infraestructura. Marca aparte los que ya no "
            "aplican porque el tema se resolvio y quedo la marca colgada. No hace falta que los "
            "enumeres todos: agrupalos por tema y decime cuantos hay en cada grupo." + CIERRE))


def sonda_gemelas():
    """Las skills duplicadas en back/ y front/: ¿divergieron en CONTENIDO?

    La sonda de asimetria mira si la skill EXISTE de los dos lados. Esta mira si
    dicen lo mismo. Son dos preguntas distintas y la segunda es la que muerde: ya
    paso que verificar-tdd del front perdiera un chequeo que el back si tenia, y
    desde afuera los dos repos parecian estar bien.

    No se comparan linea por linea, porque la diferencia legitima -adaptar el texto
    al stack de cada lado- ensucia ese numero. Se comparan los TITULOS de seccion:
    si un lado tiene una seccion que el otro no, alguien perdio algo."""
    a, b = espejo_de("back"), espejo_de("front")
    # Secciones que viven de UN SOLO lado a proposito, con su motivo escrito.
    # Sin esto la sonda marca como drift lo que en realidad es adaptacion al stack,
    # y una sonda que grita lobo es peor que no tenerla: la gente deja de leerla.
    # Se declaran aca, explicitas, porque una diferencia declarada es una decision y
    # una sin declarar es un descuido — y desde afuera se ven iguales.
    PROPIAS = {
        ("guiar-tdd", "back"): "Test de integración (si la Tarea lo pide)",
        ("guiar-tdd", "front"): "Qué se prueba en front (y qué NO)",
    }
    comunes = sorted(set(dirs_de(a)) & set(dirs_de(b)))
    if not comunes:
        return res("Gemelas: back vs. front", "SIN DATOS",
            "No hay ninguna skill que exista en los dos repositorios.",
            significa="Compara el contenido de las skills que viven en back/ Y en front/.",
            importa="SIN DATOS no es aprobado, pero aca es esperable mientras los repos de "
                    "codigo no tengan sus skills.")
    filas = []
    for s in comunes:
        ta = leer(a + "/" + s + "/SKILL.md")
        tb = leer(b + "/" + s + "/SKILL.md")
        sa = [l.strip() for l in ta.splitlines() if l.startswith("## ")]
        sb = [l.strip() for l in tb.splitlines() if l.startswith("## ")]
        prop_a = PROPIAS.get((s, "back"))
        prop_b = PROPIAS.get((s, "front"))
        solo_a = [x for x in sa if x not in sb and x[3:].strip() != prop_a]
        solo_b = [x for x in sb if x not in sa and x[3:].strip() != prop_b]
        declaradas = [x for x in (prop_a, prop_b) if x]
        dif_lineas = abs(len(ta.splitlines()) - len(tb.splitlines()))
        if solo_a or solo_b:
            detalle = []
            if solo_a:
                detalle.append("solo en back: " + "; ".join(x[3:] for x in solo_a))
            if solo_b:
                detalle.append("solo en front: " + "; ".join(x[3:] for x in solo_b))
            filas.append([s, str(len(sa)), str(len(sb)), " · ".join(detalle), "HALLAZGO"])
        else:
            det = ("mismas secciones" if not declaradas else
                   "coinciden, salvo " + str(len(declaradas)) + " seccion(es) declarada(s) "
                   "propia(s) de cada lado")
            if dif_lineas:
                det += " · " + str(dif_lineas) + " lineas de diferencia (adaptacion al stack)"
            filas.append([s, str(len(sa)), str(len(sb)), det, "OK"])
    malas = [f[0] for f in filas if f[4] == "HALLAZGO"]
    estado = "OK" if not malas else "HALLAZGO"
    return res("Gemelas: back vs. front", estado,
        str(len(comunes)) + " skill(s) viven en los dos repositorios. " +
        ("Todas tienen las mismas secciones." if not malas else
         "Divergieron en estructura: " + ", ".join(malas) + "."),
        (["Skill", "Secciones en back", "Secciones en front", "Detalle", "Estado"], filas),
        significa="Varias skills de desarrollo estan duplicadas, una copia en back/ y otra en "
                  "front/. Que el TEXTO difiera es normal y buscado -cada una se adapta a su "
                  "stack-. Lo que no es normal es que difiera la ESTRUCTURA: si un lado tiene "
                  "una seccion que el otro no, alguien perdio un chequeo por el camino.",
        importa="Es el drift mas caro de detectar a ojo, porque de cada lado todo parece estar "
                "bien: el defecto solo aparece cuando comparas. Ya paso una vez -verificar-tdd "
                "del front habia perdido el chequeo de codigo huerfano que el back si tenia-, y "
                "el resultado es que la misma regla se aplica en un repositorio y en el otro no.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada skill que divergio, abri las dos versiones y compara las secciones "
                     "que la tabla marca como 'solo en'."},
            {"paso": "Decidi si la seccion que falta de un lado tiene sentido ahi. Si la tiene, "
                     "copiala y adaptala al stack. Si no, DECLARALO en el SKILL.md del que no la "
                     "tiene, para que la proxima corrida no lo vuelva a marcar."},
            {"paso": "Si la diferencia salio de un arreglo que solo se aplico de un lado, revisa "
                     "si el otro lado necesita el mismo arreglo. Suele ser que si."}],
        pedido=None if estado == "OK" else (
            "En este repositorio hay skills duplicadas en back/.claude/skills/ y "
            "front/.claude/skills/, y estas divergieron en estructura:\n\n" +
            "\n".join("- " + f[0] + ": " + f[3] for f in filas if f[4] == "HALLAZGO") +
            "\n\nAbri las dos versiones de cada una y decime, por cada seccion que esta de un "
            "solo lado: si tiene sentido en el otro repositorio -adaptada al stack- o si es "
            "genuinamente de un lado solo. Fijate especialmente si la diferencia salio de un "
            "arreglo que se aplico en un lado y se olvido en el otro." + CIERRE))


def sonda_andamiaje():
    """Restos de la etapa de armado que ya no hacen falta."""
    filas = []
    for ruta in git("ls-files").splitlines():
        ruta = ruta.strip()
        if not ruta.endswith(".gitkeep"):
            continue
        carpeta = os.path.dirname(ruta)
        hermanos = [l for l in git("ls-files", carpeta).splitlines()
                    if l.strip() and not l.strip().endswith(".gitkeep")]
        if hermanos:
            filas.append([ruta, str(len(hermanos)) + " archivo(s) en la carpeta",
                          "ya no hace falta: la carpeta tiene contenido", "HALLAZGO"])
        else:
            filas.append([ruta, "carpeta vacia", "cumple su funcion: reserva el lugar", "OK"])
    estado = "HALLAZGO" if any(f[3] == "HALLAZGO" for f in filas) else "OK"
    sobran = [f[0] for f in filas if f[3] == "HALLAZGO"]
    return res("Andamiaje obsoleto", estado,
        ("No hay archivos .gitkeep en el repositorio." if not filas else
         str(len(filas)) + " archivo(s) .gitkeep" +
         ("; todos siguen haciendo falta." if not sobran else
          "; " + str(len(sobran)) + " ya no hace(n) falta.")),
        (["Archivo", "Estado de la carpeta", "Detalle", "Estado"], filas) if filas else None,
        significa="Un archivo .gitkeep existe para que git versione una carpeta vacia. En cuanto "
                  "la carpeta tiene contenido real, deja de cumplir ninguna funcion.",
        importa="No rompe nada: es ruido. Pero es la clase de resto que se acumula y despues "
                "nadie se anima a tocar porque no sabe si hace falta. Dejarlo declarado y "
                "medido evita esa duda.",
        acciones=[] if estado == "OK" else [
            {"paso": "Borra los .gitkeep de carpetas que ya tienen archivos. No afecta a nadie: "
                     "la carpeta se versiona igual por su contenido.",
             "comando": "git rm " + " ".join(sobran[:5])}],
        pedido=None if estado == "OK" else (
            "En este repositorio hay archivos .gitkeep que ya no cumplen ninguna funcion, "
            "porque su carpeta tiene contenido real:\n\n" +
            "\n".join("- " + f[0] + " (" + f[1] + ")" for f in filas if f[3] == "HALLAZGO") +
            "\n\nConfirmame que cada una de esas carpetas efectivamente tiene archivos "
            "versionados y proponeme el comando para borrar los .gitkeep que sobran. Si "
            "alguno hace falta por otro motivo que no sea reservar una carpeta vacia, "
            "decimelo en vez de borrarlo." + CIERRE))


def skills_externas_declaradas():
    """Las skills que el repositorio declara EXTERNAS, en su propio manifiesto.

    De donde sale. DEPENDENCIAS-EXTERNAS.md, en la raiz: la tabla que enumera las
    skills declaradas EXTERNAS -de terceros, que no se copian al disco: se leen de
    su origen en el momento de usarlas y se descartan- junto con el hash de arbol
    contra el que se las verifico.

    Se toman SOLO las filas que traen ese hash de 40 caracteres. El hash es el
    ancla de la auditoria: exigirlo evita que cualquier fila con un nombre entre
    comillas invertidas -y hay varias tablas en ese archivo- funcione como
    exencion.

    Por que no una lista clavada en el Doctor. Silenciar por nombre de archivo
    taparia una rotura real el dia que alguien escriba mal una ruta local. Asi la
    exencion la declara el repositorio, en un documento que un humano mantiene y
    que una auditoria puede leer; el Doctor solo la respeta.

    Si el manifiesto no esta o cambio de forma, esto devuelve un conjunto vacio y
    esas rutas vuelven a reportarse. El default es avisar, no callar."""
    p = ROOT + "/DEPENDENCIAS-EXTERNAS.md"
    if not es_archivo(p):
        return set()
    fila = re.compile(r"^\|\s*`([A-Za-z0-9][A-Za-z0-9._\-]*)`\s*\|.*\|\s*`[0-9a-f]{40}`\s*\|\s*$")
    return set(m.group(1) for m in
               (fila.match(l) for l in leer(p).splitlines()) if m)


def skills_vendidas_declaradas():
    """Las skills que el repositorio declara VENDORIZADAS en DEPENDENCIAS-EXTERNAS.md: de
    terceros, copiadas al disco y que no se editan. Se toman SOLO las filas de la forma
    | `nombre` | origen | version | `hash` | que-no-viaja |  (hash hex de 16 o mas, en la 4ta
    columna; las EXTERNAS llevan el hash de 40 al final, asi una fila no vale por las dos).
    Sus rutas internas y sus [[...]] no se reportan: lo que les falta se quito a proposito
    (columna «Que no viaja») y lo que vigila que no queden viejas es el detector de deriva.
    Sin manifiesto, conjunto vacio: el default es avisar, no callar."""
    p = ROOT + "/DEPENDENCIAS-EXTERNAS.md"
    if not es_archivo(p):
        return set()
    fila = re.compile(r"^\|\s*`([A-Za-z0-9][A-Za-z0-9._\-]*)`\s*\|[^|]*\|[^|]*\|\s*`[0-9a-f]{16,}`\s*\|[^|]*\|\s*$")
    return set(m.group(1) for m in (fila.match(l) for l in leer(p).splitlines()) if m)


def es_de_skill_vendida(ruta_rel, vendidas):
    partes = ruta_rel.replace("\\", "/").split("/")
    return any(partes[i] == "skills" and partes[i + 1] in vendidas for i in range(len(partes) - 1))


def sonda_referencias():
    """Rutas de archivo que las skills nombran y que no existen.

    Distinta de la sonda de wikilinks: aquella mira enlaces [[asi]] entre documentos;
    esta mira RUTAS DE ARCHIVO citadas adentro del texto -un openapi.yaml, un .json
    de configuracion-. Una skill que manda a un archivo inexistente hace perder tiempo
    al que la sigue."""
    fuentes = []
    for raiz in raices_de_skills():
        for s in dirs_de(raiz):
            p = raiz + "/" + s + "/SKILL.md"
            if es_archivo(p):
                fuentes.append(p)
    if not fuentes:
        return res("Referencias a archivos", "SIN DATOS", "No se encontraron skills que revisar.",
                   significa="Revisa las rutas de archivo que las skills citan en su texto.",
                   importa="SIN DATOS no es aprobado: este aspecto quedo sin revisar.")

    # Rutas con extension y con barra: un "config.json" suelto es casi siempre un
    # ejemplo generico, no una ruta real del repositorio.
    # El primer caracter tiene que ser alfanumerico: sin esa restriccion, un inciso
    # como "-doctor/bin/doctor.sh-" se captura CON el guion pegado y la ruta nunca
    # resuelve. Paso de verdad, y produjo un hallazgo falso.
    patron = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*(?:/[A-Za-z0-9_.\-]+)+\.(?:yaml|yml|json|xml|md|py|sh|ps1|ts|js)")
    GENERICAS = ("ruta/", "path/", "<", "ejemplo", "nombre-", "tu-", "mi-", "...", "nnnn")

    # Un enlace markdown tiene DOS partes y solo una es una referencia: el destino.
    # La etiqueta es texto para leer. Cuando la etiqueta ademas tiene pinta de ruta
    #     [externas/como-se-delega.md](references/externas/como-se-delega.md)
    # el escaneo crudo capturaba las dos, y la etiqueta -que no resuelve desde
    # ningun lado, ni tiene por que- se reportaba como archivo faltante. Siete
    # hallazgos falsos salian de esto, todos del mismo documento, y el informe
    # anunciaba que el proyecto habia empeorado despues de un merge.
    # Se resuelve el enlace a su destino ANTES de buscar rutas: se valida adonde
    # lleva, no como se lee.
    ENLACE_MD = re.compile(r"!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?[^)\n]*\)")

    def destinos(texto):
        """El texto con cada enlace markdown reducido a su destino."""
        return ENLACE_MD.sub(lambda m: " " + m.group(1) + " ", texto)

    # Las skills declaradas EXTERNAS en DEPENDENCIAS-EXTERNAS.md no estan en disco A
    # PROPOSITO: son de terceros, se leen de su origen en el momento de usarlas y se
    # descartan. Sus rutas -skills/<skill>/...- son del repositorio REMOTO, asi que
    # pedirle al disco que las tenga es pedir algo que el proyecto decidio no hacer.
    # No se silencian por nombre de archivo: eso taparia una rotura de verdad el dia
    # que alguien escriba mal una ruta local. Se exige que el propio repositorio las
    # declare externas en su manifiesto, y aun asi NO se dan por buenas: van a la
    # tabla como SIN DATOS, porque el Doctor no puede verificar el origen remoto.
    # Quien verifica eso es el detector de deriva del manifiesto, no esta sonda.
    externas = skills_externas_declaradas()
    vendidas = skills_vendidas_declaradas()
    # Las VENDORIZADAS se saltean enteras como fuente: citan sus propios archivos, y lo que
    # no esta se quito a proposito (DEPENDENCIAS-EXTERNAS.md, columna «Que no viaja»).
    salteadas = [p for p in fuentes if es_de_skill_vendida(rel(p), vendidas)]
    fuentes = [p for p in fuentes if p not in salteadas]

    def es_externa(ruta):
        partes = ruta.split("/")
        return len(partes) >= 3 and partes[0] == "skills" and partes[1] in externas

    # Una ruta puede estar escrita relativa a varias bases, y todas son legitimas:
    # a la raiz del repo, al Cerebro -que es como lo escribe medio Cerebro-, a cada
    # modulo del Cerebro, a la carpeta de Azure o a la carpeta de la propia skill.
    # Probar SOLO la raiz produce falsos positivos en masa: la primera version de esta
    # sonda marco 7 rutas rotas y 6 eran esto. Una sonda que grita lobo es peor que no
    # tenerla, porque la gente deja de leer el informe.
    # Los modulos del Cerebro NO se clavan por nombre: son sus subcarpetas de primer
    # nivel y se leen del disco, asi un modulo nuevo entra solo sin tocar el Doctor.
    CEREBRO = "cerebro-digital"
    BASES = (["", CEREBRO, "tablero"] +
             [CEREBRO + "/" + d for d in dirs_de(ROOT + "/" + CEREBRO)])

    def resuelve(ruta, desde):
        # existe() y no os.path.exists(): en un clone hondo, el limite de 260
        # caracteres de Windows devuelve False sobre archivos sanos y esta sonda
        # sale a decir que el proyecto esta roto. Ver largo(), arriba.
        for b in BASES + [os.path.dirname(rel(desde))]:
            if existe(os.path.join(ROOT, b, ruta)):
                return True
        return False

    vistas, filas, sin_verificar = set(), [], []
    for p in fuentes:
        for m in patron.findall(destinos(leer(p))):
            if m in vistas or any(g in m.lower() for g in GENERICAS):
                continue
            vistas.add(m)
            if resuelve(m, p):
                continue
            if es_externa(m):
                sin_verificar.append([rel(p), m,
                    "declarada externa en DEPENDENCIAS-EXTERNAS.md: es de terceros y "
                    "no se copia al disco", "SIN DATOS"])
                continue
            filas.append([rel(p), m, "no resuelve desde ninguna base conocida", "HALLAZGO"])
    rotas = len(filas)
    claves = [f[0] + " | " + f[1] for f in filas]   # una skill puede tener varias rutas rotas
    filas = filas + sin_verificar
    estado = "OK" if not rotas else "HALLAZGO"
    return res("Referencias a archivos", estado,
        str(len(vistas)) + " ruta(s) citadas en " + str(len(fuentes)) + " skills. " +
        ("Todas resuelven." if not rotas else str(rotas) + " no existen.") +
        ("" if not sin_verificar else " " + str(len(sin_verificar)) + " son de skills "
         "declaradas externas en DEPENDENCIAS-EXTERNAS.md -de terceros- y quedan SIN DATOS: "
         "no estan en disco a proposito y esta sonda no puede verificar su origen.") +
        ("" if not salteadas else " No se miraron " + str(len(salteadas)) + " SKILL.md de skills "
         "vendorizadas (" + ", ".join(sorted(set(rel(p).split("/skills/")[1].split("/")[0] for p in salteadas))) + "): "
         "son de terceros, declaradas en DEPENDENCIAS-EXTERNAS.md, y las vigila el detector de deriva."),
        (["Skill", "Ruta citada", "Detalle", "Estado"], filas) if filas else None,
        claves=claves,
        significa="Las skills citan rutas de archivo en su texto -un contrato, un script, un "
                  "documento-. Esta sonda verifica que cada una exista de verdad. De un enlace "
                  "markdown mira el DESTINO, no la etiqueta: la etiqueta es texto para leer.",
        importa="Una skill que manda a un archivo inexistente hace perder tiempo al que la sigue, "
                "y peor: lo deja dudando de si el problema es el archivo o su propia maquina.",
        acciones=[] if estado == "OK" else [
            {"paso": "Por cada ruta, fijate si el archivo se movio -buscalo por nombre- o si "
                     "todavia no existe porque es trabajo pendiente."},
            {"paso": "Si es trabajo pendiente, dejalo escrito EN la skill como pendiente, para "
                     "que quien la lea sepa que todavia no esta."}],
        pedido=None if estado == "OK" else (
            "Estas skills citan rutas de archivo que no existen en el repositorio:\n\n" +
            # Solo las ROTAS. Las declaradas externas estan en la tabla como SIN
            # DATOS, y meterlas aca mandaria a buscar en disco algo que por
            # decision del proyecto no esta ni va a estar.
            "\n".join("- " + f[0] + " cita: " + f[1]
                      for f in [x for x in filas if x[3] == "HALLAZGO"][:30]) +
            "\n\nPor cada una, busca si el archivo existe con otro nombre o en otra carpeta, y "
            "decime si es que se movio o si es trabajo que todavia no se hizo." + CIERRE))


def sonda_tendencia(previas=None, sufijo=""):
    """Como venimos: si los hallazgos suben o bajan respecto de la corrida anterior.

    Por que hace falta. El informe dice "223 marcas de deuda" y eso, solo, no decide
    nada: no se sabe si la semana pasada eran 180 o 260. Un numero aislado no dice si
    vamos bien; la DIRECCION si. Es la diferencia entre una foto y un signo vital.

    De donde sale. Del historico que ya se guardaba y que nadie leia: cada corrida
    completa deja un JSON con el veredicto y la cantidad de filas de cada sonda. Aca
    se compara lo de ESTA corrida contra lo de la anterior — que al momento de correr
    esta sonda todavia esta en ultimo.json, porque la rotacion pasa despues.

    Lo que NO es. No mide el proyecto: mide el informe. Por eso no puede reemplazar a
    ninguna sonda, y por eso una tendencia que baja no significa que este todo bien —
    significa que hoy hay menos que ayer.
    """
    if not previas:
        return res("Como venimos", "SIN DATOS", "No hubo sondas previas que comparar.",
                   significa="Compara esta corrida con la anterior.",
                   importa="SIN DATOS no es aprobado: la tendencia quedo sin calcular.")

    historico = ROOT + "/doctor/salida/historico"
    anterior = historico + "/ultimo" + sufijo + ".json"
    if not es_archivo(anterior):
        return res("Como venimos", "SIN DATOS",
            "Esta es la primera corrida guardada de este alcance: todavia no hay con "
            "que comparar.",
            significa="Compara los hallazgos de esta corrida con los de la anterior, "
                      "para mostrar si suben o bajan. El historico se guarda solo, en "
                      "cada corrida completa.",
            importa="SIN DATOS no es aprobado, pero aca es esperable: hace falta una "
                    "segunda corrida. A partir de la proxima, esta sonda mide sola.",
            acciones=[{"paso": "Volve a correr el Doctor despues de trabajar un rato. "
                               "La comparacion aparece sola.",
                       "comando": "bash doctor/bin/doctor.sh"}])

    try:
        viejo = json.loads(leer(anterior))
    except Exception as e:
        return res("Como venimos", "SIN DATOS",
            "No se pudo leer la corrida anterior: " + str(e),
            significa="Compara esta corrida con la anterior, que vive en el historico.",
            importa="SIN DATOS no es aprobado: la tendencia quedo sin calcular.",
            acciones=[{"paso": "Si el archivo quedo corrupto, borralo: se regenera solo "
                               "en la proxima corrida.",
                       "comando": "rm " + rel(anterior)}])

    # UNA SOLA implementacion de la comparacion, la de comparar.py. La primera version
    # de esta sonda tenia la suya propia, y eran dos formas de contestar la misma
    # pregunta sobre los mismos datos: podian separarse y decir cosas distintas sin
    # que nada avisara. Es el defecto que este proyecto viene pisando -una regla con
    # dos duenos- y no habia motivo para repetirlo aca.
    #
    # Lo que cambia entre las dos vistas es CUANDO se mira, no como se calcula:
    #   este panel        -> "¿como venimos?", en cada corrida, adentro del informe
    #   reporte de arreglos -> "¿sirvio lo que acabo de tocar?", con --comparar
    import comparar as _cmp                                                # noqa

    # Quien queda afuera de la comparacion -las sondas que miran el informe- lo
    # decide comparar.py, no este panel: si cada vista lo resolviera por su cuenta
    # volveriamos a tener dos numeros distintos sobre los mismos datos.
    actual = {"sondas": [{"id": d["id"], "titulo": d["titulo"], "estado": d["estado"],
                          "resumen": d.get("resumen", ""),
                          "filas": len(d["tabla"][1]) if d.get("tabla") else 0,
                          "claves": _cmp.claves_de(d)}
                         for d in previas]}
    cuenta, comparadas = _cmp.comparar(viejo, actual)

    DETALLE = {
        "arreglado": "mejoro",
        "empeoro": "EMPEORO",
        "igual": "sin cambios",
        "nuevo": "sonda nueva: todavia no tiene con que compararse",
        "ya no esta": "no corrio en esta corrida",
    }
    ESTADO = {"arreglado": "OK", "igual": "OK", "empeoro": "HALLAZGO",
              "nuevo": "SIN DATOS", "ya no esta": "SIN DATOS"}

    filas, empeoraron = [], []
    for f in comparadas:
        v = f["veredicto"]
        detalle = DETALLE.get(v, v)
        if v in ("arreglado", "empeoro"):
            d_filas = f["filas_ahora"] - f["filas_antes"]
            if d_filas:
                detalle += ": " + str(abs(d_filas)) + " fila(s) " + \
                           ("mas" if d_filas > 0 else "menos")
            elif f["antes"] != f["ahora"]:
                detalle += ": paso de " + f["antes"] + " a " + f["ahora"]
        if v == "empeoro":
            empeoraron.append(f["titulo"])
        # Antes y Ahora son SIEMPRE numeros de fila. Poner un veredicto ahi mezcla dos
        # unidades en la misma columna, y el grafico -que la lee como numerica- dibuja
        # ceros donde habia texto. El cambio de veredicto se cuenta en el detalle.
        filas.append([f["titulo"],
                      "-" if v == "nuevo" else str(f["filas_antes"]),
                      "-" if v == "ya no esta" else str(f["filas_ahora"]),
                      detalle, ESTADO.get(v, "SIN DATOS")])

    estado = "HALLAZGO" if empeoraron else "OK"
    corridas = len([f for f in listar(historico)
                    if f.startswith("reporte-") and f.endswith(sufijo + ".json")]) \
        if es_dir(historico) else 0
    resumen = ("Contra la corrida del " + str(viejo.get("fecha", "?")) + ". " +
               str(cuenta.get("arreglado", 0)) + " mejoraron · " +
               str(cuenta.get("empeoro", 0)) + " empeoraron · " +
               str(cuenta.get("igual", 0)) + " sin cambios.")
    if empeoraron:
        resumen += " Empeoraron: " + ", ".join(empeoraron[:4]) + "."

    return res("Como venimos", estado, resumen,
        (["Sonda", "Antes", "Ahora", "Que paso", "Estado"], filas),
        significa="Compara esta corrida con la anterior y dice, sonda por sonda, si los "
                  "hallazgos subieron o bajaron. Sale del historico que el Doctor ya "
                  "venia guardando en cada corrida completa: hay " + str(corridas) +
                  " guardada(s) de este alcance. La comparacion la hace comparar.py, el "
                  "MISMO codigo que arma el reporte de arreglos, para que las dos vistas "
                  "no puedan decir cosas distintas sobre los mismos datos.",
        importa="Un numero solo no decide nada: que haya 223 marcas de deuda no dice si "
                "vamos bien o mal, porque no se sabe si la semana pasada eran 180 o "
                "260. La DIRECCION si lo dice. Es lo que convierte al informe de una "
                "foto en un signo vital.\n\n"
                "Este panel y el reporte de arreglos contestan preguntas distintas en "
                "momentos distintos: este, «¿como venimos?», en cada corrida; aquel, "
                "«¿sirvio lo que acabo de tocar?», despues de arreglar algo.\n\n"
                "Ojo con lo que NO significa: esta sonda mide el informe, no el "
                "proyecto. Que todo baje no quiere decir que este bien — quiere decir "
                "que hoy hay menos que ayer. Y el historico es de CADA MAQUINA: la "
                "tendencia que ves es la tuya, no la del equipo.",
        acciones=[] if estado == "OK" else [
            {"paso": "Mira primero las que cambiaron de veredicto, no las que sumaron "
                     "filas: pasar de OK a hallazgo suele ser algo que se rompio recien, "
                     "y es lo mas barato de arreglar."},
            {"paso": "Por cada una que empeoro, abri su panel en este mismo informe: "
                     "ahi estan las filas nuevas y el pedido para atacarlas."},
            {"paso": "Si empeoro por un cambio que hiciste a proposito, no hay nada que "
                     "arreglar. Esta sonda avisa, no juzga."}],
        pedido=None if estado == "OK" else (
            "Desde la corrida del " + str(viejo.get("fecha", "?")) +
            ", estas sondas del Doctor empeoraron:\n\n" +
            "\n".join("- " + f[0] + ": " + f[1] + " -> " + f[2] + " (" + f[3] + ")"
                      for f in filas if f[4] == "HALLAZGO") +
            "\n\nMira el git log de ese periodo y decime que cambio pudo haberlas "
            "empeorado. Para cada una, distingui si es un problema nuevo que hay que "
            "arreglar o una consecuencia esperable de algo que se hizo a proposito — "
            "por ejemplo, agregar documentacion sube la deuda declarada y eso no es "
            "malo." + CIERRE))


def sonda_autocontrol(previas=None):
    """Revisa el informe a si mismo. Corre ULTIMA y mira lo que produjeron las otras."""
    if not previas:
        return res("Autocontrol del informe", "SIN DATOS",
                   "No hubo sondas previas que revisar.")
    filas = []

    def chequeo(nombre, ok, detalle):
        filas.append([nombre, "si" if ok else "NO", detalle, "OK" if ok else "HALLAZGO"])

    for d in previas:
        sid = d["id"]
        tabla = d.get("tabla")
        cols, fs = (tabla if tabla else ([], []))

        # (a) Una sonda en OK no puede tener filas en HALLAZGO. Si las tiene,
        #     el veredicto miente y alguien va a pasar de largo un problema real.
        if cols and "Estado" in cols:
            i = list(cols).index("Estado")
            con_hallazgo = [f for f in fs if len(f) > i and f[i] == "HALLAZGO"]
            chequeo(sid + ": veredicto vs. filas",
                    not (d["estado"] == "OK" and con_hallazgo),
                    "OK con " + str(len(con_hallazgo)) + " fila(s) en hallazgo"
                    if (d["estado"] == "OK" and con_hallazgo) else "coherente")

        # (b) Una sonda en HALLAZGO tiene que decir que hacer. Reportar un
        #     problema sin salida deja al lector igual que antes de leerlo.
        if d["estado"] == "HALLAZGO":
            chequeo(sid + ": hallazgo con pasos", bool(d.get("acciones")),
                    "sin pasos que seguir" if not d.get("acciones") else
                    str(len(d["acciones"])) + " paso(s)")

        # (b2) Y tiene que traer el texto para copiarle a un asistente. El README
        #      lo promete para TODA sonda con hallazgo, y esa promesa no tenia
        #      control: una sonda se habia quedado sin el y nadie se entero. Un
        #      control que no deja evidencia no es un control, y una promesa que
        #      nadie verifica se vuelve mentira sola.
        if d["estado"] == "HALLAZGO":
            chequeo(sid + ": hallazgo con pedido", bool(d.get("pedido")),
                    "sin texto para copiarle a la inteligencia artificial"
                    if not d.get("pedido") else "pedido presente")

        # (c) Toda sonda tiene que explicarse. Sin esto vuelve a ser un numero suelto.
        chequeo(sid + ": explicada", bool(d.get("significa") and d.get("importa")),
                "falta significa/importa" if not (d.get("significa") and d.get("importa"))
                else "significa e importa presentes")

        # (d) Filas con distinta cantidad de columnas que el encabezado: el
        #     informe las dibuja corridas y el dato se lee mal.
        if cols and fs:
            malas = [k for k, f in enumerate(fs) if len(f) != len(cols)]
            chequeo(sid + ": filas completas", not malas,
                    "fila(s) " + str(malas[:5]) + " con distinto largo" if malas
                    else str(len(fs)) + " filas de " + str(len(cols)) + " columnas")

    malos = [f for f in filas if f[3] == "HALLAZGO"]
    estado = "OK" if not malos else "HALLAZGO"
    return res("Autocontrol del informe", estado,
        str(len(filas)) + " chequeos de coherencia sobre las otras sondas. " +
        ("todos pasan." if not malos else str(len(malos)) + " fallan."),
        (["Chequeo", "Pasa", "Detalle", "Estado"], filas),
        significa="El Doctor se revisa a si mismo: que ninguna sonda diga OK teniendo filas en "
                  "hallazgo, que toda sonda con hallazgo diga que hacer, que todas se expliquen, y "
                  "que ninguna tabla tenga filas corridas respecto de su encabezado.",
        importa="Un informe con un dato mal es peor que no tener informe: se actua sobre el. Pero "
                "ojo con que esto promete: el Doctor revisandose a si mismo detecta errores de "
                "COHERENCIA -que el veredicto no coincida con las filas, que falte una explicacion-. "
                "NO detecta que una sonda MIDA MAL, porque para eso usaria el mismo codigo que "
                "produjo el error. Ese segundo chequeo lo tiene que hacer alguien distinto, igual "
                "que en las tarjetas: el que produce nunca es el que aprueba.",
        acciones=[] if estado == "OK" else [
            {"paso": "Un fallo aca es un bug del Doctor, no del proyecto. Mira la fila que falla: "
                     "dice que sonda y que chequeo."},
            {"paso": "Arreglalo en doctor/doctor.py, en la sonda que se nombra, antes de confiar "
                     "en el resto del informe."}],
        pedido=None if estado == "OK" else (
            "El autocontrol del Doctor esta fallando. Esto es un bug del Doctor mismo, no un "
            "problema del proyecto: quiere decir que el informe se contradice.\n\n" +
            "\n".join("- " + f[0] + ": " + f[2] for f in filas if f[3] == "HALLAZGO") +
            "\n\nAbri doctor/doctor.py, busca la sonda que se nombra en cada linea y decime por "
            "que produce ese resultado incoherente. Arreglalo en la sonda, no en el autocontrol: "
            "el autocontrol esta haciendo bien su trabajo al marcarlo." + CIERRE))


SONDAS = [sonda_guardarrailes, sonda_espejos, sonda_conteos, sonda_referencias,
          sonda_wikilinks, sonda_estructura, sonda_asimetria, sonda_gemelas,
          sonda_andamiaje, sonda_tamano, sonda_deuda]

# ------------------------------------------------------------------------ informe

def correr(solo=None):
    """Devuelve una lista de diccionarios, uno por sonda (ver res()).

    El id es estable y sale del NOMBRE DE LA FUNCION, no del titulo: el informe
    engancha los graficos por id, asi que si alguien reescribe un titulo el grafico
    no se tiene que caer."""
    # Las sondas de codigo viven en codigo.py y se enganchan aca. No importan nada de
    # este modulo -no habria forma sin un ciclo-: se les pasa lo que necesitan, en una
    # sola linea y en un solo lugar. Y se les pasa ACA y no al importar, porque ALCANCE
    # recien tiene su valor definitivo despues de leer los argumentos.
    import codigo                                                          # noqa
    codigo.CTX = {"root": ROOT, "alcance": ALCANCE, "res": res, "leer": leer,
                  "rel": rel, "git": git, "cierre": CIERRE}
    con_codigo = codigo.hay_codigo()

    salida = []
    for f in SONDAS + codigo.SONDAS:
        nombre = f.__name__.replace("sonda_", "")
        if solo and nombre not in solo:
            continue
        if ALCANCE and nombre in SOLO_PROYECTO:
            continue
        # Sin codigo clonado, nueve de las diez sondas de codigo no tienen nada que
        # medir. Se saltean en vez de emitir nueve paneles identicos: la que explica
        # por que -repos- si corre, y las nombra una por una.
        if not con_codigo and nombre in codigo.SOLO_CON_CODIGO:
            # Salvo que la hayan pedido por nombre. Ahi el silencio es peor que el
            # panel repetido: alguien escribio `--solo limites`, no vio nada y no
            # tiene forma de saber si la sonda no encontro problemas o ni corrio.
            if solo:
                salida.append(dict(codigo.sin_codigo(
                    "Sonda de codigo pedida: " + nombre,
                    "Se la pidio por nombre con --solo."), id=nombre))
            continue
        try:
            d = f()
        except Exception as e:
            # Una sonda que explota no puede tumbar el informe entero: se reporta
            # como SIN DATOS, que es exactamente lo que es — no se pudo medir.
            d = res(nombre, "SIN DATOS", "La sonda fallo: " + str(e),
                    significa="Esta sonda no se pudo ejecutar.",
                    importa="SIN DATOS no es aprobado: quiere decir que este aspecto quedo sin "
                            "revisar, no que este bien.",
                    acciones=[{"paso": "Corre la sonda sola para ver el error completo.",
                               "comando": "bash doctor/bin/doctor.sh --solo " + nombre}])
        d["id"] = nombre
        salida.append(d)

    # La tendencia va antes del autocontrol -que asi tambien la revisa a ella- y solo
    # en corridas COMPLETAS: con --solo se compararian dos sondas contra todas y todas
    # las demas figurarian como desaparecidas. Es el mismo motivo por el que una
    # corrida parcial tampoco toca el historico.
    if not solo:
        sufijo = ("-" + ALCANCE.replace("/", "-").replace("\\", "-")) if ALCANCE else ""
        tend = sonda_tendencia(salida, sufijo)
        tend["id"] = "tendencia"
        salida.append(tend)

    # El autocontrol corre SIEMPRE y al final: necesita ver lo que produjeron las demas.
    # No se puede saltear con --solo, justamente porque es el que avisa si el informe miente.
    auto = sonda_autocontrol(salida)
    auto["id"] = "autocontrol"
    salida.append(auto)
    return salida


def _valor_de(args, bandera):
    """El valor que sigue a una bandera, o None si no vino.

    Existe porque `args[args.index(x) + 1]` revienta con un IndexError crudo cuando
    la bandera es el ultimo argumento. Un traceback de Python no le dice nada a
    quien se olvido de escribir el nombre de la sonda."""
    i = args.index(bandera)
    if i + 1 >= len(args) or args[i + 1].startswith("--"):
        return None
    return args[i + 1]


def _serie(historico, sufijo, resultados, hoy, parcial):
    """Las corridas guardadas, contadas por estado, para la tendencia del tablero.

    Sale del MISMO historico que alimenta a --comparar, no de una medicion nueva.
    La corrida de ahora pisa la del dia: dos corridas el mismo dia son una sola
    foto, igual que en el historico.
    """
    def contar(sondas):
        c = {"ok": 0, "hal": 0, "sd": 0}
        for s in sondas:
            e = s.get("estado") if isinstance(s, dict) else None
            if e == "OK":
                c["ok"] += 1
            elif e == "HALLAZGO":
                c["hal"] += 1
            elif e == "SIN DATOS":
                c["sd"] += 1
        return c

    por_fecha = {}
    if es_dir(historico):
        for nombre in listar(historico):
            if not (nombre.startswith("reporte-") and nombre.endswith(".json")):
                continue
            resto = nombre[len("reporte-"):-len(".json")]
            fecha, cola = resto[:10], resto[10:]
            # El sufijo del alcance tiene que coincidir EXACTO: mezclar la corrida
            # del proyecto con la de un repo daria una tendencia que no significa
            # nada -son universos de sondas distintos-.
            if cola != sufijo or len(fecha) != 10:
                continue
            try:
                d = json.load(abrir(os.path.join(historico, nombre)))
            except Exception:
                continue
            por_fecha[fecha] = contar(d.get("sondas", []))

    # Una corrida PARCIAL no entra a la tendencia, por el mismo motivo por el que no
    # entra al historico: `--solo espejos` mide dos sondas, y dibujada como un punto
    # mas se lee como si el proyecto se hubiera desplomado de catorce sondas a dos.
    # La tendencia queda con lo ultimo COMPLETO, que es lo unico comparable.
    if not parcial:
        por_fecha[hoy] = contar([{"estado": r["estado"]} for r in resultados])

    def orden(f):
        p = f.split("-")
        return (p[2], p[1], p[0]) if len(p) == 3 else ("", "", f)

    salida = []
    for f in sorted(por_fecha, key=orden)[-12:]:
        fila = {"fecha": f}
        fila.update(por_fecha[f])
        salida.append(fila)
    return salida


def main():
    args = [a for a in sys.argv[1:]]
    solo = None
    if "--solo" in args:
        import codigo as _cod                                              # noqa
        validos = ([f.__name__.replace("sonda_", "") for f in SONDAS] +
                   [f.__name__.replace("sonda_", "") for f in _cod.SONDAS])
        crudo_solo = _valor_de(args, "--solo")
        if not crudo_solo:
            print("doctor: --solo necesita el nombre de al menos una sonda.")
            print("        Sondas validas: " + ", ".join(validos))
            return 2
        solo = [s.strip() for s in crudo_solo.split(",") if s.strip()]
        # Un nombre mal escrito producia un informe VACIO con exit 0 y sin un solo
        # mensaje. Eso se lee como "no hay nada que corregir", que es lo contrario
        # de lo que paso: no se midio nada.
        malos = [s for s in solo if s not in validos]
        if malos:
            print("doctor: no existe(n) la(s) sonda(s): " + ", ".join(malos))
            print("        Sondas validas: " + ", ".join(validos))
            return 2
    if "--repo" in args:
        pedido = (_valor_de(args, "--repo") or "").strip("/\\")
        # Se acepta CUALQUIER carpeta del repositorio, no una lista fija. Hoy los
        # repos de codigo son back/ y front/, pero manana pueden ser otros o mas de
        # dos: clavar los nombres obligaria a tocar el Doctor cada vez que aparezca
        # uno nuevo, que es justo el acoplamiento que este proyecto evita.
        if not pedido or not es_dir(ROOT + "/" + pedido):
            candidatas = [d for d in dirs_de(ROOT) if not d.startswith(".")]
            print("doctor: no existe la carpeta '" + pedido + "/' en este repositorio.")
            print("        Carpetas disponibles: " + ", ".join(candidatas))
            return 2
        globals()["ALCANCE"] = pedido
    comparar_tambien = "--comparar" in args
    formato_json = "--json" in args

    resultados = correr(solo)

    if formato_json:
        print(json.dumps([{"id": r["id"], "titulo": r["titulo"], "estado": r["estado"],
                           "resumen": r["resumen"], "acciones": len(r["acciones"])}
                          for r in resultados], ensure_ascii=False, indent=2))
        return 0

    salida = ROOT + "/doctor/salida"
    historico = salida + "/historico"
    for d in (salida, historico):
        if not es_dir(d):
            os.makedirs(largo(d))

    from plantilla import render          # noqa
    html = render(resultados, ROOT)

    # informe.html es SIEMPRE el ultimo: la ruta que uno pone en favoritos no cambia.
    # El alcance puede ser una carpeta anidada -apps/portal, equipo/web-, y esa
    # barra terminaba metida en el nombre del archivo: el informe se queria escribir
    # dentro de una subcarpeta que no existe y la corrida moria al final, despues de
    # haber medido todo. Se aplana aca, en el unico lugar donde el alcance se vuelve
    # un nombre de archivo.
    sufijo = ("-" + ALCANCE.replace("/", "-").replace("\\", "-")) if ALCANCE else ""
    destino = salida + "/informe" + sufijo + ".html"
    abrir(destino, "w").write(html)

    hoy = _hoy()

    # El tablero: el mismo resultado, resumido de un vistazo. Sale de `resultados`
    # y no vuelve a medir nada, para que no pueda decir algo distinto del informe.
    # No se copia al historico: la historia ya vive en el historico del informe, y
    # el tablero la lee de ahi para dibujar la tendencia.
    from plantilla import render_tablero     # noqa
    es_parcial = bool(solo)
    destino_tab = salida + "/tablero" + sufijo + ".html"
    abrir(destino_tab, "w").write(
        render_tablero(resultados, ROOT,
                       _serie(historico, sufijo, resultados, hoy, es_parcial),
                       ALCANCE, hoy, es_parcial))
    copia = None

    # Una corrida PARCIAL no entra al historico. Antes si entraba, y el efecto era
    # grave y silencioso: `--solo espejos` -que el propio README recomienda para
    # iterar rapido- pisaba el reporte del dia con dos sondas y rotaba ultimo.json,
    # con lo cual el `--comparar` siguiente comparaba todas las sondas contra dos y
    # anunciaba "0 empeoraron", que se lee como "nada empeoro". Falsa confianza, en
    # la herramienta cuyo unico trabajo es dar confianza. Y pegaba justo donde mas
    # duele, porque atender-hallazgos cierra su flujo con --comparar.
    #
    # El informe SI se escribe: para eso se usa --solo. Lo que no se toca es la
    # linea de base.
    parcial = bool(solo)
    if not parcial:
        # Una copia fechada, para tener la historia. Dos corridas del mismo dia
        # pisan la del dia: es a proposito, para que el historico sea una foto por
        # dia y no una pila de archivos casi iguales.
        copia = historico + "/reporte-" + hoy + sufijo + ".html"
        abrir(copia, "w").write(html)

        # El JSON de la misma corrida: es lo que hace posible comparar dos dias sin
        # tener que parsear HTML. Es el insumo de la tendencia, que todavia no existe.
        import comparar as _cmp_medidas  # noqa: la huella de cada fila, para comparar hallazgo por hallazgo
        medidas = {"fecha": hoy, "alcance": ALCANCE or "proyecto",
                   "sondas": [{"id": r["id"], "titulo": r["titulo"],
                               "estado": r["estado"], "resumen": r["resumen"],
                               "filas": len(r["tabla"][1]) if r.get("tabla") else 0,
                               "claves": _cmp_medidas.claves_de(r),
                               "acciones": len(r.get("acciones", []))} for r in resultados]}
        crudo = json.dumps(medidas, ensure_ascii=False, indent=2)
        abrir(historico + "/reporte-" + hoy + sufijo + ".json", "w").write(crudo)

        # Rotacion previo <- ultimo <- este. Es lo que permite comparar dos corridas
        # del MISMO dia: el archivo fechado se pisa -una foto por jornada, a
        # proposito- pero el par previo/ultimo conserva los dos ultimos estados.
        ult = historico + "/ultimo" + sufijo + ".json"
        if es_archivo(ult):
            abrir(historico + "/previo" + sufijo + ".json", "w").write(leer(ult))
        abrir(ult, "w").write(crudo)

        _indice(historico)

    print("Doctor de {{PROYECTO}}" + (" — solo " + ALCANCE + "/" if ALCANCE else ""))
    print("=" * 60)
    for r in resultados:
        marca = "  ->" + str(len(r["acciones"])) + " paso(s)" if r["acciones"] else ""
        print("  [" + r["estado"].ljust(9) + "] " + r["titulo"] + marca)
    con_datos = [r for r in resultados if r["estado"] != "SIN DATOS"]
    print("-" * 60)
    print("  " + str(len(con_datos)) + " de " + str(len(resultados)) + " sondas con datos")
    if ALCANCE:
        print("  no aplican a un solo repo: " + ", ".join(sorted(SOLO_PROYECTO)))
    print("  informe:   " + rel(destino))
    print("  tablero:   " + rel(destino_tab))
    if copia:
        print("  historico: " + rel(copia))
    else:
        print("  historico: NO se toco — esta es una corrida parcial (--solo).")
        print("             El informe de arriba tiene solo las sondas pedidas; la foto")
        print("             del dia y la linea de base de --comparar quedan como estaban.")

    if comparar_tambien and parcial:
        print()
        print("  --comparar ignorado: comparar una corrida parcial contra una completa")
        print("             daria un resultado que no significa nada. Corre sin --solo.")
    elif comparar_tambien:
        import comparar as _cmp          # noqa
        ruta, info = _cmp.generar(historico, sufijo, hoy)
        if ruta:
            print()
            print("  arreglos:  " + rel(ruta))
            print("             " + str(info.get("arreglado", 0)) + " mejoraron · " +
                  str(info.get("empeoro", 0)) + " empeoraron · " +
                  str(info.get("igual", 0)) + " sin cambios")
        else:
            print()
            print("  sin reporte de arreglos: " + info)
    return 0


def _hoy():
    """Fecha del sistema en dia-mes-anio, que es como el equipo nombra los reportes."""
    import datetime
    return datetime.date.today().strftime("%d-%m-%Y")


def _indice(historico):
    """Un INDICE.md con una fila por corrida guardada.

    Existe para que la carpeta se pueda leer sin abrir ocho archivos: de un
    vistazo se ve cuando se corrio y como salio cada vez."""
    filas = []
    for fn in sorted(listar(historico)):
        # Solo los reportes FECHADOS. ultimo.json y previo.json son copias de
        # rotacion, no corridas: contarlos daba dieciseis filas para ocho corridas
        # reales, y ocho de esas filas enlazaban a un .html que nunca se genera.
        if not fn.startswith("reporte-") or not fn.endswith(".json"):
            continue
        try:
            d = json.loads(leer(os.path.join(historico, fn)))
        except Exception:
            continue
        c = Counter(s["estado"] for s in d.get("sondas", []))
        filas.append((d.get("fecha", fn), d.get("alcance", "proyecto"),
                      len(d.get("sondas", [])), c.get("OK", 0), c.get("HALLAZGO", 0),
                      c.get("SIN DATOS", 0), fn.replace(".json", ".html")))
    # Por fecha descendente, y dentro del mismo dia el proyecto entero primero:
    # sin la columna de alcance, tres corridas del mismo dia se ven identicas.
    filas.sort(key=lambda f: (tuple(reversed(f[0].split("-"))), f[1] == "proyecto"),
               reverse=True)
    txt = ["# Historico de corridas del Doctor", "",
           "Una fila por corrida guardada, de la mas reciente a la mas vieja.",
           "Lo genera `doctor/doctor.py` en cada corrida: **no se edita a mano**.", "",
           "El **alcance** dice que miro esa corrida: `proyecto` es todo, `back` o `front` es",
           "un solo repositorio. En una corrida acotada hay menos sondas, porque tres de ellas",
           "comparan los dos repos entre si y con uno solo no aplican.", "",
           "| Fecha | Alcance | Sondas | OK | Hallazgo | Sin datos | Informe |",
           "|---|---|---|---|---|---|---|"]
    for f in filas:
        txt.append("| " + f[0] + " | " + f[1] + " | " + str(f[2]) + " | " + str(f[3]) + " | " +
                   str(f[4]) + " | " + str(f[5]) + " | [" + f[6] + "](" + f[6] + ") |")
    txt += ["", "> Esta carpeta **no se versiona**: el historico es de cada maquina. Si el equipo",
            "> quiere una historia compartida, hay que decidir donde se publica — no se resuelve",
            "> sacandola del `.gitignore`, porque un informe por dia por persona ensucia el repo."]
    abrir(os.path.join(historico, "INDICE.md"), "w").write("\n".join(txt) + "\n")


if __name__ == "__main__":
    # UTF-8 en la salida, pase lo que pase. Los envoltorios bin/doctor.* ya setean
    # PYTHONIOENCODING, pero al motor se lo puede invocar con `python` directo, y
    # al redirigir en Windows la consola cae a cp1252: el archivo resultante no se
    # podia volver a leer como UTF-8. Un informe ilegible es un informe perdido.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass                          # Python 3.6 y anteriores: se sigue sin esto
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
