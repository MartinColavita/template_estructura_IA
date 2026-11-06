---
id: organizacion-y-trazabilidad
tipo: concepto
estado: F-Draft
modulo: integracion-azure-devops
title: "Organización y trazabilidad del backlog: tags, relaciones, documento fuente, reglas y mapeo OKF→ADO"
author: equipo
tags: [azure-devops, tags, etiquetas, relaciones, links, trazabilidad, reglas-negocio, okf, jerarquia]
last_updated: 2026-10-01
---

# Organización y trazabilidad del backlog

Cómo dejar el backlog **ordenado y trazable**: un **tag temático** en cada ticket, **relaciones/links** entre tickets, la **referencia al documento fuente** (barata, sin duplicar contenido), los **códigos de regla de negocio** y el **mapeo de un módulo funcional a la jerarquía de Azure**. Agnóstico de dominio; los recuadros "Ejemplo (genérico)" son solo ilustrativos.

Relacionados: [[mapa-campos-azure]] · [[historias-de-usuario]] · [[criterios-aceptacion-gherkin]] · [[bugs-y-defectos]]

---

## 1. Tag temático (etiqueta que engloba un tema) — UNO, y solo uno

Cada ticket lleva **exactamente una etiqueta**: el **tag temático**, que agrupa el tema/asunto al que pertenece. Sirve para **filtrar de un saque todos los tickets de un mismo tema** (una épica funcional, un flujo, un módulo) aunque estén repartidos en Historias, Bugs y Tareas — y para que la **deduplicación** (buscar por tag antes de crear, ver [[deduplicacion-antes-de-crear]]) funcione: un ticket por tema bajo **un único** tag, no fragmentado bajo distintas combinaciones.

- **Techo duro: UN solo tag por ticket.** No hay "tags opcionales" de producto, versión, módulo o proyecto. Si mañana el equipo necesita trazar versión (`<versión>`/`<versión>`) es una **decisión aparte a tomar explícitamente** (otro campo, no un segundo tag) — hasta entonces, un ticket con más de un tag es un error a corregir.
- **Formato: sin prefijo, kebab-case.** El tag es el **nombre del tema**: `reserva-salas`, `<etiqueta-tematica>`, `georreferenciacion`. **Nunca se arma con el nombre del slice** (`<slice-1>-…`, `<slice-2>-…`): el slice ya es la Épica.
- **Se deriva del módulo / documento fuente**: el mismo tema del que salió el ticket (ver §3).
- **NUNCA el nombre del producto, la organización o el repositorio como tag** (ej. `<producto>`, `<repositorio>`). En un proyecto de un solo producto/repo, ese "tag" lo comparte el 100% de los tickets del tablero — no filtra nada, es ruido, exactamente lo opuesto al propósito del tag temático.
- **Sin tag de vertical slice.** El slice/dominio (`<slice-1>` · `<slice-2>` · `<slice-n>`) **no lleva tag propio**: ya queda capturado por la **Épica** (Épica = slice; ver [[contexto-proyecto]] y §5). Filtrás el slice filtrando por su Épica, no por un tag repetido en cada hijo — y **nunca** un sub-flujo del slice (`<sub-flujo>`) como tag aparte de una Historia: sigue siendo el mismo tema, mismo tag único.
- **Obligatorio en TODA la descendencia, siempre el mismo.** Al bajar un árbol, el **mismo y único** tag temático va en la Épica y en cada Feature, Historia y Tarea — nunca uno distinto por nodo, nunca acumulando más de uno.

> **Regla de oro del tag sin prefijo — consistencia.** Como no hay prefijo que lo distinga, el tema **se escribe siempre igual**. `reserva-salas` y `reservas-salas` son dos tags distintos y rompen el filtro. Definí el tag de cada tema **una sola vez** y reusalo idéntico. Conviene mantener una lista corta de tags de tema por proyecto (en el glosario del dominio o en un `pendiente` a acordar con el equipo) para no duplicar.

> **Antipatrón (evitar) — sobre-etiquetado.** En una prueba del proyecto de origen, un árbol se cargó con: Épica `<etiqueta-tematica>; <producto>; <repositorio>` (3 tags) y una Historia `<etiqueta-tematica>; <slice-1>; <producto>; <repositorio>` (4 tags). Los 3 tags extra (`<producto>`, `<repositorio>`, `<slice-1>`) no aportan filtro — todo el tablero comparte los dos primeros, y el tercero es un tag de sub-flujo prohibido. **Correcto:** los dos work items llevan **solo** `<etiqueta-tematica>`.

---

## 2. Relaciones / enlaces entre tickets

Un ticket casi nunca vive solo. Se registran dos clases de vínculo:

- **Jerárquicos (Parent/Child):** la Feature/Épica/Historia madre y sus hijos. Una Tarea **cuelga** de una Historia/Feature; una Historia, de una Feature; una Feature, de una Épica.
- **No jerárquicos (Related / Predecesor-Sucesor):** tickets del mismo tema que se tocan, sin ser padre-hijo. **Related** = "tiene que ver con"; **Predecesor/Sucesor** = "esto va antes/después de aquello".

Cada ticket incluye un bloque **Relaciones / Enlaces** con lo que aplique:

```
Relaciones / Enlaces
- Primario/Parent: <#ID o título de la Feature/Épica/Historia madre>
- Relacionadas (Related): <#ID o título de otras UH/tickets del mismo tema>
- Predecesor/Sucesor: <#ID> (si hay un orden de trabajo)   ← opcional
- Documento fuente: <ruta/al/archivo.md> (link al repo)     ← ver §3
```

> **Los #ID son dato duro (no se inventan).** La IA **propone** las relaciones por **título/tema** (lo que sí puede inferir del contenido), pero el **número de work item** real se **confirma con el autor o se resuelve por MCP** (`list_work_items` / `search_work_items`). Hasta confirmarlo, va `⚠`. Al crear/actualizar por MCP, el vínculo se materializa con `manage_work_item_link` (Parent/Child/Related), siempre **con confirmación humana** (ver [[integracion-azure-mcp/00-index]]).

> **Ejemplo (genérico):** la UH "Solicitar la reserva de una sala" lleva `Primario/Parent: Feature "Reserva de salas de reunión"` y `Relacionadas: UH "Aprobar/rechazar la reserva"` — el proceso es bietápico (un paso solicita, otro aprueba), así que las dos UH van relacionadas.

---

## 3. Documento fuente (trazabilidad **por referencia**, no por copia)

Cuando el ticket sale de un documento funcional (una ficha del OKF, una spec), se deja **el link/ruta al documento**, para poder ir del backlog al origen y viceversa.

- **Se guarda una REFERENCIA, nunca el contenido.** Una línea con la ruta/URL del `.md` (más, si sirve, la sección/ancla). **No se pega el texto del documento** en el ticket ni en el historial.
- **Traza bidireccional barata:** el ticket apunta al doc (una línea); el `historial/` registra el **ID generado + la ruta del doc** (una fila). Ninguno copia el cuerpo del documento → el costo es constante por ticket y **no crece la memoria** con el tamaño del doc.
- Si el proyecto quiere el otro sentido explícito (el doc lista los IDs que generó), que sea también **solo la lista de IDs**, no contenido duplicado.

> Por qué así: duplicar el contenido del documento en cada ticket (y en cada registro del historial) infla todo y se desincroniza apenas el doc cambia. La referencia siempre apunta a la versión viva. Regla: **enlazar, no copiar.**

> **Ejemplo (genérico):** la UH de reserva de salas lleva `Documento fuente: cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md (link al repo)`. Si mañana cambia la regla, se edita el doc; el ticket sigue apuntando al mismo lugar, sin arrastrar una copia vieja.

---

## 4. Códigos de regla de negocio `[RN-…]`

Para que la tarjeta sea trazable **por dentro**, las reglas de negocio se **numeran** y se **referencian** en los criterios de aceptación.

- En **Descripción → Reglas de negocio**, numerá cada regla: `[RN-<TEMA>-01]`, `[RN-<TEMA>-02]`… (el `<TEMA>` es una sigla corta del tema, coherente con el tag de §1).
- En **Criterios de aceptación (Gherkin)**, referenciá la regla que cada escenario verifica (en el nombre del escenario o como comentario `# [RN-…]`).
- En un **Bug**, indicá **qué RN se rompe** (si el tema las tiene numeradas): conecta el defecto con la regla violada.

Así se puede rastrear: regla → escenario que la prueba → (si falla) bug que la rompe.

> **Ejemplo (genérico):**
> Regla `[RN-MOD-01] Solo el rol solicitante puede iniciar la solicitud de reserva.`
> Escenario: `Solicitar la reserva de una sala [RN-MOD-01]` — Dado soy asistente de recepción con rol solicitante, Cuando presiono "Reservar", Entonces se genera aviso al rol aprobador.

---

## 5. Mapeo OKF → Azure DevOps (descomposición y alta en lote)

Regla para bajar un **documento/módulo funcional** a la jerarquía del board sin improvisar:

| En el dominio / arquitectura | En Azure DevOps |
|---|---|
| **Vertical slice / dominio** (bounded context: los slices declarados en [[contexto-proyecto]]) | **Épica** |
| **Capacidad / caso de uso** dentro del slice | **Feature** |
| **Flujo / acción de negocio** | **Historia de usuario** |
| **Desglose técnico** dentro del slice (capas `api` / `application` / `domain` / `infra`) | **Tarea** (la crean los desarrolladores; con **contrato técnico** de entrada/salida si otro código la llama — ver [[plantillas/tarea]]) |

> **Por qué por vertical slice:** la arquitectura del módulo es un **monolito modular por vertical slices** — cada ticket vive en **un** slice, así el trabajo en paralelo no genera conflictos de fusión. Por eso la **Épica es el slice/dominio** y su tag baja a toda la descendencia. Fuente: doc de arquitectura del módulo (ver [[contexto-proyecto]]).
>
> **Nota de vocabulario:** en material viejo puede aparecer «Módulo→Épica · MVP→Feature». Vale el modelo de arriba: la **Épica es el vertical slice/dominio** y la **Feature es una capacidad/caso de uso** dentro del slice (un MVP/release atraviesa varias Features, no equivale a una); el «desglose técnico» son las capas del slice.

### Cardinalidad: el conteo lo fija la ficha (1:1)

El mapeo de arriba dice **qué tipo**, no **cuántos**. El **cuántos** sale **1:1** de un bloque **enumerado y cerrado** que la ficha declara — así **cualquier LLM produce el mismo árbol**, porque copia una lista en vez de segmentar prosa a ojo (esa era la causa del conteo variable entre Claude/opencode/Antigravity).

**La ficha derivable trae este bloque** (lo produce la **curación**, lo valida un humano; el funcional que sube el doc **no** lo escribe):

```markdown
## Derivación a backlog
### Slices [Épicas]
- [S-01] <slice/dominio>
### Capacidades [Features]
- [C-01] <capacidad/caso de uso>  · Slice: S-01
### Flujos [Historias]
- [F-01] <flujo/acción de negocio>  · Capacidad: C-01 · Reglas: [RN-…], [RN-…]
- [F-02] <flujo/acción de negocio>  · Capacidad: C-01
```

**Derivación 1:1:** **1 Épica por cada `[S-nn]`** (default 1; nunca inferir slices no listados) · **1 Feature por cada `[C-nn]`** (Parent = Épica de su slice) · **1 Historia por cada `[F-nn]`** (Parent = Feature de su capacidad) · **0 Tareas** por default. Ningún nodo **Épica/Feature/Historia** que no salga de un ítem enumerado; no se parte ni se fusiona un flujo por criterio propio. **Las Tareas son la excepción declarada**: la ficha nunca enumera `[T-nn]`, así que su conteo **no** sale 1:1 — sale del juicio técnico de la reunión de devs (por endpoint y capa, ver [[sincronizar-backlog]]), con GATE de NIVEL en su propio turno. Lo que reemplaza al conteo como control —opcional, a pedido— es [[analizar-tareas]]: que cada `[RN-]` y cada **Escenario** de la Historia quede cubierto entre todas las Tareas. **La unidad de Historia es el flujo listado, NO la pantalla** (decisión cerrada). **Si la ficha no trae el bloque (o tiene `⚠`), NO se deriva:** se frena y se pide cerrarlo en el Cerebro (extiende el gate del bloque enumerado de [[sincronizar-backlog]]).

- Todos los work items de ese slice comparten el **mismo tag temático** (§1) — el slice ya está dado por la Épica, no lleva tag — y quedan **enlazados** (§2: Épica→Features→UHs) con **Documento fuente** (§3).
- **Crear EXACTAMENTE lo pedido (no inflar el árbol).** El alta en lote (Épica + Features + UHs) es **solo** cuando se pide explícitamente *bajar una ficha/módulo entero*. Si se pide **una** tarea, historia o bug, se crea **ese único ítem** — nunca se genera el árbol entero "por las dudas".
- **Alta en lote con confirmación:** por MCP se puede crear la jerarquía en una operación, pero **siempre con confirmación humana previa** del árbol propuesto (nada se escribe sin "dale"; ver [[integracion-azure-mcp/00-index]]). Para varias Historias con sus Tareas, el lote corre con [[planificar-lote]]: dos turnos humanos (arranque y cierre) y agentes en paralelo.
- **Description en HTML.** El campo Descripción (y Pasos para reproducir, en Bug) es HTML: **armá el HTML** (`<h3>`, `<ul>/<li>`, `<b>`, `<br>`) antes de escribir; no pegues markdown crudo (`**`, `-`, `#`). Esqueleto por tipo listo para copiar en [[mapa-campos-azure]] («Esqueleto HTML de la Descripción por tipo»), para que Épicas, Features e Historias **queden bien formateadas**.
- **No inventar la estructura como si fuera dato**: la descomposición sale **1:1 del bloque `## Derivación a backlog`** de la ficha (ver arriba). El humano confirma el árbol propuesto; **no** re-decide la granularidad en la derivación — esa decisión ya la cerró la **curación** al enumerar la ficha.
- **Dos momentos (funcional vs dev/planning).** El flujo **funcional** baja hasta **Historia** (Épica/Feature/Historia): valida la necesidad de negocio. Las **Tareas** (desglose técnico por capas `api`/`application`/`domain`/`infra`) son un **segundo momento de Desarrollo/planning** y **no** se crean en el flujo funcional; se generan solo cuando el humano declara ese contexto dev/planning explícitamente, en la conversación y en respuesta a la pregunta del nivel (el pedido «creá las tareas» no alcanza; GATE de NIVEL de [[AGENTS]]).

> **Ejemplo (genérico):** una ficha que declara `[S-01]` un vertical slice/dominio, `[C-01]` una capacidad/caso de uso y `[F-01]`/`[F-02]` dos flujos → **exactamente 4 work items**: 1 Épica (=S-01) + 1 Feature "`<capacidad>`" (=C-01) + 2 Historias (=F-01, F-02). El desglose técnico (endpoint, validación, pantalla) → Tareas, solo en el segundo momento dev/planning. Todo con el tag temático y `Documento fuente` a la ficha.

---

## Resumen operativo (qué agrega cada ticket)

Todo ticket que produce el toolkit incluye, además de sus campos propios:

- **Etiqueta temática** sin prefijo (§1), escrita siempre igual.
- Bloque **Relaciones / Enlaces** (§2): Parent + Related (+ Predecesor/Sucesor si aplica), con `#ID` a confirmar (`⚠`).
- **Documento fuente** como **link/ruta** (§3), nunca contenido copiado.
- **Reglas de negocio numeradas** `[RN-…]` referenciadas en Gherkin (§4).
