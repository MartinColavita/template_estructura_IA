# Refactor y deuda técnica

> Prioridad **ALTA**, uso diario: es la tercera fase del ciclo.
> Adaptado de `refactor-clean` y `tech-debt` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## La definición, que no es obvia

**Refactor es cambiar la forma sin cambiar el comportamiento.** Si el comportamiento cambia,
no es un refactor: es un cambio, y necesita su propio test primero.

De ahí sale la regla única:

> **Los tests no se tocan durante un refactor.** Si hay que ajustar un test para que pase, o
> cambiaste el comportamiento, o el test estaba atado a la implementación. Las dos cosas se
> avisan; ninguna se arregla ajustando el test en silencio.

## Cuándo

| Momento | Qué se hace |
|---|---|
| **Después de cada verde** | El refactor de la fase 3. Chico, inmediato |
| **Antes de tocar algo feo** | Si vas a cambiar código enredado, primero ordenalo **con la suite en verde**, y después cambialo |
| **Nunca** | Junto con un cambio de comportamiento, en el mismo commit |

Ese último punto es el que más se rompe: un Merge Request que mezcla refactor y
funcionalidad es imposible de revisar. El que revisa no puede distinguir qué líneas cambian
la lógica y cuáles sólo la mueven. **Van en commits separados**, y si son grandes, en Merge
Requests separados.

## Qué se busca

En orden de cuánto duele dejarlo:

1. **Código muerto.** Métodos que nadie llama, ramas inalcanzables, imports colgados,
   configuración de algo que ya no existe. Cuesta cero sacarlo y confunde a todo el que lee.
2. **Duplicación real.** Dos lugares que **cambian juntos siempre**. Ojo: dos cosas parecidas
   que cambian por motivos distintos **no son duplicación**, y unificarlas las acopla.
3. **Métodos que hacen tres cosas.** Se nota en el nombre: si lleva "y", son dos métodos.
4. **Condicionales anidados**. Tres niveles ya es difícil de seguir; cuatro, imposible.
5. **Números y textos sueltos** que deberían tener nombre.
6. **Fugas entre módulos**: un import de `api` o `infra` de otro módulo. Eso no es deuda,
   **es bloqueante**.

## Lo que NO se refactoriza

- **Código sin tests.** Sin red, un refactor es un cambio a ciegas. Primero los tests.
- **Código que no vas a tocar.** Feo pero estable y aislado no es deuda urgente: es el
  aspecto que tiene algo que funciona.
- **Por gusto personal.** Renombrar todo a tu estilo cuesta revisión y no aporta.

## Deuda técnica: registrarla, no lamentarla

Cuando algo queda mal a propósito —un atajo con un límite conocido, por tiempo, por una decisión
pendiente, por una dependencia externa— **se marca en el código con una sola línea**, no en el
chat ni en la memoria de alguien. Con el comentario del lenguaje (`//`, `#`, `--`, `/*`):

```
// atajo: <qué se simplificó y hasta dónde aguanta>; cuando <qué tiene que pasar para mejorarlo> <#ID o DT-nnn>
```

Por ejemplo: `# atajo: lee el archivo entero en memoria, alcanza hasta ~50 MB; cuando lleguen archivos más grandes, DT-004`.

| Parte | Qué lleva |
|---|---|
| **El límite** | Qué se simplificó y hasta dónde aguanta, en una línea |
| **`cuando …`** | El disparador para mejorarlo. Un atajo sin disparador es el que se pudre sin que nadie lo note |
| **`#ID` o `DT-nnn`** | La Tarea, o la fila de `aplicacion/deuda.md`, donde está el porqué y el riesgo |

El **porqué** y el riesgo no van en el comentario: van a la descripción del Merge Request, como
pendiente a confirmar en la tarjeta y, si se acepta como deuda, a `aplicacion/deuda.md` como
`DT-nnn` (por `cerebro-curator`, con el «sí» de una persona).

Para ver todo lo que un repo dejó para después: `bin/atajos.py --repo <repo> [--deuda <ruta a deuda.md>]`
(qué marca, en el encabezado del script); con `--base <rama de base>`, sólo lo que agrega el cambio. Una nota suelta, sin límite ni disparador, no es deuda registrada.

Una deuda sin registrar no es deuda: es un bug que todavía no se manifestó.

## Cómo se prioriza

No por lo fea que se ve. Por dos cosas:

- **Cuánto se toca.** Código enredado que nadie abre hace un año molesta poco. Código
  enredado que se toca todas las semanas cuesta en cada Tarea.
- **Qué rompe si falla.** Un módulo que decide si una operación del negocio sale o no pesa
  más que una pantalla de consulta.

Lo que se toca seguido **y** duele si falla: eso primero. El resto espera.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Suite en verde antes y después, ningún test tocado, sin cambio de comportamiento |
| **HALLAZGO** | Se tocó un test, o el refactor viene mezclado con un cambio de comportamiento |
| **SIN DATOS** | **No había tests antes de refactorizar.** No se puede afirmar que el comportamiento no cambió |

Ese `SIN DATOS` es el importante: refactorizar sin red y decir "quedó igual" es una opinión,
no una verificación.
