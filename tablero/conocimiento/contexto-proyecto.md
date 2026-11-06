---
id: contexto-proyecto
tipo: contexto
estado: F-Draft
modulo: integracion-azure-devops
title: "Contexto del proyecto — {{PROYECTO}}"
author: equipo
tags: [contexto, aterrizaje, cerebro-digital, azure-devops]
last_updated: 2026-08-26
---

# Contexto — {{PROYECTO}}

> **Plantilla a completar por proyecto.** Contexto del proyecto de este repo. Lo confirmado va abajo; lo que no está confirmado va `(pendiente)` y se pregunta — no se inventa. Cada `<completar: …>` es un dato que el equipo tiene que escribir antes de usar el pipeline. El **tablero autorizado** de Azure es el de abajo (`{{AZURE_ORG}}` / `{{AZURE_PROYECTO}}`); las skills **solo** pueden escribir ahí — cualquier otro se rechaza ([[tablero-autorizado]]).

## Producto
<completar: qué es el producto y qué módulos cubre este repo, en 2-3 frases — p. ej. «Migración del módulo **{{PROYECTO}}** de {{PRODUCTO}} ({{ORGANIZACION}}) desde <sistema legado> a una arquitectura web moderna, con análisis y desarrollo asistidos por IA»>.

## Cerebro Digital (fuente del dominio)
- Ubicación: `../../cerebro-digital/` — Bundle OKF, fuente única de verdad del negocio.
- Índice / punto de entrada: `../../cerebro-digital/index.md`.
- Documentación funcional en bruto: `../../documentos/`.
- Provenance (jerarquía de fuentes): observado > minado > spec > derivado.

## Qué lee la IA del Cerebro (mínimos)
La IA no reescribe el dominio: lo **LEE** del Cerebro y referencia la ficha por ruta (enlazar, no copiar). Necesita poder encontrar ahí cuatro grupos:
1. **Entidades del flujo** — los sustantivos del negocio (alimentan el sujeto de los criterios, no un genérico "el registro").
2. **Estados / estatus** — cadenas de estado y transiciones (el "Entonces … queda en estado `<X>`").
3. **Roles** — quién hace qué (el "Como `<rol>`" de las historias).
4. **Canales / integraciones** — por dónde entra el trabajo y con qué sistemas externos habla.
Si alguno no está claro en el Cerebro, ese hueco se completa **en el Cerebro**, no acá.

## Vertical slices / dominios (→ Épicas)
La arquitectura del módulo es un **monolito modular por vertical slices**: cada **Épica = un slice/dominio** (así el trabajo en paralelo no genera conflictos; cada ticket vive en un slice). Fuente: `<completar: ruta del doc de arquitectura en el Cerebro — p. ej. ../../cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md>`.
> **Estos nombres NO son etiquetas.** El slice queda en la Épica; la etiqueta es el tema
> (ver «Etiquetas», más abajo). Un ticket con etiqueta `<slice-1>` está mal etiquetado.

- **<completar: nombre del slice 1>** — slice `<slice-1>`
- **<completar: nombre del slice 2>** — slice `<slice-2>`
- **<completar: nombre del slice n>** — slice `<slice-n>`
- **Integración con <sistema externo>** — slice `<slice-integracion>` `(pendiente)` — si existe, es el único slice que toca la conexión con ese sistema (qué lee y qué escribe se declara acá).
- `(pendiente)` confirmar el desglose fino de capacidades / MVPs por slice contra `../../cerebro-digital/`.

## Flujo troncal del negocio
`(pendiente)` confirmar contra `../../cerebro-digital/` — <completar: la cadena de pasos principal del negocio, p. ej. «solicitud → asignación → ejecución → cierre», y el modelo de datos que la sostiene>.

## Etiquetas (canónicas, sin prefijo)
- **Tag temático — uno solo, techo duro**: el asunto/flujo del ticket, p. ej. `<etiqueta-tematica>`; se escribe **siempre igual**. `(pendiente)` completar la lista con el equipo:

  | Tema | Etiqueta |
  |---|---|
  | <completar: tema 1> | `<etiqueta-tematica>` |
  | <completar: tema 2> | `<completar>` |

  > **Por qué importa la lista (y qué pasa mientras no esté).** Sin una lista acordada, el mismo
  > tema puede salir con nombres distintos según la corrida: una misma Historia puede salir con
  > `<otra-etiqueta>` en una y `<etiqueta-tematica>` en otra. Las dos cumplen la regla, pero
  > filtrar el tablero por una no trae las tarjetas de la otra, y la búsqueda de duplicados
  > pierde una de sus tres pistas. Mientras la lista no exista: si el tema ya tiene una etiqueta
  > en el tablero, se reusa esa; si no, se propone con `⚠` a confirmar. Definirla es completar la
  > tabla de arriba —tema → etiqueta—; no cambia ninguna regla ni ninguna skill.
- **Slice/dominio: sin tag.** El slice (`<slice-1>` · `<slice-2>` · `<slice-n>`) queda capturado por la **Épica** (Épica = slice), no por un tag repetido.
- **Nunca el nombre del producto/repo como tag** (`<producto>`, `<repositorio>`): no filtra nada, lo comparte todo el tablero.

## Azure DevOps (tablero) — ÚNICO tablero autorizado
> Guard de escritura: las skills **solo** pueden crear/editar en ESTE tablero; cualquier otro org/proyecto/team se rechaza con advertencia. Procedimiento y texto de la advertencia: [[tablero-autorizado]]. (El PAT accede a toda la organización, por eso el límite vive en el skill, no en el token.)
- Organización / URL: **`{{AZURE_ORG}}`** — `https://dev.azure.com/{{AZURE_ORG}}`
- Proyecto / board: **`{{AZURE_PROYECTO}}`**
- Team: **`{{AZURE_TEAM}}`**
- URL de referencia: `https://dev.azure.com/{{AZURE_ORG}}/%7B%7BAZURE_PROYECTO%7D%7D/_backlogs/backlog/%7B%7BAZURE_TEAM%7D%7D/Epics`
- Proceso: `(pendiente)` <completar: p. ej. Agile customizado — confirmar contra el tablero>
- Tipos de work item: `(pendiente)` <completar: esperado User Story / Task / Bug / Feature / Epic — confirmar>
- Flujo de estados: `(pendiente)` <completar: p. ej. New → Active → … → Closed>
- Ruta de iteración (formato): `(pendiente)` <completar: p. ej. `<Proyecto>\<Equipo> - Sprint NN`>
- Área (AreaPath): `(pendiente)` <completar>

## Prefijos de etiqueta
No hay prefijo de tag: el tag temático se escribe tal cual (ver «Etiquetas» arriba). La versión (`<versión>`/`<versión>`), si se necesita, va como **campo de contenido** (ej. en Pasos para reproducir de un Bug — ver [[checklists/checklist-bug]] §3), nunca como tag.

## Reglas
- La IA **LEE** el Cerebro Digital (`../../cerebro-digital/`), **referencia** el documento fuente por ruta y **NO copia** contenido (enlazar, no copiar).
- **No inventar**: cada dato duro sin confirmar va `(pendiente)`/`⚠` y se pregunta.
- **PHI prohibido**: marcadores (`<persona>`, `<identificador>`, `<dato-sensible>`…) en vez de datos reales.
