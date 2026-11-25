# Autochequeo antes de entregar

Parte de la skill `redactar-tarea`: se lee antes de entregar el ticket (§5 de la skill), y se corre entero cada vez.

**Autochequeo antes de entregar** (mecánico; si uno falla, se corrige antes de mostrar):

| # | Chequeo |
|---|---|
| 1 | **Etiquetas: exactamente una.** No es un slice (`<slice-1>` · `<slice-2>` · `<slice-n>`), ni `<producto>`, ni `modulo-ejemplo`. Si el tema no tiene etiqueta acordada, va con `⚠` |
| 2 | Descripción y Criterios **en HTML**; cero markdown |
| 3 | Cada `[RN-…]` citada **existe en el Cerebro**, y se puede decir en qué archivo. **Y dice lo que se le atribuye**: se lee la regla, no alcanza con encontrar el número. Una regla con un sufijo agregado (`-REV`, `-CONF`) no es esa regla: es una inventada. **Si el pedido choca con una regla** (p. ej. pide validar algo que la regla deja fuera de esta etapa), se frena y se pregunta: no se redacta el arreglo igual |
| 4 | Si el pedido era corregir una tarjeta existente, **se leyó su texto actual** (del tablero o pegado). Si no, no se reconstruyó: se pidió |
| 5 | Todo lo que no se sabe está marcado `⚠`, no rellenado con lo esperable. En particular, **un código HTTP, un código de error o un número de regla** que no figura en la tarjeta ni en el Cerebro va `⚠ a definir`, nunca con un valor que suene bien: un código de estado típico, un nombre de error armado a partir del pedido, o un número de regla correlativo |
| 6 | **No existe ya.** Si al leer el Cerebro aparece un ticket del mismo pedido (el bloque «Tickets derivados» de la ficha, o un `#ID` citado en el flujo), se frena y se pregunta si se actualiza ése: no se redacta uno nuevo en paralelo ([[deduplicacion-antes-de-crear]]) |
| 7 | **El tipo sale de la señal, no del pedido.** Si lo que se describe como falla todavía no existe según el Cerebro (figura como pendiente o fuera de esta etapa), no es un Bug: es una Historia o mejora, y se dice por qué |
