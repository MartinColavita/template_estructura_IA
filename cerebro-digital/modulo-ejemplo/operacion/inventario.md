---
id: inventario
tipo: operacion
estado: F-Draft
modulo: modulo-ejemplo
title: Inventario de activos autorizados — modulo-ejemplo
description: Los servidores, clusters, imágenes y URLs de ambientes que la IA puede tocar, por alias, y hasta qué nivel. Lo que no figura acá no existe para la IA.
tags: [operacion, inventario, seguridad, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# Inventario de activos autorizados — modulo-ejemplo

> **Lo que no está en esta tabla no existe para la IA**, ni siquiera para leerlo (GATE de SERVIDOR, en
> [[AGENTS]]). La lee un script, siempre igual: `python -I bin/activo-autorizado.py --alias <alias>`.
> Nace **vacía**: mientras no haya una fila cargada, todo lo que dependa de ella da `SIN DATOS` y no se
> toca nada. La completa una persona; cada fila que se suma o cambia es una decisión, con su firma en
> [[log]].

## Los activos

| Alias | Tipo | Ambiente | Destino | Expuesto a internet | Criticidad | Nivel máximo para la IA | Pruebas dinámicas | Ventana de cambios | Dueño (rol) |
|---|---|---|---|---|---|---|---|---|---|
| `<alias>` | servidor | prueba | `<alias-ssh>` | no | media | N0 | no | `<día y horario>` | `<rol>` |

## Cómo se llena cada columna

| Columna | Qué va | Qué **no** va |
|---|---|---|
| **Alias** | El nombre con el que se lo nombra en toda conversación, runbook e informe (`web-prueba-1`). Único y exacto: `Web-Prueba-1` es otro | La IP, el nombre real del host |
| **Tipo** | `servidor` · `url` · `cluster` · `imagen` · `nube` · `otro` | — |
| **Ambiente** | `desarrollo` · `prueba` · `produccion` (los de `DEC-007`) | — |
| **Destino** | Servidor: el alias de la configuración de SSH de la máquina. URL: la dirección **exacta**, con `https://`. Cluster: el nombre del contexto. Imagen: la referencia del registro | Usuarios, contraseñas, claves, tokens: nunca |
| **Expuesto a internet** | `sí` o `no`. Pesa en la prioridad de una vulnerabilidad | — |
| **Criticidad** | `alta` · `media` · `baja` | — |
| **Nivel máximo para la IA** | `nada` · `N0` (sólo leer) · `N1` (un cambio que se deshace, con un «sí») · `N2` (un cambio con impacto, con dos «sí»). Vacío o `⚠` vale como `nada` | `N3`: eso lo hace siempre una persona |
| **Pruebas dinámicas** | `no` · `pasivo` · `activo`. Sólo para el tipo `url`. Contra producción, una prueba activa no se corre nunca, diga lo que diga la fila | — |
| **Ventana de cambios** | Cuándo se puede cambiar algo (`martes y jueves, 22 a 24`). Se muestra antes de cada cambio; no la calcula ningún script | — |
| **Dueño (rol)** | El rol que responde por el activo | El nombre de una persona |

## Qué significa cada nivel

Los niveles, con sus ejemplos y sus preguntas, están en [[operacion-de-servidores]]; la regla, en [[AGENTS]].

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-046)_
