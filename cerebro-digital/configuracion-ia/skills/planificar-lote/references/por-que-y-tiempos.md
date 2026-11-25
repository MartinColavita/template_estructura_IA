# Por qué existe el modo lote y cuánto tarda

Parte de la skill `planificar-lote`: se lee para explicar por qué existe el modo lote, o cuando una fase se alarga.

> **Por qué existe.** En el proyecto de origen, las Tareas de una Feature (5 Historias,
> 13 Tareas) llevaron **más de cuatro horas** con los devs: contadas sobre las reglas, el flujo
> pedía más de treinta confirmaciones en turnos separados (el nivel por Historia, el análisis
> del set, cada preview, cada sello, cada edición), y además se preguntaba lo que la maqueta y
> el Cerebro ya decían. Ninguna de esas vueltas agregaba control: el control está en los
> GATES duros, y esos quedan; las auditorías independientes pasaron a ser opcionales, a pedido
> (decisión de diseño del template). **Objetivo: ese mismo
> lote en 30 a 40 minutos.**

## Tiempos esperados (lote de 5 Historias y 13 Tareas)

| Fase | Quién | Tiempo |
|---|---|---|
| 0. Preparar | IA, en paralelo | 5 min |
| 1. Arranque | Humano | 5 min |
| 2. Redactar | IA, un agente por Historia | 10 a 12 min |
| 3. Auditar (sólo si se pidió) | IA, agentes distintos | 0, o 5 a 8 min |
| 4. Cierre | Humano | 5 min |
| 5. Escribir | IA | 5 min |

Lo que más tarda es la revisión del humano en el cierre. Si se alarga, casi siempre es porque
volvieron P que la fase 0 no levantó: anotarlo en el log del lote para afinar la próxima.
