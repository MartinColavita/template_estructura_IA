# Simular la API en el front, desde el contrato

> Método propio. La herramienta con la que se simula la provee el stack del front (⚠ a
> definir, se anota en `arquitectura/esqueleto-proyectos.md`); nada de lo que sigue depende de
> cuál sea. Prácticas adaptadas de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## La regla dura

**Las simulaciones salen del `openapi.yaml` que consolida el back. Nunca se inventa la forma
de una respuesta.**

Es lo que permite que los repositorios de front del proyecto (uno por aplicación) programen
**sin esperar** al back. Y es también donde se rompe todo si alguien se apura: un front que
anda perfecto contra una respuesta inventada falla en integración, tarde, y parece un problema
del back.

Si el endpoint todavía no está en el contrato, **eso bloquea la Tarea**. Ver
[contrato-openapi.md](contrato-openapi.md).

## Qué se simula, más allá del camino feliz

Ésta es la parte que siempre se saltea. Por cada endpoint:

| Escenario | Qué verifica en la UI |
|---|---|
| **Éxito** | Que muestre los datos |
| **Lista vacía** | Que muestre el estado vacío, **no** una tabla en blanco ni un error |
| **Cada `4xx` del contrato** | Mensaje distinto por código. Un `403` no se comunica igual que un `404` |
| **Cada `5xx` del contrato** | Que ofrezca reintentar, y que no pierda lo que el usuario cargó |
| **Respuesta lenta** | Que aparezca el indicador de carga, y que no se pueda enviar dos veces |
| **Sin red** | Que avise, y que no quede colgado para siempre |

**Cada código declarado en el contrato lleva su test.** Si el contrato dice que existe un
`409`, la UI tiene que saber qué hacer con él.

## Latencia y carga — el escenario que nadie prueba

Simular la respuesta instantánea esconde tres bugs muy comunes:

1. **El indicador de carga que nunca se ve** porque en desarrollo todo responde en 2 ms.
2. **El doble envío**: el usuario aprieta dos veces porque no pasó nada visible.
3. **La condición de carrera**: dos pedidos que vuelven desordenados y la pantalla queda con
   el resultado del primero.

Por eso al menos un test por flujo corre **con retardo simulado**.

## Deriva entre la simulación y la API real

El riesgo de fondo: la simulación se escribe una vez, el contrato cambia, y la simulación
sigue devolviendo lo viejo. **El test pasa en verde y la app está rota.**

Se evita así:

- **La simulación de la API se genera desde el contrato, o se valida contra el
  `openapi.yaml`**; no se escribe de memoria.
- **Toda llamada no simulada falla el test.** Si el código llama a un endpoint que nadie
  declaró, tiene que gritar — no devolver un valor vacío en silencio.
- **Cuando el contrato cambia, los tests de front se corren igual**, aunque el cambio parezca
  del back. Es el único momento en que la deriva se puede ver barata.

## Datos: nunca PHI

Ni en las simulaciones, ni en los fixtures, ni en las capturas. **Marcadores siempre**:
`<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.

Los fixtures se versionan: lo que entre ahí queda en el historial de git para siempre.

## Lo que no se simula

**La lógica de negocio propia del front.** Si la validación la hace el front, se prueba de
verdad, no se simula su resultado. Simular lo que querías probar es probar tu simulación.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Todos los códigos del contrato tienen su escenario simulado y su test |
| **HALLAZGO** | Falta un código, o la simulación devuelve algo que el contrato no declara |
| **SIN DATOS** | **No hay contrato** para ese endpoint, o no se pudo validar contra él |

Ese `SIN DATOS` es el más frecuente en el front y el que más engaña: una suite entera en
verde contra simulaciones que nadie comparó con el contrato **no verifica nada**.
