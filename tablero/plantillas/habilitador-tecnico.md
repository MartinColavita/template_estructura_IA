---
id: plantilla-habilitador-tecnico
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Habilitador técnico / Investigación acotada (Azure DevOps)"
author: equipo
tags: [azure-devops, habilitador-tecnico, enabler, spike, plantilla, redaccion]
last_updated: 2026-08-26
---

# Plantilla — Habilitador técnico / Investigación acotada (Spike)

Plantilla rellenable para trabajo técnico sin valor de negocio directo (migración/reestructuración de servicios, upgrades, análisis técnicos), pensada para reemplazar el anti-patrón "descripción = 3 links de GitLab". Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[tarea]] · [[historia-de-usuario]] · [[mapa-campos-azure]]

---

## Cuándo usar esta plantilla

Usala para el trabajo que **habilita** o **desbloquea** valor pero no lo entrega directamente al usuario:

- **Habilitador técnico (Enabler):** reestructuración de un servicio/módulo, unificación de componentes, homogenización de configuración, upgrade de dependencias, adecuación de infra/deploy. Hay que **construir algo**.
- **Investigación acotada (Spike):** investigación con un **tiempo máximo fijo (timebox)** para **responder una pregunta técnica** o reducir incertidumbre antes de estimar. El entregable es **conocimiento** (una recomendación, una prueba de concepto, una ficha), no código productivo.

> **Anti-patrón que esto reemplaza:** una Historia/Tarea "Reestructurar microservicio X" cuya Descripción son 3 links de GitLab + "Rama a mover: develop", con **Criterios de aceptación vacíos** y sin Puntos de historia. Acá los links son **contexto**, y el trabajo queda **escrito y verificable**.

---

## En qué tipo de work item se carga

En Azure DevOps (proceso Agile) no existe un tipo "Spike/Enabler" propio. Cargalo como:

- **Tarea** (Task) si cuelga de una Historia/Característica concreta y es un paso técnico de ella. Ver [[tarea]].
- **Historia de usuario** con **Área de valor = `Architectural`** si es un habilitador grande y autónomo (típico en reestructuraciones). Así aprovechás **Criterios de aceptación** y **Puntos de historia**.

| Campo visible (Azure) | Referencia interna | Qué poner acá |
|---|---|---|
| Título | `System.Title` | Verbo técnico + componente/alcance |
| Descripción | `System.Description` (HTML) | Objetivo, contexto, motivación, alcance, riesgos, DoD |
| Criterios de aceptación | `Microsoft.VSTS.Common.AcceptanceCriteria` | Criterios técnicos verificables (si es Historia) |
| Área de valor | `Microsoft.VSTS.Common.ValueArea` | `Architectural` para habilitadores |
| Puntos de historia | `Microsoft.VSTS.Scheduling.StoryPoints` | Estimación (si es Historia) |
| Esfuerzo original | `Microsoft.VSTS.Scheduling.OriginalEstimate` | Horas (si es Tarea) |
| Prioridad / Riesgo | `Priority` / `Risk` | Prioridad `1`·`2`·`3`·`4` · Riesgo `1 - High` · `2 - Medium` · `3 - Low` |
| Etiquetas | `System.Tags` | p.ej. `migracion` (una sola etiqueta temática) |

> Los desplegables de Azure muestran su valor **en inglés** y no se pueden traducir en la herramienta: se selecciona el valor **tal cual aparece**; el texto entre paréntesis es solo ayuda en español. Área de valor: `Business (negocio)` · `Architectural (arquitectura)`. Riesgo: `1 - High (alto)` · `2 - Medium (medio)` · `3 - Low (bajo)`. Prioridad: `1`·`2`·`3`·`4`.

---

## PLANTILLA (copiar y rellenar)

### Título
```
<verbo tecnico> <componente / servicio> — <resultado>
```
<!-- Ejemplos:
     "Reestructurar ms-reservas a api+impl"
     "Unificar el componente de notificaciones en la libreria comun"
     "Investigacion acotada (Spike): evaluar migracion de la libreria de graficos"
     Empezá con "Investigación acotada (Spike):" cuando sea investigación con tiempo máximo fijo. -->

### Descripción

**Objetivo técnico**
<!-- Una o dos oraciones: qué resultado técnico se busca. Para un spike: qué pregunta hay que responder. -->
<que se va a lograr tecnicamente>

**Contexto**
<!-- El estado actual y los datos duros. Acá SÍ van los links, como contexto, no como todo el contenido. -->
- Origen → destino: <p.ej. ms-origen → ms-destino> (si es unificación/migración)
- Rama: <p.ej. develop>
- Estructura actual → objetivo: <p.ej. repo unico → api + impl>
- Repos / MRs relacionados: <links GitLab self-hosted, como contexto>
- Doc / plan de referencia: <ruta o wikilink>

**Motivación (por qué / qué desbloquea)**
<!-- Por qué se hace ahora y qué habilita. Sin esto, el habilitador parece trabajo porque sí. -->
<p.ej. "Homogeneizar la estructura desbloquea el retiro del sistema legacy por etapas y alinea con los servicios ya reestructurados">

**Alcance**
<!-- Qué entra. Sé concreto con archivos/módulos/config. -->
- <p.ej. crear modulo `-api`, mover DTOs/interfaces, ajustar la configuracion de build compartida>
- <p.ej. actualizar configuracion (puerto/root-path) segun convencion>

**Fuera de alcance**
<!-- Qué explícitamente NO entra. Clave para que no crezca. -->
- <p.ej. cambios de comportamiento observable>
- <p.ej. cambios en el frontend>

**Criterios de aceptación técnicos (verificables)**
<!-- Reemplazan al "Criterios de aceptación vacío". Cada uno debe poder marcarse sí/no. -->
- [ ] <p.ej. El servicio compila con el comando de build del proyecto sin errores.>
- [ ] <p.ej. Existe el modulo `<servicio>-api` con las interfaces/DTOs movidos.>
- [ ] <p.ej. Los endpoints responden igual que antes: mismo contrato de request/response.>
- [ ] <p.ej. Config alineada a la convencion del proyecto (puerto, root-path).>
- [ ] (Spike) <p.ej. Queda una recomendacion escrita con opcion elegida y justificacion.>

**Riesgos**
<!-- Qué puede salir mal y cómo se mitiga. -->
- <riesgo> → <mitigacion>
- <p.ej. "Romper el contrato del endpoint" → cubrir con tests de aprobacion antes y despues>

**Definición de terminado (DoD)**
- [ ] Compila / buildea en el orden correcto.
- [ ] Tests pasan (unitarios y/o de integración/aprobación).
- [ ] Pasa gates aplicables (seguridad: SAST/SCA; calidad de código: cobertura/duplicación/complejidad/code smells) sin nuevos hallazgos propios.
- [ ] **No cambia el contrato** hacia los consumidores (o el cambio está declarado y coordinado).
- [ ] Build publicado en el registry y desplegado en el ambiente que corresponda.
- [ ] Documentación / ficha de memoria actualizada.
- [ ] (Spike) Recomendación / conclusión documentada y compartida.

### Área de valor
```
Architectural (arquitectura)   ← seleccionar en Azure el valor "Architectural"
```

### Estimación
```
Puntos de historia (si es Historia): <n>   |   Esfuerzo original (si es Tarea): <N> h
```
<!-- Para una investigación acotada (Spike), la estimación es un tiempo máximo fijo (timebox), no un compromiso de resultado. -->

### Prioridad / Riesgo
```
Prioridad: <1|2|3|4>   ·   Riesgo: <1 - High (alto) | 2 - Medium (medio) | 3 - Low (bajo)>
```

---

## Ejemplo (genérico)

> Recuadro ilustrativo con un dominio neutro. Es solo un ejemplo; la plantilla de arriba es la que se usa.
>
> **Título:** `Reestructurar ms-notificaciones a api+impl`
> **Objetivo técnico:** separar el micro en `ms-notificaciones-api` (contratos/DTOs) e `impl`, alineado a los micros ya reestructurados, sin cambiar comportamiento.
> **Motivación:** homogeneizar estructura desbloquea el retiro por etapas del monolito legacy.
> **Fuera de alcance:** lógica de negocio (límite con el sistema legado), frontend.
> **Área de valor:** Architectural · **Puntos de historia:** 5 · **Riesgo:** 2 - Medium (medio).
