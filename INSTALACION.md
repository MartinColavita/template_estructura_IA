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

- **Claude Code**: `.claude/skills/` ya trae las **38 skills** — invocables con `/nombre-de-la-skill`. `CLAUDE.md` carga las reglas de `AGENTS.md` automáticamente (Claude Code leería `AGENTS.md` solo únicamente si no hubiera ningún `CLAUDE.md`, desde la v2.1.277, y un `CLAUDE.local.md` también lo apaga; con el import funciona en toda versión). `/context` muestra qué cargó y `/doctor prompt-audit` revisa que las instrucciones no hayan envejecido. Los agentes (`/agents` o invocación automática) requieren haber corrido el instalador.
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

A partir de ahí, si lo que vas a commitear deja algún espejo de skills distinto de su fuente, un conteo de skills desactualizado, un archivo con BOM o con caracteres de control invisibles, el commit se frena y te dice qué corregir. Mira lo que entra al commit, no el disco: un cambio sin `git add` en otra parte no lo frena. Los espejos de agentes no se versionan: si están viejos, avisa y no frena. Quien solo clona no necesita nada — los hooks no viajan activados en el clone.

**Atajo:** `bin/actualizar.sh` (o `.ps1`) hace `git pull` y corre el instalador (hook, espejos, agentes, especificación de skills). Corrélo después de traer cambios.

**Especificación de skills:** `bin/verificar-skills.py` exige lo que piden la [especificación abierta de Agent Skills](https://agentskills.io/specification) y Claude Code: `name` igual a la carpeta, en minúsculas con guiones y hasta 64 caracteres; `description` no vacía y de hasta 1024 caracteres (Claude Code la corta en 1536, Gemini CLI y opencode siguen la especificación); avisa si un `SKILL.md` pasa de 500 líneas; y frena si pasa de 12.500 caracteres (unos 5.000 tokens, medidos con el modelo a ~2,6 caracteres por token: al compactar una conversación, Claude Code vuelve a cargar cada skill usada hasta ese tope y corta el final, así que lo que no se negocia va arriba y el detalle a `references/`), con aviso desde 12.000. Lo corre el hook, el instalador y el pipeline.

**En el servidor:** `.gitlab-ci.yml` (GitLab) y `.github/workflows/verificar.yml` (GitHub) corren en cada push los espejos, la especificación, el conteo y las listas de skills, el BOM y los caracteres de control (`bin/verificar-staged.py --todo`), las pruebas de `bin/` y el Doctor, con sólo Python y git: el hook es local y se saltea con `--no-verify`, el servidor no. En otra plataforma se traducen esos tres pasos.

> `opencode` puede reportar la ubicación de una skill de forma inconsistente entre sesiones (tiene el mismo contenido en dos rutas) — no afecta el comportamiento y puede degradar su cacheo de prompt; es un trade-off aceptado. opencode escanea `.opencode/skills/`, `.claude/skills/` y `.agents/skills/` y no documenta una variable para apagar una ruta.

## Un orquestador por función (sesión dedicada, opcional)

Cada función tiene una skill «puerta», que es el rol de su orquestador. En la sesión de siempre la puerta se carga
cuando el pedido es de su función: la nombran `AGENTS.md` y la skill `cerebro-orquestador`, así que no depende de que
su descripción entre en el listado de skills. Para un trabajo largo de una sola función se puede abrir una **sesión
dedicada** con su agente:

| Función | Sesión dedicada | Puerta que carga |
|---|---|---|
| Conocimiento | `claude --agent orquestador-conocimiento` | `cerebro-orquestador` |
| Arquitectura e infraestructura | `claude --agent orquestador-arquitectura` | `arquitectura-e-infraestructura` |
| CI/CD y despliegue | `claude --agent orquestador-despliegue` | `despliegue-continuo` |
| Operación de servidores | `claude --agent orquestador-operacion` | `operacion-de-servidores` |
| Seguridad | `claude --agent orquestador-seguridad` | `seguridad` |
| GitLab | `claude --agent orquestador-gitlab` | `gestion-de-gitlab` |

El orquestador coordina y no debe escribir archivos (la lista negra no alcanza a la terminal): delega en `nucleo-productor` y en `nucleo-verificador` (éste, en sólo
lectura y con contexto limpio). Hace falta haber corrido el instalador, que materializa los agentes. Es propio de
Claude Code: en las otras tres herramientas se usa la puerta en la sesión de siempre. Los orquestadores de las cinco
funciones nuevas no tienen instrucciones propias (su archivo es sólo la cabecera): por eso **no se usan como
subagentes**, y `.claude/settings.json` los bloquea como tales (`permissions.deny` con `Agent(orquestador-…)`): lanzado
como subagente, un orquestador perdería su lista de herramientas. Ese bloqueo no impide abrirlo con `claude --agent`
(probado). `python -I bin/sesion-proyecto.py --verificar` controla que ningún agente de sesión principal quede sin
bloquear. ⚠ Sin probar en una sesión interactiva: que el orquestador pregunte con la herramienta nativa de
preguntas; si no la tiene, pregunta en el texto y espera.

**Sesión aislada del proyecto (recomendada en una máquina con muchos plugins o MCP).** `python -I
bin/sesion-proyecto.py` abre Claude Code sin tu configuración de usuario (ni plugins ni skills personales), con sólo
los MCP del `.mcp.json` del proyecto y sin los conectores de claude.ai; `python -I bin/sesion-proyecto.py --agent
orquestador-seguridad` hace lo mismo con la sesión de una función. Así las descripciones de las puertas entran en el
listado y no quedan a mano herramientas de otros proyectos (en una máquina real: de 45 servidores MCP y 119 skills a
0 y 62). `--verificar --en-vivo` abre una sesión corta y comprueba qué cargó. Quien quiera sus plugins en este
proyecto abre `claude` como siempre.

**Cómo se sabe qué skill corrió.** Al cerrar cada sesión, `bin/registrar-sesion.py` anota en
`cerebro-digital/configuracion-ia/sesiones.jsonl` qué skills se usaron y cuántas veces; `python -B
bin/medir-uso-skills.py` lo junta de todas las sesiones de la máquina y dice cuáles no se usaron nunca. Y que cada
skill tenga su ruta escrita (para no depender de su descripción) lo verifica `bin/verificar-skills.py` en el hook y
en el servidor.

## Ver el Cerebro en Obsidian (opcional)

Obsidian es un **visor**: muestra el Cerebro como un grafo de notas enlazadas. No es otra fuente ni otro camino de
escritura (al Cerebro lo escribe `cerebro-curator`) y no hace falta para nada más.

1. Instalar Obsidian y elegir **Open folder as vault** sobre **la raíz de este repositorio**. No sobre
   `cerebro-digital/`: se cortarían los enlaces a `tablero/` y a `AGENTS.md`.
2. Abrir la vista de grafo. La configuración viaja con el repositorio (`.obsidian/app.json` y
   `.obsidian/graph.json`): oculta lo que no es conocimiento (`borrador/`, `documentos/`, el código clonado, las
   skills) y pinta cada nota según su `tipo` y su carpeta.
3. Nada más: no se instala ningún plugin de la comunidad ni ningún MCP. Claude Code ya lee esos mismos archivos.

Qué conviene saber:

- Un enlace a una skill por su nombre (`[[comentar-tarea]]`) **no resuelve** en Obsidian, porque el archivo de toda
  skill se llama `SKILL.md`; el grafo los oculta. Las skills, los scripts y las decisiones se ven en
  `INFORME-ESQUELETO.html`.
- Obsidian reescribe `graph.json` cuando se toca el panel del grafo: ese cambio no se commitea salvo que se acuerde.
  Lo demás que Obsidian guarda en `.obsidian/` es de cada máquina y git lo ignora.
- Una edición hecha desde Obsidian pasa igual por el hook y por la revisión.
- ⚠ **Sin probar en una instalación real**: el formato de `graph.json` y de la lista de carpetas ocultas sale de
  fuentes de terceros que coinciden entre sí, no de la ayuda oficial. Si algo no se ve como dice acá, se ajusta
  desde la interfaz (Settings → Files and links → Excluded files) y se commitea el archivo que queda.

## Integraciones externas

- **Azure DevOps (MCP)**: el tablero de trabajo. Documentado en [`cerebro-digital/configuracion-ia/integracion-azure-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-azure-mcp/00-index.md). El único tablero donde las skills pueden escribir se declara en `tablero/conocimiento/tablero-autorizado.md`.
- **GitLab (MCP)**: para leer Merge Requests y sus notas de revisión en los repos de código, y —si el equipo lo habilita— comentarlos. Guía: [`cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md). Sin el MCP el proyecto funciona igual: los Merge Requests se abren y se leen a mano.
- **Google Stitch (MCP, diseño UX/UI)**: donde se diseñan y se pulen las pantallas. Servidor remoto con API key por máquina (`STITCH_API_KEY`); guía: [`cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md`](cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md). Sin MCP, la skill `disenar-con-stitch` funciona en modo manual.
- **Engram (memoria persistente, MCP)**: corre como binario local; la configuración (`.mcp.json`, `.engram/config.json`) es por máquina y está gitignoreada — cada colaborador la arma con su propia instalación. Protocolo de uso: skill `engram-memory-protocol`.

## Decisiones abiertas relacionadas

- `DEC-001` (código de la aplicación fuera de este repo) viene decidida con el template. Queda pendiente, en los repos de código, decidir el stack técnico (`DEC-003`) y completar `tdd-stack-back.md` / `tdd-stack-front.md` de la skill `desarrollo`.
