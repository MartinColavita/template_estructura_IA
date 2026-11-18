---
id: index-operacion
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "05 - Operación (modulo-ejemplo)"
description: Índice del pilar de lo que corre — qué servidores, clusters y URLs puede tocar la IA, qué cambios se hicieron, los runbooks y los incidentes.
tags: [operacion, indice, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# 05 - Operación (modulo-ejemplo)

Este pilar es la **memoria de lo que corre**: qué se puede tocar y hasta dónde, qué se cambió, cómo se arregla lo
que se rompe y qué pasó cuando se rompió. Los otros pilares dicen qué tiene que hacer la aplicación y cómo se
construye; éste dice **cómo se la mantiene andando**. Nace vacío: sin una fila en el inventario, nada está
autorizado. El método está en [[operacion-de-servidores]]; las barreras, en [[AGENTS]].

| Archivo | Qué guarda | Código | Quién lo alimenta |
|---|---|---|---|
| [[inventario]] | Los servidores, clusters, imágenes y URLs que la IA puede tocar, por alias, y hasta qué nivel | — | Una persona; lo leen `bin/activo-autorizado.py` y los scripts de operación y de seguridad |
| [[cambios]] | Una línea por cambio N1 o N2 ejecutado: qué, dónde, quién aprobó y cómo quedó | — | El cierre de cada plan de cambio |
| `runbooks/` | Un runbook por síntoma o por alerta, molde en [[plantilla-runbook]] | `RB-nnn` | Un incidente, una alerta nueva, un mantenimiento que se repite |
| `incidentes/` | Un incidente cerrado por archivo, operativo o de seguridad, molde en [[plantilla-incidente]] | `INC-nnn` | El postmortem de [[operacion-de-servidores]] o de [[seguridad]] |

## Reglas de este pilar

- **Lo escribe `cerebro-curator`** con el «sí» de una persona, como todo el Cerebro, y queda en [[log]]. Lo que está
  en curso (un diagnóstico, un plan, el documento vivo de un incidente) vive en `borrador/operacion/` y no entra
  hasta que se cierra.
- **Por alias, nunca por dirección.** Ni IPs, ni nombres reales de servidores, ni usuarios, ni claves: el alias del
  inventario y, para una credencial, dónde vive (el gestor que fije `DEC-008`), nunca su valor.
- **Sin datos de personas**: marcadores (`<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`).
- **Un incidente o un runbook que no cambió nada es una anécdota**: cada uno termina en una Tarea, un aprendizaje
  (`aplicacion/aprendizajes.md`), una deuda (`aplicacion/deuda.md`) o un runbook nuevo o corregido.
- **El registro completo vive en el servidor** (lo que entró por SSH y lo que corrió `sudo`); acá va el resumen.

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-049)_
