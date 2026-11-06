# -*- coding: utf-8 -*-
"""
Render del informe HTML del Doctor.

El diseno vive en doctor/informe/plantilla.html — un HTML completo, autocontenido y
con datos de ejemplo reemplazados por un marcador. Aca solo se le inyectan los datos
reales de la corrida.

Por que asi y no con el HTML embebido en Python:
  - el diseno se puede abrir, mirar y editar como lo que es, un HTML;
  - quien toca el CSS no tiene que pelear con comillas dentro de un string de Python;
  - y el contrato entre los dos es UN objeto JSON, chico y explicito.

El HTML lleva su CSS y su JavaScript adentro y dibuja los graficos con SVG generado a
mano: cero librerias, cero CDN, cero llamadas de red. El informe puede contener rutas y
nombres internos, asi que NO sale de la maquina y se abre igual sin conexion.
"""
import io
import json
import os
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANTILLA = os.path.join(AQUI, "informe", "plantilla.html")

ABRE, CIERRA = "/*__DATOS__*/", "/*__FIN__*/"

# Ancho de cada panel en la grilla de 12 columnas del informe.
# Las sondas con grafico o con tabla ancha piden mas lugar.
SPAN = {
    # Sondas de documentacion y configuracion.
    "guardarrailes": 4, "espejos": 4, "conteos": 4,
    "wikilinks": 6, "estructura": 6,
    "asimetria": 5, "tamano": 7, "deuda": 12,
    # Sondas de codigo. Las anchas son las que traen tablas de cinco columnas con
    # texto largo adentro -la regla que se rompe, el por que importa-: apretadas en
    # media grilla, esa columna se lee en cuatro palabras por renglon.
    "repos": 12, "limites": 12, "duplicacion": 12, "costura": 12,
    "contrato": 6, "trazabilidad": 6, "dependencias": 6,
    "seguridad": 6, "calidad": 6, "practicas": 12,
    # La tendencia va ancha: es la primera que se mira y tiene una fila por sonda.
    "tendencia": 12,
}

# Umbral por sonda: el informe lo usa para pintar de naranja lo que lo supera.
UMBRAL = {"tamano": 250}


def _git(root, *args):
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                           cwd=root, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def render(resultados, root):
    """resultados: lista de diccionarios, tal como los devuelve doctor.correr()."""
    if not os.path.isfile(PLANTILLA):
        raise RuntimeError("Falta la plantilla del informe: " + PLANTILLA)

    sondas = []
    for r in resultados:
        sid = r["id"]
        cols, filas = (r["tabla"] if r["tabla"] else ([], []))
        s = {
            "id": sid,
            "titulo": r["titulo"],
            "estado": r["estado"],
            "resumen": r["resumen"],
            "sp": SPAN.get(sid, 6),
            "cols": list(cols),
            "filas": [[str(c) for c in f] for f in filas],
        }
        # Los tres campos de guia son OPCIONALES: si una sonda no los trae, no se
        # emiten, y el informe degrada sin romperse. No se inventa texto aca.
        if r.get("significa"):
            s["significa"] = r["significa"]
        if r.get("importa"):
            s["importa"] = r["importa"]
        if r.get("acciones"):
            s["acciones"] = [
                {k: v for k, v in (("paso", a.get("paso")), ("comando", a.get("comando"))) if v}
                for a in r["acciones"]
            ]
        if r.get("pedido"):
            s["pedido"] = r["pedido"]
        if sid in UMBRAL:
            s["umbral"] = UMBRAL[sid]
        sondas.append(s)

    datos = {
        "rama": _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "sin datos",
        "fecha": _git(root, "log", "-1", "--format=%cd", "--date=short") or "sin datos",
        "sondas": sondas,
    }

    plantilla = io.open(PLANTILLA, encoding="utf-8", newline="").read()

    # Respaldo sin JavaScript. El informe arma todo el cuerpo con JS a partir del
    # objeto de arriba: si el JS no corre -politica del navegador, archivo abierto
    # de una forma rara, un error nuestro-, sin esto la pagina queda EN BLANCO y el
    # lector no sabe si el proyecto esta sano o si se rompio el informe.
    # No reemplaza al informe: da el veredicto de cada sonda, que es lo minimo.
    plantilla = plantilla.replace("<body>", "<body>" + _respaldo(sondas), 1)

    i = plantilla.index(ABRE)
    j = plantilla.index(CIERRA) + len(CIERRA)

    # ensure_ascii=False para que los acentos salgan legibles en el HTML;
    # el </script> se escapa porque adentro de un <script> cerraria el bloque.
    json_datos = json.dumps(datos, ensure_ascii=False, indent=2).replace("</", "<\\/")

    return plantilla[:i] + json_datos + plantilla[j:]


def _id_de(titulo):
    """Respaldo: si una sonda no declara id, se deriva del titulo.
    No deberia usarse — los ids son estables a proposito, porque el informe
    engancha los graficos por id."""
    base = titulo.lower().split()[0]
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")]:
        base = base.replace(a, b)
    return "".join(c for c in base if c.isalnum())


def _respaldo(sondas):
    """Bloque <noscript>: el veredicto de cada sonda, en HTML plano."""
    import html as _h
    filas = "".join(
        "<tr><td>" + _h.escape(s["titulo"]) + "</td>"
        "<td><b>" + _h.escape(s["estado"]) + "</b></td>"
        "<td>" + _h.escape(s["resumen"]) + "</td></tr>"
        for s in sondas)
    return (
        '<noscript><div style="max-width:60rem;margin:2rem auto;padding:1.5rem;'
        'font:14px/1.5 system-ui,sans-serif;color:#1A1D26;background:#fff;'
        'border:1px solid #e5e7eb;border-radius:8px">'
        '<h1 style="font-size:1.25rem;margin:0 0 .25rem">Doctor de {{PROYECTO}}</h1>'
        '<p style="color:#8390a2;margin:0 0 1rem">Este navegador tiene el JavaScript '
        'desactivado, asi que no se puede mostrar el informe completo. Abajo va el '
        'veredicto de cada sonda, que es lo esencial.</p>'
        '<table style="width:100%;border-collapse:collapse;font-size:13px">'
        '<thead><tr>'
        '<th style="text-align:left;border-bottom:1px solid #e5e7eb;padding:.4rem">Sonda</th>'
        '<th style="text-align:left;border-bottom:1px solid #e5e7eb;padding:.4rem">Estado</th>'
        '<th style="text-align:left;border-bottom:1px solid #e5e7eb;padding:.4rem">Resumen</th>'
        '</tr></thead><tbody>' + filas + '</tbody></table>'
        '<p style="color:#8390a2;margin:1rem 0 0">SIN DATOS no es aprobado: significa que '
        'esa sonda todavia no pudo medir.</p></div></noscript>')


# --------------------------------------------------------------------- tablero

TABLERO = os.path.join(AQUI, "informe", "tablero.html")

# Los pocos numeros que el tablero muestra como titular. La regla es no inventar:
# cada uno dice de que sonda sale y de que COLUMNA de su tabla, y si esa sonda no
# corrio -una corrida acotada, o la sonda fallo- el numero simplemente no aparece.
# Columna en None significa "contar las filas".
DUROS = [
    ("deuda", "Cantidad", "marcas", "de pendiente en la documentacion"),
    ("tamano", "Tokens que pesan siempre", "tokens", "que pesan en cada sesion, solo por tener las skills"),
    ("autocontrol", None, "chequeos", "de coherencia que el informe se hace a si mismo"),
]


def _entero(v):
    """Un entero de una celda. Las celdas traen '~6533' o '1.234': se leen los
    digitos y nada mas. Si no hay ninguno, la celda no aporta."""
    d = "".join(c for c in str(v) if c.isdigit())
    return int(d) if d else 0


def _columna(sonda, nombre):
    try:
        return sonda["cols"].index(nombre)
    except (ValueError, KeyError, AttributeError):
        return -1


def render_tablero(resultados, root, serie=None, alcance="", hoy="", parcial=False):
    """El resumen de un vistazo. Misma corrida y mismos datos que el informe.

    Sale de `resultados` -lo que devuelve doctor.correr()- sin volver a medir
    nada: si el tablero y el informe dijeran cosas distintas seria un bug, no una
    diferencia de criterio. `serie` son las corridas guardadas, para la tendencia.
    """
    if not os.path.isfile(TABLERO):
        raise RuntimeError("Falta la plantilla del tablero: " + TABLERO)

    try:
        import codigo                                    # noqa
        de_codigo = set(f.__name__.replace("sonda_", "") for f in codigo.SONDAS)
    except Exception:
        de_codigo = set()

    sondas, por_id = [], {}
    for r in resultados:
        cols, filas = (r["tabla"] if r["tabla"] else ([], []))
        s = {
            "id": r["id"],
            "titulo": r["titulo"],
            "estado": r["estado"],
            "resumen": r["resumen"],
            "acciones": len(r.get("acciones") or []),
            "grupo": "codigo" if r["id"] in de_codigo else "proyecto",
        }
        sondas.append(s)
        por_id[r["id"]] = {"cols": list(cols), "filas": [[str(c) for c in f] for f in filas]}

    # Un numero que no se puede calcular NO se saltea: se muestra diciendo por que.
    # El caso que esto ataja es silencioso y real: alguien renombra una columna en
    # una sonda, este modulo deja de encontrarla y el numero se evapora del tablero
    # sin una sola linea de aviso. Nadie lo nota, porque nadie se acuerda de que ahi
    # iba un numero. Es el mismo agujero que la lista de sondas dormidas: el que no
    # avisa es el que hace dano.
    #
    # La sonda AUSENTE es otra cosa y no se reporta: en una corrida acotada faltan
    # sondas a proposito, y gritar por eso seria gritar por todo. Una sonda que grita
    # lobo es peor que no tenerla.
    duros = []
    for sid, col, unidad, etiqueta in DUROS:
        if sid not in por_id:
            continue
        d = por_id[sid]
        if col is None:
            duros.append({"id": sid, "valor": len(d["filas"]),
                          "unidad": unidad, "etiqueta": etiqueta})
            continue
        i = _columna(d, col)
        if i < 0:
            duros.append({"id": sid, "unidad": unidad, "etiqueta": etiqueta,
                          "falta": u"la sonda corrio, pero su tabla ya no trae la columna "
                                   u"«" + col + u"»: el numero no se puede calcular"})
            continue
        # Un cero tambien es un dato -cero deuda es una buena noticia-, asi que se
        # muestra. Antes se descartaba junto con los faltantes, y eran cosas distintas.
        duros.append({"id": sid, "valor": sum(_entero(f[i]) for f in d["filas"] if len(f) > i),
                      "unidad": unidad, "etiqueta": etiqueta})

    # El grafico de skills sale de la misma tabla que el informe ya dibuja, para
    # que los dos muestren lo mismo. Si la sonda no corrio, el panel lo dice.
    skills = None
    if "tamano" in por_id:
        d = por_id["tamano"]
        i = _columna(d, "Lineas")
        if i < 0:
            skills = {"falta": u"la sonda de costo de contexto corrio, pero su tabla ya no "
                               u"trae la columna «Lineas»: no hay que dibujar"}
        else:
            # Ordenadas por lo que la barra mide. La tabla del informe viene en otro
            # orden, y un grafico de barras desordenado se lee como un error.
            todas = sorted(([f[0], _entero(f[i])] for f in d["filas"] if len(f) > i),
                           key=lambda x: -x[1])
            skills = {"umbral": UMBRAL.get("tamano", 0), "unidad": "lineas",
                      "filas": todas[:8]}

    datos = {
        "rama": _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "sin datos",
        "fecha": hoy or (_git(root, "log", "-1", "--format=%cd", "--date=short") or "sin datos"),
        "commit": _git(root, "log", "-1", "--format=%cd", "--date=short") or "sin datos",
        "alcance": alcance or "proyecto",
        "corridas": len(serie or []),
        "parcial": bool(parcial),
        "sondas": sondas,
        "serie": serie or [],
        "duros": duros,
    }
    if skills:
        datos["skills"] = skills

    plantilla = io.open(TABLERO, encoding="utf-8", newline="").read()
    plantilla = plantilla.replace("<body>", "<body>" + _respaldo(sondas), 1)

    i = plantilla.index(ABRE)
    j = plantilla.index(CIERRA) + len(CIERRA)
    json_datos = json.dumps(datos, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return plantilla[:i] + json_datos + plantilla[j:]
