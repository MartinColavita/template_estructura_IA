---
id: integracion-stitch-mcp
tipo: guia
estado: F-Draft
modulo: general
title: Integración con Google Stitch (diseño UX/UI) por MCP
description: Cómo conectar Stitch al asistente (Claude Code, Gemini CLI, opencode, Antigravity), qué herramientas expone, qué exporta y qué guarda el Cerebro.
tags: [stitch, diseno, ux, ui, mcp]
last_updated: 2026-11-02
author: "equipo"
---

# Integración con Google Stitch (diseño UX/UI) por MCP

**Stitch** (`stitch.withgoogle.com`) genera pantallas a partir de texto o imágenes, deja iterarlas en un
canvas (variantes, voz, agente de diseño) y exporta **HTML/CSS** por pantalla (y a Figma por su plugin). En
este ecosistema es **la herramienta de diseño**: el diseño nace y se pule en Stitch; el Cerebro guarda la
exportación como maqueta vigente y, de ahí, `cerebro-architect-ui` la baja a especificación y a Tareas de
front. El flujo completo está en la skill [[disenar-con-stitch]].

> ⚠ **Verificado contra guías de terceros el 2026-11-02; la página oficial `stitch.withgoogle.com/docs/mcp/setup`
> es la fuente.** Si un nombre de herramienta o un comando difiere en tu versión, gana la página oficial y
> se corrige acá.

## Qué hace falta

- Una cuenta de Google con acceso a Stitch y una **API key** creada en `stitch.withgoogle.com/settings`,
  sección *API Keys*. La clave va en una variable de entorno (`STITCH_API_KEY`), **nunca en un archivo
  del repositorio** ni en el chat.
- Ningún Node ni paquete: el servidor es remoto (`https://stitch.googleapis.com/mcp`, transporte HTTP).
- Cuota (según la guía consultada, puede cambiar): unas 350 generaciones por mes en modo estándar y 50 en
  modo experimental. Iterar sin pensar gasta la cuota del mes.

## Registrar el servidor, por herramienta

| Herramienta | Cómo |
|---|---|
| **Claude Code** | `claude mcp add stitch --transport http https://stitch.googleapis.com/mcp --header 'X-Goog-Api-Key: ${STITCH_API_KEY}' -s user` (queda en tu configuración de usuario, fuera del repo). Las comillas simples son a propósito, por lo mismo que en Azure ([[03-configurar-mcp]] §Opción 2). Verificá con `/mcp` que conecte (⚠ si no llega la clave, ver `headersHelper` en la documentación de MCP de Claude Code). Si ya lo habías registrado con comillas dobles, la clave quedó escrita en tu configuración: `claude mcp remove stitch -s user`, registralo de nuevo y generá una clave nueva. |
| **Gemini CLI** | `gemini extensions install https://github.com/gemini-cli-extensions/stitch` (extensión oficial del equipo de Gemini CLI). |
| **opencode / Antigravity** | Un servidor MCP remoto de tipo HTTP con la URL de arriba y el header `X-Goog-Api-Key`; el formato exacto lo fija cada herramienta (⚠ verificar). |

## Las herramientas que expone (las que usa la skill)

| Función | Herramienta | Para qué la usa `disenar-con-stitch` |
|---|---|---|
| Crear un proyecto de diseño | `create_project` | Uno por módulo del Cerebro, una sola vez |
| Listar proyectos / pantallas | `list_projects` · `list_screens` | Reusar el proyecto y ver qué pantallas ya existen |
| Leer un proyecto / una pantalla | `get_project` · `get_screen` | Traer el HTML exportado y los datos de la pantalla |
| Generar una pantalla desde texto | `generate_screen_from_text` (`project_id`, `prompt`, `model_id`: `GEMINI_3_PRO` o `GEMINI_3_FLASH`) | El brief de la ficha, convertido en prompt |
| Captura y código de una pantalla | `get_screen_image` · `get_screen_code` (⚠ según versión; si no existen, se exporta desde la web) | La maqueta para `entregables/disenos/` |

## Qué guarda el Cerebro, y qué no

| Se guarda | Dónde | No se guarda |
|---|---|---|
| La exportación de la pantalla (PNG o HTML) que una ficha cita en `fuente_maqueta` | `entregables/disenos/<pantalla>.*` (promovida con un «sí» desde `borrador/disenos/`) | El proyecto de Stitch entero, ni las variantes descartadas |
| Los tokens que salieron del diseño (colores, tipografías, radios) | `diseno/diseno-sistema.md`, como propuesta con «sí» | Hexadecimales sueltos en skills o mockups |
| El brief que generó la pantalla | En la ficha, sección Pantalla (es trazabilidad) | Datos de personas en prompts o pantallas: **marcadores siempre** |

## Sin MCP (modo manual)

Todo el flujo funciona igual sin servidor: la skill arma el brief y el prompt, la persona lo pega en
`stitch.withgoogle.com`, itera ahí, exporta el HTML y la captura a `borrador/disenos/`, y sigue por el mismo
camino. La diferencia es sólo quién copia y pega.

## Si falla

| Síntoma | Causa probable |
|---|---|
| `401 Unauthenticated` | Clave inválida o vencida: generar otra en Settings |
| `403` al crear un proyecto | La cuenta no tiene acceso a Stitch |
| Genera pantallas que ignoran las reglas | El brief no listó las reglas y los estados: volver a la ficha, no al prompt |
