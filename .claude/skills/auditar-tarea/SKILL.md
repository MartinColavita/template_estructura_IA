---
name: auditar-tarea
description: >-
  (Solo lectura, adversarial) Auditar UNA Tarea técnica ya escrita —el segundo chequeo, hecho
  por un agente DISTINTO del que la redactó— con foco en la lista "Tests a escribir PRIMERO":
  que no falte ningún caso (cada validación, cada Caso de error, cada código del contrato
  OpenAPI, cada [RN-…] y cada Escenario del padre tienen su test), que ningún test sobre, que
  cada test sea VERIFICABLE (input concreto → resultado concreto), que PUEDA FALLAR (salvo
  guardarraíl declarado) y que cada ítem tenga UNA sola condición. Usar cuando se pida "auditá
  la tarea", "revisá los tests de la #NNNNN", "doble chequeo de la tarjeta", "¿esta Tarea está
  lista para desarrollar?", "/auditar-tarea". OPCIONAL: corre sólo a pedido y NO es requisito
  para arrancar el desarrollo (lo que encuentre queda como pendiente en la tarjeta). NO
  redacta, NO corrige, NO escribe en el board: devuelve hallazgos y preguntas. Español
  (Argentina).
---

# Auditar tarea

Audita **una** Tarea técnica contra su Historia padre. Es el **segundo chequeo** del
par: el primero lo hace quien escribe la tarjeta ([[cargar-a-azure]] §2b, autochequeo
al momento de escribir); este lo hace **otro agente, en otro turno, sin haber
participado de la redacción** (en modo lote, un sub-agente aparte, con su propio contexto,
cuenta como otro turno).

> **Es opcional y no frena el desarrollo** (decisión de diseño del template). Corre sólo cuando alguien
> la pide. Ni [[tomar-tarea]] ni el orquestador de desarrollo buscan su sello antes de arrancar:
> exigirlo gastaba muchos tokens y volvía a preguntar cosas ya cerradas o que no hacían falta
> para empezar. Lo que encuentre se deja **como pendiente en la tarjeta**, con
> [[comentar-tarea]] §«Pendientes a confirmar», y se mira al cerrarla.

## Regla de oro

- **Verificador ≠ productor.** Lo corre un agente **distinto** del que redactó o cargó
  la Tarea. Si sos quien la escribió, decilo y **no la audites**: pedí que la tome otro.
- **Adversarial, no complaciente.** El trabajo es **encontrar el hueco**, no confirmar
  que está bien. Una auditoría sin hallazgos es un resultado válido, pero recién
  después de haber buscado en serio.
- **Solo lectura.** No redacta, no corrige, no escribe en el board, no toca el Cerebro.
  Lo que encuentra sale como **hallazgo + pregunta**, nunca como arreglo silencioso.
- **En modo lote ([[planificar-lote]]) cada hallazgo sale marcado F o P.** **F**: lo
  resuelve una fuente (regla del Cerebro, maqueta vigente, respuesta del humano, contrato de
  otra Tarea), y se escribe cuál y el texto exacto del arreglo; lo aplica **el que redactó**,
  no esta skill. **P**: necesita a una persona. Un F sin su fuente escrita es un P.
- **No inventar.** Si falta contexto para juzgar (una `[RN-…]` que no está en el
  Cerebro, un contrato incompleto), se marca **NO AUDITABLE** en ese punto. Nunca se
  supone el comportamiento que "debería" tener.
- **Español (Argentina)**, sin emojis como íconos.

## Barreras

- **Solo lectura del board.** Nunca `create_work_item` / `update_work_item`.
- **No corrige.** Propone el texto del test que falta; escribirlo es otro turno y otra skill.
- **No aprueba por cansancio.** Si un punto no se pudo verificar, es NO AUDITABLE, no «cumple».
- **PHI prohibido** en el reporte (marcadores `<persona>`, `<documento>`, etc.).

## Insumos (los tres, o no se audita)

1. La **Tarea**: contrato técnico, validaciones, casos de error, tabla de Escenarios y
   lista de tests — con la herramienta de lectura del board que tenga el entorno (solo
   lectura), o pegada si este entorno no llega al tablero. En modo lote, el **archivo del
   borrador** (`borrador/lote-*/`), antes de que exista la tarjeta.
2. La **Historia padre**: sobre todo el campo **Criterios de aceptación** (el Gherkin).
   Se consigue con la herramienta de lectura del board que tenga el entorno; si este
   entorno no llega al tablero, se pide pegada. En modo lote, si el lote crea o pisa la
   Historia, su **borrador** (`borrador/lote-*/<clave>-criterios.html`): es la Historia como va a
   quedar, y auditar contra la del tablero daría huecos falsos.
3. Las **reglas citadas** (`[RN-…]` / `[DEC-…]`) en el Cerebro, por su ruta.

Si falta el 1, no hay nada que auditar. Si falta el 2 o el 3, se audita lo que se
puede y el resto sale **NO AUDITABLE** — nunca «cumple» por defecto.

> ### Regla del cero — un conteo vacío NUNCA es un «cumple»
> Casi todos los chequeos de abajo son **conteos contra un insumo externo**: los
> `Escenario:` del padre, las filas de Casos de error, los códigos del contrato. Si ese
> insumo viene **vacío**, el conteo da `0 = 0` y el chequeo **pasa por vacuidad**: no
> porque esté bien, sino porque no había nada que mirar. Es la falla más engañosa de
> todas, porque el reporte sale en verde.
> **Caso concreto y frecuente:** una Historia **sin Gherkin** (el campo Criterios de
> aceptación aparece vacío en la mayoría de las historias del board). Con 0 Escenarios,
> los chequeos 5, 13 y 14 «pasan» y el loop BDD↔TDD **no existe**, sin que ningún
> artefacto lo diga.
> **Por eso:** si un insumo externo viene vacío, el veredicto de ese punto es
> **NO AUDITABLE**, nunca PASA — y hay que decir **cuál** insumo estaba vacío. Si la
> Historia padre no tiene Escenarios, además se reporta que **no pasó su propio DoR**
> ([[definicion-preparado-terminado]]) y que derivar Tareas de ella es prematuro.

## Flujo

### 1. Conseguir los tres insumos
Leer la Tarea, la Historia padre y las reglas citadas. Si falta alguno, decirlo antes
de empezar y acotar el alcance de la auditoría.

### 2. Correr el script, y después los chequeos de criterio
**Primero el script** —lo corre esta skill, no se le pide a nadie—:

```
python bin/auditar-tarea.py <tarea.html> --historia <criterios-del-padre.html> --json
```

(La Tarea y los Criterios del padre van como archivos: en modo lote son los borradores; si no,
se guardan desde el tablero.) El script hace los chequeos de **conteo y forma**: secciones,
numeración, Escenarios del padre contra la tabla y la línea «No cubre», reglas que existen,
códigos del contrato y filas de Casos de error con su test, test de integración, enlaces,
HTML, guardarraíles, Modos de falla, Datos a confirmar y tamaño. **Esos no se rehacen a mano**:
su resultado se copia al reporte. Lo que el script marca HALLAZGO es hallazgo; si no corrió, esos
chequeos son SIN DATOS. Si esta herramienta no puede correr comandos, se le pide a la persona
ese comando exacto y se espera el resultado.

**Después, sólo los de criterio**: los que el script lista en «Lo que este script NO mira», más
confirmar o descartar sus AVISOS. Para cada hallazgo guardar **qué** falta o sobra y **contra
qué** se detectó (la validación, la fila de la tabla, el código del contrato, el Escenario). Un
hallazgo sin evidencia no se reporta.

Los 16 chequeos, uno por uno (Completitud 1–5 · Calidad 6–10 · Suficiencia 11–12 · Coherencia
13–16): `references/chequeos.md` (leerlo antes de auditar).

### 3. Dar un veredicto por Tarea

| Veredicto | Cuándo | Qué significa |
|---|---|---|
| **COMPLETA** | Los 16 chequeos pasan | No se encontró nada que falte |
| **CON HUECOS** | Falta al menos un test, o hay uno que no puede fallar | Lo que falta se deja como **pendiente a confirmar** en la tarjeta. **No frena el desarrollo** |
| **NO AUDITABLE** | No se consiguió la Historia padre, o una regla citada no existe en el Cerebro | Se dice qué no se pudo mirar, y queda como pendiente. Nunca se da por buena una Tarea que no se pudo auditar, pero **tampoco frena el desarrollo** |

**Tamaño (no cambia el veredicto).** Si la lista pasa de **30 ítems**, el reporte agrega
«conviene partir la Tarea» ([[plantillas/tarea]] §«Tamaño y forma»). No es un hueco: es una
Tarea demasiado grande para leerla y para desarrollarla de un tirón.

**Si se dan las dos a la vez** (faltan tests **y** hay un punto que no se pudo verificar),
el veredicto es **CON HUECOS + NO AUDITABLE en «el punto X»** — se reportan las dos cosas,
no se elige una. Ninguna de las dos frena el desarrollo, pero se arreglan por caminos
distintos: los huecos los cierra quien redacta la tarjeta; lo no auditable exige **cargar
la regla que falta en el Cerebro** o conseguir el insumo. Ocultar una detrás de la otra
deja media Tarea sin arreglar.

### 3-bis. Dejar el veredicto en la tarjeta (constancia, no barrera)

Un veredicto que vive solo en el chat de esta sesión se pierde: mañana otra sesión —u otra
persona, u otro LLM— abre el board y no sabe si se auditó. Por eso, cuando se corre, el
veredicto **se deja en la tarjeta** con [[comentar-tarea]] (que pide su propia confirmación
humana —en modo lote, la del cierre—; esta skill no escribe por su cuenta). Los hallazgos van
en el mismo comentario, como **pendientes a confirmar** ([[comentar-tarea]] §«Pendientes a
confirmar»), para que se vean al cerrar la Tarea. **El sello no habilita ni frena nada:** es
constancia de lo que se miró y cuándo.

El formato del sello, cuándo vence, cuál manda y cómo se verifica (`bin/verificar-sello.sh`), y
cómo sella el modo lote: `references/sello.md` (leerlo antes de escribir el sello o de juzgar uno
anterior).

**El sello no es requisito para desarrollar.** Ni el orquestador ni [[tomar-tarea]] lo buscan
antes de arrancar. Si alguien quiere saber si una auditoría sigue al día, corre
`verificar-sello` a mano; su resultado informa, no bloquea.

### 4. Reportar como hallazgos y preguntas
Agrupar por chequeo. Cada ítem: qué se detectó · evidencia · **la pregunta o el test que
falta**, redactado de forma que se pueda pegar en la tarjeta. No corregir la tarjeta:
eso lo hace [[redactar-tarea]] y lo carga [[cargar-a-azure]], con su confirmación. **Si la
Tarea está congelada** (en un sprint y ya tomada), [[cargar-a-azure]] no la edita: el arreglo
va como comentario y lo carga una persona a mano ([[cambios-en-el-backlog]] §4).

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| `references/chequeos.md` | Antes de auditar: los 16 chequeos de criterio, uno por uno |
| `references/sello.md` | Al dejar el veredicto en la tarjeta, o al juzgar si un sello anterior sigue vigente |
| `references/por-que-y-ejemplo.md` | Para el porqué de la skill, su lugar en el pipeline o un reporte de ejemplo |

## Contexto adicional

- DoR de la Tarea: [[redactar-tarea]] §3.1
- Consistencia del conjunto de Tareas (no de una): [[analizar-tareas]]
- Plantilla y secciones: [[plantillas/tarea]]
- Autochequeo al escribir: [[cargar-a-azure]]
