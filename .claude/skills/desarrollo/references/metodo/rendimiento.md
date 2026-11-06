# Rendimiento

> Prioridad **MEDIA** — se atiende cuando hay un número que lo pida, no antes.
> Adaptado de `performance-optimization` y `multi-agent-optimize` de `wshobson/commands`
> (MIT), [referencias-externas.md](../referencias-externas.md).

## La regla

**No se optimiza sin medir.** Una optimización sin medición previa es una complicación con
buena intención: agrega código difícil, no mejora nada medible, y nadie se anima a sacarla
después porque "debe estar por algo".

```
1. MEDIR      dónde se va el tiempo, de verdad
2. ELEGIR     lo que más pesa, no lo más fácil
3. TEST       que fije el comportamiento -> optimizar no puede cambiarlo
4. OPTIMIZAR  una cosa por vez
5. MEDIR      otra vez. Si no mejoró, se revierte
```

Ese paso 5 es el que casi nadie hace, y es el único que distingue una optimización de una
creencia.

## Qué medir

Percentiles, **nunca el promedio**. Con 99 respuestas de 50 ms y una de 10 segundos el
promedio da 150 ms y parece sano; el percentil 99 dice 10 segundos, que es lo que le pasó a
alguien de verdad.

Ver [observabilidad.md](observabilidad.md), que es de donde salen los números.

## Los cuatro sospechosos de siempre

En orden de frecuencia real, no de lo interesantes que son:

| # | Problema | Cómo se ve |
|---|---|---|
| 1 | **Consulta dentro de un bucle** | La pantalla tarda proporcional a la cantidad de filas. Traer 50 filas dispara 51 consultas |
| 2 | **Falta un índice** | Una consulta que anda bien en desarrollo y se arrastra en producción. La diferencia es el volumen |
| 3 | **Se trae de más** | `SELECT *` para usar dos campos, o una lista completa para mostrar diez filas |
| 4 | **Llamadas en serie que podrían ir juntas** | Tres servicios consultados uno después del otro cuando no dependen entre sí |

**El 90% de los problemas de rendimiento de una aplicación de gestión son los cuatro de
arriba, y ninguno se arregla con código más listo: se arregla trayendo menos cosas.**

## En el front

| Problema | Señal |
|---|---|
| Se re-dibuja de más | La grilla parpadea al escribir en un filtro |
| Se trae todo y se filtra en el navegador | Anda bien con 100 filas, se muere con 5000 |
| Todo el código en un solo paquete | La primera carga tarda |
| Imágenes sin optimizar | Suele ser la mitad del peso de la página |

## Lo que NO se hace

- **Optimizar lo que nadie usa.** Una pantalla que se abre dos veces por mes no justifica
  nada.
- **Sacrificar claridad por una mejora que no se midió.**
- **Optimizar con el ciclo de TDD abierto.** Primero verde, después rápido. Nunca al revés.
- **Cachear para tapar una consulta mal hecha.** El caché esconde el problema y agrega otro:
  datos viejos.

## Antes de tocar nada, tres preguntas

1. **¿Cuál es el número hoy?** Si no lo sabés, no empieces.
2. **¿Cuál tiene que ser?** Si no está definido, es una decisión de equipo, no técnica.
3. **¿Quién lo sufre?** Si nadie se quejó y ninguna métrica lo marca, probablemente no sea el
   problema.

**Propuesta del método:**

| Qué | Objetivo |
|---|---|
| Endpoint de lectura simple | p95 < 500 ms |
| Endpoint de lectura con filtros o agregación | p95 < 1 s |
| Endpoint de escritura | p95 < 2 s |
| Pantalla interactiva (la lista ya cargada responde) | < 100 ms |
| Carga inicial de una pantalla | < 2,5 s |

**Y lo que hace que estos números signifiquen algo: se miden con volumen parecido al de
producción.** Cualquier consulta vuela con doscientas filas. El problema aparece con las que
va a haber, y aparece de golpe.

⚠ *Propuesta del método, a confirmar por el equipo.*

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Se midió antes, se optimizó una cosa, se midió después y mejoró |
| **HALLAZGO** | Hay un problema claro identificado y medido |
| **SIN DATOS** | **No hay medición.** Una afirmación de rendimiento sin número es una opinión |
