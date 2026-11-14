---
id: redaccion-tickets-conocimiento-index
tipo: indice
estado: F-Draft
modulo: integracion-azure-devops
title: Índice del conocimiento de redacción de tickets
author: equipo
tags: [redaccion, tickets, azure-devops, historias, bugs, indice]
last_updated: 2026-08-26
---

# Índice del conocimiento de redacción de tickets

Mapa de la carpeta `conocimiento/` del paquete de redacción de tickets para Azure DevOps. Cada archivo enseña **cómo se escribe bien** una historia, un criterio de aceptación, un bug, cómo se estima y cómo se prioriza. El método es **agnóstico** (sirve para cualquier proyecto del equipo); el conocimiento del dominio concreto del proyecto está en [[contexto-proyecto]].

El **método** es agnóstico de dominio y reutilizable entre los proyectos del equipo: el contexto concreto (dominio + tablero) se completa por proyecto. Los recuadros rotulados **Ejemplo (genérico)** son solo ilustración; no son el tema.

---

## Los archivos

| Archivo | Qué contiene | Cuándo consultarlo |
|---|---|---|
| [[historias-de-usuario]] | Cómo convertir un pedido pobre en una historia con rol, necesidad y valor; formato "Como/quiero/para", criterios INVEST, cuándo algo NO debería ser historia, técnicas de división. | Al redactar o auditar una **Historia de usuario**. |
| [[criterios-aceptacion-gherkin]] | Cómo escribir el campo Criterios de aceptación: Gherkin en español (Dado/Cuando/Entonces) vs. lista de reglas, verificables y sin PHI, incluyendo el camino no feliz. | Al escribir los **Criterios de aceptación** de una historia. |
| [[definicion-preparado-terminado]] | Definición de Preparado (DoR) y de Terminado (DoD): las dos listas de control para que un ítem entre a un sprint y para poder cerrarlo. | Para decidir si una historia **está lista para el sprint** o cuándo está terminada. |
| [[estimacion-y-priorizacion]] | Cómo estimar esfuerzo (Puntos de historia) y ordenar el trabajo (Gravedad 1-4, Prioridad 1-4, MoSCoW), con tablas de referencia. | Al **estimar** una historia/tarea o asignar **Gravedad/Prioridad** a un bug. |
| [[requisitos-no-funcionales]] | Cuándo y cómo sumar requisitos no funcionales (seguridad, rendimiento, disponibilidad, auditoría, compatibilidad, usabilidad) redactados de forma medible. | Cuando el ticket toca **calidad** además de función. |
| [[bugs-y-defectos]] | Cómo reportar un bug reproducible: Ambiente, Versión, Pasos, Esperado, Obtenido, **por qué es un error**, Observaciones, Evidencia. | Al redactar o auditar un **Bug**. |
| [[antipatrones]] | Catálogo de errores típicos (historia que es tarea, "ver adjunto", criterios vacíos, mezcla de ambientes...) con ejemplo pobre y arreglo. | Para **revisar** un ticket dudoso o entender por qué uno está mal. |
| [[organizacion-y-trazabilidad]] | **Etiqueta temática** (sin prefijo), **relaciones/links** entre tickets (Parent/Related), **documento fuente por referencia** (link, sin copiar contenido), **códigos `[RN-…]`** y **mapeo OKF→ADO**. | **En cada ticket** (aplica a todos los tipos) y al **bajar un módulo entero** al backlog. |
| [[cambios-en-el-backlog]] | Qué hacer cuando el documento cambia y la tarjeta ya existe: **desfase (drift)** con DIFF antes de pisar, **protocolo de aviso** (comentario @mención, acuse con la respuesta + query guardado) y **modificaciones sobre lo entregado** (bug vs. evolutivo; lo cerrado no se reabre). | Cuando un **doc evoluciona** y ya hay tickets creados. |
| [[contexto-proyecto]] | La plantilla de contexto a completar para el proyecto destino (producto, Cerebro Digital, módulos, etiquetas y tablero), con lo confirmado y lo `(pendiente)`. | Para saber el **contexto real** del proyecto actual al redactar o bajar tickets. |
| [[tablero-autorizado]] | El **guard de escritura**: el único tablero autorizado (`{{AZURE_ORG}}` / `{{AZURE_PROYECTO}}` / `{{AZURE_TEAM}}`), el chequeo obligatorio antes de crear/editar y el texto de la advertencia. | **Antes de escribir** en el board (barrera dura de AGENTS). |
| [[deduplicacion-antes-de-crear]] | Cómo **buscar equivalentes/solapamientos** en el board antes de crear (tag/título/documento fuente, foco en abiertas), con el flujo fijo: si ya existe, no se duplica. | **Antes de crear** cualquier work item (barrera dura de AGENTS). |
| [[pipeline-doc-a-tickets]] | El **puente doc→tickets** de punta a punta: cómo se baja una ficha del Cerebro al backlog (mapeo OKF→ADO, confirmación, alta por MCP) y se deja la traza doc↔ticket por referencia. | Para entender el **pipeline completo** o al bajar una ficha al board. |

---

## Combos recomendados por tipo de ticket

- **Historia de usuario** → [[historias-de-usuario]] + [[criterios-aceptacion-gherkin]] + [[definicion-preparado-terminado]] (y [[estimacion-y-priorizacion]] para estimar, [[requisitos-no-funcionales]] si hay calidad en juego).
- **Tarea / Habilitador técnico** → [[estimacion-y-priorizacion]] (esfuerzo) + antipatrón 1 de [[antipatrones]].
- **Bug** → [[bugs-y-defectos]] (+ [[estimacion-y-priorizacion]] para Gravedad/Prioridad).
- **Auditar un ticket existente** → [[definicion-preparado-terminado]] (DoR/DoD) + [[antipatrones]].
- **En TODO ticket (cualquier tipo)** → [[organizacion-y-trazabilidad]]: etiqueta temática + relaciones (Parent/Related) + documento fuente por referencia + códigos `[RN-…]`.
- **Bajar un módulo/documento entero al backlog** → [[organizacion-y-trazabilidad]] §5 (mapeo Vertical slice→Épica·Capacidad→Feature·Flujo→Historia·Técnico→Tarea, alta en lote con confirmación).
- **El doc cambió y ya hay tickets** → [[cambios-en-el-backlog]] (desfase/drift, avisos, modificaciones) + [[consultar-backlog]] para detectar lo desfasado (solo lectura).

---

## Reglas culturales que atraviesan todo el paquete

- **No inventar.** Lo que no está confirmado se marca "(pendiente)" y se pregunta; nunca se rellena con supuestos.
- **Respetar la provenance.** Cuando hay varias fuentes (spec, observado, derivado), gana la de mayor autoridad y se anota el desvío.
- **PHI prohibido.** Los datos personales reales (nombre, documento, identificador, teléfono, dato sensible del dominio) nunca van en un ticket: se usan marcadores como `<persona>`, `<documento>`, `<dato-sensible>`.
- **Silencio al entregar.** El resultado se entrega al grano, sin narrar el proceso ni pedir aplausos.
