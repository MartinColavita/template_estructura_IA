---
id: index-aplicacion
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "04 - Aplicación (modulo-ejemplo)"
description: Índice del pilar de la aplicación construida — qué existe hoy, qué aprendió el equipo al construirla y qué deuda arrastra.
tags: [modulo-ejemplo, aplicacion, indice, okf]
last_updated: 2026-10-30
author: "equipo"
---

# 04 - Aplicación (modulo-ejemplo)

Este pilar es la **memoria viva de la aplicación construida**. Los otros tres dicen qué debe hacer
(`funcional/`), cómo se diseña (`arquitectura/`) y cómo trabaja el equipo (`metodologia/`); este dice
**qué existe hoy y qué se aprendió construyéndolo**. Nace vacío con el template y lo llenan el
desarrollo (paso 7-bis del [[orquestador-desarrollo]]), la absorción de una aplicación existente
([[absorber-aplicacion]]) y los hallazgos aceptados del Doctor ([[atender-hallazgos]]).

| Archivo | Qué guarda | Código | Quién lo alimenta |
|---|---|---|---|
| [[mapa]] | **Lo que existe**: cada módulo de código con su repositorio, qué hace, qué expone, qué Historias lo construyeron y en qué estado está; integraciones y ambientes reales | — | El cierre de cada Tarea (datos de `datos-cierre.py`) y el inventario de la absorción |
| [[aprendizajes]] | **Lo que se aprendió**: un bug y su causa, una trampa del stack, un patrón que funcionó, una decisión que hubo que revertir; siempre con lo que cambió a partir de eso | `AP-nnn` | El paso 7-bis, las revisiones de Merge Request, los incidentes |
| [[modernizacion]] | **El avance de la modernización** de una app existente, slice por slice: estrategia, estado, contrato, corpus, golden, paridad y quién aprobó el corte. Sólo si hay `DEC-004` | — | `planificar-modernizacion` la crea; `modernizar-slice` la avanza; `bin/mapa-modernizacion.py` la lee |
| [[deuda]] | **Lo que se debe**: deuda técnica aceptada a sabiendas, con su riesgo y cuándo se paga | `DT-nnn` | La absorción, los hallazgos del Doctor aceptados, los pendientes técnicos de un Merge Request |

## Reglas de este pilar

- **Nada entra de memoria.** Cada fila cita su fuente: la Tarea (`#ID`), el Merge Request, el commit
  o la corrida del Doctor. Un dato que no se pudo leer va `⚠ sin dato`.
- **Lo que es del negocio no va acá**: una regla, un estado o una respuesta a un pendiente van a
  `funcional/` o a `decisiones.md`, por la Consulta Interactiva de Decisión. Lo que es del
  **ecosistema** (una skill, un script, una convención que falla) va a `configuracion-ia/mejoras.md`
  por [[mejorar-ecosistema]]. Acá va sólo lo que es de **esta aplicación**.
- **Un aprendizaje que no cambió nada es una anécdota.** Cada `AP-nnn` dice qué quedó distinto:
  un test, una convención (`C-n`), una regla de negocio, una skill o una decisión.
- **Lo escribe `cerebro-curator`** con el «sí» de una persona, como todo lo demás del Cerebro, y
  queda en `log.md`.
- **Sin PHI y sin secretos**: ambientes y hosts sí; credenciales, nunca; datos de personas, nunca.
- **Es lo primero que abre un worker** antes de tocar un módulo que ya existe (skill
  `consultar-cerebro`): acá está la trampa que ya pisó otro.
