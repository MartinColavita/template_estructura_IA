---
id: index-seguridad
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "06 - Seguridad (modulo-ejemplo)"
description: Índice del pilar de seguridad — la política del módulo, el registro de vulnerabilidades y los modelos de amenazas.
tags: [seguridad, indice, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# 06 - Seguridad (modulo-ejemplo)

Este pilar guarda **lo que el equipo decidió y sabe sobre la seguridad del módulo**: qué se protege y contra
qué línea base, qué vulnerabilidades hay abiertas y en qué plazo se cierran, y qué puede salir mal en cada
flujo. Nace vacío con el template; lo llenan las actividades de [[seguridad]], siempre por `cerebro-curator` y
con el «sí» de una persona.

## Contenido de esta carpeta

| Archivo | Qué guarda | Código |
|---|---|---|
| [[politica]] | El alcance, la línea base por sistema operativo, los punteros a los plazos y a quién acepta excepciones, los contactos por rol, cada cuánto se audita y el registro de auditorías | — |
| [[vulnerabilidades]] | El registro de vulnerabilidades: cada CVE por activo, con su prioridad, su plazo, su tarjeta y su excepción si la hay | `V-nnn` |
| `amenazas/` | Los modelos de amenazas validados, uno por flujo | — |

**Lo que no está acá, y dónde está:**

- **Qué se puede tocar y hasta dónde**: [[inventario]], en el pilar `operacion/`. Un activo que no figura ahí no
  está en el alcance de la seguridad tampoco.
- **Los incidentes**, de seguridad u operativos: `operacion/incidentes/` (`INC-nnn`).
- **Las decisiones** (herramientas, umbrales, plazos, quién responde): `DEC-009` en [[decisiones]].

## Reglas de este pilar

- **Nada crudo**: ni la salida de un escáner, ni un registro, ni evidencia. Un informe de escaneo es un mapa
  para un atacante: vive en `borrador/` de quien lo corrió; acá entra el resumen.
- **Sin direcciones, sin nombres reales de servidores, sin secretos, sin datos de personas**: los activos van
  por su alias del inventario; los secretos, por su referencia en el gestor; las personas, por rol.
- **Las líneas base, por número de control**: nunca el texto de un benchmark y nunca «cumple»; se escribe
  «resultado del perfil X, fecha Y».
- Cada cambio queda firmado en [[log]].

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-050)_
