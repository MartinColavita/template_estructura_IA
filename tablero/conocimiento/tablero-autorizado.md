---
id: tablero-autorizado
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Tablero autorizado — guard de escritura (solo {{AZURE_PROYECTO}})"
author: equipo
tags: [azure-devops, guard, seguridad, tablero, restriccion]
last_updated: 2026-08-28
---

# Tablero autorizado — guard de escritura

El PAT de Azure DevOps da acceso a **toda la organización** (no se puede acotar por proyecto en el token). Por eso la restricción de "en qué tablero puede operar el agente" vive **acá, en el skill**, no en el token.

## Tablero local (modo solo, `DEC-006`)

Si el proyecto fijó el **tablero local**, el único tablero autorizado es la carpeta
`cerebro-digital/<modulo>/backlog/` y toda lectura o escritura va por `bin/tablero-local.py`: no hay MCP, no
hay PAT y el guard es la ruta. Los GATEs de `AGENTS.md` aplican igual (dedup con `buscar`, confirmación, nivel,
borrado con `--confirmado`, tarjeta congelada por `estado`). Lo que sigue aplica cuando el tablero es Azure DevOps.

## Jira u otro tablero por MCP (modo equipo, `DEC-006`)

El guard es el mismo con otro dato duro: la **clave del proyecto** (o el espacio) autorizado, que se escribe acá y
en [[contexto-proyecto]]; antes de crear, editar o comentar se verifica que el destino coincida exactamente. Las
operaciones se traducen con la tabla de herramientas por función de `integracion-azure-mcp/00-index.md`, y el
método del toolkit (plantillas, checklists, GATEs) vale igual. Lo que sigue aplica a Azure DevOps.

## Único tablero autorizado (dato duro)

- **Organización:** `{{AZURE_ORG}}` — `https://dev.azure.com/{{AZURE_ORG}}`
- **Proyecto / board:** `{{AZURE_PROYECTO}}`
- **Team:** `{{AZURE_TEAM}}`
- **URL de referencia:** `https://dev.azure.com/{{AZURE_ORG}}/%7B%7BAZURE_PROYECTO%7D%7D/_backlogs/backlog/%7B%7BAZURE_TEAM%7D%7D/Epics`

(Fuente única del dato: [[contexto-proyecto]] §Azure DevOps. Si el proyecto real usa otro string exacto —p. ej. plural— se corrige acá y en [[contexto-proyecto]], en un solo lugar.)

## Acceso del token (verificar antes de operar)

El PAT del MCP **debe tener acceso** al proyecto autorizado. **Antes de operar, verificarlo con un smoke test de solo lectura**: listar los proyectos de la organización (`list_projects`) y leer un work item cualquiera de `{{AZURE_PROYECTO}}` (`get_work_item`). Si el proyecto no aparece en la lista o devuelve **"Project not found"**, el token no sirve para este tablero (Azure responde igual si el proyecto no existe **o** si el token no tiene permiso): hace falta un token con acceso a ese proyecto, y hasta tenerlo **no se opera el pipeline**. El guard sigue siendo correcto en todos los casos: si el destino no es el autorizado, **no se escribe**.

## Guard (obligatorio antes de escribir)

Antes de CUALQUIER `create_work_item` / `update_work_item` / `manage_work_item_link` (alta, edición, asignación, cambio de estado o comentario):

1. El destino es **siempre** el tablero autorizado de arriba: el skill usa ese `project` / `team`, no otro.
2. Si el pedido nombra **otro** org/proyecto/team, o el destino no se puede determinar con certeza → **NO se escribe**. Se muestra la advertencia y se frena.
3. (Recomendado) verificar la organización real contra `AZURE_DEVOPS_ORG_URL` / `get_me` antes del primer write; si no es `{{AZURE_ORG}}`, abortar.
4. Las **lecturas** (consultar/auditar) también se acotan al proyecto autorizado; si se consultara otro, avisar.

## Advertencia (texto para mostrar y frenar)

> ⛔ **Tablero no autorizado.** El destino (org=`<X>` / proyecto=`<Y>` / team=`<Z>`) no coincide con el único tablero autorizado (org=`{{AZURE_ORG}}` / proyecto=`{{AZURE_PROYECTO}}` / team=`{{AZURE_TEAM}}`). **No creé ni modifiqué ningún work item.** Si hay que operar en otro tablero, pedí autorización explícita para cambiar el tablero autorizado en [[contexto-proyecto]].

## Cambiar el tablero autorizado

Se cambia **solo** editando [[contexto-proyecto]] (§Azure DevOps) con confirmación humana. No se "autoriza" un tablero distinto por un pedido suelto en el chat.
