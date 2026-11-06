---
id: esqueleto-proyectos
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: Especificación de Esqueletos y Estructuras Base
description: Estructura base de los repositorios de código (back, front y despliegue), convenciones de código y su bloque de derivación a backlog. Se completa cuando el equipo decide el stack (DEC-003).
tags: [arquitectura, esqueleto, repositorios, convenciones, modulo-ejemplo]
last_updated: 2026-10-22
author: "equipo"
---

# Especificación de Esqueletos y Estructuras Base

> Plantilla. Es el documento que reciben, **por ruta absoluta**, los workers que programan: de acá
> salen las convenciones que el verificador chequea una por una (C1 a C8 de
> `configuracion-ia/orquestador-desarrollo.md`). Lo que esté `⚠` el verificador lo reporta
> `SIN DATOS`, nunca OK. Se completa con [[decisiones#DEC-003]].

## 1. Contexto y objetivos técnicos

<completar: qué se va a construir, con qué restricciones de la organización (red, registry
interno, autenticación corporativa, plataforma de despliegue), y qué queda fuera.>

### Repositorios objetivo

| Repositorio | Carpeta donde se clona | Qué contiene | Estado |
|---|---|---|---|
| `<repo-back>` | `back/<repo-back>` | El back: módulos de dominio ([[decisiones#DEC-002]]) | ⚠ nombre a definir |
| `<repo-front-1>` | `front/<repo-front-1>` | Una aplicación de front | ⚠ nombre a definir |
| `<repo-infra>` | fuera de este repositorio | Configuración de despliegue | ⚠ a definir si existe |

## 2. Esqueleto del front

<completar cuando se decida el stack: estructura de carpetas, cómo se organiza una pantalla y
su lógica, cómo se simula la API desde el contrato `openapi.yaml`, configuración base, comandos
de lint/test/build.>

### Configuración base

- ⚠ <versiones fijadas (se pinnean al crear el primer repo)>
- ⚠ <registry/proxy de dependencias, si la organización lo tiene>
- ⚠ <linter, formateador y runner de tests, exigidos por el build>

## 3. Esqueleto del back

### Estructura del back (módulos y capas)

La estructura es la de [[decisiones#DEC-002]]: un paquete/carpeta por módulo de dominio con
`api/`, `application/`, `domain/`, `exceptions/` e `infra/`, más `shared/`. Al materializarla:

```
<paquete-base>/
├─ shared/{api/error, exceptions, infra/config}/
├─ <modulo-a>/{api, application, domain, exceptions, infra}/
└─ <modulo-b>/{api, application, domain, exceptions, infra}/
```

- `api/`: un adaptador HTTP por recurso o sub-recurso con funcionalidad propia (no por front); DTOs de entrada y salida en `api/dto/`.
- `application/`: `usecase/` (una clase por caso de uso), `gateway/` (interfaces a sistemas externos), `repository/` (interfaces a la base propia).
- `domain/`: entidades, valores y reglas; plano hasta que crece, después por concepto.
- `infra/`: `client/<sistema>/` y `client/mock/`, `repository/`, `config/`.
- Tests: los dobles y datos de ejemplo reusados van en una carpeta `support/` del módulo.

⚠ <completar: nombre del paquete base, qué test para qué capa, cómo se verifica la estructura
en el build (fitness function), migraciones de base por módulo>.

### Configuración base

- ⚠ <versión del lenguaje y del framework; modo de ejecución>
- ⚠ <extensiones/librerías obligatorias: documentación de la API, métricas, trazas, logs estructurados, chequeos de salud>
- ⚠ <umbral de cobertura exigido por el build>

### Convenciones de código

Son las reglas duras que reciben los que programan. Las C1 a C7 vienen definidas en
`configuracion-ia/orquestador-desarrollo.md` §«Convenciones del Cerebro» (estructura por módulo,
errores centralizados, idioma de los nombres, documentación resumida en español, un solo contrato,
el Cerebro manda, una Tarea un módulo). Acá se completa **C8**:

- ⚠ **C8 — convenciones propias del stack:** <anotaciones permitidas y prohibidas, inyección de
  dependencias, cómo se hacen las tareas programadas, política de librerías de utilidad, estilo de
  los tipos de datos inmutables>. Cuando se decida, se copia en la tabla del orquestador.

## 4. Configuración de entornos y despliegue

<completar: ambientes, artefactos, imágenes de contenedor, variables de entorno documentadas,
secretos por variable de entorno (nunca en el repo), chequeos de salud expuestos, qué frena el
pipeline (build, tests, cobertura, análisis estático, SAST, contrato, dependencias).>

## Derivación a backlog

> ⚠ Bloque a validar por una persona antes de derivar. Estructura esperada: 1 Épica por slice,
> 1 Feature por capacidad, 1 Historia por flujo. Las Tareas no se enumeran acá.

**Etiqueta temática:** `<etiqueta-tematica>`

### Slices [Épicas]
- [S-01] Esqueleto base de los repositorios

### Capacidades [Features]
- [C-01] Esqueleto del back · Slice: S-01
- [C-02] Esqueleto del front · Slice: S-01
- [C-03] Entornos y despliegue · Slice: S-01

### Flujos [Historias]
- [F-01] <crear el repositorio del back con su estructura por módulos, build, tests y contrato> · Capacidad: C-01 · Reglas: DEC-002
- [F-02] <crear el repositorio del front con su estructura, lint, tests y simulación del contrato> · Capacidad: C-02 · Reglas: DEC-002
- [F-03] <pipeline con las puertas que frenan y despliegue al primer ambiente> · Capacidad: C-03 · Reglas: DEC-003

**Conteo:** 1 Épica + 3 Features + 3 Historias = **7 work items**, 0 Tareas.

## Tickets derivados

| Fecha | Tipo | #IDs Azure | Resumen |
|---|---|---|---|

## Dudas y Preguntas

- ⚠ Ver [[decisiones#DEC-003]] y `pendientes.md`.
