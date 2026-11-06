# Refactor y migración de una aplicación existente

> Método propio. Es el "cómo" de las Tareas que salen de [[planificar-modernizacion]] una vez que el
> humano decidió `DEC-004`; la red la pone [[caracterizar-comportamiento]] (`bin/paridad.py grabar`) y la
> secuencia por slice la conduce [[modernizar-slice]] (`bin/paridad.py comparar`, `bin/mapa-modernizacion.py corte`). Lo que es común a todo cambio (ciclo rojo-verde, evidencia, revisión,
> Merge Request) sigue siendo [tdd-ciclo-y-evidencia.md](tdd-ciclo-y-evidencia.md),
> [code-review.md](code-review.md) y [merge-request.md](merge-request.md); acá va sólo lo que cambia.

## La regla que ordena las dos

**Primero la red, después el cambio.** Una aplicación existente casi nunca trae los tests que el
método exige, y el ciclo rojo-verde no aplica hacia atrás: no se puede escribir el test primero de
algo que ya está escrito. Entonces, antes de tocar o de reescribir, se le pone una red:

- **Test de caracterización**: un test que captura **lo que la aplicación hace hoy**, sea correcto o
  no, ejecutándola y fijando su salida real como la esperada. No valida el comportamiento: lo
  **congela**, y es lo único que avisa si el cambio lo alteró.
- Cuando después aparece que ese comportamiento estaba mal, se arregla con el ciclo normal (un
  rojo que afirma lo correcto) y el test de caracterización se reemplaza. **Se registra como
  regla candidata** y pasa por la Consulta Interactiva: un bug viejo no se corrige por criterio
  propio, porque alguien puede depender de él.

El commit de la red se llama `test(caracterizacion): <qué congela>`, y `bin/verificar-tdd.py --modo caracterizacion`
exige que esté **antes** de cualquier commit que toque producción: primero se congela, después se toca. El script
acepta también un `test(rojo)` como primer commit: es el caso en que lo primero que se hace ya es un cambio de regla
decidido, con su rojo normal. Que la red **siga en verde después** no lo mira el script: lo mira el verificador
corriendo la suite completa (control 5).

Sin red no se refactoriza ni se migra: el veredicto es `SIN DATOS`.

## Refactor — se modifica en su lugar

La secuencia (red → límites → forma → reglas → verificación) y cómo se mide el avance están en una sola
skill: [[modernizar-slice]] → `references/refactor-en-el-lugar.md`. Acá, sólo las reglas que no cambian:

- **Un módulo por vez**, de adentro hacia afuera: `domain` primero, después `application`, después
  los adaptadores. Una Tarea sigue modificando **un solo módulo** (C7).
- **Refactor y cambio de comportamiento nunca en el mismo commit** ([refactor.md](refactor.md)).
  Un Merge Request que mezcla los dos no se puede revisar.
- **Los tests de caracterización no se tocan durante el refactor.** Si uno se pone en rojo, el
  refactor cambió algo: se vuelve atrás.
- **Lo que hoy viola `C1…C8` no se marca como HALLAZGO hasta que la Tarea que lo arregla exista**:
  se declara en `arquitectura/decisiones.md` qué código queda fuera de la regla y en qué orden se
  trae. Así el verificador no frena todo el repo el primer día.
- **El Doctor mide el avance**: las sondas de límites y de prácticas pasan de HALLAZGO a OK módulo
  por módulo. Esa tendencia es el indicador del refactor.

## Migración — se construye de nuevo en otro repositorio

La secuencia por slice (contrato → red → construido → paridad → cortado → apagado) la conduce
[[modernizar-slice]], con `bin/paridad.py` y `bin/mapa-modernizacion.py`. Acá, sólo las reglas que no cambian:

- **La aplicación vieja no se toca.** Es el **oráculo**: la fuente de verdad de lo que hay que
  reproducir hasta que una persona diga otra cosa. Lo único que se le agrega, si hace falta, es un
  desvío de tráfico por slice (patrón estrangulador), y eso es una Tarea con su propio "sí".
- **Paridad funcional como criterio de aceptación**: cada Historia migrada declara los casos que
  tiene que contestar igual que la vieja, y el test los corre contra las dos (o contra un registro
  de respuestas de la vieja, capturado con marcadores, nunca con PHI). Un caso distinto es un
  HALLAZGO o una decisión de cambiar el comportamiento, que se pregunta.
- **El contrato se saca del código viejo, no se diseña de cero**: endpoints, formas de respuesta,
  códigos de error reales. Lo que se quiera cambiar se cambia **después** de la paridad, como una
  Historia nueva. Si no hay contrato que sacar (no es una API), el oráculo son los flujos de
  pantalla: casos de uso con entradas y salidas observables.
- **Por slice, en el orden que diga la ficha** (`[S-nn]`): primero el que tiene menos dependencias
  y más valor. Un slice no se da por migrado hasta el corte de tráfico.
- **Datos**: la migración de datos sigue [migracion-de-base.md](migracion-de-base.md)
  (expandir/migrar/contraer), con conteos y sumas de control, y **nunca copiando producción a un
  ambiente de prueba**.
- **Corrida en paralelo** cuando el riesgo lo pide: la vieja y la nueva reciben lo mismo y se comparan
  las salidas antes del corte. Es caro; se usa en los flujos que dan plata.

## Lo que frena, en las dos

| Freno | Por qué |
|---|---|
| **No hay red** (caracterización o paridad) para lo que se va a tocar | Sin eso, "quedó igual" es una opinión |
| **Se encontró un comportamiento que parece un bug** y no se preguntó | Alguien puede depender de él |
| **PHI real** en fixtures, registros del oráculo o bases de prueba | Bloqueante, sin discusión |
| **`DEC-004` no está confirmada** | No hay plan sin decisión humana |
| **Una Tarea toca dos módulos** o un slice no cortado y la vieja a la vez | Dos cambios en uno: se parte |

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Red en verde antes y después; paridad o caracterización cumplida; sin cambio de comportamiento no declarado |
| **HALLAZGO** | Un caso distinto a la vieja sin decisión; un test de red tocado; un bug "arreglado" sin preguntar |
| **SIN DATOS** | **No había red** antes de tocar, o la paridad no se pudo correr contra el oráculo |
