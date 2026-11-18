---
id: plantilla-runbook
tipo: runbook
estado: F-Draft
modulo: modulo-ejemplo
title: "RB-nnn — <el síntoma, en criollo> — plantilla de runbook"
description: Molde de un runbook para un síntoma o una alerta. Copiar como RB-nnn-<slug>.md y completar paso por paso.
tags: [plantilla, runbook, operacion, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
servicio: "<alias del inventario>"
alertas: []
duenio: "<rol o equipo>"
nivel_max: "<el nivel más alto entre sus pasos>"
ultima_verificacion: "<AAAA-MM-DD: la última vez que alguien lo corrió de verdad>"
---

# RB-nnn — <el síntoma, en criollo>

> **Cómo se usa este molde.** Se copia a `operacion/runbooks/RB-nnn-<slug>.md` con el siguiente número libre, se
> escribe en `borrador/` y entra al Cerebro por `cerebro-curator` con el «sí» de una persona. Cómo se escribe cada
> paso y por qué: [[operacion-de-servidores]] (referencia «runbook»). Las barreras: [[AGENTS]]. Sin secretos (se dice
> dónde vive una credencial, nunca su valor), sin IPs (alias del [[inventario]]) y sin datos de personas.

## Cuándo se usa

<La alerta o el síntoma que lo dispara, tal como lo ve quien está de guardia. Y qué NO cubre: a qué runbook o a qué
skill se va en ese caso.>

## Qué le pasa a la gente

<El impacto en criollo: qué no se puede hacer mientras dura. Sin datos de personas.>

## Lista rápida

1. <Diagnóstico: `python -I bin/salud-host.py --ssh <alias>`>
2. <Un renglón por paso, espejo de la mitigación de abajo>
3. <Verificación>

## Antes de empezar

- Identidad: <la de lectura para el diagnóstico; la de cambio, firmada para esta ventana, si hay pasos N1 o N2>
- Ventana: <la del inventario; en un incidente declarado, la que ordene quien comanda>
- Respaldo verificado: <cuál y de cuándo, si algún paso toca datos o configuración>

## Diagnóstico (N0)

<Qué se mide y con qué script; qué resultado lleva a qué paso.>

## Mitigación

### Paso 1 — <qué> · Nivel <N1 o N2>

- Precondición: <qué tiene que ser cierto para correrlo>
- Comando: `<el comando exacto>`
- Salida esperada: <lo que tiene que imprimir y con qué código sale>
- Si falla: <qué hacer, en concreto>
- Vuelta atrás: <cómo se deja como estaba; sin vuelta atrás, el paso es N3>

### Paso 2 — <qué> · Nivel N3 · Lo hace una persona

- Qué hay que hacer: <la acción>
- Por qué no lo hace la IA: <borra datos, toca accesos, no tiene vuelta atrás…>
- Lo que arma la IA para que la persona decida: <el resumen exacto>

## Verificación

<Qué script o qué medición dice que volvió, y qué tiene que dar.>

## Si nada funciona

<A quién se escala (un rol), cómo y con qué datos a mano.>

## Aviso

<El texto listo, en criollo y sin datos de personas: qué pasa, a quién afecta, qué se está haciendo y cuándo hay
novedades. Mandarlo pide su «sí».>

## Historial

| Fecha | Incidente (`INC-nnn`) o simulacro | Qué se corrigió en este runbook |
|---|---|---|
| `<AAAA-MM-DD>` | `<INC-nnn>` | `<qué cambió>` |

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-049)_
