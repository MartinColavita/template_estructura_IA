---
id: politica
tipo: seguridad
estado: F-Draft
modulo: modulo-ejemplo
title: Política de seguridad — modulo-ejemplo
description: El alcance de la seguridad del módulo, la línea base por sistema operativo, los punteros a plazos y excepciones, los contactos por rol, cada cuánto se audita y el registro de auditorías.
tags: [seguridad, politica, modulo-ejemplo]
last_updated: 2026-11-14
author: "equipo"
---

# Política de seguridad — modulo-ejemplo

> Nace **vacía, con filas de molde**. Mientras una sección esté sin completar, lo que dependa de ella es
> `SIN DATOS`: una auditoría no puede compararse contra una línea base que nadie eligió. La completa el equipo;
> cada cambio es una decisión, con su firma en [[log]]. Las decisiones de fondo (herramientas, umbrales, plazos,
> quién responde) viven en `DEC-009` ([[decisiones]]); acá van los punteros, **no una copia**.

## Alcance

Lo que está en el alcance es **lo que figura en [[inventario]]**: los activos por su alias, con su ambiente,
su exposición a internet y su criticidad. Lo que no figura ahí no se audita, no se escanea y no se toca.

| Ambiente | Qué entra | Qué queda afuera, y por qué |
|---|---|---|
| `<ambiente>` | `<tipos de activo: servidores, imágenes, URLs>` | `<lo excluido y su motivo>` |

## Línea base por sistema operativo

Se cita **el perfil y la versión del contenido**; los controles, **por número**. Nunca se copia el texto de un
benchmark y nunca se escribe «cumple»: el resultado se escribe como «resultado del perfil X, fecha Y».

| Sistema operativo | Perfil de referencia | Versión del contenido | Controles que no se aplican (número y motivo) |
|---|---|---|---|
| `<sistema y versión>` | `<id del perfil, por ejemplo de ComplianceAsCode>` | `<versión>` | `<número>: <motivo>, aceptado por <rol>, vence <fecha>` |

## Plazos de remediación y excepciones

- **Los plazos** por prioridad: los fija `DEC-009` («Prioridad y plazos»). No se repiten acá.
- **Quién acepta una excepción** (un riesgo que se decide no arreglar en plazo): quien fije el equipo, que no
  puede ser quien escribió el cambio (`DEC-009`, «Supresiones y excepciones»). Toda excepción lleva motivo, quién la aceptó y **fecha de vencimiento**; vive en
  [[vulnerabilidades]], en la fila de la vulnerabilidad.

## Contactos por rol

Por rol, **nunca el nombre de una persona**: los nombres cambian, el rol no. Quién ocupa cada rol hoy lo
sabe el equipo, fuera de este repositorio.

| Rol | Para qué se lo busca | Suplente (rol) | Canal |
|---|---|---|---|
| `<rol responsable de seguridad>` | `<incidentes de seguridad, aceptar excepciones>` | `<rol>` | `<canal de escalamiento>` |

## Cada cuánto se audita

| Qué | Herramienta | Cada cuánto | Quién la corre |
|---|---|---|---|
| El acceso remoto de cada servidor, desde afuera | ssh-audit (`bin/auditar-host.py --correr-ssh-audit`) | `<frecuencia>` | `<la IA o un rol>` |
| Cada servidor, por dentro | Lynis (el informe lo genera una persona) | `<frecuencia>` | `<rol>` |
| Las imágenes que corren | `bin/escanear-imagenes.py` | `<frecuencia, y en cada imagen nueva>` | `<la IA o el pipeline>` |

## Registro de auditorías

Una fila por auditoría hecha: el resumen, **nunca el informe crudo** (ese queda en `borrador/` de quien la
corrió y no se versiona).

| Fecha | Activo (alias) | Qué se corrió | Veredicto | Vulnerabilidades que abrió (`V-nnn`) |
|---|---|---|---|---|
| `<AAAA-MM-DD>` | `<alias>` | `<herramientas>` | `<OK · HALLAZGO · SIN DATOS, con el motivo>` | `<V-nnn>` |

_Últ. modif.: 2026-11-14 — @equipo — plantilla heredada del template (M-050)_
