---
id: index-funcional
tipo: indice
estado: F-Draft
modulo: modulo-ejemplo
title: "01 - Funcional (modulo-ejemplo)"
description: Índice del pilar funcional — reglas de negocio, glosario de dominio y flujos de usuario del módulo.
tags: [modulo-ejemplo, funcional, indice, okf]
last_updated: 2026-10-22
author: "equipo"
---

# 01 - Funcional (modulo-ejemplo)

Este directorio es el **Manual de Negocio** del módulo. Acá documentamos el *qué* y el *para qué*
construimos el software, en el lenguaje del dominio.

## ¿Qué vas a encontrar acá?
* **Reglas de negocio:** lógica pura, validaciones y restricciones del dominio (`RN-MOD-nnn`).
* **Glosario de dominio:** definición de términos (lenguaje ubicuo).
* **Flujos y pantallas:** descripción de los casos de uso y la navegación del usuario, una ficha por flujo con su bloque `## Derivación a backlog`.

> **Regla de oro:** si el documento habla de bases de datos, librerías o código, NO va acá. Esta carpeta habla el idioma de negocio.

## Contenido de esta carpeta

* **`plantilla-ficha-flujo.md`**: el molde de una ficha de flujo derivable a backlog. Se copia por tema.
* <una línea por ficha: nombre, qué cubre, estado (`F-Draft`/`F-Verified`) y si su bloque de derivación está validado>

> **Sistema vigente vs. módulo nuevo:** si el proyecto reemplaza un sistema que hoy está en producción, no confundir las reglas del sistema vigente con las del módulo nuevo: se dice en cada ficha cuál describe.
