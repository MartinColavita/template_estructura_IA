# {{PROYECTO}} — Ecosistema de Agentes y Reglas

> Se carga en cada sesión y en cada subagente: la regla en una línea, el detalle donde apunta; las barreras de
> escritura y de worktrees, enteras, porque valen aunque no se cargue ninguna skill.

## 📁 Estructura del Proyecto

* **`documentos/`**: lo que entra (requerimientos, notas, reuniones, documentos de origen), de quien sea.
* **`cerebro-digital/`**: 🧠 **Bundle OKF (Open Knowledge Format)**. Fuente única de verdad.
* **`entregables/`**: lo generado y ya promovido desde `borrador/`. El código de la aplicación no vive acá (`DEC-001` en `cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md`).
* **`borrador/`**: 🧪 borrador de trabajo; nunca se versiona (`borrador/README.md`).
* **`tablero/`**: 🎫 método, plantillas y checklists para derivar tickets desde el Cerebro, para cualquier tablero (`DEC-006`).
* **`cerebro-digital/configuracion-ia/skills/`**: ⚙️ **33 habilidades**, fuente canónica: se edita acá y `bin/sync-skills.*` regenera los espejos `.claude/skills/` y `.agents/skills/`, que el hook y el CI verifican (`INSTALACION.md`).

---

## 🤖 Agentes

Cada agente tiene sus reglas y su DoD en `cerebro-digital/configuracion-ia/agentes/<agente>.md` (fuente única); el
orquestador de desarrollo, en `cerebro-digital/configuracion-ia/orquestador-desarrollo.md`.

| Agente | Qué hace | La regla que no se negocia |
|---|---|---|
| `orquestador-conocimiento` | Coordina el conocimiento (skill `cerebro-orquestador`) | El conocimiento de negocio que aparece en la conversación va a una Consulta Interactiva de Decisión por ítem (Guardar / Ignorar / Editar y Guardar), nunca como texto en la respuesta; en modo lote, al cierre |
| `cerebro-analyst` | De `documentos/` a un borrador con «Dudas y Preguntas» | Nunca escribe en el Cerebro ni en el código: todo a `borrador/` |
| `cerebro-curator` | Persiste en el Cerebro | Sólo lo que el humano validó, con frontmatter, wikilinks y firma en `log.md` |
| `cerebro-architect` | De maqueta y requerimiento a especificación técnica (`cerebro-architect-ui`) | Ningún control de interfaz sin su regla de negocio |
| `orquestador-desarrollo` | Despacha Tareas listas a workers en paralelo | Sólo Tareas con el DoR «lista para desarrollar» (contrato, SDD, Tests PRIMERO, Modos de falla; un `⚠` declarado no la saca); coordina, no programa; verifica otro agente (`DEC-005`); cada worktree pasa por el GATE de WORKTREE |

## 🎨 Skills que se cargan solas

Por si su descripción no llega al modelo: una **presentación** → `cerebro-ppt-generator`; **diseñar una pantalla** →
`disenar-con-stitch` (llama a `cerebro-mockup-design` y a `cerebro-architect-ui`); un **HTML o prototipo hecho a mano** →
`cerebro-mockup-design`; una **transcripción de reunión** → `cerebro-meet-analyst`; un **diagrama técnico** → `archify`;
el **manual o la documentación de la aplicación** → `documentar-aplicacion`.

---

## 📖 Instrucciones Obligatorias (Comportamiento y Lectura)

1. **Fuente Única de Verdad**: `cerebro-digital/` es la única fuente de verdad validada. Las memorias de herramienta (Engram, la de Claude Code, `bd`) no son fuente de reglas ni decisiones del proyecto: si contradicen al Cerebro, gana el Cerebro.
2. **Herramienta nativa de lectura**: los `.md` del OKF se leen con la herramienta nativa de lectura del entorno, nunca con comandos de terminal (`Get-Content`, `cat`, `type`).
3. **No asumir ni inventar**: lo que no está en el OKF queda pendiente del equipo funcional.
3.1. **Borrador antes que entregable**: todo documento funcional, mockup o presentación que genera un agente nace en `borrador/` (nunca versionado) y se promueve sólo cuando el usuario lo pide explícitamente: un mockup o una presentación a `entregables/`; una ficha o una regla, al Cerebro por `cerebro-curator`. **Nunca a `documentos/`**, que sólo recibe lo que se entrega. Nunca por iniciativa propia.
4. **Entregas directas**: al grano, sin narrar qué herramientas se corrieron, sin perder el tono conversacional.
5. **UTF-8 sin BOM y neutralidad**: se escribe con la herramienta nativa de escritura del entorno, y en reglas y skills se la nombra así («herramienta nativa de lectura/escritura»), nunca por su nombre en un entorno, para que valga igual en los cuatro (cómo carga cada uno: `INSTALACION.md` §«Carga por herramienta»).
6. **Orquestación obligatoria**: toda solicitud pasa por la skill `cerebro-orquestador`, con su Plan de Ejecución inicial (en modo lote, dentro del mensaje de arranque). Los tickets son un sub-flujo que el orquestador enruta a las skills del pipeline, que aplican además «Redacción y carga de tickets en Azure DevOps» (abajo).
7. **Todo en español (Argentina)**, en todas las herramientas y en toda misión que se delegue: un subagente no hereda el idioma de la conversación.
8. **Autocorrección consultada**: lo que la IA detecte mal o mejorable del propio ecosistema se registra como propuesta en `cerebro-digital/configuracion-ia/mejoras.md` y se pregunta **de a una**, con el cambio exacto y su impacto (skill `mejorar-ecosistema`). **Nunca aplica por su cuenta** un cambio de arquitectura, skills o scripts: sólo lo aprobado, con su prueba en OK. Una skill sin uso o redundante se propone sacar, nunca se saca sola.

---

## 🌿 Trabajo en paralelo (worktrees) — barreras

### GATE de WORKTREE (duro) — antes de crear uno

- **De dónde sale la rama se PREGUNTA, nunca se infiere.** El asistente propone la base con su porqué (qué rama está
  al día con `origin`, si la Tarea depende de otra sin mergear) y **espera el «sí»**; sin él, no se crea el worktree.
  Salir de la base equivocada no falla en el momento: aparece recién en el Merge Request, arrastrando trabajo ajeno.
  **Excepción:** `DEC-005` confirmada («Autorización permanente», en el GATE de confirmación).
- **Techo: entre 4 y 8 worktrees por máquina, nunca más.** Antes de crear uno se dice cuántos hay abiertos; al llegar a
  8 se frena y se avisa.
- **Con el árbol sucio, o si la rama ya tiene un worktree, se frena** y se dice qué hay o cuál es, antes del error de `git`.
- **Dos Tareas que tocan el mismo archivo van en serie.** ⚠ Regla candidata a confirmar por el equipo de devs.

### GATE de BORRADO de worktree (duro)

Borrar un worktree con trabajo sin pushear **no lo hace la IA nunca**: no hay papelera. Antes de cualquier borrado se
muestran los commits sin pushear, los cambios sin commitear, la rama y de dónde salió. Si hay algo sin pushear, se arma
el resumen y **lo borra el humano a mano**; con todo pusheado y el árbol limpio, alcanza **un** «sí».

**Las preguntas van siempre en criollo**: *«Voy a abrir un espacio de trabajo aparte para la Tarea #NNNN. Propongo
salir de `develop`, que está al día con el servidor. Tenés 3 abiertos de los 8 que conviene como máximo. ¿Arranco?»*
Una confirmación que el lector no puede evaluar no es una confirmación: es un trámite.

## 🎫 Redacción y carga de tickets en Azure DevOps

Reglas para cuando el asistente **redacta o carga work items** (historias, tareas, bugs, habilitadores), en Azure o en
cualquier tablero (`DEC-006`). Priman sobre cualquier atajo. El método y los moldes viven en `tablero/`
(`conocimiento/`, `plantillas/`, `checklists/`); las skills del pipeline, en `cerebro-digital/configuracion-ia/skills/`;
el MCP, en `cerebro-digital/configuracion-ia/integracion-azure-mcp/`.

### Reglas de oro (no negociables)

1. **Cero inglés en la prosa.** Gherkin en español: Característica, Antecedentes, Escenario, Esquema del escenario, Ejemplos, Dado, Cuando, Entonces, Y, Pero. Las siglas (INVEST, DoR, DoD, MoSCoW) llevan su explicación al lado; los campos, como se llaman en Azure en español ([[checklists/mapa-campos-azure]]; Gherkin: [[criterios-aceptacion-gherkin]]).
2. **PHI (dato real de una persona, incluidos los sensibles del dominio) = PROHIBIDO.** Marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>` (y los que sume [[contexto-proyecto]]). Si el insumo trae PHI, se reemplaza y se avisa.
3. **No inventar nunca.** Versión, ambiente, fecha, IDs, sprint, nombres y valores reales, y toda regla, comportamiento o estado que ninguna fuente defina («Fuentes que deciden»), se preguntan. Se puede proponer, marcado `⚠`: estructura, título, criterios tentativos, estimación, tipo. Una tarjeta que no se leyó no se reconstruye: se pide. Una `[RN-…]` se cita sólo si existe en el Cerebro, con su archivo.
4. **El tipo se decide primero** (Historia, Tarea, Bug, Habilitador técnico / Spike), con una frase de por qué; si no está claro, se pregunta.
5. **Criterios de aceptación en Gherkin español**, con al menos un caso feliz y un borde o error. En un Bug: resultado esperado, obtenido y por qué es un error.
6. **Se respeta la intención del autor**: se mejora la forma y se completan huecos, no se cambia el pedido; un tipo mal encuadrado se señala y se propone el correcto.
7. **Se pregunta sólo lo que ninguna fuente define** («Fuentes que deciden», abajo), todo junto, numerado y con la recomendación al lado, **y se espera la confirmación antes de dar algo por «listo»**; se cierra con «Queda pendiente de tu confirmación: …».
8. **Silencio al entregar**: el ticket, no el relato; afuera, sólo el tipo y su porqué, los `⚠` y el veredicto.
9. **Backlog ordenado y trazable**: exactamente **una** etiqueta temática, la misma en toda la descendencia (nunca el slice, el producto ni el repo; si no hay una acordada, se propone con `⚠`), Relaciones (Parent y Related; los `#ID` con `⚠` hasta confirmar), el documento fuente por ruta y las `[RN-…]` en los criterios. Para bajar una ficha: «Regla de cardinalidad». Detalle: [[organizacion-y-trazabilidad]].

### Fuentes que deciden (lo que ya está definido no se pregunta)

Antes de preguntar algo, se busca quién lo define. En este orden:

1. **El Cerebro** (`[RN-…]`, `[DEC-…]`, pendientes resueltos, decisiones registradas en la ficha).
2. **La maqueta vigente**, para el comportamiento de pantalla: textos, botones, avisos, estados vacíos, formatos, orden de campos. Vigente es **la que la ficha cita en `fuente_maqueta`**; una maqueta «propuesta», o que ninguna ficha cita, no decide. Si contradice una regla del Cerebro, **gana el Cerebro** y se avisa.
3. **Lo que el humano ya respondió**, en esta conversación.
4. **Los contratos de las tarjetas ya cargadas** (Tareas hermanas, el back que consume el front).
5. **Una recomendación técnica clara de la IA** (partición, nombres internos —clases, rutas, nombres de test—, patrones del esqueleto): se aplica y se lista, para que el humano la vete. No se pide respuesta por cada una. **No cubre** códigos HTTP, códigos de error, números de regla ni valores de negocio: esos siguen la regla de oro 3. Lo aplicado por recomendación tampoco se guarda en el Cerebro como decisión.

**Se pregunta sólo** un dato duro sin fuente, una regla o un comportamiento que ninguna fuente define **y que cambia un test o un Escenario**, o un choque entre dos fuentes del mismo rango. Lo ya respondido no se vuelve a preguntar. Esto no habilita inventar: lo que no tiene fuente sigue siendo pregunta o `⚠` declarado (regla de oro 3).

### Modo lote (planificación rápida)

Varios ítems de una vez ([[planificar-lote]]) en **dos turnos humanos**: el **arranque** (alcance, nivel y todas las
dudas juntas) y el **cierre** (la tabla del lote y **un «sí» que lo escribe**). Las barreras de abajo valen igual;
donde el lote cambia algo, lo dice la barrera.

### Auditorías: opcionales, a pedido

[[auditar-tarea]], [[auditar-historia]] y [[analizar-tareas]] **no corren solas** y su sello no habilita ni frena nada.
Lo que encuentran, o lo que aparece al programar, queda como **pendiente a confirmar** en la tarjeta ([[comentar-tarea]]);
antes de cerrar una Tarea se leen sus comentarios y los pendientes van en la pregunta del cierre, que decide la persona.

### Lo que se cuenta, lo cuenta un script

Todo chequeo de **conteo o formato** lo hace un script de `bin/`, no el modelo: cuenta siempre igual, tarda segundos y
no gasta tokens. Qué mira cada script: `bin/README.md`.

1. **La skill corre el script sola**, antes de leer nada a mano. Sólo si no puede —la herramienta no tiene terminal, o el script pide el token de la persona— le dice a la persona **el comando exacto** a correr, y espera el resultado.
2. **El modelo no reemplaza al script.** Lo que el script marca HALLAZGO no lo da por bueno el modelo. Un script que no corrió es **SIN DATOS**, no OK.
3. **El modelo hace sólo lo que pide criterio**, que el script lista al final de su reporte («Lo que este script NO mira»), y confirma o descarta sus AVISOS.

### Automatización por MCP — barreras al escribir en el board

Leer es libre; al **escribir** (`create_work_item`, `update_work_item`, `manage_work_item_link`, o el tablero local),
estas barreras no se negocian y valen aunque no se haya cargado ninguna skill:

- **GATE de TABLERO (duro).** Sólo el tablero autorizado: org `{{AZURE_ORG}}` · proyecto `{{AZURE_PROYECTO}}` · team `{{AZURE_TEAM}}`; con tablero local, la carpeta `backlog/` del módulo ([[tablero-autorizado]]). Si el destino no coincide exactamente o no se puede saber, **no se escribe** y se muestra la advertencia de [[tablero-autorizado]]. El token accede a toda la organización: por eso la barrera vive en la regla.
- **Sin acceso al tablero, ningún GATE que dependa de leerlo da OK**: la deduplicación y la tarjeta congelada son **SIN DATOS** —no «0 candidatos», no «no está congelada»— y no se escribe. Si se entrega texto para pegar a mano, arriba va: *«No busqué duplicados: buscalos vos en el tablero antes de pegar.»*
- **GATE de deduplicación (duro).** Antes de crear se busca por etiqueta + documento fuente + objetivo, **comparando objetivo y alcance, no título**. El preview lleva el **Bloque de dedup** (consultas, candidatos con `#ID`, link y estado, veredicto por candidato); sin él no se escribe, y el «sí» confirma contenido **y** dedup. **Ante la duda, es duplicado**: se muestra el `#ID` y se pregunta; un equivalente **bloquea el alta**. En modo lote, el bloque va por fila. Detalle: [[deduplicacion-antes-de-crear]].
- **GATE de confirmación (duro).** **Nunca** se escribe sin un «sí» explícito sobre el contenido **ya mostrado**: proponer y escribir son turnos distintos, una escritura por confirmación. Cuentan como una unidad el árbol de [[sincronizar-backlog]], el lote de comentarios de cierre que se mostró junto ([[comentar-tarea]]) y el lote entero de [[planificar-lote]]; lo que no está en su mensaje de cierre no se escribe.
  **Autorización permanente (`DEC-005`).** Con `DEC-005` confirmada en `arquitectura/decisiones.md`, lo que su tabla fija cuenta como el «sí» de este GATE, del de WORKTREE, del de edición destructiva y de G4, y se cita en el plan en vez de preguntarse; nunca autoriza *Closed*; lo que no fija se pregunta, y con la DEC en `⚠`, todo.
- **GATE de NIVEL (funcional vs dev/planning) — bloqueante en modo equipo.** En modo solo (`DEC-006` fijada) no se pregunta; con la DEC en `⚠`, sí. En modo equipo se crean sólo Épica, Feature e Historia; una **Tarea** exige confirmar **en su propio turno** que es contexto dev/planning, citando **textual** una frase **del humano, de esta conversación**, que no sea el pedido («creá las tareas» no alcanza); el rol nunca se infiere y, ante la duda, se pregunta; sin eso no se crea **ni se redacta**. En modo lote, la pregunta va en el arranque y nombra las Historias: la respuesta vale para las que nombra, no para otras. Toda Tarea usa la plantilla detallada ([[plantillas/tarea]]).
- **GATE de BORRADO y EDICIÓN DESTRUCTIVA (duro) — el nivel lo fija el daño.**
  - **Edición aditiva** (agregar, comentar, pasar a *Active*, relacionar): **un** «sí».
  - **Edición destructiva** (pisar una Descripción o unos Criterios ya escritos, vaciar un campo, un Estado terminal como *Closed*/*Resolved*): **dos** «sí» en turnos distintos, con el ANTES y el DESPUÉS a la vista entre uno y otro. **Excepción del modo lote:** pisar la Descripción o los Criterios de una tarjeta en `New`, sin asignar o de quien confirma, con el ANTES guardado en `borrador/lote-*/antes/` y la fila marcada **PISA**, va con el «sí» del cierre; vaciar un campo, un Estado terminal y borrar, nunca en el lote. **Excepción de `DEC-005`:** «Autorización permanente», GATE de confirmación.
  - **Borrado** (a *Removed* o a la papelera): **dos** «sí» **en turnos distintos**, mostrando exactamente qué se borra (título, estado, hijos, relaciones) entre una pregunta y la otra. El borrado permanente **no lo hace la IA nunca**, ni con dos «sí»: lo hace el humano a mano.
  - Las preguntas, **en criollo y sin siglas**, que el lector pueda evaluar: *«Voy a borrar la Tarea #NNNN "‹título›", que está en ‹estado› y cuelga de la Historia #MMMM. No se deshace fácil. ¿La borro?»*
- **GATE de TARJETA CONGELADA (duro) — en modo equipo (y con `DEC-006` en `⚠`).** Una tarjeta **en un sprint y con Estado distinto de `New`** sólo se **comenta** (`System.History`, y **ningún otro campo en esa escritura**): Título, Descripción, Criterios, Puntos, Etiquetas, Estado, Asignado, Ruta de iteración y relaciones no se tocan, ni con uno ni con dos «sí»; este GATE se chequea antes que los demás y, ante la duda, está congelada. Lo que se quería cambiar va como comentario con el DIFF ([[comentar-tarea]]) y lo aplica una persona; un hijo nuevo se vincula desde el hijo. Detalle: [[cambios-en-el-backlog]] §4.
- **Crear exactamente lo pedido**: un ítem pedido es un ítem; el árbol, sólo ante el pedido **explícito** de bajar una ficha o un módulo entero ([[sincronizar-backlog]]) o de derivar Tareas ([[planificar-lote]]).
- **Descripción en HTML**, nunca markdown crudo ([[checklists/mapa-campos-azure]]). **Ningún `⚠` sin declarar** en lo que se escribe; uno declarado en «Datos a confirmar», con su `P-nnn` o su pregunta, **su recomendación** y la marca en el test que depende de él, sí se carga.

### Regla de cardinalidad (conteo determinista)

El árbol sale **1:1** del bloque `## Derivación a backlog` de la ficha, no del criterio del modelo (lo arma
`bin/derivar-arbol.py`): una Épica por `[S-nn]`, una Feature por `[C-nn]`, una Historia por `[F-nn]` (el flujo, no la
pantalla), ni un nodo más ni uno menos; cero Tareas salvo el GATE de NIVEL, y entre todas cierran los Escenarios y las
`[RN-…]` del padre. **Sin el bloque, o con `⚠`, no se deriva.** Detalle y ejemplo: [[organizacion-y-trazabilidad]] §5.

### Pipeline, Cerebro Digital y skills

El dominio vive en el Cerebro; de ahí se derivan los tickets ([[pipeline-doc-a-tickets]]), que lo citan por ruta, sin
copiarlo. Toda escritura en el tablero, la haga la skill que la haga, pasa por las barreras de arriba.

---

## 🧩 Skills de desarrollo — cómo se usan

Todo lo que es **código** entra por **una sola puerta**: [[desarrollo]] (el método completo; lo del stack, en
`references/metodo/tdd-stack-*.md`, según `DEC-003`). Las skills que ejecutan dentro del código (`guiar-tdd`,
`verificar-tdd`, `auditar-codigo`, `armar-swagger`, `consultar-cerebro`, `diagnosticar-repo`) viven en `back/` y
`front/`.

Los **seis guardarraíles** (detalle en la skill `desarrollo`):

| # | Guardarraíl |
|---|---|
| G1 | **El código y el conocimiento no se mezclan.** En la zona gris, primero la Tarea (**qué**), después el método (**cómo**) |
| G2 | **Punto de entrada único**: ninguna guía de desarrollo, propia o ajena, se aplica sin pasar por `desarrollo` |
| G3 | **La precedencia está escrita, no se deduce**: un estándar corporativo se envuelve con una tabla de quién gana; lo que choca y no está, se pregunta |
| G4 | **Nada sale del repositorio hacia afuera sin un «sí» explícito** sobre lo que se publica, en su propio turno |
| G5 | **Lo externo se declara** en `DEPENDENCIAS-EXTERNAS.md`, con hash y detector de deriva; no se copia ni se instala, y sin servidor es `SIN DATOS` |
| G6 | **El lenguaje lo pone el repositorio**, también en los tests de pipeline y scripts (`sh` en el CI y el `Dockerfile`, sin preguntar); si con el del repo no se puede, se pregunta antes de escribir. No aplica al repo del Cerebro, donde `bin/` es Python |
