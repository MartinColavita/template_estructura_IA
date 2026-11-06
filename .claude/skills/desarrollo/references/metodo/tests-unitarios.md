# Qué prueba un test unitario, y qué no

> Método propio.

## La pregunta que ordena todo

Antes de escribir un test, una sola pregunta: **¿qué comportamiento verifica, y cómo sé que
puede fallar?**

Si no podés contestar la segunda, no escribas el test todavía. Un test que pasa contra
cualquier implementación no mide nada, y peor: cuenta en la cobertura, así que **tapa el
hueco que debería mostrar**.

## Una condición por test

Cada test verifica **una sola cosa**. Un test que afirma "A **o** B" pierde una rama en
silencio: pasa si A se cumple, y nadie se entera de que B nunca se probó.

```
MAL:  "el endpoint devuelve 400 o 422 ante entrada inválida"
BIEN: "ante <campo> vacío devuelve 400"
      "ante <campo> con formato inválido devuelve 422"
```

Esto además es lo que permite que la lista de "Tests a escribir PRIMERO" de la Tarea se
mapee uno a uno con los tests reales.

## Qué se simula y qué no

| | Regla |
|---|---|
| **Integraciones externas** (otro microservicio, una API, la base) | **Se simulan.** Sin excepción en un test unitario |
| **Lógica de negocio** | **NUNCA se simula.** Si simulás la regla que querés probar, probás tu simulación |
| **Reloj, aleatoriedad, IDs generados** | Se fijan. Si no, el test es inestable y termina ignorado |

Esa segunda fila es la que más se rompe y la más cara: un test que simula el cálculo que
debía verificar pasa siempre, se ve prolijo, y no protege nada.

## Qué caso merece un test

Sale de la Tarea, no del criterio del momento. Cada uno de éstos lleva el suyo:

- Cada **validación** declarada en el contrato.
- Cada fila de la tabla de **Casos de error**.
- Cada **código de respuesta** del contrato OpenAPI.
- Cada regla de negocio `[RN-…]` que la Tarea cita.
- Cada **Escenario** del Gherkin de la Historia padre.

Si algo de esa lista no tiene test, **es un hueco**. Y un hueco no avisa: nadie recibe una
notificación por el caso que nadie escribió.

## Los bordes que siempre faltan

La lista corta de lo que se olvida, en orden de frecuencia:

1. **Colección vacía** — no `null`, vacía. Rompe distinto.
2. **`null`** donde el contrato lo permite, y donde no.
3. **Los límites exactos**: el valor mínimo, el máximo, y uno más allá de cada uno.
4. **Cadena vacía** vs. cadena con espacios.
5. **Duplicados** donde se asume unicidad.
6. **Orden**: cuando el código asume uno que la fuente no garantiza.
7. **Concurrencia**: dos pedidos sobre el mismo recurso, cuando aplica.

## Nombre del test

El nombre dice **qué comportamiento**, no qué método. Se tiene que entender sin abrir el
cuerpo del test:

```
MAL:  testCalcular()  ·  test1()  ·  deberiaFuncionar()
BIEN: rechazaLaSolicitudCuandoLaPersonaNoEstaHabilitada()
```

Cuando un test falla en el pipeline, el nombre es lo único que se lee. Si no dice nada, hay
que abrir el archivo.

## Cobertura: lo que mide y lo que no

**Mide qué líneas se ejecutaron. No mide si se verificó algo.** Un test sin una sola
aserción da cobertura completa.

Por eso la cobertura acá es un **piso, no un objetivo**: el número ⚠ lo fija el equipo / la
organización del nuevo proyecto —sobre el código nuevo, no sobre el repositorio entero— y se
anota en `arquitectura/decisiones.md` del Cerebro. Pero el chequeo que vale es el otro: **que
cada caso de la Tarea tenga su test, y que cada test pueda fallar.**

## Nada de datos sensibles del dominio

Ni en los tests, ni en las simulaciones, ni en los mensajes de error. Marcadores: `<persona>`,
`<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.

Los tests se versionan. Lo que entre ahí queda en el historial de git para siempre.

## Lo específico de cada stack

Plantillas que se completan con el stack que elija el proyecto:

- [tdd-stack-back.md](tdd-stack-back.md)
- [tdd-stack-front.md](tdd-stack-front.md)
