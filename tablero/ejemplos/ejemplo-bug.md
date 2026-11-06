---
id: ejemplo-bug
tipo: ejemplo
estado: F-Draft
modulo: integracion-azure-devops
title: "Ejemplo — Bug (pobre → profesional)"
author: equipo
tags: [azure-devops, ejemplo, bug, defecto, antes-despues, qa]
last_updated: 2026-08-26
---

# Ejemplo — Bug (pobre → profesional)

Muestra cómo transformar un Bug mal escrito ("Ver adjunto", con typo y mezcla de ambientes) en un reporte que un desarrollador puede reproducir en el primer intento. Es un caso genérico; el recuadro final "Ejemplo (genérico)" refuerza el mismo patrón con otra variante.

Relacionados: [[bug]] · [[checklist-bug]] · [[mapa-campos-azure]]

---

## Cómo usar este ejemplo

Pegá tu bug pobre junto con el conocimiento del toolkit y pedí que lo reescriba con el patrón de abajo. Este archivo es la referencia de "qué bien se ve el resultado". La plantilla vacía está en [[bug]] y el checklist en [[checklist-bug]].

Recordá: en un Bug la **Descripción casi no se usa**; TODO va en el campo **Pasos para reproducir** (`Microsoft.VSTS.TCM.ReproSteps`, HTML).

---

## ANTES (tal cual llegó — pobre)

> **Título:** `Se dehabilita el boton Cancelar`
>
> **Pasos para reproducir:**
> Ver adjunto. Cuando el usuario entra al registro y quiere cancelar el boton aparece gris y no lo deja seguir, en testing pasaba a veces y en produccion tambien lo vi el otro dia con una persona, parece que es cuando el registro no tiene algo cargado. Adjunto captura.
>
> **Gravedad:** (vacío) · **Prioridad:** (vacío) · **Etiquetas:** (vacío)

---

## Qué le falta (diagnóstico)

| Problema | Por qué importa |
|---|---|
| **Título con typo** ("dehabilita") y sin módulo/contexto | Queda para siempre en el tablero; no se entiende dónde ni cuándo pasa. |
| **Pasos = "Ver adjunto"** | El adjunto se pierde/comprime; nadie puede reproducir sin él. |
| **Mezcla Testing y Producción** en el mismo reporte | Un bug = un ambiente; si difiere entre ambientes puede ser otro problema (datos/config). |
| **Flujo de conciencia**, sin pasos numerados | No hay punto de partida conocido ni secuencia repetible. |
| **No separa Resultado esperado de Resultado obtenido** | No se sabe cuál es el comportamiento correcto ni cuándo está "arreglado". |
| **Sin Gravedad ni Prioridad** | No se puede triar. |
| **Causa a medias** ("cuando el registro no tiene algo cargado") | Hay una pista real, pero sin precisar qué campo. |
| **Menciona "una persona" con datos** (riesgo PHI) | El sistema maneja datos personales reales: hay que enmascarar. |

---

## DESPUÉS (profesional — listo para pegar en Azure DevOps)

### Título
```
Formulario del registro - Cancelación: el botón "Cancelar" queda deshabilitado cuando el registro no tiene dirección cargada
```

### Pasos para reproducir
*(todo el cuerpo va en este campo — `Microsoft.VSTS.TCM.ReproSteps`)*

**Ambiente:** TEST
**Versión Frontend:** <versión> — **(pendiente)** confirmar la versión exacta del sprint
**Versión Backend:** <versión> — **(pendiente)** confirmar
**Fecha de detección:** <AAAA-MM-DD>
**Capa afectada:** Frontend (la aplicación de front) — validación/estado del botón en el formulario del registro. Ver "Observaciones" para el origen del dato.

**Precondiciones:**
- Usuario logueado con perfil de operador.
- Un registro en un estado que habilita la cancelación (ej.: en estado `<X>`).
- Un registro/recurso candidato **sin dirección/domicilio cargado** en su ficha (esta es la condición que dispara el defecto).
- Datos usados solo como estructura, nunca reales: persona `<persona>`, identificador `<identificador>`, recurso `<recurso>`, domicilio `<direccion>`.

**Pasos:**
1. Iniciar sesión en el sistema (TEST) y abrir el registro a cancelar.
2. Ir a la sección de **selección/asignación de recurso** del formulario del registro.
3. Seleccionar un recurso que **no tenga dirección cargada**.
4. Intentar usar la opción **"Cancelar"** (el flujo de cancelación).

**Resultado esperado:**
- El botón **"Cancelar"** debe estar **habilitado** independientemente de si el recurso tiene o no dirección cargada, porque cancelar no requiere domicilio. El usuario debe poder registrar la cancelación y continuar el flujo.

**Resultado obtenido:**
- El botón **"Cancelar"** aparece **deshabilitado (gris)** y no permite continuar cuando el recurso seleccionado no tiene dirección cargada. El usuario queda bloqueado en ese punto.

**Por qué es un error (motivo / impacto):**
- La opción de **cancelar no requiere domicilio**, así que la habilitación del botón no debería depender de la dirección del recurso. Al bloquearse, el usuario **no puede registrar la cancelación** y queda trabado; impacta la operación diaria.

**Observaciones:**
- **Frecuencia:** consistente (siempre que el recurso no tiene dirección cargada). Con recursos que sí tienen dirección, el botón se habilita normalmente.
- **Alcance:** afecta el flujo de cancelación; no bloquea el flujo normal.
- **Hipótesis de causa (a validar):** la habilitación del botón parece estar atada por error a la existencia de dirección del recurso; esa condición aplicaría a otro flujo, no a la cancelación. **(pendiente)** a confirmar por el equipo si la validación vive en el front (estado del botón) o si el estado llega del backend.
- **Reproducido también en:** se observó un comportamiento similar en PROD (fecha `<AAAA-MM-DD>`), misma condición. **(pendiente)** no se mezcla en estos pasos: si se confirma en PROD con otra versión, abrir/enlazar reporte aparte por ambiente.

**Evidencia:**
- Captura del formulario con el botón deshabilitado (adjunta como apoyo). El texto de arriba alcanza para reproducir sin abrir el adjunto.
- **(pendiente / PHI):** en la captura tapar nombre, documento, identificador, teléfono y domicilio antes de adjuntar.

### Gravedad

> **Nota sobre los desplegables de Azure:** el valor se selecciona tal cual aparece en Azure DevOps (en inglés, no se puede traducir en la herramienta); el texto entre paréntesis es solo ayuda en español.

```
2 - High (alta)
```
*Justificación:* bloquea un flujo operativo (el usuario no puede registrar la cancelación) y no hay solución alternativa clara; no llega a crítica (Critical) porque no cae el sistema ni afecta a todos los casos, solo a los que tienen recurso sin dirección.

### Prioridad
```
2
```
*Justificación:* impacta la operación diaria y ya se observó en PROD, pero existe margen (afecta un subconjunto de casos). Sube a 1 si se confirma que ocurre de forma masiva en PROD.

### Etiquetas
```
cancelacion
```
Una sola etiqueta: el tema. La versión (si hace falta) ya quedó registrada como **campo de contenido** en Pasos para reproducir (§ arriba), no como tag.

---

## Por qué el "DESPUÉS" está bien (checklist)

- [x] Título `Módulo - Contexto: síntoma`, sin typos, con la condición que dispara el bug.
- [x] Un solo ambiente en los pasos (TEST); el dato de PROD queda en Observaciones, sin mezclar.
- [x] Versión frontend y backend (marcadas (pendiente) para confirmar, no inventadas).
- [x] Precondiciones con rol, estado del registro y la condición clave (recurso sin dirección).
- [x] Pasos numerados desde un punto conocido (login).
- [x] Resultado esperado y obtenido, separados.
- [x] **Por qué es un error** (motivo/impacto) explícito, separado de la causa técnica.
- [x] Gravedad y Prioridad asignadas y justificadas.
- [x] PHI enmascarado en texto y con recordatorio para la captura.
- [x] Evidencia como apoyo, no como sustituto.
- [x] Capa señalada (Frontend) con hipótesis de causa marcada como a validar.

---

## Ejemplo (genérico)

> Recuadro ilustrativo. El mismo bug puede aparecer como *"Se deshabilita el botón `<acción>`"*: en un módulo `<modulo>`, con un usuario de rol `<rol>`, un registro de tipo `<tipo>` en estado `<estado>`, y un recurso relacionado sin dirección cargada. Esa acción no requiere domicilio, así que el botón no debería bloquearse. Etiqueta: `<tema>` (una sola).
