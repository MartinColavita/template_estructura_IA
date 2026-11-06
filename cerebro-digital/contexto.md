---
id: contexto
tipo: contexto
estado: F-Draft
modulo: general
title: Contexto del proyecto {{PROYECTO}}
description: Visión general del dominio de {{PROYECTO}}, su propósito, alcance, origen del proyecto y equipo.
tags: [contexto, dominio, origen]
last_updated: 2026-10-22
author: "equipo"
---

# Contexto — {{PROYECTO}}

> Plantilla. Cada sección trae lo que tiene que contestar; lo que no se sabe se marca
> `(pendiente)` y se pregunta — nunca se inventa.

## ¿Qué es {{ORGANIZACION}} y qué es {{PRODUCTO}}?

**{{ORGANIZACION}}** <completar: qué tipo de organización es, a quién sirve>.

**{{PRODUCTO}}** <completar: qué sistema/producto es, qué gestiona, y qué lugar ocupa este
proyecto adentro de él>.

## Origen del proyecto

<completar: por qué existe este proyecto. Por ejemplo: una migración de un sistema legado, una
funcionalidad que quedó afuera de una entrega anterior, un producto nuevo. Quién lo pidió y qué
se espera.>

## Propósito del sistema

<completar: en dos o tres oraciones, qué hace el módulo que este Cerebro documenta y qué lo
distingue de lo que ya existe.>

## Alcance del dominio

El sistema cubre el ciclo de vida completo de <la entidad central del negocio>:

1. **<Etapa 1>** — <qué pasa, por qué canal entra>
2. **<Etapa 2>** — <…>
3. **<Etapa n>** — <cierre o finalización>

## Integraciones con sistemas externos

| Sistema | Rol | Tipo de integración |
|---------|-----|-------------------|
| <sistema> | <qué hace en el flujo> | <entrada / salida / migración / consulta> |

## Principios operativos clave

- **<Principio>**: <qué significa en la operación. Si describe el sistema vigente y no el nuevo, decirlo.>

## Equipo

- <Quiénes forman el equipo y qué rol tiene cada uno: funcionales, programadores, QA, arquitectura.>
- Se usa **IA** como herramienta principal de documentación y desarrollo; el ecosistema lo usa todo el equipo.
- El stack técnico lo definen los programadores y queda escrito en [[decisiones]] y [[esqueleto-proyectos]].

## Formato de conocimiento

El proyecto utiliza **OKF (Open Knowledge Format)**: conocimiento representado como archivos
markdown con frontmatter YAML. Este bundle en `cerebro-digital/` es la fuente única de verdad del
dominio. Catálogo de `tipo`/`estado`, códigos y footer de trazabilidad: [[index]].

## Referencias

- Documentos de origen: ver [[fuentes]].
- Preguntas abiertas: ver `modulo-ejemplo/pendientes.md`.
