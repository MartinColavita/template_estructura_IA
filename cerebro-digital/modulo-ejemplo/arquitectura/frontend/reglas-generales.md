---
id: reglas-generales
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: "Frontend — reglas generales (duras, numeradas)"
description: Las reglas que se le pasan a un worker de front como reglas duras y que el verificador chequea una por una. Plantilla a completar con el stack del front.
tags: [arquitectura, frontend, reglas, modulo-ejemplo]
last_updated: 2026-10-22
author: "equipo"
---

# Frontend — reglas generales

> Numeradas y cortas a propósito: cada una se copia **tal cual** en la misión del worker y el
> verificador da **un veredicto por regla** (control 5-quater de [[orquestador-desarrollo]]).
> Valen además C3 a C6 de la tabla del orquestador (idioma de los nombres, documentación
> resumida en español, un solo contrato, el Cerebro manda).

## Reglas que vienen con el template

1. **El contrato manda.** Toda llamada a la API se escribe y se simula a partir del `openapi.yaml` consolidado por el back; una respuesta inventada es HALLAZGO.
2. **Sin lógica en la vista.** La vista muestra; la lógica (datos, estado, cálculos, formateos) vive en piezas probables sin renderizar.
3. **Límites entre partes.** Una funcionalidad no importa el interior de otra: sólo su punto de entrada público. Un import cruzado es HALLAZGO.
4. **Cada estado del contrato tiene UI.** Vacío, cargando, cada `4xx` y cada `5xx` declarado se muestran y se prueban.
5. **Accesible por construcción.** Todo se puede hacer con teclado, todo elemento tiene nombre, el color nunca va solo (ver `accesibilidad.md` de la skill `desarrollo`).
6. **Sin valores hexadecimales a mano.** Los colores salen de los tokens del design system (`diseno/diseno-sistema.md`).
7. **Sin datos sensibles** en código, fixtures, simulaciones ni capturas: marcadores `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.

## Reglas propias del stack (⚠ a completar con `DEC-003`)

8. ⚠ <estructura de carpetas de una funcionalidad y qué archivo lleva cada cosa>
9. ⚠ <cómo se nombran componentes, hooks/controladores y utilidades>
10. ⚠ <estilado: sistema de clases, nomenclatura, qué está prohibido>
11. ⚠ <estado compartido: qué va al estado global y qué no>
12. ⚠ <tests: qué prueba cada pieza, qué se simula, cobertura exigida por el build>
