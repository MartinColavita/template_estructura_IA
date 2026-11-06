---
id: checklist-bug
tipo: checklist
estado: F-Draft
modulo: integracion-azure-devops
title: "Checklist de calidad — Bugs"
author: equipo
tags: [azure-devops, checklist, calidad, bug, defecto, qa]
last_updated: 2026-08-26
---

# Checklist de calidad — Bugs

Lista accionable para verificar, antes de pegar en Azure DevOps, que un Bug es reproducible, está bien tipificado y separa claramente lo esperado de lo obtenido — sin los vicios de los bugs "Ver adjunto". Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[bug]] · [[mapa-campos-azure]] · [[ejemplo-bug]]

---

## Cómo usar este checklist

1. Pegá el bug POBRE junto con este checklist y el conocimiento de dominio del toolkit.
2. Recorré cada casilla. Todo lo que quede `[ ]` es un hueco a completar antes de crear el Bug.
3. En Azure, **casi todo el contenido del bug va en un solo campo**: **Pasos para reproducir** (HTML). La Descripción casi no se usa. Ver [[mapa-campos-azure]].
4. Objetivo: que cualquier bug —lo escriba QA u otro rol— tenga la **misma calidad** (Ambiente / Versión / Pasos / Esperado / Obtenido / Evidencia).

---

## 1. Título

- [ ] Formato **`Modulo - Contexto: sintoma`**.
- [ ] **Sin typos** (un título con "se dehabilita" es justo lo que NO hay que hacer).
- [ ] Describe el **síntoma observable**, no la causa supuesta ni "no anda".
- [ ] Prefijo de módulo **consistente** con el tablero.

## 2. Ambiente

- [ ] Indica el **ambiente** exacto donde ocurre: DESA / TEST / PREPROD / PROD.
- [ ] **No mezcla ambientes** en el mismo reporte. Si ocurre en varios, se dice explícitamente y se ordena, o se abren bugs separados.
- [ ] Si es específico de un **canal**, **rol** o **configuración**, lo aclara.

## 3. Versiones

- [ ] **Versión Frontend**, formato `<versión>`.
- [ ] **Versión Backend** cuando aplica, formato `<versión>`.
- [ ] Si no se sabe la versión exacta, se marca **(pendiente)** (no se inventa un número).

## 4. Fecha y contexto

- [ ] **Fecha (y hora si importa)** en que se detectó/reprodujo.
- [ ] Rol/usuario con el que se reprodujo — **sin** credenciales reales.
- [ ] Datos de configuración relevantes (navegador si es de UI, permisos/rol, tipo de registro involucrado).

## 5. Precondiciones

- [ ] Lista el **estado de partida** necesario para reproducir (registro en cierto estado, entidad de cierto tipo, condición previa).
- [ ] Las precondiciones usan **marcadores** (`<persona>`, `<documento>`, `<identificador>`), nunca PHI real.

## 6. Pasos para reproducir

- [ ] Pasos **numerados**, en orden, **reproducibles** por un tercero sin conocimiento previo del bug.
- [ ] Cada paso es una **acción concreta**.
- [ ] **No** es "Ver adjunto" ni un texto en flujo de conciencia. El adjunto es **apoyo**, nunca el reemplazo de los pasos escritos.
- [ ] Si el bug es intermitente, se indica la **frecuencia** (siempre / X de cada Y veces) y qué condiciones lo disparan.

## 7. Esperado vs. Obtenido vs. Por qué (SEPARADOS)

- [ ] Hay un bloque **Resultado esperado** claro (qué debería pasar, según la spec / comportamiento correcto).
- [ ] Hay un bloque **Resultado obtenido** claro (qué pasa realmente).
- [ ] Hay un bloque **Por qué es un error (motivo / impacto)**: por qué lo obtenido está mal y a quién/qué afecta — no solo el síntoma.
- [ ] Si el tema tiene reglas numeradas, indica **qué `[RN-<TEMA>-NN]` se rompe** (ver [[organizacion-y-trazabilidad]] §4).
- [ ] Los tres están **separados y etiquetados**, no mezclados en un párrafo.
- [ ] El "por qué" funcional no se confunde con la **causa técnica** (esa, si va, es hipótesis **(pendiente)** en Observaciones).
- [ ] El esperado se apoya, si se puede, en la spec funcional o en el comportamiento previo.

## 8. Gravedad y Prioridad (coherentes)

- [ ] **Gravedad** asignada según impacto real:
  - `1 - Critical`: impide operar / caída / pérdida de datos / bloqueo total de un flujo troncal.
  - `2 - High`: funcionalidad importante rota sin solución alternativa razonable.
  - `3 - Medium`: falla con solución alternativa, o afecta a pocos casos.
  - `4 - Low`: cosmético, textual, menor.
- [ ] **Prioridad (1–4)** asignada y **coherente** con la gravedad y la urgencia (una gravedad 1 no debería quedar con prioridad baja sin justificación).
- [ ] Si gravedad y prioridad no coinciden, hay una **justificación** en las observaciones.

## 9. Evidencia (como apoyo, no como reemplazo)

- [ ] Adjunta **evidencia**: captura, video, log, respuesta del endpoint, traza del error.
- [ ] La evidencia **complementa** los pasos escritos; el bug se entiende **sin** abrir los adjuntos.
- [ ] **PHI enmascarada** en toda la evidencia: tapar nombres, documentos, credenciales, diagnósticos, teléfonos en capturas y logs. Nunca pegar valores reales.
- [ ] Si aplica, incluye **Información del sistema** (la completa la extensión del navegador de Azure) y el `traceId`/correlación del error.

## 10. Observaciones

- [ ] Notas útiles: solución alternativa temporal, alcance (¿un usuario, un rol, todos?), si es regresión (desde qué versión), bugs/tarjetas relacionadas.
- [ ] Hipótesis de causa marcada como hipótesis (**(pendiente) posible causa**), no como hecho, para no sesgar a quien lo investigue.

## 11. Idioma y PHI (reglas de oro — no negociables)

- [ ] **Todo en español (Argentina).** Cero inglés en prosa, títulos o viñetas.
- [ ] **Sin PHI**: ni en título, pasos, esperado/obtenido, observaciones ni evidencia. Solo marcadores `<...>` y descripción de estructura.

## 12. Organización y trazabilidad (tags · relaciones · documento fuente)

- [ ] **Etiqueta temática** presente (`<tema>`, **sin prefijo**) y escrita igual que el resto de los tickets del tema (ver [[organizacion-y-trazabilidad]] §1).
- [ ] **Relacionadas (Related)**: enlazado a la UH/bug del mismo tema (suele ser la UH cuyo comportamiento rompe); `#ID` `⚠` a confirmar o resuelto por MCP.
- [ ] **Documento fuente** enlazado como ruta/link (no se copió el contenido).

---

## Veredicto rápido

> Un bug está listo para Azure cuando otra persona puede **reproducirlo siguiendo solo los pasos escritos**, entiende **qué debería pasar y qué pasa** por separado, y la **gravedad/prioridad** reflejan el impacto real — todo **sin** abrir un solo adjunto y **sin** un solo dato real de una persona.

---

## Ejemplo (genérico)

> Recuadro ilustrativo. La gravedad se lee en clave del dominio: `1 - Critical` = impide operar el flujo troncal del negocio (el proceso principal, sin solución alternativa). En cada proyecto, el criterio de "flujo troncal" cambia, pero el valor del desplegable de Azure es el mismo.
