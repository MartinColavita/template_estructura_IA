---
id: seccion-diseno
tipo: indice
estado: F-Draft
modulo: diseno
title: "Diseño: pantallas, maquetas y sistema de diseño"
description: Portada de la sección de diseño — cómo se diseña una pantalla (en Stitch o a mano), dónde van las maquetas, cómo baja una maqueta a especificación técnica, y el sistema de diseño del producto.
tags: [diseno, ui, ux, maquetas, stitch, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# Diseño: pantallas, maquetas y sistema de diseño

Cómo se diseña una pantalla del producto, dónde vive la maqueta y cómo llega al front. Esta carpeta guarda **el
sistema de diseño** del producto ([[diseno-sistema]]: tokens y componentes, el documento descriptivo); el método
vive en las skills y las maquetas, en `borrador/` y `entregables/`.

| Para… | Skill |
|---|---|
| Diseñar una pantalla en Google Stitch, desde la ficha | `disenar-con-stitch` |
| Un HTML o prototipo hecho a mano, y el sistema de diseño que toda maqueta sigue | `cerebro-mockup-design` |
| Pasar una maqueta a especificación técnica, control por control contra su regla | `cerebro-architect-ui` (agente `cerebro-architect`) |

## Qué cubre y qué no

**Cubre:**

- El brief de una pantalla desde su ficha de flujo: propósito, pasos, cada control con su regla, estados, glosario
  y tokens.
- Generar y pulir la pantalla en Stitch (o a mano), exportarla y promoverla como **maqueta vigente**.
- Los tokens del sistema de diseño y la revisión de que ninguna maqueta invente colores.
- La trazabilidad en las dos direcciones: ningún control sin regla, ninguna regla sin control.

**No cubre:**

- El código del front: el HTML exportado es referencia, no se pega → [[cerebro-digital/desarrollo/index|Desarrollo]].
- Los diagramas técnicos → la skill `archify`. Las presentaciones → la skill `cerebro-ppt-generator`.
- Las reglas de negocio de la pantalla: viven en la ficha del módulo → [[cerebro-digital/conocimiento/index|Conocimiento]].

## Cómo se le pide

- «diseñá la pantalla de X», «armá el diseño en Stitch», «pasá la ficha a Stitch», «exportá las pantallas» →
  `cerebro-digital/configuracion-ia/skills/disenar-con-stitch/SKILL.md`.
- «armá un mockup», «mejorá este HTML», un prototipo hecho a mano →
  `cerebro-digital/configuracion-ia/skills/cerebro-mockup-design/SKILL.md`.
- «validá esta maqueta contra las reglas», «pasá este diseño a spec técnica», «¿este toggle tiene regla?» →
  `cerebro-digital/configuracion-ia/skills/cerebro-architect-ui/SKILL.md`.

## Qué hace la IA sola y qué no

Arma el brief sin preguntar lo que la ficha ya dice, y muestra el prompt antes de generar: **cada generación en
Stitch gasta la cuota de la persona y se corre con un «sí»**. La persona pule la pantalla en Stitch y dice cuál
queda. Nada pasa de `borrador/` a `entregables/` sin un pedido explícito (regla 3.1 de [[AGENTS]]). Sin datos de
personas en prompts, pantallas ni capturas; si la maqueta contradice una regla del Cerebro, **gana el Cerebro** y
se avisa.

## El recorrido de una maqueta

1. **Borrador**: `borrador/disenos/<ficha>/`, con el brief (`brief.md`), el HTML y la captura. Nunca se versiona.
2. **Promovida**, con un «sí»: `entregables/disenos/`. La ficha la cita en `fuente_maqueta` (lo escribe
   `cerebro-curator`, con su línea en [[log]]); recién ahí es la **maqueta vigente** y decide textos, botones,
   estados y orden de campos. Una maqueta que ninguna ficha cita no decide nada.
3. **Especificación técnica**: `cerebro-architect-ui` mapea cada control a su regla y la deja en
   `entregables/especificaciones-tecnicas/`; de ahí salen las Tareas de front.
4. **Tokens**: los colores, tipografías y radios que salieron del diseño se proponen para [[diseno-sistema]], con
   un «sí».

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/disenar-con-stitch/SKILL.md` — el flujo con Stitch: precondición, brief, generar, pulir, exportar, promover, tokens y bajada al front.
- `cerebro-digital/configuracion-ia/skills/cerebro-mockup-design/SKILL.md` — los principios visuales, los tokens y los anti-patrones de un diseño «hecho por IA».
- `cerebro-digital/configuracion-ia/skills/cerebro-architect-ui/SKILL.md` — los guardarraíles contra controles cosméticos, estados huérfanos y reglas sin pantalla.
- [[cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index|Integración con Stitch]] — cómo se conecta
  Stitch al asistente, qué herramientas expone, qué exporta y el modo manual sin MCP.

## Dónde va lo del proyecto

| Qué | Dónde |
|---|---|
| Los tokens y componentes del producto | [[diseno-sistema]] |
| La maqueta vigente de cada pantalla | `entregables/disenos/`, citada en `fuente_maqueta` de su ficha ([[plantilla-ficha-flujo]]) |
| Las maquetas en iteración | `borrador/disenos/` (nunca se versiona) |
| La especificación técnica de cada pantalla | `entregables/especificaciones-tecnicas/` |
| Las reglas del front una vez decidido el stack (`DEC-003`) | [[cerebro-digital/modulo-ejemplo/arquitectura/frontend/index|Arquitectura del frontend]] |

_Últ. modif.: 2026-11-27 — @equipo — portada nueva de la sección_
