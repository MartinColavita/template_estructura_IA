# CÓMO USAR ESTE TEMPLATE — Estructura IA (Cerebro Digital + agentes + skills)

Este es el **esqueleto completo** de un repositorio de conocimiento y agentes para construir y
mantener una aplicación con IA, obtenido por ingeniería inversa de un proyecto real. Trae **toda
la lógica de infraestructura** —reglas, agentes, skills, hooks, scripts, el Doctor, el toolkit de
tickets, los moldes del Cerebro— y **nada del negocio ni del lenguaje de programación**: eso lo
pone cada proyecto al instanciar.

## Qué trae y qué no

| Trae | No trae (a propósito) |
|---|---|
| `AGENTS.md` con todas las reglas y barreras (GATEs de tablero, dedup, confirmación, nivel, borrado, tarjeta congelada, worktrees) y sus loaders `CLAUDE.md` / `GEMINI.md` / `opencode.json` | Fichas funcionales, reglas de negocio, decisiones de negocio, reuniones, mockups ni presentaciones del proyecto de origen |
| El Cerebro Digital con su estructura (index, contexto, fuentes, roadmap, log, un módulo de ejemplo con sus cuatro pilares —funcional, metodología, arquitectura y la memoria de la aplicación (`aplicacion/`: mapa, aprendizajes `AP-nnn`, deuda `DT-nnn`)—, pendientes, extracciones de reunión, sistema de diseño) como **moldes a completar** | Lenguajes, frameworks, runners de tests ni herramientas de build: el stack es `DEC-003`, a definir |
| 4 agentes + 33 skills (9 del Cerebro, 13 del pipeline del tablero, 10 de desarrollo, QA y evolución, 1 externa vendorizada: Archify) con sus espejos | El envoltorio de skills corporativas de un tercero, su detector de deriva y sus fichas de corrección (se explica cómo armarlo si hace falta: `DEPENDENCIAS-EXTERNAS.md` y G5 de `AGENTS.md`) |
| Las skills scoped de desarrollo de `back/` y `front/` (guiar-tdd, verificar-tdd, auditar-codigo, armar-swagger, consultar-cerebro, diagnosticar-repo) | Las skills de front atadas a un framework concreto (crear componentes, features del núcleo, testear componentes) |
| El toolkit de tickets `tablero/` (método, plantillas, checklists, ejemplos neutros, histórico vacío, guías HTML) | El histórico de tickets ni los IDs del tablero de origen |
| `bin/`: sincronización de espejos, integración semanal, enviar notas, auditorías mecánicas de tickets, modo lote, pruebas de reglas, verificación de sellos, política de sólo lectura del verificador, ruleset de OpenAPI, **instanciación del template**, **instalador** (`instalar.py`) y **verificador de la especificación de skills** (`verificar-skills.py`) | Scripts de acceso a servidores de la organización de origen |
| El Doctor (`doctor/`) con sus 23 sondas | Los informes generados (`doctor/salida/`) |
| El hook pre-commit (`.githooks/`), `.gitignore`, `.gitattributes` | Configuración local por máquina (`.mcp.json`, `.gemini/.env`, `.claude/settings.local.json`) |
| `qa/` con las pruebas de punta a punta del proyecto (`disenar-pruebas`, `automatizar-e2e`, `bin/armar-e2e.py`, `bin/cobertura-e2e.py`) y el método de esa capa (`pruebas-de-aceptacion.md`); `.gitlab-ci.yml` opcional que verifica el propio repositorio del Cerebro | Las pruebas de aceptación en sí: las escribe QA a partir del Gherkin de las Historias |

## Modo solo o en equipo: se pregunta en cada proyecto

El mismo esqueleto sirve para un desarrollo personal y para un equipo, y los flujos cambian. Por eso
`instanciar.py` exige `--modo solo|equipo` y lo deja escrito en `DEC-006` del módulo:

| | Modo solo | Modo equipo |
|---|---|---|
| Tablero | Local: `cerebro-digital/<modulo>/backlog/` con `bin/tablero-local.py` (sin MCP, sin tokens) | Azure DevOps, Jira u otro del mercado por su MCP (`--tablero azure|jira|otro`; la tabla de herramientas por función traduce) |
| Conocimiento | Directo a `develop`, por `cerebro-curator` con tu «sí» | Igual; si hay un segundo dev, cada uno en su rama y lo integra un Merge Request que revisa el otro |
| Verificación | Otro agente del mismo motor, contexto limpio (DEC-005) | El otro motor |
| Confirmaciones | Las que deja DEC-005 modo solo si la firmaste al arrancar (auto-Aprobar con cero bloqueantes); sin firma, todas | Todas las de los GATEs |

Nada se borra al elegir: las skills del otro modo quedan disponibles por si el proyecto cambia.

## Instanciar, paso a paso

1. **Copiá la carpeta** del template a donde va a vivir el repositorio nuevo y renombrala.
2. **Corré el instanciador** (Python 3, biblioteca estándar) parado en esa carpeta:

   ```bash
   python -I bin/instanciar.py --modo solo --tablero local --proyecto "Gestión de Reservas" --producto "ReservaWeb" --organizacion "Acme" --modulo reservas
   python -I bin/instanciar.py --modo equipo --tablero azure --proyecto "Gestión de Reservas" --producto "ReservaWeb" --organizacion "Acme" --modulo reservas --azure-org acme-devops --azure-proyecto "Reservas" --azure-team "Reservas Team"
   ```

   Reemplaza los placeholders en todos los archivos de texto, renombra `cerebro-digital/modulo-ejemplo/` al slug del módulo (y todas las referencias), regenera los espejos de skills y agentes, y te deja la lista de lo que sigue. Con `--dry-run` muestra qué haría sin tocar nada.

   | Placeholder | Qué es | Ejemplo |
   |---|---|---|
   | `{{PROYECTO}}` | Nombre del proyecto / módulo que este Cerebro documenta | Gestión de Reservas |
   | `{{PRODUCTO}}` | Nombre del sistema / producto del que forma parte | ReservaWeb |
   | `{{ORGANIZACION}}` | La organización dueña | Acme |
   | `modulo-ejemplo` | Slug del módulo principal del Cerebro (carpeta y referencias) | `reservas` |
   | `{{AZURE_ORG}}` · `{{AZURE_PROYECTO}}` · `{{AZURE_TEAM}}` | El **único tablero autorizado** de Azure DevOps | `acme-devops` · `Reservas` · `Reservas Team` |

3. **Iniciá el repositorio y corré el instalador**: `git init` (o cloná el remoto vacío) y `python -I bin/instalar.py` (activa el hook, materializa los agentes, verifica espejos y la especificación de cada skill, y te dice qué falta); después, el primer commit. Quien clone más adelante corre ese mismo comando y nada más.
4. **Completá el Cerebro**, en este orden (todo lo que no sepas queda `(pendiente)` o `⚠`, nunca inventado):
   - `cerebro-digital/contexto.md` y `fuentes.md` (los documentos de origen van a `documentos/`).
   - `tablero/conocimiento/contexto-proyecto.md`: slices (→ Épicas), lista de etiquetas temáticas, proceso del tablero, tipos de work item, formato de iteración.
   - `cerebro-digital/<modulo>/arquitectura/decisiones.md`: confirmar `DEC-002` y tomar `DEC-003` (el stack); después `esqueleto-proyectos.md` (incluida la convención **C8** del verificador).
   - La skill `desarrollo`: completar `references/metodo/tdd-stack-back.md` y `tdd-stack-front.md`, y la tabla de precedencia si la organización tiene un estándar corporativo.
   - `back/README.md` y `front/README.md`: la tabla «Stack».
   - `cerebro-digital/diseno/diseno-sistema.md` y los tokens de la skill `cerebro-mockup-design`; el logo en `entregables/disenos/logo.png`.
   - `bin/probar-reglas.py`: la constante del `#ID` de una Historia real del Cerebro para el caso del duplicado, y los slices/producto.
   - `bin/gemini-verificador-solo-lectura.toml`: los comandos de test del stack que el verificador puede correr.
   - `doctor/codigo.py`: si el stack no usa los marcadores de build conocidos, ampliar `MARCAS`, `EXTENSIONES` y `CALIDAD_*`.
5. **Configurá los MCP** por máquina (no se versionan): Azure DevOps (`cerebro-digital/configuracion-ia/integracion-azure-mcp/`), GitLab (`integracion-gitlab-mcp/`), Stitch para diseñar pantallas (`integracion-stitch-mcp/`), Engram (opcional). Variables de entorno por referencia, nunca el valor en un archivo.
6. **Verificá**: `bash doctor/bin/doctor.sh` (o `.ps1`) tiene que correr entero; `python -B bin/probar-auditar-tarea.py`, `probar-auditar-historia.py`, `probar-analizar-tareas.py`, `probar-lote.py`, `probar-verificar-sello.py`, `probar-derivar-arbol.py`, `probar-scripts-git.py`, `probar-verificar-skills.py`, `probar-instalar.py`, `probar-radiografiar.py`, `probar-armar-mision.py`, `probar-generar-informe.py`, `probar-tablero-local.py`, `probar-relevar-config-ia.py`, `probar-medir-uso-skills.py`, `probar-adoptar-proyecto.py`, `probar-arrancar-proyecto.py`, `probar-derivar-a-tablero-local.py` y `probar-generar-documentacion.py` tienen que dar OK; `python -B bin/generar-informe.py` deja `INFORME-ESQUELETO.html` al día; el hook tiene que dejar pasar un commit con los espejos sincronizados.
7. **Escribí la primera ficha funcional** copiando `cerebro-digital/<modulo>/funcional/plantilla-ficha-flujo.md`, y bajala al tablero con `sincronizar-backlog` cuando una persona valide su bloque `## Derivación a backlog`.

## Cómo se produce código de forma autónoma con este esqueleto

El template está pensado para que la IA **construya la aplicación** y, después, la **mantenga**
sin que el Cerebro deje de ser la fuente de verdad. La cadena, de punta a punta:

1. **Conocimiento** — el funcional aporta (documento, reunión, chat); `cerebro-analyst` arma el
   borrador en `borrador/`, una persona valida, `cerebro-curator` lo persiste en el Cerebro con su
   bloque `## Derivación a backlog` enumerado.
2. **Tickets** — `sincronizar-backlog` baja la ficha al tablero **1:1** (Épica→Feature→Historia);
   `planificar-lote` deriva las Tareas (contrato, Especificación cerrada con los Escenarios mapeados
   a tests, lista de «Tests a escribir PRIMERO», modos de falla) con un "sí" humano por lote.
3. **Código** — `orquestador-desarrollo` (`desarrollar-asignadas` dentro de Orca o
   `desarrollar-asignadas` (modo sin Orca) fuera) abre un worktree por Tarea y despacha un worker por Tarea con la
   misión autocontenida y las skills explícitas; el worker programa con `guiar-tdd` (test primero,
   evidencia del rojo en commits) siguiendo el método de `desarrollo`.
4. **Verificación independiente** — **otro agente** (DEC-005: el otro motor si hay dos; el mismo motor con contexto limpio si hay uno), en sólo lectura, corre `verificar-tdd`
   (¿el ciclo ocurrió?), la revisión de código, `auditar-codigo` (¿la entrega cumple?) y las
   convenciones C1…C8; veredicto OK / HALLAZGO / SIN DATOS por control.
5. **Entrega** — con el "Aprobar" humano: respaldo `evidencia/<ID>`, commits por importancia, push,
   link del Merge Request y comentario de cierre en la Tarea (`comentar-tarea`). El Estado de la
   tarjeta lo cambia una persona.
6. **Salud** — el Doctor mide el repositorio del Cerebro y los repos clonados por hito;
   `atender-hallazgos` recorre lo que encuentra, uno por uno.

Lo que el equipo tiene que decidir para que esa cadena arranque es `DEC-003` (el stack) y
completar `tdd-stack-back.md` / `tdd-stack-front.md`: hasta entonces, todo lo que dependa del
stack queda `SIN DATOS`, no inventado.

## Skills de código: una pregunta por skill, sin solapes

Las skills que tocan código se revisaron para que **ninguna repita a otra ni se pase de su
pregunta**. Cada una contesta una sola cosa:

| Skill | Dónde vive | La pregunta que contesta | Lo que NO hace |
|---|---|---|---|
| `desarrollo` | Cerebro | ¿**Cómo** se escribe código acá? (el método: contrato primero, TDD con evidencia, revisión, entrega) | No ejecuta ni audita: es la guía que reciben los workers |
| `guiar-tdd` | `back/`, `front/` | ¿Se está escribiendo **con el test primero**? (árbitro del ciclo mientras se programa) | No escribe la solución; no aprueba su propia evidencia |
| `verificar-tdd` | `back/`, `front/` | ¿El ciclo **ocurrió**? (rojo en la aserción antes del código, verde hoy, cierre BDD↔TDD contra la Historia) | No revisa calidad ni corrige tests; la corre otro agente |
| `auditar-codigo` | `back/`, `front/` | ¿La entrega **cumple lo que este pipeline exige**? (contrato de la Tarea, límites de módulo, lista de tests cubierta, sin PHI ni secretos) | No revisa calidad genérica (eso es `/code-review`), no audita TDD, no mira el repo en reposo |
| `armar-swagger` | sólo `back/` | ¿El **contrato** está consolidado y válido? | No inventa endpoints |
| `consultar-cerebro` | `back/`, `front/` | ¿Qué dice el Cerebro de **esta** regla? (una ficha, a pedido) | No escribe el Cerebro; no se usa por defecto |
| `diagnosticar-repo` | `back/`, `front/` | ¿El repo está **sano**? (corre el Doctor) | No revisa un cambio puntual |
| `desarrollar-asignadas` (modo Orca o sin Orca) | Cerebro | ¿**Quién** programa qué, en qué worktree, y quién verifica? (orquestación; un solo texto, dos lanzadores) | No programan ni autorizan la entrega |
| `atender-hallazgos` | Cerebro | ¿Qué hago con **cada** hallazgo del Doctor? | No arregla sola ni en lote |
| `absorber-aplicacion` | Cerebro | ¿Qué hay en una aplicación que **ya existe** y qué sabe? | No toca la aplicación; termina con el Cerebro poblado |
| `planificar-modernizacion` | Cerebro | ¿**Qué hacemos** con esa aplicación: refactor, estrangulador, subir de versión, nada? | No decide: compara con lo medido y pregunta (`DEC-004`) |
| `caracterizar-comportamiento` | Cerebro | ¿**Cómo responde hoy**, para que un cambio se note? | No valida: congela; el golden lo firma el script |
| `modernizar-slice` | Cerebro | ¿Cómo avanza **un slice** hasta el corte y el apagado? | No corta ni apaga: muestra la barrera en OK y lo hace una persona |
| `disenar-pruebas` | Cerebro | ¿**Qué** probamos de punta a punta de esta Historia, con qué datos, y qué queda a mano? | No inventa pasos: el Gherkin es la fuente |
| `automatizar-e2e` | Cerebro | ¿**Cómo** se ejecuta cada Escenario contra la app, con el motor del tipo de aplicación? | Un esqueleto no es una prueba; nunca contra producción |
| `mejorar-ecosistema` | Cerebro | ¿Qué está **mal en el propio ecosistema** y qué cambio concreto lo arregla? | No aplica nada sin el \"sí\" por propuesta |

**Lo que se dejó afuera por redundante o por pasarse de su pregunta:** las tres skills de front del
proyecto de origen (scaffolding de un framework concreto: lo genérico de ellas ya está en
`guiar-tdd`, `tdd-stack-front.md` y `arquitectura/frontend/reglas-generales.md`), el envoltorio de
un estándar corporativo con sus fichas de corrección y su detector de deriva (el mecanismo queda
descripto en G3/G5 por si un proyecto lo necesita), y los archivos de método atados a un stack.

**Solape resuelto (M-002):** `desarrollar-asignadas` absorbió a la skill de IntelliJ como modo sin Orca (`references/sin-orca.md`); antes compartían la
misión del worker y la del verificador; se mantuvieron como dos skills porque son **excluyentes
por entorno** (la una se niega a arrancar donde corre la otra) y el texto compartido ya remite a
`orquestador-desarrollo.md`. Si en el proyecto nuevo sólo se usa un entorno, se borra la otra.

**Lo que se volvió determinístico con scripts** (la skill corre el script primero; lo que el script
marca no lo discute el modelo; un script que no corrió es `SIN DATOS`): `derivar-arbol.py` (el árbol
1:1 de una ficha), `gate-worktree.py` (los datos del GATE de WORKTREE), `verificar-tdd.py` (rojo antes
del verde, por ítem, desde `git log`), `auditar-diff.py` (secretos y posibles datos personales en el
diff), `atajos.py` (las marcas `atajo:` del código y si dicen cuándo se mejoran), `datos-cierre.py` (los datos duros del comentario de cierre), `inventariar-codigo.py` (el
inventario de una aplicación existente) y `radiografiar-codigo.py` (los hechos del código con `archivo:línea`, para que la lectura no sea a ciegas). Lo que sigue siendo del modelo es lo que pide criterio: la
aserción literal de un test, el cierre BDD↔TDD, el contrato contra el código, los límites de módulo
y la lectura de un aviso.

## Arrancar: decile a Claude, no leas pasos

> **Prompt maestro listo para pegar:** arriba de todo de `INFORME-ESQUELETO.html` (con botón de copiar) y, como fuente
> única, en `cerebro-digital/configuracion-ia/skills/arrancar-proyecto/references/prompt-maestro.md`. Trae el contexto
> que la skill ya no pregunta, los pasos en orden con un «sí» en cada uno, y las frases para lo que sigue.

Copiá (o cloná) el template a la carpeta donde va a vivir el núcleo del proyecto, abrí Claude Code ahí y decí
**«arrancá un proyecto»** o **«agarrá el proyecto C:\...\mi-proyecto»**. La skill `arrancar-proyecto` te pregunta
en **un solo mensaje** lo básico, con una propuesta al lado de cada cosa: si es nuevo o ya existe (y dónde está,
si es back o front, si se enlaza o se muda), los nombres, el módulo, si trabajás solo o en equipo, el tablero,
quién sos, y si agrega a tu `CLAUDE.md` la línea que importa las reglas. Te muestra el plan con el comando exacto,
y con tu «sí» corre todo por script, en orden fijo: instanciar, `git init`, instalar, enchufar tu carpeta
(enlace en `back/` o `front/`, relevamiento, inventario, radiografía, la línea en tu `CLAUDE.md`) e informe.
Al terminar te dice qué quedó y te pregunta si absorbe la aplicación en modo documentar. Nada se inventa: lo
que no contestás se vuelve a preguntar.

Por debajo es `python -I bin/arrancar-proyecto.py …`; la sección siguiente es lo mismo a mano, por si querés
verlo o correrlo vos.

## Si la aplicación ya existe: ingeniería inversa, refactor o migración

El template no sólo crea de cero. Son **cuatro skills encadenadas**, cada una con su dueño: `absorber-aplicacion`
(ingeniería inversa: inventario, radiografía, Cerebro; sirve también sólo para documentar), `planificar-modernizacion`
(estrategia, curaduría de reglas, `DEC-004`, slices), `caracterizar-comportamiento` (la red: corpus y golden contra la
vieja) y `modernizar-slice` (contrato, construcción, paridad, corte con barrera, apagado). Los scripts que cuentan:
`inventariar-codigo.py`, `radiografiar-codigo.py`, `esquema-base.py`, `armar-corpus.py`, `paridad.py`, `mapa-modernizacion.py`.
El orden:

0. **Si el proyecto ya trabaja con IA** (`CLAUDE.md`, skills, `.mcp.json`): `bin/relevar-config-ia.py` lista qué trae y adónde
   va cada cosa; el método es `adoptar-proyecto-existente.md`. El repo se enchufa adentro de `back/` o `front/`, no se muda.
1. **Inventario por script** (`bin/inventariar-codigo.py`): lenguajes, build, pipeline, contratos,
   migraciones, tests, deuda, posibles secretos, y las filas medibles de `DEC-004`. Sin criterio, siempre igual.
1-bis. **Radiografía por script** (`bin/radiografiar-codigo.py`): endpoints, entidades y tablas, enums y
   campos de estado, pantallas, reglas candidatas, integraciones, permisos y dependencias entre módulos,
   **cada hecho con `archivo:línea`**, y con `--mermaid` los diagramas de módulos y de tablas en texto
   versionable. La lectura empieza por lo que señala, y la matriz de cobertura dice
   qué módulo quedó sin leer (HUECO, no «sin reglas»). Cada afirmación lleva su marca: CONFIRMADO,
   INFERIDO o HUECO.
2. **Lectura ítem por ítem** de afuera hacia adentro (README y contrato → carpetas → un flujo → tests →
   historial) y **Consulta Interactiva de Decisión** por cada entidad, estado, rol, regla candidata
   `⚠`, integración, decisión implícita, deuda y duda. Nada entra al Cerebro en bloque. La aplicación
   **no se toca**: sólo se lee.
3. **Diagnóstico y decisión con el humano** (`DEC-004`): una tabla con lo medido (stack, red de tests,
   límites de módulo, contrato, deuda, si tiene que seguir en producción) y una propuesta con su
   porqué. **Refactor** = se modifica en su lugar, módulo por módulo, con tests de caracterización
   primero. **Migración** = se construye de nuevo en otro repositorio, por slices, con la vieja como
   oráculo y paridad funcional como criterio de aceptación, hasta apagarla con un "sí".
4. **El plan** son fichas con su bloque de derivación: desde ahí la aplicación se construye o se
   transforma con las mismas skills que una nueva. El método de cada Tarea está en
   `desarrollo/references/metodo/refactor-y-migracion.md`.

## Las pruebas: tres capas, ninguna redundante

| Capa | Dónde | Pregunta | Cuándo |
|---|---|---|---|
| Unitaria y de contrato | `back/`, `front/`, con `guiar-tdd` (TDD por defecto) | ¿Cada pieza cumple su contrato y sus `[RN-…]`? | En cada commit y Merge Request |
| Integración | `back/`, `front/`, sólo si la Tarea lo declara | ¿La dependencia externa real responde como el contrato dice? | En el Merge Request |
| Aceptación (punta a punta) | `qa/` o el repo de código (`DEC-003`) | ¿La aplicación **desplegada** cumple los Escenarios de la Historia, de afuera? | Al desplegar a prueba, por día, antes de cortar a producción |

Un repositorio de QA aparte **no es redundante**: el back y el front se prueban cada uno
simulando al otro, y la costura entre los dos sólo la ve la capa de aceptación. Lo que sí tiene que
cumplir es la **trazabilidad**: cada prueba nombra la Historia (`#ID`) y el Escenario que automatiza,
y el Gherkin es la fuente. Si ya hay un repositorio de pruebas de aceptación, se absorbe con `absorber-aplicacion` y se
le agrega la trazabilidad que le falte. Detalle: `desarrollo/references/metodo/pruebas-de-aceptacion.md`.

**TDD no es para todo, y eso está escrito.** Cada Tarea declara su «Modo de pruebas»: TDD por
defecto (reglas, casos de uso, endpoints, lógica de front, bugs); `test-después` con motivo
(esqueleto, configuración, migraciones, UI puramente visual) con la red mínima que cada caso exige;
`sin tests` sólo para un spike que no va a producción; `caracterización primero` para código
existente sin red. Sin motivo escrito, es TDD. Detalle: `tdd-ciclo-y-evidencia.md` §«Cuándo TDD».

## Los tres bucles del esqueleto

1. **Construir**: conocimiento → tickets → código con TDD → verificación independiente → entrega.
2. **Autocorregirse** (consultado): lo que el ecosistema muestra que tiene mal va a `mejoras.md` y se
   pregunta de a una (`mejorar-ecosistema`); nada se aplica solo.
3. **Alimentar el Cerebro mientras se trabaja**: lo que cada Tarea confirma o descubre pasa por la
   Consulta Interactiva de Decisión y lo persiste `cerebro-curator` (paso 7-bis del orquestador de
   desarrollo), cada cosa a su lugar: lo del **negocio** (una respuesta a un pendiente, una regla
   precisada, un estado que no estaba escrito) a `funcional/` o `decisiones.md`; lo de **la
   aplicación** (qué módulo quedó construido, un bug y su causa, una trampa del stack, una deuda
   aceptada) a `<modulo>/aplicacion/` —`mapa.md`, `aprendizajes.md`, `deuda.md`—, que es la división
   del Cerebro que **aprende con la aplicación** y que un worker abre antes de tocar un módulo que
   ya existe; lo del **ecosistema** a `mejoras.md`. Nada de lo aprendido se queda en el chat.

## Diseño con Stitch, y los entregables al cerrar

**Lo visual se diseña en Google Stitch.** `disenar-con-stitch` arma el brief desde la ficha (propósito, pasos, cada
control con su regla, estados, glosario, tokens), genera la pantalla por MCP (o te deja el prompt para pegar), vos la
pulís en Stitch, y la exportación (HTML y captura) entra a `borrador/disenos/` y, con tu «sí», a `entregables/disenos/`
como maqueta vigente citada por la ficha. Los tokens que salieron del diseño van al design system; la bajada al front
la hace `cerebro-architect-ui` (cada control mapeado a su regla) y las Tareas de front. Setup del MCP:
`cerebro-digital/configuracion-ia/integracion-stitch-mcp/00-index.md`. Sin PHI en prompts ni pantallas, nunca.

**Al cerrar un slice o la aplicación**, `documentar-aplicacion` produce dos entregables profesionales desde el Cerebro:
la **guía de uso** (empezar en pocos pasos, cada flujo con su pantalla y su paso a paso dibujado, glosario, preguntas
frecuentes) y la **documentación técnica y funcional** (resumen, módulos y arquitectura con el grafo del código,
modelo de datos, API, flujos, catálogo de reglas, integraciones, decisiones, pruebas, pendientes y deuda,
aprendizajes, bitácora, glosario, diagramas de Archify). Primero el script `bin/generar-documentacion.py` (índice,
diagramas SVG, pantallas embebidas, lo que falta marcado en amarillo); después se pule la prosa sólo con lo que está
en el Cerebro, y se promueve a `entregables/documentacion/` con un «sí».

## Autocorrección consultada

La IA que trabaja con este esqueleto también ve dónde el propio esqueleto falla: una convención que
todos rompen igual, un control que siempre da `SIN DATOS`, un pendiente que vuelve, un script que
cuenta mal. `mejorar-ecosistema` lo convierte en **una propuesta por vez** —qué, por qué, impacto y el
cambio exacto— registrada en `cerebro-digital/configuracion-ia/mejoras.md`, y **la pregunta**. Las
opciones son Aplicar / Rechazar (con motivo) / Editar y aplicar / Posponer. **Nunca aplica un cambio de
arquitectura, skills o scripts por su cuenta**; lo aprobado se aplica por los canales normales
(curator, `sync-skills`, la prueba del script en OK) y queda asentado. Una propuesta rechazada no se
repite: queda escrita con su motivo. Es la regla 8 de `AGENTS.md`.

**Cómo mejora solo, y con qué herramientas.** Claude Code trae hoy varias piezas que informan primero y piden
confirmación antes de tocar, y el esqueleto las usa como señales: `/doctor` (alias `/checkup`: skills, MCP y plugins
sin uso frente a su costo, `CLAUDE.md` duplicado o derivable del código, hooks lentos), `/doctor prompt-audit`
(instrucciones viejas o contradictorias en `AGENTS.md`, reglas, skills y agentes, con ediciones propuestas), `/context`
y `/usage` (qué pesa), la **auto memory** (lo que Claude anota por correcciones repetidas: una regla que falta) y el
`skill-creator` con sus evals para reescribir una skill midiendo antes y después. A eso el esqueleto le suma lo
determinístico: `bin/medir-uso-skills.py` lee las transcripciones locales y dice qué skills se usaron, cuáles no y
cuánto pesan; `bin/verificar-skills.py`, el Doctor y las pruebas de `bin/`. **El ritual mensual** está en
`mejorar-ecosistema` §«El ritual mensual», y el criterio de poda en §«Poda de skills»: cero usos en 60 días con la
pregunta cubierta por otra, dos skills con la misma pregunta, una que se dispara cuando no debe, o una que pesa y
se usa poco. Así se evita lo que pasó en el proyecto de origen: skills de más que se pisaban y sobregiraban el
código. Nada se saca solo.

## Mapa de equivalencias con el proyecto de origen

Para quien conoce el proyecto del que salió este template:

| Origen | Template | Por qué |
|---|---|---|
| `<prefijo-de-origen>-<x>` (9 skills) y agentes `<prefijo-de-origen>-analyst/curator/architect/auditor` | `cerebro-<x>` | Prefijo neutro; mismo sufijo para que la correspondencia sea 1:1 |
| `orquestador-<origen>` | `orquestador-conocimiento` | Es el par de `orquestador-desarrollo`: aquel coordina el conocimiento, este el código |
| `<org>-desarrollo` (envoltorio de skills corporativas) + `references/<org>/` + `scripts/verificar-deriva.*` + `version-fijada.md` | `desarrollo` (el método propio, sin envoltorio) | El estándar corporativo era del proyecto de origen; el mecanismo para envolver uno queda explicado en G3/G5 y `DEPENDENCIAS-EXTERNAS.md` |
| `references/metodo/tdd-java-quarkus.md`, `tdd-react-vite.md`, `simular-api-msw.md`, `testing-automatico.md` | `tdd-stack-back.md`, `tdd-stack-front.md` (plantillas a completar), `simular-api-desde-el-contrato.md` | Lo específico del stack se decide por proyecto |
| `seguridad-y-datos-de-salud.md` | `seguridad-y-datos-sensibles.md` | Los datos sensibles dependen del dominio |
| `cerebro-digital/<modulo-de-origen>/` | `cerebro-digital/modulo-ejemplo/` (se renombra al instanciar) | El módulo es del negocio |
| `RN-<PREFIJO>-nnn` | `RN-MOD-nnn` (el prefijo lo elige cada módulo) | Idem |
| Marcadores `<socio>`, `<credencial>`, `<diagnostico>` | `<persona>`, `<identificador>`, `<dato-sensible>` | El dominio de origen era de salud |
| Skills de front `agregar-feature-core`, `crear-componente`, `testear-componente` | No vienen | Atadas a un framework concreto |
| `bin/verificar-acceso-<org>.*` | No viene | Accedía al servidor de la organización de origen |
| Las decisiones 7 (código fuera del repo) y 17 (módulos por dominio) del origen | `DEC-001`, `DEC-002` | Renumeradas; el resto de las decisiones eran de negocio |
| Convenciones `C1…C8` del verificador | `C1…C7` genéricas + `C8` a completar con el stack | C8 era la política de librerías del stack de origen |

## Decisiones que el proyecto nuevo tiene que tomar (y dónde quedan)

| Decisión | Dónde se escribe |
|---|---|
| Stack del back, del front, base de datos, migraciones, SAST, cobertura, observabilidad, despliegue | `arquitectura/decisiones.md` (`DEC-003`) y `esqueleto-proyectos.md` |
| Confirmar o cambiar la arquitectura por módulos de dominio | `DEC-002` |
| Slices (→ Épicas), lista de etiquetas temáticas, tablero, proceso | `tablero/conocimiento/contexto-proyecto.md` |
| Marcadores adicionales de datos sensibles del dominio | `contexto-proyecto.md` y regla de oro 2 de `AGENTS.md` |
| Si se sigue un estándar corporativo de desarrollo, y quién gana en cada tema | Tabla de precedencia de la skill `desarrollo` + `DEPENDENCIAS-EXTERNAS.md` |
| Dos Tareas que tocan el mismo archivo se serializan (regla candidata) | GATE de WORKTREE de `AGENTS.md` |
| Dónde viven los worktrees y los repos de infraestructura | `desarrollar-asignadas` (modo sin Orca) §Decisiones abiertas |
| Umbrales del método marcados `⚠ Propuesta del método` (tiempos de suite, alertas, SLO, rendimiento) | Cada archivo de `desarrollo/references/metodo/` |

## Cómo mantener el template

- El template se mantiene **genérico**: si en un proyecto aparece una mejora del método (una regla nueva, un chequeo, un guardarraíl), se vuelve a traer acá sin el negocio.
- Antes de publicar una versión nueva del template: `grep` de términos de negocio y de stack (ver el final de este archivo), el Doctor en verde en lo que aplica, y los `probar-*.py` en OK.
- Chequeo rápido de que no quedó negocio ni stack:

  ```bash
  grep -r -n -i -E '\b(quarkus|java|maven|react|vite|vitest|msw|typescript|pnpm)\b' --include='*.md' --include='*.html' --include='*.toml' --include='*.sh' --include='*.ps1' . | grep -v -E 'COMO-USAR|doctor/'
  ```
