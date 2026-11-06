---
id: index-frontend
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "Arquitectura del frontend — índice"
description: Qué leer antes de tocar qué en el front: stack, estructura, flujo de datos y cómo se trabaja. Se completa cuando el equipo decide el stack del front (DEC-003).
tags: [arquitectura, frontend, indice, modulo-ejemplo]
last_updated: 2026-10-22
author: "equipo"
---

# Arquitectura del frontend — índice

> Pilar **opcional**: existe si el proyecto tiene front. Es lo que reciben, por ruta absoluta,
> los workers que programan una Tarea de front ([[orquestador-desarrollo]]), junto con
> [[reglas-generales]]. Lo que esté `⚠` el verificador lo reporta `SIN DATOS`, nunca OK.

## Qué leer antes de tocar qué

| Si vas a tocar… | Leé primero |
|---|---|
| Cualquier cosa | [[reglas-generales]] (las reglas duras, numeradas) |
| Una pantalla o componente | ⚠ `components.md` <completar: cómo se organiza un componente, su lógica y su estilado> |
| La llamada a la API | ⚠ `http.md` <completar: cómo se consume el contrato `openapi.yaml` y cómo se simula> |
| El estado compartido | ⚠ `state.md` <completar> |
| Validaciones de formulario | ⚠ `validation.md` <completar> |
| Tests | ⚠ `testing.md` <completar: qué prueba cada pieza, con qué runner; coherente con `tdd-stack-front.md` de la skill `desarrollo`> |

## Stack

⚠ Lo fija [[decisiones#DEC-003]]. Hasta entonces, ninguna skill asume un framework.

## Estructura

⚠ <completar: carpetas de primer nivel, dónde vive una funcionalidad, qué puede importar a qué
(los límites entre partes del front son lo que mira `auditar-codigo`)>.

## Cómo se trabaja

- Test-primero con evidencia del rojo (`guiar-tdd` de `front/`), verificación independiente (`verificar-tdd`).
- El contrato `openapi.yaml` manda: la API se simula a partir de él, nunca se inventa la forma de una respuesta.
- ⚠ <completar: los comandos de lint, test y build que tienen que pasar antes del Merge Request>.
