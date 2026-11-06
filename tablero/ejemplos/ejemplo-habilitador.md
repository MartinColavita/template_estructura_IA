---
id: ejemplo-habilitador
tipo: ejemplo
estado: F-Draft
modulo: integracion-azure-devops
title: "Ejemplo — Habilitador técnico (pobre → profesional)"
author: equipo
tags: [azure-devops, ejemplo, habilitador-tecnico, migracion, antes-despues]
last_updated: 2026-08-26
---

> **Ejemplo genérico (ilustrativo).** Caso de una migración de microservicios; las rutas `<...>` que se citan son marcadores de la documentación del proyecto (no de este repo/proyecto). Sirve de modelo de cómo queda un Habilitador bien escrito.

# Ejemplo resuelto — Habilitador técnico (pobre → profesional)

*Muestra cómo convertir una "Historia" de migración que en realidad es puro trabajo técnico (3 links de GitLab + "rama: develop", con Criterios de aceptación vacíos) en un Habilitador técnico con objetivo, alcance origen→destino, criterios verificables, riesgos y Definición de terminado.*

---

## Cómo usar este ejemplo

Muchas tarjetas del tablero son de la **migración/reestructuración de microservicios** (mover un dominio, absorber un micro en otro durante una fase de migración). No tienen rol/necesidad/beneficio de negocio: no son Historias de usuario, son **Habilitadores técnicos**. El error típico es escribirlas como Historia con criterios vacíos.

Este archivo es la referencia del resultado bien hecho. El método y el contexto de la migración viven en el plan de migración del proyecto (`<plan-de-migracion.md>`); si el habilitador es "retirar un micro de una fase", el destino está **fijado por el mapa de migración**, no se elige libre.

> Nota de tipo de work item: en el tablero real esto suele cargarse como **Historia de usuario** o **Tarea** (no hay tipo "Habilitador" nativo). Lo importante no es la etiqueta del tipo sino que el contenido sea técnico y **verificable**. Etiquetalo con **una sola** etiqueta temática (ej.: `migracion`) — nunca producto ni versión como tag.

---

## ANTES (tal cual llegó — pobre)

> **Título (Historia):** `Reestructurar microservicio de notificaciones`
>
> **Descripción:**
> https://<host-gitlab>/.../ms-notificaciones
> https://<host-gitlab>/.../ms-mensajeria
> https://<host-gitlab>/.../ms-reportes
> Rama a mover: develop
>
> **Criterios de aceptación:** (vacío)
> **Puntos de historia:** (vacío) · **Área de valor:** (vacío)

---

## Qué le falta (diagnóstico)

| Problema | Por qué importa |
|---|---|
| **Es una Historia sin rol/necesidad/beneficio** | No hay valor de usuario que describir: es trabajo técnico. Forzarlo a formato Historia deja todo vacío. |
| **Descripción = links + "rama: develop"** | Los links son apoyo, no alcance. Nadie sabe qué se mueve, de dónde a dónde, ni qué queda igual. |
| **Criterios de aceptación vacíos** | No hay forma de saber cuándo está "hecho". |
| **Sin origen → destino explícito** | En una fase de migración un micro se **absorbe** en otro; hay que decir cuál en cuál. |
| **Sin fuera de alcance** | Riesgo de tocar lógica de negocio del sistema legacy (límite de arquitectura del backend) o el frontend sin querer. |
| **Sin riesgos ni plan de verificación** | Migrar sin criterios de despliegue/ruteo rompe ambientes. |
| **Sin Puntos de historia / estimación** | No se puede planificar el sprint. |

---

## DESPUÉS (profesional — listo para pegar en Azure DevOps)

### Título
```
[Migración] Absorber ms-notificaciones dentro de ms-mensajeria y retirar el micro de notificaciones
```
<!-- Prefijo claro de trabajo técnico. Origen y destino en el título. Sin typos. -->

### Descripción

**Objetivo técnico**
Consolidar la funcionalidad de notificaciones (hoy en `ms-notificaciones`) dentro de `ms-mensajeria`, siguiendo la **fase actual** de la reestructuración de microservicios (destino confirmado en `<plan-de-migracion.md>`), y retirar `ms-notificaciones` como repo/deploy independiente. No cambia el comportamiento funcional visible para el operador: es una reestructuración interna del backend.

**Contexto y motivación**
- Los servicios de back son hoy un **pasamanos (passthrough)** al sistema legado; la reestructuración reduce la cantidad de micros unificando dominios afines antes de migrar la lógica.
- `ms-notificaciones` es un dominio chico que, según el mapa de la fase (`<plan-de-migracion.md>`), se absorbe en su destino fijo `ms-mensajeria` (mover código + endpoint). ⚠ Ojo: el repo de `ms-reportes` contiene algo de código del dominio de notificaciones (ver `<doc-microservicios>`), pero el destino de **esta** absorción es `ms-mensajeria`, no `ms-reportes`; confirmar el estado real antes de empezar para no duplicar.
- Beneficio: menos micros que desplegar/observar, menos superficie de mantenimiento y de gates (seguridad y calidad).

**Alcance (origen → destino)**
- **Origen:** `ms-notificaciones` (rama `develop`).
- **Destino:** `ms-mensajeria` / `ms-mensajeria-api` (rama `develop`), según `<plan-de-migracion.md>`.
- Mover: controllers/services/DTOs del dominio de notificaciones, sus distintos casos/subtipos, el endpoint de notificaciones, la configuración relevante (puertos/root-path se resuelven en el destino), y dependencias propias.
- Actualizar: la configuración de build del destino, config de despliegue/ruteo por ambiente y referencias del frontend/otros micros que apunten a `ms-notificaciones` para que apunten a `ms-mensajeria`.

**Fuera de alcance (explícito)**
- **No** se toca lógica de negocio ni la base de datos del sistema legacy (esquemas, stored procedures): rige el **límite de arquitectura** (passthrough — el micro no agrega lógica ni accede a BD propia).
- **No** se agregan features nuevas ni se cambia el contrato de los endpoints (mismas rutas/headers y misma estructura de respuesta).
- **No** se despliega a PROD en esta tarjeta (la promoción de ambientes va aparte).

**Subtareas / pasos**
1. Confirmar en el repo el estado actual del dominio de notificaciones (`ms-notificaciones`) y qué falta mover a `ms-mensajeria`.
2. Mover el código del dominio de notificaciones al destino, respetando el patrón controller → service → resolución por subtipo.
3. Ajustar la configuración de build, la configuración de la aplicación y la config de despliegue/ruteo del destino.
4. Redireccionar consumidores (frontend / otros micros) hacia `ms-mensajeria`.
5. Marcar `ms-notificaciones` como absorbido en el registro/memoria del proyecto y coordinar el retiro del deploy con DevOps.
6. Verificar en <ambiente de prueba> y luego <ambiente de aceptación>.

**Material de apoyo**
- Repos (apoyo, no reemplazan el alcance): `ms-notificaciones`, `ms-mensajeria` / `ms-mensajeria-api`, `ms-reportes` (⚠ verificar por qué estaba enlazado el tercero; puede no ser parte de esta migración).
- Guía: `<plan-de-migracion.md>` (procedimiento de retiro y config por ambiente) y ficha del micro destino (`<doc-micro-destino>`).

### Criterios de aceptación (técnicos)

Redactados como verificables (formato Gherkin en español donde ayuda):

- **Escenario: paridad de endpoints tras la absorción**
  - **Dado** que la funcionalidad de notificaciones se movió de `ms-notificaciones` a `ms-mensajeria`
  - **Cuando** se llama a cada endpoint de notificaciones contra `ms-mensajeria` con los mismos headers y payload que contra `ms-notificaciones`
  - **Entonces** la respuesta (estructura, códigos, cuerpo) es equivalente a la del micro original.

- [ ] `ms-mensajeria` compila y buildea con el dominio de notificaciones incorporado; el orden de build respeta el árbol de módulos/parent del proyecto.
- [ ] Todos los casos/subtipos de notificaciones quedan cubiertos por tests (unitarios y/o de aprobación) y pasan.
- [ ] Los consumidores (frontend / otros micros) apuntan a `ms-mensajeria`; no queda ninguna referencia viva a `ms-notificaciones`.
- [ ] La config de despliegue/ruteo del destino está actualizada por ambiente (<ambientes de prueba>).
- [ ] `ms-notificaciones` queda sin deploy activo (coordinado con DevOps) y marcado como absorbido en el registro/memoria del proyecto.
- [ ] No hay cambios en la lógica/BD del sistema legacy ni en el contrato de los endpoints (se respeta el passthrough).
- [ ] Pasan los gates que apliquen (seguridad/calidad) sin nuevos hallazgos propios del código movido.
- [ ] Verificado funcionando en <ambiente de prueba> y <ambiente de aceptación>.

### Riesgos

| Riesgo | Mitigación |
|---|---|
| Referencias colgadas a `ms-notificaciones` (front u otros micros) → 404/401 | Grep de consumidores antes de retirar; retirar el deploy recién cuando no queden referencias. |
| Código del dominio ya disperso (algo vive en el repo `ms-reportes`) | Confirmar estado real primero (`<doc-microservicios>`); el destino es `ms-mensajeria`, no re-mover lo que no corresponda. |
| Ruptura del passthrough al tocar headers/rutas | Criterio de paridad de endpoints + tests de aprobación antes/después. |
| Config de ruteo mal migrada por ambiente | Verificar en <ambientes de prueba> antes de promover; despliegue lo valida DevOps. |
| Tercer repo enlazado (`ms-reportes`) sin relación clara | ⚠ Confirmar alcance con quien creó la tarjeta antes de tocarlo. |

### Definición de terminado (DoD)
- [ ] Todos los criterios de aceptación cumplidos y verificados en <ambiente de prueba> y <ambiente de aceptación>.
- [ ] PR(s) mergeado(s) — un commit por repo (poly-repo) — con descripción y enlace a esta tarjeta.
- [ ] `ms-notificaciones` retirado del deploy (con DevOps) y marcado como absorbido en el registro/memoria del proyecto.
- [ ] Documentación/fichas actualizadas (`<doc-microservicios>`).
- [ ] Sin nuevos hallazgos de seguridad/calidad atribuibles al cambio.

### Metadatos sugeridos

> Los campos desplegables de Azure DevOps muestran su valor **en inglés** y no se pueden traducir en la herramienta: se selecciona el valor **tal cual aparece en Azure**; el texto entre paréntesis es solo ayuda en español.

```
Puntos de historia: 5  (⚠ estimar con el equipo; migración con consumidores a redireccionar)
Área de valor:      Business (negocio) · Architectural (arquitectura)  → seleccionar Architectural (arquitectura)
Prioridad:          2
Etiquetas:          migracion
Ruta de iteración:  <Proyecto>\<Equipo> - Sprint NN
```

---

## Por qué el "DESPUÉS" está bien (checklist)

- [x] Se reconoce como **trabajo técnico**, no se fuerza a formato Historia con campos vacíos.
- [x] Objetivo y motivación escritos; los links quedan como apoyo.
- [x] Alcance **origen → destino** explícito y **fuera de alcance** que protege el límite de arquitectura (passthrough).
- [x] Criterios de aceptación **verificables** (incluido el de paridad de endpoints).
- [x] Riesgos con mitigación y dudas marcadas con ⚠ (no se inventa).
- [x] Definición de terminado que cierra la tarjeta.
- [x] Estimación y metadatos propuestos, alineados al estilo de casa.
