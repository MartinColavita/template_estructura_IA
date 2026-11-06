---
id: checklist-epica
tipo: checklist
estado: F-Draft
modulo: integracion-azure-devops
title: "Checklist — Épica (Epic)"
author: equipo
tags: [azure-devops, epica, epic, checklist, calidad]
last_updated: 2026-09-11
---

# Checklist — Épica (Epic)

Faltaba, igual que el de Feature. La Épica es **el nodo más reutilizado de todos**: hay una por vertical slice, así que en cada re-sincronización se marca YA EXISTE y el paso de auditoría de calidad de [[cargar-a-azure]] §1c no tenía checklist que correr.

Relacionados: [[checklist-caracteristica]] · [[plantillas/epica]] · [[organizacion-y-trazabilidad]] §5

---

## Contenido propio

- [ ] **Título = el vertical slice**, y **su alcance es exactamente el del `[S-nn]`** de la ficha — ver abajo, es el punto más delicado.
- [ ] **Objetivo de negocio** y **Problema / oportunidad** escritos.
- [ ] **Alcance macro** y **Fuera de alcance**, los dos.
- [ ] **Criterios de éxito medibles**: con unidad y valor. «Mejorar la gestión» no es un criterio.
- [ ] **Riesgos y supuestos** anotados.
- [ ] **Una sola etiqueta temática** — la misma de toda la descendencia, sin versión ni producto ([[organizacion-y-trazabilidad]] §1).
- [ ] **Área de valor** puesta.

## El título tiene que decir exactamente lo que el slice abarca

- [ ] **El título NO es más amplio que el `[S-nn]` que representa.** Si la ficha declara `[S-01] Reserva de salas de reunión` y deja otro escenario explícitamente fuera, la Épica **no** se llama «Gestión de salas» a secas.

> **Por qué es el punto más delicado de todo el nivel funcional.** Una Épica con título más
> amplio que su slice es una **bomba de retardo con el gate de deduplicación**: cuando llegue
> el documento del alcance que quedó afuera, la dedup va a buscar por objetivo, va a encontrar
> esa Épica, y va a **prohibir el alta** de un slice que esa misma Épica declaró fuera de su
> alcance. El gate va a funcionar perfecto y va a producir el resultado equivocado — y el
> síntoma («ya existe, no lo creo») se lee como si estuviera todo bien.

- [ ] **Si el título quedó amplio y la Épica ya está creada**, no se renombra en silencio: se anota el desvío y se pregunta. Renombrar un nodo con hijos afecta la traza de todo el árbol.

## Vocabulario que heredan las hijas

- [ ] **Roles del slice** nombrados igual que en el Cerebro.
- [ ] **Estados del dominio** que el slice maneja, con su nombre exacto.
- [ ] Lo que no exista todavía va `⚠` y se pregunta. **No se inventa un nombre**: acá se propaga a Features, Historias, Tareas y tests.

## Cierre contra la ficha y las hijas

- [ ] **Rastrea a un `[S-nn]` concreto** de la ficha fuente.
- [ ] **Hay una Épica por `[S-nn]`, ni una más.** Default: **1**. Crear más de una exige que la ficha declare más de un slice ([[organizacion-y-trazabilidad]] §5).
- [ ] **Cada `[C-nn]` del slice tiene su Feature hija**, y la tabla «Historias / Características hijas candidatas» coincide con lo realmente creado (por `#ID`).
- [ ] **Documento fuente** como link, y **fila en [[historial/INDICE]]**.

---

## Veredicto

| Resultado | Qué habilita |
|---|---|
| Todas tildadas | La Épica está en condiciones de recibir Features |
| Título más amplio que el slice | **Frenar y preguntar.** Es el hallazgo caro: rompe la dedup a futuro, no hoy |
| Falta vocabulario | Se completa antes de crear las hijas: acá se multiplica por todo el árbol |

> No reemplaza a [[auditar-historia]] ni a [[auditar-tarea]]: cada nivel se puede auditar, a pedido, en su turno.
