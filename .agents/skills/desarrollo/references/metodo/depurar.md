# Depurar — encontrar la causa, no el síntoma

> Prioridad **ALTA**, uso diario. Adaptado de `smart-debug`, `debug-trace`, `error-trace` y
> `error-analysis` de `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## La regla que ahorra más tiempo

**Antes de tocar una línea, reproducilo con un test que falle.**

Si no podés reproducirlo, no lo entendiste todavía — y cualquier arreglo va a ser una
apuesta. Ese test que falla es, además, el rojo del ciclo: cuando pase a verde, el bug está
arreglado *y* queda cubierto para siempre.

> Arreglar sin test de reproducción es la forma más común de "arreglar" un bug dos veces.

## El orden

```
1. REPRODUCIR    un test que falla, con los datos mínimos que lo disparan
2. ACOTAR        en qué módulo y en qué capa vive
3. CAUSA         por qué pasa, no dónde se ve
4. ARREGLAR      el mínimo, con el test en verde
5. SUITE         completa, para no haber roto otra cosa
```

## Acotar en microservicios: el `trace_id` manda

El back lleva trazas distribuidas y logs estructurados en JSON —con qué herramienta lo fija
el stack del proyecto, en `arquitectura/esqueleto-proyectos.md` del Cerebro— y eso es
justamente lo que hace posible depurar sin adivinar.

| Herramienta | Para qué |
|---|---|
| **`trace_id`** | Seguir **un** pedido a través de todos los servicios que tocó |
| **`span_id`** | Ubicar en qué tramo se fue el tiempo o saltó el error |
| **Logs en JSON** | Filtrar por servicio, nivel y `trace_id` en vez de leer texto suelto |

**Sin `trace_id` en el log, un error en microservicios es una aguja en un pajar.** Si al
depurar descubrís que un log no lo lleva, eso es un `HALLAZGO` en sí mismo: arreglalo antes
de seguir, porque el próximo bug te va a costar lo mismo.

## Qué mirar, en orden

1. **El mensaje completo y la traza**, no la primera línea.
2. **El `trace_id`** del pedido que falló, y todos los servicios que atravesó.
3. **Qué entró**: los datos exactos. La mayoría de los bugs son un caso borde que nadie
   previó, no lógica rota.
4. **Qué cambió**: si andaba y dejó de andar, el `git log` del módulo es más rápido que leer
   el código.
5. **Si es sistemático o intermitente.** Intermitente casi siempre es tiempo, orden o
   concurrencia — las mismas tres causas que hacen inestables a los tests.

## Distinguir el síntoma de la causa

| Síntoma | Causa probable |
|---|---|
| Una excepción por valor nulo en la capa `api` | Alguien más arriba devolvió nulo sin declararlo en el contrato |
| Timeout contra un servicio externo | Falta el tiempo de espera configurado, o falta el reintento |
| "A veces da mal el total" | Orden no garantizado, o redondeo |
| Un `500` mudo | Se tragó una excepción en algún `catch` sin registro |

**Arreglar donde explota no arregla nada.** El `null` hay que rechazarlo donde se origina, no
taparlo donde se ve.

## Lo que NUNCA va en un log

Esto no es estilo, es la regla de PHI aplicada al peor lugar posible — porque los logs se
guardan, se centralizan y los ve gente que no está en el equipo:

- **Nada de datos sensibles del dominio ni datos personales reales.** Marcadores: `<persona>`,
  `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.
- **Nada de credenciales, tokens ni claves.** Ni siquiera "para probar un ratito".
- **Ni el cuerpo entero de un pedido** cuando puede traer datos de la persona.

Si para depurar necesitás ver el dato real, se reproduce **en local con datos falsos**. Un
dato real pegado en un log queda ahí para siempre y lo ve todo el mundo.

## Agrupar errores en vez de contarlos

Cien errores idénticos son **un** problema, no cien. Al mirar un tablero de errores:

- **Agrupar por causa**, normalizando el mensaje (sacar IDs, fechas y valores variables).
- **Ordenar por impacto**, no por cantidad: diez errores que frenan una operación del negocio
  pesan más que mil de un log ruidoso.
- **Comparar contra ayer.** Lo que importa casi siempre es qué *cambió*, no el total.

## Cómo cierra

| Estado | Cuándo |
|---|---|
| **OK** | Reproducido con un test, arreglado, suite en verde, y el test queda |
| **HALLAZGO** | Encontrado pero no arreglado — o se encontró otra cosa de paso |
| **SIN DATOS** | **No se pudo reproducir.** No es "está arreglado": es que no se sabe |

Cerrar un bug sin poder reproducirlo es `SIN DATOS`. Se dice qué falta —logs, `trace_id`, el
dato que lo dispara— en vez de darlo por resuelto.
