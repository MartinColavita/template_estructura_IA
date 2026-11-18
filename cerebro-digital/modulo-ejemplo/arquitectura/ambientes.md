---
id: ambientes
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: Ambientes y promoción — modulo-ejemplo
description: Los ambientes a los que se despliega, por su nombre exacto en la plataforma, si están protegidos, quién aprueba y dónde, qué entra a cada uno y cómo se vuelve atrás. Lo que no figura acá no se promueve.
tags: [arquitectura, ambientes, despliegue, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# Ambientes y promoción — modulo-ejemplo

> **A un ambiente que no está en esta tabla no se le prepara ninguna promoción** (GATE de DESPLIEGUE, en
> [[AGENTS]]). La lee un script, siempre igual:
> `python -I bin/gate-despliegue.py --ambiente <nombre> --version <versión>`.
> Nace con **una fila de molde**: mientras no haya una fila cargada, el gate da `SIN DATOS` y no se prepara
> nada. La completa una persona; cada fila que se suma o cambia es una decisión, con su firma en [[log]].
> Qué plataforma se usa y dónde vive la aprobación de producción lo fija [[decisiones#DEC-007]].

## Los ambientes

Las filas van **en orden de promoción**, de la primera a la última: el gate toma la fila de arriba como «el
ambiente anterior», por el que tiene que haber pasado el mismo artefacto.

| Ambiente | Para qué es | Protegido | Quién aprueba (rol) | Dónde se aprueba | Qué entra (rama o tag) | Ventana de observación | Cómo se vuelve atrás | Cuánto tarda en volver |
|---|---|---|---|---|---|---|---|---|
| `<nombre-exacto-en-la-plataforma>` | `<para qué se usa>` | sí | `<rol>` | `<plataforma y pantalla>` | `<rama o tag>` | `<minutos>` | `<procedimiento>` | `<minutos>` |

## Cómo se llena cada columna

| Columna | Qué va | Qué **no** va |
|---|---|---|
| **Ambiente** | El nombre **exacto** con el que existe en la plataforma (`Produccion`). Único: `produccion` es otro. En algunas plataformas, un nombre mal escrito en el pipeline **crea un ambiente nuevo, sin aprobaciones** | Un apodo, la URL, el nombre del servidor |
| **Para qué es** | Quién lo usa y para qué, en una línea | — |
| **Protegido** | `sí` o `no`. Protegido quiere decir que la plataforma exige la aprobación de una persona antes de desplegar. Vacío o `⚠` vale como protegido y deja el gate en `SIN DATOS` | — |
| **Quién aprueba (rol)** | El rol que aprueba el despliegue. Obligatorio si es protegido | El nombre de una persona |
| **Dónde se aprueba** | La plataforma y la pantalla donde se da esa aprobación. Obligatorio si es protegido | Un «sí» en el chat: eso no es la aprobación |
| **Qué entra (rama o tag)** | La rama o el patrón de tag que puede llegar a ese ambiente (`rama develop`, `tags v*`). Lo exige la regla de la plataforma; acá queda escrito para mostrarlo en el plan | — |
| **Ventana de observación** | Cuánto tiempo mira alguien después de desplegar (`30 minutos`) | — |
| **Cómo se vuelve atrás** | El procedimiento, escrito (`volver a desplegar la versión anterior desde el pipeline`). Sin esto el gate frena | «Se ve en el momento» |
| **Cuánto tarda en volver** | El tiempo estimado de esa vuelta (`5 minutos`). Sin esto el gate frena | — |

## Lo que esta ficha no guarda

- **Servidores, clusters y URLs**: van en [[inventario]], con su nivel para la IA.
- **Secretos, credenciales y conexiones de servicio**: viven en la plataforma y los toca sólo una persona.
- **La protección misma** (quiénes son los revisores, las reglas de rama): se configura en la plataforma. Esta
  ficha dice qué *debería* haber; que siga ahí lo mira una persona.

El método de cada despliegue y de su vuelta atrás, con sus preguntas, está en [[despliegue-continuo]].

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-048)_
