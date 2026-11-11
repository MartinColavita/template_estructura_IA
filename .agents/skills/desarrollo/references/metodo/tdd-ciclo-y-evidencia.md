# El ciclo rojo-verde, y qué cuenta como evidencia

> Método propio.
> Adaptado en parte de `wshobson/commands` (MIT) — ver [referencias-externas.md](../referencias-externas.md).

## Por qué existe esta página

Casi todas las guías de desarrollo mandan lo mismo: *escribí el test antes de generar o
modificar código funcional*. Estamos de acuerdo. El problema es que casi ninguna **pide una
prueba de que eso haya pasado**.

Un test escrito después, que nunca estuvo en rojo, cumple la letra del mandato al pie y no
cumple nada. Y no se nota: el archivo queda igual, el commit queda igual, la cobertura queda
igual. La única diferencia está en un momento que ya pasó y nadie miró.

Por eso acá el ciclo no termina en "el test pasa". Termina en **evidencia**.

---

## Las cuatro fases

> Las fases 1 a 3 son para **quien programa**; la 4 y lo que sigue (veredicto, entrega), para **quien verifica**.

### 1. ROJO — el test falla, y falla bien

Se escribe **un** test que describa el comportamiento que todavía no existe, y **se corre**.

Tiene que fallar. Pero no alcanza con que falle:

| Cómo falló | ¿Sirve? |
|---|---|
| **Falló la aserción** — corrió, llegó al final, y lo esperado no coincidió con lo obtenido | **SÍ.** Es el único rojo válido |
| Error de compilación o de carga: el runner de tests del repo ni llega a ejecutarlo | **No.** No probás nada: probás que falta una clase o una función |
| Un símbolo que no existe —clase, función o método sin definir—, un import roto | **No.** Idem |
| El test ni se ejecutó (error de configuración, dependencia faltante) | **No.** Ni siquiera corrió |
| Falló por un `fail()` puesto a mano | **No.** Eso no mide nada |

> **La regla, en una línea: un test que no puede llegar hasta su aserción no es un test
> todavía, es un esqueleto.**
>
> Por qué importa: si el rojo viene de que la clase o la función no existe, el test podría
> estar midiendo cualquier cosa —o nada— y no te enterás. Cuando esa clase o función
> aparezca, el test va a pasar a verde y vos vas a creer que verificaste un comportamiento.
> Verificaste que el código compila o carga.

**El rojo se registra en un commit** `test(rojo): <n.º de ítem> <resumen>` con **sólo el test**: ése es el
dato duro que `verificar-tdd` lee del historial, y la única evidencia que vale. El mensaje de la aserción
(lo esperado y lo obtenido) se guarda como apoyo, no como prueba: un texto pegado es indistinguible de
uno fabricado.

### 2. VERDE — el mínimo código que lo hace pasar

Nada más que eso. Sin adelantarse a casos que ningún test pide todavía.

**Cómo se llega al mínimo: la escalera.** **Una vez por Tarea**, antes del primer ítem, se lee el código
que el cambio toca y quién lo llama (cómo: [code-review.md](code-review.md) §«qué toca el cambio»). En
cada verde se para en el **primer escalón que alcanza**:

1. **¿Hace falta?** Si ningún ítem lo pide, no (lo de arriba); se nombra en una línea del resumen final.
2. **¿Ya existe en el repo?** Un helper, un componente, un caso de uso, un patrón: se usa como lo usa
   el código de alrededor.
3. **¿Lo resuelve la biblioteca estándar o la plataforma?** Se usa, salvo que el repo tenga lo suyo.
4. **¿Lo resuelve una dependencia ya declarada en el manifiesto del repo?** Se usa (no una que llegó de
   rebote con otra). Una nueva pasa por [dependencias-y-config.md](dependencias-y-config.md).
5. **¿Entra en una línea que se entiende de un vistazo?** Una línea.
6. **Si no:** el mínimo código nuevo que pone el test en verde.

Lo que la escalera no cruza:

- **La estructura no es abstracción de más:** las interfaces de `C1` ([[decisiones#DEC-002]]) aunque
  tengan una sola implementación, las capas y `exceptions/`, el resumen de clase de `C4`; en el front,
  lo que fije `arquitectura/frontend/`.
- **Nunca se recorta** la validación en los bordes de confianza, el manejo de errores que evita perder
  datos, la seguridad ni la accesibilidad. Eso también lleva su test: si la lista no trae el caso, se
  anota como pendiente a confirmar, no se agrega sin rojo.
- **Completo dentro del módulo:** se ajustan los llamadores y los datos de prueba que el cambio rompe, y
  el código que se mueve conserva su validación. Un llamador de otro módulo no se toca (`C7`): queda
  como pendiente. Un test existente que se rompe, como dice `guiar-tdd` (`chore(firma)` o rojo propio):
  cambiar lo esperado sin eso es mover el arco.

Un atajo tomado a sabiendas se marca con una línea `atajo:` ([refactor.md](refactor.md) §«Deuda técnica»).

Se corre **toda** la suite, no sólo el test nuevo: el verde de uno con el rojo de otros tres
no es verde.

**Se guarda la salida del verde**: igual que el rojo, las líneas del conteo del runner en el cuerpo del commit de la implementación.

### 3. REFACTOR — con la red puesta

Recién con verde se mejora la forma. Después de cada cambio, la suite entera otra vez.

Si en el refactor aparece un test en rojo, **se vuelve atrás**. No se ajusta el test para que
pase: eso es mover el arco.

### 4. EVIDENCIA — lo verifica otro

La corre **un agente distinto del que escribió el código**. Quien produce nunca aprueba.

Qué mira lo fija **una sola lista**: la skill `verificar-tdd` (y `bin/verificar-tdd.py`, que cuenta).
En una línea: rojo en la aserción y no por compilación, verde de la suite completa, un test una
condición, cada test puede fallar, todos los casos de la Tarea cubiertos. No se repite acá para que no diverja.

---

## Veredicto de tres estados

Nunca dos. Nunca un puntaje.

| Estado | Cuándo | Qué significa |
|---|---|---|
| **OK** | Se miró y está bien | Aprobado |
| **HALLAZGO** | Se miró y hay algo | Se describe, con archivo y línea |
| **SIN DATOS** | **No se pudo mirar** | **NO es aprobado** |

`SIN DATOS` es el estado que falta en casi todas las guías de revisión, y es el que más
importa. Sin él, *"no encontré nada"* y *"no pude fijarme"* se dicen con la misma frase, y el
segundo pasa por aprobado.

**No hay evidencia del rojo guardada → `SIN DATOS`.** No es "probablemente lo hicieron
bien". Es no auditable.

## Regla del cero

**Un conteo en cero sobre entrada externa no es un aprobado: es una señal de que no se
midió.** Cero tests que fallen, cero validaciones de entrada, cero casos de error — no
quiere decir que esté limpio. Quiere decir que no es auditable. Se reporta `SIN DATOS`.

---

## Cómo se entrega

```
TDD — <Tarea #NNNN> — <componente>

  ROJO     <N> tests, todos fallando EN SU ASERCIÓN
           evidencia: commit test(rojo): <n> <sha> (sólo el test); la salida del runner, de apoyo
  VERDE    suite completa: <N> pasan, 0 fallan
           evidencia: commit de implementación <sha>, posterior al rojo
  REFACTOR <sí/no>, suite en verde después de cada paso

  Verificado por: <agente distinto del que programó>

  OK .......... N
  HALLAZGO .... N   <- uno por línea, con archivo:línea
  SIN DATOS ... N   <- uno por línea, con el motivo

  SIN DATOS (no se pudo mirar) ........ N   <- frena
  SIN DATOS (pendiente declarado) ..... N   <- se lista, no frena (C8, SAST, cobertura, DEC-003)

  Veredicto: APROBADO sólo si BLOQUEANTES = 0 y SIN DATOS (no se pudo mirar) = 0.
```

**Dos clases de `SIN DATOS`.** «No se pudo mirar» (el script no corrió, la suite no se ejecutó, falta
la evidencia) **frena**: se dice qué falta para poder mirarlo. «Pendiente declarado» (C8, SAST, la
cobertura, la guía del stack con `<completar>`: lo que una `DEC-nnn` todavía no fijó) **se lista y no
frena**: ya está a la vista en el Cerebro, y frenar por eso dejaría todo parado hasta `DEC-003`. El
veredicto dice cuál es cada uno; el formato canónico de toda la cadena está en
`orquestador-desarrollo.md` §«Formato del veredicto».

> **Qué frena y qué no.** No todo hallazgo frena: lo fija la **severidad**, igual que en
> [code-review.md](code-review.md) y [merge-request.md](merge-request.md). Frenan los
> **BLOQUEANTES** —evidencia del rojo ausente o inválida, un test que no puede fallar, un caso
> de la Tarea sin cubrir— y frena cualquier `SIN DATOS` de los que no se pudieron mirar (el pendiente
> declarado se lista, no frena). Una **RECOMENDACIÓN** o una
> **SUGERENCIA** no frenan, pero **se responden**.
>
> Los tres documentos usan la misma fórmula a propósito: si cada uno tuviera la suya, el
> criterio de aprobación dependería de cuál se abrió primero.

---

## Cuándo TDD y cuándo test-después (declarado)

TDD es el **default**, no un dogma. Rinde donde hay un comportamiento verificable que escribir
antes: reglas de `domain`, casos de uso, endpoints con contrato, lógica de front. Y estorba donde
no hay comportamiento que afirmar todavía. La Tarea lo declara en **«Modo de pruebas»**:

| Modo | Cuándo | La red mínima que igual se exige |
|---|---|---|
| **TDD** (default) | Reglas de negocio, casos de uso, endpoints, lógica de front, arreglo de bugs | El ciclo entero con evidencia del rojo |
| **test-después**, con motivo | Esqueleto y scaffolding de un repo, configuración, migraciones de base, UI puramente visual | Esqueleto: el build y la suite vacía en verde; migración: el test antes/después de [migracion-de-base.md](migracion-de-base.md); UI visual: revisión humana y el test de aceptación del flujo |
| **sin tests**, con motivo | Un spike o prueba de concepto que **no va a producción** | Que se borre o se reescriba con TDD antes de entrar a una rama de entrega |
| **caracterización primero** | Código existente sin red ([refactor-y-migracion.md](refactor-y-migracion.md)) | El test que congela lo que hace hoy, antes de tocar |

**El campo «Modo de pruebas» de la Tarea gana sobre esta tabla**: si una migración de base declara TDD, es TDD (la
tabla sugiere, la Tarea decide). Lo que no está declarado se hace con TDD. Un «test-después» sin motivo escrito es un HALLAZGO;
uno con motivo es una decisión a la vista, y `verificar-tdd` audita la red mínima en vez del rojo
por ítem: `bin/verificar-tdd.py --modo test-despues --motivo "<el motivo de la Tarea>"` (el modo se pasa
**textual** desde el campo de la Tarea; sin declarar, es `tdd`).

## Lo específico de cada stack

- Back: [tdd-stack-back.md](tdd-stack-back.md)
- Front: [tdd-stack-front.md](tdd-stack-front.md)

Las dos son plantillas que se completan con el stack que elija el proyecto: dónde va cada
archivo, cómo se ve un rojo válido en el runner de tests del repo y con qué comando se corre
la suite. La estructura de los repositorios está en `arquitectura/esqueleto-proyectos.md` del
Cerebro.

## Qué NO cubre este ciclo

- **Tests de integración con dependencias externas reales**: sólo si la Tarea lo declara.
  Hay guías que los piden siempre; acá manda la Tarea.
- **Código que ya existe sin tests.** Ahí el ciclo no aplica hacia atrás: no se puede escribir
  el test primero de algo que ya está escrito. Para eso hay que ponerle una red antes de tocarlo,
  y la **propuesta del método** es ésta: antes de tocarlo, se le escribe un test que capture
  **lo que hace hoy** —sea correcto o no—, ejecutándolo y fijando su salida real como la
  esperada. Eso no valida el comportamiento: lo **congela**, y es lo único que avisa si el
  refactor lo cambió. Cuando después aparezca que ese comportamiento estaba mal, se arregla con
  el ciclo normal y el test congelado se reemplaza por uno que afirme lo correcto.
  ⚠ *Propuesta del método, a confirmar por el equipo.* Mientras no haya red, **no se
  refactoriza código sin tests.** Ver [refactor.md](refactor.md).
