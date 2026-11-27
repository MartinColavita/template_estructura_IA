---
id: seccion-conocimiento
tipo: indice
estado: F-Draft
modulo: general
title: "Conocimiento: documentos, reuniones y curaduría del Cerebro"
description: Portada de la sección transversal de conocimiento — cómo entra lo que se sabe del negocio (documentos, reuniones, la conversación) y cómo llega al Cerebro con el «sí» de una persona; los agentes, las skills, la Consulta Interactiva de Decisión y dónde queda cada cosa.
tags: [conocimiento, curaduria, okf, reuniones, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# Conocimiento: documentos, reuniones y curaduría del Cerebro

Cómo entra al Cerebro lo que se sabe del negocio: un documento, una reunión o algo que se dijo en la conversación.
Esta sección es **transversal**: es la portada del flujo, que vive en los agentes y en las skills. El conocimiento
en sí vive en los pilares de cada módulo (abajo, «Dónde va lo del proyecto»).

La puerta es la skill `cerebro-orquestador`; en una sesión propia, `claude --agent orquestador-conocimiento`.

| Quién | Qué hace | Lo que no se negocia |
|---|---|---|
| `orquestador-conocimiento` (skill `cerebro-orquestador`) | Arma el Plan de Ejecución, delega y vigila la conversación | Lo que aparece de negocio va a una Consulta Interactiva de Decisión por ítem |
| `cerebro-analyst` | De `documentos/` a un borrador con «Dudas y Preguntas» | Nunca escribe en el Cerebro: todo a `borrador/` |
| `cerebro-curator` | Persiste en el Cerebro | Sólo lo que una persona validó, con frontmatter, wikilinks y firma en [[log]] |
| `cerebro-architect` (skill `cerebro-architect-ui`) | De maqueta y requerimiento a especificación técnica | Ningún control de interfaz sin su regla → [[cerebro-digital/diseno/index|Diseño]] |

Las reglas y el DoD de cada agente: `cerebro-digital/configuracion-ia/agentes/<agente>.md` y [[agentes]].

## Qué cubre y qué no

**Cubre:**

- Procesar un documento de `documentos/` hasta un borrador con sus dudas, y de ahí al Cerebro.
- Analizar la transcripción de una reunión y extraer lo confirmado, ítem por ítem.
- Detectar conocimiento de negocio nuevo o cambiado en cualquier conversación.
- Consultar el Cerebro: qué se lee, en qué orden y cómo se cita.
- Escribir borradores fáciles de leer: tablas de decisión, poco texto denso, la consulta guiada al funcional.

**No cubre:**

- Derivar fichas a Historias y Tareas → [[cerebro-digital/tickets/index|Tickets]].
- El código → [[cerebro-digital/desarrollo/index|Desarrollo]]. G1: el código y el conocimiento no se mezclan.
- Absorber una aplicación existente al Cerebro → [[cerebro-digital/modernizacion/index|Modernización]] (usa la misma
  Consulta Interactiva).

## Cómo se le pide

- «procesá esta documentación», «actualizá el cerebro», «armá el plan» →
  `cerebro-digital/configuracion-ia/skills/cerebro-orquestador/SKILL.md`.
- Una transcripción de reunión (`.docx` o `.txt`), «analizá esta reunión» →
  `cerebro-digital/configuracion-ia/skills/cerebro-meet-analyst/SKILL.md`.
- Cualquier pregunta sobre el dominio, una regla, una decisión o un pendiente →
  `cerebro-digital/configuracion-ia/skills/cerebro-knowledge/SKILL.md`.

## El recorrido: del insumo al Cerebro

1. **Plan**: el orquestador arma el Plan de Ejecución antes de delegar.
2. **Borrador**: `cerebro-analyst` (o `cerebro-meet-analyst`, para una reunión) deja un `.md` en `borrador/` con
   sus «Preguntas/Dudas». Nunca directo en `documentos/`, que sólo recibe lo que se entrega.
3. **Validación**: una persona responde las dudas. Nada entra al Cerebro sin su confirmación.
4. **Persistencia**: `cerebro-curator` lo guarda en `cerebro-digital/`, en UTF-8 sin BOM, y firma en [[log]].

**La Consulta Interactiva de Decisión.** Lo que aparece de negocio en la conversación no se resuelve como texto en
la respuesta: cada ítem dispara su propia pregunta con tres opciones, **Guardar**, **Ignorar** o **Editar y
Guardar**. Sin una respuesta explícita a cada una, nada avanza. En modo lote, lo detectado se lista al cierre, un
renglón por ítem. Ante la duda sobre si algo es conocimiento de negocio, se pregunta.

## Qué hace la IA sola y qué no

Lee, extrae y arma borradores; **no inventa**: lo que no está en el Cerebro queda pendiente del equipo funcional.
No escribe en el Cerebro sin el «sí» de una persona. Si un pedido contradice el Cerebro, frena y avisa. Las memorias
de herramienta no son fuente: si contradicen al Cerebro, gana el Cerebro. Las reglas exactas, en [[AGENTS]]
(«Instrucciones Obligatorias»).

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/cerebro-orquestador/SKILL.md` — el flujo de curaduría, las barandas y el ruteo por función.
- `cerebro-digital/configuracion-ia/skills/cerebro-orquestador/references/vigilancia-semantica.md` — los disparadores de la vigilancia de la conversación y la excepción del modo lote.
- `cerebro-digital/configuracion-ia/skills/cerebro-orquestador/references/orquestacion-de-sub-agentes.md` — cuándo delegar, cuándo pausar, y que las skills no se heredan al delegar.
- `cerebro-digital/configuracion-ia/skills/cerebro-meet-analyst/SKILL.md` — el checklist de una reunión, la consulta ítem por ítem y las contradicciones con el Cerebro.
- `cerebro-digital/configuracion-ia/skills/cerebro-knowledge/SKILL.md` — el orden de lectura del Cerebro y cómo se cita.
- `cerebro-digital/configuracion-ia/skills/cognitive-doc-design/SKILL.md` — los patrones para que un borrador se lea rápido.

## Los scripts

- `bin/extraer-reunion.ps1` — saca el texto de una transcripción `.docx` para que la analice `cerebro-meet-analyst`.
- `doctor/doctor.py` — el Doctor: entre otras cosas, los wikilinks que no resuelven y los conteos que se desfasaron; sus hallazgos se recorren de a uno con la skill `atender-hallazgos`.

## Dónde va lo del proyecto

| Qué | Dónde |
|---|---|
| Lo que entra (requerimientos, notas, documentos de origen) | `documentos/` |
| Los borradores en curso | `borrador/` (nunca se versiona) |
| Origen, organización, producto, alcance y equipo | [[cerebro-digital/contexto|Contexto del proyecto]] |
| Cada documento de origen (`[DOC-nn]`) | [[cerebro-digital/fuentes|Fuentes del proyecto]] |
| Reglas de negocio, flujos y pantallas | Las fichas de `funcional/` del módulo ([[plantilla-ficha-flujo]]) |
| Cómo trabaja el equipo | [[cerebro-digital/modulo-ejemplo/metodologia/index|Metodología del módulo]] |
| Las extracciones de reunión (insumo crudo) | `extraccion-reuniones/` del módulo |
| Las preguntas abiertas (`P-nnn`) | [[pendientes]] |
| El historial de cambios del Cerebro | [[log]] |

_Últ. modif.: 2026-11-27 — @equipo — sección nueva del Cerebro_
