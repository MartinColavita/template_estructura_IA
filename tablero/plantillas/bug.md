---
id: plantilla-bug
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Bug (Azure DevOps)"
author: equipo
tags: [azure-devops, bug, defecto, plantilla, redaccion, qa]
last_updated: 2026-08-26
---

# Plantilla — Bug

Plantilla rellenable para reportar un defecto en Azure DevOps con calidad de QA: todo el cuerpo va en **"Pasos para reproducir"**, separando siempre Resultado esperado de Resultado obtenido. Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[checklist-bug]] · [[mapa-campos-azure]] · [[ejemplo-bug]]

---

## Cuándo usar esta plantilla

Usala para reportar un **comportamiento incorrecto** (error, dato mal, pantalla rota, botón que no responde). En Azure, un Bug pone **casi todo el contenido en "Pasos para reproducir"** (`ReproSteps`), no en la Descripción.

> **Anti-patrones que esto viene a eliminar:**
> - Pasos = "Ver adjunto" + texto en flujo de conciencia.
> - Mezclar ambientes (Testing y Producción) en el mismo reporte.
> - No separar **Resultado esperado** de **Resultado obtenido**.
> - No explicar **por qué es un error** (el motivo/impacto), solo qué pasa.
> - Título con typos o sin prefijo de módulo.

> **PHI PROHIBIDO:** nunca pegues datos personales sensibles ni personales reales (persona, documento, teléfono, dato sensible del dominio, identificador). Usá marcadores tipo `<persona>`, `<documento>`, `<identificador>` y describí la **estructura**, no el dato.

---

## A qué campo de Azure va cada bloque

| Bloque de esta plantilla | Campo visible (Azure) | Referencia interna |
|---|---|---|
| Título | Título | `System.Title` |
| Ambiente · Versión · Fecha · Precondiciones · Pasos · Esperado · Obtenido · Observaciones · Evidencia | **Pasos para reproducir** | `Microsoft.VSTS.TCM.ReproSteps` (HTML) |
| (lo llena la extensión del navegador) | Información del sistema | `Microsoft.VSTS.TCM.SystemInfo` |
| Gravedad | Gravedad | `Microsoft.VSTS.Common.Severity` |
| Prioridad | Prioridad | `Microsoft.VSTS.Common.Priority` |
| Puntos de historia | Puntos de historia | `Microsoft.VSTS.Scheduling.StoryPoints` |
| Etiquetas (incluye la temática) | Etiquetas | `System.Tags` |
| Relaciones (Related) + Documento fuente | (enlaces del work item) | `System.LinkTypes.Related` |
| Validación de QA (al reabrir/cerrar) | Historial | `System.History` |

> La **Descripción** de un Bug casi no se usa: todo va en **Pasos para reproducir**. Detalle de campos: [[mapa-campos-azure]].

---

## PLANTILLA (copiar y rellenar)

### Título
```
<Modulo/dominio> - <Contexto>: <sintoma>
```
<!-- Estructura fija "Módulo - Contexto: síntoma". Sin typos, prefijo de módulo consistente.
     Ejemplos:
       "Reservas - Confirmacion de turno: el boton 'Cancelar' queda deshabilitado"
       "Listados - Grilla de registros: muestra el estado viejo tras actualizar" -->

### Pasos para reproducir  *(este es el cuerpo del Bug)*

**Ambiente**
```
<Desarrollo (DESA) | Testing (TEST) | Preproduccion (PREPROD) | Produccion (PROD)>
```
<!-- UN solo ambiente por bug. Si pasa en varios, indicá el principal y anotalo en Observaciones. Nunca mezclar. -->

**Versión**
```
Frontend: <<versión>>   ·   Backend: <<versión>>
```
<!-- Es un CAMPO de contenido (Pasos para reproducir), no un tag. Anotá las dos si aplica. -->

**Fecha de detección**
```
<AAAA-MM-DD> <hh:mm si es relevante>
```

**Precondiciones**
<!-- Qué tiene que estar dado antes de empezar los pasos. Rol/perfil, estado del dato, canal. -->
- Perfil / rol: <p.ej. operador / administrador>
- Datos de contexto (sin PHI): <p.ej. un registro en estado <X>, de tipo <Y>>
- Canal / entrada: <si aplica>

**Pasos**
<!-- Numerados, uno por acción, reproducibles por cualquiera. Sin "flujo de conciencia". -->
1. <accion concreta>
2. <accion concreta>
3. <accion concreta>

**Resultado esperado**
<!-- Qué DEBERÍA pasar. Una cosa, clara. -->
<comportamiento correcto esperado>

**Resultado obtenido**
<!-- Qué pasa REALMENTE. Separado del esperado, sin mezclar. Incluí mensaje de error textual si lo hay. -->
<comportamiento incorrecto observado + mensaje/codigo de error si aparece>

**Por qué es un error (motivo / impacto)**
<!-- SIEMPRE presente. Una o dos frases: por qué el resultado obtenido está mal (qué regla/expectativa rompe) y a quién/qué impacta. NO es la causa técnica: esa, si la hay, va como hipótesis en Observaciones.
     Si el tema tiene reglas de negocio numeradas, indicá cuál se rompe: [RN-<TEMA>-NN] (ver organizacion-y-trazabilidad §4). -->
<por que esta mal + a quien/que afecta> — Regla violada: [RN-<TEMA>-NN] (si aplica)

**Observaciones**
<!-- Datos extra: frecuencia (siempre/intermitente), si afecta a un solo perfil, solución alternativa, correlación con un cambio reciente, si también se ve en otro ambiente. -->
- Frecuencia: <siempre | intermitente (N de M)>
- <otra nota relevante>

**Evidencia**
<!-- Capturas / video / logs adjuntos. NO "ver adjunto" a secas: describí qué muestra cada evidencia. Cuidar PHI: tapar datos reales. -->
- <captura-01.png>: <que muestra>
- <video / log>: <que muestra> — (sin PHI visible)

### Gravedad (Severity)
```
<1 - Critical (critica) | 2 - High (alta) | 3 - Medium (media) | 4 - Low (baja)>
```
<!-- El valor se selecciona TAL CUAL aparece en Azure (los desplegables muestran el texto en inglés y no se traducen en la herramienta); el texto entre paréntesis es solo ayuda en español.
     Guía rápida:
     1 - Critical: bloquea la operación / pérdida de datos / sin solución alternativa.
     2 - High: funcionalidad importante rota, con solución alternativa costosa.
     3 - Medium: molesto pero con solución alternativa simple.
     4 - Low: cosmético / menor. -->

### Prioridad
```
<1 | 2 | 3 | 4>
```
<!-- Gravedad = impacto técnico; Prioridad = urgencia de resolución. Pueden no coincidir. -->

### Puntos de historia (opcional)
```
<n>
```

### Etiquetas
```
<tema>
```
<!-- UN solo tag, techo duro (<tema>, sin prefijo, siempre igual: p.ej. "cancelacion"). Nunca producto/repo ni versión ni slice como tag — la versión, si aplica, va como campo de contenido en "Versión" arriba. Ver organizacion-y-trazabilidad §1. -->

### Relaciones / Enlaces
```
- Relacionadas (Related): <#ID o título de la UH/bug del mismo tema>
- Documento fuente: <ruta/al/documento.md> (link al repo) — referencia, no contenido
```
<!-- La IA propone las relaciones por título/tema; los #ID reales son dato duro (se confirman o se resuelven por MCP). Un bug suele relacionarse con la UH cuyo comportamiento rompe. Ver organizacion-y-trazabilidad §2-§3. -->

---

## Ejemplo (genérico)

> Recuadro ilustrativo con un dominio neutro (reservas), anonimizado. Es solo un ejemplo; la plantilla de arriba es la que se usa.
>
> **Título:** `Reservas - Boton "Cancelar solicitud": queda deshabilitado tras seleccionar el recurso`
> **Ambiente:** Testing (TEST) · **Versión:** Frontend `<versión>` · Backend `<versión>`
> **Precondiciones:** operador `<perfil>`, registro en estado `<Estado1>`, solicitud de tipo `<tipo>`.
> **Resultado esperado:** el botón permanece habilitado para poder cancelar la solicitud.
> **Resultado obtenido:** el botón queda deshabilitado (gris); no hay mensaje de error.
> **Por qué es un error:** la cancelación no depende del recurso seleccionado; al bloquearse, el operador queda trabado. Regla violada: `[RN-RES-04]`.
> **Gravedad:** 2 - High (alta) · **Prioridad:** 2.
> **Etiquetas:** `reservas` (una sola; la versión ya quedó en el campo "Versión" de arriba).
> **Relaciones:** Related: UH "Cancelar una solicitud de reserva" · **Documento fuente:** `conocimiento/funcional/cancelacion-de-reserva.md` (link al repo).
