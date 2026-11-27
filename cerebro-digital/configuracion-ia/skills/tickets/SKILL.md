---
name: tickets
description: >-
  Puerta única de los tickets del tablero (Azure DevOps o el tablero local): redactar o mejorar un
  ticket, cargarlo al board, bajar una ficha del Cerebro a tickets, planificar un lote de Historias o
  Tareas, consultar el board, tomar, comentar o cerrar una tarjeta, auditar una Tarea o una Historia y
  estimar Puntos. El objeto del pedido decide la skill, de forma determinista. Usar cuando se pida
  "redactá esta historia", "cargá esto a Azure", "bajá la ficha al board", "armá las tareas de estas
  historias", "¿esta funcionalidad tiene historia?", "tomo la #NNNN", "comentá en la tarjeta", "cerrá
  la #NNNN", "auditá la tarea", "estimá los puntos", "/tickets". Español (Argentina).
metadata:
  seccion: tickets
  rol: puerta
---

# Tickets — la puerta

Esta skill es **la puerta** a todo lo que es un work item: redactarlo, escribirlo en el tablero, derivarlo de una
ficha, consultarlo, tomarlo, comentarlo, cerrarlo, auditarlo y estimarlo. No redacta ni escribe por sí misma:
clasifica el pedido por su **objeto**, carga **una** skill de la sección y la deja trabajar. Se carga sólo la
elegida; ella lee lo que le hace falta.

Las skills de esta sección, con para qué sirve cada una: `references/indice-seccion.md` (lo genera
`bin/puerta-skills.py`); leelo cuando el pedido no nombra la skill.

## Qué NO es

- **Desarrollar** las Tareas asignadas (worktrees, workers) es de [[desarrollo]], con `desarrollar-asignadas`.
- **Diseñar las pruebas** de una Historia o automatizarlas, también de [[desarrollo]].
- **Persistir conocimiento** en el Cerebro (una ficha, una regla) es de `cerebro-orquestador` y `cerebro-curator`.

## Ruteo del sub-flujo Azure (tickets) — determinista

Cuando el pedido toca Azure DevOps, el **objeto del pedido** decide la skill (no el gusto del modelo), para que la **cantidad** de work items no dependa de qué skill elija el LLM:

- Objeto = **una ficha/módulo del Cerebro** ("bajá la ficha X al board", "armá el backlog del módulo Y", "derivá los tickets de esta doc") → **`sincronizar-backlog`** (árbol completo, 1:1 del bloque `## Derivación a backlog` de la ficha). Con más de una Historia, la redacción —y, si se pide, la auditoría— corren con el método de **`planificar-lote`**.
- Objeto = **las Tareas de una o más Historias**, o **una ficha con sus Tareas** ("armá las tareas de F-04 a F-08", "planificación con los devs") → **`planificar-lote`** (dos turnos humanos, agentes en paralelo; la cardinalidad de las Historias sigue siendo la de `sincronizar-backlog`).
- Objeto = **un ticket suelto** (texto suelto, "redactá/mejorá esta historia", un `#ID`) → **`redactar-tarea`** (solo redacta) y, si hay que escribirlo, **`cargar-a-azure`** (**un** ítem, nunca un árbol).
- **Consultar/auditar** el board (solo lectura) → **`consultar-backlog`**. **Tomar/comentar** un `#ID` → **`tomar-tarea`** / **`comentar-tarea`**. **Terminó un desarrollo** → **`comentar-tarea`**, con su molde de cierre. **Cerrar una Tarea** ("cerrá la #NNNN") → **`comentar-tarea`** §«Antes de cerrar una Tarea» (pendientes a la vista) y, si no está congelada, **`cargar-a-azure`** con el GATE de edición destructiva de [[AGENTS]].
- **Un segundo chequeo o una estimación** (a pedido; nunca es requisito para avanzar): la lista de tests de una Tarea → **`auditar-tarea`**; los criterios de una Historia → **`auditar-historia`**; la coherencia del conjunto de Tareas de una Historia → **`analizar-tareas`**; los Puntos de historia → **`estimar-story-points`**.
- **Desempate:** si el pedido nombra una ficha/módulo/documento del Cerebro → árbol; si nombra o describe **un** work item / `#ID` → 1 ítem. **Ante ambigüedad, preguntar** cuál — nunca asumir árbol ni ítem. Las barreras de escritura (tablero, dedup, confirmación, nivel/cardinalidad) las aplican las skills del pipeline (ver [[AGENTS]] §«Redacción y carga de tickets en Azure DevOps» (las barreras) y [[redaccion-de-tickets]] (el método)).

## Las barreras

Las reglas enteras están en [[AGENTS]] («Redacción y carga de tickets en Azure DevOps»: TABLERO, deduplicación,
confirmación, NIVEL, BORRADO y EDICIÓN DESTRUCTIVA, TARJETA CONGELADA) y valen aunque no se cargue esta skill; el
método (reglas de oro, «Fuentes que deciden», modo lote, cardinalidad), en [[redaccion-de-tickets]]. Esta puerta no
las repite ni las afloja: las aplica la skill elegida.

## Cómo se trabaja

1. **Plan corto**: el objeto del pedido, la skill que se carga y, si va a escribir en el tablero, qué GATE aplica.
   Ese plan cuenta como el Plan de Ejecución del orquestador.
2. **Una skill por pedido.** Si el pedido cruza dos (redactar y cargar; comentar y cerrar), el plan las nombra en
   orden, y cada escritura va con el «sí» que le pide su GATE.
3. Las preguntas a la persona van con la herramienta nativa de preguntas del entorno (por ejemplo
   `AskUserQuestion`); si no está, la pregunta va sola en la respuesta y se espera.
