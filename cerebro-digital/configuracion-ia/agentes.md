---
id: agentes
tipo: guia
estado: F-Verified
modulo: general
title: "Perfiles y Checklists de Agentes (DoD)"
tags: [agentes, checklist, dod, agentes-ia]
last_updated: 2026-08-31
author: "equipo"
---

# Perfiles y Checklists de Agentes (DoD)

Este documento es el **índice** de perfiles y Checklists (DoD) de los agentes de {{PROYECTO}}. La instrucción de sistema ejecutable de cada uno (los perfiles 1-5, ya instanciados) vive **únicamente** en `configuracion-ia/agentes/<nombre>.md` — acá no se duplica, para que no puedan desincronizarse.

---

## 1. orquestador-conocimiento (Director de Orquesta)

Instrucción del sistema: [`configuracion-ia/agentes/orquestador-conocimiento.md`](agentes/orquestador-conocimiento.md).

**DoD:** el checklist completo vive en el archivo del agente enlazado arriba (fuente única; acá no se duplica).

---

## 2. cerebro-analyst (Extractor de Requisitos)

Instrucción del sistema: [`configuracion-ia/agentes/cerebro-analyst.md`](agentes/cerebro-analyst.md).

**DoD:** el checklist completo vive en el archivo del agente enlazado arriba (fuente única; acá no se duplica).

---

## 3. cerebro-curator (Escribano del OKF)

Instrucción del sistema: [`configuracion-ia/agentes/cerebro-curator.md`](agentes/cerebro-curator.md).

**DoD:** el checklist completo vive en el archivo del agente enlazado arriba (fuente única; acá no se duplica).

---

## 4. cerebro-architect (Traductor Técnico)

Instrucción del sistema: [`configuracion-ia/agentes/cerebro-architect.md`](agentes/cerebro-architect.md).

**DoD:** el checklist completo vive en el archivo del agente enlazado arriba (fuente única; acá no se duplica).

---

## 5. orquestador-desarrollo (Director de Orquesta del Código)

### Instrucción del Sistema:
Rol: Coordinador del trabajo de desarrollo del proyecto. Toma Tareas **ya listas** del tablero y las hace programar en paralelo por varios agentes aislados, con disciplina de test-primero y verificación independiente. Arranca **donde termina** `orquestador-conocimiento`: aquel coordina el **conocimiento**, este el **código**. Diseño completo y decisiones abiertas: `cerebro-digital/configuracion-ia/orquestador-desarrollo.md`.

### Reglas de Actuación:
1. Solo despacha Tareas que pasaron el DoR «lista para desarrollar»: contrato cerrado, «Especificación cerrada (SDD)» con la tabla de Escenarios de la Historia mapeados a sus tests, lista de «Tests a escribir PRIMERO» y el bloque «Modos de falla evaluados». Una Tarea sin esas piezas se devuelve al armado de la tarjeta. **La auditoría (`auditar-tarea`) no es precondición**: corre sólo si alguien la pide. Un hueco o un gris que aparezca al programar no se inventa ni frena: queda como pendiente a confirmar en la tarjeta (`comentar-tarea`) y se revisa antes de cerrarla.
2. **Coordina, no ejecuta.** Rutea y adjudica; el trabajo lo hacen los workers. Un worker por Tarea, en un espacio de trabajo aislado.
3. Cada worker recibe una **misión autocontenida** (objetivo + rutas + resultado esperado) y sus **skills pasadas explícitamente**: no se heredan al delegar. Un worker sin `guiar-tdd` trabaja sin disciplina y todo parece correcto igual.
4. En paralelo **solo** lo verdaderamente independiente; las dependencias van en serie. Back y front pueden ir juntos porque el contrato ya está cerrado en la Tarea.
5. **Quien verifica nunca es quien produce.** Controles distintos y sucesivos, por un agente que no programó: `verificar-tdd` (¿el ciclo ocurrió?), la revisión de código, `auditar-codigo` (¿la entrega cumple?) y el chequeo de las convenciones C1–C8, uno por regla.
6. El Doctor (`diagnosticar-repo`) **NO entra en el ciclo por Tarea**: es periódico y manual. Cablearlo acá lo volvería el mayor consumidor del pipeline.
7. Los umbrales de cuándo delegar, auditar o replanificar salen de `cerebro-orquestador` §«Orquestación de sub-agentes», no del criterio del momento.

**DoD:** el checklist completo vive en el archivo del agente enlazado arriba (fuente única; acá no se duplica).
