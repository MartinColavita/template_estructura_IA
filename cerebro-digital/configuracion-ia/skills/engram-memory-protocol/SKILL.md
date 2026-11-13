---
name: engram-memory-protocol
description: Cómo se usa Engram (mem_save, mem_search, mem_context, mem_session_summary) en este proyecto - sólo para la continuidad entre sesiones (en qué estaba, qué quedó a medias, el próximo paso), nunca como fuente de una regla o una decisión, que van al Cerebro. Usar al retomar o cerrar una sesión con Engram instalado.
license: Apache-2.0
---

# Engram — continuidad entre sesiones

> La fuente es el Cerebro ([[AGENTS]], instrucción 1): Engram vive en una máquina y no se versiona. Si no está
> instalado, no falta nada.

## Qué va a Engram y qué no

| Va a Engram | Va al Cerebro, con el «sí» de la persona |
|---|---|
| En qué estaba la sesión, qué quedó a medias, el próximo paso | Una regla, un estado, una decisión (`DEC-nnn`), un pendiente (`P-nnn`) |
| Un puntero: «la decisión quedó en `decisiones.md`, `DEC-005`» | El contenido de esa decisión |
| Una trampa de esta máquina (una ruta, un comando que acá falla) o una preferencia de la persona | Una trampa del stack o un bug con causa: `AP-nnn` en `<modulo>/aplicacion/` |

Nunca PHI ni secretos.

## Retomar y cerrar

- Al retomar —«¿en qué estábamos?», después de una compactación—: `mem_context` y, si no alcanza, `mem_search` →
  `mem_get_observation`. Lo que aparezca se contrasta con el Cerebro antes de usarlo.
- Al cerrar una sesión con trabajo a medias: `mem_session_summary` (con el formato de la herramienta).
