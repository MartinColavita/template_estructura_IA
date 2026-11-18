---
id: gitlab
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: GitLab del proyecto — modulo-ejemplo
description: En qué GitLab vive el proyecto (instancia, grupo, plan y versión), quién mergea, dónde vive la barrera de producción, los runners por alias y las identidades. Lo que no figura en «Destino autorizado» no existe para la IA.
tags: [arquitectura, gitlab, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# GitLab del proyecto — modulo-ejemplo

> **Un GitLab, un grupo o un proyecto que no está en «Destino autorizado» no existe para la IA**, ni para leerlo
> (GATE de GITLAB, en [[AGENTS]]). La tabla la lee un script, siempre igual:
> `python -I bin/auditar-gitlab.py proyecto --instancia <instancia> --ruta <grupo>/<proyecto>`.
> Nace con **una fila de molde**: mientras no haya una fila cargada, el script da `SIN DATOS` y no se pide nada.
> La completa una persona; cada fila que se suma o cambia es una decisión, con su firma en [[log]]. El plan, la
> identidad de la IA y las barreras los fija `DEC-010` (en [[decisiones]]); el método, [[gestion-de-gitlab]].

## Destino autorizado

| Instancia | Ruta (grupo o proyecto) | Ofrecimiento | Plan | Versión | Mirado el |
|---|---|---|---|---|---|
| `<https://host-gitlab>` | `<grupo>` | `<GitLab.com · propia · Dedicated>` | `<Free · Premium · Ultimate>` | `<19.x.y>` | `<aaaa-mm-dd>` |

| Columna | Qué va | Qué **no** va |
|---|---|---|
| **Instancia** | La URL exacta, con `https://`, sin barra final ni `/api/v4` (`https://gitlab.example.com`). GitLab.com es `https://gitlab.com`. Una fila con `http://` no autoriza nada: el token viajaría en claro | La IP |
| **Ruta** | La ruta completa del grupo (`grupo/subgrupo`) o del proyecto (`grupo/proyecto`). Un grupo autoriza todo lo que cuelga de él; un proyecto, sólo ese. Se compara **exacto**, segmento por segmento y con mayúsculas: `Grupo` no es `grupo`, y `grupo-a` no autoriza `grupo-ab`. Si una ruta cabe en dos filas, vale la más específica | Un nombre aproximado |
| **Ofrecimiento** | `GitLab.com` · `propia` (la instancia la administra la organización) · `Dedicated` | — |
| **Plan** | `Free` · `Premium` · `Ultimate`. Decide qué barreras existen; vacío o `⚠` vale como «sin declarar» y lo que pide Premium queda `SIN DATOS` | — |
| **Versión** | La que respondió la instancia (`19.5.4`), sólo si es propia | — |
| **Mirado el** | Fecha en que se miraron el plan y la versión | — |

## Quién mergea y dónde vive la barrera de producción

| Rama o ambiente | Quién empuja directo | Quién mergea | Barrera de producción (según el plan) | Quién la aprueba (rol) |
|---|---|---|---|---|
| `<rama por defecto>` | `<No one>` | `<Maintainers>` | `<Free: rama o tag protegido · Premium: ambiente protegido con aprobación>` | `<rol>` |

## Runners

Por **alias**: si el host es de la organización, el mismo alias que en [[inventario]].

| Alias | Alcance (instancia, grupo o proyecto) | Ejecutor | Etiquetas | Protegido | Quién lo administra (rol) |
|---|---|---|---|---|---|
| `<alias>` | `<proyecto>` | `<docker>` | `<etiqueta>` | `<sí>` | `<rol>` |

## Identidades

La de la IA **no pasa de Developer**: un token de permisos finos por persona, sólo con los proyectos del destino.

| Quién (rol) | Tipo de token | Alcance (recursos y proyectos) | Rol máximo | Vence |
|---|---|---|---|---|
| `<IA de lectura de una persona>` | `<permisos finos>` | `<lectura; proyectos del destino>` | `<Developer>` | `<aaaa-mm-dd>` |

**Servidor MCP elegido:** `<oficial · comunidad · ninguno>` (cómo se configura:
`cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md`).

## Última auditoría

| Fecha | Modo | Veredicto | Dónde quedó el informe |
|---|---|---|---|
| `<aaaa-mm-dd>` | `<proyecto>` | `<OK · HALLAZGO · SIN DATOS>` | `<borrador/gitlab/aaaa-mm-dd/>` (local, no se versiona) |

## Lo que esta ficha no guarda

- **Valores** de tokens, variables o secretos, ni el token de registro de un runner: viven en GitLab y los toca
  sólo una persona.
- **Nombres reales de host** de los runners: van por alias.
- **La salida cruda** del script: queda en `borrador/gitlab/`.
- **La protección misma**: se configura en GitLab. Esta ficha dice qué *debería* haber; que siga ahí lo mide el script.

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-051)_
