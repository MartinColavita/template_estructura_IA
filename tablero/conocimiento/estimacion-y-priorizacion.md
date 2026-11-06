---
id: redaccion-tickets-estimacion-y-priorizacion
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Estimación y priorización
author: equipo
tags: [estimacion, story-points, tokens, complejidad, gravedad, prioridad, moscow]
last_updated: 2026-08-26
---

# Estimación y priorización

Cómo estimar el esfuerzo (Puntos de historia) y cómo ordenar el trabajo (Gravedad, Prioridad, MoSCoW), con tablas de referencia concretas para no discutir cada vez. Método agnóstico; los ejemplos van rotulados **Ejemplo (genérico)**.

---

## 1. Puntos de historia (Story Points)

**Acá el desarrollo lo hace la IA**, así que los Puntos de historia miden **cuánto le cuesta al sistema (la IA) entregar el ítem**: la **complejidad a nivel sistema** (capas, integraciones, reglas) + el **consumo de tokens** para resolverlo e investigar lo relacionado. **No son horas** ni salen de un consenso humano.

Por qué así: el token es la señal más directa del costo real de resolver, y la complejidad a nivel sistema completa el cuadro. El número lo **calcula la IA** (lo detalla la skill [[estimar-story-points]]); el humano puede ajustarlo.

### Escala tipo Fibonacci

Se usa una escala creciente **1, 2, 3, 5, 8, 13, 20** (Fibonacci). Los saltos crecen a propósito: cuanto más grande el ítem, más difícil es ser preciso, así que se ofrecen menos opciones.

| Puntos | Qué significa | Regla práctica |
|---|---|---|
| **1** | Trivial, entendido del todo, sin incertidumbre. | Se hace casi sin pensarlo. |
| **2** | Chico, alguna consideración menor. | Claro pero con un par de pasos. |
| **3** | Mediano-chico, algo de lógica o varios archivos. | Cabe cómodo en un día de trabajo. |
| **5** | Mediano, varias piezas o una integración simple. | Requiere diseño mínimo. |
| **8** | Grande, varias capas o incertidumbre real. | Candidato a partirse en subtareas. |
| **13** | Muy grande, integración/feature con incógnitas. | **Casi siempre conviene partir.** |
| **20** | Épica encubierta; demasiada incertidumbre. | **No entra así**: se descompone. |

> Regla de casa: si un ítem da **13 o más**, se trata como señal de que hay que **partirlo**, no de que sea heroico.

### Tabla de referencia con ejemplos

> **Ejemplo (genérico).** Cómo se ve la escala con un backend de servicios y una aplicación de front:

| Puntos | Ejemplo típico |
|---|---|
| **1** | Cambio trivial de UI: renombrar una etiqueta, corregir un texto, mostrar/ocultar un botón según un indicador que ya existe. |
| **2** | Ajuste de validación simple en un formulario; agregar una columna ya disponible a un listado. |
| **3** | Bug de lógica acotado en un endpoint: el servicio arma mal un filtro o no mapea un caso; corrección con su test. |
| **5** | Nuevo caso en un endpoint existente (controller + service + DTO + test) siguiendo el patrón canónico. |
| **8** | Nueva sublista con filtros completa: endpoint nuevo, DTOs, filtros combinables, con sus tests y documentación de API. |
| **13** | Feature con integración externa que toca frontend + servicio + coordinación con otro sistema. Se parte en historias/tareas más chicas. |

### Cómo se fija el puntaje (sin Planning Poker)

Como **desarrolla la IA**, no hay votación ni Planning Poker: el número lo **calcula la IA** a partir de la complejidad a nivel sistema y el consumo de tokens (resolver + investigar lo relacionado), y lo expresa en la escala Fibonacci de arriba. El método completo está en [[estimar-story-points]].

1. La IA evalúa el ítem: complejidad, integraciones, reglas `[RN-…]`, relacionadas a investigar, incertidumbre y si hay un `gold` parecido para imitar.
2. Si ya resolvió o investigó, suma el **token real** (resolver + navegar) como señal principal.
3. Propone un número con 1-2 líneas de justificación. **El humano puede ajustarlo.**
4. El número (y los tokens, si hubo) quedan en la fila del historial para **calibrar** las próximas estimaciones.

> Los umbrales "tantos tokens ≈ tanta banda" no se inventan: se fijan con datos reales del historial. Igual vale como control de "listo para desarrollar": si la IA no puede evaluar el alcance ni los criterios, la historia no estaba Preparada (ver [[definicion-preparado-terminado]]).

---

## 2. Gravedad y Prioridad de bugs

Son **dos cosas distintas** y se completan por separado en Azure:

- **Gravedad (Severity) = impacto.** Cuánto daño hace el defecto cuando ocurre.
- **Prioridad (Priority) = urgencia de atención.** Qué tan pronto lo agarramos, dado el impacto **y** el contexto (frecuencia, ambiente, si hay solución alternativa, cuántos usuarios afecta).

Un bug puede ser **Gravedad alta pero Prioridad media** (rompe fuerte pero pasa poquísimo y hay solución alternativa) o **Gravedad media pero Prioridad alta** (molesto pero le pega a todos los usuarios todo el día).

> **Valores de los campos de Azure DevOps**: los campos de tipo desplegable (Gravedad/Severity, Prioridad/Priority) muestran su valor **en inglés** y no se pueden traducir en la herramienta. El valor se selecciona tal cual aparece en Azure; el texto entre paréntesis es solo ayuda en español.

### Escala de Gravedad

La pregunta rectora es la del impacto en la operación del negocio; en un dominio operativo es siempre: **¿esto bloquea o pone en riesgo la operación?** Y, en segundo plano: **¿hay solución alternativa?**

El valor se selecciona tal cual aparece en el desplegable de Azure (en inglés); el texto entre paréntesis es solo ayuda en español.

| Gravedad (campo Severity) | Criterio | Ejemplos |
|---|---|---|
| **1 - Critical** (crítica) | Bloquea el flujo troncal del negocio; hay riesgo operativo o para las personas; sin solución alternativa. | No se puede completar la operación principal; el usuario no puede registrar el trabajo; caída de un paso que frena todo el flujo. |
| **2 - High** (alta) | Afecta una función importante del flujo pero hay solución alternativa incómoda, o afecta a un segmento concreto (una sede, un canal). | Un canal no ingresa trabajo pero otro sí; un listado clave no filtra bien y obliga a buscar a mano. |
| **3 - Medium** (media) | Molesto, con solución alternativa clara; no frena el flujo. Datos secundarios mal mostrados. | Un listado ordena mal; un botón se deshabilita cuando no debería pero hay otra vía; texto/estado que confunde sin bloquear. |
| **4 - Low** (baja) | Cosmético o de conveniencia; sin impacto operativo. | Typo en una etiqueta, desalineación visual, tooltip incorrecto. |

> Nota de dominio: en un producto **crítico para la operación**, un defecto que impide gestionar un caso escala rápido a **1 - Critical** aunque técnicamente sea chico. El impacto se mide por la operación, no por el tamaño del código.

### Cómo se combinan Gravedad y Prioridad

| Situación | Gravedad (campo Severity) | Prioridad |
|---|---|---|
| Rompe el flujo troncal en PROD, sin solución alternativa | 1 - Critical (crítica) | 1 |
| Rompe fuerte pero solo en un caso rarísimo y hay solución alternativa | 1 - Critical / 2 - High | 3 |
| Molesto pero le pasa a todos los usuarios todo el día en PROD | 3 - Medium (media) | 1 / 2 |
| Cosmético en un ambiente de prueba | 4 - Low (baja) | 4 |

Escala de **Prioridad 1-4** (1 = atender ya, 4 = cuando haya hueco; valor numérico, sin glosa). Al fijarla, pesar: **ambiente** (PROD pesa más que DESA), **frecuencia**, **cantidad de usuarios afectados** y **existencia de solución alternativa**.

---

## 3. Priorizar el backlog

### Valor vs esfuerzo

Ordená por **valor de negocio contra esfuerzo (Puntos de historia)**. Lo que primero entra es lo de **alto valor y bajo esfuerzo** ("fruta madura"); lo de bajo valor y alto esfuerzo va al fondo.

| | Esfuerzo bajo | Esfuerzo alto |
|---|---|---|
| **Valor alto** | Hacer YA (fruta madura) | Planificar y partir |
| **Valor bajo** | Rellenar huecos | Evitar / posponer |

El "valor" pondera fuerte lo que toca el flujo troncal del negocio y los compromisos con fecha (releases, hitos de la migración).

### MoSCoW (en español)

Técnica para clasificar el alcance por obligatoriedad. Las cuatro categorías:

- **Imprescindible** (*Must have*): sin esto, el entregable/sprint no sirve.
- **Debería** (*Should have*): importante, pero el entregable sobrevive sin ello un tiempo; entra si hay margen.
- **Podría** (*Could have*): deseable, bajo costo de omitir; primero en caer si aprieta la fecha.
- **No por ahora** (*Won't have this time*): explícitamente fuera de este ciclo; queda registrado para no volver a discutirlo.

> Buen uso de "No por ahora": deja por escrito lo que **se decidió NO hacer**, que es tan valioso como la lista de lo que sí.

---

## Resumen operativo

- **Puntos de historia** = costo para la IA de entregar el ítem (complejidad a nivel sistema + tokens de resolver/investigar), escala Fibonacci; 13+ ⇒ partir. Lo calcula la IA (no hay Planning Poker: desarrolla la IA); el humano puede ajustar.
- **Gravedad** = impacto (¿bloquea el flujo? ¿hay solución alternativa?). **Prioridad** = urgencia de atención (impacto + frecuencia + ambiente + cantidad de afectados). Son campos distintos.
- **Backlog** = valor vs esfuerzo, y encima **MoSCoW** (Imprescindible / Debería / Podría / No por ahora) para acordar el alcance.

---

## Ver también

- Definición de Preparado / Terminado: [[definicion-preparado-terminado]]
- Bugs y defectos (dónde caen Gravedad/Prioridad): [[bugs-y-defectos]]
- Historias de usuario e INVEST: [[historias-de-usuario]]
