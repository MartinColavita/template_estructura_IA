---
id: convenciones-git
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: "Convenciones Git y Azure DevOps"
description: Estándar de nombres de ramas, mensajes de commit y Merge Requests, y cómo se vinculan los repositorios de GitLab con el tablero de Azure Boards.
tags: [modulo-ejemplo, metodologia, git, azure, convenciones]
last_updated: 2026-10-22
author: "equipo"
---

# Convenciones Git y Azure DevOps

Esta ficha define el estándar de nomenclatura y la forma en que los repositorios del proyecto (gestionados en GitLab) interactúan con el tablero de seguimiento de requerimientos (Azure Boards). La estructura de los repositorios está en [[esqueleto-proyectos]].

## Integración Multi-repositorio

Los repositorios de código son **uno de back** y **uno o más de front** (uno por aplicación), clonados en `back/<nombre>` y `front/<nombre-de-la-app>` ([[orquestador-desarrollo]] § Dudas y Preguntas). ⚠ Los nombres de cada repositorio los fija el equipo del proyecto. ⚠ Dónde vive la configuración de despliegue: a definir.

⚠ A verificar con Infraestructura/DevOps: que Azure Boards esté integrado con GitLab en **1 a N** (un tablero, varios repositorios).


* **Historia de Usuario:** Opera como el "pegamento" funcional. Representa el flujo completo de negocio y no tiene una rama de código asociada directamente.
* **Tarea:** Es la unidad técnica a nivel código. Cada Tarea pertenece a un único repositorio.

## Nomenclatura de Ramas (Branches)

Se utiliza el formato: `tipo/ID-descripcion-corta`

* El `ID` corresponde **siempre al número de la Tarea** (o del Bug/Habilitador) en Azure DevOps.
* La descripción debe ir en minúsculas, separada por guiones y sin acentos.

**Prefijos actuales permitidos:**
*(Esta lista puede extenderse a futuro según las necesidades del equipo)*
* `task/`: Para el desarrollo de nuevas Tareas técnicas de una historia. Ej: `task/1001-endpoint-alta`
* `bugfix/`: Para corrección de defectos durante el ciclo de vida del sprint. Ej: `bugfix/1050-falla-redireccion`
* `hotfix/`: Para correcciones críticas en producción. Ej: `hotfix/2010-caida-gateway`

## Trazabilidad con Azure

El número del ticket de Azure DevOps **importa en la rama y en el Merge Request; en los commits no importa**.

* **Rama:** lleva el ID en su nombre (`tipo/ID-descripcion`, ver arriba).
* **Merge Request:** lleva el ID en su título (ver abajo).


## Mensajes de Commit

Los commits **no llevan requisito de ID de Azure ni de formato**. La evidencia TDD en los commits (`test(rojo): …`) se rige por [[orquestador-desarrollo]].

**En el Merge Request, los commits se agrupan por importancia**: uno por cambio lógico (el dominio con sus tests, el endpoint, la migración, la documentación), no uno por test, y con un mensaje específico. Como guía, **alrededor de 10 por Tarea**; pueden ser más si la Tarea lo pide (por ejemplo 15): no es un techo obligatorio. Lo que se evita es una rama con 20 o 30 commits chicos. Los commits chicos de TDD son de trabajo: antes del push se unifican con su cambio. **Antes de reorganizar, un agente distinto del que programó verifica sobre esos commits de trabajo que el ciclo de TDD haya ocurrido** (`verificar-tdd`), y su veredicto queda escrito en el Merge Request y en el comentario de cierre de la Tarea. El historial de trabajo, con los `test(rojo)`, se guarda en la rama de respaldo `evidencia/<ID>` y **se sube a `origin`**, sin Merge Request, para que quien revisa pueda ver el rojo. La rama de la Tarea se mergea a `develop` sin squash. **Las dos ramas no se borran del servidor hasta que termina el sprint** ([[orquestador-desarrollo]]).






## Merge Requests (MR) e Integración Continua

* **Título del MR:** Debe ser descriptivo, en español, e incluir el ID de la tarea. Ej: `Draft: feat: [AB#1001] Creación de endpoint de alta`.
* **Cierre automático de tickets:** ⚠ **PENDIENTE DEFINICIÓN**. Aún no está definido en el flujo del equipo si utilizar las palabras clave en la descripción del MR (ej: `Fixes AB#ID`) para mover automáticamente el ticket a *Closed* o a un estado intermedio de validación (un estado intermedio de validación, si el tablero lo tiene).
* ⚠ A verificar con Infraestructura/DevOps: que las menciones `AB#ID` y `Fixes AB#ID` funcionen desde GitLab.
* **README.md del repositorio:** El `README.md` de la raíz de cada repositorio de código documenta lo necesario para levantar y probar el proyecto: dependencias a instalar con versión, variables de entorno y comandos. Todo cambio que agregue o modifique cualquiera de esas cosas actualiza el README en el mismo Merge Request.

