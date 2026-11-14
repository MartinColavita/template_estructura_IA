---
id: redaccion-tickets-cambios-en-el-backlog
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Cambios en el backlog: desfase, avisos y modificaciones"
author: equipo
tags: [backlog, drift, desfase, avisos, trazabilidad, azure-devops, coordinacion, congelada]
last_updated: 2026-09-24
---

# Cambios en el backlog: desfase, avisos y modificaciones

Qué hacer cuando **el documento funcional cambia y la tarjeta ya existe** en Azure
DevOps. Dos situaciones, dos protocolos: la tarjeta está **en curso** (desfase) o
la tarjeta ya está **entregada** (cerrada). Método agnóstico; los ejemplos van
rotulados **Ejemplo (genérico)**.

---

## 1. Desfase (drift): el doc cambió y alguien trabaja una versión vieja

**El problema.** El doc del Cerebro Digital se actualizó (v2), la Historia ya
existe en el board, y alguien la está trabajando **desde antes del cambio** — sin
enterarse. Trabaja sobre una versión desactualizada. A eso le decimos **desfase**.

**La regla: DIFF antes de pisar.** Nada se sobrescribe en silencio. Al detectar el
desfase (lo detecta [[consultar-backlog]] o la propia [[sincronizar-backlog]] al
re-sincronizar), la IA **compara** el doc nuevo con la tarjeta y **propone el
DIFF**; solo con tu "sí" lo aplica:

```
La Historia #12345 tiene estos cambios respecto del doc v2:
  + Agregado:   criterio "reserva parcial permitida"     [RN-...-06]
  ~ Modificado: código por defecto 02 -> 03              [RN-...-13]
  - Eliminado:  (nada)
¿Aplico los cambios?
```

> **Si la tarjeta está congelada** —en un sprint y ya tomada— el DIFF **no se aplica**: va
> como comentario, y aplicarlo lo decide una persona. Ver §4.

## 2. Protocolo de aviso obligatorio (al aplicar la actualización)

Actualizar una tarjeta que tiene **asignado o seguidores** SIEMPRE dispara un
aviso, para que el que la trabaja no siga sobre lo viejo:

1. **Comentario con @mención** (vía [[comentar-tarea]] →
   `System.History`) diciendo **qué cambió** y la **fuente**:

   > @persona Esta historia se actualizó tras un cambio en el doc funcional.
   > QUÉ CAMBIÓ: + criterio "reserva parcial permitida" [RN-…-06] · ~ código por
   > defecto 02→03 [RN-…-13]. FUENTE: `<ruta-del-doc>` (v2). Si venías trabajando
   > una versión anterior, refrescá antes de seguir.

2. **Acuse de lectura: la persona responde el comentario** («Leído»). No se agrega una
   etiqueta: el techo es **una sola**, la temática ([[organizacion-y-trazabilidad]] §1), y
   además una etiqueta es una edición, que una tarjeta congelada no admite (§4). El comentario
   con la @mención sirve en los dos casos.

3. **Notificaciones nativas de Azure DevOps** que sostienen esto sin esfuerzo:
   *History* (todo cambio queda registrado: quién, cuándo, antes/después),
   *Follow* (quien sigue la tarjeta recibe un mail), *AssignedTo* y la **@mención**
   del comentario.

### Query guardado para el equipo — el "git pull" del backlog

Guardá en Azure DevOps un query **"Mis items que cambiaron"** y revisalo al empezar el día;
en cada uno, la @mención sin respuesta es el cambio que falta leer. Mira la última semana, para
que el lunes aparezca lo del viernes; lo que quedó más atrás sin leer lo trae la vista
**«Mencionado»** del hub de Work items de Azure Boards (las tarjetas donde te @mencionaron):

```
SELECT [System.Id], [System.Title], [System.ChangedDate]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.ChangedDate] >= @Today - 7
```

### Convención cultural (sin esto, ninguna herramienta alcanza)

- Antes de **cerrar** trabajo en una tarjeta, mirá su **History**.
- Antes de **empezar** el día, mirá tu query «Mis items que cambiaron».
- La IA comenta y notifica; el **hábito del equipo** cierra el circuito.

---

## 3. Modificaciones sobre funcionalidad ya ENTREGADA

**Principio: lo entregado no se reabre.** Una Historia desarrollada, probada y
entregada queda **cerrada para siempre** como registro de lo que se pidió y se
construyó. Reabrirla contamina las métricas (velocity, cycle time), mezcla
alcances y rompe la trazabilidad. Toda modificación vive en un **work item
nuevo**, siempre con validación humana.

### Árbol de decisión: ¿bug o evolutivo?

Ante un cambio del doc sobre algo ya entregado, la pregunta que resume todo es:
**¿se desvió del contrato, o cambió el contrato?**

| Pregunta | Respuesta | Qué se crea |
|---|---|---|
| ¿Lo entregado **funciona como decía el doc original**? | **No** → se desvió del contrato | **Bug** nuevo, linkeado a la Historia original como *Affects* |
| | **Sí**, pero el negocio **cambió la regla** | **Historia nueva**, linkeada *Related* a la original, bajo la misma Feature |

La Historia original **no se toca**: cuenta qué se pidió y se entregó en su momento.

### Tests que quedan obsoletos

Si QA ya tenía casos de prueba sobre esa área, quedaron escritos contra el
comportamiento **viejo**. Al proponer la modificación, listar qué planes/suites de
prueba cubren esa área para que QA los ajuste o retire antes del próximo
regresivo. Regla práctica: cada Historia nueva nace con su Gherkin y de ahí salen
los casos de prueba (ver [[criterios-aceptacion-gherkin]]), nunca de memoria.

---

## 4. Tarjeta congelada: en un sprint y ya tomada, sólo se comenta

**Cuándo queda congelada.** Cuando se cumplen **las dos** cosas a la vez:

| Condición | Cómo se lee en la tarjeta |
|---|---|
| Está **en un sprint** | `System.IterationPath` apunta a un sprint, no a la raíz del proyecto (`{{AZURE_PROYECTO}}`) |
| **Ya la tomaron** | `System.State` distinto de `New` (Active, Resolved, Closed…) |

⚠ El formato de la Ruta de iteración y el flujo de estados del tablero figuran `(pendiente)` en
[[contexto-proyecto]]. **Si no se puede leer el sprint o el estado, se trata como congelada**:
ante la duda, no se edita. En el Bloque de GATES esa fila dice **SIN DATOS**, y SIN DATOS
significa lo mismo: no se edita.

**Qué se puede y qué no.**

| Sobre una tarjeta congelada | |
|---|---|
| Leerla, con su historial y sus comentarios | Libre |
| **Comentar**: `System.History`, y **ningún otro campo** en esa misma escritura | Sí, con el "sí" de siempre ([[comentar-tarea]]) |
| Colgarle un **hijo nuevo**, o relacionar con ella una tarjeta **que no está congelada** | Sí, **siempre creando el vínculo desde la otra tarjeta** (`manage_work_item_link` con la no congelada como origen). Azure lo muestra en las dos, pero no se escribe **en** la congelada |
| Todo lo demás: Título, Descripción, Criterios de aceptación, Puntos de historia, Etiquetas, Estado, Asignado, Ruta de iteración, vínculos creados desde ella | **La IA no lo toca.** Frena y avisa |

Esta barrera se chequea **antes** que las demás: sobre una tarjeta congelada **no hay "sí" que
habilite una edición**, ni uno ni dos.

**Por qué.** Lo que está en el sprint y alguien está trabajando es lo que el equipo se
comprometió a hacer. Cambiarle el contenido en el medio le mueve el objetivo al que programa, y
aunque Azure lo registre en el historial, nadie lo lee a tiempo. El comentario lleva la misma
información **sin pisar lo acordado**, y le llega a quien la trabaja.

**Qué hace la IA cuando quería editarla.**

1. Frena **antes** de escribir y lo dice en criollo: *«La Tarea #NNNN está en el Sprint NN y
   ya la tomó `<persona>`: quedó congelada, sólo se puede comentar. ¿Dejo como comentario lo
   que quería cambiar?»*
2. Con el "sí", comenta **el cambio propuesto** con @mención a quien la tiene, usando el molde
   de [[comentar-tarea]]: *se agrega · se modifica · se quita*, no los símbolos `+ ~ -`.
3. **Aplicarlo o no lo decide una persona**: a mano en Azure o, si lo que cambió es el pedido,
   en un ítem nuevo, como en la §3.

**Lo que NO frena.** El flujo de desarrollo sigue andando:

- **Tomar la tarjeta** ([[tomar-tarea]]) la pasa de `New` a `Active`: en ese momento todavía no
  está congelada. Es justamente la escritura que la congela, y el preview lo avisa.
- El **sello de auditoría** ([[auditar-tarea]], [[auditar-historia]]), cuando se pidió una, el
  **comentario de cierre de desarrollo** y los **pendientes a confirmar** ([[comentar-tarea]])
  son comentarios: entran. Y un comentario **no vence ningún sello**: el sello vence sólo si
  cambia el contenido auditado.
- La auditoría es opcional y **no frena tomar una Tarea**: lo que encuentre queda como
  pendiente en la tarjeta y se revisa antes de cerrarla.
- **Tomar una Tarea que ya es tuya** y está en `Active` no hace falta: no hay nada que escribir.

**Lo que SÍ cambia, y hay que saberlo.** Si una tarjeta **ya congelada** necesita un arreglo de
contenido —una Tarea tomada que se vuelve a auditar y da **con huecos**, o una Historia en curso
cuyo Gherkin no cierra—, **la IA no la corrige**. Propone el arreglo como comentario, y **lo
carga una persona a mano** en Azure. Volver a auditarla es opcional, a pedido.

**El límite, dicho de frente.** Esta barrera frena a la IA, no a las personas: desde la pantalla
de Azure, quien tenga permiso puede editar igual. Para que el tablero mismo lo impida hace falta
una regla del proceso —campos de sólo lectura según el estado—, que la configura quien
administra la organización. ⚠ A confirmar con esa persona.

---

## Ver también

- Detectar desfase y auditar cobertura (solo lectura): [[consultar-backlog]]
- Aplicar la actualización en lote / re-sincronizar: [[sincronizar-backlog]]
- Dejar el comentario de aviso, y el único que entra en una tarjeta congelada: [[comentar-tarea]]
- Criterios como contrato verificable: [[criterios-aceptacion-gherkin]]
- Etiqueta temática, relaciones y documento fuente: [[organizacion-y-trazabilidad]]
