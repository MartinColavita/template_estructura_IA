# -*- coding: utf-8 -*-
"""
Reporte de arreglos: que cambio entre la corrida anterior y esta.

Existe porque el informe del Doctor contesta "como esta el proyecto HOY", y esa no
es la pregunta que uno tiene despues de arreglar algo. Ahi la pregunta es "¿sirvio
lo que hice?", y para contestarla hace falta comparar dos momentos.

Funciona igual si los arreglos los hizo una persona a mano o un comando: compara
estados, no le importa quien los produjo.
"""
import html
import io
import json
import os
from collections import Counter

ORDEN = {"OK": 0, "HALLAZGO": 1, "SIN DATOS": 2}


def esc(s):
    return html.escape(str(s), quote=True)


def _cargar(p):
    try:
        return json.loads(io.open(p, encoding="utf-8").read())
    except Exception:
        return None


# Las sondas que miran el INFORME y no el proyecto. Quedan afuera de cualquier
# comparacion: decir "la tendencia empeoro" no significa nada -es la sonda
# midiendose a si misma midiendo- y decir "el autocontrol empeoro" tampoco, porque
# eso ya sale de su propio panel.
#
# Vive aca y no en quien llama, porque las DOS vistas -el panel del informe y este
# reporte- tienen que excluirlas igual. Cuando la exclusion estaba solo de un lado,
# las dos vistas daban numeros distintos sobre los mismos datos: 1 empeoro contra 2.
PROPIAS_DEL_INFORME = ("tendencia", "autocontrol")


def claves_de(r):
    """La huella de cada hallazgo de una sonda, para comparar dos corridas hallazgo por hallazgo (contar filas
    confunde uno arreglado y otro nuevo con "sin cambios"). Si la sonda la calculo sobre su lista completa (la que
    corta su tabla), esa. Si no, la primera columna de cada fila de la tabla y, si la tabla tiene columna Estado,
    solo de las filas en HALLAZGO: una fila en OK no es un hallazgo. Con repetidas: dos filas, dos hallazgos."""
    if isinstance(r.get("claves"), list):
        return sorted(str(c) for c in r["claves"])
    t = r.get("tabla")
    if not t or len(t) < 2:
        return []
    cab = [str(c).strip().lower() for c in t[0]]
    ie = cab.index("estado") if "estado" in cab else None
    return sorted(str(f[0]) for f in t[1]
                  if f and (ie is None or (ie < len(f) and "HALLAZGO" in str(f[ie]))))


def comparar(previo, actual):
    """Devuelve (resumen, filas). Cada fila: id, titulo, antes, ahora, veredicto."""
    pa = {s["id"]: s for s in previo.get("sondas", [])
          if s.get("id") not in PROPIAS_DEL_INFORME}
    ac = {s["id"]: s for s in actual.get("sondas", [])
          if s.get("id") not in PROPIAS_DEL_INFORME}

    filas, cuenta = [], {"arreglado": 0, "empeoro": 0, "igual": 0, "nuevo": 0, "ya no esta": 0}
    for sid in sorted(set(pa) | set(ac), key=lambda k: ORDEN.get(ac.get(k, {}).get("estado", "SIN DATOS"), 9)):
        a, b = pa.get(sid), ac.get(sid)
        nuevos = resueltos = None
        if not a:
            v = "nuevo"
        elif not b:
            v = "ya no esta"
        elif (a["estado"] == b["estado"] == "HALLAZGO" and isinstance(a.get("claves"), list)
              and isinstance(b.get("claves"), list)):
            # Hallazgo por hallazgo: uno nuevo es EMPEORO aunque se hayan arreglado otros (lo nuevo pide
            # atencion); sin nuevos, arreglar alguno es progreso aunque siga en HALLAZGO.
            ca, cb = Counter(a["claves"]), Counter(b["claves"])
            nuevos, resueltos = sum((cb - ca).values()), sum((ca - cb).values())
            v = "empeoro" if nuevos else ("arreglado" if resueltos else "igual")
        elif a["estado"] == b["estado"]:
            # Una corrida vieja, sin huellas: solo se puede comparar la cantidad de filas.
            # Pasar de 12 wikilinks rotos a 3 es progreso aunque siga en HALLAZGO.
            if a.get("filas", 0) != b.get("filas", 0) and b["estado"] == "HALLAZGO":
                v = "arreglado" if b.get("filas", 0) < a.get("filas", 0) else "empeoro"
            else:
                v = "igual"
        elif b["estado"] == "OK":
            v = "arreglado"
        elif a["estado"] == "OK":
            v = "empeoro"
        else:
            v = "igual"
        cuenta[v] = cuenta.get(v, 0) + 1
        filas.append({
            "id": sid,
            "titulo": (b or a).get("titulo", sid),
            "antes": a["estado"] if a else "—",
            "ahora": b["estado"] if b else "—",
            "filas_antes": a.get("filas", 0) if a else 0,
            "filas_ahora": b.get("filas", 0) if b else 0,
            "resumen_antes": a.get("resumen", "") if a else "",
            "resumen_ahora": b.get("resumen", "") if b else "",
            "veredicto": v,
            "nuevos": nuevos,
            "resueltos": resueltos,
        })
    return cuenta, filas


PILL = {"OK": "ok", "HALLAZGO": "hal", "SIN DATOS": "sd", "—": "sd"}
VER = {"arreglado": ("Arreglado", "ok"), "empeoro": ("Empeoró", "hal"),
       "igual": ("Sin cambios", "sd"), "nuevo": ("Sonda nueva", "az"),
       "ya no esta": ("Ya no se mide", "sd")}


def render(previo, actual, cuenta, filas):
    mejor = [f for f in filas if f["veredicto"] == "arreglado"]
    peor = [f for f in filas if f["veredicto"] == "empeoro"]
    igual = [f for f in filas if f["veredicto"] == "igual"]
    otros = [f for f in filas if f["veredicto"] in ("nuevo", "ya no esta")]
    abiertos = [f for f in filas if f["ahora"] == "HALLAZGO"]

    def flecha(f):
        """El antes -> ahora, que es el corazon de este reporte."""
        izq = ('<span class="p ' + PILL.get(f["antes"], "sd") + '">' + esc(f["antes"]) + "</span>"
               + ('<span class="cnt">' + str(f["filas_antes"]) + " filas</span>"
                  if f["filas_antes"] else ""))
        der = ('<span class="p ' + PILL.get(f["ahora"], "sd") + '">' + esc(f["ahora"]) + "</span>"
               + ('<span class="cnt">' + str(f["filas_ahora"]) + " filas</span>"
                  if f["filas_ahora"] else ""))
        return ('<div class="salto"><div class="lado">' + izq + "</div>"
                '<div class="fl" aria-hidden="true">&rarr;</div>'
                '<div class="lado">' + der + "</div></div>")

    def tarjeta(f):
        etq, cl = VER[f["veredicto"]]
        # Cuanto bajo, cuando el estado no cambio pero si la cantidad
        delta = ""
        if f.get("nuevos") or f.get("resueltos"):
            delta = ('<div class="delta">Se resolvi' + ('ó ' if f["resueltos"] == 1 else 'eron ') + str(f["resueltos"] or 0) +
                     ' y apareci' + ('ó ' if f["nuevos"] == 1 else 'eron ') + str(f["nuevos"] or 0) + '.</div>')
        elif f["filas_antes"] > f["filas_ahora"] > 0:
            delta = ('<div class="delta">Bajó de ' + str(f["filas_antes"]) + " a " +
                     str(f["filas_ahora"]) + " — sigue abierto, pero menos.</div>")
        elif f["filas_antes"] and not f["filas_ahora"]:
            delta = '<div class="delta">No queda ninguno.</div>'
        return ('<article class="t ' + cl + '">'
                '<div class="th"><h3>' + esc(f["titulo"]) + "</h3>"
                '<span class="v ' + cl + '">' + etq + "</span></div>"
                + flecha(f) + delta +
                '<div class="par"><div class="col"><div class="rot">Antes</div><p>' +
                esc(f["resumen_antes"] or "—") + "</p></div>"
                '<div class="col ahora"><div class="rot">Ahora</div><p>' +
                esc(f["resumen_ahora"] or "—") + "</p></div></div></article>")

    def seccion(titulo, bajada, items, vacio):
        if not items:
            return ('<section><div class="cab"><h2>' + titulo + "</h2></div>"
                    '<p class="vacio">' + vacio + "</p></section>")
        return ('<section><div class="cab"><h2>' + titulo +
                '<span class="n">' + str(len(items)) + "</span></h2></div>"
                '<p class="baj">' + bajada + "</p>" +
                "".join(tarjeta(f) for f in items) + "</section>")

    # Lo que sigue abierto se lista compacto: no es el tema de este reporte,
    # pero esconderlo daria la sensacion de que quedo todo resuelto.
    if abiertos:
        pend = ('<section><div class="cab"><h2>Lo que sigue abierto'
                '<span class="n">' + str(len(abiertos)) + "</span></h2></div>"
                '<p class="baj">No se tocó en esta vuelta. Sigue igual que antes.</p>'
                '<ul class="lista">' + "".join(
                    "<li><b>" + esc(f["titulo"]) + "</b><span>" + esc(f["resumen_ahora"]) +
                    "</span></li>" for f in abiertos) + "</ul></section>")
    else:
        pend = ('<section><div class="cab"><h2>Lo que sigue abierto</h2></div>'
                '<p class="vacio">Ninguna sonda quedó con hallazgos.</p></section>')

    sin = ""
    if igual:
        sin = ('<section><div class="cab"><h2>Sin cambios'
               '<span class="n">' + str(len(igual)) + "</span></h2></div>"
               '<p class="baj">Estas sondas midieron lo mismo en las dos corridas. '
               "<b>No quiere decir que estén bien</b>: quiere decir que ahí no se tocó nada.</p>"
               '<ul class="lista chica">' + "".join(
                   "<li><b>" + esc(f["titulo"]) + '</b><span class="p ' +
                   PILL.get(f["ahora"], "sd") + '">' + esc(f["ahora"]) + "</span></li>"
                   for f in igual) + "</ul></section>")

    extra = ""
    if otros:
        extra = ('<section><div class="cab"><h2>Sondas que cambiaron de set</h2></div>'
                 '<ul class="lista">' + "".join(
                     "<li><b>" + esc(f["titulo"]) + "</b><span>" + VER[f["veredicto"]][0] +
                     "</span></li>" for f in otros) + "</ul></section>")

    return """<!DOCTYPE html>
<html lang="es-AR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Doctor de {{PROYECTO}} — reporte de arreglos</title>
<style>
:root{--txt:#4b5563;--s0:#fff;--s1:#f3f4f6;--az:#1226aa;--azf:#f0f4ff;--azb:#ced2ed;
--lin:#e5e7eb;--ten:#6b7480;--osc:#1A1D26;--ok:#35a339;--okf:#dcfce7;--okb:#b7e3b9;--okt:#1c6b20;
--hal:#f97316;--half:#fef3c7;--halb:#f0d99a;--halt:#8a4b00;--sd:#8390a2;--sdf:#f6f7f9;--sdb:#c0c7d0;
--f:'Segoe UI',-apple-system,Roboto,sans-serif;--m:'Cascadia Mono',Consolas,monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--f);font-size:14px;color:var(--txt);background:var(--s1);line-height:1.55}
.w{max-width:1000px;margin:0 auto;padding:24px 20px 48px}
.top{background:var(--osc);color:#fff;border-radius:8px;padding:22px 26px;margin-bottom:16px}
.top h1{font-size:24px;font-weight:700;color:#fff;margin-bottom:5px}
.top .s{font-size:13px;color:#c0c7d0;max-width:62ch}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.chip{font-family:var(--m);font-size:12px;background:rgba(255,255,255,.08);
border:1px solid rgba(255,255,255,.15);color:#e5e7eb;padding:3px 10px;border-radius:999px}
.kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
.kpi .k{background:var(--s0);border:1px solid var(--lin);border-radius:8px;padding:15px;text-align:center}
.kpi .n2{font-size:30px;font-weight:700;line-height:1.05}
.kpi .l{font-size:11.5px;color:var(--ten);margin-top:4px}
.n2.ok{color:var(--ok)}.n2.hal{color:var(--hal)}.n2.sd{color:var(--sd)}
section{background:var(--s0);border:1px solid var(--lin);border-radius:8px;padding:20px;margin-bottom:12px}
.cab{display:flex;align-items:center;justify-content:space-between;gap:12px}
h2{font-size:16px;font-weight:700;color:var(--osc);display:flex;align-items:center;gap:9px}
h2 .n{font-family:var(--m);font-size:12px;font-weight:700;background:var(--s1);
border:1px solid var(--lin);color:var(--ten);padding:1px 9px;border-radius:999px}
.baj{font-size:12.5px;color:var(--ten);margin:5px 0 14px;max-width:78ch}
.vacio{font-size:13px;color:var(--ten);margin-top:6px}
.t{border:1px solid var(--lin);border-left:3px solid var(--sdb);border-radius:8px;
padding:15px 17px;margin-bottom:11px;background:var(--s0)}
.t.ok{border-left-color:var(--ok);background:linear-gradient(90deg,#f6fdf7,#fff 38%)}
.t.hal{border-left-color:var(--hal);background:linear-gradient(90deg,#fffaf2,#fff 38%)}
.th{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px}
h3{font-size:14.5px;font-weight:700;color:var(--osc)}
.salto{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:9px}
.lado{display:flex;align-items:center;gap:8px}
.fl{color:var(--sdb);font-size:19px;line-height:1}
.cnt{font-family:var(--m);font-size:11.5px;color:var(--ten)}
.delta{font-size:12.5px;color:var(--okt);background:var(--okf);border:1px solid var(--okb);
border-radius:6px;padding:6px 10px;margin-bottom:11px;display:inline-block}
.par{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.col{border:1px solid var(--lin);border-radius:7px;padding:11px 13px;background:var(--sdf)}
.col.ahora{background:var(--azf);border-color:var(--azb)}
.rot{font-size:10px;text-transform:uppercase;letter-spacing:.7px;font-weight:700;
color:var(--ten);margin-bottom:5px}
.col p{font-size:12.5px;line-height:1.55;color:var(--txt)}
.p{display:inline-block;font-size:11px;font-weight:600;padding:2px 10px;border-radius:999px;white-space:nowrap}
.p.ok{background:var(--okf);color:var(--okt);border:1px solid var(--okb)}
.p.hal{background:var(--half);color:var(--halt);border:1px solid var(--halb)}
.p.sd{background:var(--sdf);color:var(--sd);border:1px solid var(--sdb)}
.v{display:inline-block;font-size:11px;font-weight:700;padding:2px 11px;border-radius:999px;white-space:nowrap}
.v.ok{background:var(--okf);color:var(--okt)}.v.hal{background:var(--half);color:var(--halt)}
.v.sd{background:var(--sdf);color:var(--sd)}.v.az{background:var(--azf);color:var(--az)}
.lista{list-style:none}
.lista li{display:flex;align-items:baseline;gap:12px;padding:9px 2px;border-bottom:1px solid var(--lin)}
.lista li:last-child{border-bottom:0}
.lista b{color:var(--osc);font-weight:600;flex:none;min-width:190px}
.lista span{font-size:12.5px;color:var(--ten)}
.lista.chica li{padding:6px 2px}
.nota{border-left:3px solid var(--az);background:var(--azf);padding:11px 14px;
border-radius:0 6px 6px 0;font-size:13px;margin-bottom:16px;max-width:90ch}
footer{text-align:center;font-size:12px;color:var(--sd);padding-top:10px}
@media(max-width:720px){.kpi{grid-template-columns:1fr}.par{grid-template-columns:1fr}
.lista li{flex-direction:column;gap:3px}.lista b{min-width:0}}
@media print{body{background:#fff}section,.t{break-inside:avoid}
.top{background:#fff!important;color:#000;border:1px solid #ccc}
.top h1,.top .s{color:#000}.chip{background:#f3f4f6;color:#333;border-color:#ccc}}
</style></head><body><div class="w">

<div class="top">
  <h1>Reporte de arreglos</h1>
  <div class="s">Qué cambió entre la corrida anterior y la última. No mide cómo está el proyecto:
  mide el movimiento. Para el estado actual está el informe de diagnóstico.</div>
  <div class="chips">
    <span class="chip">antes: FECHA_PREV</span>
    <span class="chip">ahora: FECHA_ACT</span>
    <span class="chip">alcance: ALCANCE</span>
  </div>
</div>

<div class="kpi">
  <div class="k"><div class="n2 ok">N_ARR</div><div class="l">mejoraron</div></div>
  <div class="k"><div class="n2 hal">N_EMP</div><div class="l">empeoraron</div></div>
  <div class="k"><div class="n2 sd">N_IGU</div><div class="l">sin cambios</div></div>
</div>

<div class="nota"><b>Cómo se lee.</b> Una sonda cuenta como <b>mejorada</b> si pasó a OK, o si
bajó la cantidad de hallazgos aunque siga en naranja — ir de doce enlaces rotos a tres es
progreso, y un reporte que sólo mirara el color no lo mostraría.</div>

SEC_MEJOR
SEC_PEOR
SEC_PEND
SEC_IGUAL
SEC_EXTRA

<footer>Generado por doctor/comparar.py — no se envió nada fuera de esta máquina</footer>
</div></body></html>""" \
        .replace("FECHA_PREV", esc(previo.get("fecha", "sin datos"))) \
        .replace("FECHA_ACT", esc(actual.get("fecha", "sin datos"))) \
        .replace("ALCANCE", esc(actual.get("alcance", "proyecto"))) \
        .replace("N_ARR", str(len(mejor))) \
        .replace("N_EMP", str(len(peor))) \
        .replace("N_IGU", str(len(igual))) \
        .replace("SEC_MEJOR", seccion(
            "Lo que se arregló", "Cada una con el estado anterior y el nuevo, y el resumen de "
            "las dos corridas lado a lado.", mejor,
            "Ninguna sonda mejoró entre estas dos corridas.")) \
        .replace("SEC_PEOR", seccion(
            "Lo que empeoró", "Apareció algo que antes no estaba, o creció la cantidad de "
            "hallazgos. Conviene mirarlo antes de seguir.", peor, "") if peor else "") \
        .replace("SEC_PEND", pend) \
        .replace("SEC_IGUAL", sin) \
        .replace("SEC_EXTRA", extra)


def generar(historico, sufijo, hoy):
    """Compara previo vs ultimo y escribe el reporte. Devuelve (ruta, cuenta) o (None, motivo)."""
    prev = _cargar(os.path.join(historico, "previo" + sufijo + ".json"))
    act = _cargar(os.path.join(historico, "ultimo" + sufijo + ".json"))
    if not act:
        return None, "todavia no hay ninguna corrida guardada"
    if not prev:
        return None, ("esta es la primera corrida de este alcance: no hay con que comparar. "
                      "Corré el Doctor de nuevo despues de arreglar algo")
    cuenta, filas = comparar(prev, act)
    destino = os.path.join(historico, "arreglos-" + hoy + sufijo + ".html")
    io.open(destino, "w", encoding="utf-8").write(render(prev, act, cuenta, filas))
    return destino, cuenta
