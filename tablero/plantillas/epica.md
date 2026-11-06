---
id: plantilla-epica
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Épica (Azure DevOps)"
author: equipo
tags: [azure-devops, epica, epic, plantilla, redaccion]
last_updated: 2026-08-26
---

# Plantilla — Épica

Plantilla rellenable para escribir una Épica: el gran objetivo de negocio que agrupa Características e Historias. Copiá el bloque, reemplazá los `<marcadores>` y borrá las líneas de ayuda (`>`) antes de pegar en Azure. Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[caracteristica]] · [[historia-de-usuario]] · [[mapa-campos-azure]]

> **Cómo usar esta plantilla**
> - Reemplazá cada `<...>` por texto real y **borrá** las líneas de ayuda que empiezan con `>`.
> - Una Épica es grande y dura varios sprints; no se estima en Puntos de historia ni se "hace" de una: se **cierra** cuando sus Características/Historias hijas están hechas.
> - **PHI PROHIBIDO:** usá marcadores como `<persona>`, `<documento>`, `<dato-sensible>`.
> - Lo que no sepas con certeza, marcalo como **(pendiente)**. No inventes.
> - Jerarquía en Azure: **Épica → Característica (Feature) → Historia de usuario → Tarea**.
> - **Esta Épica = un vertical slice / dominio** (los slices declarados en [[contexto-proyecto]]). La arquitectura es un monolito modular por vertical slices; la Épica agrupa todo lo de su slice y su **tag baja a toda la descendencia** (Feature, Historia, Tarea).
> - Al crear por MCP, la **Descripción va en HTML** (`<h3>`, `<ul>/<li>`, `<b>`), no markdown crudo, para que quede bien formateada.

---

## Título sugerido

> **El título tiene que abarcar exactamente lo que abarca el `[S-nn]`, ni un poco más.** Si la
> ficha declara `[S-01] Reserva de salas de reunión` y deja otro escenario explícitamente fuera, la
> Épica **no** se llama «Gestión de salas» a secas. Un título más amplio que su slice es una
> bomba de retardo con el GATE de deduplicación: cuando llegue el documento del alcance que
> quedó afuera, la dedup va a encontrar esta Épica y va a **bloquear el alta** de un slice que
> esta misma Épica declaró fuera de su alcance — el gate va a funcionar perfecto y va a dar
> el resultado equivocado. Detalle: [[checklists/checklist-epica]].

`<Objetivo de negocio en una frase, orientado a resultado>`

> Que exprese el "para qué" grande, no una funcionalidad puntual.
> Correcto: `Asignacion de recursos por cercania geografica`
> Correcto: `Migracion del backend a logica propia en microservicios`
> Incorrecto: `Tocar el mapa` / `Micros`

---

## Descripción
> Va al campo **Descripción** (HTML enriquecido).

### Objetivo de negocio
`<Que resultado de negocio busca la organizacion con esta epica y por que ahora. 3-5 frases. El "porque" estrategico.>`

### Problema / oportunidad
`<Situacion actual y su costo (tiempo del usuario, errores, demoras, riesgo, deuda tecnica que frena una migracion).>`

### Alcance macro
- `<gran bloque 1 que entra: modulos, flujos, canales afectados>`
- `<gran bloque 2>`
- `<gran bloque 3>`

### Fuera de alcance
- `<que NO entra en esta epica, aunque sea tentador incluirlo>`
- `<...>`

---

## Historias / Características hijas candidatas
> Listado inicial de lo que colgará de esta Épica (típicamente Características, y bajo ellas Historias). Es una hipótesis de descomposición, se refina después.

| # | Título candidato | Tipo (Característica/Historia) | Notas |
|---|---|---|---|
| 1 | `<...>` | `<Caracteristica>` | `<...>` |
| 2 | `<...>` | `<Historia>` | `<...>` |
| 3 | `<...>` | `<...>` | `(pendiente) <sin confirmar>` |

---

### Vocabulario que heredan las hijas

<!-- Lo que NO se fija acá, lo elige cada hija por su cuenta: después los "Como <rol>" y los
     "Entonces <estado>" no coinciden entre hermanas, y nada lo detecta porque cada una es
     internamente coherente. Los nombres se copian del Cerebro, no se inventan. -->

| Roles que intervienen | De dónde sale el nombre |
|---|---|
| `<rol tal como se llama en el Cerebro>` | `<ruta de la ficha>` |

| Estados del dominio | De dónde sale el nombre |
|---|---|
| `<estado exacto>` | `<ruta de la ficha>` |

> Si un rol o un estado **no existe todavía en el Cerebro**, va `⚠` y se pregunta. **No se
> inventa un nombre para poder seguir**: acá se propaga a todas las hijas y a sus tests.

## Criterios de éxito medibles
> Cómo sabremos que la Épica cumplió su objetivo. **Medibles**, no aspiracionales. Definí métrica + valor objetivo + cómo se mide.

- `<metrica 1: p.ej. "el usuario ve el resultado en < 2 s en el 95% de los casos">`
- `<metrica 2: p.ej. "0 registros asignados incorrectamente tras el cambio">`
- `<metrica 3: p.ej. "N servicios con logica propia y sistema legacy apagado para el dominio X">`
- `(pendiente) <metrica que falta acordar con el negocio>`

---

## Riesgos y supuestos
- **Riesgo:** `<que puede salir mal>` — **Mitigación:** `<como lo reducimos>`
- **Supuesto:** `<que damos por cierto y de que depende (integracion externa, dato de otro sistema)>`
- **Dependencia:** `<con otra migracion / feature en curso / otra epica / integracion externa>`

---

## Etiquetas
`<tema>`  *(único tag — techo duro, ninguno más)*
> El **tag temático** se pone en la Épica y se hereda idéntico a toda su descendencia. **No hay tag de slice**, ni de producto/repo: solo el tema.

## Ruta de iteración (Sprint)
`<Proyecto>\<Equipo> - Sprint <NN>`
> Una Épica normalmente cruza varios sprints; poné el de arranque o dejala a nivel de área.

---

## A qué campo de Azure va cada bloque

| Bloque de esta plantilla | Campo visible en Azure | Referencia interna |
|---|---|---|
| Título sugerido | Título | `System.Title` |
| Descripción (objetivo, problema, alcance macro, fuera de alcance) | Descripción | `System.Description` |
| Historias / Características hijas | (se crean como work items y se enlazan) | relación Primario/Parent |
| Criterios de éxito medibles | Descripción (o Criterios de aceptación de alto nivel) | `System.Description` / `Microsoft.VSTS.Common.AcceptanceCriteria` |
| Riesgos y supuestos | Riesgo + Descripción | `Microsoft.VSTS.Common.Risk` |
| Área de valor | Área de valor | `Microsoft.VSTS.Common.ValueArea` |
| Etiquetas | Etiquetas | `System.Tags` |
| Ruta de iteración | Ruta de iteración | `System.IterationPath` |

> Tipo de work item: **Épica (Epic)**. Detalle de campos y valores: [[mapa-campos-azure]].

---

## Ejemplo (genérico)

> Recuadro ilustrativo con un dominio neutro. Es solo un ejemplo; la plantilla de arriba es la que se usa.
>
> **Título:** `Migracion del backend de passthrough a logica propia en microservicios`
> **Objetivo de negocio:** mover la lógica del monolito legacy a los micros por etapas hasta apagarlo.
> **Criterio de éxito:** N micros con lógica propia y monolito legacy apagado para el dominio X.
> **Área de valor:** Architectural.
