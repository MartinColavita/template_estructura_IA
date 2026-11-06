# Referencias externas — qué se tomó y de dónde

## Para qué existe este archivo

Dos motivos, y ninguno es burocrático:

1. **La licencia MIT lo pide.** Permite usar y modificar el material, **con atribución**. Si
   tomamos ideas de ahí y no lo decimos, incumplimos la única condición que pone.
2. **Para poder revisar la fuente después.** Cuando alguien pregunte *"¿de dónde salió esta
   regla?"*, o cuando la fuente se actualice y queramos ver si aprendió algo nuevo, la
   respuesta tiene que estar escrita y no en la memoria de quien la escribió.

**Lo que NO es: una dependencia.** Esto es **bibliografía**, no un import. Nada de lo que se
cita acá se instala, se invoca ni se descarga en ninguna máquina; no hay servidor que
consultar ni token que configurar. Las skills están **escritas en este repositorio**, en
español, con nuestro vocabulario y nuestras reglas; lo que vino de afuera son ideas y
estructura, y acá queda dicho cuáles y de dónde.

---

## `wshobson/commands`

| | |
|---|---|
| Origen | https://github.com/wshobson/commands |
| Licencia | **MIT** — uso, modificación y redistribución **con atribución** |
| Consultado el | 2026-09-18 |
| Qué es | 57 comandos para Claude Code: 15 workflows y 42 herramientas |

### Qué se tomó, archivo por archivo

**Ideas y estructura, no texto.** El original está en inglés, escrito como *comandos*
(invocados por el usuario, no elegidos por el modelo) y referencia subagentes de su
repositorio hermano —`architect-review`, `test-automator`, `code-reviewer`— que acá no
existen. Copiarlo tal cual habría dejado referencias rotas.

| De dónde | Qué se adaptó | A dónde fue |
|---|---|---|
| `workflows/tdd-cycle.md` | Las fases como **compuertas**: no se avanza sin cumplir la anterior | [metodo/tdd-ciclo-y-evidencia.md](metodo/tdd-ciclo-y-evidencia.md) |
| `workflows/full-review.md` | Revisión **por dimensiones separadas** y clasificación por severidad | [metodo/code-review.md](metodo/code-review.md) |
| `workflows/feature-development.md` · `full-stack-feature.md` | La orquestación back + front **en paralelo** a partir de un contrato | [metodo/arrancar-funcionalidad.md](metodo/arrancar-funcionalidad.md) |
| `workflows/smart-fix.md` | El ciclo de arreglo y la distinción entre tipos de bug | [metodo/arreglar-un-bug.md](metodo/arreglar-un-bug.md) |
| `workflows/security-hardening.md` · `tools/security-scan.md` · `compliance-check.md` | Los controles de dato sensible: mínimo necesario, propósito, registro de acceso | [metodo/seguridad-y-datos-sensibles.md](metodo/seguridad-y-datos-sensibles.md) |
| `workflows/performance-optimization.md` · `tools/multi-agent-optimize.md` | Medir antes de optimizar, y los sospechosos habituales | [metodo/rendimiento.md](metodo/rendimiento.md) |
| `workflows/incident-response.md` | Contener → avisar → entender → arreglar → aprender | [metodo/incidentes.md](metodo/incidentes.md) |
| `workflows/git-workflow.md` | Convención de ramas y de mensajes de commit | [metodo/ramas-y-commits.md](metodo/ramas-y-commits.md) |
| `workflows/workflow-automate.md` · `tools/deploy-checklist.md` | Qué tiene que **frenar** el pipeline, y la vuelta atrás definida antes | [metodo/entregar-a-produccion.md](metodo/entregar-a-produccion.md) |
| `tools/test-harness.md` | Las **7 categorías**, el **testing por mutación**, el basado en propiedades, las fábricas y las causas de tests inestables | [metodo/armar-la-suite.md](metodo/armar-la-suite.md) |
| `tools/api-mock.md` | Generar las simulaciones **desde el contrato**, escenarios de error, latencia, deriva | [metodo/simular-api-desde-el-contrato.md](metodo/simular-api-desde-el-contrato.md) |
| `tools/api-scaffold.md` | La **taxonomía de familias de error** y la checklist de cierre. **Con el orden invertido** — ver abajo | [metodo/crear-endpoint.md](metodo/crear-endpoint.md) |
| `tools/pr-enhance.md` | Los **límites de tamaño** (20 archivos / 1000 líneas) y los bloques de la descripción | [metodo/merge-request.md](metodo/merge-request.md) |
| `tools/smart-debug.md` · `debug-trace.md` · `error-trace.md` · `error-analysis.md` | Reproducir antes de arreglar, correlación por `trace_id`, agrupar errores por causa | [metodo/depurar.md](metodo/depurar.md) |
| `tools/refactor-clean.md` · `tech-debt.md` | Qué se busca al refactorizar, y cómo se prioriza la deuda | [metodo/refactor.md](metodo/refactor.md) |
| `tools/monitor-setup.md` · `slo-implement.md` | Las **4 señales**, campos del log estructurado, alertas sin fatiga, presupuesto de error | [metodo/observabilidad.md](metodo/observabilidad.md) |
| `tools/db-migrate.md` | **Expandir / migrar / contraer**, tandas, vuelta atrás, validación antes y después | [metodo/migracion-de-base.md](metodo/migracion-de-base.md) |
| `tools/deps-audit.md` · `deps-upgrade.md` · `config-validate.md` | Revisión de vulnerabilidades y licencias, actualizar de a una, manejo de secretos | [metodo/dependencias-y-config.md](metodo/dependencias-y-config.md) |
| `tools/accessibility-audit.md` | Los chequeos de teclado, foco, nombre accesible y contraste | [metodo/accesibilidad.md](metodo/accesibilidad.md) |
| `tools/code-explain.md` · `onboard.md` | Leer de afuera hacia adentro, y el arranque de alguien nuevo | [metodo/entender-codigo-ajeno.md](metodo/entender-codigo-ajeno.md) |

Las plantillas por stack —[metodo/tdd-stack-back.md](metodo/tdd-stack-back.md) y
[metodo/tdd-stack-front.md](metodo/tdd-stack-front.md)— no toman nada de esta fuente: son
material propio que cada proyecto completa al elegir su stack.

**33 de los 57 comandos**, agrupados en las 20 filas de arriba — varias filas citan más de una
fuente. **Los otros 24 se descartaron por no aplicar.**

**De esos 24 se nombran 20 acá abajo; la lista NO es exhaustiva.** Agrupados por el motivo del
descarte: ML y datos (`data-pipeline`, `data-driven-feature`, `data-validation`), móvil
(`multi-platform`), migración de sistemas viejos (`legacy-modernize`, `code-migrate`),
infraestructura que todavía no manejamos (`docker-optimize` y el de manifiestos de
orquestación de contenedores), nube y costos (`cost-optimize`), meta-herramientas
(`improve-agent`, `prompt-optimize`, `ai-assistant`, `ai-review`, `langchain-agent`,
`multi-agent-review`, `context-save`, `context-restore`), y los que ya cubren nuestras propias
skills del Cerebro (`issue`, `standup-notes`, `doc-generate`).

### Lo más valioso que salió de ahí

**El testing por mutación.** Es la respuesta mecánica a nuestra propia regla *"un test que no
puede fallar no sirve"*: cambia el código a propósito y mira si algún test se da cuenta. Mide
lo que la cobertura no puede.

### Dónde le dimos vuelta el orden

`api-scaffold` genera el schema y los tests **al final**, después de la implementación. Acá es
al revés: **contrato primero, tests después, código último**. Un contrato que sale de la
implementación no puede contradecirla nunca, y entonces no sirve para que el front programe
contra él.

### Dónde somos más exigentes que la fuente

Vale dejarlo escrito, porque justifica haber escrito material propio en vez de traducir:

1. **Evidencia del rojo guardada**, y que haya fallado **en su aserción** — no sólo la
   instrucción de verificar que falle.
2. **Verificador distinto del productor.** Quien escribe nunca aprueba.
3. **Veredicto de tres estados** (OK / HALLAZGO / SIN DATOS). "No pude mirar" no es "está
   bien".
4. **Regla del cero.** Un conteo en cero sobre entrada externa no es aprobado: es no
   auditable.
5. **PHI prohibido** con lista de marcadores, en todo: código, tests, fixtures, logs,
   contrato y descripción del Merge Request.

### Qué NO se tomó

El formato de comando, las referencias a subagentes inexistentes, el inglés, su stack de
ejemplo, y su definición más floja de "test en rojo".
