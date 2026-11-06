---
id: redaccion-tickets-historias-de-usuario
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Historias de usuario
author: equipo
tags: [historias-de-usuario, invest, azure-devops, valor-de-negocio, split]
last_updated: 2026-08-26
---

# Historias de usuario

Guía agnóstica para convertir un pedido pobre ("Reestructurar el módulo X", "Pantalla de login", un link de diseño suelto) en una **historia de usuario** profesional, con rol, necesidad, valor y forma de saber cuándo está terminada. Los criterios de aceptación tienen su propia guía: ver [[criterios-aceptacion-gherkin]].

Aplica a cualquier proyecto del equipo. Los ejemplos concretos van en recuadros **Ejemplo (genérico)**; el dominio de tu proyecto se define en [[contexto-proyecto]].

---

## 1. Qué es (y qué NO es) una historia de usuario

Una **historia de usuario** es una descripción corta de una funcionalidad **contada desde la perspectiva de quien la va a usar y del valor que obtiene**. No es una especificación técnica ni un contrato: es una **promesa de conversación** entre el analista, el equipo de desarrollo y el negocio.

El tipo de work item equivalente en Azure DevOps suele ser **Historia de usuario** (proceso Agile). Es el nivel donde se planifica valor para el usuario final, por encima de las **Tareas** técnicas que la implementan.

### Qué SÍ es

- Una unidad de **valor entregable** para un rol de negocio.
- Algo **verificable**: se puede demostrar y decir "listo".
- El punto de partida de una **conversación**, no el final.

### Qué NO es

| No es... | Ejemplo de mal ticket | Por qué está mal |
|---|---|---|
| **Una tarea técnica disfrazada** | Historia "Reestructurar el módulo de alertas" con Descripción = 3 links de repositorio + "Rama a mover: develop", Criterios de aceptación **vacíos**, sin Puntos de historia. | No hay rol, ni necesidad, ni beneficio. Nadie sabe cuándo está "hecha" para el usuario. Esto es una **Tarea**, no una Historia (ver sección 7). |
| **Un volcado de pantallas / un link** | Tarea "Pantalla de inicio de sesión" cuya Descripción es solo un enlace de diseño: "Adjunto el link que contiene las tareas a realizar". | El diseño es **apoyo**, no sustituye el alcance escrito. Sin texto, el equipo interpreta lo que quiere y QA no puede validar. |
| **Un pantallazo de la solución técnica** | "Agregar el parámetro `estado=<código>` al controller de estados". | Describe el **cómo** interno, no el **qué** ni el **para qué** del usuario. Encierra la solución antes de la conversación. |

> Regla rápida: si la frase solo tiene sentido para un desarrollador y no menciona a ningún rol de negocio ni el valor que recibe, **probablemente es una Tarea, no una Historia**.

---

## 2. La plantilla de rol: Como / quiero / para

Toda historia arranca por esta estructura de una sola oración:

> **Como** `<rol>`, **quiero** `<necesidad / capacidad>`, **para** `<beneficio / valor de negocio>`.

- **Como `<rol>`** — quién la necesita. Usá un **rol real del negocio**, no "el usuario" genérico.
- **quiero `<necesidad>`** — qué capacidad quiere tener (en lenguaje de negocio, no técnico).
- **para `<beneficio>`** — por qué le importa; el valor. Si no podés completar el "para", quizás la historia no aporta valor y hay que revisarla.

### Cómo identificar los roles reales

El paso agnóstico es siempre el mismo: **usá los roles que ya existen en el dominio del proyecto**, no "usuario". Cada proyecto define su catálogo de roles en el Cerebro Digital ([[contexto-proyecto]]). Un rol bien elegido tiene un objetivo operativo claro y una necesidad que solo él tiene.

> **Ejemplo (genérico).** Roles reales de un sistema: operador (recibe la solicitud, arma el registro), asignador (asigna el recurso), supervisor, revisor, referente de monitoreo, operador de campo (informa el avance en terreno), administrador funcional. Una necesidad típica del asignador: "...quiero filtrar recursos por cercanía geográfica...".

> Regla PHI: en los ejemplos de historias **nunca** pongas datos reales (nombre, documento, teléfono, dato sensible del dominio, identificador). Usá marcadores como `<persona>`, `<documento>`, `<dato-sensible>`.

### Ejemplo bueno (genérico)

> **Como** asignador, **quiero** filtrar la lista de recursos por cercanía geográfica al domicilio de la `<persona>`, **para** asignar el recurso que llega antes y reducir el tiempo de respuesta.

Tiene rol real, necesidad de negocio y un beneficio medible (tiempo de respuesta).

---

## 3. Las 3C: Tarjeta, Conversación, Confirmación

Una historia vive en tres dimensiones (las **3C** de Ron Jeffries). Recuerdan que la historia no es solo el texto:

1. **Tarjeta (Card)** — el texto corto de la historia (el "Como/quiero/para" + notas). Es un **recordatorio**, deliberadamente breve. En Azure es el Título + el arranque de la Descripción. No intenta capturar todo el detalle.
2. **Conversación (Conversation)** — el intercambio entre analista, equipo y negocio que llena los huecos. Muchas dudas ("¿aplica a todos los casos o solo a uno?", "¿el dato llega por este canal o por otro?") se resuelven acá, no en el texto. La historia **habilita** la conversación, no la reemplaza.
3. **Confirmación (Confirmation)** — cómo sabemos que está terminada: los **Criterios de aceptación**. Es la parte que más se descuida (historias con criterios vacíos). Ver [[criterios-aceptacion-gherkin]].

> Las 3C explican por qué una historia con Descripción rica pero **Criterios de aceptación vacíos** está incompleta: le falta la tercera C.

---

## 4. INVEST: las seis propiedades de una buena historia

**INVEST** es el chequeo de calidad de una historia. Cada letra, con su verificación y un ejemplo de cumplir / no cumplir.

### I — Independiente

Se puede priorizar, estimar y desarrollar **sin depender fuertemente** de otra historia. Si dos historias solo tienen sentido juntas, quizás son una sola o hay que reordenarlas.

- **No cumple:** "Guardar el filtro" que no sirve para nada hasta que exista "Aplicar el filtro".
- **Cumple:** "Filtrar por cercanía" es útil por sí sola; "Guardar el filtro favorito" se puede hacer después como mejora independiente.

### N — Negociable

Describe **qué** y **para qué**, no encierra el **cómo**. Deja margen para que el equipo proponga la mejor solución técnica en la conversación.

- **No cumple:** "Agregar el parámetro `estado=<código>` al controller y propagarlo por la capa de integración." (dicta la implementación).
- **Cumple:** "Como operador de campo, quiero informar que llegué al domicilio para que el equipo vea el avance de la solicitud en tiempo real." (el cómo lo define el equipo).

### V — Valiosa

Entrega valor visible a un rol de negocio. Si el "para" queda vacío o suena a "para que el código quede mejor", revisá si es una historia o una tarea de refactor.

- **No cumple:** "Reestructurar el módulo de alertas a estructura `api+impl`." (valor puramente técnico → es Tarea/Feature técnica).
- **Cumple:** "Como referente de monitoreo, quiero recibir la alerta en el panel para actuar antes de que el problema se agrave."

### E — Estimable

El equipo tiene información suficiente para asignarle **Puntos de historia**. Si no se puede estimar, suele faltar alcance o hay demasiada incertidumbre (hace falta una investigación previa / spike).

- **No cumple:** "Mejorar la georreferenciación." (¿qué parte? ¿qué precisión?) → no estimable.
- **Cumple:** "Mostrar en el mapa la posición del recurso actualizada cada `<intervalo>` segundos." → acotada, estimable.

### S — Pequeña (Small)

Cabe cómoda dentro de un sprint. Si es más grande, se **divide** (ver sección 7).

- **No cumple:** "Integración bidireccional con un sistema externo" completo (integración, mapa, estados, notificaciones) como una sola historia.
- **Cumple:** "Recibir por la integración el cambio de estado del recurso y reflejarlo en el registro."

### T — Verificable (Testable)

Se puede comprobar objetivamente si está hecha, con criterios de aceptación demostrables. QA tiene que poder validarla.

- **No cumple:** "La pantalla de login tiene que ser rápida y linda." (subjetivo, no verificable).
- **Cumple:** "El inicio de sesión corporativo redirige al usuario autenticado a la pantalla inicial en menos de `<N>` segundos y muestra error legible si las credenciales fallan."

---

## 5. Anatomía completa de una buena historia (mapa a campos de Azure DevOps)

Estos son los campos del work item **Historia de usuario** y qué poner en cada uno.

### Título (`System.Title`)

Enunciado claro, orientado a valor, con prefijo de módulo consistente. Evitá el imperativo técnico seco.

- Evitar: "Reestructurar módulo de alertas", "Pantalla login".
- Preferir: "Asignación — Filtrar recursos por cercanía geográfica", "Estados — Registrar el avance del recurso (`<código de estado>`)".

### Descripción (`System.Description`, HTML enriquecido)

Es el corazón de la Tarjeta. Estructura recomendada:

1. **Contexto** — dónde ocurre en el flujo del negocio y qué problema resuelve hoy.
2. **Rol / necesidad / beneficio** — la oración "Como... quiero... para..." (sección 2).
3. **Alcance (dentro)** — qué entra: módulo, entidades afectadas, canales, tipos de operación, estados involucrados.
4. **Fuera de alcance** — qué **no** entra (evita malentendidos y peleas en QA).
5. **Datos y estados (funcional)** — inventario **funcional** (no técnico) de los **campos/datos** que toca (obligatorio, catálogo, default, formato/rango, con su `[RN-…]`) y los **estados y transiciones** permitidas/bloqueadas. Es el **qué** del dato; el **cómo** (tipos, columnas, endpoints) va en la Tarea. Borrable si la historia no toca datos ni estados.
6. **Reglas de negocio (con referencia al OKF)** — condiciones y validaciones; cada `[RN-…]` indica su **ruta#ancla en el Cerebro Digital** para poder consultarla (enlazar, no copiar). Si no lo sabés con certeza, marcalo "(pendiente)" y preguntá; no inventes.
7. **Casos de uso (alcance de pruebas)** — inventario de flujos que Testing debe cubrir (feliz + alternativos + borde/negativos + permisos por rol), cada uno mapeado a un `[RN-…]` y cubierto por ≥1 escenario Gherkin. No son los Criterios (pass/fail): son el **alcance** de las pruebas.
8. **Dependencias** — de otras historias, de una migración, de una integración externa, de datos de un sistema legacy.
9. **Notas de diseño** — el link de diseño va **como apoyo**, nunca como sustituto del alcance escrito. Resumí en texto qué muestra el diseño; el link amplía, no reemplaza.

> **Aterrizaje al proyecto.** Ajustar al stack real del equipo, que se documenta en `cerebro-digital/modulo-ejemplo/arquitectura/esqueleto-proyectos.md`: qué hace el back (con lógica y base de datos propias, no un mero pasamanos), cómo se construye el front y qué design system usa. Si una historia implica lógica nueva, aclará en qué capa vive (servicio de back, front, integración) para que sea estimable.

### Criterios de aceptación (`Microsoft.VSTS.Common.AcceptanceCriteria`)

La tercera C (Confirmación). **Nunca los dejes vacíos.** Redacción y formato (incluido Gherkin en español: Dado/Cuando/Entonces) en [[criterios-aceptacion-gherkin]].

### Puntos de historia (`Microsoft.VSTS.Scheduling.StoryPoints`)

Estimación relativa del esfuerzo/complejidad (no horas). Si no se puede estimar, la historia falla la "E" de INVEST: falta alcance.

### Prioridad (`Microsoft.VSTS.Common.Priority`, 1–4)

1 = máxima. Refleja urgencia/valor de negocio, no dificultad técnica.

### Riesgo (`Microsoft.VSTS.Common.Risk`)

Alto/Medio/Bajo. Subilo cuando toca integraciones externas, PHI, migración de módulos o cambios en el flujo troncal.

### Área de valor (`Microsoft.VSTS.Common.ValueArea`)

**Business** (valor al negocio/usuario) o **Architectural** (habilita capacidad técnica). Una historia de valor de usuario suele ser Business; la reestructuración de módulos es Architectural.

### Etiquetas y Ruta de iteración

Etiquetas: **una sola, temática**, sin prefijo y siempre igual — **techo duro, ninguna más**. Nunca el nombre del producto/repo, nunca la versión, nunca el slice. Si hace falta dejar asentado el componente o la versión, van como **campo de contenido**, no como etiqueta ([[organizacion-y-trazabilidad]] §1). Ruta de iteración: el sprint al que apunta.

---

## 6. De título imperativo-técnico a historia con valor

El patrón para rescatar un pedido pobre: **preguntá "¿quién lo necesita y para qué?"** hasta que aparezca el valor.

### Caso A — "Reestructurar el módulo de alertas"

Es una reestructuración técnica. Dos salidas válidas:

- **Si de verdad no hay valor de usuario nuevo** → no la fuerces a Historia: registrala como **Tarea** (o Feature Architectural) con su alcance técnico, criterios de "hecho" técnicos (compila, pasa los gates, mismo comportamiento observable) y enlazada a su Feature de migración. No toda tarjeta debe ser una historia.
- **Si detrás hay valor** (ej. la reestructuración habilita una alerta nueva) → separá: la parte técnica queda como Tarea, y la capacidad de negocio se escribe como Historia:
  > **Como** referente de monitoreo, **quiero** recibir la alerta `<tipo>` en el panel, **para** intervenir antes de que el problema se agrave.

### Caso B — "Pantalla de login" (solo un link de diseño)

Convertila preguntando qué logra el usuario:

> **Título:** Autenticación — Ingreso del operador con el inicio de sesión corporativo
> **Como** operador, **quiero** iniciar sesión con mis credenciales corporativas, **para** acceder al sistema de forma segura y empezar a trabajar.
>
> **Alcance:** pantalla de login del frontend, redirección de autenticación, manejo de error de credenciales, redirección post-login a la pantalla inicial.
> **Fuera de alcance:** recuperación de contraseña (la gestiona el proveedor de identidad corporativo), gestión de roles/permisos (historia aparte).
> **Notas de diseño:** el diseño `<link>` muestra el layout; **es apoyo, no reemplaza este alcance**.
> **Criterios de aceptación:** ver [[criterios-aceptacion-gherkin]].

---

## 7. Técnicas de división (split) de historias grandes

Cuando una historia no cumple la "S" (Pequeña) de INVEST, se divide en historias más chicas que **cada una entregue valor**. Nunca dividas en "capas técnicas" (frontend / backend / base de datos) como si fueran historias: eso son tareas de una misma historia.

### a) Por pasos del flujo (workflow)

El flujo troncal del negocio sugiere los cortes.

> **Ejemplo (genérico).** Épica "Gestión de la solicitud" → registrar la solicitud y datos del `<persona>` · clasificar la solicitud · seleccionar y asignar el recurso · ejecutar la solicitud y seguir su estado.

### b) Por reglas de negocio / variaciones

Empezá por la regla más común y dejá las excepciones como historias aparte.

> "Registrar el avance de estado" → para el caso principal · para una variante · manejo del intento en un registro que no lo admite (excepción).

### c) Por camino feliz vs. caminos alternativos

Entregá primero el camino feliz; los errores y excepciones van después.

> "Selección de recurso" → (feliz) asignar un recurso disponible · (alternativo) no hay recurso → derivar/escalar · (alternativo) el recurso rechaza → reasignar.

### d) Por operaciones CRUD

Cada operación es una historia si aporta valor por separado.

> "Gestión de canales" → ver los canales configurados · alta de un canal · baja/deshabilitación de un canal.

### e) Por interfaz / servicio (mismo negocio, distinto canal)

La misma capacidad expuesta por distintos canales.

> "Informar estado de la solicitud" → desde la app del operador de campo · desde el panel de monitoreo · desde la integración externa.

> Señal de que hay que dividir: la historia usa "y" varias veces, mezcla varios canales, o su estimación se dispara. Cortá hasta que cada pedazo sea INVEST.

---

## 8. Checklist rápido antes de guardar la historia

- [ ] El **Título** orienta a valor y tiene prefijo de módulo (no es un imperativo técnico seco).
- [ ] La **Descripción** tiene contexto + "Como/quiero/para" + alcance + fuera de alcance + **datos y estados (funcional)** + reglas (con ref al OKF) + **casos de uso** + dependencias.
- [ ] Si hay diseño, está **como apoyo** y el alcance está escrito igual.
- [ ] Los **Criterios de aceptación** NO están vacíos (ver [[criterios-aceptacion-gherkin]]).
- [ ] Pasa **INVEST** (o está justificado por qué no).
- [ ] Tiene **Puntos de historia**, **Prioridad** y (si aplica) **Riesgo**.
- [ ] Si es puramente técnica sin valor de usuario → es **Tarea/Feature**, no Historia (sección 7 caso A).
- [ ] Cero PHI: solo marcadores `<persona>`, `<documento>`, `<dato-sensible>`, etc.

---

## Ver también

- Criterios de aceptación (Gherkin en español): [[criterios-aceptacion-gherkin]]
- Definición de Preparado / Terminado: [[definicion-preparado-terminado]]
- Estimación y priorización: [[estimacion-y-priorizacion]]
- Antipatrones (cómo NO escribir): [[antipatrones]]
- Dominio del proyecto: [[contexto-proyecto]]
