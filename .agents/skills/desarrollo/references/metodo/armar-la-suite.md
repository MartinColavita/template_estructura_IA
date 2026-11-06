# Armar la suite de tests

> Método propio. Categorías, testing basado en propiedades y **mutación** adaptados de
> `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## Las siete categorías, y cuáles usamos

| Categoría | ¿Acá? |
|---|---|
| **Unitario** | **Sí, por defecto.** La base de la pirámide |
| **De integración** | **Sólo si la Tarea lo declara** (dependencia externa real) |
| **De contrato** | **Sí.** Que la respuesta coincida con el `openapi.yaml`. Es la bisagra entre back y front |
| **De punta a punta (aceptación)** | **Sí**: los Escenarios de la Historia contra la aplicación desplegada, trazados al `#ID` ([pruebas-de-aceptacion.md](pruebas-de-aceptacion.md)); la herramienta la fija [tdd-stack-front.md](tdd-stack-front.md). Pocos, y sólo de los flujos que dan plata |
| **De rendimiento** | **Sólo sobre endpoints con volumen**, no de rutina. Ver [rendimiento.md](rendimiento.md) |
| **De seguridad** | **Sí**, pero la puerta que tiene que mandar es **SAST**, no un test — ⚠ **pendiente de definir** por el equipo / la organización del nuevo proyecto ([seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md)) |
| **De mutación** | **Recomendado.** Ver abajo — es lo mejor que salió de la fuente |

La pirámide: muchos unitarios, menos de integración, poquísimos de punta a punta. Al revés,
la suite tarda veinte minutos, nadie la corre y termina desactivada.

## Testing por mutación — la respuesta mecánica a "¿este test puede fallar?"

Nuestra regla dice que **un test que no puede fallar no sirve**. El problema es que
verificarlo a mano es tedioso y se saltea.

El testing por mutación lo hace solo: **cambia el código a propósito** —invierte un `>` por
un `>=`, da vuelta un booleano, borra una línea— y corre la suite.

- Si **algún test falla** → la mutación fue *matada*. Bien: hay un test que cubre eso.
- Si **todos pasan** → la mutación *sobrevivió*. **Hay código que ningún test verifica**,
  aunque la cobertura diga 100%.

> Es la única herramienta que mide lo que la cobertura no puede: **la cobertura dice qué
> líneas se ejecutaron; la mutación dice cuáles estaban realmente verificadas.** Un test sin
> una sola aserción da cobertura completa y no mata ni una mutación.

**Cómo se usa acá:** no en cada corrida —es lento— sino sobre el código nuevo de una Tarea,
antes del Merge Request. Un superviviente es un `HALLAZGO`: o falta un test, o el código
sobra.

Herramienta, **propuesta del método**: la de testing por mutación del stack de cada
repositorio. Cuál es, se fija en la plantilla de ese stack:

| Stack | Con qué |
|---|---|
| **Back** | La herramienta de mutación del stack del back — [tdd-stack-back.md](tdd-stack-back.md) |
| **Front** | La herramienta de mutación del stack del front — [tdd-stack-front.md](tdd-stack-front.md) |

⚠ *Propuesta del método, a confirmar por el equipo.*

## Testing basado en propiedades

En vez de escribir veinte ejemplos, se declara **la propiedad que siempre tiene que valer** y
la herramienta genera entradas al azar buscando el contraejemplo.

Sirve para lo que tiene muchas combinaciones: validadores de formato, cálculos con rangos,
cualquier cosa con fechas.

No reemplaza a los tests por ejemplo: **los complementa**. Los ejemplos documentan el
comportamiento esperado; las propiedades encuentran el borde que nadie imaginó.

Herramienta, **propuesta del método**: la biblioteca de testing basado en propiedades del
stack de cada repositorio, fijada en [tdd-stack-back.md](tdd-stack-back.md) y
[tdd-stack-front.md](tdd-stack-front.md).

⚠ *Propuesta del método, a confirmar por el equipo.*

## Datos de prueba

**Fábricas, no fixtures pegados.** Una función que arma el objeto con valores por defecto
razonables y te deja pisar sólo lo que importa para ese test:

```
unaSolicitud()                       // válida, valores por defecto
unaSolicitud().vencida()             // la variante que este test necesita
```

Por qué: con fixtures fijos, cuando cambia un campo obligatorio hay que tocar cuarenta
archivos. Y el test no dice **qué** lo hace distinto, porque todos los valores están a la
vista y ninguno resalta.

**Nunca PHI.** Marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`,
`<direccion>`, `<dato-sensible>`.

## Tests inestables — no se marcan, se arreglan

Un test que a veces pasa y a veces no **es peor que ninguno**: entrena al equipo a ignorar el
rojo, y el día que falla de verdad nadie lo mira.

Las cuatro causas, en orden:

| Causa | Arreglo |
|---|---|
| **Tiempo**: `now()`, fechas relativas, esperas fijas | Reloj fijo, inyectado |
| **Orden**: el test B depende de lo que dejó el A | Cada test arranca de cero. Transacción que se revierte |
| **Aleatoriedad**: IDs generados, colecciones sin orden garantizado | Semilla fija, orden forzado antes de comparar |
| **Red**: llamada real a un servicio | Se simula. Siempre |

**Marcar un test como inestable y seguir es tapar el problema.** Si falla dos veces sin que
nadie toque el código, está mal escrito.

## Qué hace bueno a un test

Cinco criterios, y los cinco se chequean:

1. **Puede fallar.** Si pasa contra cualquier implementación, no mide nada.
2. **Falla por una sola razón.** Una condición por test.
3. **El nombre dice qué comportamiento**, no qué método. Cuando falla en el pipeline, el
   nombre es lo único que se lee.
4. **No sabe cómo está implementado.** Si se rompe en cada refactor sin que nada esté mal,
   está atado a la implementación.
5. **Corre solo, en cualquier orden, en cualquier máquina.**

## Umbrales

| | |
|---|---|
| Cobertura de líneas | ⚠ **Lo define el equipo / la organización del nuevo proyecto**, sobre el código nuevo (no sobre el repositorio entero); se anota en `arquitectura/decisiones.md` del Cerebro |
| Supervivientes de mutación | **Cero sobre el código nuevo de la Tarea.** Cada superviviente es un `HALLAZGO`: falta un test o sobra código |
| Tiempo máximo — **unitarios** | **2 minutos.** Es la suite que se corre a cada rato; si tarda más, se deja de correr |
| Tiempo máximo — **suite completa** | **10 minutos.** Pasado eso, el pipeline deja de dar respuesta útil y la gente mergea sin esperarlo |

⚠ *Los otros tres son propuesta del método, a confirmar por el equipo.*

**La cobertura es un piso, no un objetivo.** El chequeo que vale es que cada caso de la Tarea
tenga su test y que cada test pueda fallar.

## Lo específico de cada stack

Plantillas que se completan con el stack que elija el proyecto:

- [tdd-stack-back.md](tdd-stack-back.md)
- [tdd-stack-front.md](tdd-stack-front.md) y [simular-api-desde-el-contrato.md](simular-api-desde-el-contrato.md)
