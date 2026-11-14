---
id: redaccion-de-tickets
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Redacción de tickets — reglas de oro, fuentes que deciden, modo lote y cardinalidad"
author: equipo
tags: [redaccion, tickets, reglas, gherkin, lote, cardinalidad]
last_updated: 2026-11-14
---

# Redacción de tickets

El método para **redactar o derivar** work items (historias, tareas, bugs, habilitadores), en Azure o en cualquier
tablero (`DEC-006`). Lo cargan las skills del pipeline ([[redactar-tarea]], [[cargar-a-azure]],
[[sincronizar-backlog]], [[planificar-lote]]). Vivía en `AGENTS.md`, que se carga en cada sesión y en cada
subagente aunque no redacte tickets (M-044). Allá quedan lo que vale siempre: las **barreras de escritura** en el
tablero, la regla de los **datos personales** (regla de oro 2) y **no inventar** (regla de oro 3).

## Reglas de oro (no negociables)

1. **Cero inglés en la prosa.** Gherkin en español: Característica, Antecedentes, Escenario, Esquema del escenario, Ejemplos, Dado, Cuando, Entonces, Y, Pero. Las siglas (INVEST, DoR, DoD, MoSCoW) llevan su explicación al lado; los campos, como se llaman en Azure en español ([[checklists/mapa-campos-azure]]; Gherkin: [[criterios-aceptacion-gherkin]]).
2. **PHI (dato real de una persona) = PROHIBIDO.** La regla entera está en [[AGENTS]]: vale siempre, se redacte o no.
3. **No inventar nunca.** La regla entera está en [[AGENTS]]; lo que define una fuente, abajo («Fuentes que deciden»).
4. **El tipo se decide primero** (Historia, Tarea, Bug, Habilitador técnico / Spike), con una frase de por qué; si no está claro, se pregunta.
5. **Criterios de aceptación en Gherkin español**, con al menos un caso feliz y un borde o error. En un Bug: resultado esperado, obtenido y por qué es un error.
6. **Se respeta la intención del autor**: se mejora la forma y se completan huecos, no se cambia el pedido; un tipo mal encuadrado se señala y se propone el correcto.
7. **Se pregunta sólo lo que ninguna fuente define** («Fuentes que deciden», abajo), todo junto, numerado y con la recomendación al lado, **y se espera la confirmación antes de dar algo por «listo»**; se cierra con «Queda pendiente de tu confirmación: …».
8. **Silencio al entregar**: el ticket, no el relato; afuera, sólo el tipo y su porqué, los `⚠` y el veredicto.
9. **Backlog ordenado y trazable**: exactamente **una** etiqueta temática, la misma en toda la descendencia (nunca el slice, el producto ni el repo; si no hay una acordada, se propone con `⚠`), Relaciones (Parent y Related; los `#ID` con `⚠` hasta confirmar), el documento fuente por ruta y las `[RN-…]` en los criterios. Para bajar una ficha: «Regla de cardinalidad». Detalle: [[organizacion-y-trazabilidad]].

## Fuentes que deciden (lo que ya está definido no se pregunta)

Antes de preguntar algo, se busca quién lo define. En este orden:

1. **El Cerebro** (`[RN-…]`, `[DEC-…]`, pendientes resueltos, decisiones registradas en la ficha).
2. **La maqueta vigente**, para el comportamiento de pantalla: textos, botones, avisos, estados vacíos, formatos, orden de campos. Vigente es **la que la ficha cita en `fuente_maqueta`**; una maqueta «propuesta», o que ninguna ficha cita, no decide. Si contradice una regla del Cerebro, **gana el Cerebro** y se avisa.
3. **Lo que el humano ya respondió**, en esta conversación.
4. **Los contratos de las tarjetas ya cargadas** (Tareas hermanas, el back que consume el front).
5. **Una recomendación técnica clara de la IA** (partición, nombres internos —clases, rutas, nombres de test—, patrones del esqueleto): se aplica y se lista, para que el humano la vete. No se pide respuesta por cada una. **No cubre** códigos HTTP, códigos de error, números de regla ni valores de negocio: esos siguen la regla de oro 3. Lo aplicado por recomendación tampoco se guarda en el Cerebro como decisión.

**Se pregunta sólo** un dato duro sin fuente, una regla o un comportamiento que ninguna fuente define **y que cambia un test o un Escenario**, o un choque entre dos fuentes del mismo rango. Lo ya respondido no se vuelve a preguntar. Esto no habilita inventar: lo que no tiene fuente sigue siendo pregunta o `⚠` declarado (regla de oro 3).

## Modo lote (planificación rápida)

Varios ítems de una vez ([[planificar-lote]]) en **dos turnos humanos**: el **arranque** (alcance, nivel y todas las
dudas juntas) y el **cierre** (la tabla del lote y **un «sí» que lo escribe**). Las barreras de [[AGENTS]] valen igual;
donde el lote cambia algo, lo dice la barrera.

## Auditorías: opcionales, a pedido

[[auditar-tarea]], [[auditar-historia]] y [[analizar-tareas]] **no corren solas** y su sello no habilita ni frena nada.
Lo que encuentran, o lo que aparece al programar, queda como **pendiente a confirmar** en la tarjeta ([[comentar-tarea]]);
antes de cerrar una Tarea se leen sus comentarios y los pendientes van en la pregunta del cierre, que decide la persona.

## Regla de cardinalidad (conteo determinista)

El árbol sale **1:1** del bloque `## Derivación a backlog` de la ficha, no del criterio del modelo (lo arma
`bin/derivar-arbol.py`): una Épica por `[S-nn]`, una Feature por `[C-nn]`, una Historia por `[F-nn]` (el flujo, no la
pantalla), ni un nodo más ni uno menos; cero Tareas salvo el GATE de NIVEL, y entre todas cierran los Escenarios y las
`[RN-…]` del padre. **Sin el bloque, o con `⚠`, no se deriva.** Detalle y ejemplo: [[organizacion-y-trazabilidad]] §5.

## Pipeline, Cerebro Digital y skills

El dominio vive en el Cerebro; de ahí se derivan los tickets ([[pipeline-doc-a-tickets]]), que lo citan por ruta, sin
copiarlo. Toda escritura en el tablero, la haga la skill que la haga, pasa por las barreras de [[AGENTS]].
