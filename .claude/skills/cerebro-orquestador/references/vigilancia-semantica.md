# Vigilancia semántica: disparadores, modo lote, clasificación y anti-patrones

Parte de la skill `cerebro-orquestador`: se lee cuando aparece en la conversación un candidato a conocimiento de negocio, antes de disparar su Consulta Interactiva de Decisión (Paso B, en `SKILL.md`), y siempre durante un lote.

### Cuándo evaluar (disparadores)
| Señal en la conversación | ¿Dispara vigilancia? |
|---|---|
| El usuario afirma una regla de negocio, dato operativo o comportamiento del sistema no documentado en el OKF | Sí |
| El usuario corrige o contradice un dato ya escrito en el OKF | Sí |
| El usuario confirma una decisión de arquitectura/negocio que estaba como hipótesis o en `pendientes.md` | Sí |
| El usuario responde una pregunta abierta de algún `pendientes.md` | Sí |
| Pedido técnico sobre el repo, consulta de lectura sin aportar dato nuevo, comentario circunstancial sin regla | No |

No evaluar turno a turno de forma ruidosa: agrupar los candidatos detectados y disparar sus Consultas Interactivas de Decisión al cierre del tema/tarea, o antes si el usuario pide cerrar la sesión.

> **Excepción: modo lote** ([[planificar-lote]]). Durante un lote, lo que el humano dice en el
> arranque **es la respuesta a las preguntas del lote**: no dispara una consulta por ítem. Lo que
> esas respuestas fijan (una decisión, una regla, un pendiente resuelto) se lista en el **cierre**
> del lote, **un renglón por ítem**, con su clasificación (🆕/♻️/✅), la paráfrasis fiel y su
> destino. El "sí" del cierre lo guarda; lo que el humano tache, no se guarda. La disciplina es la
> misma —cada ítem a la vista, paráfrasis fiel, nada se guarda sin decisión explícita—; cambia que
> se decide en el cierre, todo junto, en lugar de una interacción por ítem. **Fuera del lote, el
> Paso B sigue igual.**

### Paso A — Detección y clasificación
Por cada candidato, contrastar contra el OKF (`contexto.md`, `index.md` del módulo correspondiente, `pendientes.md` del módulo) y clasificar:
- 🆕 **Nuevo**: no hay nota existente que lo cubra.
- ♻️ **Cambio**: contradice o actualiza una nota ya escrita en el OKF (identificar la nota afectada con wikilink).
- ✅ **Resuelve pendiente**: matchea un ítem de algún `pendientes.md` (referenciar su `P-XXX`).

### Anti-patrones (prohibido)
- ❌ Escribir directo al OKF sin pasar por su propia Consulta Interactiva de Decisión.
- ❌ Renderizar los ítems detectados como texto o tabla dentro de la respuesta normal, en vez de disparar interacciones estructuradas.
- ❌ Agrupar varios ítems detectados en una sola interacción o pregunta genérica (fuera del modo lote; en el lote van en el cierre, un renglón por ítem).
- ❌ Inventar o completar la redacción de una regla más allá de lo que el usuario dijo (incluso al procesar "Editar y Guardar").
- ❌ Disparar una interacción por cada mensaje trivial (ruido conversacional).
- ❌ Interpretar "no dijo que no" como confirmación.
