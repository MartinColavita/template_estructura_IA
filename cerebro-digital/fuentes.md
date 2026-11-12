---
id: fuentes
tipo: fuentes
estado: F-Draft
modulo: general
title: Registro de Fuentes de Información y Trazabilidad
description: Catálogo oficial de documentos de origen que alimentan el Cerebro Digital de {{PROYECTO}}.
tags: [okf, fuentes, trazabilidad]
last_updated: 2026-10-22
author: "equipo"
---

# Registro de Fuentes de Información — {{PROYECTO}}

Este documento actúa como el **índice de trazabilidad** del Cerebro Digital. Cada regla de negocio, flujo o componente visual documentado en el OKF debe poder rastrearse hasta uno de los documentos oficiales listados acá.

---

## 📂 1. Catálogo de documentación funcional de origen

| Código | Documento de origen | Versión | Autor / Origen | Ubicación oficial | Mapeo en el Cerebro Digital (OKF) |
|--------|---------------------|---------|----------------|-------------------|----------------------------------|
| **[DOC-01]** | <nombre del documento funcional> | <vX.Y> | <equipo que lo entregó> | <link o ruta del original> | `[[contexto]]`, `[[index]]` |

Los documentos en bruto viven en `documentos/` (no se generan: se reciben) y **no** se
versionan: acá queda su código, su versión y su ubicación oficial. Las transcripciones de reunión
tampoco; su extracción sí, en `modulo-ejemplo/extraccion-reuniones/`.

---

## 🔗 2. Trazabilidad de reglas de negocio a fuentes

A continuación se detalla qué partes del Cerebro Digital responden a qué secciones de los documentos de origen:

### 2.1 Módulo: `modulo-ejemplo`
- **<Ficha> (`modulo-ejemplo/funcional/<ficha>.md`)**:
  - Las reglas **RN-MOD-001 a RN-MOD-nnn** mapean con **[DOC-01] Sección <n>**.

### 2.2 Sistema de diseño (`diseno/`)
- **<Componente> (`diseno-sistema.md`)**: responde a **[DOC-nn] <sección>**.

---

## 🛠️ 3. Reglas de mantenimiento de fuentes

1. **Inmutabilidad de códigos**: los códigos de origen (**[DOC-01]**, **[DOC-02]**, etc.) no cambian. Si se agrega un documento nuevo, se le asigna el siguiente consecutivo.
2. **Cita en el texto**: al documentar una regla de negocio en el OKF, se incluye al final la cita a la fuente correspondiente.
   * *Ejemplo:* `El rol aprobador valida la solicitud antes de enviarla. (Fuente: [DOC-01] Sección 4.1)`
3. **Control de versiones**: si se recibe una versión nueva de un documento (ej. `[DOC-01] v2.0`), se actualiza este registro, se revisan los archivos OKF afectados y se deja asentada la revisión en `[[log]]`.
