---
id: redaccion-tickets-antipatrones
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Antipatrones al escribir tickets
author: equipo
tags: [antipatrones, calidad, tickets, historias, bugs, revision]
last_updated: 2026-08-26
---

# Antipatrones al escribir tickets

Catálogo de los errores típicos que se ven en un tablero de Azure DevOps, con ejemplo pobre, por qué falla y cómo se arregla. Tono constructivo: no es reproche, es un mapa de las trampas más comunes para no caer en ellas. Método agnóstico; los ejemplos concretos van rotulados **Ejemplo (genérico)**.

---

## Cómo usar este catálogo

Cada antipatrón tiene: **nombre**, **ejemplo pobre** (parafraseado, sin nombres reales ni PHI), **por qué falla** y **cómo se arregla**. Si estás por pegar una tarjeta que se parece a alguno de estos "ejemplos pobres", frená y aplicá el arreglo.

Los ejemplos usan marcadores tipo `<persona>`, `<identificador>`, `<link>` en vez de datos reales, tal como debe hacerse siempre en un producto que maneja datos personales (datos personales sensibles = PHI, prohibido).

---

## 1. La historia que en realidad es una tarea técnica (sin rol / necesidad / beneficio)

**Ejemplo pobre**
> **Título:** Reestructurar módulo de alertas
> **Descripción:** Ver repos: `<link-1>` · `<link-2>` · `<link-3>` · Rama a mover: develop
> **Criterios de aceptación:** *(vacío)*
> **Puntos de historia:** *(sin valor)*

**Por qué falla**
- Está tipada como **Historia de usuario** pero no tiene rol, necesidad ni beneficio: nadie sabe para quién ni para qué. Es trabajo técnico interno.
- Sin criterios de aceptación no hay forma de saber cuándo está "hecha".
- Sin puntos de historia no se puede planificar.

**Cómo se arregla**
- Si es trabajo técnico de la migración/reestructuración sin valor directo al usuario, tipalo como **Tarea** (o como Historia con Área de valor = *Architectural*), colgada de su Feature/Épica.
- Escribí el objetivo técnico concreto: qué se mueve, desde/hacia qué estructura (`api+impl`), qué queda igual.
- Poné **criterios de aceptación verificables**: "el servicio compila y arranca en dev mode", "los endpoints responden igual que antes", "gates de seguridad y calidad del pipeline en verde", "no cambió el contrato de la API".
- Estimá (puntos de historia o esfuerzo en horas según el tipo).

---

## 2. Descripción = solo un link (diseño / repositorio)

**Ejemplo pobre**
> **Título:** Pantalla de inicio de sesión
> **Descripción:** Adjunto el link que contiene las tareas a realizar: `<link-diseño>`

**Por qué falla**
- El link puede cambiar, caducar o requerir permisos. Dentro de un año nadie sabe qué decía.
- El alcance no está escrito en ningún lado: no se puede estimar, revisar ni testear.
- El desarrollador tiene que interpretar el diseño sin criterio de "listo".

**Cómo se arregla**
- El link es **apoyo**, no el contenido. Escribí el alcance en texto: qué pantalla, qué campos, qué validaciones, qué pasa en error (inicio de sesión fallido, usuario sin permisos), qué comportamiento responsive.
- Traducí el diseño a **criterios de aceptación** concretos.
- Dejá el link de diseño como referencia adicional, no como la única fuente.

---

## 3. Criterios de aceptación vacíos

**Ejemplo pobre**
> **Título:** Como operador quiero ver las solicitudes activas de mi grupo
> **Criterios de aceptación:** *(vacío)*

**Por qué falla**
- El título promete valor, pero sin criterios no hay definición de "hecho". QA no sabe qué validar y el dev no sabe cuándo parar.
- Se abre a interpretación: ¿qué es "activo"? ¿de qué grupo? ¿qué columnas?

**Cómo se arregla**
- Escribí criterios verificables, preferentemente en **Gherkin en español** (Dado / Cuando / Entonces):

> **Escenario:** Ver solicitudes activas del grupo propio
> **Dado** que soy operador asignado al grupo `<grupo>`
> **Cuando** abro el listado de solicitudes activas
> **Entonces** veo solo las solicitudes en estado activo del grupo `<grupo>`
> **Y** cada fila muestra tipo de solicitud, estado y recurso asignado.

- Cubrí también el camino no feliz (sin resultados, sin permisos, error del backend). Ver [[criterios-aceptacion-gherkin]].

---

## 4. El bug "Ver adjunto"

**Ejemplo pobre**
> **Título:** Se dehabilita el botón No asignar el recurso
> **Pasos para reproducir:** Ver adjunto. Pasa cuando estás en la solicitud y le das y no te deja, ya lo vio también producción.

**Por qué falla**
- "Ver adjunto" no es reproducible: el adjunto se pierde o no se entiende sin contexto.
- El título tiene typo ("dehabilita") y no dice el módulo.
- Mezcla ambientes (Testing + Producción) en una línea.
- No separa esperado de obtenido.

**Cómo se arregla**
- Título: `Asignación - Selección de recurso: el botón "No asignar el recurso" queda deshabilitado tras cancelar`.
- Escribí los pasos numerados en el cuerpo (el adjunto es apoyo).
- Un solo ambiente por reporte.
- Bloques separados de Resultado esperado / Resultado obtenido, más el porqué. Ver [[bugs-y-defectos]].

---

## 5. Flujo de conciencia sin estructura

**Ejemplo pobre**
> **Pasos:** entro a la solicitud de la persona y ahí cuando quiero asignar el recurso me tira que no y a veces sí anda pero cuando volvés para atrás ya no, me parece que es algo de la pantalla anterior, probé de nuevo y nada, avisen.

**Por qué falla**
- Todo en una oración: no se pueden seguir pasos.
- Mezcla hipótesis ("me parece que es de la pantalla anterior") con hechos.
- "A veces sí a veces no" sin decir la frecuencia ni las condiciones.

**Cómo se arregla**
- Separá en **pasos numerados** desde un punto conocido.
- Poné la frecuencia en Observaciones ("intermitente, ~3 de 10 intentos, siempre al volver atrás con el navegador").
- Las hipótesis van en Observaciones marcadas como hipótesis, no en los pasos.
- Los hechos (esperado/obtenido) van en sus bloques.

---

## 6. No separar esperado de obtenido

**Ejemplo pobre**
> **Pasos para reproducir:** Al confirmar la clasificación el sistema tira error y no debería, tendría que guardar la clasificación.

**Por qué falla**
- Esperado y obtenido están fundidos en una frase: cuesta leer qué es el defecto y qué es el comportamiento correcto.
- No hay texto del error (¿500? ¿mensaje en pantalla?).

**Cómo se arregla**
- **Resultado esperado:** al confirmar, se guarda la clasificación y se avanza a la solicitud.
- **Resultado obtenido:** al confirmar aparece error `500` (mensaje exacto: `<texto>`) y la clasificación no se guarda.
- **Por qué es un error:** el operador no puede continuar con la solicitud, se traba el flujo de atención.
- Dos bloques de hecho + el porqué, siempre.

---

## 7. Título con typos / prefijo de módulo inconsistente

**Ejemplo pobre**
> `boton no anda` · `Se dehabilita...` · `LISTADOS>>servcios` · `bug caso`

**Por qué falla**
- Los typos quedan para siempre y dan imagen de descuido.
- Sin prefijo de módulo consistente, el tablero no se puede filtrar ni escanear.
- Títulos genéricos ("bug caso") no dicen nada en una lista de 200 tarjetas.

**Cómo se arregla**
- Formato de casa: **`Módulo - Contexto: síntoma`**, revisado sin typos.
- Prefijo de módulo consistente con el resto del tablero.
- Un síntoma concreto y observable en el título.

---

## 8. Mezcla de ambientes / versiones

**Ejemplo pobre**
> **Pasos:** Pasa en Testing pero también lo vimos en Producción, y en una versión no me acuerdo cuál, capaz la vieja.

**Por qué falla**
- Un mismo reporte describiendo dos ambientes no se puede cerrar limpio: el fix se valida en uno y "sigue" en otro.
- Sin versión (frontend y backend), el dev no sabe contra qué código mirar.

**Cómo se arregla**
- **Un ambiente por reporte** (<ambientes de prueba>/PREPROD/PROD). Si aplica a más, aclaralo en Observaciones pero describí uno.
- Siempre las dos versiones: frontend y backend.
- Si no sabés la versión con certeza, marcala "(pendiente)", no la inventes.

---

## 9. Sin valor de negocio ni impacto en el usuario

**Ejemplo pobre**
> **Título:** Agregar campo nuevo en la grilla
> **Descripción:** Hay que sumar una columna más.

**Por qué falla**
- No dice para quién ni para qué. ¿Qué decisión operativa habilita esa columna? ¿A quién le sirve?
- Sin impacto, no se puede priorizar contra el resto del backlog.

**Cómo se arregla**
- Formato historia: **Como** `<rol>` **quiero** `<capacidad>` **para** `<beneficio operativo>`.
- Ejemplo: "Como operador quiero ver el grupo asignado en la grilla de solicitudes activas para derivar la solicitud sin abrir cada una".
- Enunciá el impacto: cuántos usuarios, qué tarea acelera, qué riesgo reduce.

---

## 10. Sin estimación / sin gravedad

**Ejemplo pobre**
> Historia sin **Puntos de historia**. Bug sin **Gravedad**.

**Por qué falla**
- Sin puntos de historia, la historia no entra a un sprint de forma planificable.
- Sin gravedad, el bug no se puede triar: compite a ciegas con todo lo demás.

**Cómo se arregla**
- Historias: asigná **Puntos de historia** (o marcá que falta refinar, no lo dejes en blanco silencioso).
- Bugs: asigná **Gravedad** (1-Critical … 4-Low) y, si podés, **Prioridad** (1–4). Criterios en [[estimacion-y-priorizacion]].
- Regla mínima: ninguna tarjeta sale a planificación sin su medida (puntos para historias/tareas, gravedad para bugs).

---

## 11. Sobre-etiquetado (más de un tag)

**Ejemplo pobre**
> Una Épica de reserva de salas con **Etiquetas:** `reserva-salas`, `<producto>`, `<repositorio>`. Una Historia hija con **Etiquetas:** `reserva-salas`, `<slice-1>`, `<producto>`, `<repositorio>`.

**Por qué falla**
- `<producto>` y `<repositorio>` son el nombre del producto/repo: los comparte el 100% del tablero, así que no filtran nada — son ruido, no trazabilidad.
- `<slice-1>` es un tag de sub-flujo/slice: ya está capturado por la Épica (Épica = slice), agregarlo lo duplica y fragmenta la búsqueda.
- Cuanto más tags distintos combine cada ticket, peor funciona la **deduplicación** por tag (ver [[deduplicacion-antes-de-crear]]): tickets del mismo tema quedan bajo combinaciones de tags distintas y la búsqueda no los encuentra a todos juntos.

**Cómo se arregla**
- **Un solo tag, siempre el mismo, en toda la descendencia:** ambos ejemplos de arriba llevan **solo** `reserva-salas`.
- Si hace falta trazar versión (frontend/backend), va como **campo de contenido** (ej. en Pasos para reproducir de un Bug), nunca como tag adicional. Ver [[organizacion-y-trazabilidad]] §1.

---

## Resumen de arreglos

| Antipatrón | Arreglo en una línea |
|---|---|
| 1. Historia que es tarea técnica | Tipala como Tarea / Architectural, con criterios verificables |
| 2. Solo un link | Escribí el alcance en texto; el link es apoyo |
| 3. Criterios vacíos | Gherkin en español, incluí el camino no feliz |
| 4. "Ver adjunto" | Pasos numerados en el cuerpo; adjunto solo de apoyo |
| 5. Flujo de conciencia | Pasos numerados + frecuencia + hipótesis aparte |
| 6. Esperado/obtenido fundidos | Dos bloques separados + el porqué, con texto exacto del error |
| 7. Typos / prefijo inconsistente | `Módulo - Contexto: síntoma`, sin typos |
| 8. Mezcla ambientes/versiones | Un ambiente por reporte + las dos versiones |
| 9. Sin valor de negocio | Como `<rol>` quiero `<algo>` para `<beneficio>` |
| 10. Sin estimación/gravedad | Puntos para historias, Gravedad para bugs |
| 11. Sobre-etiquetado | Un solo tag, siempre igual; nunca producto/repo ni slice |

---

## Ver también

- Cómo escribir bugs bien: [[bugs-y-defectos]]
- Cómo escribir historias bien: [[historias-de-usuario]]
- Criterios de aceptación: [[criterios-aceptacion-gherkin]]
- Estimación y priorización: [[estimacion-y-priorizacion]]
