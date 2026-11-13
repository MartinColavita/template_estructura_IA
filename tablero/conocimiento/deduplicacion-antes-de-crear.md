---
id: deduplicacion-antes-de-crear
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Deduplicación antes de crear — buscar equivalentes en el board"
author: equipo
tags: [azure-devops, dedup, duplicados, guard, backlog]
last_updated: 2026-10-01
---

# Deduplicación antes de crear

Antes de crear cualquier work item hay que **buscar si ya existe** algo equivalente o solapado en el board. Es **obligatorio** y vive **dentro del skill**: no depende de que la persona lo pida en el prompt.

## Qué buscar (herramientas de LECTURA)

Con `search_work_items` / `list_work_items` / `get_work_item`, buscar por:

- **Tag temático** (el del ítem a crear) — trae el subárbol del mismo tema.
- **Objetivo / alcance** (búsqueda textual) — cubre tags y títulos inconsistentes (p. ej. `reserva-salas` vs `reservas-salas`). La **comparación** es por objetivo/alcance, no por el string del título.
- **Documento fuente** (misma ruta de ficha = mismo origen).

Foco en ítems **ABIERTOS** (New/Active/…); los cerrados equivalentes se tratan aparte (ver abajo).

## Qué comparar

Nombre/título, **objetivo**, **funcionalidad**, **alcance** y **relaciones** (Parent/Related). No alcanza con el título: se compara la **intención**.

> **Anti-patrón (la causa #1 de duplicados reales):** buscar por título y, al no encontrar un match **exacto**, concluir "sin match" y crear. Un **título distinto NO prueba** que no sea duplicado — el mismo ítem se escribe con el título apenas reformulado ("Reservar sala" vs "Reserva de una sala de reunión"). La búsqueda por tag temático + documento fuente trae el subárbol del tema **sin depender del título**; sobre ese subárbol se compara **objetivo/alcance**, nunca el string del título.

> **Sesgo obligatorio — ante la duda, es duplicado.** Si un ítem abierto del mismo tema o documento fuente tiene un objetivo/alcance que **plausiblemente se solapa**, se trata como **posible duplicado**: se informa y se **pregunta**, nunca se crea en automático. El default en la ambigüedad es *frenar y preguntar*, no *crear*. "No es idéntico" no habilita crear; solo un "distinto y por qué" justificado (o el "sí" humano) lo habilita.

## Evidencia obligatoria — gatea la escritura (no negociable)

La dedup deja de ser "un paso que el modelo debería hacer" y pasa a ser **evidencia que el modelo TIENE que mostrar antes de escribir**. El preview/confirmación (de [[cargar-a-azure]] o [[sincronizar-backlog]]) **DEBE** incluir un **Bloque de dedup** con:

1. **Consultas corridas** — las búsquedas reales y sus términos: por **tag temático**, por **objetivo** (textual), por **documento fuente**. Si no se pudo consultar el board (MCP caído, PAT), **no se escribe** y el bloque dice **SIN DATOS** —nunca «0 candidatos»—. Si se entrega el texto para pegar a mano, arriba va *«No busqué duplicados: buscalos vos en el tablero antes de pegar.»*
2. **Candidatos devueltos** — cada ítem abierto del tema con su `#ID` + link + estado (o "0 candidatos" explícito).
3. **Veredicto por candidato** — para CADA candidato: `equivalente` / `solapa parcial` / `distinto`, con **una frase de por qué** (comparando objetivo/alcance, no título).

**Regla dura:** si ese bloque **no está** en el preview, la escritura **no está habilitada** — da igual que el contenido esté perfecto. El "sí" humano confirma el contenido **y** el resultado de dedup a la vez. Un preview sin Bloque de dedup es un preview inválido: se rehace, no se escribe.

**En modo lote** ([[planificar-lote]]) la búsqueda corre en la preparación, el detalle de los tres puntos queda en el `CONTEXTO.md` del lote, y la tabla del cierre lleva una columna de dedup por ítem (candidatos y veredicto). Un candidato dudoso se pregunta en el arranque, con los demás: no se espera al cierre para frenar un alta.

### GATE de existencia (bloqueante) — encontrar ≠ crear igual

La falla más grave no es no buscar: es **buscar, encontrar el duplicado y crear el alta igual**. Contra eso, encontrar un equivalente/solapado es un **hard-stop**:

1. Queda **PROHIBIDO `create_work_item`** para ese ítem (o ese nodo del árbol).
2. Se presenta la lista de existentes: `#ID` + link + estado.
3. Se **pregunta explícitamente**: ¿ACTUALIZAR (`update_work_item`) el existente o modificar algo? Se espera el "sí".

Nunca se crea un ítem nuevo **en paralelo** a uno que la búsqueda ya encontró. En un árbol en lote, los nodos `YA EXISTE` se **excluyen del `create`** aunque otros nodos de la misma ficha sí sean alta nueva.

## Qué informar y decidir

- **Equivalente** (mismo objetivo/alcance) → **NO crear**. Avisar con `#ID` + link + estado, **auditar su calidad** (ver abajo) y proponer **reutilizar** (si cumple) o **reutilizar y completar** (si le falta algo) + **relacionar** (Related) — con la confirmación humana de siempre.
- **Solapamiento parcial** → avisar, proponer **acotar el alcance** o **relacionar**, y esperar decisión.
- **Sin match** → seguir a la creación normal (con el GATE de confirmación).
- **Equivalente CERRADO** (ya entregado) → no se reabre; deriva al árbol bug/evolutivo de [[cambios-en-el-backlog]] §3.

## Auditoría de calidad al reutilizar (equivalente encontrado)

Encontrar el `#ID` no cierra el trabajo: hay que mirar si esa tarjeta cumple el DoR de su tipo antes de darla por buena tal cual.

1. Leer el work item completo (`get_work_item`, incluida la Descripción en HTML).
2. Correr el checklist básico de calidad según el tipo (los puntos mínimos, no el DoR entero):
   - **Historia / Tarea**: ¿Criterios de aceptación en Gherkin español, no vacíos, con camino feliz + borde/error? ¿reglas `[RN-…]` numeradas y referenciadas en los criterios? ¿Documento fuente enlazado (ruta/link, no copiado)? ¿una sola etiqueta temática, la misma que el resto del subárbol? Ver [[checklists/checklist-historia]].
   - **Bug**: ¿Pasos para reproducir numerados? ¿Resultado esperado / Resultado obtenido separados con el porqué? ¿Ambiente y Gravedad/Prioridad puestos? Ver [[checklists/checklist-bug]].
   - **Habilitador técnico**: ver [[checklists/checklist-habilitador]].
   - Base común: [[definicion-preparado-terminado]] (DoR).
3. Reportar el resultado **junto con** el aviso de duplicado (no aparte): `#ID` + link + estado + qué le falta en concreto, o "cumple el DoR" si no le falta nada.
4. Si le falta algo, la propuesta pasa de "reutilizar" a **"reutilizar y completar"**: ofrecer el texto concreto de los campos faltantes (criterios Gherkin, `[RN-…]`, Documento fuente, tag) y esperar el mismo "sí" explícito de siempre antes de `update_work_item` — es una escritura, corre el mismo GATE de confirmación que un alta. **Si el equivalente está congelado** (en un sprint y ya tomado), no se completa: lo que falta va como comentario ([[cambios-en-el-backlog]] §4).
5. Si cumple el DoR, sigue como antes: reutilizar/relacionar sin tocar nada.

Es un chequeo de calidad **intrínseca** contra una checklist fija — independiente de si hay o no un documento fuente vigente con el que comparar. **No reemplaza** el desfase (drift) de [[consultar-backlog]] (documento vigente vs. tarjeta): corren los dos, uno no sustituye al otro. No inventar reglas nuevas para "tildar" el checklist: si el gap viene de que la ficha del Cerebro tampoco tiene algo (ej. `[RN-…]` sin numerar), se marca `(pendiente)` y se frena hacia el Cerebro — igual que la Regla de cardinalidad con fichas sin el bloque de derivación cerrado.

## Flujo (fijo)

```
ítem a crear
   │
   ▼
buscar en el board  (tag temático · objetivo/alcance · documento fuente; foco ABIERTAS)
   │
   ├─ sin match ─────────────► crear normal (GATE de confirmación)
   │
   └─ hay match
         ├─ equivalente ─────► avisar #ID + link → auditar DoR del tipo
         │                        ├─ cumple ────► NO crear · reutilizar/relacionar
         │                        └─ falta algo ─► NO crear · reutilizar Y completar (preview + "sí" → update_work_item)
         └─ solapa parcial ──► avisar · proponer acotar/relacionar · esperar decisión humana
```

## Relación con las skills

- La búsqueda la hace la skill que va a escribir, con este método, como **precondición obligatoria** antes de crear; [[consultar-backlog]] corre la misma búsqueda a pedido, sólo para informar.
- Relacionar el equivalente (Related) es una escritura: va con la misma confirmación humana que todo el MCP. Si el equivalente está **congelado**, el vínculo se crea **desde** la tarjeta nueva, nunca desde la congelada ([[cambios-en-el-backlog]] §4).
