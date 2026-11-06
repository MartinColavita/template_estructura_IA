---
id: extraccion-reuniones-readme
tipo: guia
estado: F-Verified
modulo: modulo-ejemplo
title: "Extracciones de reunión — insumo crudo"
description: Qué va en esta carpeta, cómo se nombra cada archivo y por qué no es conocimiento consolidado.
tags: [reuniones, extraccion, insumo]
last_updated: 2026-10-22
author: "equipo"
---

# Extracciones de reunión

Acá viven las **extracciones** de las reuniones del equipo: lo que la skill `cerebro-meet-analyst`
saca de una transcripción, **ítem por ítem confirmado por una persona**. Son **insumo crudo**, no
conocimiento consolidado: por eso no están en `funcional/`, `metodologia/` ni `arquitectura/`.

- **Nombre:** `meet-<tipo>-YYYYMMDD.md` (`tipo`: `dominio`, `arquitectura`, `funcional`, `revision`).
- **Frontmatter:** `tipo: extraccion-reunion`, `estado: F-Draft`, `modulo: modulo-ejemplo`, `fuentes: [...]`.
- **Qué trae:** propósito y asistentes, decisiones (`DEC-nnn`), reglas (`RN-MOD-nnn`), dolores, hipótesis,
  contradicciones con el OKF y dudas (`P-nnn`). El molde exacto está en la skill.
- **Qué pasa después:** lo validado se **promueve** al pilar que corresponda (`decisiones.md`, la ficha
  funcional, `pendientes.md`) y el archivo de la reunión agrega una tabla de consolidación («dónde quedó
  cada ítem»). El archivo no se borra: es el registro de la fuente.
- **La transcripción en bruto nunca se versiona** (`*.docx` y `scratch/` están en el `.gitignore`):
  puede traer nombres y datos de personas.
