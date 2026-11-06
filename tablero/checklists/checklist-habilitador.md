---
id: checklist-habilitador
tipo: checklist
estado: F-Draft
modulo: integracion-azure-devops
title: "Checklist — Habilitador técnico / Spike"
author: equipo
tags: [checklist, habilitador, spike, calidad, azure]
last_updated: 2026-08-26
---

# Checklist — Habilitador técnico / Spike

Control de calidad antes de crear en Azure un **Habilitador técnico** (migración,
reestructuración, upgrade, config) o un **Spike** (investigación con timebox). Molde:
`[[plantillas/habilitador-tecnico]]`. Campos: `[[mapa-campos-azure]]`.

> **Regla previa — tipo correcto.** ¿Es de verdad un Habilitador (trabajo técnico
> sin valor de usuario directo que **desbloquea** valor) y no una Historia? Si tiene
> rol / necesidad / beneficio de negocio, es Historia. El antipatrón "descripción =
> 3 links" casi siempre es un Habilitador mal escrito.

## Estructura
- [ ] **Título**: verbo técnico + componente + resultado (sin typos, con prefijo de módulo).
- [ ] **Objetivo técnico**: qué resultado se busca, en 1–2 frases. (Spike: qué pregunta hay que responder.)
- [ ] **Contexto**: componente / rama origen→destino; los links van como **apoyo**, no como todo el contenido.
- [ ] **Motivación (qué desbloquea)**: por qué se hace ahora.
- [ ] **Alcance** y **Fuera de alcance** escritos (qué SÍ / qué NO; respetar límites de arquitectura).

## Verificable
- [ ] **Criterios de aceptación técnicos** como checklist (compila/buildea, contrato/endpoints igual, config alineada).
- [ ] **Paridad de comportamiento** presente (cada endpoint/función responde igual que antes) — criterio **obligatorio**.
- [ ] (Spike) Queda una **recomendación escrita** con la opción elegida y su justificación.
- [ ] **DoD**: tests pasan, gates aplicables sin nuevos hallazgos propios, no rompe lo existente, doc/ficha actualizada.
- [ ] **Riesgos** con su mitigación.

## Campos y trazabilidad
- [ ] **Área de valor = Architectural** (si va como Historia autónoma) o cuelga de un **Parent** (si va como Tarea).
- [ ] **Estimación**: Puntos (si Historia) / Esfuerzo en horas (si Tarea) / Timebox (si Spike). Si supera ~8, partir.
- [ ] **Etiqueta temática** (sin prefijo, siempre igual) + **Relaciones** (Parent/Related, `#ID` `⚠` a confirmar).
- [ ] **Documento fuente** por ruta (referencia, no contenido). Reglas `[RN-…]` si aplican.

## Idioma / PHI / no inventar
- [ ] Todo en **español**. **Sin PHI** (marcadores). Lo no confirmado va `⚠ (pendiente)` y se pregunta.

> **Veredicto rápido:** no va a Azure si le falta la **paridad de comportamiento**,
> los **criterios técnicos verificables** o el **DoD**. Los links solos no alcanzan.
