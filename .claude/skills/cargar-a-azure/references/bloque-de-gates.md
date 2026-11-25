# Bloque de GATES: casos de llenado y por qué existe

Parte de la skill `cargar-a-azure`: se lee cuando una fila del Bloque de GATES (§2a) no es el caso simple, o cuando alguien propone sacar o achicar la tabla.

## Casos de llenado

- **Si el pedido no crea una Tarea** (corregir una existente, una Historia, un Bug), la fila de
  NIVEL dice **no aplica**. Nunca OK: un OK pide una cita, y acá no hay qué citar.
- **Sin MCP, el Tablero autorizado también es SIN DATOS.** Se sabe cuál es el tablero que
  corresponde, pero no se verificó que el destino sea ése: esa verificación es la que da OK.
- **Lo que cuenta el humano no es leer el tablero.** «Está en el Sprint 7 y en New» sirve para
  decidir qué proponer, pero la fila de Tarjeta congelada dice SIN DATOS hasta que se lea la
  tarjeta, porque es la lectura la que confirma el dato.

## NIVEL en modo lote

> **El gate de NIVEL no se hereda entre Historias.** Cada Historia necesita su declaración,
> dicha por el humano en esta conversación, y la cita textual de dónde se dio — si hay que
> buscarla y no aparece, FRENA. En **modo lote** ([[planificar-lote]]) una sola respuesta
> declara varias Historias si la pregunta del arranque **las nombró a todas**: lo que no se
> hereda es la declaración para una Historia que la pregunta no nombró.

## Por qué existe

> **Por qué existe este bloque.** Los GATES eran **instrucciones que el agente tenía que
> acordarse de aplicar**, y bajo la inercia de producir se comprimen: en una corrida real se
> saltearon **cuatro de cuatro** — el de NIVEL no se preguntó (se arrastró una confirmación de
> otra Historia, que la regla prohíbe explícitamente), el de confirmación se dio por cumplido
> con un "sí" sobre la **forma** y no sobre el **contenido**, la dedup se corrió pero se reportó
> en prosa sin el bloque, y el checklist de §2b no se corrió.
> El único control de este toolkit que nunca falla es la dedup, y no falla porque **produce un
> artefacto visible**. Esta tabla le da la misma forma al resto.
