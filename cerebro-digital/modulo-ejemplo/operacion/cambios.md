---
id: cambios
tipo: operacion
estado: F-Draft
modulo: modulo-ejemplo
title: Registro de cambios en lo que corre — modulo-ejemplo
description: Una línea por cada cambio N1 o N2 ejecutado en un servidor, un cluster o una URL del inventario, con su plan, quién lo aprobó y cómo quedó.
tags: [operacion, cambios, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# Registro de cambios en lo que corre — modulo-ejemplo

> **Es lo primero que se lee en un diagnóstico**: la pregunta que más rinde es «¿qué cambió?». Una fila por cada
> cambio N1 o N2 **ejecutado** (no por cada plan), la más nueva arriba. La escribe `cerebro-curator` con el «sí» de
> la persona, al cerrar el plan de cambio ([[operacion-de-servidores]]). Es el resumen: el registro completo (qué
> entró por SSH y qué corrió `sudo`) queda en el servidor, donde fije `DEC-008`. Nace vacía.

## Los cambios

| Fecha (UTC) | Alias | Nivel | Qué | Plan | Aprobó (rol) | Resultado | Verificación | ¿Se volvió atrás? |
|---|---|---|---|---|---|---|---|---|
| `<AAAA-MM-DD HH:MM>` | `<alias>` | `<N1 o N2>` | `<qué se cambió, en criollo>` | `<archivo del plan>` | `<rol>` | `<salió como se esperaba / distinto>` | `<script y su veredicto>` | `<no / sí, por qué>` |

## Cómo se llena cada columna

| Columna | Qué va | Qué **no** va |
|---|---|---|
| **Fecha (UTC)** | Cuándo se corrió el comando | La fecha del plan |
| **Alias** | El exacto del inventario ([[inventario]]) | La IP o el nombre real |
| **Nivel** | El del plan, que pasó por `bin/gate-operacion.py` | N0 (leer no se registra acá) ni N3 (no lo hace la IA) |
| **Plan** | El nombre del archivo del plan, y la Tarea o el `INC-nnn` si lo hay | El comando con valores secretos |
| **Aprobó (rol)** | El rol de quien dio el «sí» (los dos, si fue N2) | El nombre de una persona |
| **Resultado** y **Verificación** | Lo que midió el script después del cambio | «Anduvo» sin medición |
| **¿Se volvió atrás?** | Si se usó la vuelta atrás del plan, y por qué | — |

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-049)_
