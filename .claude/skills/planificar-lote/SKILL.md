---
name: planificar-lote
description: >-
  (Modo lote / planificación rápida) Derivar en una sola pasada, con agentes en
  paralelo, las Historias de una ficha del Cerebro, las Tareas de varias Historias,
  o las dos cosas, con SOLO DOS turnos humanos: el ARRANQUE (alcance + nivel + todas
  las dudas sin fuente, juntas y con recomendación) y el CIERRE (una tabla con el lote
  entero y UN "sí" que escribe todo: altas, relaciones, ediciones de tarjetas en New,
  sellos de auditoría si se pidió alguna, y la traza en el Cerebro). Lo que definen la
  maqueta vigente o el Cerebro se aplica sin preguntar y se lista. Las auditorías son
  OPCIONALES: corren sólo si se piden (entonces las corre un agente distinto, en
  paralelo) y nunca frenan una fila. Los GATES duros (tablero, nivel, dedup, tarjeta
  congelada, PHI, borrado) siguen iguales. Usar cuando se pida "armá las tareas de
  estas historias", "planificación con los devs", "derivá las historias de la ficha",
  "bajá el lote", "/planificar-lote". NO inventa. Español (Argentina).
---

# Planificar lote

> **Tablero local (`DEC-006`):** si el proyecto usa el tablero local, «el board» es `cerebro-digital/<modulo>/backlog/`
> y se opera con `bin/tablero-local.py`, con los mismos GATEs y sin MCP (detalle: `backlog/README.md` del módulo).
> Con Azure DevOps, Jira u otro tablero, las operaciones se traducen con la tabla de `integracion-azure-mcp/00-index.md`.

> **El método de redacción** —las reglas de oro, «Fuentes que deciden», el modo lote y la regla de cardinalidad— está en
> [[redaccion-de-tickets]]: se lee antes de redactar o derivar. Las barreras de escritura, en [[AGENTS]].

Baja **muchos ítems de una vez** —las Historias de una ficha, las Tareas de varias
Historias, o las dos cosas— con dos turnos humanos en lugar de decenas.

## Lo que no cambia (ver [[AGENTS]])

- **Tablero autorizado.** Sin MCP, los GATES que leen el tablero dicen **SIN DATOS** y no se escribe.
- **Dedup por ítem.** Un equivalente **bloquea el alta** de ese ítem; un candidato dudoso es pregunta del arranque.
- **Tarjeta congelada** (en un sprint y distinta de `New`): sólo comentario.
- **PHI prohibido**, un solo tag temático, HTML.
- **El lote no borra ni cierra** tarjetas. Eso va fuera del lote, con el GATE de [[AGENTS]] (dos «sí»; en modo solo, cerrar la propia Tarea, uno).
- **Las auditorías son opcionales** (decisión de diseño del template): [[auditar-historia]], [[auditar-tarea]] y [[analizar-tareas]] corren **sólo si se piden** —en el pedido o en la respuesta del arranque—, y entonces las corre un agente distinto del que redactó. **Nunca frenan una fila**: lo que encuentren va como **pendiente a confirmar** en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar»), y el sello no es requisito para desarrollar.
- **No inventar.** Lo que ninguna fuente define se pregunta en el arranque o queda como `⚠` declarado.

## Barreras propias

- **Nada se escribe en el tablero ni en el Cerebro antes del "sí" del cierre.** Antes sólo se escribe en `borrador/`.
- **El "sí" no se generaliza** al lote siguiente.
- **Quien redacta no audita**, y **quien audita no corrige**: corrige el que redactó (cuando se pidió auditoría).
- **Un F sin su fuente escrita es un P.** Decidir en silencio sigue prohibido; lo que cambia es que se decide con la fuente a la vista y se lista.

## Qué se decide sin preguntar (fuentes, en orden)

| # | Fuente | Qué decide |
|---|---|---|
| 1 | **El Cerebro** (`[RN-…]`, `[DEC-…]`, pendientes resueltos, decisiones del día en la ficha) | Reglas, estados, datos, decisiones ya tomadas |
| 2 | **La maqueta vigente**: la que la ficha cita en `fuente_maqueta` | Comportamiento de pantalla: textos, botones, avisos, estados vacíos, formatos, orden de campos, paginación. Una maqueta «propuesta» o que ninguna ficha cita no decide. **Si contradice una regla del Cerebro, gana el Cerebro** y se avisa en el cierre |
| 3 | **Lo que el humano ya respondió**, en esta conversación o en el arranque | Lo respondido no se vuelve a preguntar |
| 4 | **Los contratos ya cargados** (Tareas hermanas, el back que consume el front) | Nombres, códigos, formas |
| 5 | **La recomendación técnica** de la IA, cuando hay una clara | Partición, nombres internos (clases, rutas, nombres de test), patrones del esqueleto. Se aplica y se lista para que el humano la vete. **No decide** códigos HTTP, códigos de error, números de regla ni valores de negocio, y no se guarda en el Cerebro como decisión |

**Se pregunta sólo:** (a) un dato duro sin fuente (`#ID`, versión, valor real, código de un
sistema externo); (b) una regla o un comportamiento que ninguna fuente define **y que cambia
un test o un Escenario**; (c) un choque entre dos fuentes del mismo rango.

## Las cinco fases

### Fase 0 — Preparar (la IA sola; en paralelo)

0. **Lo primero:** `python bin/lote.py preparar <tema> --ficha <ficha>` y `python bin/lote.py tiempos <carpeta> preparar inicio`, así la fase se mide entera. **Antes de seguir, leé `references/script-y-archivos-del-lote.md`** (formato de los ítems, tiempos y archivos).
1. Verificar el tablero autorizado y leer las tarjetas involucradas (Estado, Ruta de iteración, Asignado).
2. Leer las fuentes: la ficha y su bloque de derivación, la maqueta, las reglas, los contratos ya cargados.
3. **Dedup por ítem** ([[deduplicacion-antes-de-crear]]: tag + documento fuente + objetivo). El resumen de cada fila va con
   `lote.py item --dedup` y dice cuántas consultas corrieron, con cada candidato como `#ID=veredicto` (`distinto`,
   `solapa`, `equivalente`, `equivalente-cerrado` o `duda`): `"3 consultas · 0 cand."` o
   `"3 consultas · 1 cand. · #125100=distinto"`; en una fila que no es alta, `"no aplica"`. Un candidato `equivalente`,
   `solapa` o `duda` bloquea el alta, y se pregunta en el arranque; uno `equivalente-cerrado` no: deriva a un evolutivo
   ([[deduplicacion-antes-de-crear]]).
4. **Tareas, sólo si se pidió auditoría:** correr [[auditar-historia]] sobre cada Historia padre, **un agente por Historia, en paralelo**. Si no se pidió, este paso no corre.
5. Clasificar cada duda —propia o, si corrieron, de las auditorías— en **F** (la resuelve una fuente: se anota cuál y el arreglo exacto), **R** (recomendación técnica clara) o **P** (necesita a una persona).
6. La carpeta del lote, cómo se anota cada ítem y qué va en `CONTEXTO.md`: `references/script-y-archivos-del-lote.md`.

### Fase 1 — Arranque (UN turno humano)

Un solo mensaje, en criollo:

1. **Alcance:** qué se va a crear o editar, una línea por ítem.
2. **Nivel**, si hay Tareas y el proyecto es de equipo (con `DEC-006` fijada en modo solo no se pregunta, porque quien pide la Tarea es quien la desarrolla; con la DEC en `⚠`, se pregunta): *«¿Estas Tareas son técnicas, para los devs (contexto dev/planning)? Vale para las Historias #A, #B y #C.»* Una Historia que todavía no existe se nombra con su `[H-nn]` y su título.
3. **Duplicados:** candidatos encontrados (o «0 candidatos en N consultas») y qué se propone.
4. **Preguntas:** todas las P, numeradas, cada una con «Recomiendo: …».
5. Una línea: *«Lo demás sale de la maqueta y del Cerebro; te lo listo en el cierre.»*
6. Una línea, sin pregunta: *«No corro auditoría salvo que me la pidas.»* (Si ya la pidieron en el pedido, se dice que va a correr.)

El mensaje **cierra el turno**: no se redacta nada antes de la respuesta. Si el lote **no tiene
Tareas en modo equipo (la pregunta del nivel), ni preguntas, ni duplicados dudosos**, el arranque no se muestra y
se pasa a la fase 2.

La respuesta vale entera: «dale», «tu recomendación» o «sí a todo» acepta las recomendaciones
de las preguntas numeradas. **La pregunta del nivel no lleva recomendación y no se da por
contestada con «tu recomendación»**: vale un «sí», «dale» o «sí a todo» dado a ese mensaje.
Una pregunta que quedó sin contestar **no se vuelve a hacer en otro turno**: queda como `⚠`
declarado en la tarjeta, con su recomendación, y se vuelve a listar en el cierre. **Dos
excepciones, porque son GATES:** sin respuesta al nivel, las Tareas de esas Historias **no se
redactan** (el lote sigue sin ellas); y un duplicado dudoso sin respuesta **no se crea**: sale de
la tabla y va al cierre como pregunta.

### Fase 2 — Redactar (un agente por Historia, en paralelo)

- La misión, la salida, los `[T-nn]`, el tamaño de las Tareas, el orden Historia → Tareas, el chequeo §2b y qué pasa sin sub-agentes: `references/fase-2-redactar.md`.
- **Los agentes no le preguntan al humano.** Lo que no pueden resolver lo devuelven como P en su reporte.
- Hasta 8 agentes a la vez. Un archivo, un solo escritor.

### Fase 3 — Auditar (OPCIONAL: sólo si se pidió; agentes distintos de los que redactaron, en paralelo)

**Si nadie pidió auditoría, esta fase no corre** y se pasa al cierre: la columna «Auditoría»
dice *no se pidió* y ninguna fila se frena por eso. Si se pidió, corre así:

Qué se audita, con qué skill, los comandos, los F y los P, y la re-auditoría: `references/fase-3-auditar.md`.

### Fase 4 — Cierre (UN turno humano)

Un solo mensaje con lo que escribe `python bin/lote.py cierre <carpeta>` en `CIERRE.md`, mostrado tal cual. La tabla sale de los archivos y de las auditorías que se hayan pedido, no de la memoria. Una fila sin el ANTES de un PISA, sin dedup en un ALTA, con una dedup que no dice cuántas consultas corrieron o con unos GATES fuera de formato, sale **FRENA** y no se escribe. La auditoría **nunca** frena: dice *no se pidió*, su veredicto, o **NO SE SELLA** si se pidió y no cierra. El mensaje trae:

Sus siete puntos, de la tabla del lote a *«¿Escribo todo el lote?»*: `references/fase-4-cierre.md`.

**El "sí" cubre exactamente lo que está en el mensaje del cierre**: la tabla, los sellos (si
hubo auditoría), los comentarios de pendientes y el conocimiento para el Cerebro. Si la respuesta cambia o tacha un ítem («sí, pero en la 3 hacé
X»), se escribe el resto, y ese ítem —con lo que depende de él: las Tareas de una Historia que
no se pisa o no se crea, las relaciones que lo nombran— se rehace, se re-audita si hubo auditoría, y se muestra en
un turno más, solo.

### Fase 5 — Escribir y verificar (la IA, con el "sí")

1. **Releer** cada tarjeta que el lote edita o de la que cuelga algo (Estado, Ruta de iteración, Asignado, `System.Rev`). Si cambió desde la fase 0 —la tomó alguien, entró a un sprint, otra mano editó el texto—, esa fila y lo que depende de ella **no se escriben**, y se informa. Antes de las altas se repite la búsqueda de duplicados, rápida: el lote dura media hora y alguien pudo crear lo mismo.
2. a 10. Ediciones, altas (padre antes que hijo), sellos si hubo auditoría, `[T-nn]` → `#ID`, relaciones, pendientes en las tarjetas y traza, en ese orden: `references/fase-5-escribir.md`.
11. **Reporte** corto: los `#ID`, lo que quedó abierto y dónde.

**Si una escritura falla, se frena el lote.** Se informa qué quedó escrito y qué no, y antes de
reintentar un alta se busca por título que no se haya creado igual: un reintento ciego duplica.

## Cuándo leer cada referencia

| Referencia (`references/`) | Se lee |
|---|---|
| `cuando-se-usa.md` | Si no está claro que el pedido es de esta skill |
| `script-y-archivos-del-lote.md` | Fase 0, y cada vez que se corre `bin/lote.py` |
| `fase-2-redactar.md` | Fase 2, al lanzar a los redactores |
| `fase-3-auditar.md` | Fase 3, sólo si se pidió auditoría |
| `fase-4-cierre.md` | Fase 4, al armar el mensaje del cierre |
| `fase-5-escribir.md` | Fase 5, con el «sí», antes de escribir |
| `por-que-y-tiempos.md` | Para explicar el modo lote, o si una fase se alarga |
| `misiones/` (fuera de `references/`) | No se leen: los imprime `bin/lote.py mision` |

## Contexto adicional

- Cardinalidad y traza del árbol: [[sincronizar-backlog]] · [[organizacion-y-trazabilidad]]
- Un ítem por vez: [[redactar-tarea]] · [[cargar-a-azure]]
- Auditorías: [[auditar-historia]] · [[auditar-tarea]] · [[analizar-tareas]]
- Sellos y comentarios: [[comentar-tarea]]
