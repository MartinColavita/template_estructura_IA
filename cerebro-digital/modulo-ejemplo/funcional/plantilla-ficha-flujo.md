---
id: plantilla-ficha-flujo
tipo: flujo
estado: F-Draft
modulo: modulo-ejemplo
title: "<Nombre del flujo> — plantilla de ficha funcional"
description: Molde de una ficha de flujo derivable a backlog. Copiar, renombrar por tema (kebab-case) y completar.
tags: [plantilla, flujo, modulo-ejemplo]
last_updated: 2026-10-22
author: "equipo"
fuente_maqueta: ""
---

# <Nombre del flujo>

> **Cómo se usa este molde.** Se copia a `funcional/<nombre-del-flujo>.md` (por tema, nunca por
> estado: nada de `nuevo-`, `final-`). La escribe `cerebro-analyst` como borrador en `borrador/`,
> la valida una persona y la persiste `cerebro-curator`. Sigue los patrones de
> `cognitive-doc-design`: propósito corto, reglas numeradas, condicionales en tablas, dudas al
> final y el bloque de derivación enumerado. **Sin el bloque `## Derivación a backlog` validado,
> la ficha no se deriva a tickets.**

## Propósito

<2-3 líneas: qué resuelve este flujo y para quién.>

## Glosario

| Término | Definición (una línea) |
|---|---|
| <término del dominio> | <qué significa acá> |

## Reglas de negocio

### RN-MOD-001 — <Título descriptivo>

<Enunciado de la regla. Si es condicional, va en tabla de decisión:>

| # | Condición | Acción |
|---|-----------|--------|
| 1 | <condición> | <acción> |
| 2 | <la contraria> | <la otra acción> |

(Fuente: [DOC-01] Sección <n>)

_Últ. modif.: YYYY-MM-DD — @autor — motivo_

### RN-MOD-002 — <Título>

<…>

## Flujo

1. <Paso 1: quién hace qué>
2. <Paso 2>
3. <Paso n>

## Pantalla

- **Maqueta vigente:** `entregables/disenos/<archivo>.html` (la que cita `fuente_maqueta` en el
  frontmatter; una maqueta que ninguna ficha cita no decide nada).
- **Lo que la pantalla muestra pero queda fuera de este flujo:** <ítem y motivo>.

## Dudas y Preguntas

- ⚠ <pregunta sin responder> → `[[pendientes#P-nnn]]`

## Derivación a backlog

> ⚠ Propuesto por la curación; lo valida una persona antes de derivar. Determina el conteo 1:1:
> 1 Épica por `[S-nn]`, 1 Feature por `[C-nn]`, 1 Historia por `[F-nn]`, 0 Tareas.

**Etiqueta temática:** `<etiqueta-tematica>`

### Slices [Épicas]
- [S-01] <nombre del slice / dominio>

### Capacidades [Features]
- [C-01] <capacidad> · Slice: S-01

### Flujos [Historias]
- [F-01] <flujo, en una línea, en criollo> · Capacidad: C-01 · Reglas: RN-MOD-001
- [F-02] <flujo> · Capacidad: C-01 · Reglas: RN-MOD-002

**Conteo:** 1 Épica + 1 Feature + 2 Historias = **4 work items**, 0 Tareas.

**Control de reglas asignadas:** cada `RN-MOD-nnn` de esta ficha aparece en algún `[F-nn]` o se
declara fuera de alcance con su motivo. <listar las que quedan afuera y por qué>

## Tickets derivados

| Fecha | Tipo | #IDs Azure | Resumen |
|---|---|---|---|
