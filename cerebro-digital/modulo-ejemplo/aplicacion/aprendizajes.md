---
id: aprendizajes-aplicacion
tipo: aplicacion
estado: F-Draft
modulo: modulo-ejemplo
title: Aprendizajes de la aplicación — modulo-ejemplo
description: Lo que el equipo y la IA aprendieron construyendo la aplicación (AP-nnn), siempre con la fuente y con lo que cambió a partir de cada uno.
tags: [modulo-ejemplo, aplicacion, aprendizajes]
last_updated: 2026-10-30
author: "equipo"
---

# Aprendizajes de la aplicación — modulo-ejemplo

> Una fila por aprendizaje, `AP-nnn` consecutivos. **Un aprendizaje que no cambió nada es una
> anécdota**: la última columna es obligatoria. Lo que es del negocio (una regla, un estado) no va
> acá, va a `funcional/`; lo que es del ecosistema (una skill, un script) va a
> `configuracion-ia/mejoras.md`. Acá va lo que es de **esta aplicación**: su stack, su código, su
> operación. Nunca PHI.

## Tipos

| Tipo | Qué es | Ejemplo típico |
|---|---|---|
| **bug** | Un defecto que llegó a un ambiente, con su causa raíz | Un formato de fecha distinto entre el back y el front que los tests de cada lado no vieron |
| **trampa del stack** | Algo del framework, la librería o la infraestructura que sorprende | Una transacción que no se abre en un método privado |
| **patrón que funcionó** | Una forma de resolver algo que conviene repetir | Cómo se simuló una integración externa en los tests |
| **decisión revertida** | Algo que se decidió, se probó y se volvió atrás, con el porqué | Una librería que se sacó |
| **operación** | Algo del despliegue o del ambiente que hay que saber | Qué variable hay que definir antes de levantar el servicio |

## Registro

| # | Fecha | Tipo | Qué pasó (síntoma) | Causa | Fuente (`#ID`, MR, commit, incidente) | Qué cambió a partir de esto |
|---|---|---|---|---|---|---|
| AP-001 | YYYY-MM-DD | bug / trampa del stack / patrón / decisión revertida / operación | <en criollo> | <la causa, no el parche> | `#NNNN` · `!nn` | <un test nuevo, `C-n`, una `RN-…`, una skill, una `DEC-nnn`> |
