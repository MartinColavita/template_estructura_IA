---
id: redaccion-tickets-criterios-aceptacion-gherkin
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Criterios de aceptación en Gherkin (español)
author: equipo
tags: [criterios-aceptacion, gherkin, dado-cuando-entonces, qa, testeable]
last_updated: 2026-08-26
---

# Criterios de aceptación en Gherkin (español)

Guía para escribir el campo **Criterios de aceptación** de una historia: cuándo usar Gherkin en español, cuándo una lista de reglas, y cómo redactarlos para que sean verificables y sin PHI. Método agnóstico; los ejemplos concretos van rotulados **Ejemplo (genérico)**.

---

## 1. Qué son y por qué son el corazón del ticket

Los **Criterios de aceptación** son la lista de condiciones que el trabajo debe cumplir para considerarse **terminado**. Son el contrato entre quien pide (analista funcional / producto), quien construye (desarrollo) y quien valida (QA):

- Definen **cuándo la historia está "hecha"** (base del *Definition of Done* específico de esa historia).
- Son la **fuente de los casos de prueba**: QA arma sus pruebas leyendo estos criterios. Si están vacíos, QA prueba a ojo.
- Cierran el alcance: lo que **no** está en los criterios, **no** es parte de la historia (evita el "yo pensé que también incluía...").

> **Criterios vs. Casos de uso.** Los **Criterios de aceptación** (este campo) son el **pass/fail** en Gherkin. Los **Casos de uso** (Bloque 4 de la Historia, dentro de la Descripción) son el **inventario de flujos** que Testing debe cubrir — delimitan el **alcance** de las pruebas. No se duplican: **cada Caso de uso se cubre con ≥1 escenario Gherkin** de acá. Ver [[historias-de-usuario]] y [[plantillas/historia-de-usuario]].

> **El problema real y recurrente:** en los tableros de Azure el campo **Criterios de aceptación** (`Microsoft.VSTS.Common.AcceptanceCriteria`) aparece **VACÍO** en la mayoría de las historias. Una historia sin criterios no se puede validar, no se puede estimar bien y termina "cerrada" por cansancio, no por cumplimiento. **Llenar bien este campo es el mayor salto de calidad que puede dar un ticket.**

Regla mínima: **ninguna historia de usuario se manda a desarrollo con este campo vacío.** Si de verdad no hay nada que verificar, probablemente no es una historia (revisá si es una **Tarea** técnica — ver [[historias-de-usuario]]).

---

## 2. Dos formatos: cuándo usar cada uno

### (a) Gherkin en español — comportamiento con contexto

Formato **Escenario / Dado / Cuando / Entonces**. Usalo cuando el comportamiento depende de un **estado previo**, una **acción del usuario** y un **resultado observable**, o cuando hay varios caminos (feliz, alternativo, error).

**Ideal para:** flujos de negocio — alertas, asignaciones, cambios de estado, validaciones de formulario, permisos por rol.

### (b) Lista de reglas / checklist — condiciones simples

Una lista de afirmaciones verificables, sin estructura Dado/Cuando/Entonces. Usala cuando son **reglas planas** sin flujo: presencia de un campo, formato de un dato, valores de una lista, textos de etiqueta.

**Ideal para:** "el combo debe listar las opciones A, B, C" o "el campo Teléfono acepta solo dígitos".

> **Se pueden combinar:** una historia puede tener 2–3 escenarios Gherkin para el flujo principal **y** una lista de reglas para las validaciones de detalle. Usá el formato que hace cada condición más clara, no uno por dogma.

---

## 3. Palabras clave de Gherkin en español

**Siempre en español. NUNCA se escribe Given / When / Then / Scenario / Feature / And / But.** Equivalencias y significado:

| Español (usar) | Inglés (NO usar) | Para qué sirve |
|---|---|---|
| **Característica** | Feature | Título/tema del conjunto de escenarios (opcional dentro del campo). |
| **Antecedentes** | Background | Pasos comunes que se repiten en **todos** los escenarios (contexto compartido). |
| **Escenario** | Scenario | Un caso concreto de comportamiento. |
| **Esquema del escenario** | Scenario Outline | Un escenario parametrizado que se corre con varias filas de datos. |
| **Ejemplos** | Examples | La tabla de datos que alimenta al Esquema del escenario. |
| **Dado** | Given | El contexto / estado inicial (lo que ya pasó). |
| **Cuando** | When | La acción que dispara el comportamiento. |
| **Entonces** | Then | El resultado observable esperado. |
| **Y** | And | Encadena un paso más del mismo tipo que el anterior. |
| **Pero** | But | Encadena una condición en contraste (variante de "Y"). |

Estructura mental: **Dado** (contexto) → **Cuando** (acción) → **Entonces** (resultado). "Y"/"Pero" suman pasos a cualquiera de los tres.

---

## 4. Reglas de un buen criterio

1. **Uno por comportamiento observable.** Cada escenario/regla verifica **una** cosa. Si tenés que usar "y también" en el resultado, probablemente son dos criterios.
2. **Describe el QUÉ, no el CÓMO.** Nada de nombres de tablas, endpoints, parámetros internos, clases o stored procedures. El criterio dice qué ve/logra el usuario, no cómo lo resuelve el servicio.
3. **Verificable / testeable.** Un tercero (QA) tiene que poder decir "sí cumple / no cumple" sin interpretar. Evitá adjetivos sueltos ("rápido", "amigable", "correcto").
4. **Cubrí todos los caminos**, no solo el feliz:
   - **Camino feliz** (todo sale bien).
   - **Caminos alternativos** (variantes válidas).
   - **Errores y excepciones** (qué pasa cuando falla).
   - **Validaciones de datos** (formatos, obligatorios, rangos).
   - **Permisos por rol** (qué puede/no puede hacer cada perfil).
5. **Sin PHI.** Jamás datos personales reales. Usá marcadores: `<persona>`, `<documento>`, `<telefono>`, `<dato-sensible>`, `<identificador>`, `<recurso>`. Describí la **estructura** del dato, no el dato.
6. **Lenguaje del negocio.** Usá los términos del dominio del proyecto tal cual (los define el Cerebro Digital, ver [[contexto-proyecto]]).

---

## 5. Ejemplos completos (Gherkin español)

> Los siguientes son **Ejemplo (genérico)**: ilustran la técnica. En tu proyecto, cambiá los términos por los de tu dominio.

### Ejemplo 1 — Alerta de solicitud recurrente en el alta

```gherkin
Característica: Alerta de solicitud recurrente en el alta

  Antecedentes:
    Dado que el operador está autenticado con un rol operativo
    Y tiene abierto el formulario de alta

  Escenario: Se avisa al operador cuando la persona ya tuvo una solicitud reciente
    Dado que ingreso el identificador de una <persona> con una solicitud
      registrada en las últimas 24 horas
    Cuando confirmo la identificación de la persona
    Entonces el sistema muestra una alerta visible de "solicitud recurrente"
    Y la alerta indica la cantidad de solicitudes previas en el período
    Y el operador debe reconocer la alerta antes de continuar

  Escenario: No se muestra alerta cuando no hay solicitudes recientes
    Dado que ingreso el identificador de una <persona> sin solicitudes
      en las últimas 24 horas
    Cuando confirmo la identificación de la persona
    Entonces el formulario continúa sin mostrar la alerta de recurrencia
```

### Ejemplo 2 — Identificación de la persona

```gherkin
Característica: Identificación de la persona en el alta

  Escenario: Alta de una persona válida por identificador
    Dado que el operador está en el formulario de alta
    Cuando ingresa un <identificador> con formato válido y presiona Buscar
    Entonces el sistema recupera y muestra los datos de la <persona> asociados
    Y habilita el resto del formulario para continuar

  Escenario: Identificador inexistente
    Dado que el operador está en el formulario de alta
    Cuando ingresa un <identificador> que no corresponde a ninguna persona
    Entonces el sistema muestra el mensaje "Persona no encontrada"
    Y no habilita la continuación
    Pero permite reintentar la búsqueda con otro identificador

  Escenario: Campo identificador vacío
    Dado que el operador está en el formulario de alta
    Cuando presiona Buscar sin ingresar el identificador
    Entonces el sistema muestra la validación "El campo identificador es obligatorio"
    Y mantiene el foco en el campo identificador
```

### Ejemplo 3 — Cambio de estado con transición controlada

```gherkin
Característica: Cambio de estado de la solicitud

  Antecedentes:
    Dado que existe una solicitud en un estado previo compatible
    Y el operador tiene permiso para gestionar estados de solicitudes

  Escenario: Registrar el avance de la solicitud
    Cuando el operador registra el avance del <recurso> en terreno
    Entonces el estado de la solicitud cambia a Estado2 (avanzada)
    Y se registra la fecha y hora del avance
    Y el cambio queda reflejado en el seguimiento de la solicitud

  Escenario: No se permite el avance desde un estado incompatible
    Dado que la solicitud está en un estado final
    Cuando el operador intenta registrar el avance
    Entonces el sistema no permite el cambio de estado
    Y muestra un mensaje indicando que el estado actual no admite esa transición
```

> Atención: la transición exacta desde la que se habilita un estado debe validarse contra la spec del proyecto; si no la conocés con certeza, marcala "(pendiente)".

### Ejemplo 4 — Validación de un campo que no acepta un carácter

```gherkin
Característica: Validación de caracteres en el campo Domicilio

  Escenario: Rechazo de apóstrofe en el domicilio
    Dado que el operador está cargando el domicilio en el formulario
    Cuando ingresa un texto que contiene un apóstrofe (por ejemplo, "O'Higgins")
    Y confirma el campo
    Entonces el sistema muestra la validación "El carácter ' no está permitido"
    Y no guarda el valor hasta que se corrija
    Y el resto del formulario permanece sin cambios

  Escenario: Domicilio válido sin caracteres prohibidos
    Dado que el operador está cargando el domicilio en el formulario
    Cuando ingresa un texto sin caracteres prohibidos
    Entonces el sistema acepta el valor y permite continuar
```

### Ejemplo 5 — Permiso por rol

Un mismo comportamiento puede estar habilitado o no según el **rol**. Este escenario ejemplifica el criterio de **permisos por rol** que pide la regla 4: no basta con probar que la acción funciona, hay que probar que un rol sin permiso **no** puede ejecutarla.

```gherkin
Escenario: Un operador sin permiso de gestión de estados no puede registrar el avance
  Dado un operador con rol de solo consulta
  Y una solicitud en un estado intermedio
  Cuando intenta registrar el avance a "Estado2"
  Entonces el sistema no habilita la acción
  Y muestra un mensaje indicando que no tiene permiso
```

---

## 6. Esquema del escenario (con tabla de Ejemplos)

Usá **Esquema del escenario** cuando el **mismo** comportamiento se repite con distintos datos. Los parámetros van entre `< >` y se completan con la tabla **Ejemplos**.

```gherkin
Característica: Transiciones válidas de estado de la solicitud

  Esquema del escenario: El sistema permite o bloquea el cambio de estado según el origen
    Dado que una solicitud está en estado <estado_actual>
    Cuando el operador intenta cambiarlo a <estado_destino>
    Entonces el sistema responde con "<resultado>"

    Ejemplos:
      | estado_actual | estado_destino | resultado  |
      | Estado1       | Estado2        | permitido  |
      | Estado2       | cierre         | permitido  |
      | cierre        | Estado2        | bloqueado  |
      | Estado1       | cierre         | bloqueado  |
```

> El marcador `< >` cumple doble función acá: parametriza el Esquema **y** sirve para no exponer PHI (por ejemplo `<persona>`, `<identificador>` como columnas de la tabla de Ejemplos).

---

## 6.b. Cómo va al campo de Azure (HTML) — que no se vea feo

Los bloques ```` ```gherkin ```` de arriba son para **leer**. El campo **Criterios de aceptación** de Azure (`Microsoft.VSTS.Common.AcceptanceCriteria`) es **HTML**: si pegás el Gherkin crudo (o con `<br>` pero sin negritas ni sangría), queda un **muro de renglones iguales** — la causa #1 de criterios "feos". Al escribir el campo, **convertí** el Gherkin a HTML con esta regla:

- **Negrita en TODAS las keywords**, no solo en `Escenario:` — `Característica`, `Antecedentes`, `Escenario`, `Esquema del escenario`, `Ejemplos`, `Dado`, `Cuando`, `Entonces`, `Y`, `Pero`.
- **Un `<p>` por escenario** (los separa visualmente); **pasos sangrados** con `&nbsp;&nbsp;`; los `[RN-…]` en `<i>` al final del renglón del `Escenario`.
- Nada de fences ```` ``` ````, markdown ni `<pre>` de código.

```html
<p><b>Escenario:</b> Inicio de sesión exitoso <i>[RN-TEMA-01]</i><br>
&nbsp;&nbsp;<b>Dado</b> que el operador está en el formulario de alta<br>
&nbsp;&nbsp;<b>Cuando</b> ingresa un &lt;identificador&gt; con formato válido y presiona Buscar<br>
&nbsp;&nbsp;<b>Entonces</b> el sistema recupera y muestra los datos del &lt;persona&gt;<br>
&nbsp;&nbsp;<b>Y</b> habilita el resto del formulario para continuar</p>
```

Esqueleto completo del campo (con `Característica`/`Antecedentes`): [[checklists/mapa-campos-azure]] §"Esqueleto HTML".

## 7. Errores comunes al escribir criterios

| Error | Ejemplo malo | Cómo se arregla |
|---|---|---|
| **Vago / no medible** | "El sistema debe responder rápido." | "El listado se muestra en menos de 3 segundos con hasta 200 filas." |
| **Describe el CÓMO** | "El servicio llama al parámetro X y guarda en la tabla de registros." | "Al confirmar, la solicitud queda registrada y visible en el listado del operador." |
| **Mezcla varios comportamientos** | "Cuando busco a la persona se muestran sus datos y también se valida el teléfono y se habilita la asignación." | Separar en tres escenarios/criterios independientes. |
| **Solo camino feliz** | Únicamente "la persona válida se identifica". | Agregar identificador inexistente, campo vacío, sin permisos. |
| **No verificable / subjetivo** | "La pantalla tiene que ser intuitiva." | "Todos los campos obligatorios están marcados y el botón Guardar se deshabilita hasta completarlos." |
| **Con PHI** | "Dada la persona «nombre y documento reales incrustados»..." | "Dada una `<persona>` con `<documento>` válido..." |
| **Inglés colado** | "Scenario: happy path del login." | "Escenario: inicio de sesión exitoso." |
| **Repite el título de la historia** | Criterio = "Que funcione el cambio de estado." | Escribir las condiciones observables concretas. |

---

## 8. Criterios verificables por máquina (modelo asistido por IA)

En este flujo **la IA programa la funcionalidad** y el desarrollador hace sobre
todo **code review** contra los criterios. Por eso los criterios de aceptación
cumplen **tres roles a la vez**:

1. **Especificación**: la IA que genera el código los lee como el **contrato** de
   qué construir.
2. **Verificación**: la misma IA puede **auto-validar** su código contra ellos.
3. **Revisión**: el desarrollador rastrea cada implementación por su `[RN-…]`.

Para que un criterio sea **verificable por máquina** (no solo por una persona con
sentido común), reforzá estas reglas al redactarlo:

| Regla | Sí | No |
|---|---|---|
| **Verbos verificables** | "el sistema **rechaza** la reserva" | "el sistema **maneja adecuadamente** la reserva" |
| **Estados y datos explícitos** | "una reserva en estado **Confirmada**", "**código 02**" | "una reserva **ya tomada**", "un **código válido**" |
| **Condiciones medibles** | "reservas con **fecha ≥ a la actual**" | "fechas **próximas**" |
| **Un comportamiento por escenario** | si hay dos resultados, son **dos** escenarios | un escenario que verifica varias cosas a la vez |
| **`[RN-…]` por escenario** | cada escenario referenciable lleva su regla | criterios sueltos sin regla que los respalde |

> La `[RN-…]` en cada escenario le permite al reviewer rastrear **regla por regla**
> qué quedó implementado, y a la IA verificar contra el requisito exacto.

**La cadena de calidad:**

```
Doc con "## Derivación a backlog" cerrado (Cerebro Digital) -> Historia con Gherkin preciso -> código generado
  -> auto-verificación contra los criterios -> code review por [RN-…]
```

> El eslabón más crítico es **el documento**. Con personas programando, un doc
> mediocre lo salvaba el sentido común del dev; con la IA programando,
> **entra-basura = sale-basura**. La disciplina del bloque **`## Derivación a
> backlog` enumerado y cerrado, sin `⚠` pendientes** (solo eso baja al backlog)
> es el control de calidad de toda la cadena.

---

## Ver también

- Estructura de la historia y cuándo algo es Tarea y no Historia: [[historias-de-usuario]]
- Definición de Preparado / Terminado: [[definicion-preparado-terminado]]
- Antipatrones: [[antipatrones]]
- Dominio del proyecto: [[contexto-proyecto]]
