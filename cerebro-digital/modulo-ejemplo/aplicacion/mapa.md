---
id: mapa-aplicacion
tipo: aplicacion
estado: F-Draft
modulo: modulo-ejemplo
title: Mapa de la aplicación — modulo-ejemplo
description: Lo que existe hoy en el código, módulo por módulo, con las Historias que lo construyeron, su estado y sus integraciones y ambientes reales.
tags: [modulo-ejemplo, aplicacion, mapa]
last_updated: 2026-10-30
author: "equipo"
---

# Mapa de la aplicación — modulo-ejemplo

> Qué existe hoy, de verdad, en los repositorios de código. Cada fila sale del repositorio (el
> Merge Request, el `openapi.yaml`, el inventario de `bin/inventariar-codigo.py`), no de la memoria
> de nadie. Se actualiza en el cierre de cada Tarea (paso 7-bis) y en la absorción de una
> aplicación existente. Si un módulo del código no está acá, el mapa está viejo: es un hallazgo.

## Módulos de código

| Módulo | Repositorio | Qué hace (una línea) | Qué expone (endpoints / pantallas / jobs) | Historias que lo construyeron | Estado | Último Merge Request |
|---|---|---|---|---|---|---|
| `<modulo>` | `back` / `front` | <qué resuelve> | <rutas del contrato o pantallas> | `#ID`, `#ID` | en construcción / en producción / legado / a migrar | `!nn` (fecha) |

Estados: **en construcción** (hay Tareas abiertas), **en producción** (desplegado y en uso),
**legado** (existe, nadie lo toca, nadie lo migró todavía), **a migrar** (DEC-004 lo marcó).

## Integraciones reales

| Sistema externo | Módulo que lo usa | Cómo (protocolo, contrato) | Ambiente de prueba disponible | Fuente |
|---|---|---|---|---|
| <sistema> | `<modulo>` | <REST / cola / archivo / base> | sí / no / ⚠ sin dato | archivo o Merge Request |

Lo que dice `contexto.md` §Integraciones es lo **previsto**; esto es lo **que está conectado**.

## Ambientes

| Ambiente | Para qué | Cómo se despliega | Quién lo administra | Fuente |
|---|---|---|---|---|
| desarrollo / prueba / producción | <uso> | <pipeline o manual> | <equipo> | <doc o pipeline> |

Sin credenciales ni hosts internos que no deban versionarse: eso va por variable de entorno
(`dependencias-y-config.md` de la skill `desarrollo`).

## Si la aplicación se absorbió

La primera versión de este mapa es el resumen de `bin/inventariar-codigo.py` validado con un «sí»:
lenguajes, build, pipeline, contenedores, contratos, migraciones, proporción de tests y deuda
declarada, con la fecha y el commit inventariado. Después se refina módulo por módulo.
