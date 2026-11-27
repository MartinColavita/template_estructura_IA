---
name: cargar-a-azure
description: >-
  (Avanzada / opcional) Con el MCP de Azure DevOps configurado y un PAT con scope
  de ESCRITURA, crear o actualizar el work item en el board a partir del ticket que
  produjo la skill redactar-tarea (create_work_item / update_work_item). Usar cuando
  se pida "cargá esto a Azure", "creá la tarjeta", "actualizá el work item #ID",
  "subilo al board". Escribir en el board es una acción IRREVERSIBLE: SIEMPRE se
  muestra el diff/preview y se espera un "sí" humano explícito antes de escribir.
  Si no hay MCP o el PAT es de solo lectura, cae a "copiá y pegá a mano" con el
  texto pegable, avisando arriba que no se buscaron duplicados. No entra PHI real; respeta la jerarquía por persona del PAT.
metadata:
  seccion: tickets
---

# Cargar a Azure

> **Tablero local (`DEC-006`):** el board es `backlog/` del módulo, con los mismos GATEs y sin MCP: [antes-de-escribir](references/antes-de-escribir.md).

> **El método de redacción** —las reglas de oro, «Fuentes que deciden», el modo lote y la regla de cardinalidad— está en
> [[redaccion-de-tickets]]: se lee antes de redactar o derivar. Las barreras de escritura, en [[AGENTS]].

Toma el ticket ya redactado (por [[redactar-tarea]]) y lo **crea o actualiza** en
el board vía el MCP de Azure DevOps: **un** work item, nunca un árbol. Escribir en el board
no se deshace solo; por eso el control humano es obligatorio.

## Barreras (no negociables)

Las barreras de escritura son las de [[AGENTS]] («Automatización por MCP — barreras»), que se cargan en cada
sesión: TABLERO, TARJETA CONGELADA (en modo equipo, y se chequea antes que las demás), deduplicación,
confirmación, NIVEL y BORRADO / EDICIÓN DESTRUCTIVA. Valen como están escritas ahí; acá, cómo se aplican.

- **Tablero y tarjeta congelada, antes de escribir.** Antes de `create_work_item`/`update_work_item` se verifica el
  destino ([[tablero-autorizado]]); antes de un `update_work_item` (en modo equipo) se leen `System.IterationPath` y
  `System.State`, y **si no se pueden leer, la tarjeta está congelada**. Lo que se quería cambiar en una congelada se
  ofrece como comentario con el DIFF, vía [[comentar-tarea]] ([[cambios-en-el-backlog]] §4).
- **Un solo work item.** Esta skill crea/edita **el** ítem pedido. Para bajar un
  árbol entero (Épica→Features→Historias) es [[sincronizar-backlog]]; para las Tareas de
  una o más Historias, [[planificar-lote]], que aplica esta skill ítem por ítem con un solo
  cierre. Nunca expandir un pedido de un ítem a varios.
- **Un solo tag temático, techo duro** ([formato-html](references/formato-html.md)).
- **Dedup: el Bloque va en el preview**, con el formato de [[deduplicacion-antes-de-crear]] (consultas · candidatos ·
  veredicto).
- **GATE de EXISTENCIA (bloqueante — encontrar ≠ crear igual).** Si la búsqueda arroja un ticket **equivalente o solapado**, encontrarlo **obliga a frenar**, no a seguir: (1) queda **PROHIBIDO `create_work_item`** para ese ítem; (2) se presenta la lista de existentes (`#ID` + link + estado); (3) se **pregunta explícitamente** si ACTUALIZAR (`update_work_item`) el existente o modificar algo, y se **espera el "sí"**. Jamás se crea un ítem nuevo en paralelo a uno que ya existe. Esta barrera es distinta de "buscar": buscar y encontrar sin frenar es la falla que este gate prohíbe.
- **NIVEL: el tipo y la plantilla.** El **tipo** ya viene decidido en [[redactar-tarea]]
  por su tabla **SELECCIÓN DE TIPO (señal objetiva)**; acá se **verifica que sea
  coherente** y no se cambia en silencio. En modo equipo, la pregunta del GATE es *«¿esto es contexto
  dev/planning y esta Tarea es técnica, para un dev?»* (en modo lote, en el arranque de [[planificar-lote]]);
  sin el «sí», la Tarea se retiene y se propone la Historia que la engloba. Toda Tarea que se cree
  usa la **plantilla detallada** con las cuatro piezas del DoR: [plantilla-de-tarea](references/plantilla-de-tarea.md).
  El default es funcional (Épica/Feature/Historia).
- **Edición destructiva y borrado: cómo caen acá.** Un `update_work_item` que reemplaza contenido ya escrito
  **no** es aditivo: lleva los dos «sí» con el ANTES y el DESPUÉS. *Cerrar una Tarea* (*Resolved*/*Closed*; en modo solo, la propia, con un «sí»): el
  **primer** aviso lleva los pendientes sin resolver de sus comentarios y de su «Datos a confirmar»
  ([[comentar-tarea]] §«Antes de cerrar una Tarea»); si está congelada, la cierra una persona. *Borrar* es sólo
  el reversible (a *Removed* o a la papelera): el permanente no lo hace esta skill nunca, se le pasan los pasos
  al humano.
- **PHI prohibido.** No subir datos personales sensibles/personales reales; van con marcadores
  (`<persona>`, `<documento>`, …).
- **Provenance / autoría.** La escritura queda auditada por el dueño del PAT; no
  usar un PAT ajeno. El token es una **password**: si se expone, se **rota**.
- **No inventar.** Si el ticket tiene un `⚠` **sin declarar** —un valor dudoso afirmado como
  dato, o un pendiente que cambia un test y no figura en «⚠ Datos a confirmar» ni marcado en
  ese test—, no se carga: se vuelve a [[redactar-tarea]] a cerrarlo. Un `⚠` **declarado** (en
  «Datos a confirmar», con su pregunta o su `P-nnn`, su recomendación y la marca en el test)
  es un punto abierto a la vista, y se carga ([[AGENTS]]).

## Precondiciones (verificar antes de intentar)

MCP configurado y PAT propio con escritura; si no, **no se escribe**: texto pegable con el aviso de dedup
y **SIN DATOS** en el Bloque de GATES. Antes de intentar: [antes-de-escribir](references/antes-de-escribir.md).

## Flujo

### 1. Confirmar la operación
**Primero, verificar el tablero autorizado** ([[tablero-autorizado]]): el destino debe ser org `{{AZURE_ORG}}` / proyecto `{{AZURE_PROYECTO}}` / team `{{AZURE_TEAM}}`. Si el pedido apunta a otro tablero o no se puede determinar, **frenar** con la advertencia — no se escribe.

Alta o edición (leyendo antes la tarjeta; congelada no se edita): [antes-de-escribir](references/antes-de-escribir.md).

### 1b. Buscar duplicados (obligatorio, en toda alta) — con evidencia
Por **tag temático + documento fuente + objetivo**, comparando objetivo y no título; **ante la duda, es
duplicado**. Cómo buscar y qué hacer con un equivalente: [dedup-y-equivalentes](references/dedup-y-equivalentes.md).

### 1c. Auditar calidad del equivalente (si 1b encontró uno)
Si 1b encontró uno, antes del preview: §1c de [dedup-y-equivalentes](references/dedup-y-equivalentes.md).

### 2. Preview + confirmación humana (obligatorio)
Mostrar exactamente lo que se va a escribir:
- **Bloque de dedup**, arriba de todo; sin él **no se escribe** ([dedup-y-equivalentes](references/dedup-y-equivalentes.md)).
- **Alta:** tipo, título, y cada campo con su valor.
- **Edición:** campo por campo, **valor actual → valor nuevo**.
- **Tag y HTML:** antes de mostrarlo, [formato-html](references/formato-html.md).

### 2a. Bloque de GATES (obligatorio, arriba de todo) — el gate que no deja rastro no es gate

El preview arranca con esta tabla, **llena**, antes que cualquier otra cosa. Sin ella el
preview es inválido y **no se escribe**, igual que sin el Bloque de dedup.

| Gate | Estado | Evidencia (una línea, concreta) |
|---|---|---|
| **Tablero autorizado** | OK / FRENA / SIN DATOS | org · proyecto · team verificados contra [[tablero-autorizado]] |
| **Tarjeta congelada (solo ediciones)** | OK / FRENA / SIN DATOS / no aplica | **Ruta de iteración** y **Estado** leídos de la tarjeta. En un sprint y distinto de `New` → FRENA. Sin poder leerlos → SIN DATOS: se trata como congelada y no se edita. Con `DEC-006` fijada en modo solo, **no aplica** |
| **NIVEL (solo Tareas)** | OK / FRENA | **La frase textual del humano**, de esta conversación y sobre esta Historia, que declara contexto dev/planning (en modo lote: la respuesta del arranque a la pregunta que nombró esta Historia) |
| **Dedup** | OK / FRENA / SIN DATOS | Consultas corridas · candidatos `#ID` · veredicto por candidato (ver §1b) |
| **Confirmación** | PENDIENTE | Se marca OK recién con el "sí" sobre **el contenido mostrado abajo**, no sobre la propuesta |

**Tres estados, no dos: OK · FRENA · SIN DATOS.** Una fila sólo dice OK con su evidencia a la
vista, y la evidencia no se escribe de memoria:

- **Dedup y Tarjeta congelada leen el tablero.** Sin MCP, o sin haber podido consultarlo, van
  **SIN DATOS** —nunca «OK · 0 candidatos», nunca «OK · no está congelada»—, y con una fila en
  SIN DATOS **no se escribe**. Si se entrega el texto para pegar a mano, arriba de todo va:
  *«No busqué duplicados: buscalos vos en el tablero antes de pegar.»*
- **NIVEL da OK sólo con una cita textual** (con `DEC-006` fijada en modo solo, la fila dice **no aplica**): la frase del humano, **de esta conversación**, que
  declara contexto dev/planning. El pedido mismo («creá las tareas») **no es** esa frase. Sin la
  cita, la fila dice FRENA, se hace la pregunta del nivel y **el turno termina ahí**: la Tarea no
  se redacta en el mismo turno, ni «de ejemplo», ni como molde vacío.

**El gate de NIVEL no se hereda entre Historias.** Modo lote, otros casos de llenado y por qué existe la
tabla: [bloque-de-gates](references/bloque-de-gates.md).

### 2b. Checklist de cierre (MECÁNICO, obligatorio en toda Tarea) — antes del "sí"

Los defectos que se cuelan no son de criterio: son **de conteo**, y por eso se revisan
contando, no releyendo. Esta tabla se **llena y se muestra dentro del preview**; si una
fila da `NO`, se corrige **antes** de pedir confirmación. Un preview de Tarea sin esta
tabla es inválido, igual que sin el bloque de dedup.

**Las filas las llena `bin/auditar-tarea.py`**; cómo correrlo y las once filas: [checklist-de-cierre](references/checklist-de-cierre.md).

### 2c. Confirmación

Luego **preguntar y esperar un "sí" explícito**. El "sí" confirma el contenido, el
resultado de dedup **y** el checklist de cierre. Sin confirmación, no se llama a ninguna
herramienta de escritura. Escribir en el board es **irreversible** desde esta skill (no
hay "deshacer").

En un lote de [[planificar-lote]]: [modo-lote](references/modo-lote.md).

### 3. Escribir
Con el "sí" dado, ejecutar `create_work_item` / `update_work_item`. Una sola
operación por confirmación; no encadenar varias escrituras sobre un único "sí" (salvo el
lote confirmado en el cierre de [[planificar-lote]], que escribe exactamente su tabla).

**Parent y Related, desde la hija; nunca se edita la Historia para colgarle la Tarea**: [parent-y-related](references/parent-y-related.md).

### 3b. Segundo chequeo: opcional, a pedido

Al reportar el alta se ofrece en una línea; si se pide: [auditorias-a-pedido](references/auditorias-a-pedido.md).

### 4. Reportar
Devolver el **ID/URL** del work item creado o actualizado y qué campos quedaron
escritos. Ir al grano (silencio al entregar). Registrar **una fila** en
[[historial/INDICE]] (tema, `#ID`, documento fuente si aplica, resumen de una línea,
puntos): log resumido e indexable, sin copiar el cuerpo del ticket. El `.md`
detallado solo si se promueve a `gold`.

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| [antes-de-escribir](references/antes-de-escribir.md) | Tablero local; antes de intentar; alta o edición; setup |
| [dedup-y-equivalentes](references/dedup-y-equivalentes.md) | Al buscar duplicados; con un equivalente |
| [bloque-de-gates](references/bloque-de-gates.md) | Una fila no simple del Bloque de GATES; NIVEL en lote |
| [formato-html](references/formato-html.md) | Antes de mostrar el preview |
| [plantilla-de-tarea](references/plantilla-de-tarea.md) · [checklist-de-cierre](references/checklist-de-cierre.md) | En toda Tarea |
| [modo-lote](references/modo-lote.md) | Dentro de un lote |
| [parent-y-related](references/parent-y-related.md) | Al escribir un alta con Parent o Related |
| [auditorias-a-pedido](references/auditorias-a-pedido.md) | Si se pide una auditoría o [[analizar-tareas]] |
| [ejemplo](references/ejemplo.md) | Para ver el flujo aplicado |
