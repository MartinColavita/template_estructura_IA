---
id: diseno-sistema
tipo: diseno
estado: F-Draft
modulo: diseno
title: "Sistema de Diseño Visual — {{PRODUCTO}}"
tags: [diseño, ui, componentes, tokens]
last_updated: 2026-10-22
author: "equipo"
---

# Sistema de Diseño Visual — {{PRODUCTO}}

Este documento especifica los tokens de diseño y los componentes de interfaz de usuario (UI)
extraídos de las pantallas y maquetas de {{PRODUCTO}}, para garantizar la consistencia visual
de los mockups y de los repositorios de código (que no viven acá — ver `DEC-001`).

> **De dónde salen los tokens.** Si el diseño se hace en Google Stitch ([[disenar-con-stitch]]), los valores
> se toman de la exportación de cada pantalla promovida y entran acá como propuesta con un «sí»; ningún
> hexadecimal queda suelto en skills ni mockups.

> **Fuente de verdad:** `cerebro-digital/configuracion-ia/skills/cerebro-mockup-design/SKILL.md` —
> este archivo es el documento **descriptivo**; el SKILL es el **prescriptivo**. Los dos tienen que
> decir lo mismo: si cambia un token, cambia en los dos.

> ⚠ Plantilla: se completa a partir de las pantallas reales o del primer mockup validado por el
> funcional. **Nunca se escribe un valor hexadecimal a mano fuera de los tokens.**

---

## 🎨 1. Paleta de colores — por orden de peso visual real

La paleta se presenta ordenada por frecuencia de uso real en el producto. Los primeros colores
son los que sostienen la interfaz; los últimos son acentos puntuales.

| # | Nombre | HEX | Rol | Frecuencia |
|---|--------|-----|-----|------------|
| 1 | **Gris de texto principal** | `<hex>` | Color de texto por defecto en toda la app (`--text-color`) | La variable más usada, por lejos |
| 2 | **Color de marca claro** | `<hex>` | Fondos suaves, resaltados, hover de botones (`--brand-soft`) | Segundo color más frecuente |
| 3 | **Blanco superficie** | `#ffffff` | Fondo de página, cards, paneles (`--surface-0`) | Base de todo el layout |
| 4 | **Gris claro superficie** | `<hex>` | Fondos alternativos, headers de tabla (`--surface-100`) | Base de todo el layout |
| 5 | **Color de marca oscuro** | `<hex>` | Botón primario, texto/borde activo, acentos (`--brand-900`) | Moderado — 1-2 elementos por pantalla |
| 6 | **Gris secundario** | `<hex>` | Texto secundario, placeholders (`--neutral-500`) | Frecuente en formularios |
| 7 | **Gris bordes** | `<hex>` | Bordes de inputs y tablas (`--neutral-200`) | Frecuente |
| 8 | **Gris divisores** | `<hex>` | Separadores (`--neutral-300`) | Frecuente |
| 9 | **Rojo error** | `<hex>` | Errores, validación inválida (`--red-600`) | Solo para error — nunca decorativo |
| 10 | **Verde éxito** | `<hex>` | Confirmaciones, estados positivos (`--green-600`) | Solo para éxito |
| 11 | **Amarillo advertencia** | `<hex>` | Advertencias, estados intermedios (`--yellow-600`) | Poco frecuente |
| 12 | **Naranja advertencia fuerte** | `<hex>` | Advertencia fuerte (`--orange-600`) | Muy poco frecuente |
| 13 | **Acento de selección** | `<hex>` | Ítem seleccionado/activo en listas de estado (`--accent-selected`), si el producto lo tiene | Uso puntual |

## 🔤 2. Tipografía

| Token | Valor | Uso |
|---|---|---|
| `--font` | `<tipografía del producto>` | Toda la interfaz |
| `--font-mono` | `SF Mono, Fira Code, Cascadia Code, Consolas, monospace` | Códigos, identificadores |

Jerarquía: título de card 1.5rem/700 · encabezado de panel 0.875rem/600 · cuerpo y tablas
0.875rem/400 · etiquetas 0.75rem/600 mayúsculas · timestamps 0.75rem/400.

## 📐 3. Radios, sombras y espaciado

| Token | Valor | Uso |
|---|---|---|
| `--radius-pill` | `999px` | Botones y switches (⚠ si el producto los usa pill) |
| `--radius-lg` | `8px` | Inputs, cards, paneles |
| `--radius-circle` | `50%` | Íconos de acción circulares |
| `--shadow-float` | `0 2px 12px rgba(0,0,0,.12)` | **Sólo** overlays flotantes (dropdowns, calendarios, menús) |
| Espaciado | pasos de `0.5rem` | Paneles ~0.5rem, cards ~1.25rem, gap entre campos 8px |

## 🧩 4. Componentes

Una entrada por componente del producto, con qué es, cuándo se usa y sus estados. Se completan
a medida que aparecen en las maquetas validadas.

| Componente | Qué es | Estados | Maqueta de referencia |
|---|---|---|---|
| Botón primario / secundario / outline | <descripción> | default, hover, deshabilitado, cargando | `entregables/disenos/<archivo>.html` |
| Input de formulario | <descripción> | vacío, con valor, inválido, deshabilitado | |
| Data grid / listado | <descripción, incluida la sintaxis de filtro si el producto la tiene> | vacío, cargando, con filas, fila seleccionada | |
| Toast / aviso | <descripción> | éxito, error, advertencia, info | |
| Modal | <descripción> | abierto, con foco atrapado | |
| Dropdown / autocomplete | <descripción> | cerrado, abierto (con `--shadow-float`), sin resultados | |

## ♿ 5. Accesibilidad mínima

- Todo se puede hacer con el teclado y se ve dónde está el foco.
- Todo elemento tiene nombre accesible; el color nunca va solo (ícono o palabra al lado).
- Contraste: texto normal 4.5:1, texto grande 3:1. Si un token de marca no llega, **se reporta**, no se acepta.
- Nada de emojis en la interfaz: iconografía SVG.

Detalle del método: `configuracion-ia/skills/desarrollo/references/metodo/accesibilidad.md`.
