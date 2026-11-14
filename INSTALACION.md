---
id: instalacion
tipo: guia
estado: F-Verified
modulo: general
title: Instalación del ecosistema de {{PROYECTO}}
description: Qué es canónico y qué es espejo en este repo, y cómo queda instalado cada cliente de IA al clonar.
tags: [okf, instalacion]
last_updated: 2026-10-22
author: "equipo"
---

# Instalación — {{PROYECTO}}

Este repositorio es **solo agentes + Cerebro Digital** (OKF). El código de la aplicación no vive
acá — ver [decisión DEC-001](cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md#dec-001) —:
vive en repositorios de código propios que se clonan adentro de `back/` y `front/`. Nada de este
instructivo scaffoldea código.

## Módulos y qué es canónico vs. espejo

| Módulo | Fuente canónica | Espejos (generados por script; versionados salvo donde se indica) |
|---|---|---|
| Reglas de comportamiento | `AGENTS.md` | `CLAUDE.md` y `GEMINI.md` (import `@AGENTS.md`) |
| Conocimiento de negocio (OKF) | `cerebro-digital/` (sin `configuracion-ia/`) | — (no tiene espejo, se lee directo) |
| Skills | `cerebro-digital/configuracion-ia/skills/` | `.claude/skills/`, `.agents/skills/` |
| Agentes | `cerebro-digital/configuracion-ia/agentes/` | `.claude/agents/`, `.agents/agents/` — **no versionados** (a diferencia de las skills): los materializa `python -I bin/instalar.py` después de clonar |
| Skills scoped de los repos de código | `back/.claude/skills/` y `front/.claude/skills/` | `back/.agents/skills/` y `front/.agents/skills/` (gemelas: no hay fuente única, las dos copias tienen que ser idénticas; lo verifica el hook) |

## Un comando después de clonar

```bash
python -I bin/instalar.py
```

Es el instalador del Cerebro (Python 3, biblioteca estándar, idempotente): comprueba los requisitos (git, Python; Node sólo si se van a usar los MCP), deja activo el hook pre-commit, materializa los espejos de agentes (no viajan en el clone), verifica que los espejos de skills sean idénticos a la fuente y que cada `SKILL.md` cumpla la especificación abierta de Agent Skills (`bin/verificar-skills.py`), avisa si quedan placeholders sin instanciar o falta el `.gemini/.env`, y lista lo que sigue. `--dry-run` muestra sin tocar. Tres salidas: OK, HALLAZGO (algo que arreglar, con el comando) y SIN DATOS (no es un repositorio del Cerebro).

## Carga por herramienta

Skills: cero pasos en las cuatro herramientas (viajan con el clone). **Agentes: los materializa el
instalador** (o `bin/sync-agents.sh` / `.ps1` a mano) una sola vez después de clonar.

- **Claude Code**: `.claude/skills/` ya trae las **33 skills** — invocables con `/nombre-de-la-skill`. `CLAUDE.md` carga las reglas de `AGENTS.md` automáticamente (Claude Code leería `AGENTS.md` solo únicamente si no hubiera ningún `CLAUDE.md`, desde la v2.1.277, y un `CLAUDE.local.md` también lo apaga; con el import funciona en toda versión). `/context` muestra qué cargó y `/doctor prompt-audit` revisa que las instrucciones no hayan envejecido. Los agentes (`/agents` o invocación automática) requieren haber corrido el instalador.
- **Antigravity**: lee `AGENTS.md` nativamente y las skills desde `.agents/skills/`. Los agentes los materializa el instalador.
- **opencode**: auto-descubre `AGENTS.md` (vía `"instructions"` en `opencode.json`, versionado) y escanea por defecto tanto `.agents/skills/` como `.claude/skills/`.
- **Gemini CLI**: `GEMINI.md` en la raíz importa las reglas con `@AGENTS.md`, igual que `CLAUDE.md`, y las skills se auto-descubren de `.agents/skills/` (alias documentado de `.gemini/skills/`). `gemini skills list` o `/skills` en la sesión muestran lo que cargó. No hay que pegar nada a mano (Gemini leería `AGENTS.md` sólo si cada persona lo agrega a `context.fileName`). Que un modelo cumpla las reglas se mide con `bin/probar-reglas.*`.
- **Si tu herramienta no está en esta lista**: primero fijate si ya lee `AGENTS.md` de forma nativa — en ese caso funciona sin tocar nada. Si tiene su propia convención de archivo pero no lee `AGENTS.md` sola, agregale un archivo-loader de una línea (`@AGENTS.md`), mismo patrón que `CLAUDE.md`. Si no tiene ninguna convención de proyecto, pegá `AGENTS.md` a mano en el contexto.

## Para el mantenedor (cuando cambiás skills o agentes)

Tras editar cualquier `SKILL.md` en `cerebro-digital/configuracion-ia/skills/`, regenerá los dos espejos **antes de commitear**
(los dos envoltorios llaman a `bin/sync-espejos.py`: hace falta Python 3):

```bash
# Linux / macOS / Git Bash
bin/sync-skills.sh
```
```powershell
# Windows PowerShell
bin/sync-skills.ps1
```

Tras editar cualquier `.md` en `cerebro-digital/configuracion-ia/agentes/`, mismo mecanismo con `bin/sync-agents.sh` (o `.ps1`), y además hace falta correrlo **una vez por dev** (no viaja con el clone, ver «Carga por herramienta» arriba).

**Guardarraíl:** hay un hook pre-commit versionado en `.githooks/`. Se activa una vez por dev con:

```bash
git config core.hooksPath .githooks
```

A partir de ahí, si intentás commitear con algún espejo desincronizado, con un conteo de skills desactualizado, con un archivo con BOM o con caracteres de control invisibles, el commit se frena y te dice qué corregir. Quien solo clona no necesita nada — los hooks no viajan activados en el clone.

**Atajo:** `bin/actualizar.sh` (o `.ps1`) hace `git pull` y corre el instalador (hook, espejos, agentes, especificación de skills). Corrélo después de traer cambios.

**Especificación de skills:** `bin/verificar-skills.py` exige lo que piden la [especificación abierta de Agent Skills](https://agentskills.io/specification) y Claude Code: `name` igual a la carpeta, en minúsculas con guiones y hasta 64 caracteres; `description` no vacía y de hasta 1024 caracteres (Claude Code la corta en 1536, Gemini CLI y opencode siguen la especificación); y avisa si un `SKILL.md` pasa de 500 líneas. Lo corre el hook, el instalador y el pipeline.

**En el servidor:** `.gitlab-ci.yml` (GitLab) y `.github/workflows/verificar.yml` (GitHub) corren en cada push los espejos, la especificación y el conteo de skills, el BOM y los caracteres de control (`bin/verificar-staged.py --todo`), las pruebas de `bin/` y el Doctor, con sólo Python y git: el hook es local y se saltea con `--no-verify`, el servidor no. Las listas de `README.md` e `index.md` siguen sólo en el hook. En otra plataforma se traducen esos tres pasos.

> `opencode` puede reportar la ubicación de una skill de forma inconsistente entre sesiones (tiene el mismo contenido en dos rutas) — no afecta el comportamiento y puede degradar su cacheo de prompt; es un trade-off aceptado. opencode escanea `.opencode/skills/`, `.claude/skills/` y `.agents/skills/` y no documenta una variable para apagar una ruta.

## Integraciones externas

- **Azure DevOps (MCP)**: el tablero de trabajo. Documentado en [`cerebro-digital/configuracion-ia/integracion-azure-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-azure-mcp/00-index.md). El único tablero donde las skills pueden escribir se declara en `tablero/conocimiento/tablero-autorizado.md`.
- **GitLab (MCP)**: para leer Merge Requests y sus notas de revisión en los repos de código, y —si el equipo lo habilita— comentarlos. Guía: [`cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md). Sin el MCP el proyecto funciona igual: los Merge Requests se abren y se leen a mano.
- **Google Stitch (MCP, diseño UX/UI)**: donde se diseñan y se pulen las pantallas. Servidor remoto con API key por máquina (`STITCH_API_KEY`); guía: [`cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md). Sin MCP, la skill `disenar-con-stitch` funciona en modo manual.
- **Engram (memoria persistente, MCP)**: corre como binario local; la configuración (`.mcp.json`, `.engram/config.json`) es por máquina y está gitignoreada — cada colaborador la arma con su propia instalación. Protocolo de uso: skill `engram-memory-protocol`.

## Decisiones abiertas relacionadas

- `DEC-001` (código de la aplicación fuera de este repo) viene decidida con el template. Queda pendiente, en los repos de código, decidir el stack técnico (`DEC-003`) y completar `tdd-stack-back.md` / `tdd-stack-front.md` de la skill `desarrollo`.
