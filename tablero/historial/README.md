---
id: historial-readme
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Historial de tickets — log resumido e indexable"
author: equipo
tags: [historial, aprendizaje, tickets, azure, memoria, trazabilidad, cerebro-digital, indice]
last_updated: 2026-08-26
---

# Historial de tickets — log resumido e indexable

El historial es un **log liviano** del trabajo hecho contra el board. Su corazón es
**[[INDICE]]**: **una fila por ticket** con el tema (etiqueta), la **referencia**
(los `#ID` de Azure y la ruta del documento del Cerebro Digital que lo originó) y un
**resumen de una línea**. Nada más. Así, aunque se generen miles de tickets, el
historial sigue siendo **una tabla que se puede indexar y buscar**, no miles de
archivos.

> **Importante:** el historial **NO escribe nada en el Cerebro Digital**
> (`cerebro-digital/`). El Cerebro es la **fuente de solo lectura**; el ticket va
> **a Azure**; el historial solo deja la **referencia** (tag + `#ID` + ruta del doc)
> para poder rastrear el origen. Enlazar, no copiar.

## Por qué así (no un `.md` por ticket)

Guardar un archivo completo por cada ticket (con el pedido y el ticket enteros)
**infla la memoria** y se desincroniza apenas cambia el documento. En cambio:

- **Una fila por ticket** en [[INDICE]] tiene costo constante y es indexable (se
  busca por fecha, tipo, tema o `#ID` con Ctrl+F).
- **Se guarda solo la referencia**: `#ID` de Azure + ruta del doc del Cerebro. El
  **cuerpo del documento y del ticket NUNCA se copian**.
- El detalle vivo siempre está en su lugar: el ticket en Azure, el dominio en el
  Cerebro Digital. El historial solo apunta.

## El registro detallado (.md) es opcional — solo para `gold`

La mayoría de los tickets viven **solo como una fila** en [[INDICE]]. El archivo
`.md` detallado (con ANTES / DESPUÉS / decisiones) se crea **únicamente** cuando un
ticket se promueve a **`gold`**: es decir, cuando vale la pena conservarlo como
**modelo de estilo** para que la IA lo imite. Molde: ver «El molde» abajo.

Resultado: N tickets → N filas baratas en el índice + un puñado de `.md` `gold`.

## Estados de una fila

| Estado | Qué significa | La IA lo usa de ejemplo |
|---|---|---|
| `registrado` | Ticket creado; queda la fila en el índice | Con baja prioridad (solo la referencia) |
| `aprobado` | Validado y cargado en Azure | Sí |
| `gold` | Aprobado **y** buen modelo a imitar → se le crea el `.md` detallado | Sí, con prioridad |

Promover es solo cambiar el `Estado` en la fila (y, para `gold`, crear el `.md`).
En un agente con skills se puede pedir *"marcá esta fila como gold"*.

## Cómo se llena

- **Con skills (automático):** al crear/cargar un ticket, la skill agrega **una
  fila** en [[INDICE]] (tema, `#ID`, documento fuente, resumen, puntos si aplica).
  No crea ningún `.md` salvo que se marque `gold`.
- **Sin skills (manual):** copiás la fila que la IA te entrega y la pegás como
  primera de la tabla de [[INDICE]] (más nuevo arriba).

## Calibración de puntos (opcional pero útil)

La fila puede llevar los **Puntos** y, cuando se sepan, los **tokens reales**
(resolver / investigar). Con varias filas, la IA **calibra** el mapeo
"tantos tokens ≈ tanta banda" (ver [[estimar-story-points]]). Sin datos, arranca
`(pendiente)`; no se inventan umbrales.

## Reglas culturales

- **PHI prohibido:** ni en las filas ni en los `.md` van datos personales sensibles/personales
  reales. Usá marcadores `<persona>`, `<documento>`, `<telefono>`, `<dato-sensible>`.
- **No inventar:** lo no confirmado se marca `⚠` y se pregunta; los `#ID` son dato
  duro (`⚠` hasta que Azure los devuelva).
- **Provenance:** si nace de una tarjeta, dejá el `#ID` en la referencia; si nace de
  un documento del Cerebro Digital, dejá su ruta. Siempre por referencia.

## Archivos de esta carpeta

- **[[INDICE]]** — el log: una fila por ticket. El punto de entrada.
- **Los `.md` `gold`** — pocos, los modelos de estilo a imitar (el molde está abajo).

> **Estado inicial:** el historial **arranca vacío** (los ejemplos de otro proyecto
> se quitaron). Hoy `historial/` tiene solo [[INDICE]] (tabla sin filas). Se va
> llenando con los tickets de **este** proyecto: cada ticket suma una fila, y los
> buenos se promueven a `gold`.

## El molde (fila de índice + registro gold)

Lo normal es **solo la fila de índice**. El **registro detallado** `.md` se crea únicamente cuando el ticket se promueve a `gold`. Todo por referencia (ruta + `#ID`), nunca copiando el contenido; sin PHI (marcadores `<persona>`, `<documento>`, `<dato-sensible>`…).

**Fila de índice (SIEMPRE)** — pegala como primera de la tabla de [[INDICE]] (más nuevo arriba):

```
| AAAA-MM-DD | historia | <tema> | #NNNN | ruta/al/doc.md | <resumen de una línea> | 5 | registrado |
```

Columnas: Fecha · Tipo · **Tema** (etiqueta, sin prefijo) · **#IDs Azure** (o `—`) · **Documento fuente** (ruta de la ficha del Cerebro, o `—`) · **Resumen** (una línea) · **Puntos** (o `—`) · **Estado** (`registrado` | `aprobado` | `gold`). Solo referencias, nunca el cuerpo.

**Registro detallado (SOLO si es `gold`)** — además de la fila, creá `AAAA-MM-DD__<tipo>__<modulo>__<slug>.md` con: frontmatter (`id`, `tipo: registro-ticket`, `estado: gold`, `tema`, `puntos`, `tokens_resolver`/`tokens_investigar` para calibrar, y la trazabilidad por referencia: `documento_fuente`, `tickets_derivados`, `relacionados`) + tres secciones: **Pedido original (ANTES)**, **Ticket generado (DESPUÉS)** y **Por qué es gold** (qué conviene reutilizar: estilo, nivel de detalle, decisiones). Si dudás si merece el `.md`, **no lo crees**: dejá solo la fila.
