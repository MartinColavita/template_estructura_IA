# DoR de la Tarea: las cuatro piezas, en detalle

Parte de la skill `redactar-tarea`: se lee antes de redactar o corregir una Tarea, para armar las cuatro piezas que la dejan «lista para desarrollar» (§3.1 de la skill).

Una **Tarea** de capa `api`/`application`/`domain` (algo que otro código va a **llamar**)
**no se entrega como "lista"** sin estas cuatro piezas cerradas:

- **Contrato técnico (entrada/salida) cerrado** — así se llama la sección en
  [[plantillas/tarea]]. Para capa `api` va como **fragmento OpenAPI (YAML) parseable**;
  si no es HTTP, la firma entrada/salida. Es lo que después `armar-swagger` consolida y
  el dev implementa.
- **Especificación cerrada (SDD)** con la **tabla de Escenarios de la Historia** que
  esta Tarea cubre, y **qué test verifica cada uno**. Es la **bisagra entre BDD y TDD**: la
  Historia trae el Gherkin (loop externo), la Tarea trae los tests (loop interno), y sin esa
  tabla los dos loops quedan sueltos — nadie puede responder si los tests de la Tarea
  alcanzan para cerrar un Escenario. Los títulos de Escenario se copian **textuales** del
  campo Criterios de aceptación del padre.
- **Lista de "Tests a escribir PRIMERO" (test-first), numerada** — un caso por cada validación y por
  cada fila de "Casos de error". Es lo que después `guiar-tdd` ejecuta en Red-Green-Refactor.
  Va numerada porque la tabla de Escenarios los referencia por número. **Una línea por test**,
  y **30 tests o menos**: si la lista completa no entra, la Tarea es demasiado grande y se
  parte, no se recorta la lista ([[plantillas/tarea]] §«Tamaño y forma»). **Cada ítem enumera un solo
  comportamiento**; si trae dos del mismo contrato (una lista que filtra y la misma con una bandera que no
  filtra), se escriben como dos ítems o se dice en el ítem que son dos aserciones del mismo test. Un ítem que
  va a **nacer verde** por construcción (una idempotencia que ya da el esqueleto, un caso que cubre el verde
  mínimo de otro) se declara **guardarraíl** en la lista, para que el worker no tenga que descubrirlo. Si la
  Tarea toca una **migración de base**, el contrato dice qué pasa con las filas viejas y con las que el código
  viejo inserta durante la ventana (default o `NULL`, y cómo las lee el repositorio), y cómo se arma en un test
  una base «hasta la versión n» (helper de test o parámetro del migrador).
- **Bloque "Modos de falla evaluados"** — una línea por familia (**estado, concurrencia,
  autorización, dependencia caída, límites, idempotencia**), y cada una **o cubierta por un
  test de arriba, o descartada con su motivo escrito**. «Cubierta por el test n» vale sólo si el ítem n
  **enumera ese caso**; si no lo enumera, el caso es un ítem nuevo de la lista, no una nota al pie. Nunca ausente: un «no aplica porque…»
  es una afirmación auditable, el silencio no lo es. Es el bloque que evita que una familia
  entera se escape sin que nadie lo note — en las tres primeras Tareas reales del proyecto de origen, que
  no lo tenían, quedaron **trece familias en silencio** entre las tres, incluida la
  autorización de un endpoint que devuelve datos sensibles. Lo chequea [[auditar-tarea]]
  (chequeo 11).

## Exención parcial de la Tarea de front

**Exención parcial de la Tarea de front.** Una Tarea de **solo UI/config** (una columna
nueva en una grilla, un texto) está exenta del contrato y del bloque entero. Pero una Tarea
de front que **implementa un Escenario de la Historia** —aunque no tenga capa
`api`/`application`/`domain`— **igual lleva la tabla de Escenarios**: es la mitad visible de
un comportamiento que el back solo cubre a medias, y sin la tabla ese Escenario queda sin
dueño del lado del usuario. Lo que la Tarea de front **no** define es contrato propio:
consume el de las Tareas de backend.
