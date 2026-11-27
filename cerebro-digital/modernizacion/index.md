---
id: seccion-modernizacion
tipo: indice
estado: F-Draft
modulo: general
title: "Modernización de una aplicación existente"
description: Portada de la sección transversal de modernización — absorber una aplicación que ya funciona, decidir refactor o migración, ponerle una red y modernizarla slice por slice; cómo se le pide a la IA, las guías, los scripts, la decisión y dónde va lo del proyecto.
tags: [modernizacion, migracion, refactor, ingenieria-inversa, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# Modernización de una aplicación existente

Qué se hace cuando el proyecto no arranca de cero sino de **una aplicación que ya funciona**: entenderla, decidir
qué hacer con ella y cambiarla sin romper lo que hace. Esta sección es **transversal**: es la portada del método,
que vive en cuatro skills, una por fase. Lo que el proyecto decidió y cómo avanza vive en el módulo (abajo, «Dónde
va lo del proyecto»).

| Fase | Skill | Termina con |
|---|---|---|
| 1. Absorber | `absorber-aplicacion` | El Cerebro poblado con lo que la aplicación hace, cada ítem con su «sí» y su marca de confianza |
| 2. Planificar | `planificar-modernizacion` | `DEC-004` escrita con el «sí», la curaduría de cada regla y una ficha por slice |
| 3. Caracterizar | `caracterizar-comportamiento` | La red: el corpus y el golden grabado contra la aplicación vieja |
| 4. Modernizar | `modernizar-slice` | Un slice construido, con paridad, cortado y la vieja apagada |

## Qué cubre y qué no

**Cubre:**

- Inventariar y radiografiar una aplicación existente (endpoints, entidades, estados, pantallas, reglas candidatas,
  integraciones, permisos), cada hecho con `archivo:línea`. Sirve también sólo para documentarla (ingeniería inversa).
- Comparar las estrategias con lo medido: refactor en el lugar, migración por estrangulador, corrida en paralelo,
  subir de versión o no tocarla. La gran explosión no es opción.
- La red antes de tocar: el corpus de casos, el golden y los tests de caracterización.
- La paridad de cada slice, el corte de tráfico con barrera y el apagado de la vieja; el código muerto y la subida
  de versión.

**No cubre:**

- El ciclo de cada Tarea (contrato, TDD, revisión) → [[cerebro-digital/desarrollo/index|Desarrollo]].
- Redactar las Historias y Tareas de cada slice → [[cerebro-digital/tickets/index|Tickets]].
- El despliegue y el corte en la plataforma → [[cerebro-digital/devops/index|DevOps]].

## Cómo se le pide

- «absorbé esta app», «hacé ingeniería inversa de esta aplicación» →
  `cerebro-digital/configuracion-ia/skills/absorber-aplicacion/SKILL.md`.
- «¿refactorizo o migro?», «armá el plan de modernización» →
  `cerebro-digital/configuracion-ia/skills/planificar-modernizacion/SKILL.md`.
- «ponele una red a este módulo», «grabá cómo responde hoy», «armá el corpus de paridad» →
  `cerebro-digital/configuracion-ia/skills/caracterizar-comportamiento/SKILL.md`.
- «migrá el slice X», «refactorizá el módulo X», «cortá el tráfico de X» →
  `cerebro-digital/configuracion-ia/skills/modernizar-slice/SKILL.md`.

## Qué hace la IA sola y qué no

Lee la aplicación vieja; **no la modifica**. Propone con los números a la vista y pregunta: la estrategia la decide
una persona. Nunca graba datos de personas en el corpus ni en el golden. **Sin paridad no hay corte**: el corte de
tráfico pasa sólo con `bin/mapa-modernizacion.py corte` en OK; una diferencia se acepta sólo con el nombre de una
persona, y nadie se aprueba a sí mismo. **El corte de tráfico y el apagado de la vieja los hace una persona**: la IA
muestra la barrera en OK.

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/absorber-aplicacion/references/lo-que-sigue.md` — qué skill toma la aplicación después de absorberla.
- `cerebro-digital/configuracion-ia/skills/modernizar-slice/references/refactor-en-el-lugar.md` — cuando `DEC-004` dice refactor: un módulo por vez, sin repositorio nuevo.
- `cerebro-digital/configuracion-ia/skills/modernizar-slice/references/codigo-muerto.md` — sacar lo que nadie llama, con evidencia y en tandas reversibles.
- `cerebro-digital/configuracion-ia/skills/modernizar-slice/references/subir-de-version.md` — framework o lenguaje, sin gran explosión.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/refactor-y-migracion.md` — el método de cada Tarea: red primero, caracterización, paridad, estrangulador.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/ingenieria-inversa.md` — leer una aplicación existente para documentarla.

## Los scripts

- `bin/inventariar-codigo.py` — el inventario: lenguajes, build, pipeline, contratos, migraciones, tests, deuda, posibles secretos; trae las filas medibles de la tabla de estrategias.
- `bin/radiografiar-codigo.py` — la radiografía, cada hecho con `archivo:línea`; la lectura de `absorber-aplicacion` empieza por lo que señala.
- `bin/esquema-base.py` — el esquema real de una base a Markdown y Mermaid; nunca filas de datos.
- `bin/armar-corpus.py` — el esqueleto del corpus de paridad de un slice desde la radiografía, con `<completar>`; no inventa valores.
- `bin/paridad.py` — `grabar` el golden contra la aplicación vieja (firmado por el script) y `comparar` con la nueva, diferencia por diferencia.
- `bin/mapa-modernizacion.py` — el avance por slice (`ver`) y la barrera del corte de tráfico (`corte`: `DEC-004`, paridad OK y reciente, persona que aprueba).
- `bin/adoptar-proyecto.py` — enchufa la carpeta de la aplicación existente a `back/` o `front/` en un comando.

## La decisión

`DEC-004` — Refactor o migración de la aplicación existente: la estrategia, qué reglas se migran o se descartan, el
orden de los slices y cuándo se apaga la vieja. Sólo existe si el proyecto arranca de una aplicación que ya
funciona; vive en [[decisiones]], en `⚠` hasta que se decida.

## Dónde va lo del proyecto

Lo escribe `cerebro-curator`, con el «sí» de una persona.

| Qué | Dónde |
|---|---|
| El avance de cada slice, con la evidencia de cada estado | [[cerebro-digital/modulo-ejemplo/aplicacion/modernizacion|Modernización del módulo]] |
| Lo que la aplicación hace (reglas, flujos), absorbido | Las fichas de `funcional/` del módulo |
| Qué existe hoy, módulo por módulo | [[mapa]] |
| Trampas y comportamientos raros encontrados (`AP-nnn`) | [[aprendizajes]] |
| La deuda que se hereda (`DT-nnn`) | [[deuda]] |
| Las preguntas abiertas | [[pendientes]] |

_Últ. modif.: 2026-11-27 — @equipo — sección nueva del Cerebro_
