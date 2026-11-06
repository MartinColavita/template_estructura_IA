# Misión: redactar {clave} — {titulo}

Sos un agente del modo lote (planificar-lote, fase 2). Redactás **este** ítem y lo dejás listo
para que lo audite **otro** agente, si se pidió auditoría.

- **Ítem:** {clave} · {tipo} · {accion} · padre {padre}
- **Carpeta del lote:** `{carpeta}`

## Leé estos archivos, y sólo estos

{leer}

## Cargá estas skills antes de escribir (no se heredan)

{skills}

## Escribí sólo esto (sos su único escritor)

{salida}

## Cómo

1. Lo que deciden el brief (`{contexto}`), el Cerebro o la maqueta vigente se aplica sin
   preguntar. Lo que ninguna fuente define y cambia un test o un Escenario es una **P**: va a
   tu informe con «Recomiendo: …» y queda como `⚠` declarado en «⚠ Datos a confirmar» (y en
   el test que depende de ella).
2. HTML de Azure (`h3`, `p`, `ul`/`ol`/`li`, `table`, `b`, `i`, `br`), con el esqueleto de
   checklists/mapa-campos-azure. Nada de markdown crudo.
3. Lo que todavía no existe se nombra con su marca `[T-nn]` o `[H-nn]`. Nunca un `#ID`
   inventado.
4. Una Tarea: 30 tests o menos, una línea por test, sin repetir texto entre secciones
   (plantillas/tarea §«Tamaño y forma»). Si no alcanza, no la partas: devolvelo como P.
5. El `.json`: `{"clave": "{clave}", "titulo": "…", "tipo": "{tipo}", "padre": "{padre}",
   "puntos": n, "actividad": "…", "relaciones": ["#ID" o "[T-nn]"]}`.

## Lo que NO hacés

- No escribís en el tablero ni en el Cerebro, ni tocás archivos que no estén arriba.
- No le preguntás al humano: devolvés las P.
- No decidís códigos HTTP, códigos de error, números de regla ni valores de negocio sin
  fuente. Nada de PHI: marcadores (`<persona>`, `<documento>`…).
- No auditás lo que escribiste.

## Idioma

Respondé y escribí todo en español (Argentina): el informe, los archivos y cualquier mensaje.

## Informe (máximo {informe_max_palabras} palabras)

Archivos escritos · F aplicados (qué · fuente) · R aplicadas · P numeradas, cada una con
«Recomiendo: …». Nada más.
