---
id: integracion-azure-mcp-01-crear-pat
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Crear el PAT en Azure DevOps"
author: equipo
tags: [azure-devops, pat, token, permisos, scopes, seguridad]
last_updated: 2026-08-26
---

# Crear el PAT en Azure DevOps

El **PAT** (Personal Access Token) es una **contraseña de un solo uso técnico**: le da al servidor MCP permiso para hablar con Azure DevOps **en tu nombre**, sin exponer tu usuario y contraseña reales. Cada persona crea el **suyo** — así queda auditoría por individuo (quién leyó, quién escribió).

> Regla de oro: **mínimo privilegio + caducidad**. Pedí sólo los permisos que vas a usar y ponele fecha de vencimiento.

## Paso a paso

1. Entrá al Azure DevOps de {{ORGANIZACION}} (`https://dev.azure.com/<org>`, donde `<org>` es tu organización).
2. Arriba a la derecha, abrí **User settings** (el ícono de la persona/engranaje) y elegí **Personal Access Tokens**.
3. Clic en **New Token**.
4. Completá:
   - **Name**: algo que reconozcas, ej. `mcp-lectura-tickets` o `mcp-rw-<tu-usuario>`.
   - **Organization**: tu organización de {{ORGANIZACION}}.
   - **Expiration**: ponele una **caducidad corta** (ej. 30 o 90 días). No elijas "sin vencimiento".
   - **Scopes**: elegí según lo que vayas a hacer (ver tabla abajo).
5. Clic en **Create**.
6. Azure te muestra el token **una sola vez**. **Copialo ahora** — no lo vas a poder volver a ver. En el próximo paso lo guardás como variable de entorno: ver [[02-guardar-token-envvar]].

## Qué scopes elegir

Elegí el nivel según tu caso. Si dudás, empezá por **solo lectura**.

### Para LEER / analizar tarjetas (recomendado para arrancar)

| Scope | Nivel | Para qué |
|---|---|---|
| **Work Items** | Read | Leer y buscar tarjetas (historias, tareas, bugs) |
| **Project and Team** | Read | Listar proyectos y equipos |

Con esto la IA puede leer y analizar todo, pero **no puede tocar nada** en Azure. Es el nivel más seguro. (**Wiki (Read)** solo si además querés que lea la wiki; el MCP de tickets no la usa.)

### Paso a paso — config con API token (scope de Work Items: **Read**; **Read, write & manage** sólo si vas a escribir)

Método: **API token (PAT)**, arrancando por solo lectura. Pasos:

1. Azure DevOps → tu foto (arriba a la derecha) → **Personal Access Tokens** → **New Token**.
2. **Name**: `mcp-rw-<tu-usuario>` · **Organization**: `{{AZURE_ORG}}` · **Expiration**: 90 días.
3. **Scopes** → **Show all scopes** → en **Work Items** elegí **Read, write, & manage**; y en **Project and Team** elegí **Read**.
4. **Create** → copiá el token (se muestra **una sola vez**) → guardalo como variable de entorno ([[02-guardar-token-envvar]]).

| Scope | Nivel | Habilita |
|---|---|---|
| **Work Items** | **Read, write & manage** (`vso.work_full`) | Leer/buscar/crear/editar tarjetas, **etiquetas**, **relaciones** (Parent/Related), **comentarios** (`System.History`) y **administrar** (mover/borrar, rutas de área/iteración) |
| **Project and Team** | **Read** (`vso.project`) | Listar proyectos/equipos (`list_projects`) |

Con esos **dos** alcanza para TODO el flujo: crear Épicas/Features/Historias/Tareas/Bugs, enlazarlos, etiquetarlos, comentar y administrar. **No** hacen falta **Code** (repos/PRs), **Build**, **Release** ni **Wiki**. (Test Management solo si más adelante generan casos de prueba desde el Gherkin.)

> **Ojo:** *manage* incluye **borrar** work items y administrar rutas de área/iteración — es más potente. Por eso el flujo **siempre** pide confirmación humana antes de escribir (ver [[04-automatizar-con-ia]]).

## Buenas prácticas

- **Un PAT por persona.** Nunca compartas el tuyo ni uses el de otro: rompe la auditoría.
- **Mínimo scope.** Si sólo vas a leer, no pidas escritura.
- **Caducidad corta.** Renovalo cuando venza; no uses tokens eternos.
- **Un PAT por uso.** Si querés separar "lectura" de "automatización", creá dos tokens distintos con nombres claros.
- Si el token se filtra (lo pegaste sin querer, quedó en un log), **revocalo y creá uno nuevo** de inmediato (ver [[05-seguridad-y-phi]]).

## Recuadro — Ejemplo (genérico)

En un producto de ejemplo, un funcional que sólo investiga bugs y mejora historias del tablero `<board>` crea un PAT `mcp-lectura` con **Work Items (Read)** + **Wiki (Read)** + **Project and Team (Read)**, caducidad 90 días. Con eso la IA lee las tarjetas y las mejora con el toolkit, pero **no puede** modificar el board. Recién cuando el equipo decide automatizar el alta, esa misma persona genera un segundo PAT `mcp-rw` con **Work Items (Read & Write)**.

## Siguiente paso

Guardar el token de forma segura → [[02-guardar-token-envvar]].
