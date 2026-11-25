# Los 16 chequeos de auditar-tarea

Parte de la skill `auditar-tarea`: se lee antes de auditar, para los chequeos de criterio que el script no hace.

## Los 16 chequeos sobre la lista de tests

### Completitud (¿falta algún test?) — es el bloque que evita el daño grave

1. **Cada validación tiene su test — una por regla, no una por campo.** Recorrer
   *Validaciones* y separar cada regla distinta: «obligatoria» y «formato válido» son
   **dos** reglas del mismo campo y necesitan **dos** tests. Una validación sin test es
   código que nadie prueba.
2. **Cada fila de «Casos de error» tiene su test, y el resultado esperado COINCIDE.**
   No alcanza con que la fila tenga un test: hay que comparar, palabra por palabra, el
   **payload de la fila**, el **resultado esperado del test** y el **schema del contrato**.
   Las tres cosas describen el mismo caso y pueden decir cosas distintas sin que nadie lo
   note — p. ej. la fila dice «telefono y email en null», el test dice «el objeto entero
   en null» y el contrato no declara `nullable` en ninguno de los dos. Esa contradicción
   hace imposible que el test y el contrato estén los dos en verde.
3. **Cada código de respuesta Y cada campo del schema tienen test.** Sacar del fragmento
   OpenAPI **todos** los códigos (`200`, `400`, `404`, `409`, `502`…) **y todos los campos
   del cuerpo de éxito**. Un código declarado y no probado es una promesa que nadie
   verifica; un campo declarado y no verificado se puede dejar de devolver sin que ningún
   test se ponga rojo. Chequear también los `nullable`: si un test espera `null` en un
   campo que el contrato no declara nullable, hay contradicción (ver chequeo 2).
   **Y cada valor de un catálogo cerrado.** Si el contrato declara `enum: [A, B, C]`, los
   **tres** tienen que aparecer en algún ítem. Ejercitar dos de tres y rechazar un cuarto
   valor **no prueba que el tercero esté aceptado**: se lo puede dejar afuera del enum y la
   lista entera queda en verde. Se cuentan los valores del enum contra los que aparecen en
   los ítems — no alcanza con ver que «el catálogo está cubierto».
4. **Cada `[RN-…]`/`[DEC-…]` citada existe Y dice lo que el test le atribuye.** Dos pasos:
   (a) abrir la regla en el Cerebro por su ruta — si no existe, ese punto es **NO
   AUDITABLE**, nunca «cumple»; (b) leerla y verificar que **contenga el criterio** que el
   test le cuelga. Una decisión que dice «se busca solo por identificador» **no** define el
   formato de la identificador: citarla en un test de formato es **trazabilidad falsa**, y es
   peor que no citar nada porque **simula cobertura**.
5. **Cada Escenario del Gherkin del padre que la Tarea declara cubrir tiene sus tests**, y
   los que cubre **en parte** nombran la Tarea complementaria **con su `#ID`** (el
   Escenario parcial solo se puede seguir si el número está escrito). Contar los
   `Escenario:` del padre contra las filas de la tabla más los títulos de la línea
   «No cubre» del pie ([[plantillas/tarea]]): tienen que dar igual. En modo lote, sobre el
   borrador, un `[T-nn]` vale como `#ID`; se vuelve a mirar después de escribir.

### Calidad (¿los tests sirven?) — sin esto, TDD es teatro

6. **Cada test es VERIFICABLE.** Tiene **input concreto → resultado esperado concreto**.
   «Valida bien la identificador» no es un test: no se sabe qué entra ni qué sale, así que
   dos devs escriben cosas distintas. Debe poder leerse como una aserción.
7. **Un ítem = UNA sola condición.** Prohibido unir dos casos con «o» / «y» en el mismo
   ítem. `guiar-tdd` escribe **un test por ítem**: si el ítem dice «el servicio devuelve
   error **o** timeout», se escribe **uno de los dos** y la otra rama queda sin probar,
   en silencio. Es el modo de falla más peligroso de todo el pipeline, y se detecta
   buscando conjunciones. Si el ítem tiene dos condiciones, el hallazgo es «faltan tests»,
   no «está mal redactado».
   **Un Esquema no es un ítem con dos condiciones.** Un ítem «Esquema» —`N. Esquema —
   <condición>:` y debajo una fila por caso, `<entrada> → <resultado esperado>`, en una lista
   con viñetas— vale como **un** ítem: `guiar-tdd` lo escribe como un test parametrizado con una
   fila por cada fila del ítem, y `verificar-tdd` comprueba que estén todas. Si las filas cambian
   la **condición** y no solo los datos, son ítems distintos y el hallazgo es «faltan tests». Si
   una fila no trae su resultado esperado, es «test no verificable» (chequeo 6).
8. **Cada test PUEDE FALLAR — y se declara si puede tener ROJO PRIMERO.** Preguntarse:
   *«¿qué código, escrito mal, haría que este test se ponga rojo?»*. Si la respuesta es
   «ninguno», el test es decorativo («el endpoint existe», «devuelve un JSON», «no tira
   excepción») → hallazgo.
   **Distinguir dos clases, porque el DoR las trata distinto:**
   - **Test del ciclo (default):** puede y **debe** arrancar en rojo. Entra en la evidencia
     rojo/verde que audita `verificar-tdd`.
   - **Test guardarraíl (regresión):** protege una **ausencia** — «ninguna clase del módulo
     depende de X», «no se filtra ningún campo fuera del contrato». **Nace verde a
     propósito**: su valor es bloquear la regresión futura, no producir el rojo de hoy.
     **Tiene que estar declarado como tal en el ítem**, y el DoD debe **excluirlo** del
     «todos los tests tuvieron su rojo previo». Un guardarraíl sin declarar convierte la
     Tarea en **imposible de cumplir**: `verificar-tdd` va a pedir una evidencia de rojo
     que no puede existir.

   **Dos filtros para no regalar la exención** — declarar guardarraíl **suprime** el commit
   de rojo de ese ítem (`guiar-tdd`), así que la etiqueta tiene que ganarse:
   - **Afirma sobre la FUENTE, no sobre el mismo observable que ya fija un test del ciclo.**
     Una constante, un catálogo, la estructura del módulo, las dependencias del módulo — no
     el DOM renderizado ni el cuerpo de una respuesta que otro test ya asegura.
   - **Ningún otro test de la lista lo implica lógicamente.** Si el test 1 dice «se ven
     **exactamente** estas tres opciones», un test que diga «no aparece esta cuarta opción»
     **no puede ponerse en rojo con el 1 en verde**: no es guardarraíl, es **redundancia**, y
     encima costó un rojo que sí existía. Preguntarse siempre: *«¿qué cambio pone en rojo
     este test y deja los demás en verde?»*. Si no hay ninguno, el ítem sobra (chequeo 13).
   - **Y el filtro de fondo:** en un componente que todavía no existe, ¿este test fallaría en
     el mismo instante que los del ciclo? Si sí, **podía tener rojo primero** y la exención
     no hacía falta.

   > **El ítem tiene que TRAER ESCRITA la respuesta, no dejarla para el auditor.** Todo
   > guardarraíl se redacta con la frase **«se pone en rojo si …»** adentro del ítem, nombrando
   > el cambio concreto que lo haría fallar. Ejemplo válido: *«se pone en rojo si alguien agrega
   > un canal a la constante de catálogo»*. Ejemplo que se cae solo: *«se pone en rojo si el
   > desplegable muestra una opción de más»* — eso ya lo detecta el test que exige «exactamente
   > estas tres».
   > **Si no se puede escribir esa frase, no es un guardarraíl.** Y si la frase describe algo
   > que otro test de la lista ya detecta, tampoco. La exención del rojo se **gana por escrito**:
   > sin esa frase, el auditor lo trata como test del ciclo y exige su rojo previo.
   > *Por qué esta regla:* el criterio anterior decía «protege una ausencia», que **describe cómo
   > se ve** un guardarraíl pero no **cómo verificar si el tuyo lo es** — y «el desplegable no
   > contiene el canal dado de baja» **es** una ausencia, así que la definición vieja admitía
   > justo el caso equivocado. Medido en el proyecto de origen, sobre sus cuatro primeras Tareas reales, con un
   > agente distinto por tarjeta: de las **dos** que reclamaron la exención, **una la tenía mal
   > otorgada** (redundante con su propio test 1), y una tercera dejó sin escribir el guardarraíl
   > que sí le correspondía. La pregunta contrafáctica (*¿qué lo pone en rojo dejando los demás en
   > verde?*) no sale sola al escribir una lista de tests: hay que obligar a escribirla.
9. **Hay al menos una invariante de negocio protegida**, no solo caso feliz + errores de
   formato. La invariante es lo que **nunca** puede pasar aunque el código cambie («un registro vencido
   no aparece en el listado»). Si la lista solo tiene validaciones de
   entrada, la lógica de negocio queda sin red.
10. **No hay tests de implementación.** Un test que se rompe al refactorizar **sin que
    cambie el comportamiento** prueba *cómo* en vez de *qué*. Señales: nombra clases
    internas, cuenta llamadas, depende del orden de ejecución.
    > **Este chequeo NO aplica a los guardarraíles del chequeo 8.** Un test de
    > arquitectura mira la estructura a propósito — esa es su función, no un defecto.
    > La diferencia: el guardarraíl falla cuando alguien **rompe una regla**; el test de
    > implementación falla cuando alguien **mejora el código sin romper nada**.

### Suficiencia (¿la enumeración misma está completa?) — el único bloque que mira hacia afuera

> Los chequeos 1 a 3 miden los tests contra las **listas que la propia Tarea declara**
> (Validaciones, Casos de error, códigos del contrato). Eso deja un agujero de fondo: si
> la enumeración está corta, la Tarea es **internamente perfecta** y pasa todo. Peor: como
> el chequeo 13 castiga los tests que no rastrean a nada, el camino más barato al veredicto
> COMPLETA es **enumerar menos**. Este bloque existe para contrarrestar ese incentivo.

11. **Modos de falla del recurso, declarados o descartados por escrito.** Tienen su sección
    propia en la tarjeta —**«Modos de falla evaluados»**, una línea por familia
    ([[plantillas/tarea]])—; **si esa sección no está, el chequeo es HALLAZGO, no OK**: la
    ausencia del bloque no se puede confundir con «no había nada que declarar». Recorrer las
    familias y verificar que cada una esté **o cubierta o descartada con su motivo**, nunca
    ausente:
    **estado** (la entidad en un estado que no admite la operación), **concurrencia** (dos
    operaciones simultáneas sobre la misma entidad), **autorización** (el usuario no puede
    operar sobre esa entidad), **dependencia caída** (el servicio o la base no responden),
    **límites** (tamaño, cantidad, rango de fechas) e **idempotencia** (repetir la misma
    llamada). Un «no aplica porque …» escrito es una afirmación auditable; el silencio no.
12. **Spec inventada por el redactor.** Cada validación y cada fila de Casos de error tiene
    que rastrear a una `[RN-…]`, al Gherkin del padre o al contrato de un sistema externo.
    Una condición que **decidió el redactor** sin respaldo — un límite de caracteres, un
    código de error, un plazo— es **especificación inventada**: hay que marcarla y
    preguntar de dónde sale. Hoy pasa inadvertida porque los tests que la cubren se ven
    perfectamente trazados… a una línea que alguien escribió de memoria.

### Coherencia (¿la lista cierra con el resto?)

13. **Ningún test sobra.** Cada uno rastrea a una validación, un caso de error, un código
    o campo del contrato, una `[RN-…]` o un Escenario. Un test que no rastrea a nada es
    alcance inventado.
14. **Ningún test depende de un `⚠ pendiente` sin declararlo.** Si el input o el resultado
    esperado no se pueden escribir hasta que el humano responda algo, el ítem tiene que
    decirlo. Escribirlo sin avisar obliga al dev a **inventar el valor**, y ese valor
    inventado queda como si fuera la especificación. Cruzar la lista de tests contra el
    bloque «Datos a confirmar»: **cada pendiente de ese bloque que afecte a un test tiene
    que aparecer marcado en el test**.
    > **Si la sección «Datos a confirmar» no está, este chequeo es HALLAZGO, no OK** — y si
    > está pero vacía sin decir «Ninguno.», también. El cruce es mecánico contra ese bloque:
    > sin bloque da `0 = 0` y **pasa por vacuidad**, que es la Regla del cero de `SKILL.md`
    > aplicada a esta misma skill. Una Tarea sin pendientes lo **declara** escribiendo
    > «Ninguno.»; el silencio no es una declaración ([[plantillas/tarea]]).
15. **Coherencia del test de integración y numeración.** Si el Alcance dice «Requiere test
    de integración: sí», tienen que estar las **tres** (test en la lista, subtarea que lo
    escriba, ítem en el DoD). Los tests están numerados y la tabla de Escenarios los
    referencia por número, sin saltos ni números inexistentes.
16. **El resultado esperado de cada test es producible por la CAPA que la Tarea declara.**
    Leer «Capa afectada» del Alcance y contrastarla ítem por ítem contra lo que cada test
    espera. Una Tarea que declara `domain`/`application` y **«no expone endpoint propio»**
    no puede tener tests que esperen un `400` o un `404`: ese código lo emite la capa `api`,
    que la Tarea dice no tener. El test queda **imposible de escribir dentro del alcance**, y
    el dev lo resuelve de una de dos maneras, las dos malas: inventando la capa que la Tarea
    excluyó, o dejando el test sin hacer.
    Y al revés: una Tarea de front cuyos tests **solo asertan sobre el DOM** no verifica el
    objeto que produce, aunque el DoD exija que coincida con el contrato del back — se puede
    renombrar un campo del estado y los siete tests siguen en verde.
    > Se escapa porque **los dos lados están bien por separado**: el alcance es correcto y el
    > test es correcto. Lo que no cierra es la **unión**, y nadie mira una unión salvo que
    > esté escrito que hay que mirarla.
