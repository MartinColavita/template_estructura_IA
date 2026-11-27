---
id: seccion-tickets
tipo: indice
estado: F-Draft
modulo: general
title: "Tickets: del Cerebro al tablero"
description: Portada corta de los tickets — apunta a tablero/ (el método, las plantillas y los checklists, que viven fuera del Cerebro a propósito) y a las skills del pipeline que redactan, auditan y cargan Historias y Tareas.
tags: [tickets, tablero, backlog, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# Tickets: del Cerebro al tablero

Cómo una ficha del Cerebro se vuelve Épicas, Features, Historias y Tareas en el tablero (Azure DevOps o el tablero
local, según `DEC-006` en [[decisiones]]). Esta portada **sólo apunta**: el método vive en `tablero/`, que queda
**fuera del Cerebro a propósito** (sirve para cualquier tablero y cualquier proyecto), y en las skills del pipeline.

## Dónde está cada cosa

- **El método**: [[redaccion-de-tickets]] (las reglas de oro, «Fuentes que deciden», el modo lote, la cardinalidad)
  y el índice de `tablero/conocimiento/` en [[tablero/conocimiento/00-index|Conocimiento de redacción de tickets]].
  El puente de punta a punta: [[pipeline-doc-a-tickets]].
- **Los moldes**: `tablero/plantillas/` (Épica, Feature, Historia, Tarea, Bug, Habilitador) y
  `tablero/checklists/` (uno por tipo, más el mapa de campos de Azure).
- **Las barreras** al escribir en el tablero (tablero autorizado, deduplicación, confirmación, nivel, tarjeta
  congelada, borrado): [[AGENTS]], «Redacción y carga de tickets en Azure DevOps».

## Las skills del pipeline

La puerta es la skill `tickets`: rutea cada pedido, por su objeto, a la skill que corresponde. La lista con una línea cada una está en [[cerebro-digital/index|el índice del
Cerebro]] («Pipeline del tablero»). Para redactar: `redactar-tarea`, `estimar-story-points`. Para revisar:
`consultar-backlog`, `analizar-tareas`, `auditar-historia`, `auditar-tarea`. Para escribir en el tablero:
`sincronizar-backlog`, `planificar-lote`, `cargar-a-azure`, `tomar-tarea`, `comentar-tarea`. Para desarrollar lo
asignado: `desarrollar-asignadas` → [[cerebro-digital/desarrollo/index|Desarrollo]].

## Los scripts

Lo que se cuenta, lo cuenta un script (qué mira cada uno: `bin/README.md`): `bin/auditar-tarea.py`,
`bin/auditar-historia.py`, `bin/analizar-tareas.py`, `bin/derivar-arbol.py`, `bin/lote.py`,
`bin/tablero-local.py`, `bin/derivar-a-tablero-local.py` y `bin/verificar-sello.py`.

_Últ. modif.: 2026-11-27 — @equipo — portada nueva de la sección_
