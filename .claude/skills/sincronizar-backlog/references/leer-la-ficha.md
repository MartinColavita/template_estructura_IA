# Leer la ficha: precondición y paso 1

Parte de la skill `sincronizar-backlog`: se lee cuando se verifica que la ficha se puede derivar y cuando se extrae su bloque de derivación (paso 1).

## Precondición: ficha con bloque de derivación enumerado y cerrado

1. **Ficha con bloque de derivación enumerado y cerrado.** Solo se derivan al
   backlog fichas que traen el bloque `## Derivación a backlog` con los
   `Slices [S-nn]`, `Capacidades [C-nn]` y `Flujos [F-nn]` **enumerados y
   cerrados** (lo produce la curación; ver [[organizacion-y-trazabilidad]] §5), más
   reglas `[RN-…]` numeradas y etiqueta temática. **Si falta el bloque enumerado, o
   hay `⚠ (pendiente)`, NO se deriva:** se frena y **primero** se
   cierra/enumera en el Cerebro (`cerebro-digital/`) — no se cuenta la ficha «a
   ojo» sobre la prosa. **Integridad referencial:** cada `[C-nn]` debe referenciar un
   `[S-nn]` existente y cada `[F-nn]` un `[C-nn]` existente; si hay una referencia
   colgada (un Parent inexistente), tampoco se deriva — se frena y se pide cerrarla.
   (Por qué el gate: [[criterios-aceptacion-gherkin]] §8 — entra-basura = sale-basura.)
   El estado de la ficha (`F-Draft`/`F-Verified`) es un metadato del ciclo de vida
   general del Cerebro; **no** es condición para derivar — la confirmación humana
   simple del paso 4 (¿creo estos work items?) es la que habilita la escritura.

## 1. Leer la ficha y su bloque de derivación

Leer la ficha del Cerebro Digital indicada (archivo de `cerebro-digital/`). Extraer
el **bloque `## Derivación a backlog`** — los `Slices [S-nn]`, `Capacidades [C-nn]` y
`Flujos [F-nn]` enumerados, que **fijan el árbol** —, más las reglas `[RN-…]`,
etiqueta temática, documento fuente y cualquier `⚠ (pendiente)`. **Si el bloque
enumerado no está** (o hay pendientes que afectan el alcance), **frenar** y pedir
cerrarlo/enumerarlo en el Cerebro (`cerebro-digital/`) — no se deriva sobre prosa
sin enumerar. **Visibilidad (no bloquea):** si la ficha tiene pendientes sin resolver que **no**
afecten el bloque de derivación, avisarlos igual al proponer el árbol. **Buscar las
cuatro formas que conviven hoy en el Cerebro**, no una sola: `## Dudas y Preguntas`,
`## Dudas y preguntas` (minúscula), `## Pendientes` y cualquier `- [ ]` o `⚠` suelto.
Buscar un solo literal hace que el aviso reporte **cero** sobre una ficha que sí tiene
pendientes abiertos — y el humano confirma el árbol sin verlos — no frena la derivación, pero
el humano debe verlo antes de confirmar.
