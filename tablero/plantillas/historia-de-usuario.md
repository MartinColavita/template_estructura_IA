---
id: plantilla-historia-de-usuario
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Historia de usuario (Azure DevOps)"
author: equipo
tags: [azure-devops, historia-de-usuario, user-story, plantilla, redaccion, gherkin]
last_updated: 2026-08-26
---

# Plantilla — Historia de usuario (Azure DevOps)

Plantilla rellenable para escribir una Historia de usuario profesional en un tablero de Azure DevOps. Copiá el bloque, reemplazá los `<marcadores>` y borrá las líneas de ayuda (las que empiezan con `>`) antes de pegar en Azure.

Es agnóstica de dominio: sirve para cualquier proyecto de migración/desarrollo. El recuadro final "Ejemplo (genérico)" es solo ilustrativo.

> **Cómo usar esta plantilla**
> - Todo lo que va entre `<...>` es un marcador: reemplazalo por texto real.
> - Las líneas que empiezan con `>` son ayuda: **borralas** antes de pegar en Azure.
> - **PHI PROHIBIDO**: nunca pongas datos personales sensibles ni personales reales. Usá marcadores como `<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`, `<telefono>`. Describí la estructura, no el dato.
> - Si un dato no lo sabés con certeza, marcalo como **(pendiente)** y preguntá; no inventes.
> - Recordá INVEST: una buena historia es Independiente, Negociable, Valiosa, Estimable, Pequeña (Small) y Testeable/verificable.

Relacionados: [[checklist-historia]] · [[mapa-campos-azure]] · [[ejemplo-historia-4-bloques]]

---

## Título sugerido

`<Modulo/dominio>: <accion concreta desde la optica del usuario>`

> Prefijá el módulo o dominio de forma consistente con el resto del tablero.
> Que sea corto, en presente, sin typos y sin jerga técnica. La historia describe VALOR para el usuario, no una tarea técnica.
> Correcto: `Reservas: mostrar el turno disponible mas cercano al confirmar una solicitud`
> Incorrecto: `Reestructurar microservicio de reservas` (eso es un Habilitador tecnico / Tarea, no una Historia)

---

## Descripción
> Va al campo **Descripción** (HTML enriquecido). La Historia se organiza en **4 bloques** para que sirva a **Desarrollo y a Testing**: **(1) Funcionalidad/Historia de usuario**, **(2) Criterios de aceptación** (en Gherkin — van al campo *Criterios de aceptación*, no a este), **(3) Reglas de negocio** con referencia al OKF, y **(4) Casos de uso** (alcance de pruebas); más un inventario de **Datos y estados (funcional)** y el **Documento fuente**. Completá TODOS los bloques: es lo que más se descuida y donde está el valor.

### Funcionalidad / Historia de usuario · *Bloque 1*
> Reúne el contexto, el "Como/quiero/para", el alcance y el fuera de alcance.

### Contexto y problema
`<Que pasa hoy, por que duele, a quien afecta. 2-4 frases. Situacion actual y dolor concreto del usuario o del negocio.>`

### Historia (rol · necesidad · beneficio)
**Como** `<rol real del sistema: operador, supervisor, administrador, usuario final, solicitante...>`
**quiero** `<necesidad concreta y observable>`
**para** `<beneficio / valor de negocio>`.

> El "para" es obligatorio: si no sabés el beneficio, la historia todavía no está lista.

### Alcance
- `<que SI entra: pantalla, campo, endpoint, estado, flujo, integracion afectada>`
- `<...>`

### Fuera de alcance
- `<que explicitamente NO entra en esta historia (evita malentendidos y crecimiento no controlado del alcance)>`
- `<...>`

### Datos y estados (funcional)
> Inventario **funcional** (no técnico) de lo que la historia toca: los **campos/datos** con su regla (obligatorio, catálogo, default, formato/rango) y los **estados y transiciones** permitidas/bloqueadas. Es el **qué** del dato, no el **cómo** (tipos, columnas, endpoints, JSON van en la **Tarea** — Contrato técnico). Da la última precisión para codear sin abrir preguntas. Borralo si la historia no toca datos ni estados (p. ej. solo un texto de UI).
- **Campos / datos:** `<campo>` (`<obligatorio | opcional>`, `<catálogo / default / formato / rango>`) — `<qué representa>` `[RN-<TEMA>-NN]`
- **Estados y transiciones:** `<Estado A>` → `<Estado B>` (`<permitida | bloqueada>`; `<condición>`) `[RN-<TEMA>-NN]`

### Reglas de negocio (con referencia al OKF) · *Bloque 3*
> Numerá cada regla `[RN-<TEMA>-NN]` y, al lado, la **referencia para consultarla en el OKF** (ruta#ancla del Cerebro Digital) — **enlazar, no copiar** (ver [[organizacion-y-trazabilidad]] §4). Así Desarrollo y Testing van a la fuente. El `<TEMA>` es una sigla corta del tema, coherente con la etiqueta temática.
- `[RN-<TEMA>-01] <regla 1>` — *(OKF: `<ruta/al/doc.md#ancla>`)*
- `[RN-<TEMA>-02] <regla 2>` — *(OKF: `<ruta/al/doc.md#ancla>`)*

### Casos de uso (alcance de pruebas) · *Bloque 4*
> Inventario de **flujos/casos que Testing debe cubrir**: delimita el **alcance de las pruebas**. **No** son los Criterios de aceptación (esos son el pass/fail en Gherkin); son la **lista de casos**, cada uno cubierto por ≥1 escenario Gherkin. Incluí feliz + alternativos + borde/negativos + permisos por rol, y mapeá cada caso a su `[RN-…]`.
> *(Ojo con el término: "caso de uso" acá = **caso de prueba/flujo de esta Historia**, distinto del "caso de uso = Feature" del mapeo OKF→ADO.)*
- `CU-01` `<flujo feliz>` — `[RN-<TEMA>-01]`
- `CU-02` `<caso alternativo / borde / negativo / permiso por rol>` — `[RN-<TEMA>-NN]`

### Dependencias
- `<otras historias, servicios/micros, integraciones externas, datos de otro sistema, features en curso>`
- `(pendiente) <marca aca lo que no este confirmado>`

### Documento fuente
- `<ruta/al/documento.md>` (link al repo) — **referencia, no copies el contenido** (ver [[organizacion-y-trazabilidad]] §3).

### Diseño / apoyo visual
- `<enlace a Figma o adjunto>` — **describí en una línea qué muestra**; no dejes el link solo. Si aplica, indicá qué componentes y tokens del design system del proyecto usa.

---

## Criterios de aceptación · *Bloque 2*
> Van al campo **Criterios de aceptación** (`AcceptanceCriteria`), **no** a la Descripción. Escribilos en Gherkin **en español**: Característica, Antecedentes, Escenario, Dado, Cuando, Entonces, Y, Pero. Nunca Given/When/Then. Cada **Caso de uso** (Bloque 4) se cubre con ≥1 escenario de acá.
> Son la definición de "hecho": si no se pueden verificar, no sirven. Cubrí el camino feliz + al menos un caso de error/borde.
> **Al escribirlos en Azure el campo es HTML**: el bloque ```` ```gherkin ```` de abajo es para leer; convertilo a HTML con **todas las keywords en negrita** (`Dado`/`Cuando`/`Entonces`/`Y`/`Pero` incluidas), pasos sangrados y un `<p>` por escenario — si no, se ve como un muro de renglones. Esqueleto y ejemplo: [[checklists/mapa-campos-azure]] §"Esqueleto HTML" y [[criterios-aceptacion-gherkin]] §6.b.

```gherkin
Característica: <nombre corto de la funcionalidad>

  Antecedentes:
    Dado que el <rol> inició sesión en el sistema
    Y está posicionado en <pantalla / modulo>

  # Referenciá la regla que verifica cada escenario: [RN-<TEMA>-NN] (ver organizacion-y-trazabilidad §4)
  Escenario: <camino feliz — nombre descriptivo> [RN-<TEMA>-01]
    Dado <estado o precondicion>
    Cuando <accion del usuario>
    Entonces <resultado observable en pantalla o en el estado del dato>
    Y <verificacion adicional: dato guardado, evento enviado, estado cambiado>

  # Agregá al menos 1 escenario de error o borde. Ejemplo:
  Escenario: <no se cumple una precondicion>
    Dado <precondicion que falta>
    Cuando <accion del usuario>
    Entonces el sistema muestra el mensaje "<texto esperado>"
    Y no se modifica el estado del dato
```

> Para variantes con datos, usá **Esquema del escenario** + **Ejemplos** (nunca con PHI real):
>
> ```gherkin
> Esquema del escenario: resultado segun tipo de <entidad>
>   Dado un registro de tipo <tipo>
>   Cuando el usuario confirma la accion
>   Entonces el registro queda en estado <estado>
>
>   Ejemplos:
>     | tipo | estado    |
>     | A    | Aprobado  |
>     | B    | Pendiente |
> ```

---

## Puntos de historia (Story Points)
`<1 · 2 · 3 · 5 · 8 · 13>`

> Escala relativa de esfuerzo/complejidad/incertidumbre (no horas). Si te da > 8, probablemente hay que partir la historia.
> Si no la podés estimar, falta información (INVEST: "Estimable").

## Prioridad
`<1 · 2 · 3 · 4>`  *(1 = máxima, 4 = mínima)*

## Riesgo
`<1 - High (alto) | 2 - Medium (medio) | 3 - Low (bajo)>` — `<por que: toca flujo critico, depende de otra migracion, afecta datos sensibles, etc.>`
> El valor se selecciona TAL CUAL aparece en Azure (los desplegables muestran el texto en inglés y no se traducen en la herramienta); el texto entre paréntesis es solo ayuda en español.

## Área de valor
`<Business | Architectural>`  *(Business = valor al negocio/usuario; Architectural = habilitador tecnico)*

## Etiquetas
`<tema>`  *(único tag — techo duro, ninguno más; sin tag de slice: el slice es la Épica)*
> **Etiqueta temática obligatoria** (`<tema>`, **sin prefijo**, siempre escrita igual: `reservas`, `cancelacion`…): agrupa todos los tickets del mismo asunto para filtrarlos juntos. Ver [[organizacion-y-trazabilidad]] §1.

## Ruta de iteración (Sprint)
`<Proyecto>\<Equipo> - Sprint <NN>`

## Relaciones / Enlaces
- **Primario/Parent:** `<#ID o título de la Feature/Épica madre>`
- **Relacionadas (Related):** `<#ID o título de otras UH del mismo tema>`
- **Documento fuente:** `<ruta/al/documento.md>` (link al repo) — referencia, no contenido
> La IA **propone** las relaciones por título/tema; los **#ID reales son dato duro**: se confirman o se resuelven por MCP (`⚠` hasta confirmar). Ver [[organizacion-y-trazabilidad]] §2.

## Notas para QA
> Lo que la **prueba de punta a punta** necesita y el Gherkin no dice. Cinco líneas fijas, siempre con este rótulo
> (las lee `bin/armar-e2e.py`); lo que no se sabe va `⚠` y vuelve como pregunta, nunca inventado.
- **Pantalla / ruta:** `<pantalla donde ocurre el flujo y su ruta, p. ej. Reservas de la sala · /salas/{id}/reservas>`
- **Rol / usuario de prueba:** `<rol que ejecuta el flujo y con qué usuario de prueba entra (nunca credenciales acá: por variable de entorno)>`
- **Datos iniciales:** `<qué tiene que existir antes de cada corrida, con marcadores: una sala, una reserva activa de <persona> de 10 a 12>`
- **Identificadores:** `<los identificadores estables que el front expone para este flujo (data-testid o el que fije DEC-003): lista-reservas, cancelar-{id}, estado-{id}>`
- **Ambiente:** `<contra qué ambiente corre y qué queda fuera (producción, nunca)>`
- `<casos borde a validar a mano, integraciones a chequear, regresión a mirar>`
> En el work item real la validación queda en el **Historial**; estas líneas se mantienen con la Historia.

---

## A qué campo de Azure va cada bloque

| Bloque de esta plantilla | Campo visible en Azure | Referencia interna |
|---|---|---|
| Título sugerido | Título | `System.Title` |
| Descripción — Bloque 1 (Funcionalidad) + Bloque 3 (Reglas de negocio) + Bloque 4 (Casos de uso) + Documento fuente | Descripción | `System.Description` |
| Criterios de aceptación (Gherkin) | Criterios de aceptación | `Microsoft.VSTS.Common.AcceptanceCriteria` |
| Puntos de historia | Puntos de historia | `Microsoft.VSTS.Scheduling.StoryPoints` |
| Prioridad | Prioridad | `Microsoft.VSTS.Common.Priority` |
| Riesgo | Riesgo | `Microsoft.VSTS.Common.Risk` |
| Área de valor | Área de valor | `Microsoft.VSTS.Common.ValueArea` |
| Etiquetas (incluye la temática) | Etiquetas | `System.Tags` |
| Ruta de iteración (Sprint) | Ruta de iteración | `System.IterationPath` |
| Relaciones (Parent / Related) | (enlaces del work item) | `System.LinkTypes.Hierarchy` (Parent) · `System.LinkTypes.Related` |
| Documento fuente | (dentro de) Descripción | `System.Description` |
| Notas para QA | (pasa al) Historial durante la validación | `System.History` |

> Tipo de work item: **Historia de usuario (User Story)**. Las historias hijas de una Épica/Característica se enlazan con relación **Primario/Parent**; las UH del mismo tema que se tocan, con relación **Related**. Al crear por MCP, los enlaces se materializan con `manage_work_item_link` (con confirmación humana). Detalle completo de campos, etiqueta temática y relaciones: [[mapa-campos-azure]] y [[organizacion-y-trazabilidad]].

---

## Ejemplo (genérico)

> Recuadro ilustrativo con un dominio neutro (reservas). Es solo un ejemplo; la plantilla de arriba es la que se usa.
>
> - **Título:** `Reservas: mostrar el recurso disponible mas cercano al confirmar una solicitud`
> - **Como** operador **quiero** ver el recurso disponible más cercano **para** reducir el tiempo de asignación.
> - **Reglas de negocio (dominio):** `[RN-RES-01]` solo aplica a solicitudes de tipo `<tipo1>`/`<tipo2>`; `[RN-RES-02]` el estado `<Estado2>` (confirmado) solo puede setearse después de `<Estado1>`.
> - **Área de valor:** Business · **Etiquetas:** `reservas` (una sola).
> - **Relaciones:** Primario/Parent: Feature "Asignación de recursos" · Relacionadas: UH "Registrar la confirmación del recurso".
> - **Documento fuente:** `conocimiento/funcional/asignacion-de-recursos.md` (link al repo) — referencia, no contenido.
