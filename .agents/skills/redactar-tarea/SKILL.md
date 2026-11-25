---
name: redactar-tarea
description: >-
  Convertir un ticket POBRE (texto suelto, "ver adjunto", un link, o el ID de una
  tarjeta de Azure DevOps) en un work item PROFESIONAL, detallado y listo para
  pegar o crear en el board. Usar cuando se pida "redactá/mejorá esta historia",
  "escribí el ticket", "hacé los criterios de aceptación", "pasá esto a Gherkin",
  "convertí este bug en un ticket", "está lista para el sprint / cumple el DoR",
  "/redactar-tarea". Decide primero el TIPO (Historia / Tarea / Bug / Habilitador
  técnico / Spike). TODO en español (Argentina), Gherkin incluido
  (Dado/Cuando/Entonces). PHI PROHIBIDO (marcadores). NO inventa: lo faltante se
  marca "pendiente" y se pregunta, esperando confirmación humana. SOLO redacta:
  no escribe en Azure (para eso está la skill cargar-a-azure).
---

# Redactar tarea

> **Tablero local (`DEC-006`):** si el proyecto usa el tablero local, «el board» es `cerebro-digital/<modulo>/backlog/`
> y se opera con `bin/tablero-local.py`, con los mismos GATEs y sin MCP (detalle: `backlog/README.md` del módulo).
> Con Azure DevOps, Jira u otro tablero, las operaciones se traducen con la tabla de `integracion-azure-mcp/00-index.md`.

> **El método de redacción** —las reglas de oro, «Fuentes que deciden», el modo lote y la regla de cardinalidad— está en
> [[redaccion-de-tickets]]: se lee antes de redactar o derivar. Las barreras de escritura, en [[AGENTS]].

Convierte una entrada pobre en un work item profesional, en español, listo para
pegar campo por campo en el board. Esta skill **solo redacta**: deja el texto
pegable. Escribir en el board es otra skill: [[cargar-a-azure]].

## Regla de oro (cultura del equipo)

- **NO INVENTAR.** Lo que no está confirmado se marca como **pendiente** y se
  pregunta al usuario. Nunca completar datos de negocio, actores, reglas o
  valores por suposición.
- **Redactá EXACTAMENTE lo pedido: un ítem.** Si piden una tarea, redactás **una**;
  no generás varias historias ni un árbol. Bajar una ficha/módulo entero al board
  es otra skill ([[sincronizar-backlog]]).
- **PHI PROHIBIDO.** Nada de datos personales sensibles o personales reales. Usar marcadores:
  `<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`, `<telefono>`, `<direccion>`.
- **Respetar la provenance.** Si hay fuentes con distinta autoridad, gana la de
  mayor jerarquía; ante conflicto, se anota el desvío, no se elige en silencio.
- **Lo definido no se pregunta.** Lo que ya definen el Cerebro, la maqueta vigente o una
  respuesta anterior del humano se aplica y se lista; una recomendación técnica clara, también
  ([[redaccion-de-tickets]] §«Fuentes que deciden»). Lo que queda se pregunta **todo junto**, numerado y con
  una recomendación por pregunta.
- **Un solo tag temático, techo duro.** El campo Etiquetas lleva **una** etiqueta
  (el tema, sin prefijo, kebab-case) — nunca el nombre del producto/repo (`<producto>`,
  `modulo-ejemplo`) ni el slice/sub-flujo como tag aparte. Detalle:
  [[organizacion-y-trazabilidad]] §1.
- **Silencio al entregar.** Al terminar, devolver el ticket pegable e ir al grano;
  sin relleno ni auto-elogio.
- **Español (Argentina)** en todo, incluido el Gherkin.

## Flujo

### 1. Conseguir la entrada
- Si el usuario pasó **texto**, se trabaja con ese texto.
- Si pasó un **ID de Azure** (p. ej. `#12345`), leerlo **solo lectura** con el MCP
  (`get_work_item`, y `get_work_item_comments` si hace falta el hilo). Ver
  [[integracion-azure-mcp/00-index]]. Si no hay MCP configurado, pedir al usuario
  que pegue el contenido.

### 2. Decidir el TIPO primero
Antes de redactar, clasificar. Es la decisión que gobierna la plantilla y los campos
(complementa la Regla de oro «el tipo se decide PRIMERO»). Para que el **mismo insumo
dé siempre el mismo tipo** — y no varíe según el LLM — elegí el **primer renglón cuya
*señal objetiva* se cumpla**; la señal es verificable, no depende de gusto:

| Tipo | Señal objetiva (verificable) | Plantilla |
|---|---|---|
| Bug | Comportamiento **observado ≠ esperado** sobre algo **YA existente**, donde el "esperado" es un comportamiento **previamente especificado / una regla ya definida** (regresión o incumplimiento) — **NO** una mejora nueva; se pueden escribir esperado, obtenido y pasos para reproducir. *(Una mejora sobre lo existente es Historia, no Bug.)* | [[plantillas/bug]] |
| Historia de usuario | **Flujo de negocio con valor para un rol** identificable (incluye **mejoras/altas** de comportamiento); se escribe "Como `<rol>` quiero `<qué>` para `<para qué>`" y se verifica con criterios de aceptación (Gherkin). | [[plantillas/historia-de-usuario]] |
| Habilitador técnico / Spike | Trabajo técnico **sin valor de usuario directo** (deuda, infra, migración) **y que NO es el desglose de una Historia** (eso es Tarea), **o** investigación **time-boxed** con una pregunta a responder (Spike); no produce comportamiento de negocio observable. | [[plantillas/habilitador-tecnico]] |
| Tarea (dev/planning) | **Desglose técnico de UNA Historia** ya existente (con Parent Historia); sin valor de usuario propio. **Solo** con contexto **dev/planning declarado** (ver nota abajo). | [[plantillas/tarea]] |
| Épica / Característica | Agrupadores de alcance mayor; **no se eligen para un ítem suelto** — salen de la derivación de cardinalidad (`[S-nn]`→Épica, `[C-nn]`→Feature). | [[plantillas/epica]] · [[plantillas/caracteristica]] |

Si aun así el tipo es ambiguo, proponer uno y **preguntar** antes de seguir.

> **Tarea = momento dev/planning.** Con `DEC-006` fijada en modo solo no se pregunta: quien la pide es quien la desarrolla, y se redacta con la plantilla detallada. En modo equipo, o con la DEC en `⚠`, si el pedido es **crear una Tarea nueva** y **no** viene declarado un contexto de desarrollo/planning explícito (p. ej. "soy dev", "estamos en planning"), **no la cierres como Tarea**: proponé la **Historia** que la engloba, o pedí esa declaración. **El pedido mismo no es la declaración**: «desglosá / creá las tareas de la Historia #NNNN» no alcanza. La pregunta del nivel (o la propuesta de la Historia) **cierra el turno**: no se adjunta un borrador de la Tarea «mientras tanto», **ni el molde vacío** de cómo quedaría. **Corregir una Tarea que ya existe no pasa por acá**: su nivel ya se decidió al crearla (ver el arreglo que pide [[auditar-tarea]]). El default es funcional (hasta Historia); las Tareas técnicas las arma Desarrollo.

### 3. Redactar según la plantilla
Tomar la estructura del dominio y las convenciones de [[conocimiento/00-index]]
(glosario, roles, DoR/DoD, estimación, RNF, antipatrones) y llenar la plantilla
del tipo elegido.

Lo que lleva cada tipo —los 4 bloques y las Notas para QA de la Historia, los tres bloques del Bug, el
detalle de Tarea/Habilitador sin inflar una tarea chica—: `references/bloques-por-tipo.md` (leerlo antes
de redactar).

### 3.1 DoR de la Tarea — "lista para desarrollar" (bloqueante)
Una **Tarea** de capa `api`/`application`/`domain` (algo que otro código va a **llamar**)
**no se entrega como "lista"** sin estas cuatro piezas cerradas:
**Contrato técnico (entrada/salida) cerrado** (OpenAPI en YAML para capa `api`) · **Especificación
cerrada (SDD)** con la tabla de Escenarios del padre y qué test cubre cada uno · **Lista de "Tests a
escribir PRIMERO"** numerada, una línea por test, 30 o menos · **Bloque "Modos de falla evaluados"**,
cada familia cubierta o descartada con su motivo, nunca ausente. Las cuatro, en detalle (y la exención
parcial de la Tarea de front): `references/dor-tarea.md` (leerlo antes de redactar o corregir una Tarea).

**Dos chequeos de coherencia, además, antes de dar la Tarea por lista:**
- Si el Alcance técnico dice «Requiere test de integración: **sí**», tiene que haber
  **un test de integración en la lista, una subtarea que lo escriba y un ítem en el DoD**.
  Declararlo y no pedirlo deja que el dev cierre con puros dobles.
- **El campo Esfuerzo original nunca queda nulo en silencio**: si no hay estimación, va **0**
  en el campo **y** la pregunta en «Datos a confirmar». Un campo vacío no se distingue de
  «nadie lo miró» y no suma al sprint.

La skill **GENERA las cuatro** con lo que el usuario/dev aporta; **no** deja el molde de la
plantilla vacío ni con placeholders. Donde falte un dato que la IA **no puede saber** (una
regla de negocio que no está en el Cerebro, un comportamiento ambiguo), se saca como
**pregunta `⚠ pendiente`** —nunca se inventa— y queda **declarada** en «Datos a confirmar», con
su recomendación. Un `⚠` declarado **no** saca a la Tarea de «lista para desarrollar»
(decisión de diseño del template): se desarrolla lo que no depende de él, y ese punto queda como
pendiente a confirmar en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar»). Lo que sí la deja **NO lista** es que falte una de
las cuatro piezas.

### 3.2 Reparar una Historia existente

Cuando [[auditar-historia]] la marcó CON HUECOS, esta skill cierra su Gherkin: se reescriben sólo
los bloques observados, y lo que la IA no puede saber va como pregunta `⚠`, nunca se completa. El
procedimiento: `references/reparar-historia.md` (leerlo antes de reparar una Historia).

### 4. Marcar lo pendiente y preguntar
Todo dato faltante se deja como `⚠ pendiente: <qué falta>` **dentro** del ticket
y se lista aparte como preguntas al usuario. **No** se avanza a un ticket "cerrado"
inventando lo que falta. Esperar la confirmación humana con los datos. Las preguntas van
**todas juntas**, numeradas y con una recomendación cada una; en modo lote van al arranque o al
cierre de [[planificar-lote]], nunca en un turno por pregunta.

### 5. Entregar pegable
Salida final: los campos separados y rotulados, alineados con el mapa de campos
del board ([[checklists/mapa-campos-azure]]), listos para copiar uno por uno.

**Descripción, Criterios de aceptación y Pasos para reproducir van en HTML**, con el
esqueleto del tipo que está en [[checklists/mapa-campos-azure]]: `<h3>` con `<hr>` entre
secciones, `<ul>`/`<ol>`, `<table>`, `<pre>` para el contrato, palabras clave del Gherkin en
`<b>` y `&lt; &gt;` en los marcadores. **Nunca markdown**: ni bloques con tres comillas
invertidas, ni `- [ ]`, ni tablas con `|`. Azure los muestra literales y la tarjeta queda
ilegible. En el chat se puede mostrar además cómo se va a ver, pero lo que se pega es el HTML.
**Vale también para los fragmentos**: si se corrige una tarjeta existente, lo que se agrega va
en HTML listo para insertar —una fila `<tr>…</tr>`, un `<li>…</li>`—, nunca una fila con `|`.

**Autochequeo antes de entregar** (mecánico; si uno falla, se corrige antes de mostrar):
una sola etiqueta · HTML sin markdown · cada `[RN-…]` existe y dice lo que se le atribuye (si el pedido
choca con una regla, se frena y se pregunta) · se leyó la tarjeta que se corrige · lo que no se sabe va
`⚠`, nunca un código o un número de regla que suene bien · no existe ya ([[deduplicacion-antes-de-crear]])
· el tipo sale de la señal. Los siete, en detalle: `references/autochequeo.md` (leerlo antes de entregar).

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| `references/bloques-por-tipo.md` | Antes de redactar: qué lleva cada tipo de ticket |
| `references/dor-tarea.md` | Antes de redactar o corregir una Tarea: las cuatro piezas del DoR y la exención parcial de la Tarea de front |
| `references/autochequeo.md` | Antes de entregar: los siete chequeos mecánicos |
| `references/reparar-historia.md` | Antes de reparar una Historia que [[auditar-historia]] marcó CON HUECOS |
| `references/ejemplo.md` | Para ver un ticket pobre convertido en uno pegable |

## Contexto adicional

- Checklist DoR/DoD y antipatrones: [[conocimiento/00-index]]
- Ejemplos antes → después: [[ejemplos/00-index]]
