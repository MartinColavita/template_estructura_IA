---
id: index-arquitectura
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "03 - Arquitectura (modulo-ejemplo)"
description: Índice del pilar de arquitectura — stack, patrones, diagramas de integración y modelos de datos del módulo.
tags: [modulo-ejemplo, arquitectura, indice, okf]
last_updated: 2026-10-22
author: "equipo"
---

# 03 - Arquitectura (modulo-ejemplo)

Este directorio es el **Manual de Ingeniería** del módulo. Acá documentamos las *decisiones
técnicas* sobre cómo construimos el software.

## ¿Qué vas a encontrar acá?
* **Stack y patrones:** tecnologías aprobadas, frameworks y arquitectura.
* **Diagramas de integración:** cómo se conecta este módulo con otros sistemas (sistemas de la organización, APIs externas).
* **Modelos de datos:** estructuras, bases de datos y persistencia.

> **Regla de oro:** acá nos ponemos puramente técnicos. Es el lugar de consulta obligada para desarrolladores antes de implementar nuevas features, y lo que reciben los workers que programan.

## Contenido de esta carpeta

* [[decisiones]]: decisiones arquitectónicas y funcionales confirmadas por el equipo (`DEC-nnn`). Vienen con el template `DEC-001` (el código no vive acá) y `DEC-002` (módulos de dominio con capas, confirmada; su materialización en el stack, ⚠ hasta `DEC-003`); `DEC-003` (el stack) es la primera que hay que tomar. Se nutre de las reuniones en `../extraccion-reuniones/`.
* [[esqueleto-proyectos]]: estructura base de los repositorios de código (back, front y despliegue), convenciones de código (C8 del verificador) y su bloque de derivación a backlog.
* [[infraestructura]]: los recursos de cada ambiente, la convención de nombres y etiquetas, dónde vive el estado, cómo entran los secretos y la vista de despliegue (`DEC-007`; skill `arquitectura-e-infraestructura`).
* [[ambientes]]: los ambientes uno por fila (nombre exacto en la plataforma, si es protegido, quién aprueba y dónde), que lee `bin/gate-despliegue.py` (`DEC-007`; skill `despliegue-continuo`).
* [[gitlab]]: el GitLab del proyecto: el destino autorizado que lee `bin/auditar-gitlab.py`, el plan, los runners por alias y las identidades (`DEC-010`; skill `gestion-de-gitlab`).
* Lo que **corre** (servidores, clusters y URLs autorizados, cambios, runbooks, incidentes) no va acá: va al pilar `../operacion/`; la seguridad, al pilar `../seguridad/`.
* `frontend/` (opcional): si el proyecto tiene front, acá va su arquitectura: un `index.md` con qué leer antes de tocar qué, las reglas duras numeradas y un documento por área.
