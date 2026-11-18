---
id: vulnerabilidades
tipo: seguridad
estado: F-Draft
modulo: modulo-ejemplo
title: Registro de vulnerabilidades — modulo-ejemplo
description: Cada vulnerabilidad conocida por activo (V-nnn), con su prioridad, su plazo, su estado, su tarjeta y su excepción si la hay.
tags: [seguridad, vulnerabilidades, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# Registro de vulnerabilidades — modulo-ejemplo

> Una fila por **CVE y activo**, `V-nnn` consecutivos. Nace **vacío** (sólo la fila de molde). La prioridad y
> el plazo los calcula un script (`bin/priorizar-vulnerabilidades.py`) con los plazos de `DEC-009`; la fila la
> escribe `cerebro-curator` con el «sí» de una persona. **No va acá**: la salida cruda de un escáner,
> direcciones, nombres reales de servidores, secretos ni datos de personas.

## Abiertas

| # | CVE | Activo (alias) | Paquete y versión | Arreglo (versión) | CVSS (versión y vector) | EPSS (valor y fecha) | KEV | Prioridad | Plazo | Estado | Tarjeta | Excepción (motivo · quién · vence) | Fuente (informe y fecha) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V-001 | `<CVE-AAAA-NNNNN>` | `<alias>` | `<paquete> <versión>` | `<versión que lo arregla o ⚠ sin arreglo>` | `<4.0 · vector>` | `<0,00 · AAAA-MM-DD>` | `<sí · no>` | `<la del script>` | `<AAAA-MM-DD>` | `<abierta · en curso · aceptada · vencida>` | `#NNNN` | `<motivo · rol y persona · AAAA-MM-DD>` | `<escaneo y fecha>` |

## Cómo se lleva

- **Una fila por CVE y activo.** La misma vulnerabilidad en dos activos son dos filas; la misma en el mismo
  activo, vista en otro escaneo, es la misma fila (se actualiza la fuente).
- **Estados**: `abierta` (sin tarjeta o sin empezar) · `en curso` (con tarjeta tomada) · `aceptada` (con una
  excepción vigente) · `vencida` (se pasó el plazo, o venció la excepción).
- **Una excepción sin vencimiento no vale**: la fila sigue abierta. La acepta el rol que fija `DEC-009`, nunca
  la IA.
- **Se cierra sólo con un nuevo escaneo que diga que ya no está**: la fila pasa a «Resueltas», con la fecha y el
  escaneo que lo mostró. La palabra de quien arregló no alcanza.

## Resueltas

| # | CVE | Activo (alias) | Cómo se resolvió (`#ID`, versión) | Escaneo que lo verificó | Fecha |
|---|---|---|---|---|---|

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-050)_
