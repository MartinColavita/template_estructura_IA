#!/usr/bin/env python3
"""Dice si el sello de auditar-tarea / auditar-historia sigue VIGENTE.

    python bin/verificar-sello.py historia <id-historia> <rev-auditado>
    python bin/verificar-sello.py tarea <id-tarea> <rev-tarea> <id-historia> <rev-historia>

Los numeros salen del propio sello (el comentario que dejo la auditoria en la tarjeta), y
del sello MAS RECIENTE: uno viejo puede dar VIGENTE aunque despues se haya auditado de nuevo
con otro veredicto. Elegir el sello es tarea de la skill; este script evalua el que le pasan.

Tres estados, nunca dos:  0 = VIGENTE   1 = VENCIDO   2 = SIN DATOS
N/A con tablero local (DEC-006): ahi no hay revisiones ni sellos en comentarios; la vigencia la mira auditar-tarea
contra el archivo de la tarjeta. Este script es para tableros con historial de revisiones (Azure DevOps, Jira).
SIN DATOS no es vigente. Cualquier error que no se esperaba tambien da 2, nunca 0 ni 1.

POR QUE EXISTE. El sello vence cuando cambia LO AUDITADO, no cuando se guarda la tarjeta.
En Azure toda escritura directa crea una revision: el propio sello (un comentario), asignar,
pasar a Active, la regla del tablero que activa al padre. Ninguna toca lo auditado. Contar
System.Rev o nace vencido -el sello mismo suma una- o frena Tareas sanas por un comentario.
Hay que mirar QUE CAMPOS cambio cada revision, y eso el MCP de Azure no lo expone:
get_work_item da el estado de ahora, no el historial. Lo da el endpoint de updates:
    GET .../_apis/wit/workItems/{id}/updates
Este script lo lee. SOLO LECTURA: nunca escribe en el board.

QUE CUENTA COMO CAMBIO DE CONTENIDO (la definicion vive en auditar-tarea, seccion 3-bis; si
se cambia alli, se cambia aca):
  - Historia: Titulo, Descripcion, Criterios de aceptacion.
  - Tarea:    Titulo, Descripcion (contrato, SDD, tests, modos de falla), Criterios de
              aceptacion si el tipo los tiene, y de QUE Historia cuelga.
NO cuentan: comentarios, Estado, Asignado, Etiquetas, Iteracion, Area, estimaciones, ni
vinculos a otros items (hijos, Related).

De que Historia cuelga la Tarea se mira en el estado ACTUAL (su Parent de hoy contra el del
sello), no en el historial de vinculos. Motivo: un vinculo agregado desde el OTRO extremo
queda en el historial con el MISMO numero de revision que ya tenia la tarjeta -Azure no la
incrementa-, asi que por historial no se puede saber si fue antes o despues de auditar. Lo
que importa es contra que Gherkin se audito, y eso lo dice el Parent de hoy.

TABLERO. Solo lee del tablero autorizado (tablero/conocimiento/
tablero-autorizado.md). Si la tarjeta es de otro proyecto, no la evalua: SIN DATOS.

ACCESO. Las mismas dos formas que ofrece la guia del MCP (integracion-azure-mcp/
03-configurar-mcp.md): el token AZDO_PAT si esta en el entorno, y si no, la sesion de
Azure CLI (`az login`), igual que AZURE_DEVOPS_AUTH_METHOD=azure-cli. Nunca imprime el
token. Si no hay ninguna de las dos, es un problema de LA MAQUINA, no de la tarjeta, y el
mensaje lo dice: re-auditar no lo destraba.

Solo biblioteca estandar, a proposito: Python 3 ya es requisito del Doctor, y asi no hay
nada que instalar. ASCII puro en este archivo, igual que los .ps1 del repo.
"""

import base64
import http.client
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# Dato duro. Fuente unica: contexto-proyecto (seccion Azure DevOps) y tablero-autorizado.md.
ORG_URL = "https://dev.azure.com/{{AZURE_ORG}}"
PROYECTO = "{{AZURE_PROYECTO}}"
API = "7.1"
# Identificador fijo de Azure DevOps como recurso de Entra ID: es el que se le pide a
# `az account get-access-token` para obtener un token que dev.azure.com acepte.
RECURSO_AZURE_DEVOPS = "499b84ac-1321-427f-aa17-267ca6975798"

CONTENIDO_HISTORIA = (
    "System.Title",
    "System.Description",
    "Microsoft.VSTS.Common.AcceptanceCriteria",
)
# La Tarea usa los mismos tres: los Criterios de aceptacion cuentan si el tipo los tiene
# (Task del proceso Agile no los trae, y entonces nunca aparecen en el historial).
CONTENIDO_TAREA = CONTENIDO_HISTORIA

NOMBRE = {
    "System.Title": "Titulo",
    "System.Description": "Descripcion",
    "Microsoft.VSTS.Common.AcceptanceCriteria": "Criterios de aceptacion",
}

VIGENTE, VENCIDO, SIN_DATOS = 0, 1, 2


class SinDatos(Exception):
    """No se pudo mirar. Nunca se convierte en VIGENTE.

    de_la_maquina=True: el problema es de este equipo (sin token, sin red, sin az), no de
    la tarjeta. Re-auditar no lo arregla: se arregla la maquina."""

    def __init__(self, motivo, de_la_maquina=False):
        super().__init__(motivo)
        self.de_la_maquina = de_la_maquina


# ---------------------------------------------------------------------------------------
# Logica pura: sin red. La prueba (bin/probar-verificar-sello.py) ejercita esto.
# ---------------------------------------------------------------------------------------

def cambios_de_contenido(updates, rev_auditado, campos):
    """Revisiones posteriores a rev_auditado que tocaron algun campo de contenido.

    Devuelve [(rev, [campos])]. Las actualizaciones que solo tocan vinculos no traen
    'fields' y no cuentan; las que traen fields pero ninguno de contenido (el sello,
    Estado, Asignado) tampoco."""
    salida = []
    for u in updates:
        rev = u.get("rev")
        if not isinstance(rev, int) or rev <= rev_auditado:
            continue
        tocados = [c for c in campos if c in (u.get("fields") or {})]
        if tocados:
            salida.append((rev, tocados))
    return salida


def evaluar(item, updates, rev_auditado, campos, etiqueta):
    """Veredicto sobre UN work item. Devuelve (estado, [lineas])."""
    if not updates:
        # Regla del cero: sin historial no se midio nada. Todo item tiene al menos la
        # actualizacion de su alta; una lista vacia es una lectura que fallo.
        raise SinDatos(etiqueta + ": el historial de cambios vino vacio")
    # Con $expand=relations, 'fields' no trae System.Rev: la revision viene en el primer
    # nivel ('rev'). System.Rev queda de respaldo para una respuesta pedida con otro $expand.
    rev_actual = item.get("rev")
    if not isinstance(rev_actual, int):
        rev_actual = (item.get("fields") or {}).get("System.Rev")
    if not isinstance(rev_actual, int):
        raise SinDatos(etiqueta + ": la tarjeta no trae su numero de revision (rev)")
    # El historial tiene que llegar hasta la revision de hoy. Si se corto antes, lo que
    # falta son justamente los cambios MAS NUEVOS -los posteriores al sello- y el
    # veredicto saldria VIGENTE sin haberlos mirado.
    revs = [u.get("rev") for u in updates if isinstance(u.get("rev"), int)]
    if not revs or max(revs) != rev_actual:
        raise SinDatos(etiqueta + ": el historial leido llega hasta el Rev " +
                       (str(max(revs)) if revs else "?") + " y la tarjeta esta en Rev " +
                       str(rev_actual) + ". Quedo incompleto")
    if rev_actual < rev_auditado:
        return VENCIDO, [etiqueta + ": el sello dice Rev " + str(rev_auditado) +
                         " pero la tarjeta esta en Rev " + str(rev_actual) +
                         ". Ese sello no es de esta tarjeta, o se copio mal"]
    cambios = cambios_de_contenido(updates, rev_auditado, campos)
    if cambios:
        return VENCIDO, [etiqueta + ": la revision " + str(r) + " cambio " +
                         ", ".join(NOMBRE.get(c, c) for c in cs) for r, cs in cambios]
    return VIGENTE, [etiqueta + ": sin cambios de contenido desde el Rev " +
                     str(rev_auditado) + " (hoy esta en Rev " + str(rev_actual) + ")"]


def padre_de(item):
    """El #ID del Parent actual, o None."""
    for r in item.get("relations") or []:
        if r.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
            cola = str(r.get("url", "")).rstrip("/").rsplit("/", 1)[-1]
            if cola.isascii() and cola.isdigit():
                return int(cola)
    return None


def chequear_tablero(item, etiqueta):
    proyecto = (item.get("fields") or {}).get("System.TeamProject")
    if proyecto != PROYECTO:
        raise SinDatos(etiqueta + ": es del proyecto '" + str(proyecto) +
                       "', no del tablero autorizado '" + PROYECTO + "'. No se evalua")


# ---------------------------------------------------------------------------------------
# Acceso y lectura del board (solo GET)
# ---------------------------------------------------------------------------------------

def obtener_autorizacion():
    """El valor del header Authorization. Primero AZDO_PAT; si no, la sesion de az."""
    pat = os.environ.get("AZDO_PAT", "")
    if pat:
        return "Basic " + base64.b64encode((":" + pat).encode("ascii")).decode("ascii")
    az = shutil.which("az")
    if not az:
        raise SinDatos("no hay AZDO_PAT en el entorno ni Azure CLI instalada. Hace falta una "
                       "de las dos, igual que para el MCP (integracion-azure-mcp/"
                       "03-configurar-mcp.md)", de_la_maquina=True)
    try:
        r = subprocess.run([az, "account", "get-access-token", "--resource",
                            RECURSO_AZURE_DEVOPS, "--query", "accessToken", "-o", "tsv"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise SinDatos("no se pudo correr Azure CLI (" + type(e).__name__ + ")",
                       de_la_maquina=True)
    token = (r.stdout or "").strip()
    if r.returncode != 0 or not token:
        raise SinDatos("no hay AZDO_PAT y Azure CLI no dio un token: falta `az login` o "
                       "la sesion vencio", de_la_maquina=True)
    return "Bearer " + token


def _get(ruta, autorizacion):
    url = ORG_URL + "/" + urllib.parse.quote(PROYECTO) + "/_apis/wit/" + ruta
    pedido = urllib.request.Request(url, method="GET")
    pedido.add_header("Authorization", autorizacion)
    pedido.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(pedido, timeout=20) as r:
            tipo = r.headers.get("Content-Type", "")
            cuerpo = r.read()
            codigo = r.status
    except urllib.error.HTTPError as e:
        motivo = {401: "token vencido o revocado",
                  403: "al token le falta el permiso de lectura de work items",
                  404: "no existe, o el token no ve el proyecto (Azure responde igual)"}
        raise SinDatos("HTTP " + str(e.code) + " -- " + motivo.get(e.code, "error del servidor"),
                       de_la_maquina=e.code in (401, 403))
    except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
        raise SinDatos("no se pudo leer de dev.azure.com (" + type(e).__name__ + ")",
                       de_la_maquina=True)
    # Con un token invalido Azure puede contestar 203 con la pagina de login en HTML.
    # Que responda no alcanza: tiene que ser JSON.
    if codigo != 200 or "json" not in tipo.lower():
        raise SinDatos("respuesta " + str(codigo) + " que no es JSON: probablemente el token "
                       "no es valido y Azure devolvio la pagina de login", de_la_maquina=True)
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except ValueError:
        raise SinDatos("la respuesta no se pudo leer como JSON")
    if not isinstance(datos, dict):
        raise SinDatos("la respuesta no tiene la forma esperada")
    return datos


def leer_item(wid, autorizacion):
    return _get("workitems/" + str(wid) + "?$expand=relations&api-version=" + API, autorizacion)


def leer_updates(wid, autorizacion):
    todos, salto, lote = [], 0, 200
    # Tope de paginas: el limite de Azure es 10.000 revisiones por item (50 paginas de
    # 200). Sin tope, un servidor que ignorara $skip dejaria el bucle girando para siempre.
    for _ in range(60):
        valores = _get("workItems/" + str(wid) + "/updates?$top=" + str(lote) +
                       "&$skip=" + str(salto) + "&api-version=" + API, autorizacion).get("value")
        if not isinstance(valores, list):
            raise SinDatos("el historial de la #" + str(wid) + " no vino como lista")
        todos.extend(valores)
        if len(valores) < lote:
            return todos
        salto += lote
    raise SinDatos("el historial de la #" + str(wid) + " no termino de paginar")


# ---------------------------------------------------------------------------------------

USO = """Uso:
  verificar-sello historia <id-historia> <rev-auditado>
  verificar-sello tarea <id-tarea> <rev-tarea> <id-historia> <rev-historia>

Los numeros salen del sello MAS RECIENTE que dejo la auditoria en la tarjeta.
Salida: 0 = VIGENTE   1 = VENCIDO   2 = SIN DATOS (no es vigente)"""


def mal_uso(mensaje):
    # Sale con 2, no con 1: un pedido mal armado no midio nada, y el 1 es VENCIDO.
    print(mensaje, file=sys.stderr)
    sys.exit(SIN_DATOS)


def entero(texto, que):
    t = texto.lstrip("#")
    # isascii: isdigit() solo acepta tambien digitos Unicode como el superindice, que
    # despues int() rechaza.
    if not (t.isascii() and t.isdigit()):
        mal_uso("verificar-sello: '" + texto + "' no es un " + que + "\n\n" + USO)
    return int(t)


def correr(argv, autorizacion, leer_item=leer_item, leer_updates=leer_updates):
    """Devuelve (estado, lineas). Los lectores se inyectan para poder probar sin red."""
    if len(argv) == 3 and argv[0] == "historia":
        hid, hrev = entero(argv[1], "#ID"), entero(argv[2], "Rev")
        tareas = []
    elif len(argv) == 5 and argv[0] == "tarea":
        tid, trev = entero(argv[1], "#ID"), entero(argv[2], "Rev")
        hid, hrev = entero(argv[3], "#ID"), entero(argv[4], "Rev")
        tareas = [(tid, trev)]
    else:
        mal_uso(USO)

    if not autorizacion:
        autorizacion = obtener_autorizacion()

    estado, lineas = VIGENTE, []
    for tid, trev in tareas:
        et = "Tarea #" + str(tid)
        item = leer_item(tid, autorizacion)
        chequear_tablero(item, et)
        padre = padre_de(item)
        if padre != hid:
            estado = VENCIDO
            lineas.append(et + ": hoy cuelga de " +
                          ("#" + str(padre) if padre else "ninguna Historia") +
                          ", y se audito contra la #" + str(hid) + ". Correr analizar-tareas "
                          "sobre las Tareas de las dos Historias: a la de origen le puede "
                          "haber quedado un Escenario sin cubrir")
        e, ls = evaluar(item, leer_updates(tid, autorizacion), trev, CONTENIDO_TAREA, et)
        estado, lineas = max(estado, e), lineas + ls

    eh = "Historia #" + str(hid)
    item = leer_item(hid, autorizacion)
    chequear_tablero(item, eh)
    e, ls = evaluar(item, leer_updates(hid, autorizacion), hrev, CONTENIDO_HISTORIA, eh)
    return max(estado, e), lineas + ls


def main():
    try:
        estado, lineas = correr(sys.argv[1:], "")
    except SinDatos as e:
        print("SIN DATOS -- no se pudo verificar el sello.")
        print("  Motivo: " + str(e))
        if e.de_la_maquina:
            print("  Es un problema de esta maquina, no de la tarjeta: re-auditar NO lo")
            print("  destraba. Se arregla el acceso y se vuelve a correr.")
        else:
            print("  Esto NO es vigente: se re-audita.")
        return SIN_DATOS
    except Exception as e:  # noqa: BLE001 -- a proposito: ningun error puede dar 0 ni 1
        print("SIN DATOS -- el verificador fallo de una forma que no se esperaba.")
        print("  Error: " + type(e).__name__ + ": " + str(e))
        print("  Esto NO es vigente. Avisar: es un bug del verificador, no de la tarjeta.")
        return SIN_DATOS
    print({VIGENTE: "VIGENTE -- nada de lo auditado cambio.",
           VENCIDO: "VENCIDO -- cambio lo auditado: hay que re-auditar."}[estado])
    for l in lineas:
        print("  " + l)
    return estado


if __name__ == "__main__":
    sys.exit(main())
