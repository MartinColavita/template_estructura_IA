---
id: redaccion-tickets-bugs-y-defectos
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Bugs y defectos
author: equipo
tags: [bugs, defectos, reproducir, esperado-obtenido, gravedad, evidencia]
last_updated: 2026-08-26
---

# Bugs y defectos

Guía para reportar bugs de forma que cualquiera pueda reproducirlos y arreglarlos. El estilo de casa del tablero suele concentrar todo el contenido del defecto en el campo **Pasos para reproducir**. Método agnóstico; los ejemplos concretos van rotulados **Ejemplo (genérico)**.

---

## Por qué esta guía

En el tablero real conviven dos clases de bug: los que escribe QA (con plantilla decente: Ambiente / Versión / Pasos / Esperado / Obtenido / Evidencia) y los que escribe cualquier otro rol (título con typo, "Ver adjunto", mezcla de ambientes, sin separar esperado de obtenido). Esta guía sube a todos al nivel de QA. El objetivo no es burocracia: es que el desarrollador reproduzca el defecto en el primer intento y no pierda medio día adivinando.

**Regla base del estilo de casa:** en un Bug la **Descripción casi no se usa**. TODO el detalle del defecto va en **Pasos para reproducir** (referencia interna `Microsoft.VSTS.TCM.ReproSteps`, HTML enriquecido). La extensión del navegador completa sola "Información del sistema" (`Microsoft.VSTS.TCM.SystemInfo`); no la toques a mano.

---

## Anatomía de un buen bug

### 1. Título

Formato de casa: **`Módulo - Contexto: síntoma concreto`**, sin typos, con el prefijo de módulo consistente.

- **Módulo**: el del flujo troncal donde aparece, o el servicio/pantalla si es backend.
- **Contexto**: la acción o estado puntual (qué se estaba haciendo).
- **Síntoma**: qué falla, observable, no la causa que suponés.

> Los siguientes son **Ejemplo (genérico)**:

| Mal | Bien |
|---|---|
| `Se dehabilita el botón No asignar el recurso` (typo, sin módulo, sin contexto) | `Asignación - Selección de recurso: el botón "No asignar el recurso" queda deshabilitado tras cancelar` |
| `No anda el listado` | `Listados - Solicitudes activas: la grilla queda vacía al filtrar por grupo <código>` |
| `Error clasificacion` | `Clasificación - Regla <código>: al confirmar la clasificación devuelve error 500` |

Reglas del título:
- Sin errores de tipeo (los revisa gente y quedan para siempre).
- Un solo síntoma por título (ver "un bug = un defecto").
- No metas el ambiente en el título salvo que el bug **solo** ocurra en uno; el ambiente va en el cuerpo.

### 2. Cuerpo (todo dentro de "Pasos para reproducir")

Estructura fija, en este orden. Poné los rótulos en negrita para que se lean rápido en el HTML de Azure.

```
Ambiente:            DESA | TEST | PREPROD | PROD
Versión frontend:    (etiqueta del frontend)
Versión backend:     (etiqueta del backend)
Fecha:               AAAA-MM-DD (cuándo se detectó)
Capa afectada:       Frontend | Backend (servicio) | Base de datos | Integración externa | Sistema legacy

Precondiciones:
- Rol/perfil del usuario.
- Estado de datos necesario (ej.: un registro en cierto estado con recurso asignado).
- Canal si importa.

Pasos:
1. ...
2. ...
3. ...

Resultado esperado:
- Qué debería pasar (una frase, comportamiento correcto).

Resultado obtenido:
- Qué pasa realmente (el defecto observable; incluí mensaje/código de error textual).

Por qué es un error (motivo / impacto):
- Por qué lo obtenido está mal (qué regla/expectativa rompe) y a quién/qué afecta. SIEMPRE.

Observaciones:
- Frecuencia (siempre / intermitente / 1 de N), solución alternativa si existe, alcance.

Evidencia:
- Capturas/video adjuntos como APOYO. El texto debe bastar sin abrir el adjunto.
```

#### Ambiente

Uno solo por bug (por ejemplo **DESA → TEST → PREPROD → PROD**). Si lo viste en dos ambientes, **no lo mezcles en el mismo reporte**: aclaralo en Observaciones ("también reproducido en TEST, misma versión") pero los pasos deben describir **un** ambiente. Si el comportamiento difiere entre ambientes, probablemente sean dos bugs o un problema de datos/config, no de código.

#### Versión

Siempre las dos, porque el bug puede estar en cualquier capa:
- **Versión frontend**: la etiqueta del front.
- **Versión backend**: la etiqueta del backend.

La versión sale del pie de pantalla / del "Acerca de" / de la etiqueta del sprint. Si no la sabés con certeza, marcala "(pendiente)" y no la inventes.

#### Pasos numerados y reproducibles

- Empezá desde un punto conocido (login, pantalla X), no desde "estando en el registro".
- Un paso = una acción. Nada de "hago todo el alta y guardo".
- Incluí los **datos usados como estructura, nunca reales** (ver PHI abajo): "busco una persona con categoría `<categoria>` e identificador `<identificador>`".
- Que un desarrollador que nunca vio el caso pueda seguirlos tal cual.

#### Resultado esperado vs Resultado obtenido — SEPARADOS SIEMPRE

Es el error más común de los bugs mal escritos: contar solo lo que pasó, o mezclar ambos en una frase. Tienen que ir en dos bloques distintos:

- **Esperado**: el comportamiento correcto según la spec/lógica de negocio.
- **Obtenido**: lo que realmente ocurre, con el texto exacto del error o el estado incorrecto.

Si no podés escribir el "esperado", quizás no es un bug sino una duda funcional: pasala a consulta, no a Bug.

#### Por qué es un error (motivo / impacto) — SIEMPRE

Después del esperado y el obtenido, agregá **por qué lo obtenido está mal y a quién/qué impacta**. No alcanza con describir el síntoma: hay que dejar claro qué regla o expectativa se rompe y qué consecuencia tiene en la operación (¿bloquea la operación?, ¿el usuario no puede completar el trabajo?, ¿la persona recibe un dato incorrecto?). Ese "por qué" es lo que permite **priorizar** el bug y entender su gravedad real.

- **No confundir con la causa técnica.** El "por qué es un error" es funcional (qué expectativa rompe y a quién afecta). La **hipótesis de causa técnica** (dónde estaría el defecto en el código/capa) es opcional y va en Observaciones, siempre marcada como hipótesis "(a confirmar)".
- Ejemplo: *"El botón de no-asignación no debería depender del domicilio del recurso (la no-asignación no requiere dirección); al bloquearse, el usuario no puede registrar la no-asignación y queda trabado en la asignación."*

> **Esta tríada se generaliza a cualquier ticket:** dejá siempre explícito **qué se espera**, **qué ocurre** y **por qué importa / a quién impacta**. En una Historia el "por qué" es el *para &lt;beneficio&gt;*; en una Tarea o Habilitador, la *motivación / qué desbloquea*.

#### Evidencia: apoyo, nunca sustituto

Adjuntá capturas o video, pero **el texto debe alcanzar para reproducir sin abrir el adjunto**. Prohibido el bug que dice solo "Ver adjunto". El adjunto se pierde, se comprime, o el revisor lo lee desde el celular. Enmascará PHI en las capturas (ver abajo).

---

## Gravedad vs Prioridad

Dos campos distintos que la gente confunde:

- **Gravedad** (`Microsoft.VSTS.Common.Severity`): cuánto daña el defecto — `1-Critical`, `2-High`, `3-Medium`, `4-Low`. Es una propiedad del bug.
- **Prioridad** (`Microsoft.VSTS.Common.Priority`, 1–4): qué tan pronto hay que atenderlo. Es una decisión de gestión.

Un defecto cosmético en una pantalla que casi no se usa puede ser Gravedad 4 y Prioridad 4. Una caída del flujo troncal en PROD es Gravedad 1 y Prioridad 1. Pero pueden divergir: un typo visible en la home de todos los usuarios puede ser Gravedad 4 y Prioridad 2. **El detalle de cómo asignar cada nivel está en [[estimacion-y-priorizacion]].**

Regla rápida: siempre completá **Gravedad**. Un bug sin gravedad no se puede triar.

---

## Reglas de oro del reporte

1. **Un bug = un defecto.** Si encontraste tres cosas mal, son tres bugs. Un reporte con varios defectos no se puede cerrar ni testear de forma limpia.
2. **Pasos que cualquiera pueda seguir.** Desde un punto de partida conocido, con datos como estructura.
3. **Separar esperado de obtenido, y agregar el porqué.** Siempre en bloques distintos: qué se espera, qué ocurre y **por qué es un error** (motivo/impacto).
4. **No mezclar ambientes.** Uno por reporte.
5. **Evidencia como apoyo, no como sustituto** del texto.
6. **Enmascarar PHI.** El producto maneja datos personales reales.
7. **Título sin typos y con prefijo de módulo consistente.**

---

## PHI: enmascarar datos personales reales

El producto maneja **datos reales de personas** (nombres, documentos, teléfonos, datos sensibles, identificadores). En el reporte y en las capturas:

- Nunca pegues valores reales. Usá marcadores: `<persona>`, `<documento>`, `<telefono>`, `<dato-sensible>`, `<identificador>`, `<direccion>`.
- Describí la **estructura** del dato, no el dato: "identificador de N dígitos con categoría `<categoria>`" en vez del número.
- En capturas, tapá/difuminá nombre, documento, teléfono y cualquier dato sensible antes de adjuntar.
- Si para reproducir hace falta un caso puntual, referenciá el **ID interno del registro/solicitud**, no los datos de la persona.

---

## Dónde vive el defecto: señalar la capa

El sistema tiene varias capas y el defecto puede estar en cualquiera. Señalar la capa correcta ahorra rebotes entre equipos.

| Capa | Qué es | Señales de que el bug es de acá |
|---|---|---|
| **Frontend** | La aplicación de front, detrás del inicio de sesión | Falla visual, validación de formulario, estado de botón, render de grilla, ruteo, algo que se arregla en el front |
| **Backend — servicio** | Los servicios de back con su lógica y datos propios | Error en la llamada al endpoint, header mal armado, 401/403, respuesta con error que nace en el servicio |
| **Base de datos** | El almacenamiento del backend | El dato viene mal/viejo, un cálculo persistido es incorrecto, una consulta devuelve otra cosa |
| **Integración externa** | Un sistema de terceros consumido por el backend | El dato que aporta la integración llega mal o no llega; el fallo coincide con la indisponibilidad del externo |
| **Sistema legacy (en migración)** | El monolito que aún concentra parte de la lógica mientras dura la migración | El comportamiento defectuoso reproduce el del legacy y no depende del código migrado |

**Cómo señalar la capa cuando la causa está fuera del código propio:** en Observaciones aclaralo explícito, porque **no se arregla desde el servicio propio**. Ejemplo de nota:

> Observaciones: El dato incorrecto no lo genera el servicio `<módulo>`, llega desde `<integración / legacy>`. El defecto no es del servicio sino de esa capa → escalar al equipo correspondiente. (a confirmar la capa exacta con el análisis de logs.)

---

## Antes de crear el bug — mini checklist

- [ ] Título `Módulo - Contexto: síntoma`, sin typos.
- [ ] Ambiente único indicado.
- [ ] Versión frontend y Versión backend.
- [ ] Precondiciones (rol, estado de datos, canal).
- [ ] Pasos numerados desde un punto conocido.
- [ ] Resultado esperado y Resultado obtenido, separados.
- [ ] **Por qué es un error** (motivo/impacto) explícito.
- [ ] Gravedad asignada (y Prioridad si la sabés).
- [ ] PHI enmascarado en texto y capturas.
- [ ] Evidencia adjunta como apoyo, no como sustituto.
- [ ] Capa señalada (front / servicio / base de datos / integración / legacy).

---

## Ver también

- Gravedad y prioridad en detalle: [[estimacion-y-priorizacion]]
- Antipatrones (cómo NO escribir): [[antipatrones]]
- Definición de Preparado / Terminado: [[definicion-preparado-terminado]]
- Dominio del proyecto: [[contexto-proyecto]]
