#!/usr/bin/env python3
"""Prueba de bin/verificar-sello.py SIN RED: se le inyectan tarjetas armadas a mano.

    python bin/probar-verificar-sello.py

Sale 0 si todos los casos dan lo esperado, 1 si alguno no.

Las formas de los datos copian las del endpoint real de updates (ejemplo oficial de
Microsoft, Updates - List, api 7.1): un cambio que solo toca vinculos NO trae 'fields' y
queda con el MISMO 'rev' que ya tenia la tarjeta. Ese es el caso que motivo el script.
La tarjeta copia la respuesta real de GET workitems con $expand=relations: la revision
viene en 'rev', en el primer nivel, y 'fields' NO trae System.Rev.
"""

import importlib.util
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("vs", os.path.join(AQUI, "verificar-sello.py"))
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

PROY = vs.PROYECTO
URL = "https://dev.azure.com/{{AZURE_ORG}}/_apis/wit/workItems/"


def item(rev, padre=None, proyecto=PROY):
    it = {"rev": rev, "fields": {"System.TeamProject": proyecto}}
    if padre:
        it["relations"] = [{"rel": "System.LinkTypes.Hierarchy-Reverse", "url": URL + str(padre)}]
    return it


def up(rev, *campos):
    """Una actualizacion con esos campos. Sin campos = solo vinculos."""
    u = {"rev": rev}
    if campos:
        u["fields"] = {c: {"newValue": "x"} for c in campos + ("System.Rev", "System.ChangedDate")}
    else:
        u["relations"] = {"added": [{"rel": "System.LinkTypes.Hierarchy-Forward", "url": URL + "9"}]}
    return u


ALTA = up(1, "System.Title", "System.Description", "System.State")
SELLO = "System.History"
DESC, TIT, CA = "System.Description", "System.Title", "Microsoft.VSTS.Common.AcceptanceCriteria"

T, H = 101, 200   # #ID de la Tarea y de la Historia en todos los casos


def lectores(items, updates):
    return (lambda wid, pat: items[wid]), (lambda wid, pat: updates[wid])


# (nombre, argv, items, updates, esperado)
CASOS = [
    ("Tarea recien sellada: la unica revision nueva es el sello",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(4, H), H: item(5)},
     {T: [ALTA, up(2, DESC), up(3, DESC), up(4, SELLO)], H: [ALTA, up(5, CA)]},
     vs.VIGENTE),

    ("Comentario de un dev, asignarla y pasarla a Active: no tocan lo auditado",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(7, H), H: item(5)},
     {T: [ALTA, up(3, DESC), up(4, SELLO), up(5, SELLO), up(6, "System.AssignedTo", "System.State"),
          up(7, "System.Tags")], H: [ALTA, up(5, CA)]},
     vs.VIGENTE),

    ("Se colgo una Tarea hermana (vinculo sin numero de revision) y se comento la Historia",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(4, H), H: item(7)},
     {T: [ALTA, up(3, DESC), up(4, SELLO)],
      H: [ALTA, up(5, CA), up(5), up(5), up(6, SELLO), up(7, "System.State", "System.Reason")]},
     vs.VIGENTE),

    ("Cambio la Descripcion de la Tarea despues del sello",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(5, H), H: item(5)},
     {T: [ALTA, up(3, DESC), up(4, SELLO), up(5, DESC)], H: [ALTA, up(5, CA)]},
     vs.VENCIDO),

    ("Cambiaron los Criterios de aceptacion de la Historia padre",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(4, H), H: item(6)},
     {T: [ALTA, up(3, DESC), up(4, SELLO)], H: [ALTA, up(5, CA), up(6, CA)]},
     vs.VENCIDO),

    ("La Tarea hoy cuelga de otra Historia",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(4, 999), H: item(5)},
     {T: [ALTA, up(3, DESC), up(4, SELLO)], H: [ALTA, up(5, CA)]},
     vs.VENCIDO),

    ("La Tarea quedo sin Historia padre",
     ["tarea", str(T), "3", str(H), "5"],
     {T: item(4), H: item(5)},
     {T: [ALTA, up(3, DESC), up(4, SELLO)], H: [ALTA, up(5, CA)]},
     vs.VENCIDO),

    ("Un cambio de contenido en el MISMO Rev auditado es anterior a la auditoria: no cuenta",
     ["historia", str(H), "5"],
     {H: item(6)},
     {H: [ALTA, up(5, TIT, CA), up(6, SELLO)]},
     vs.VIGENTE),

    ("Historia: cambio el Titulo despues del sello",
     ["historia", str(H), "5"],
     {H: item(7)},
     {H: [ALTA, up(5, CA), up(6, SELLO), up(7, TIT)]},
     vs.VENCIDO),

    ("El sello dice un Rev mayor al que tiene la tarjeta",
     ["historia", str(H), "9"],
     {H: item(7)},
     {H: [ALTA, up(7, CA)]},
     vs.VENCIDO),

    ("Historial vacio: no se midio nada (regla del cero)",
     ["historia", str(H), "5"],
     {H: item(6)},
     {H: []},
     vs.SIN_DATOS),

    ("Tarjeta de otro proyecto: no se evalua",
     ["historia", str(H), "5"],
     {H: item(6, proyecto="Otro_Proyecto")},
     {H: [ALTA, up(6, SELLO)]},
     vs.SIN_DATOS),

    # El caso real: primero un comentario (Rev 6) y DESPUES se cuelga una Tarea desde la
    # hija. Ese vinculo llega con rev 6 -mayor al auditado- y sin 'fields'. Tiene que pasar
    # por el filtro de campos, no por el de rev, y no contar.
    ("Vinculo sin campos con rev MAYOR al auditado: no cuenta",
     ["historia", str(H), "5"],
     {H: item(6)},
     {H: [ALTA, up(5, CA), up(6, SELLO), up(6)]},
     vs.VIGENTE),

    ("Sin 'rev' de primer nivel pero con System.Rev en fields (otro $expand): se usa ese",
     ["historia", str(H), "5"],
     {H: {"fields": {"System.Rev": 6, "System.TeamProject": PROY}}},
     {H: [ALTA, up(5, CA), up(6, SELLO)]},
     vs.VIGENTE),

    ("La tarjeta no trae su revision en ningun lado: no se puede dar vigente",
     ["historia", str(H), "5"],
     {H: {"fields": {"System.TeamProject": PROY}}},
     {H: [ALTA, up(5, CA), up(6, SELLO)]},
     vs.SIN_DATOS),

    ("Historial cortado antes de la revision de hoy: no se puede dar vigente",
     ["historia", str(H), "5"],
     {H: item(8)},
     {H: [ALTA, up(5, CA), up(6, SELLO)]},
     vs.SIN_DATOS),
]


def correr_caso(argv, items, updates, pat="token-de-prueba"):
    li, lu = lectores(items, updates)
    try:
        estado, _ = vs.correr(argv, pat, leer_item=li, leer_updates=lu)
    except vs.SinDatos:
        estado = vs.SIN_DATOS
    return estado


def main():
    nombre = {vs.VIGENTE: "VIGENTE", vs.VENCIDO: "VENCIDO", vs.SIN_DATOS: "SIN DATOS"}
    malos = 0
    for titulo, argv, items, updates, esperado in CASOS:
        obtenido = correr_caso(argv, items, updates)
        ok = obtenido == esperado
        malos += not ok
        print(("  OK     " if ok else "  FALLA  ") + titulo + " -> " + nombre[obtenido] +
              ("" if ok else "  (se esperaba " + nombre[esperado] + ")"))

    extra = 0

    def chequeo(titulo, obtenido, esperado):
        nonlocal malos, extra
        extra += 1
        ok = obtenido == esperado
        malos += not ok
        print(("  OK     " if ok else "  FALLA  ") + titulo + " -> " + nombre.get(obtenido, str(obtenido)) +
              ("" if ok else "  (se esperaba " + nombre[esperado] + ")"))

    # Sin AZDO_PAT y sin Azure CLI: SIN DATOS, y marcado como problema de la maquina.
    guardado_pat, guardado_which = os.environ.pop("AZDO_PAT", None), vs.shutil.which
    vs.shutil.which = lambda _: None
    try:
        vs.correr(["historia", str(H), "5"], "", leer_item=lambda *a: item(6),
                  leer_updates=lambda *a: [ALTA, up(6, SELLO)])
        obtenido = vs.VIGENTE
    except vs.SinDatos as e:
        obtenido = vs.SIN_DATOS if e.de_la_maquina else -1
    finally:
        vs.shutil.which = guardado_which
        if guardado_pat is not None:
            os.environ["AZDO_PAT"] = guardado_pat
    chequeo("Sin AZDO_PAT ni Azure CLI: SIN DATOS de la maquina", obtenido, vs.SIN_DATOS)

    # Un digito Unicode (superindice) no es un numero: error de uso, sale 2 y no 1.
    try:
        vs.entero(chr(0xB2), "Rev")
        obtenido = vs.VIGENTE
    except SystemExit as e:
        obtenido = e.code
    chequeo("Argumento con un digito Unicode: error de uso", obtenido, vs.SIN_DATOS)

    # Un error que nadie esperaba nunca puede dar 0 ni 1.
    guardado_correr = vs.correr

    def explota(*a, **k):
        raise AttributeError("forma inesperada")
    vs.correr = explota
    try:
        obtenido = vs.main()
    finally:
        vs.correr = guardado_correr
    chequeo("Error inesperado dentro del verificador", obtenido, vs.SIN_DATOS)

    total = len(CASOS) + extra
    print()
    print(("OK -- " if not malos else "FALLA -- ") + str(total - malos) + " de " + str(total) +
          " casos dieron lo esperado.")
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
