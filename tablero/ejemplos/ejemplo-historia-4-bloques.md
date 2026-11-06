---
id: ejemplo-historia-4-bloques
tipo: ejemplo
estado: F-Draft
modulo: integracion-azure-devops
title: "Ejemplo (gold) — Historia de usuario con los 4 bloques"
author: equipo
tags: [ejemplo, historia-de-usuario, gherkin, casos-de-uso, reglas-de-negocio, okf]
last_updated: 2026-10-22
---

# Ejemplo (gold) — Historia con los 4 bloques

Modelo de una **Historia de usuario completa** con los **4 bloques** que pide el equipo (Funcionalidad · Criterios · Reglas de negocio con referencia al OKF · Casos de uso), en Gherkin español y con la línea de **Documento fuente**, para que sirva **igual a Desarrollo y a Testing**. Dominio de ejemplo inventado y claramente ilustrativo (reserva de salas de reunión); reemplazar por el real. Molde: [[plantillas/historia-de-usuario]].

---

## Título
`Reserva de salas: cancelar en serie las ocurrencias futuras de una reserva periódica`

## Descripción (Bloques 1, 3 y 4 + Documento fuente)

### (1) Funcionalidad / Historia de usuario
**Contexto:** hoy, para cancelar una reserva periódica (p. ej. la reunión semanal de un equipo), el asistente de recepción cancela ocurrencia por ocurrencia; es lento y se saltean ocurrencias por error.
**Como** asistente de recepción
**quiero** cancelar de una vez todas las ocurrencias futuras de una reserva periódica
**para** liberar la sala sin dejar ocurrencias huérfanas y sin cargar una por una.
**Alcance:** cancelación de las ocurrencias **futuras** (no realizadas) de una reserva periódica desde la pantalla de reservas; registro del motivo de cancelación.
**Fuera de alcance:** cancelar ocurrencias ya **realizadas**; cancelación pedida por el solicitante `<persona>` desde el autoservicio (es otra Historia, Related).

### Datos y estados (funcional)
- **Campos / datos:** Motivo de cancelación (obligatorio, del **catálogo de motivos**) — se registra en cada ocurrencia cancelada. `[RN-MOD-002]`
- **Campos / datos:** Solicitante de la reserva (`<persona>`, identificado por `<documento>`) — solo se muestra, no se edita en esta Historia.
- **Estados y transiciones:** Reservada → Cancelada (**permitida**, con motivo) `[RN-MOD-001]` · Realizada → Cancelada (**bloqueada**; la ocurrencia no se toca) `[RN-MOD-001]`

### (3) Reglas de negocio (con referencia al OKF)
- `[RN-MOD-001]` Solo se cancelan ocurrencias en estado **Reservada** (no Realizada ni Cerrada). — *(OKF: `cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md`)*
- `[RN-MOD-002]` Cancelar una reserva periódica exige **motivo** (catálogo de motivos). — *(OKF: `cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md`)*

### (4) Casos de uso (alcance de pruebas)
- `CU-01` Cancelar una reserva periódica con todas las ocurrencias Reservadas → todas quedan Canceladas con el motivo. — `[RN-MOD-001]` `[RN-MOD-002]`
- `CU-02` Reserva mixta (algunas Realizadas): solo se cancelan las Reservadas; las Realizadas quedan intactas. — `[RN-MOD-001]`
- `CU-03` Intento de cancelar sin motivo → se rechaza y no cambia ningún estado. — `[RN-MOD-002]`
- `CU-04` Asistente sin permiso de cancelación → la acción no se ofrece. — *(permiso por rol)*

### Documento fuente
`cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md` — referencia, no contenido.

## Criterios de aceptación (Bloque 2 — campo aparte `AcceptanceCriteria`)

```gherkin
Característica: Cancelar en serie las ocurrencias futuras de una reserva periódica

  Antecedentes:
    Dado que el asistente de recepción abrió una reserva periódica con ocurrencias futuras

  Escenario: Cancelar una reserva periódica con todas las ocurrencias reservadas [RN-MOD-001] [RN-MOD-002]
    Dado que todas las ocurrencias de la reserva están en estado "Reservada"
    Cuando el asistente cancela la reserva periódica y elige un motivo del catálogo
    Entonces todas las ocurrencias quedan en estado "Cancelada"
    Y cada ocurrencia registra el motivo elegido

  Escenario: Reserva periódica con ocurrencias ya realizadas [RN-MOD-001]
    Dado que la reserva tiene ocurrencias "Reservada" y ocurrencias "Realizada"
    Cuando el asistente cancela la reserva periódica
    Entonces solo las ocurrencias "Reservada" pasan a "Cancelada"
    Y las ocurrencias "Realizada" no se modifican

  Escenario: Falta el motivo [RN-MOD-002]
    Dado que el asistente no eligió un motivo
    Cuando intenta confirmar la cancelación
    Entonces el sistema muestra "Elegí un motivo de cancelación"
    Y no se modifica el estado de ninguna ocurrencia

  Escenario: Asistente sin permiso de cancelación (permiso por rol)
    Dado que el asistente de recepción no tiene permiso de cancelación
    Cuando abre la reserva periódica
    Entonces el sistema no ofrece la acción de cancelar
    Y no puede iniciar la cancelación
```

## Etiquetas
`reserva-salas`  *(único tag temático; sin tag de slice — el slice es la Épica "Gestión de salas")*

## Relaciones / Enlaces
- **Parent:** Feature "Reserva de salas de reunión" (bajo la Épica **Gestión de salas**).
- **Related:** Historia "Cancelar una reserva desde el autoservicio del solicitante".
- **Documento fuente:** `cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md` (referencia).

---

> **HTML pegable de la Descripción** (Bloques 1, 3, 4 + Documento fuente; los Criterios van al campo `AcceptanceCriteria`):
>
> ```html
> <h3>Funcionalidad / Historia de usuario</h3>
> <p><b>Contexto:</b> hoy el asistente de recepción cancela ocurrencia por ocurrencia; es lento y se saltean ocurrencias.</p>
> <p><b>Como</b> asistente de recepción<br><b>quiero</b> cancelar de una vez las ocurrencias futuras de una reserva periódica<br><b>para</b> liberar la sala sin ocurrencias huérfanas.</p>
> <h3>Alcance</h3><ul><li>Cancelar ocurrencias futuras (Reservada) de una reserva periódica desde la pantalla de reservas, con motivo.</li></ul>
> <h3>Fuera de alcance</h3><ul><li>Ocurrencias ya realizadas; cancelación desde el autoservicio del solicitante.</li></ul>
> <h3>Datos y estados</h3><ul><li><b>Campo:</b> Motivo de cancelación (obligatorio, del catálogo de motivos) <i>[RN-MOD-002]</i></li><li><b>Campo:</b> Solicitante (&lt;persona&gt;, identificado por &lt;documento&gt;) — solo lectura</li><li><b>Estado:</b> Reservada → Cancelada (permitida, con motivo); Realizada → Cancelada (bloqueada) <i>[RN-MOD-001]</i></li></ul>
> <h3>Reglas de negocio</h3><ul><li><b>[RN-MOD-001]</b> Solo ocurrencias "Reservada". <i>(OKF: cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md)</i></li><li><b>[RN-MOD-002]</b> Exige motivo. <i>(OKF: cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md)</i></li></ul>
> <h3>Casos de uso (alcance de pruebas)</h3><ul><li><b>CU-01</b> Reserva toda Reservada → todas Canceladas. <i>[RN-MOD-001][RN-MOD-002]</i></li><li><b>CU-02</b> Reserva mixta → solo Reservadas. <i>[RN-MOD-001]</i></li><li><b>CU-03</b> Sin motivo → rechazo. <i>[RN-MOD-002]</i></li><li><b>CU-04</b> Sin permiso → no se ofrece.</li></ul>
> <h3>Documento fuente</h3><p><a href="cerebro-digital/modulo-ejemplo/funcional/flujo-reserva-sala.md">flujo-reserva-sala.md</a> — referencia, no contenido</p>
> ```

> **HTML pegable de los Criterios de aceptación** (campo `AcceptanceCriteria`; el Gherkin de arriba convertido a HTML — TODAS las keywords en negrita, pasos sangrados, `[RN-…]` en itálica, un `<p>` por escenario):
>
> ```html
> <p><b>Característica:</b> Cancelar en serie las ocurrencias futuras de una reserva periódica</p>
> <p><b>Antecedentes:</b><br>
> &nbsp;&nbsp;<b>Dado</b> que el asistente de recepción abrió una reserva periódica con ocurrencias futuras</p>
> <p><b>Escenario:</b> Cancelar una reserva periódica con todas las ocurrencias reservadas <i>[RN-MOD-001][RN-MOD-002]</i><br>
> &nbsp;&nbsp;<b>Dado</b> que todas las ocurrencias de la reserva están en estado "Reservada"<br>
> &nbsp;&nbsp;<b>Cuando</b> el asistente cancela la reserva periódica y elige un motivo del catálogo<br>
> &nbsp;&nbsp;<b>Entonces</b> todas las ocurrencias quedan en estado "Cancelada"<br>
> &nbsp;&nbsp;<b>Y</b> cada ocurrencia registra el motivo elegido</p>
> <p><b>Escenario:</b> Reserva periódica con ocurrencias ya realizadas <i>[RN-MOD-001]</i><br>
> &nbsp;&nbsp;<b>Dado</b> que la reserva tiene ocurrencias "Reservada" y ocurrencias "Realizada"<br>
> &nbsp;&nbsp;<b>Cuando</b> el asistente cancela la reserva periódica<br>
> &nbsp;&nbsp;<b>Entonces</b> solo las ocurrencias "Reservada" pasan a "Cancelada"<br>
> &nbsp;&nbsp;<b>Y</b> las ocurrencias "Realizada" no se modifican</p>
> <p><b>Escenario:</b> Falta el motivo <i>[RN-MOD-002]</i><br>
> &nbsp;&nbsp;<b>Dado</b> que el asistente no eligió un motivo<br>
> &nbsp;&nbsp;<b>Cuando</b> intenta confirmar la cancelación<br>
> &nbsp;&nbsp;<b>Entonces</b> el sistema muestra "Elegí un motivo de cancelación"<br>
> &nbsp;&nbsp;<b>Y</b> no se modifica el estado de ninguna ocurrencia</p>
> <p><b>Escenario:</b> Asistente sin permiso de cancelación (permiso por rol)<br>
> &nbsp;&nbsp;<b>Dado</b> que el asistente de recepción no tiene permiso de cancelación<br>
> &nbsp;&nbsp;<b>Cuando</b> abre la reserva periódica<br>
> &nbsp;&nbsp;<b>Entonces</b> el sistema no ofrece la acción de cancelar<br>
> &nbsp;&nbsp;<b>Y</b> no puede iniciar la cancelación</p>
> ```
