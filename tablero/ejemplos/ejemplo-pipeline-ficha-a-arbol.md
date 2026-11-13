---
id: ejemplo-pipeline-ficha-a-arbol
tipo: ejemplo
estado: F-Draft
modulo: integracion-azure-devops
title: "Ejemplo — del Cerebro Digital al backlog (ficha → árbol de tickets → histórico)"
author: equipo
tags: [ejemplo, pipeline, cerebro-digital, azure-devops, trazabilidad, end-to-end]
last_updated: 2026-08-26
---

# Ejemplo — del Cerebro Digital al backlog (end-to-end)

Muestra la **capacidad nueva** completa: partir de una **ficha del Cerebro Digital**, derivar el **árbol de tickets** con el mapeo OKF→ADO, crearlos por MCP con confirmación, y dejar la **traza doc↔ticket por referencia**. Agnóstico; el dominio es solo un recuadro "Ejemplo (genérico)".

Ver también: [[pipeline-doc-a-tickets]] · [[sincronizar-backlog]] · [[organizacion-y-trazabilidad]]

---

## 1. Punto de partida — ficha funcional (Cerebro Digital)

Una ficha **validada** del Cerebro Digital (`cerebro-digital/`, recortada):

```markdown
# Módulo <tema> — <asunto funcional>            estado: F-Verified · tema: <tema>

## Propósito
<qué resuelve el módulo, en 1-2 frases>

## Flujos
- Flujo A: <flujo de usuario completo 1>
- Flujo B: <flujo de usuario completo 2>

## Reglas de negocio
### RN-<MODULO>-001 — <regla 1>
### RN-<MODULO>-002 — <regla 2>

## Derivación a backlog          # ← lo cierra la CURACIÓN; fija el árbol 1:1
### Slices [Épicas]
- [S-01] <vertical slice/dominio>
### Capacidades [Features]
- [C-01] <capacidad/caso de uso>  · Slice: S-01
### Flujos [Historias]
- [F-01] Flujo A  · Capacidad: C-01
- [F-02] Flujo B  · Capacidad: C-01

## Tickets derivados (Azure)
(pendiente — se completa al bajar al board)
```

El bloque **`## Derivación a backlog`** es el contrato de conteo: la curación lo cierra y un humano lo valida. El funcional **no** lo escribe — su entrada es texto libre; la estructura la pone la curación. **El árbol de abajo es una copia 1:1 de este bloque** (2 flujos enumerados → 2 Historias, ni más ni menos).

## 2. La IA propone el árbol (mapeo OKF → ADO)

Con la skill [[sincronizar-backlog]], la IA copia **1:1** el bloque `## Derivación a backlog` y **propone** (nada creado aún) — 1 Épica (=S-01) + 1 Feature (=C-01) + 2 Historias (=F-01, F-02):

```
Épica: <vertical slice/dominio>                   [tag: <tema>] [Doc fuente: cerebro-digital/.../<ficha>.md]
├─ Feature: <capacidad/caso de uso>               [Parent: Épica]
│  ├─ Historia: <Flujo A>                          [Parent: Feature] [Related: Historia <Flujo B>] [RN-<MODULO>-001]
│  └─ Historia: <Flujo B>                          [Parent: Feature]                                [RN-<MODULO>-002]
└─ (Tareas técnicas: las crean los devs al desglosar cada Historia)
```

Cada nodo con: título, tipo justificado, criterios en Gherkin español referenciando las `[RN-…]`, **etiqueta temática** `<tema>` (sin prefijo), **relaciones** propuestas por título (los `#ID` van `⚠` hasta resolverse por MCP) y **Documento fuente** = la ruta de la ficha. Datos duros faltantes (sprint, versión) → `⚠`.

## 3. Confirmación humana

La IA muestra el árbol y pregunta *"¿Creo estos work items con estos enlaces?"*. El humano confirma el árbol (que salió **1:1** de la ficha; no re-decide granularidad acá — esa decisión ya la cerró la curación al enumerar), resuelve los `⚠` (sprint, versión) y da el **"dale"**. **Hasta acá no se tocó Azure.**

## 4. Alta por MCP y registro de la traza

Con el "dale", la IA crea por MCP (`create_work_item` + `manage_work_item_link`) y obtiene los `#ID`. Luego:

- **En la ficha** (`cerebro-digital/.../<ficha>.md`), completa el bloque:
  ```
  ## Tickets derivados (Azure)
  #<ID-épica>, #<ID-feature>, #<ID-historia-A>, #<ID-historia-B>
  ```
- **En cada ticket**, la línea `Documento fuente: cerebro-digital/.../<ficha>.md`.
- **En el historial** (`historial/INDICE.md`), una **fila** (log resumido, por referencia):
  ```
  | AAAA-MM-DD | historia | <tema> | #<ID-épica>..#<ID-historia-B> | cerebro-digital/.../<ficha>.md | <resumen de una línea> | 5 | registrado |
  ```
  El `.md` detallado se crea solo si el ticket se promueve a `gold`.

Ninguno copia el contenido de la ficha ni de los tickets: **enlazar, no copiar**. La traza queda viva en los dos sentidos.

---

> **Ejemplo (genérico)** — ilustrativo.
> Ficha `cerebro-digital/.../reservas.md` (tema `reservas`, validada). La IA propone: **Épica** "Gestión de reservas" → **Feature** "Alta y cancelación de reservas" → **Historias** "Crear una reserva" `[RN-RESE-01]` (Related con la de cancelación) y "Cancelar una reserva" `[RN-RESE-02]`, todas con tag `reservas` y `Documento fuente: cerebro-digital/.../reservas.md`. El equipo confirma y resuelve el sprint (`⚠`); la IA crea por MCP, obtiene `#4821..#4824`, los anota en la ficha (`Tickets derivados`) y agrega la fila en `historial/INDICE.md` con `documento_fuente` + `tickets_derivados` + resumen. Sin copiar contenido.
