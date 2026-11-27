---
id: seccion-qa
tipo: indice
estado: F-Draft
modulo: general
title: "QA y pruebas de punta a punta"
description: Portada de la sección transversal de QA — el plan de pruebas de aceptación desde el Gherkin y las pruebas de punta a punta de la aplicación desplegada; cómo se le pide a la IA, las guías, los scripts, la decisión que fija el motor y dónde va lo del proyecto.
tags: [qa, pruebas, e2e, aceptacion, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# QA y pruebas de punta a punta

Cómo se prueba **la aplicación desplegada** contra los Escenarios de cada Historia, de afuera, como la usa una
persona. Esta sección es **transversal**: es la portada del método, que vive en las skills. Las pruebas en sí viven
en `qa/`, en la raíz de este repositorio, versionadas (la excepción de `DEC-001`, M-045): qué capa prueba qué y
cómo se ata cada prueba a su Historia está en `qa/README.md`.

| Rol | Skill | Qué deja |
|---|---|---|
| Tester | `disenar-pruebas` | El plan de pruebas de aceptación, como comentario corto en la Historia |
| QA automatización | `automatizar-e2e` | Las pruebas de punta a punta en `qa/`, con el motor que fija `DEC-003` |

Las dos se piden por la puerta `desarrollo`, que también las atiende.

## Qué cubre y qué no

**Cubre:**

- Qué Escenarios del Gherkin se automatizan de punta a punta y cuáles quedan exploratorios, con su motivo.
- Los datos y el estado inicial de cada corrida (fábricas y marcadores, nunca datos de personas).
- Las pruebas de punta a punta por tipo de aplicación: web, Electron, escritorio, móvil, línea de comandos, API.
- La cobertura: qué Escenario tiene prueba, cuál es sólo esqueleto y cuál no tiene nada.

**No cubre:**

- Los tests unitarios, de contrato y de integración, que viven en el repositorio del código →
  [[cerebro-digital/desarrollo/index|Desarrollo]].
- La prueba dinámica de seguridad contra una aplicación que corre → [[cerebro-digital/seguridad/index|Seguridad]].
- Redactar la Historia o su Gherkin → [[cerebro-digital/tickets/index|Tickets]]. Sin Gherkin, QA frena.

## Cómo se le pide

- «diseñá las pruebas de la Historia X», «qué probamos de punta a punta», «armá el plan de pruebas» →
  `cerebro-digital/configuracion-ia/skills/disenar-pruebas/SKILL.md`.
- «automatizá la Historia X», «escribí las pruebas de punta a punta», «qué cobertura e2e tenemos» →
  `cerebro-digital/configuracion-ia/skills/automatizar-e2e/SKILL.md`.

## Qué hace la IA sola y qué no

Arma el plan y lo muestra; con el «sí», queda como comentario en la Historia. Escribe las pruebas siguiendo el
Gherkin paso a paso, **sin inventar**: lo que la Historia no dice vuelve como pregunta. **Nunca corre contra
producción**; el ambiente y las credenciales van por variable de entorno. Un esqueleto no cuenta como prueba.

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/disenar-pruebas/SKILL.md` — el plan: qué se automatiza, bordes que la tarjeta no tiene, datos, lista exploratoria, identificadores que el front tiene que exponer.
- `cerebro-digital/configuracion-ia/skills/automatizar-e2e/SKILL.md` — el motor por tipo de aplicación, los pasos y cómo entra en el veredicto.
- `cerebro-digital/configuracion-ia/skills/automatizar-e2e/references/playwright.md` — Playwright: web, Electron y el front de una app con webview.
- `cerebro-digital/configuracion-ia/skills/automatizar-e2e/references/otros-tipos.md` — escritorio, móvil, línea de comandos y API, cuando no hay navegador.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/pruebas-de-aceptacion.md` — la capa que prueba el sistema desplegado, qué expone el front y cuándo corre.

## Los scripts

- `bin/armar-e2e.py` — el esqueleto de las pruebas de una Historia desde su Gherkin: un test por Escenario, con el título textual, la traza `Historia #id · Escenario` y cada uno marcado sin automatizar; no pisa lo que existe.
- `bin/cobertura-e2e.py` — por Historia y Escenario, qué tiene prueba automatizada, qué es sólo esqueleto y qué no tiene nada; vale para cualquier motor porque lee la traza.

## La decisión que lo fija

`DEC-003` — Stack técnico: el tipo de aplicación y su motor de punta a punta (Playwright, WebDriver, Appium o
Maestro, proceso, HTTP), el atributo de identificación estable, y la herramienta, el ambiente y si las pruebas de
aceptación frenan la entrega. Vive en [[decisiones]], en `⚠` hasta que el equipo la decida; mientras tanto, la capa
de aceptación es `SIN DATOS`.

## Dónde va lo del proyecto

| Qué | Dónde |
|---|---|
| Las pruebas de punta a punta | `qa/e2e/` (o `qa/<app>-e2e/` con varias aplicaciones), versionadas acá |
| El plan de pruebas de cada Historia | Un comentario en su tarjeta, no un archivo |
| Lo que falta en la Historia para probar | Una pregunta a la Historia (`comentar-tarea`) |
| El motor, el ambiente y el identificador estable | [[decisiones]] (`DEC-003`) |

_Últ. modif.: 2026-11-27 — @equipo — sección nueva del Cerebro_
