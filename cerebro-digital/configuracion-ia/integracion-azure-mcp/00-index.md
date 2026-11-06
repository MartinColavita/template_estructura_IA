---
id: integracion-azure-mcp-00-index
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Integración Azure DevOps por MCP — índice"
author: equipo
tags: [azure-devops, mcp, ia, automatizacion, tickets, funcional]
last_updated: 2026-08-26
---

# Integración Azure DevOps por MCP

Esta sección conecta tu asistente de IA (Claude Code, opencode, Antigravity o Gemini CLI) con **Azure DevOps** a través de un **servidor MCP**. Es la pieza que convierte el toolkit de redacción de tickets en algo **operativo**: la IA no sólo escribe el texto del ticket, sino que puede **leer** las tarjetas del tablero y —si vos se lo pedís y confirmás— **crearlas o editarlas** directamente en Azure.

## Qué es MCP (en una línea)

MCP (Model Context Protocol) es un estándar que le da a la IA **herramientas** para hablar con sistemas externos. Un "servidor MCP" es un programita que expone esas herramientas; en este caso, las de Azure DevOps (leer y escribir work items, comentarios, wikis, etc.).

## Qué vas a lograr

- **Leer tarjetas**: pedirle a la IA "traé la tarjeta <ID> y decime qué le falta".
- **Analizar el tablero**: "listá los bugs abiertos del sprint actual".
- **Redactar mejor**: la IA lee la tarjeta pobre, la mejora con el toolkit y te la devuelve lista.
- **(Opcional) Escribir**: "mejorá la <ID> y guardá los cambios" o "creá esta historia en el board X" — siempre con **confirmación humana** antes de tocar Azure.

## Qué NO hace por vos

- No decide sola qué escribir en producción: **vos aprobás** cada alta o edición.
- No maneja tu contraseña de {{ORGANIZACION}}: usa un **token personal (PAT)** con permisos acotados.
- No expone datos personales sensibles: **PHI prohibido** en las tarjetas (ver [[05-seguridad-y-phi]]).

## Modelo de permisos (dos niveles)

| Nivel | Qué permite | Cuándo usarlo |
|---|---|---|
| **Solo lectura** | Leer y analizar tarjetas, comentarios, wikis | Por defecto. La mayoría de los funcionales sólo necesita esto. |
| **Lectura y escritura** | Crear y editar tarjetas, dejar comentarios | Sólo si vas a automatizar el **alta/edición**. Requiere scope extra en el PAT. |

Empezá siempre por **solo lectura**. Subís a escritura sólo cuando lo necesites.

## Índice de la sección

1. [[01-crear-pat-azure]] — Crear tu token personal (PAT) en Azure DevOps y elegir los permisos.
2. [[02-guardar-token-envvar]] — Guardar el token como variable de entorno (nunca en un archivo ni en el chat).
3. [[03-configurar-mcp]] — Registrar el servidor MCP en Claude Code, opencode, Antigravity y Gemini CLI.
4. [[04-automatizar-con-ia]] — El flujo del funcional: redactar → leer/crear/actualizar en Azure.
5. [[05-seguridad-y-phi]] — Reglas de seguridad del token y prohibición de PHI.
6. [[06-troubleshooting]] — Errores típicos (token vencido, permisos, URL de la organización; y el certificado solo si tu red intercepta el TLS) y cómo resolverlos.

## Requisitos previos

- Tener cuenta en el **Azure DevOps de la organización** con acceso al proyecto/tablero.
- Tener instalada la herramienta de IA (Claude Code, opencode, Antigravity o Gemini CLI).
- Tener **Node.js** disponible (el servidor MCP se ejecuta con `npx`).
- (Opcional) Solo si tu red corporativa intercepta el TLS de `dev.azure.com`: tener a mano el certificado de tu red. Para la mayoría de las conexiones no hace falta (ver [[03-configurar-mcp]] y [[06-troubleshooting]]).

> Provenance: los datos de configuración del MCP (server, variables, scopes) son los del servidor elegido en esta guía (`@tiberriver256/mcp-server-azure-devops`). **Es una decisión**: si tu organización usa otro servidor MCP de Azure DevOps, las herramientas cambian de nombre; la tabla de abajo las nombra por función para traducirlas. Si algún dato de tu entorno difiere, marcalo como **pendiente** y consultá antes de asumir.

## Las herramientas por función (para cambiar de servidor sin reescribir las skills)

Las skills y los GATEs de `AGENTS.md` nombran las herramientas del servidor elegido. Si se cambia de
servidor, se completa la tercera columna y se reemplaza en las skills; el GATE no cambia.

| Función | `@tiberriver256/mcp-server-azure-devops` | Otro servidor | Tablero local (`bin/tablero-local.py`) | Jira (MCP de Atlassian; ⚠ verificar los nombres en tu versión) |
|---|---|---|---|---|
| Leer un work item | `get_work_item` | `<completar>` | `ver <id>` | `getJiraIssue` |
| Buscar work items | `search_work_items` / `list_work_items` | `<completar>` | `buscar "<texto>"` / `listar` | `searchJiraIssuesUsingJql` |
| Crear un work item | `create_work_item` | `<completar>` | `crear --tipo … --titulo …` | `createJiraIssue` |
| Actualizar un work item (campos, Estado, comentario vía `System.History`) | `update_work_item` | `<completar>` | `editar` / `estado` / `comentar` | `editJiraIssue` / `transitionJiraIssue` / `addCommentToJiraIssue` |
| Vincular dos work items (Parent / Related) | `manage_work_item_link` | `<completar>` | `vincular <id> <otro> --relacion …` | ⚠ enlaces de issue (`createIssueLink` o el campo `parent`) |
| Leer los comentarios | `get_work_item_comments` | `<completar>` | `ver <id>` (sección Comentarios) | `getJiraIssue` (campo `comment`) |
| Saber quién soy (para `AssignedTo=@Me`) | `get_me` | `<completar>` | `--asignado <nombre>` en `listar` | `atlassianUserInfo` |
