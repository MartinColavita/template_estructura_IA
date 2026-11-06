---
id: integracion-azure-mcp-04-automatizar
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Automatizar tickets con IA (el flujo del funcional)"
author: equipo
tags: [azure-devops, mcp, ia, flujo, work-items, confirmacion, funcional]
last_updated: 2026-10-01
---

# Automatizar tickets con IA (el flujo del funcional)

Esta es la parte que te ahorra trabajo. Con el MCP configurado ([[03-configurar-mcp]]), la IA puede **leer** una tarjeta, **mejorarla** con el toolkit de redacción y —si vos lo pedís y confirmás— **crearla o actualizarla** en Azure. Vos seguís mandando; la IA ejecuta.

## El flujo en 3 pasos

1. **Redactar** — la IA convierte una tarjeta pobre (o una idea suelta) en un ticket profesional usando el toolkit (historia/tarea/bug, criterios de aceptación en Gherkin español, DoR/DoD).
2. **Leer / traer** — la IA usa el MCP para **leer** la tarjeta real de Azure (`get_work_item`), así trabaja sobre el contenido verdadero, no sobre lo que vos recordás.
3. **Escribir (opcional)** — si querés, la IA **crea** (`create_work_item`) o **actualiza** (`update_work_item`) la tarjeta en el board. **Siempre te muestra qué va a escribir y espera tu OK.**

## Herramientas del MCP que entran en juego

| Herramienta | Qué hace | Nivel |
|---|---|---|
| `list_projects` | Lista los proyectos/boards disponibles | Lectura |
| `get_work_item` | Trae una tarjeta por su ID | Lectura |
| `search_work_items` / `list_work_items` | Busca/lista tarjetas (por sprint, estado, responsable) | Lectura |
| `get_work_item_comments` | Trae los comentarios de una tarjeta | Lectura |
| `create_work_item` | **Crea** una tarjeta nueva | Escritura |
| `update_work_item` | **Edita** una tarjeta existente | Escritura |
| `manage_work_item_link` | **Enlaza** dos work items (Parent/Child, Related, Predecesor/Sucesor) | Escritura |

> **Comentar una tarjeta** se hace con `update_work_item` sobre el campo `System.History` (así lo usa la skill `comentar-tarea`); `get_work_item_comments` los lee. `add_pull_request_comment` existe en el server pero es para pull requests, no para work items.

Las de **escritura** sólo funcionan si tu PAT tiene scope **Read & Write** ([[01-crear-pat-azure]]).

> **Lo que el MCP no trae: el historial por campo.** `get_work_item` da cómo está la tarjeta
> **ahora**, no qué cambió en cada revisión. Para saber si el sello de una auditoría sigue
> vigente hace falta justamente eso, así que lo lee un script de **solo lectura**,
> `bin/verificar-sello.sh` (o `.ps1`). Entra igual que el MCP: con `AZDO_PAT` o, si no está,
> con la sesión de Azure CLI (`az login`). Detalle en la skill
> `auditar-tarea` §3-bis. Se prueba sin red con `python bin/probar-verificar-sello.py`.

> **Lo que se cuenta, lo cuenta un script.** Los chequeos de conteo y de forma de las
> auditorías no los hace el modelo: los hacen `bin/auditar-tarea.py`, `bin/auditar-historia.py`
> y `bin/analizar-tareas.py`, sobre los archivos de la tarjeta (el borrador o lo guardado del
> tablero). Cuentan siempre igual, tardan segundos y no gastan tokens. El modelo queda para lo
> que pide criterio: lo que cada script lista al final de su reporte. El modo lote lo maneja
> `bin/lote.py`, que prepara la carpeta, arma las misiones de los sub-agentes, corre las
> auditorías, escribe la tabla del cierre, compara la tarjeta con el archivo auditado antes de
> sellar y mide cuánto tardó cada fase. Ninguno escribe en Azure ni en GitLab. Las skills los
> corren solas; sólo si la herramienta no tiene terminal le pasan a la persona el comando. Se
> prueban sin red con `python -B bin/probar-auditar-tarea.py`, `probar-auditar-historia.py`,
> `probar-analizar-tareas.py` y `probar-lote.py`.

> **¿El modelo cumple estas reglas? Se mide, no se supone.** `bin/probar-reglas.sh` (o `.ps1`)
> le pasa a Gemini CLI o a Claude Code nueve casos armados —tarjeta congelada, comentario de
> cierre, nivel de las Tareas, el arranque de un lote, duplicado, etiquetas— y revisa cada respuesta: que las reglas
> citadas existan en el Cerebro, que ningún GATE diga OK sin tablero, una sola etiqueta, HTML
> sin markdown. Corre **con todos los MCP apagados** y **sin herramientas de escritura**: Gemini
> en su modo de sólo lectura (`plan`), Claude con sólo las de leer. Verificado:
> a las dos se les pidió crear un archivo, también por la terminal, y ninguna pudo. Gasta la
> cuota de quien lo corre (unos 20 minutos). Las respuestas completas quedan en
> `borrador/pruebas-reglas/` para **leerlas a mano**: los chequeos son señales, y un OK no prueba
> que la respuesta esté bien. `--herramienta claude`, `--modelo <modelo>` y `--casos 3,6`
> cambian qué se prueba. Correlo después de tocar las reglas o las skills del pipeline.

## Relaciones y alta en lote

- **Enlazar tickets:** para poner un **Parent** (jerarquía) o una relación **Related** (mismo tema), la IA primero **resuelve el `#ID`** real (con `search_work_items`/`list_work_items` — el número es dato duro, no se inventa) y luego crea el vínculo con `manage_work_item_link`, **tras tu OK**. El Parent se crea **siempre desde la hija** (o directo en el alta, con `parentId`): el MCP escribe sobre el ítem de origen, y así no se escribe en una tarjeta que no es la que se está cargando. Ver [[organizacion-y-trazabilidad]] §2.
- **Bajar un módulo entero (alta en lote):** la IA puede crear la **jerarquía completa** (Épica + Features + UHs, con el mapeo Vertical slice→Épica·Capacidad→Feature·Flujo→Historia) en una tanda: `create_work_item` por nodo + `manage_work_item_link` para colgarlos. **Primero te muestra el árbol propuesto y espera el "dale"**; recién ahí escribe. Todos los tickets llevan la **etiqueta temática** y el **documento fuente** por referencia. Ver [[organizacion-y-trazabilidad]] §5.

## Ejemplos de pedidos (lo que le decís a la IA)

### Sólo lectura / análisis

- "Traé la tarjeta **<ID>** y decime qué le falta para cumplir el DoR."
- "Listá los **bugs abiertos** del sprint actual del board X y ordenalos por gravedad."
- "Leé la historia <ID> y sus comentarios, y resumime el estado."

### Mejorar y guardar (escritura, con confirmación)

- "**Mejorá la tarjeta <ID>** con el toolkit y **guardá** los cambios en Azure."
- "Tomá esta idea y **creá una historia** en el board X: «como operador quiero...»."
- "Pasá los criterios de aceptación de la <ID> a **Gherkin en español** y **actualizá** la tarjeta."

## Barreras al escribir

Las barreras al escribir en el board (**leer es libre; escribir solo con tu confirmación**, mostrar el diff antes del OK, tablero autorizado, deduplicación, confirmación en turnos distintos, nivel funcional/dev, un board por vez, no PHI, no inventar) son las de **`AGENTS.md`** — valen íntegras acá; el MCP es solo el transporte. Un par de prácticas del flujo: trabajá sobre lo real (que la IA **traiga la tarjeta** con `get_work_item` antes de mejorarla) y revisá el **diff** antes del OK (a veces "mejorar" toca el título o el tipo). PHI y seguridad del token: [[05-seguridad-y-phi]].

## Recuadro — Ejemplo (genérico)

En un producto de ejemplo, un funcional usa la skill de redacción para convertir un bug pobre ("no anda, ver adjunto") en un ticket con **Pasos para reproducir**, **Gravedad** y criterios. La IA primero hace `get_work_item` de la tarjeta en `<board>`, la reescribe respetando el estilo de casa (User Story/Task/Bug, etiquetas `FE_x.y.z`), la muestra, y sólo tras el OK del funcional hace `update_work_item`. Si al bug le falta el dato de la persona, no lo inventa: deja `<persona>` y pregunta.

## Siguiente paso

Reglas de seguridad y PHI → [[05-seguridad-y-phi]].
