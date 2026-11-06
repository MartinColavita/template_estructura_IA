---
id: plantilla-caracteristica
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Característica / Feature (Azure DevOps)"
author: equipo
tags: [azure-devops, caracteristica, feature, plantilla, redaccion]
last_updated: 2026-08-26
---

# Plantilla — Característica / Feature

Plantilla rellenable para escribir una Característica (Feature): el bloque de valor entregable que agrupa Historias dentro de una Épica. Copiá el bloque, reemplazá los `<marcadores>` y borrá las líneas de ayuda (`>`) antes de pegar en Azure. Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[epica]] · [[historia-de-usuario]] · [[mapa-campos-azure]]

> **Cómo usar esta plantilla**
> - Reemplazá cada `<...>` por texto real y **borrá** las líneas de ayuda que empiezan con `>`.
> - Una Característica es más chica que una Épica y más grande que una Historia: un entregable con valor propio que se completa en uno o pocos sprints.
> - **PHI PROHIBIDO:** usá marcadores como `<persona>`, `<documento>`, `<dato-sensible>`.
> - Lo que no sepas con certeza, marcalo como **(pendiente)**. No inventes.
> - Jerarquía en Azure: **Épica → Característica (Feature) → Historia de usuario → Tarea**.
> - La Feature **pertenece al vertical slice de su Épica** (los slices declarados en [[contexto-proyecto]]); **no** lleva tag de slice propio — el slice es la Épica.
> - Al crear por MCP, la **Descripción va en HTML** (`<h3>`, `<ul>/<li>`, `<b>`), no markdown crudo.

---

## Título sugerido

`<Modulo o capacidad>: <bloque de valor concreto>`

> Correcto: `Reservas: seleccion de turno por cercania geografica`
> Correcto: `Estado de arribo: registro y notificacion del arribo`
> Incorrecto: `Mejoras varias` / `Cambios en reservas`

---

## Descripción
> Va al campo **Descripción** (HTML enriquecido).

### Qué es
`<Descripcion de la capacidad que entrega la Caracteristica. Que podra hacer el sistema al terminarla. 3-5 frases.>`

### Valor para el negocio / los usuarios
`<Por que le importa al negocio y al usuario: ahorro de tiempo, menos errores, mejor trazabilidad, mejor experiencia. Concreto.>`

### Alcance
- `<que SI entra: pantallas, estados, canales, endpoints o servicios afectados>`
- `<...>`

### Fuera de alcance
- `<que NO entra en esta Caracteristica>`
- `<...>`

---

## Historias que agrupa
> Las Historias de usuario que, juntas, completan esta Característica. Cada una se crea como work item aparte y se enlaza con relación Primario/Parent. Usá [[historia-de-usuario]] para cada una.

| # | Título de la Historia | Estimación aprox. (SP) | Notas |
|---|---|---|---|
| 1 | `<...>` | `<1·2·3·5·8>` | `<...>` |
| 2 | `<...>` | `<...>` | `<...>` |
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

## Criterios de aceptación de alto nivel
> Condiciones que deben cumplirse para dar la Característica por terminada, a nivel entregable (el detalle fino va en el Gherkin de cada Historia). Deben ser verificables.

- `<condicion 1>`
- `<condicion 2>`
- `<condicion 3>`
- `(pendiente) <condicion por acordar>`

---

## Métricas de éxito
> Cómo medimos que la Característica cumplió. Métrica + objetivo + forma de medición.

- `<metrica 1: tiempo, tasa de error, adopcion, cobertura de casos>`
- `<metrica 2>`

---

## Dependencias
- **Otras migraciones / features en curso:** `<relacion con otro trabajo>` — `(pendiente) si no esta confirmado, marcalo`
- **Backend / datos:** `<depende de un endpoint nuevo, de una entidad de otro servicio>`
- **Integraciones externas:** `<sistema externo del que depende; describi cual y para que>`
- **Otras Características/Historias:** `<...>`

---

## Riesgo
`<1 - High (alto) | 2 - Medium (medio) | 3 - Low (bajo)>` — `<motivo>`
> El valor se selecciona TAL CUAL aparece en Azure (los desplegables muestran el texto en inglés y no se traducen en la herramienta); el texto entre paréntesis es solo ayuda en español.

## Área de valor
`<Business | Architectural>`

## Etiquetas
`<tema>`  *(único tag — techo duro, ninguno más)*

## Ruta de iteración (Sprint)
`<Proyecto>\<Equipo> - Sprint <NN>`

---

## A qué campo de Azure va cada bloque

| Bloque de esta plantilla | Campo visible en Azure | Referencia interna |
|---|---|---|
| Título sugerido | Título | `System.Title` |
| Descripción (qué es, valor, alcance, fuera de alcance) | Descripción | `System.Description` |
| Historias que agrupa | (se crean como work items y se enlazan) | relación Primario/Parent |
| Criterios de aceptación de alto nivel | Criterios de aceptación | `Microsoft.VSTS.Common.AcceptanceCriteria` |
| Métricas de éxito | Descripción | `System.Description` |
| Dependencias | Descripción | `System.Description` |
| Riesgo | Riesgo | `Microsoft.VSTS.Common.Risk` |
| Área de valor | Área de valor | `Microsoft.VSTS.Common.ValueArea` |
| Etiquetas | Etiquetas | `System.Tags` |
| Ruta de iteración | Ruta de iteración | `System.IterationPath` |

> Tipo de work item: **Característica (Feature)**. Detalle de campos y valores: [[mapa-campos-azure]].

---

## Ejemplo (genérico)

> Recuadro ilustrativo con un dominio neutro (reservas). Es solo un ejemplo; la plantilla de arriba es la que se usa.
>
> **Título:** `Reservas: seleccion de recurso por cercania geografica`
> **Qué es:** el operador puede ver y elegir el recurso más cercano al asignar solicitudes de tipo `<tipo1>` y `<tipo2>`.
> **Dependencia:** migración backend (el sistema debe exponer el endpoint de cercanía).
> **Área de valor:** Business.
