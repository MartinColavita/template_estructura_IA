# Misión: corregir {clave} — {titulo}

Sos quien redactó este ítem, o lo tomás porque esa persona ya no está y **vos no lo
auditaste** (planificar-lote, fase 3). Aplicás los **F** de la auditoría, y nada más.

- **Ítem:** {clave} · {tipo} · {accion} · padre {padre}

## Leé estos archivos, y sólo estos

{leer}

## Cargá estas skills (no se heredan)

{skills}

## Escribí sólo esto

{salida}

## Cómo

1. Los F son los renglones `- F-n · …` de la sección `## F` de `{informe}` (y cualquier
   renglón que empiece con `F:`). Aplicás cada uno tal como lo escribió el auditor, con su
   fuente. Un F sin la fuente escrita no se aplica: es una P.
2. Las P (sección `## P`, o renglones `P:`) no las resolvés: quedan como `⚠` declarado en
   «⚠ Datos a confirmar», con su recomendación, y van a tu informe.
3. No cambiás nada que ningún F pida. Si cambia el título de una Historia, avisalo: sus
   Tareas se re-auditan.
4. Lo que todavía no existe sigue como `[T-nn]` / `[H-nn]`.
5. Al cambiar el archivo, la auditoría anterior deja de valer (su huella ya no coincide): se
   vuelve a correr `lote.py auditar` y la re-audita otro agente.

## Lo que NO hacés

- No escribís en el tablero ni en el Cerebro, ni tocás archivos que no estén arriba.
- No le preguntás al humano.
- No te re-auditás: la re-auditoría la hace otro agente, una sola vez, sólo de lo que cambió.

## Idioma

Respondé y escribí todo en español (Argentina): el informe, los archivos y cualquier mensaje.

## Informe (máximo {informe_max_palabras} palabras)

F aplicados (número · qué cambió) · F no aplicados y por qué · P que quedaron.
