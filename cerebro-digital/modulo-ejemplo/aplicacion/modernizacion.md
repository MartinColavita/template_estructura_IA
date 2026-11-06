---
id: aplicacion-modernizacion
tipo: tablero
estado: F-Draft
modulo: modulo-ejemplo
title: "Modernización de la aplicación existente (modulo-ejemplo)"
description: Avance de la modernización decidida en DEC-004, slice por slice, con la evidencia de cada estado. Lo lee bin/mapa-modernizacion.py.
tags: [modulo-ejemplo, aplicacion, modernizacion, okf]
last_updated: 2026-11-03
author: "equipo"
---

# Modernización de la aplicación existente

Sólo existe si el proyecto arrancó de una aplicación que ya funciona y `DEC-004` está confirmada
([[decisiones#DEC-004]]). La escribe `cerebro-curator` con el "sí" de una persona; la leen
`bin/mapa-modernizacion.py ver` (avance) y `bin/mapa-modernizacion.py corte` (la barrera del corte).

**Estados, en orden:** `pendiente` → `contrato` → `red` → `construido` → `paridad` → `cortado` → `apagado`
(qué exige cada uno: [[modernizar-slice]]). Un slice no salta estados.

| Slice | Estrategia | Estado | Contrato | Corpus | Golden | Paridad | Corte aprobado por | Notas |
|---|---|---|---|---|---|---|---|---|
| `<completar: nombre del slice>` | `<completar: migración / refactor / subir de versión>` | pendiente | | | | | | `<completar: ficha en funcional/>` |

**Columnas.** *Contrato*: el `openapi.yaml` del slice o el documento de límites (refactor). *Corpus* y
*Golden*: rutas en `aplicacion/paridad/<slice>/` una vez versionados. *Paridad*: fecha y veredicto de la
última corrida de `bin/paridad.py comparar`. *Corte aprobado por*: el nombre de la **persona** que aprobó el
corte, escrito antes de cortar; un agente no vale.

## Diferencias aceptadas

Las lleva `aplicacion/paridad/<slice>/aceptadas.json` (con `aprobado_por`, fecha y motivo). Acá se
resume, para que se lea sin abrir el JSON:

| Slice | Caso | Camino | Por qué se acepta | Quién |
|---|---|---|---|---|
| | | | | |
