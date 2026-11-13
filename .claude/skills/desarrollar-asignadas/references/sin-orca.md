
# Modo sin Orca (IntelliJ o terminal) — referencia de `desarrollar-asignadas`

> Este es el **modo de lanzamiento sin Orca** de [[desarrollar-asignadas]] (antes era una skill aparte;
> se fusionó por la propuesta M-002). El flujo, los GATEs, la misión (`bin/armar-mision.py`), los
> controles y el veredicto son los mismos; acá está sólo lo operativo de abrir worktrees con git y lanzar
> los workers y el verificador con `claude -p` o `gemini -p` desde IntelliJ o una terminal.

Es el **orquestador de desarrollo** ([[orquestador-desarrollo]]) para quien trabaja dentro de
IntelliJ y no usa Orca. Toma Tareas **ya listas**, abre un worktree por Tarea, le asigna un
worker (Claude Code o Gemini CLI), hace auditar lo producido por un verificador
independiente (`DEC-005`) y deja todo
listo para que el humano decida la entrega.

> Es el **modo sin Orca** de [[desarrollar-asignadas]] (la misma skill, elegido en su paso 0 por la
> variable `ORCA_APP_VERSION`). Los pasos de relevamiento, dependencias y repo destino son los de
> esa skill; lo que cambia es **cómo se abre el espacio de trabajo y quién lo programa**.

## Lo que NO hace

- **No programa.** El código lo escribe el worker; el orquestador coordina, adjudica y junta
  resúmenes.
- **No decide reglas de negocio.** Se implementa **sólo** lo que dice la Tarea y las reglas
  `[RN-…]` del Cerebro que la Tarea cita. Lo que no está no se inventa: queda como pendiente a
  confirmar ([[comentar-tarea]] §«Pendientes a confirmar»).
- **No elige por su cuenta** una decisión que el Cerebro tiene abierta (`⚠` en
  `arquitectura/decisiones.md`, `arquitectura/esqueleto-proyectos.md`, `pendientes.md`).
- **No autoriza la entrega.** Commit, push, Merge Request y cambio de estado los decide una
  persona, salvo lo que autoriza `DEC-005` confirmada ([[desarrollar-asignadas]] 6.3).

## Prerrequisitos — se chequean al arrancar, y se dicen

| Herramienta | Para qué | Si no está |
|---|---|---|
| `ORCA_APP_VERSION` (variable de entorno) | Saber que NO estamos en Orca | **Si está definida, no se arranca**: «Estás adentro de Orca. Para Orca está [[desarrollar-asignadas]].» y se termina el turno |
| MCP `azure-devops` | Leer las Tareas, tomarlas, comentar el cierre | **No se arranca.** Setup: `integracion-azure-mcp/00-index` |
| MCP `gitlab` | Leer los Merge Requests y sus notas de revisión en los repos de código (sólo lectura) | Se leen a mano en GitLab y se dice en el plan. Setup: `integracion-gitlab-mcp/00-index` |
| MCP `jetbrains` (servidor MCP de IntelliJ) | Build, tests, errores de un archivo, debug | Se corre el comando de build/test del stack en el worktree |
| MCP `GitKraken` + GitKraken Desktop | Estado de git y mostrarle al humano diffs y conflictos | Se muestra con `git` en la terminal |
| MCP `engram` | Continuidad entre sesiones ([[engram-memory-protocol]]) | Se sigue sin memoria y se dice |
| `gemini` (Gemini CLI) | Programar o verificar | Se avisa; con un solo motor verifica otro agente del mismo (paso 4) |
| `claude` (Claude Code) | Programar o verificar | Ídem |

`SIN DATOS` no es aprobado: una fila que no se pudo chequear se informa así, no como OK.

Los MCP se chequean **en la CLI de cada LLM que va a trabajar** (`claude mcp list`,
`gemini mcp list`): cada uno tiene su propia configuración, y que anden en la sesión del
orquestador no prueba que anden en el worker.

## Flujo

### 1. Relevar
Las Tareas que nombra el humano, o las asignadas a él como en [[desarrollar-asignadas]]
paso 1. Siempre dentro del tablero autorizado ([[tablero-autorizado]]).

### 2. Precondición dura, Tarea por Tarea
Sólo entra una Tarea que cumple el DoR «lista para desarrollar» ([[orquestador-desarrollo]]
§Precondición): contrato cerrado, «Especificación cerrada (SDD)», «Tests a escribir PRIMERO» y
«Modos de falla evaluados». Si le falta una de esas piezas, se devuelve al armado de la tarjeta.

**No se busca el sello de [[auditar-tarea]]**: la auditoría es opcional y no frena el
despacho (decisión de diseño del template). Un hueco o un gris de la Tarea queda como pendiente
([[comentar-tarea]] §«Pendientes a confirmar»), no se vuelve a preguntar.

### 3. Dependencias y repo destino
- **Dependencias:** [[desarrollar-asignadas]] paso 2. Libre o bloqueada, con el `#ID` del que
  depende. Además se informan las dependencias **fuera del lote** que todavía no mergearon:
  cambian de qué rama conviene salir (GATE de WORKTREE). Dos Tareas que tocan el mismo archivo
  van **en serie** (⚠ regla candidata del GATE de WORKTREE).
- **Repo destino:** [[desarrollar-asignadas]] paso 3.2 (evidencia en la tarjeta) y 3.3 (cómo se
  decide), salvo su viñeta de Orca, que acá no aplica.
- **Dónde se buscan los repos — ⚠ decisión abierta.** El Cerebro tiene escrito que se clonan
  **adentro** de este repositorio, en `back/<repo>` y `front/<app>`
  ([[orquestador-desarrollo]] §Dudas y Preguntas). En la práctica pueden estar **al lado**
  (por ejemplo `Backend/<repo>`, `Frontend/<repo>` en la carpeta padre). Hasta que se decida,
  se buscan en los dos lugares, cada carpeta que sea un repo git, y se muestra en el plan de
  dónde salió cada uno. Si aparece el mismo repo en los dos, o en ninguno, **se pregunta**.
- **Se excluyen** este repositorio, la carpeta de worktrees y los repos de infraestructura
  (los que el equipo declare como tales), salvo pedido explícito del humano para esa Tarea (regla del usuario: la
  infraestructura no se toca sin pedido; ⚠ todavía no está escrita en el Cerebro).

### 4. Qué LLM programa y quién verifica

> Con `DEC-005` (modo desatendido) **confirmada** en `decisiones.md`, el motor, los permisos, la carpeta de
> worktrees y la base salen de la DEC y se citan en el plan; lo que sigue aplica cuando la DEC no existe o
> está en `⚠`.
Motor y verificador, como en [[desarrollar-asignadas]] paso 4 (con motor único, no se pregunta). Con dos
motores, en su propio turno:

> *«¿Con qué querés programar estas Tareas: Claude o Gemini? Podés elegir uno para todas o uno
> distinto por Tarea. El chequeo lo hace el otro.»*

Si no hay verificador disponible, se avisa **antes** de despachar y esa Tarea **no se despacha**:
programar algo que después nadie independiente puede verificar deja la entrega sin control.

### 5. Plan y confirmación — un turno propio
Antes de armar el plan se corren los chequeos de antes de despachar de
[[orquestador-desarrollo]] §«Convenciones del Cerebro: reglas que se chequean» (Cerebro de
`develop` al día con `main`, el `ARCHITECTURE.md` de la carpeta `docs` del repo, Tareas que tocan los mismos archivos
y Tareas de más de 20 archivos), y lo que encuentren va en la tabla.

Se muestra, en criollo, y se termina el turno:

| Tarea | Repo | Rama | Sale de (propuesta y por qué) | Worktree | Programa | Verifica | Estado |
|---|---|---|---|---|---|---|---|

«Programa» y «Verifica» salen del paso 4.

Antes de armarla se corre `git -C <repo> fetch` en cada repo destino (sólo lee del servidor),
para que «Sale de» se apoye en ramas al día y no en referencias viejas.

Junto con la tabla:
- **Cuántos worktrees hay abiertos en la máquina**: `git worktree list` de **todos** los repos,
  incluidos este repositorio y los de infraestructura (el techo es por máquina), sin contar el principal
  de cada uno. Cuántos quedarían. Techo: **8**. Las Tareas que lo pasarían quedan **pendientes
  en el plan**, sin tomar ni abrir, para la próxima corrida.
- **Por cada repo destino:** si tiene el árbol sucio (qué hay) y si la rama propuesta ya existe
  o ya tiene un worktree (cuál). Se muestra **acá**, antes del "sí" y antes de tocar el
  tablero: una Tarea que no se va a poder abrir no se toma.
- Las bloqueadas, con su dependencia.
- Lo que quedó `SIN DATOS` en los prerrequisitos.
- Las preguntas de «Decisiones abiertas» que hoy se resuelven acá: **autorización de commits
  locales** por Tarea, y el **modo de permisos** de quien programa y de quien verifica.

Sin un "sí" explícito sobre esta tabla, no se toca nada.

### 6. Tomar cada Tarea
[[tomar-tarea]], con sus barreras (otra persona, tarjeta congelada). Es escritura en el
tablero: confirmación propia.

### 7. Abrir el worktree — GATE de WORKTREE
Por cada Tarea libre, con el "sí" del paso 5 sobre la base de **esa** Tarea:

- **Ubicación — propuesta, se confirma en el paso 5:**
  `<carpeta padre de este repositorio>/worktrees/<back|front>-<ID>`. No vive adentro de ningún
  repo, así que no se versiona en ninguno. Si el humano usa otra carpeta, va la suya.
- **Sólo sobre repos de código** (back o front). **Nunca un worktree de este repositorio.**
- **Rama:** la convención real de `metodologia/convenciones-git.md`:
  `task/<ID>-<slug>` (o `bugfix/`, `hotfix/`), con el ID de la Tarea, no de la Historia.
- **Comando:** `git -C <repo> worktree add <ubicación> -b task/<ID>-<slug> <base confirmada>`.
- **Se anota el SHA de la base** en ese momento (`git -C <repo> rev-parse <base confirmada>`):
  el verificador audita `<sha-base>..<rama>`, que no se mueve aunque la rama base avance.
- **Base al día (regla dura).** Todo lo que se envía contempla lo último de la rama base, sin
  importar cuándo se empezó el trabajo. Antes de despachar **cualquier** worker o verificador
  —también sobre un worktree que ya existe (ajuste, retoma, verificación)— y antes de abrir o
  actualizar un MR: `git -C <worktree> fetch origin` y `git -C <worktree> rev-list --count
  HEAD..origin/<base>`. Si es mayor que 0, se trae `origin/<base>` a la rama **con merge, nunca
  rebase** (ya se pusheó: no se reescribe historia), se resuelven los conflictos, se corre la
  suite completa (el comando de la suite completa del stack) y, si hay `openapi.yaml`, Spectral,
  y se anota el **nuevo SHA de base** (el audit pasa a ser `<nuevo-sha-base>..<rama>`). Si el
  conflicto cambia comportamiento o la suite queda en rojo por lo traído, se frena y se avisa en
  criollo: no se despacha. La misión del worker y la del verificador dicen que la rama ya
  contiene la base al día y con qué SHA. Sin eso la misión no sale.
- **Justo antes de crearlo se vuelve a chequear** (pudo cambiar desde el plan): si el repo
  tiene el árbol sucio (se muestra qué hay), si la rama ya tiene un worktree (se dice cuál) o
  si se llegó a 8, **se frena** y se avisa.

### 8. Despachar el worker
**Misión autocontenida** ([[cerebro-orquestador]] §«Compresión de handoffs»): objetivo, rutas y
resultado esperado. Nada del historial del chat. Las skills **no se heredan**: van por ruta
absoluta. En lo que sigue, `<núcleo>` es la ruta absoluta de este repositorio: el worker está
parado en otro repo, así que una ruta relativa no le sirve.

**Antes de despachar** rige la «Base al día» del paso 7, también en un worktree que ya existe;
la misión dice que la rama la contiene y con qué SHA.

**La misión la arma `bin/armar-mision.py`** (`--rol worker --entorno intellij --motor <claude|gemini>`),
la misma plantilla que en Orca, para que dos sesiones con la misma Tarea reciban lo mismo. Lleva: idioma
(todo en español); la Tarea **completa** pegada, con su link y el Gherkin de la Historia padre (el worker
no reconstruye la tarjeta); el worktree, la rama y el SHA de base (se trabaja **sólo** ahí, `git -C
<worktree> …`); `<núcleo>/AGENTS.md`; el método por ruta absoluta (`tdd-ciclo-y-evidencia.md`,
`crear-endpoint.md`, `contrato-openapi.md`, la guía de TDD del stack); las skills (`guiar-tdd` y, en
back, `armar-swagger`; **no** `auditar-codigo`, que es del verificador); la arquitectura
(`esqueleto-proyectos.md`, `decisiones.md`, `aplicacion/`, y en front `arquitectura/frontend/`); las
convenciones C1 a C8 **copiadas** de [[orquestador-desarrollo]]; los límites (sólo lo que dicen la Tarea y
sus `[RN-…]`, lo gris como pendiente a confirmar, sin PHI, un módulo, sin push ni Merge Request ni tablero,
el núcleo se lee y no se escribe); el modo de pruebas; el resultado esperado (estado, commits rojo → verde,
tests, archivos, pendientes a confirmar, conocimiento para el Cerebro y memoria de la aplicación); y el
canal: una línea `PREGUNTA-ORQUESTADOR: …` sola y termina el turno; al final `TAREA-TERMINADA` o
`TAREA-FALLIDA`. El texto **no vive acá**: cambiarlo es cambiar el script y su prueba.

**Antes de despachar, foto del núcleo:** se guarda `git -C <núcleo> rev-parse HEAD`, un hash
de `git -C <núcleo> diff HEAD` (el contenido, no sólo los nombres: el núcleo puede estar sucio
de antes) y la lista de `git -C <núcleo> ls-files --others --exclude-standard`. Lo que un worker escriba en el núcleo aparece en el git del
**núcleo**, no en el del worktree; por eso se compara contra esta foto (paso 9).

**Cómo se lanza**, en segundo plano, uno por worktree, sin pasar el techo:

| LLM | Cómo |
|---|---|
| Claude | **Nunca como sub-agente interno**: lo que escribe en un worktree va a la vista ([[desarrollar-asignadas]] §Barreras). Parado en el worktree: `claude -p "<misión>" --session-id <uuid nuevo> --add-dir <núcleo> --permission-mode <el elegido en el paso 5> --output-format json > <carpeta de worktrees>/<ID>.claude.json` |
| Gemini | Parado en el worktree: `gemini -p "<misión>" --include-directories <núcleo> --approval-mode <el elegido en el paso 5> -o json > <carpeta de worktrees>/<ID>.gemini.json` |

- Los comandos de terminal se corren **en segundo plano** (el orquestador no espera a cada uno)
  y la salida queda en ese `.json`, **fuera de los repos**. El orquestador lo lee al terminar.
- Se anota por Tarea: LLM, worktree, archivo de salida y cómo se reanuda la sesión (paso 9).
- `--add-dir` / `--include-directories` suman el núcleo **como carpeta de trabajo**: el worker
  lo necesita para leer las skills y el Cerebro, pero según el modo de permisos **también
  podría escribirlo**. Por eso va el límite del punto 7 de la misión y la foto del núcleo.

### 9. Seguir sin programar, y atento
- El orquestador espera los resultados; no relee el código del worker. **Queda atento hasta que
  el último worker termina**: cada worker corre en segundo plano y su final despierta al
  orquestador. **Apenas termina uno, se le avisa al humano** —*«Terminó la #NNNN: ‹resumen›.
  Arranco la verificación con ‹el verificador›.»*— y se sigue con el paso 10. No se da el
  trabajo por terminado mientras quede un worker o un verificador corriendo. Si un worker
  termina frenado o falla, se avisa igual y se da el resumen del paso 13-bis.
- **Al terminar cada worker, se compara el núcleo contra la foto del paso 8.** Si cambió algo
  (archivos o `HEAD`), se frena todo, se muestra qué cambió y decide el humano. No se limpia
  nada por cuenta propia.
- Una pregunta del worker se le trae al humano **tal cual**, en criollo, con la Tarea al lado.
  La respuesta vuelve al **mismo** worker, con su contexto:
  - `claude -p`: `claude -p "<respuesta>" --resume <el uuid del paso 8>`, parado en el mismo
    worktree;
  - `gemini -p`: `gemini --list-sessions` en el mismo worktree para ubicar la sesión, y
    `gemini -p "<respuesta>" --resume <esa sesión>`. ⚠ Confirmarlo en la primera corrida real.
  Si no se puede reanudar, se avisa: lanzar uno nuevo arranca sin el contexto de lo hecho.
- Umbrales de [[cerebro-orquestador]] §«Orquestación de sub-agentes»: ~20 llamadas o un
  incidente (directorio equivocado, accidente de git) → pausar, auditar y replanificar.

### 10. Verificar con otro agente
Antes de lanzarlo rige la «Base al día» del paso 7: la misión del verificador lleva el SHA de
base vigente (si se trajo `develop`, el nuevo).

Se lanza igual que en el paso 8 pero con **el verificador** (el otro LLM si hay dos; si no, el
mismo motor con contexto limpio, `DEC-005`), en el mismo worktree (por eso, antes y
después de verificar se mira `git -C <worktree> status --porcelain`: si el verificador dejó algo
—por ejemplo, un test que reescribió un archivo—, se frena y decide el humano), con el modo de
permisos elegido para verificar en el paso 5. **Si verifica Claude**, además con `--disallowedTools "Edit"
"Write" "NotebookEdit"`: sin herramientas de edición, como el sub-agente de la skill (Bash queda para los
tests y el git de lectura; lo que igual escriba lo muestra el `status` de después). **Si verifica Gemini**, siempre con
`--approval-mode plan --policy <núcleo>/bin/gemini-verificador-solo-lectura.toml`: el modo
`plan` solo no es de sólo lectura (sin interacción pasa solo a modo automático, y deja escribir
archivos `.md` sueltos); la política lo cierra y deja correr sólo los comandos de git de lectura
que necesita `verificar-tdd`, los tests y el linter de OpenAPI (Spectral) con el ruleset `bin/spectral-oas.yaml` del repositorio del Cerebro (el comando exacto va en la misión). El modelo es el que fije `decisiones.md`; sin decisión, el que Gemini CLI trae por defecto (no se fuerza `-m`). Si la salida dice `Policy file error`, Gemini corrió **sin** la política: el
veredicto es SIN DATOS y se avisa. **No lee de Engram nada de esa Tarea** ni el
resumen del worker: verifica sobre el repositorio y la tarjeta. Si leyera lo que dejó quien
programó, dejaría de ser independiente.

**Cómo se sabe qué motor verificó:** el `.json` de salida trae los modelos que se usaron —en
`stats` si es Gemini, en `modelUsage` si es Claude—; con eso y `gemini --version` (o `claude
--version`), el comentario de cierre y el resumen lo registran con el formato «‹motor› v‹versión› · ‹modelo o worktree›», por
ejemplo «Gemini CLI v0.62.0 · gemini-2.5-pro». Sin ese dato, va `⚠ sin dato`.

**La misión del verificador la arma `bin/armar-mision.py`** (`--rol verificador --entorno intellij --motor
<el otro>`): la Tarea completa con el Gherkin del padre (el verificador no lee el tablero ni usa MCP), el
worktree, la rama y el **SHA de la base** del paso 7 (se auditan los commits `<sha-base>..<rama>`; si la
rama ya se reorganizó y se pusheó, la evidencia anterior está en `<sha-base>..evidencia/<ID>`),
`<núcleo>/AGENTS.md`, las skills por ruta absoluta de la tabla de abajo con los comandos exactos de
`verificar-tdd.py` (con el `--modo` de la Tarea) y `auditar-diff.py`, los límites (**no escribe** código,
no commitea, no pushea, no toca el tablero ni el núcleo, no consulta Engram sobre esta Tarea, no delega, sin
PHI) y el resultado esperado: el bloque `VEREDICTO-INICIO … FIN` de [[orquestador-desarrollo]] §«Formato
del veredicto», con un veredicto por control y las dos clases de `SIN DATOS` separadas.

Al terminar el verificador, **el núcleo se compara contra la foto** igual que en el paso 9: el
verificador también lo tiene como carpeta de trabajo.

| Control | Pregunta | Skill |
|---|---|---|
| 5 | ¿El ciclo rojo → verde ocurrió? | `<núcleo>/back/.claude/skills/verificar-tdd/SKILL.md` (o `front/`) |
| 5-bis | ¿El código está bien escrito? | `<núcleo>/cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/code-review.md` (revisión por dimensiones) en cualquier motor; en Claude Code, `/code-review` es un atajo válido |
| 5-ter | ¿La entrega cumple contrato, límites de módulo, tests, sin PHI ni secretos? | `<núcleo>/back/.claude/skills/auditar-codigo/SKILL.md` (o `front/`) |
| 5-quater | ¿Cumple las convenciones del Cerebro, una por una? | Las reglas C1 a C8 de [[orquestador-desarrollo]] §«Convenciones del Cerebro: reglas que se chequean», copiadas en la misión, con un veredicto por regla |

Los cuatro son preguntas distintas: **el 5-ter y el 5-quater no se saltean aunque el 5-bis salga limpio**
([[orquestador-desarrollo]] §Ciclo por Tarea).

### 11. Mostrarle al humano
- **Diffs, historial y conflictos:** se abre el worktree en GitKraken Desktop
  (`gitkraken -p <ruta del worktree>`), o con la herramienta externa «Abrir en GitKraken» de
  IntelliJ, si la configuraste en tu máquina (no viaja con el repositorio).
- **Errores, build y tests en el IDE:** el humano abre el worktree en IntelliJ (*File → Open*) y
  ahí se usan las herramientas del MCP `jetbrains` **pasando siempre `projectPath`** con la ruta
  del worktree (`get_file_problems`, `build_project`, `execute_run_configuration`). Sólo actúan
  sobre proyectos abiertos en IntelliJ; si no está abierto, se corre el comando de build/test del stack en el
  worktree.

### 12. Entrega — decide el humano
Con los cuatro veredictos a la vista, el humano decide. **Push y Merge Request: un "sí" explícito
por cada acción**, en GitLab no se escribe nada sin esa autorización puntual. Con `DEC-005`
confirmada, el «sí» del push lo da su «Aprobar» automático ([[desarrollar-asignadas]] 6.3).
- **Antes del push, la rama se reorganiza** **por importancia**, uno por cambio lógico
  (alrededor de 10 commits, como guía), con mensajes específicos: lo hace el orquestador (es git,
  no código), con el respaldo `evidencia/<ID>` subido a `origin` sin Merge Request y el chequeo `git diff evidencia/<ID> HEAD` vacío ([[orquestador-desarrollo]] §«Commits: de trabajo, y pocos en el Merge Request»). Sólo lo que
  nunca se pusheó.
- **Push:** lo corre el orquestador, nunca el worker, y sube **la rama de respaldo y la de la
  Tarea**: `git -C <worktree> push -u origin evidencia/<ID>` y `git -C <worktree> push -u origin
  <rama>`, con un "sí" por Tarea. Ninguna de las dos se borra del servidor hasta que termina el
  sprint. **Ese "sí" nombra también la reorganización y el respaldo** —*«subo el respaldo
  `evidencia/<ID>`, reorganizo la rama en N commits y pusheo»*—: sin él no se reorganiza, para que la rama no quede
  reescrita si el push se niega. Después se le deja al humano el link armado del Merge Request:
  `https://<host-gitlab>/<grupo>/<proyecto>/-/merge_requests/new?merge_request%5Bsource_branch%5D=<rama>&merge_request%5Btarget_branch%5D=<base>` (el `<grupo>/<proyecto>` sale de `git remote get-url origin`; sin `target_branch` GitLab apunta a la rama por defecto, que puede no ser la base).
- **Merge Request:** el MCP `gitlab` está en **sólo lectura**, así que no lo abre: lo abre
  el humano.

### 13. Comentario de cierre
[[comentar-tarea]] §«Comentario de cierre de desarrollo»: rama, Merge Request y resumen técnico,
con los veredictos de 5, 5-bis, 5-ter y 5-quater, y los **pendientes a confirmar** que devolvió el
worker. Los datos duros salen del repositorio, no de la memoria del worker; lo que no se pudo
leer va `⚠ sin dato`. **No cambia el Estado de la Tarea**, salvo [[desarrollar-asignadas]] 6.3,
punto 4. Cerrarla lo decide una persona, y antes se le muestran los pendientes sin resolver
([[comentar-tarea]] §«Antes de cerrar una Tarea»).

### 13-bis. Resumen al humano, siempre
Al terminar cada Tarea —entregada, frenada o fallida— el orquestador le da al humano el resumen
de qué se hizo y qué quedó pendiente, con el molde de [[orquestador-desarrollo]] §«Resumen al terminar cada Tarea». Al terminar el lote, la tabla con
todas.

### 14. Memoria y limpieza
- **Engram**, si está: [[engram-memory-protocol]]. El verificador no lo consulta sobre la Tarea que
  audita (paso 10).
- **Borrar un worktree:** GATE de BORRADO de `AGENTS.md`. Se muestra lo que hay sin pushear y
  sin commitear; si hay algo, **lo borra el humano a mano**.

## Barreras

- **Los datos del GATE de WORKTREE los da `bin/gate-worktree.py`** (worktrees abiertos en la máquina,
  árbol sucio, rama ya con worktree, base atrás de `origin`) y los del cierre, `bin/datos-cierre.py`.
  La pregunta al humano se hace con esos números a la vista; un script que no corrió es `SIN DATOS`.

- **GATE de TABLERO** y los demás GATES de escritura en Azure de `AGENTS.md`: tomar y comentar
  pasan por [[tomar-tarea]] y [[comentar-tarea]], que los aplican.
- **GATE de WORKTREE:** la base se pregunta, se dice cuántos hay abiertos (techo 8), con el
  árbol sucio se frena.
- **Quien verifica no es quien programó** (`DEC-005`: el otro motor si hay dos; otro agente del
  mismo motor con contexto limpio si hay uno). Sin verificador, no se despacha.
- **Ningún worktree sobre este repositorio**, y el núcleo no se escribe desde un worker.
- **Nunca se inventa:** ni regla, ni `#ID`, ni estado, ni dependencia, ni repo destino.
- **Sin PHI** en código, fixtures, commits, comentarios ni misiones.
- Este repositorio no recibe código de la aplicación ([[decisiones#DEC-001]]).

## Decisiones abiertas ⚠ — hasta cerrarlas, se resuelven como dice «Mientras tanto»

| Tema | Por qué está abierta | Mientras tanto |
|---|---|---|
| Commits locales en la rama del worktree | La evidencia del rojo exige un commit por test, local y de trabajo (antes del push se reorganiza por importancia, con el respaldo `evidencia/<ID>` en `origin`); la regla del usuario es no commitear sin pedido | Se pregunta en el paso 5: un "sí" **por Tarea** que autoriza commits locales en su rama, nunca push. Sin ese "sí" la Tarea no se despacha: sin commits, `verificar-tdd` da `SIN DATOS` |
| Modo de permisos de Gemini | `--approval-mode` acepta `default`, `auto_edit`, `yolo` y `plan`; el worker tiene que editar y correr tests | Se pregunta en el paso 5, para programar y para verificar |
| Modo de permisos de Claude | `--permission-mode` de `claude -p` | Se pregunta en el paso 5 |
| Quién abre el Merge Request | El MCP de GitLab es de sólo lectura | Lo abre el humano |
| Dos Tareas sobre el mismo archivo | Regla candidata del GATE de WORKTREE | En serie |
| Dónde viven los repos de código | El Cerebro dice adentro de `back/` y `front/`; en la práctica pueden estar al lado | Se buscan en los dos lugares y, ante la duda, se pregunta (paso 3) |
| Dónde van los worktrees | No está escrito en el Cerebro | Se propone `<carpeta padre>/worktrees/` y se confirma en el paso 5 |
| Repos de infraestructura fuera de alcance | Es regla del usuario, todavía no escrita en el Cerebro | Se excluyen salvo pedido explícito |

## Contexto adicional

- Diseño del orquestador de código: `cerebro-digital/configuracion-ia/orquestador-desarrollo.md`
- La versión con Orca: [[desarrollar-asignadas]]
- Entrada a todo lo que es código (el método propio): [[desarrollo]]
- Auditoría de la Tarea (opcional, a pedido): [[auditar-tarea]]
- Pendientes a confirmar y revisión antes de cerrar: [[comentar-tarea]]
- Ramas, commits y MR: `cerebro-digital/modulo-ejemplo/metodologia/convenciones-git.md`
- Setup de los MCP: `integracion-azure-mcp/00-index`, `integracion-gitlab-mcp/00-index`
