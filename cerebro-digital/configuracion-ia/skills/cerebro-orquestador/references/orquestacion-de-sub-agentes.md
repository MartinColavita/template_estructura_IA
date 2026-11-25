# Orquestación de sub-agentes, sesión dedicada y entrega directa

Parte de la skill `cerebro-orquestador`: se lee cuando se va a delegar en un sub-agente, mientras haya workers corriendo, antes de dar por listo un entregable, al abrir una sesión dedicada a una función y al entregar al usuario el resultado de un sub-agente.

## 🤖 Orquestación de sub-agentes — umbrales objetivos

La tabla que manda es la de `SKILL.md` (§«Orquestación de sub-agentes»); ésta es su detalle, y si difieren, se
corrige ésta.

Umbrales **objetivos**, para que el comportamiento no dependa de la sesión ni del modelo.
Cuando se cumple el disparador **se actúa**; no se evalúa "si hace falta".

| Disparador | Acción obligatoria |
|---|---|
| Hay que leer **4+ archivos** para entender un flujo | Delegar la exploración a un sub-agente; no hacerla inline |
| Se van a tocar **2+ archivos no triviales** | **Un solo** escritor; o revisión con contexto fresco antes de dar por cerrado |
| Hubo un **incidente** (directorio equivocado, accidente de git, recuperación de merge, comandos de test confusos, workaround de entorno) | **Auditoría fresca** antes de seguir |
| Se acumulan ~**20 llamadas a herramientas**, 5 lecturas exploratorias o 2 ediciones no mecánicas con complejidad creciente | **Pausar y replanificar** (en modo lote, sin pedirle un turno al humano: el lote ya tiene sus dos) |
| Se va a entregar un PR/MR | La revisión aporta **evidencia**, pero **NUNCA autoriza la entrega por sí sola**: decide la política del repo y el humano |

**Ruteo por tamaño:**
- **1 a 3 archivos** y sin ambigüedad → implementación **directa**, sin proceso largo.
- **4+ archivos**, o si toca contrato o reglas de negocio → **delegar** por fases.
- Una tarea chica **no se infla** con estructura que no aplica (ver [[plantillas/tarea]]).

### Herramientas y skills NO se heredan

Al delegar en un sub-agente, **el contexto del padre no viaja**: toolsets, servidores MCP y
skills **hay que pasárselos explícitamente** en la misión. Un worker que necesita `guiar-tdd`
y no la recibe, **no la tiene** — y va a trabajar sin la disciplina que creíamos aplicada.
Es el error silencioso más caro al orquestar: todo "parece" correr bien y el control no existió.

### Compresión de handoffs (control de tokens)

Los agentes no se pasan el historial completo del chat. Cada delegación incluye **únicamente**:
el **Objetivo** actual, la **Ruta** de los archivos relevantes, y el **Resultado Esperado** en
Markdown estructurado.

**Y siempre, la línea del idioma: «Respondé y escribí todo en español (Argentina).»** Un
sub-agente no hereda el idioma de la conversación: si la misión no lo dice, contesta en inglés.

### El orquestador queda atento a sus workers

Delegar no es irse. Mientras haya un worker o un verificador corriendo, el orquestador **sigue
escuchando**: la espera de sus mensajes corre en segundo plano y lo despierta. Cada pregunta se
contesta al llegar (la técnica con recomendación clara la contesta él y se la lista al humano;
un dato duro o una regla de negocio se le trae al humano en ese momento), y **cada worker que
termina se le avisa al humano en ese momento**. El trabajo no se da por terminado mientras quede
uno sin cerrar. En Orca, el detalle es [[desarrollar-asignadas]] §6.0.

### Revisión adversarial — el Juez

Antes de que `cerebro-curator` escriba en el OKF, o de que `cerebro-architect` valide una
especificación, se puede invocar un rol de **Juez temporal** que valida **a ciegas** el
entregable contra la checklist de `agentes.md`. Si detecta fallas, vuelve al emisor; si pasa,
va a validación humana.

**Para revisar diffs, conflictos o "¿está listo para entregar?", se usa un agente con contexto
nuevo — nunca el mismo que produjo el cambio.** Es el mismo principio aplicado al código, y es
la forma concreta de "quien produce no aprueba".

### Autonomía de los sub-agentes

Los ejecutores (`analyst`, `curator`, `architect`) operan **aislados**: **PROHIBIDO** delegar a
otros agentes o invocar sub-agentes adicionales. Resuelven su tarea de forma atómica y
devuelven el resultado al orquestador.

## Sesión dedicada a una función

Viene de la sección «Ruteo por función» de `SKILL.md`.

**Sesión dedicada.** Para un trabajo largo de una sola función se puede abrir la sesión con su orquestador
(`claude --agent orquestador-<función>`, en `INSTALACION.md`): carga la puerta sola y no debe escribir archivos; delega en
`nucleo-productor` y en `nucleo-verificador`.

## 🎯 Entrega Directa
Al entregar el resultado final del sub-agente al usuario, evitá reportes, tablas o explicaciones técnicas innecesarias sobre las herramientas usadas internamente. Presentá el entregable de forma directa, manteniendo el tono conversacional habitual del asistente — sin narrar el paso a paso interno.

> **No aplica a la Consulta Interactiva de Decisión.** Esta regla restringe la narración técnica/de herramientas al entregar un resultado ya resuelto. La Consulta Interactiva de Decisión de la Vigilancia Semántica de Conversación es precisamente lo opuesto a "texto dentro de la respuesta": es una interacción estructurada fuera del cuerpo de la respuesta, obligatoria, y nunca debe omitirse ni convertirse en una tabla dentro de la respuesta por esta regla.
