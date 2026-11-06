---
id: deuda-aplicacion
tipo: aplicacion
estado: F-Draft
modulo: modulo-ejemplo
title: Deuda técnica de la aplicación — modulo-ejemplo
description: Deuda técnica aceptada a sabiendas (DT-nnn), con dónde está, por qué se aceptó, qué riesgo tiene y cuándo se paga.
tags: [modulo-ejemplo, aplicacion, deuda]
last_updated: 2026-10-30
author: "equipo"
---

# Deuda técnica de la aplicación — modulo-ejemplo

> Una fila por deuda, `DT-nnn` consecutivos. Deuda es lo que **se decidió dejar así, sabiendo que
> no está bien**: no es un bug (eso es un `AP-nnn` de tipo bug, o una Tarea) ni una pregunta
> abierta (eso es `pendientes.md`). Entra por tres caminos: la absorción de una aplicación
> existente, un hallazgo del Doctor que se **acepta** con motivo ([[atender-hallazgos]]) y lo que un
> Merge Request deja pendiente a propósito. Lo que no tiene fecha ni Tarea para pagarse no es
> deuda aceptada: es deuda ignorada, y eso se pregunta.

## Abiertas

| # | Qué | Dónde (módulo, archivo) | Por qué se aceptó | Riesgo si no se paga | Cuándo se paga (`#ID` o sprint) | Fuente |
|---|---|---|---|---|---|---|
| DT-001 | <qué está mal> | `<modulo>/…` | <la razón de entonces> | <qué puede pasar> | `#NNNN` / sprint N / ⚠ sin fecha | Doctor YYYY-MM-DD · `!nn` · absorción |

## Pagadas

| # | Qué | Cómo se pagó (`#ID`, MR) | Fecha |
|---|---|---|---|
