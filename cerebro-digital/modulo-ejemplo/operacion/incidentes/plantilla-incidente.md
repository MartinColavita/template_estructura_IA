---
id: plantilla-incidente
tipo: incidente
estado: F-Draft
modulo: modulo-ejemplo
title: "INC-nnn — <qué no anduvo, en términos del negocio> — plantilla de incidente"
description: Molde del registro de un incidente cerrado, operativo o de seguridad, con su postmortem sin culpa. Copiar como INC-nnn-<slug>.md y completar.
tags: [plantilla, incidente, postmortem, operacion, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
clase: "<operativo | seguridad>"
severidad: "<Crítico | Alto | Medio | Bajo>"
inicio_utc: "<AAAA-MM-DDTHH:MM>"
fin_utc: "<AAAA-MM-DDTHH:MM>"
---

# INC-nnn — <qué no anduvo, en términos del negocio>

> **Cómo se usa este molde.** Se copia a `operacion/incidentes/INC-nnn-<slug>.md` con el siguiente número libre.
> Nace del documento vivo del incidente (en `borrador/`), se completa al cerrar y entra al Cerebro por
> `cerebro-curator` con el «sí» de una persona. Es **sin culpa**: se busca qué permitió que pasara, nunca quién. La
> escala de severidad está en `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/incidentes.md`.
> Un incidente operativo sigue [[operacion-de-servidores]]; uno de seguridad, [[seguridad]], que completa además el
> bloque «Evidencia». Sin datos de personas ni secretos: marcadores (`<persona>`, `<identificador>`,
> `<dato-sensible>`) y alias del [[inventario]].

## Resumen

<Tres líneas en criollo: qué pasó, cuánto duró, cómo se resolvió.>

## Impacto

<A quiénes afectó, cuánto tiempo y qué no pudieron hacer. Sin datos de personas.>

## Detección

<¿Lo detectó una alerta o una persona? ¿Cuánto tardamos en enterarnos desde que empezó?>

## Línea de tiempo (UTC)

Empieza **antes** del incidente (el cambio, el despliegue o la carga que lo preparó). Hechos, con la hora, sin juicio.

| Hora (UTC) | Qué pasó | Quién (rol) |
|---|---|---|
| `<AAAA-MM-DD HH:MM>` | `<un hecho>` | `<rol>` |

## Factores que contribuyeron

Varios, y **ninguno es una persona**. «Error humano» no es un factor: si aparece, se pregunta qué lo hizo posible.

- <factor: qué del sistema, del proceso o de la información lo permitió>

## Disparador

<Lo que lo desencadenó, como hecho.>

## Mitigación y resolución

<Qué se hizo, con qué runbook (`RB-nnn`) y qué plan de cambio, y quién lo aprobó (rol). Los cambios ejecutados
figuran en [[cambios]].>

## Salió bien · salió mal · tuvimos suerte

| Salió bien | Salió mal | Tuvimos suerte |
|---|---|---|
| <...> | <...> | <...> |

## Acciones

| Acción | Para qué (prevenir / detectar / mitigar) | Dueño (rol) | Tarea |
|---|---|---|---|
| `<acción>` | `<prevenir>` | `<rol>` | `<#ID>` ⚠ |

## Aprendizajes y deuda

<`AP-nnn` en `aplicacion/aprendizajes.md`, `DT-nnn` en `aplicacion/deuda.md`, y el runbook (`RB-nnn`) a crear o
corregir.>

## Información de soporte

<Enlaces a consultas y tableros. Nunca capturas con datos de personas ni con secretos.>

## Evidencia (opcional: sólo un incidente de seguridad)

La evidencia **no vive en este repositorio**: se guarda donde fije `DEC-009`. Acá va sólo lo que permite probar que
no cambió. Nunca su contenido. Una fila por archivo y **una fila para el propio manifiesto**, cuya huella es el ancla
para verificar después; cada traspaso de la evidencia, en la línea de tiempo.

| Qué es | Ubicación (fuera del repositorio) | Huella (SHA-256) | Cuándo se tomó (UTC) | Quién la pidió (rol) |
|---|---|---|---|---|
| `<qué evidencia, o «manifiesto»>` | `<dónde se guarda>` | `<huella>` | `<AAAA-MM-DD HH:MM>` | `<rol>` |

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-049)_
