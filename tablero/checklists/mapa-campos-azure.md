---
id: mapa-campos-azure
tipo: referencia
estado: F-Draft
modulo: integracion-azure-devops
title: "Mapa de campos de Azure DevOps"
author: equipo
tags: [azure-devops, campos, mapeo, referencia, work-items]
last_updated: 2026-10-01
---

# Mapa de campos de Azure DevOps

Referencia de dónde va cada bloque de contenido en Azure DevOps por tipo de work item, para que la salida del toolkit sea pegable directo, en el campo correcto y con los valores válidos. Es agnóstica de dominio; los recuadros "Ejemplo (genérico)" son solo ilustrativos.

Relacionados: [[checklist-historia]] · [[checklist-bug]]

---

## Cómo leer este mapa

- Cada tabla es **por tipo de work item**: **Campo visible (español)** → **Referencia interna** → **Qué contenido poner**.
- Proceso: Microsoft **Agile** (customizado en el proyecto de Azure DevOps del equipo).
- El toolkit produce el contenido en español; este mapa dice **en qué caja** de Azure pegar cada parte.
- Los campos HTML enriquecido (Descripción, Criterios de aceptación, Pasos para reproducir) admiten listas, tablas y formato: usalo, pero mantené el texto en español y sin PHI.

---

## Tipos de work item

**Historia de usuario (User Story)** · **Tarea (Task)** · **Bug** · **Característica (Feature)** · **Épica (Epic)** · **Test Suite**.

---

## Historia de usuario

| Campo visible (español) | Referencia interna | Qué contenido poner |
|---|---|---|
| Título | `System.Title` | `Modulo - Capacidad concreta`. Sin typos, prefijo de módulo consistente. |
| Descripción | `System.Description` (HTML) | Rol/necesidad/beneficio ("Como `<rol>`, quiero..., para..."), contexto y problema, alcance y **fuera de alcance**, reglas de negocio (con referencia al OKF), **casos de uso (alcance de pruebas)**, dependencias. Enlaces (Figma/GitLab) como **apoyo**, nunca como único contenido. |
| Criterios de aceptación | `Microsoft.VSTS.Common.AcceptanceCriteria` (HTML) | **Gherkin en español** (`Característica`/`Escenario`/`Dado`/`Cuando`/`Entonces`), **en HTML con TODAS las keywords en negrita y los pasos sangrados** (esqueleto abajo — sin markdown ni fences). Verificables. **Nunca vacío.** |
| Puntos de historia (Story Points) | `Microsoft.VSTS.Scheduling.StoryPoints` | Número de la estimación relativa. No dejar vacío. |
| Prioridad | `Microsoft.VSTS.Common.Priority` | 1–4 (ver valores abajo). |
| Riesgo | `Microsoft.VSTS.Common.Risk` | Nivel de riesgo si aplica. |
| Área de valor | `Microsoft.VSTS.Common.ValueArea` | `Business` (features de negocio) o `Architectural` (reestructuración/migración). |
| Etiquetas | `System.Tags` | Ver convención abajo. |
| Ruta de iteración | `System.IterationPath` | Ver convención abajo. |
| Área | `System.AreaPath` | Área/nodo del equipo dentro del proyecto. |
| Estado | `System.State` | Ver flujo de estados abajo. |
| (Enlace) Primario/Parent + Related | links `Parent` / `Related` | Feature/Épica madre (Parent) y otras UH del mismo tema (Related). Los `#ID` se confirman o se resuelven por MCP. |

## Tarea

| Campo visible (español) | Referencia interna | Qué contenido poner |
|---|---|---|
| Título | `System.Title` | Acción técnica concreta (`ms-reservas - Reestructurar a api+impl`). |
| Descripción | `System.Description` (HTML) | Objetivo + alcance técnico + subtareas + **Material de apoyo** (con el Documento fuente adentro) + **Resultado entregable** + Definición de terminado. **Si la capa es `api`/`application`/`domain`, además el bloque obligatorio**: Contrato técnico (fragmento OpenAPI en `<pre>` si es `api`), Validaciones, Casos de error (en `<table>`), Dependencias, **Especificación cerrada (SDD)** con la tabla de Escenarios de la Historia, **Tests a escribir PRIMERO** (numerados) y **Modos de falla evaluados**. Ver el esqueleto completo abajo. Links de GitLab/Figma como apoyo, no como único contenido. |
| Esfuerzo original | `Microsoft.VSTS.Scheduling.OriginalEstimate` | Horas estimadas. |
| Trabajo restante | `Microsoft.VSTS.Scheduling.RemainingWork` | Horas restantes. |
| Trabajo completado | `Microsoft.VSTS.Scheduling.CompletedWork` | Horas hechas. |
| Actividad | `Microsoft.VSTS.Common.Activity` | Ver valores abajo. |
| Prioridad | `Microsoft.VSTS.Common.Priority` | 1–4. |
| (Enlace) Primario / Parent | link `Parent` | Historia o Feature madre. Una Tarea técnica **cuelga** de una Historia/Feature, no va suelta. |
| Etiquetas | `System.Tags` | Ver convención abajo. |
| Ruta de iteración | `System.IterationPath` | Ver convención abajo. |
| Estado | `System.State` | Ver flujo abajo. |

## Bug

| Campo visible (español) | Referencia interna | Qué contenido poner |
|---|---|---|
| Título | `System.Title` | `Modulo - Contexto: sintoma`. Sin typos. |
| Pasos para reproducir | `Microsoft.VSTS.TCM.ReproSteps` (HTML) | **Acá va TODO el cuerpo del bug**: Ambiente · Versión (Frontend `<versión>` / Backend `<versión>`) · Fecha · Precondiciones · Pasos numerados · **Resultado esperado** · **Resultado obtenido** (separados) · Por qué es un error · Observaciones · Evidencia. Todo en español, PHI enmascarada. |
| Información del sistema | `Microsoft.VSTS.TCM.SystemInfo` | La completa la **extensión del navegador** de Azure. No inventar. |
| Descripción | `System.Description` (HTML) | En bugs **casi no se usa**. Dejar vacía o una línea de contexto. |
| Gravedad | `Microsoft.VSTS.Common.Severity` | `1 - Critical` / `2 - High` / `3 - Medium` / `4 - Low`. |
| Prioridad | `Microsoft.VSTS.Common.Priority` | 1–4, coherente con la gravedad. |
| Puntos de historia (Story Points) | `Microsoft.VSTS.Scheduling.StoryPoints` | Opcional: solo si se decide dar puntos a los bugs (los calcula la IA por complejidad + tokens). |
| Etiquetas | `System.Tags` | Ver convención abajo. |
| Historial | `System.History` | Notas de validación de QA (registro del ida y vuelta). |
| Ruta de iteración | `System.IterationPath` | Ver convención abajo. |
| Estado | `System.State` | Ver flujo abajo. |

## Feature

| Campo visible (español) | Referencia interna | Qué contenido poner |
|---|---|---|
| Título | `System.Title` | Capacidad mayor que agrupa varias historias. |
| Descripción | `System.Description` (HTML) | Objetivo de negocio, alcance general, criterios de éxito de alto nivel. |
| Área de valor | `Microsoft.VSTS.Common.ValueArea` | `Business` / `Architectural`. |
| Prioridad | `Microsoft.VSTS.Common.Priority` | 1–4. |
| Etiquetas / Ruta de iteración / Estado | `System.Tags` / `System.IterationPath` / `System.State` | Según convenciones y flujo. |
| (Enlace) hijos | links `Child` | Historias de usuario que la componen. |

## Épica (Epic)

| Campo visible (español) | Referencia interna | Qué contenido poner |
|---|---|---|
| Título | `System.Title` | Iniciativa grande que agrupa Features. |
| Descripción | `System.Description` (HTML) | Visión, objetivo estratégico, alcance macro. |
| Área de valor | `Microsoft.VSTS.Common.ValueArea` | `Business` / `Architectural`. |
| Etiquetas / Ruta de iteración / Estado | `System.Tags` / `System.IterationPath` / `System.State` | Según convenciones y flujo. |
| (Enlace) hijos | links `Child` | Features que la componen. |

---

## Valores válidos

### Gravedad (Bug) — `Microsoft.VSTS.Common.Severity`
| Valor | Cuándo |
|---|---|
| `1 - Critical` | Impide operar / caída / pérdida de datos / bloqueo total de un flujo troncal. |
| `2 - High` | Funcionalidad importante rota sin solución alternativa razonable. |
| `3 - Medium` | Falla con solución alternativa, o afecta a pocos casos. |
| `4 - Low` | Cosmético, textual, menor. |

> **Ejemplo (genérico):** `1 - Critical` = impide operar el flujo troncal del negocio (el proceso principal). El impacto se lee en clave del dominio, el valor del desplegable no cambia.

### Prioridad — `Microsoft.VSTS.Common.Priority`
`1` (máxima) · `2` · `3` · `4` (mínima). Debe ser coherente con la gravedad y la urgencia operativa.

### Riesgo — `Microsoft.VSTS.Common.Risk`
`1 - High (alto)` · `2 - Medium (medio)` · `3 - Low (bajo)`. Se selecciona el valor tal cual aparece en Azure (en inglés); el texto entre paréntesis es solo ayuda en español.

### Área de valor — `Microsoft.VSTS.Common.ValueArea`
`Business` (valor de negocio / features) · `Architectural` (reestructuración/migración, deuda técnica).

### Actividad (Tarea) — `Microsoft.VSTS.Common.Activity`
`Requirements` · `Design` · `Development` · `Testing` · `Documentation` · `Deployment`.
(Al referirse a ellas describir en español, p.ej. "Actividad: Development (Desarrollo)".)

### Flujo de estados — `System.State`
**Work items de desarrollo (Historia/Tarea/Bug/Feature/Épica):**
`New` (Nuevo) → `Active` (Activo) → `Design` (Diseño) → `Review` (Revisión) → `QA` → `Closed` (Cerrado).

**Work items de test (Test Suite / casos):** usan `In Progress` (En progreso) en lugar de `Active`.

> El flujo exacto depende de cómo esté customizado el proceso en cada proyecto: si difiere, marcá **(pendiente)** y confirmá contra el tablero real antes de dar por buenos los estados.

---

## Convenciones

### Etiquetas (`System.Tags`)
- **Etiqueta temática — UNA sola, techo duro**: una etiqueta **sin prefijo** que engloba el **tema/asunto** del ticket (`reservas`, `pagos`, `notificaciones`). Va en **todos** los tickets del tema para poder filtrarlos juntos. Se deriva del módulo/documento fuente. **Consistencia crítica**: al no haber prefijo, el tema se escribe **siempre igual** (`reserva` ≠ `reservas`). Detalle: [[organizacion-y-trazabilidad]] §1.
- **Sin tag de slice**: el vertical slice (`<slice-1>` · `<slice-2>` · `<slice-n>`) queda dado por la **Épica** (Épica = slice), no por un tag repetido en cada hijo.
- **Nunca el nombre del producto/repo** (`<producto>`, `<repositorio>`) como tag: lo comparte el 100% del tablero, no filtra nada.

> **Ejemplo (genérico):** etiqueta temática `reservas`, sola. Filtrando por `reservas` cae todo el tema (Historias, Bugs, Tareas).

### Ruta de iteración (`System.IterationPath`)
Formato: `<Proyecto>\<Equipo> - Sprint NN` (donde `NN` es el número de sprint).

### Área (`System.AreaPath`)
Nodo del equipo dentro del proyecto. Elegir el área que corresponda según cómo esté configurado el tablero.

### Relaciones entre work items (enlaces)
Dos clases de vínculo, además de los campos:
- **Jerárquicos** — `System.LinkTypes.Hierarchy` (**Parent/Child**): Tarea→Historia, Historia→Feature, Feature→Épica.
- **No jerárquicos** — `System.LinkTypes.Related` (**Related**, mismo tema que se toca) y `System.LinkTypes.Dependency` (**Predecesor/Sucesor**, orden de trabajo).

La IA **propone** las relaciones por título/tema; el **`#ID` es dato duro** (se confirma con el autor o se resuelve por MCP con `list_work_items`/`search_work_items`). Al crear por MCP, el vínculo se materializa con `manage_work_item_link`, **con confirmación humana**. Detalle: [[organizacion-y-trazabilidad]] §2.

### Documento fuente y códigos de regla `[RN-…]`
- **Documento fuente**: dentro de la Descripción (o Pasos para reproducir, en Bug), una **línea con el link/ruta** al `.md` de origen — **referencia, nunca el contenido copiado**. El `historial/` registra ID + ruta, no el cuerpo del doc (no crece la memoria). Ver [[organizacion-y-trazabilidad]] §3.
- **Códigos `[RN-<TEMA>-NN]`**: numerar las reglas de negocio en la Descripción y **referenciarlas** en los escenarios Gherkin; en un Bug, indicar qué `[RN-…]` se rompe. Ver [[organizacion-y-trazabilidad]] §4.

### Mapeo → jerarquía de Azure (por vertical slices)
Para bajar un documento/módulo entero al board (este proyecto): **Vertical slice/dominio → Épica · Capacidad → Feature · Flujo → Historia · Desglose técnico (capas `api`/`application`/`domain`/`infra`) → Tarea.** Todos con la **misma etiqueta temática** y enlazados. Alta en lote por MCP **solo con confirmación** del plan propuesto. Detalle y equivalencia con el mapeo genérico: [[organizacion-y-trazabilidad]] §5.

---

## Esqueleto HTML de la Descripción por tipo

El campo **Descripción** de Azure (`System.Description`) y **Pasos para reproducir** de un Bug (`Microsoft.VSTS.TCM.ReproSteps`) son **HTML**, no markdown. **Armá el cuerpo en HTML antes de escribir**: el markdown de las plantillas/ejemplos es solo para leer; convertilo. **Nunca** pegues `**`, `-`, `#` (Azure los muestra literales). Reglas del esqueleto: solo `<h3>` para secciones, `<ul>/<li>` (o `<ol>/<li>` para pasos), `<b>` inline, `<p>` prosa, `<br>` saltos, **`<pre>` para bloques de código** y **`<table>` para tablas**; nada de `<h1>/<h2>` (Azure ya pone el título) ni estilos inline; escapá `<` `>` como `&lt;` `&gt;` en los marcadores.

> **Separadores entre secciones — `<hr>` antes de cada `<h3>` (menos el primero).** Azure renderiza los `<h3>` muy pegados entre sí y una Tarea completa queda como un muro: el ojo no encuentra dónde termina una sección y empieza la otra. Un `<hr>` por sección lo resuelve sin estilos inline. **Verificado en el board:** Azure conserva el `<hr>`, no lo filtra. En los tipos cortos (Épica, Feature) es opcional; en la **Tarea es obligatorio**, que es la que tiene 14 secciones.
> **Bloques de código (contrato OpenAPI, JSON) — `<pre>`, nunca fences.** La plantilla de Tarea escribe el contrato de capa `api` como fragmento **OpenAPI (YAML)**. En Azure eso va dentro de `<pre>…</pre>`, que conserva saltos y sangría y lo muestra monoespaciado. **Nunca** pegues los fences de markdown (` ``` `): Azure los muestra literales y el contrato queda ilegible.
> **Cuidado crítico con el escape:** adentro del `<pre>` hay que escapar `<` y `>` como `&lt;` y `&gt;`, porque el contrato está lleno de marcadores tipo `<ruta>`, `<método>`, `<campo>`. Si no se escapan, **el navegador se los come como si fueran etiquetas HTML** y desaparecen de la tarjeta sin aviso — el error más silencioso de todos. Copiá el esqueleto del tipo y reemplazá los `...`:

**Épica** (`System.Description`):
```html
<h3>Objetivo de negocio</h3><p>...</p>
<h3>Problema / oportunidad</h3><p>...</p>
<h3>Alcance macro</h3><ul><li>...</li></ul>
<h3>Fuera de alcance</h3><ul><li>...</li></ul>
<h3>Criterios de éxito</h3><ul><li>...</li></ul>
```

**Feature** (`System.Description`):
```html
<h3>Qué es</h3><p>...</p>
<h3>Valor para el negocio</h3><p>...</p>
<h3>Alcance</h3><ul><li>...</li></ul>
<h3>Fuera de alcance</h3><ul><li>...</li></ul>
<h3>Dependencias</h3><ul><li>...</li></ul>
```

**Historia** — 4 bloques (`System.Description`; el Bloque 2, Criterios de aceptación, va al campo aparte `AcceptanceCriteria`):
```html
<h3>Funcionalidad / Historia de usuario</h3>
<p><b>Contexto:</b> ...</p>
<p><b>Como</b> &lt;rol&gt;<br><b>quiero</b> &lt;necesidad&gt;<br><b>para</b> &lt;beneficio&gt;.</p>
<h3>Alcance</h3><ul><li>...</li></ul>
<h3>Fuera de alcance</h3><ul><li>...</li></ul>
<h3>Datos y estados</h3><ul><li><b>Campo:</b> &lt;campo&gt; (obligatorio, del catálogo X; default ...) <i>[RN-TEMA-01]</i></li><li><b>Estado:</b> &lt;Estado A&gt; → &lt;Estado B&gt; (permitida / bloqueada) <i>[RN-TEMA-02]</i></li></ul>
<h3>Reglas de negocio</h3><ul><li><b>[RN-TEMA-01]</b> ... <i>(OKF: ruta/al/doc.md#ancla)</i></li></ul>
<h3>Casos de uso (alcance de pruebas)</h3><ul><li><b>CU-01</b> ... <i>[RN-TEMA-01]</i></li></ul>
<h3>Documento fuente</h3><p><a href="ruta/al/doc.md">ruta/al/doc.md</a> — referencia, no contenido</p>
```
> Los **Criterios de aceptación** (Bloque 2) van en Gherkin al campo `AcceptanceCriteria` (esqueleto propio abajo); cada **Caso de uso** de arriba se cubre con ≥1 escenario.

**Criterios de aceptación** (`Microsoft.VSTS.Common.AcceptanceCriteria`) — el **Gherkin en español va en HTML**, no en markdown ni en fence ```` ``` ````. Regla de oro para que rinda limpio: **negrita en TODAS las keywords** (`Característica`, `Antecedentes`, `Escenario`, `Esquema del escenario`, `Ejemplos`, `Dado`, `Cuando`, `Entonces`, `Y`, `Pero`) — no solo en `Escenario:`; **un `<p>` por escenario** (los separa visualmente); **pasos sangrados** con `&nbsp;&nbsp;`; los `[RN-…]` en `<i>` al final del renglón del `Escenario`:
```html
<p><b>Característica:</b> ...</p>
<p><b>Antecedentes:</b><br>
&nbsp;&nbsp;<b>Dado</b> que ...<br>
&nbsp;&nbsp;<b>Y</b> ...</p>
<p><b>Escenario:</b> ... <i>[RN-TEMA-01]</i><br>
&nbsp;&nbsp;<b>Dado</b> que ...<br>
&nbsp;&nbsp;<b>Cuando</b> ...<br>
&nbsp;&nbsp;<b>Entonces</b> ...<br>
&nbsp;&nbsp;<b>Y</b> ...</p>
<p><b>Escenario:</b> ... <i>[RN-TEMA-02]</i><br>
&nbsp;&nbsp;<b>Dado</b> ...<br>
&nbsp;&nbsp;<b>Cuando</b> ...<br>
&nbsp;&nbsp;<b>Entonces</b> ...</p>
```
> Anti-patrón (lo que se ve feo): pegar el Gherkin crudo o con `<br>` pero **sin** negrita en `Dado/Cuando/Entonces` ni sangría → queda un muro de renglones iguales. Bold en cada keyword + sangría es lo que lo hace legible.

**Tarea** (`System.Description`) — el esqueleto **completo**. Los bloques del medio (desde *Contrato técnico* hasta *Tests a escribir PRIMERO*) son **obligatorios si la capa es `api`/`application`/`domain`** y se **borran enteros** si es una tarea chica de solo UI/config (ver [[plantillas/tarea]]). No infles una tarea chica con secciones que no aplican:
```html
<h3>Objetivo</h3><p>...</p>
<hr>
<h3>Alcance técnico</h3><ul><li><b>Vertical slice:</b> ...</li><li><b>Capa:</b> ...</li><li><b>Requiere test de integración:</b> sí / no</li><li><b>Fuera de alcance:</b> ...</li></ul>
<hr>
<h3>Contrato técnico (entrada/salida)</h3>
<pre>paths:
  /api/&lt;recurso&gt;/&lt;accion&gt;:
    post:
      summary: ...
      responses:
        '200': { description: ... }
        '409': { description: CODIGO_ERROR }</pre>
<hr>
<h3>Validaciones</h3><ul><li><b>&lt;campo&gt;:</b> regla exacta <i>[RN-TEMA-01]</i></li></ul>
<hr>
<h3>Casos de error</h3>
<table>
<tr><th>Condición</th><th>Código</th><th>Payload</th><th>Regla</th></tr>
<tr><td>&lt;condición&gt;</td><td>404</td><td>{ "error": "CODIGO" }</td><td><i>[RN-TEMA-01]</i></td></tr>
</table>
<hr>
<h3>Dependencias</h3><ul><li><b>Depende de:</b> ...</li><li><b>De esto depende:</b> ...</li></ul>
<hr>
<h3>Especificación cerrada (SDD)</h3>
<p><b>Comportamiento exacto:</b> ... <i>[RN-TEMA-01]</i></p>
<p><b>Escenarios de la Historia que esta Tarea cubre</b> (mapeo al Gherkin del padre):</p>
<table>
<tr><th>Escenario de la Historia #NNNN</th><th>Qué parte cubre esta Tarea</th><th>Tests que lo verifican</th></tr>
<tr><td>&lt;título del Escenario, textual&gt;</td><td>&lt;la parte que le toca a esta Tarea&gt;</td><td>&lt;n.º de los tests de la lista de abajo&gt;</td></tr>
</table>
<p><b>No cubre:</b> &lt;título del Escenario, textual&gt; (#NNNN) · &lt;título&gt; (#NNNN)</p>
<hr>
<h3>Tests a escribir PRIMERO</h3><p><b>Datos base:</b> &lt;datos de prueba comunes; cada test dice sólo lo que cambia&gt;</p><ol><li>Caso feliz: ... → 200 + ...</li><li>&lt;validación&gt; → 400 + ... <i>[RN-TEMA-01]</i></li><li>Invariante de negocio protegida: ... <i>[RN-TEMA-02]</i></li><li>Esquema — &lt;condición común&gt;:<ul><li>&lt;entrada 1&gt; → &lt;resultado esperado 1&gt;</li><li>&lt;entrada 2&gt; → &lt;resultado esperado 2&gt;</li></ul></li><li><b>Guardarraíl (nace verde, EXENTO del rojo previo):</b> ... — <b>se pone en rojo si</b> &lt;el cambio concreto que lo haría fallar&gt; <i>[RN-TEMA-03]</i> (si no se puede escribir esa frase no es guardarraíl: borrá este renglón)</li><li>Integración: ... (obligatorio si arriba decís «Requiere test de integración: sí»)</li></ol>
<hr>
<h3>Modos de falla evaluados</h3><ul><li><b>Estado:</b> ... / no aplica porque ...</li><li><b>Concurrencia:</b> ... / no aplica porque ...</li><li><b>Autorización:</b> ... / no aplica porque ...</li><li><b>Dependencia caída:</b> ... / no aplica porque ...</li><li><b>Límites:</b> ... / no aplica porque ...</li><li><b>Idempotencia:</b> ... / no aplica porque ...</li></ul>
<hr>
<h3>Subtareas</h3><ol><li>...</li></ol>
<hr>
<h3>Material de apoyo</h3><ul><li><b>Diseño (Figma):</b> <a href="URL">URL</a> — apoyo, no reemplaza el alcance escrito</li><li><b>Repo / rama (GitLab):</b> <a href="URL">URL</a></li><li><b>Documento fuente:</b> <a href="ruta/al/doc.md">ruta/al/doc.md</a> — referencia, no contenido</li></ul>
<hr>
<h3>Resultado entregable</h3><p>...</p>
<hr>
<h3>Definición de terminado</h3><ul><li>...</li></ul>
<hr>
<h3>⚠ Datos a confirmar</h3><ul><li>&lt;pregunta que tiene que responder un humano, y qué test queda bloqueado&gt;</li></ul><i>(obligatoria: si no hay pendientes va &laquo;Ninguno.&raquo;; la sección no se borra)</i>
```
> **«Material de apoyo» lleva el Documento fuente adentro, no como sección aparte** — así queda igual que [[plantillas/tarea]]. Los links de Figma y de GitLab van **acá y no se borran**: son los que la Regla anti-patrón exige como apoyo. Lo que está prohibido es que el link sea *lo único* que hay; el alcance se escribe igual en texto.
> **La sección «Especificación cerrada (SDD)» es la bisagra entre BDD y TDD — no la borres en una tarea de capa `api`/`application`/`domain`.** Arriba, la Historia trae el Gherkin (loop externo, BDD); abajo, la Tarea trae la lista de tests (loop interno, TDD). Sin esa tabla de mapeo, los dos loops existen por separado y **nadie puede responder si escribir los tests de la Tarea alcanza para cerrar un Escenario de la Historia**. La tabla se llena con el **título textual** del Escenario tal como está en el campo Criterios de aceptación del padre: si no coincide palabra por palabra, no sirve para rastrear.
> **Numerá los tests (`<ol>`, no `<ul>`)** — la columna «Tests que lo verifican» los referencia por número; con viñetas no hay a qué apuntar.
> **Coherencia obligatoria del test de integración:** si en *Alcance técnico* pusiste «Requiere test de integración: **sí**», entonces tienen que estar las **tres** cosas: **(a) al menos un test de integración en la lista, (b) una subtarea que lo escriba y (c) un ítem propio en la Definición de terminado**. Declararlo arriba y no pedirlo abajo es el defecto silencioso más común: el dev cierra la tarea con puros dobles y nadie lo nota. Son las mismas tres que exigen [[plantillas/tarea]] y [[redactar-tarea]], y las que chequea [[analizar-tareas]]: si acá pedís menos, la Tarea sale incompleta y después el análisis la marca.
> **Por qué la Tarea quedó más larga que los otros tipos:** es deliberado. Es el único work item que un dev (o una IA) usa para **codear sin ida y vuelta**, así que lleva el contrato y las pruebas adentro. El largo se controla **borrando el bloque del medio** en las tareas chicas, no recortando el contrato de las grandes, y **partiendo la Tarea** cuando la lista de tests pasa de 30. La línea «No cubre» y el párrafo «Datos base» se borran si no hay nada que poner. Detalle: [[plantillas/tarea]] §«Tamaño y forma».

**Bug** (va a **Pasos para reproducir** `Microsoft.VSTS.TCM.ReproSteps`, **no** a Descripción):
```html
<h3>Ambiente</h3><p>TEST</p>
<h3>Pasos</h3><ol><li>...</li><li>...</li></ol>
<h3>Resultado esperado</h3><p>...</p>
<h3>Resultado obtenido</h3><p>...</p>
<h3>Por qué es un error</h3><p>... <b>Regla violada:</b> [RN-TEMA-NN]</p>
```

---

## Reglas transversales al pegar en Azure

- **Todo en español**, incluidos los Criterios de aceptación en Gherkin (`Característica`/`Escenario`/`Dado`/`Cuando`/`Entonces`).
- **HTML consistente**: en Descripción usá `<h3>` **sin** prefijos tipo `BLOQUE 1:/2:/3:` (el `<h3>` ya nombra la sección); usá `<b>` (no `<strong>`) e `<i>` (no `<em>`). En Criterios, seguí el esqueleto de arriba (keywords en negrita + sangría). Coherencia = tickets que se leen igual y prolijos.
- **Sin PHI** en ningún campo ni adjunto: solo marcadores `<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`, `<telefono>`.
- **Nada de campos "estrella" vacíos**: Historia sin Criterios de aceptación, Bug con pasos "Ver adjunto", tarjetas sin Puntos de historia/Gravedad = rechazar y completar antes de crear.
- Los **enlaces** (Figma, GitLab, wiki) van como apoyo dentro del campo que corresponda, **nunca** como único contenido.
- Verificá el tipo antes de crear: si es trabajo técnico sin cara de usuario, es **Tarea** (hija de Historia/Feature), no **Historia**.
- **No inventar**: lo no confirmado se marca **(pendiente)** y se pregunta; respetá la jerarquía/provenance de las fuentes.
