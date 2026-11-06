# {{PROYECTO}} — ecosistema de agentes + Cerebro Digital

> **Esto es una instancia del TEMPLATE ESTRUCTURA IA.** Si este archivo todavía muestra marcadores
> entre llaves dobles, el template no se instanció: leé [`COMO-USAR-ESTE-TEMPLATE.md`](COMO-USAR-ESTE-TEMPLATE.md)
> y corré `python -I bin/instanciar.py`.

Repositorio de **conocimiento y agentes** del proyecto {{PROYECTO}} ({{PRODUCTO}}, {{ORGANIZACION}}).
Acá viven el **Cerebro Digital** (la fuente única de verdad del negocio, en formato OKF), las
**reglas** que rigen a los asistentes de IA, las **skills** que ejecutan el método y los
**scripts** que verifican que todo cierre. El código de la aplicación **no** vive acá
(`DEC-001`): se clona en `back/` y `front/`, en repositorios propios.

## ⚡ Acciones rápidas

0. **Arrancar un proyecto**: abrí Claude Code en una copia del template y decí «arrancá un proyecto» o «agarrá el
   proyecto <carpeta>». La skill `arrancar-proyecto` pregunta lo básico en un mensaje, muestra el plan y con tu «sí»
   corre todo por script. Nada de pasos a mano.
1. **Explorar el dominio**: leer `cerebro-digital/index.md` y después el `index.md` del pilar que
   corresponda (`funcional/`, `metodologia/`, `arquitectura/`) del módulo.
2. **Procesar un documento funcional o una reunión**: pedírselo al asistente; aplica el flujo de
   `cerebro-orquestador` (plan → borrador en `borrador/` → validación humana → Cerebro).
3. **Bajar una ficha al tablero**: `sincronizar-backlog` (árbol 1:1) o `planificar-lote` (Tareas
   de varias Historias), siempre con confirmación.
4. **Desarrollar Tareas en paralelo**: `desarrollar-asignadas`, dentro de Orca o sin Orca (IntelliJ o
   terminal; `references/sin-orca.md`). El método de código es la skill `desarrollo`.
5. **Ver cómo está el proyecto**: `bash doctor/bin/doctor.sh` (o `.\doctor\bin\doctor.ps1`).
 6. **Sumar un proyecto que ya existe**: lo mismo, «agarrá el proyecto <carpeta>» (por debajo corre `bin/adoptar-proyecto.py`).
 7. **Ver qué skills se usan y cuáles sobran** (mensual): `python -B bin/medir-uso-skills.py`, más `/doctor` y
    `/doctor prompt-audit` en Claude Code; lo que salga se propone en `mejoras.md`, nunca se saca solo.
 8. **Diseñar una pantalla**: «diseñá la pantalla de X» (Google Stitch por MCP, `disenar-con-stitch`).
 9. **Al cerrar un slice o la app**: «documentá la app» (guía de uso + documentación técnica y funcional, `documentar-aplicacion`).

## 📂 Estructura del repositorio

| Directorio | Propósito | Se versiona |
|------------|-----------|-------------|
| `documentos/` | Lo que **entra**: requerimientos, notas, reuniones, documentos de origen, vengan de vos, de un cliente o de un funcional. Nunca se genera acá, se recibe; cada uno queda registrado en `cerebro-digital/fuentes.md` | Sí (salvo `*.docx`) |
| `cerebro-digital/` | 🧠 **Cerebro Digital (bundle OKF)**. Fuente única de verdad del negocio, la metodología y la arquitectura, más la configuración de IA (`configuracion-ia/`: agentes, skills, orquestador de desarrollo, integraciones) | Sí |
| `entregables/` | Artefactos ya promovidos desde `borrador/` (diseños, especificaciones técnicas; presentaciones sólo en local) | Sí |
| `borrador/` | 🧪 Borrador de trabajo (mockups, docs, presentaciones en curso, lotes de tickets). Nunca se versiona | No |
| `tablero/` | 🎫 Toolkit para derivar tickets desde el Cerebro, para cualquier tablero (local por archivos, Azure DevOps, Jira u otro; `DEC-006`): método, plantillas, checklists, ejemplos e histórico por referencia | Sí |
| `bin/` | Scripts: sincronizar espejos, integración semanal, enviar notas, auditorías mecánicas de tickets, modo lote, pruebas de reglas, instanciación del template | Sí |
| `doctor/` | 🩺 El Doctor: diagnóstico de salud del repositorio (y del código clonado), sólo lectura, informe HTML | Sí (menos `salida/`) |
| `back/` · `front/` | Carpetas donde se **clonan** los repos de código. Sólo aportan su README y las skills scoped de desarrollo | Sólo README y skills |
| `qa/` | Carpeta donde se **clona** el repositorio de pruebas de aceptación, si está aparte del código. Sólo aporta su README | Sólo README |
| `.gitlab-ci.yml` | Pipeline opcional del propio repositorio del Cerebro: espejos, conteos, pruebas de `bin/` y el Doctor | Sí |
| `.githooks/` | Hook pre-commit: espejos de skills, conteos, BOM y caracteres de control | Sí |

## 📊 Informe visual del esqueleto

`INFORME-ESQUELETO.html` muestra, en una sola página con índice, qué tiene el esqueleto, cómo fluye el
desarrollo, qué miden los scripts y el Doctor, qué propuestas esperan decisión y la bitácora. Lo genera
`python -B bin/generar-informe.py` (corre las pruebas y el Doctor; con `--rapido`, sólo el catálogo):
regenerarlo después de cambiar skills, scripts o decisiones.

## 🧠 Módulos del Cerebro Digital (OKF)

| Documento | Temática |
|-----------|----------|
| `contexto.md` | Origen del proyecto, organización, producto, alcance y equipo |
| `fuentes.md` | Registro de documentos de origen y trazabilidad |
| `roadmap.md` | Tablero de control de avance (MVPs, documentación, desarrollo) |
| `log.md` | Historial de cambios del Cerebro |
| `configuracion-ia/agentes.md` | Perfiles de agentes y sus checklists de entrega (DoD) |
| `configuracion-ia/orquestador-desarrollo.md` | Diseño del orquestador de código (Tareas listas → Merge Request) |
| `modulo-ejemplo/funcional/` · `metodologia/` · `arquitectura/` | Tres pilares del módulo: el qué, el cómo trabajamos y el cómo se construye |
| `modulo-ejemplo/aplicacion/` | El cuarto pilar, la memoria viva de la aplicación construida: `mapa.md` (qué existe), `aprendizajes.md` (`AP-nnn`) y `deuda.md` (`DT-nnn`); nace vacío y lo llena el desarrollo |
| `modulo-ejemplo/pendientes.md` | Preguntas abiertas (`P-nnn`) |
| `modulo-ejemplo/extraccion-reuniones/` | Insumo crudo de reuniones, sin consolidar |
| `diseno/diseno-sistema.md` | Tokens y componentes visuales del producto |

## 🛠️ Skills del Ecosistema (33 habilidades)

Registradas en `cerebro-digital/configuracion-ia/skills/` (fuente canónica) y reflejadas en los
espejos versionados `.claude/skills/` y `.agents/skills/`: **9 del Cerebro Digital** + **13 del
pipeline del tablero** (Azure DevOps por MCP o el tablero local) + **10 de desarrollo, QA y evolución** + **1 externa
vendorizada** (Archify).

### Cerebro Digital (9)

- `disenar-con-stitch`: las pantallas se diseñan y se pulen en Google Stitch (por MCP o pegando el prompt) a partir de la ficha; la exportación es la maqueta vigente y baja al front por `cerebro-architect-ui`.
- `cerebro-knowledge`: directivas de consulta obligatoria del Cerebro Digital.
- `cerebro-orquestador`: plan de ejecución, flujo de curaduría de 5 pasos, vigilancia semántica, ruteo del sub-flujo de tickets y umbrales de orquestación.
- `cerebro-architect-ui`: análisis de maquetas contra reglas, sin fake toggles.
- `cerebro-ppt-generator`: presentaciones HTML autocontenidas, sin compilar.
- `cerebro-mockup-design`: design system y tokens para mockups HTML.
- `cerebro-meet-analyst`: análisis de transcripciones de reunión y su registro en el OKF.
- `cognitive-doc-design`: patrones de documentación cognitiva (progressive disclosure, tablas de decisión, bloque de derivación).
- `engram-memory-protocol`: protocolo de memoria persistente en Engram.

### Pipeline del tablero (13)

- `redactar-tarea`: redacta un ticket suelto; no toca el board.
- `estimar-story-points`: Puntos de historia; no toca el board.
- `consultar-backlog`: consulta y audita el board (cobertura y desfase); sólo lectura.
- `analizar-tareas`: consistencia del set de Tareas de una Historia; opcional, a pedido.
- `auditar-historia`: segundo chequeo del Gherkin de una Historia; opcional, a pedido.
- `auditar-tarea`: segundo chequeo de la lista de tests de una Tarea; opcional, a pedido.
- `sincronizar-backlog`: baja una ficha entera al árbol Épica→Feature→Historia; escribe con confirmación.
- `planificar-lote`: modo lote con agentes en paralelo y dos turnos humanos; escribe con el "sí" del cierre.
- `cargar-a-azure`: crea o actualiza un work item; escribe con confirmación.
- `tomar-tarea`: asigna la tarjeta y la pasa a Active; escribe con confirmación.
- `comentar-tarea`: comenta la tarjeta (cierre de un desarrollo, pendientes a confirmar); lo único que entra en una tarjeta congelada.
- `desarrollar-asignadas`: desarrolla en paralelo las Tareas asignadas, con Orca o sin Orca (IntelliJ o terminal), sobre Azure o el tablero local; escribe con confirmación o según `DEC-005`.
- `atender-hallazgos`: recorre los hallazgos del Doctor uno por uno, con decisión humana en cada uno.

### Desarrollo, QA y evolución (10)

- `disenar-pruebas`: el rol de tester: desde el Gherkin de una Historia, el plan de pruebas de aceptación (qué se automatiza, qué queda exploratorio, bordes, datos sin datos de personas, ambiente, lista para recorrer a mano). No depende de la herramienta ni del tipo de aplicación.
- `automatizar-e2e`: el rol de QA automatización: las pruebas de punta a punta con el motor que fija `DEC-003` según el tipo de aplicación (Playwright para web y Electron; WebDriver para Tauri y escritorio; Appium o Maestro para móvil; proceso para línea de comandos; HTTP para API). `bin/armar-e2e.py` arma el esqueleto desde el Gherkin con la traza `Historia #id · Escenario`; `bin/cobertura-e2e.py` dice qué Escenarios quedaron sin prueba.
- `documentar-aplicacion`: al cerrar un slice o la app, la guía de uso y la documentación técnica y funcional, generadas desde el Cerebro (`bin/generar-documentacion.py`) con pantallas de Stitch y diagramas, y pulidas sin inventar.
- `arrancar-proyecto`: la puerta de entrada. «Arrancá un proyecto» o «agarrá el proyecto <carpeta>»: pregunta lo básico en un solo mensaje (nuevo o existente, nombres, módulo, solo o equipo, tablero, quién sos), muestra el plan y con tu «sí» corre `bin/arrancar-proyecto.py`.
- `desarrollo`: punto de entrada **único** para escribir, revisar o migrar código. Trae el método completo (TDD con evidencia del rojo, crear un endpoint, contrato primero, revisión por dimensiones, Merge Request, seguridad y datos sensibles, migraciones, observabilidad, entrega) y los guardarraíles. Lo específico del stack se completa en `references/metodo/tdd-stack-back.md` y `tdd-stack-front.md` cuando el equipo lo decide.
- `absorber-aplicacion`: una aplicación que ya existe se inventaría y se radiografía (`bin/inventariar-codigo.py`, `bin/radiografiar-codigo.py`: cada hecho con `archivo:línea`), se vuelca al Cerebro ítem por ítem con su marca de confianza y termina con la matriz de cobertura; qué hacer con la app lo decide `planificar-modernizacion` (sirve también sólo para documentarla: ingeniería inversa, método en `desarrollo/references/metodo/ingenieria-inversa.md`) y se decide con el humano si se refactoriza o se migra (`DEC-004`); sólo lee la aplicación.
- `planificar-modernizacion`: con el Cerebro poblado, compara estrategias (refactor en el lugar, estrangulador, corrida en paralelo, subir de versión, no tocarla) con la tabla medida, cura cada regla (migrar / descartar / decide el humano), escribe `DEC-004` con el «sí» y arma una ficha por slice. No programa.
- `caracterizar-comportamiento`: la red antes de tocar: corpus de casos desde la radiografía (`bin/armar-corpus.py`), golden grabado y firmado contra la app vieja (`bin/paridad.py grabar`), tests `test(caracterizacion)` si es refactor. Nunca PHI.
- `modernizar-slice`: ejecuta un slice de punta a punta: contrato del código viejo, construcción por el pipeline normal, paridad (`bin/paridad.py comparar`), clasificación de diferencias con una persona, corte sólo con `bin/mapa-modernizacion.py corte` en OK, apagado con «sí». Variantes: refactor en el lugar, código muerto, subir de versión.
- `mejorar-ecosistema`: autocorrección consultada: la IA registra en `mejoras.md` lo que detecta mal en arquitectura, reglas, skills o scripts y lo pregunta de a una; nunca lo aplica sola.

### Externa, vendorizada (1)

- `archify`: diagramas de arquitectura, flujo, secuencia, ERD y estados como HTML interactivo, con evidencia opcional del código; Apache-2.0, versión 3.2, requiere Node. Vendorizada con su licencia (sin `examples/`); detalle y cómo se actualiza en `DEPENDENCIAS-EXTERNAS.md`. Lo que entra al Cerebro sigue siendo el Mermaid de `radiografiar-codigo.py`.

**Carga por herramienta:** en **opencode** las reglas se leen del `AGENTS.md` nativo y las skills se auto-descubren de `.agents/skills/` y `.claude/skills/`; en **Claude Code**, `CLAUDE.md` importa las reglas con `@AGENTS.md` y las skills se auto-descubren de `.claude/skills/`; en **Antigravity**, `AGENTS.md` nativo y `.agents/skills/`; en **Gemini CLI**, `GEMINI.md` importa `@AGENTS.md` y las skills salen de `.agents/skills/`. Los dos espejos los mantiene idénticos a la fuente el hook pre-commit (`.githooks/`). Los **agentes** no viajan en el clone: los materializa `python -I bin/instalar.py` — ver `INSTALACION.md`.

## 📋 Checklist de contribución

- [ ] ¿Consultaste la fuente de verdad en `cerebro-digital/` antes de programar o redactar?
- [ ] ¿El cambio de negocio fue validado por una persona antes de que `cerebro-curator` lo escribiera en el OKF?
- [ ] ¿Las especificaciones técnicas en `entregables/especificaciones-tecnicas/` tienen wikilinks hacia las reglas funcionales?
- [ ] ¿Corriste `python -I bin/instalar.py` después de clonar (hook activo, agentes materializados, espejos y skills verificados)?
