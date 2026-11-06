# Arreglar un bug

> Prioridad **ALTA**, uso diario.
> Adaptado de `smart-fix` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## El ciclo, que es el mismo de siempre

Un bug no es una excepción al método: **es el caso más limpio de TDD**, porque el
comportamiento esperado ya está definido y el rojo te lo da la realidad.

```
1. REPRODUCIR    un test que falla, con los datos mínimos que lo disparan
2. ENTENDER      la causa, no el síntoma   ->  ver depurar.md
3. ARREGLAR      el mínimo que pone ese test en verde
4. SUITE         completa
5. EL TEST QUEDA para siempre
```

**El paso 5 es el que convierte un arreglo en una mejora.** Un bug arreglado sin test vuelve;
con test, no puede volver sin que alguien lo vea en rojo.

## Antes de arreglar, tres preguntas

| Pregunta | Por qué |
|---|---|
| **¿Es un bug o es una funcionalidad que falta?** | Si el comportamiento nunca se definió, no es un bug: es una Historia. Se avisa, no se inventa la regla |
| **¿Lo contradice alguna regla `[RN-…]`?** | Si el Cerebro dice otra cosa, quizás el bug es el código **o** la regla. Se pregunta, no se elige |
| **¿Es el mismo de otra tarjeta?** | Antes de arreglar se busca en el tablero. Arreglar dos veces el mismo bug de dos formas distintas es peor que no arreglarlo |

## Qué NO hacer

- **No arreglar donde explota.** Un `null` se rechaza donde se origina, no se tapa donde se
  ve. Ver [depurar.md](depurar.md).
- **No aprovechar y refactorizar de paso.** El arreglo tiene que ser legible en el diff. Si
  hay que ordenar, va en otro commit. Ver [refactor.md](refactor.md).
- **No ampliar el alcance.** Si encontrás otros dos bugs, se registran aparte — no se
  arreglan los tres en el mismo Merge Request.
- **No cerrarlo sin reproducirlo.** Si no se pudo reproducir, es `SIN DATOS`.

## Los tres que no se parecen

| Tipo | Cómo se ataca |
|---|---|
| **Sistemático** | Se reproduce fácil. Es el caso feliz del bug |
| **Intermitente** | Casi siempre es **tiempo, orden o concurrencia**. Se busca ahí antes que en la lógica |
| **"Sólo pasa en producción"** | Es una diferencia de **datos** o de **configuración**, no de código. Se compara la config de los dos ambientes antes de leer una línea |

Ese último desperdicia más horas que ningún otro, porque se busca en el código lo que está en
el entorno.

## Si está en producción

El orden se invierte: **primero se frena el daño, después se entiende.**

1. **Contener.** Volver atrás el despliegue, apagar la funcionalidad, lo que corte el daño.
2. **Avisar.** Quién está afectado y desde cuándo.
3. **Recién ahí**, el ciclo completo con su test.

Un parche caliente sin test **es deuda con fecha de vencimiento**: hay que volver y hacerlo
bien, y eso se registra antes de cerrar el incidente. Ver [incidentes.md](incidentes.md).

## Nada de PHI en la reproducción

El caso que lo dispara se describe con **marcadores**, nunca con el dato real de la persona
que lo reportó: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`,
`<dato-sensible>`.

Esto vale para el test, para el comentario en la tarjeta y para la descripción del Merge
Request. Es donde más se filtra, porque pegar el caso real parece lo más práctico.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Reproducido con un test, arreglado, suite en verde, el test queda |
| **HALLAZGO** | Arreglado pero sin test que lo cubra — puede volver sin aviso |
| **SIN DATOS** | **No se pudo reproducir.** No es "arreglado": es que no se sabe |
