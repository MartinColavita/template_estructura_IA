---
name: auditar-historia
description: >-
  (Solo lectura, adversarial) Auditar UNA Historia de usuario ya escrita —el segundo chequeo,
  hecho por un agente DISTINTO del que la redactó— antes de derivar Tareas de ella: que el
  Gherkin de los Criterios de aceptación sea VERIFICABLE (un Entonces observable y un
  comportamiento por Escenario, actor explícito, sin "correctamente"), que los Casos de uso y
  los Datos y estados queden cubiertos, que las reglas citadas existan y digan lo que se les
  atribuye, que ningún Entonces afirme sobre un punto que el Cerebro tiene abierto, y que el
  bloque "## Derivación a backlog" de la ficha fuente esté COMPLETO en los dos sentidos. Si el
  Documento fuente es un mockup no bloquea: deja escrito qué queda sin auditar. Usar cuando se
  pida "auditá la historia", "revisá los criterios de la #NNNNN", "¿esta Historia está lista
  para derivar Tareas?", "/auditar-historia". OPCIONAL: corre sólo a pedido y NO frena la
  derivación. NO redacta, NO corrige, NO escribe en el board: devuelve hallazgos y preguntas.
  Español (Argentina).
---

# Auditar historia

Audita **una** Historia de usuario contra su ficha fuente, **antes** de que se deriven
Tareas de ella. Es el equivalente de [[auditar-tarea]] un nivel más arriba, y lo corre
**otro agente, en otro turno, sin haber participado de la redacción** (en modo lote, un
sub-agente aparte, con su propio contexto, cuenta como otro turno).

## Regla de oro

- **Verificador ≠ productor.** Lo corre un agente **distinto** del que redactó la Historia
  o la ficha. Si sos quien la escribió, decilo y **no la audites**.
- **Adversarial.** El trabajo es encontrar el hueco. Una auditoría sin hallazgos es un
  resultado válido, pero recién después de haber buscado en serio.
- **Solo lectura.** No redacta, no corrige, no escribe en el board, **no toca el Cerebro**.
  Lo que encuentra sale como **hallazgo + pregunta**.
- **En modo lote ([[planificar-lote]]) cada hallazgo sale marcado F o P.** **F**: lo
  resuelve una fuente (regla del Cerebro, maqueta vigente, respuesta del humano), y se escribe
  cuál y el texto exacto del arreglo; lo aplica quien redacta, no esta skill. **P**: necesita a
  una persona, y va como pregunta al arranque o al cierre del lote. Una regla que no existe es
  siempre P: ninguna fuente la reemplaza. Un hallazgo del chequeo 19 (un `Entonces` sobre un
  punto que el Cerebro tiene abierto) es F sólo si la maqueta vigente lo define, y entonces va
  también al «Conocimiento para el Cerebro» del cierre como ✅ que resuelve ese `P-nnn`: el "sí"
  del cierre es la decisión. Si nada lo define, es P.
- **No inventar, y no completar por analogía.** Si una regla citada no existe, **no se
  deduce cuál «debería» ser**: se marca NO AUDITABLE y se pregunta. Proponer la regla que
  falta es exactamente el defecto que esta skill persigue.
- **Español (Argentina)**, sin emojis como íconos.

## Barreras

- **Solo lectura del board y del Cerebro.** Nunca `create_work_item`/`update_work_item`, ni
  escritura en `cerebro-digital/`.
- **No corrige.** Propone el texto del Escenario o del `[F-nn]` que falta, para que otro lo
  cargue con su confirmación.
- **No aprueba por cansancio.** Lo que no se pudo verificar es NO AUDITABLE, no «cumple».
- **PHI prohibido** en el reporte (marcadores `<persona>`, `<documento>`, etc.).

## Insumos

1. La **Historia**: campo Descripción (bloques *Datos y estados*, *Reglas de negocio*,
   *Casos de uso*, *Documento fuente*) y campo **Criterios de aceptación** (el Gherkin). En
   modo lote, si el lote la crea o la pisa, su **borrador** (`borrador/lote-*/`).
2. La **ficha fuente** del Cerebro que la Historia declara en *Documento fuente*, con su
   bloque **`## Derivación a backlog`** y su prosa completa.
3. Las **reglas citadas**, por su ruta en el Cerebro.

Si falta el 1, no hay nada que auditar. Si falta el 2 o el 3, se audita lo que se puede y
el resto sale **NO AUDITABLE** — nunca «cumple» por defecto.

> ### Regla del cero — un conteo vacío NUNCA es un «cumple»
> Igual que en [[auditar-tarea]]: si un insumo externo viene vacío, el conteo da `0 = 0` y
> el chequeo **pasa por vacuidad**. El caso central de esta skill: **una Historia sin
> Gherkin**. Hoy el campo Criterios de aceptación *«aparece vacío en la mayoría de las
> historias»* ([[criterios-aceptacion-gherkin]]), y con 0 Escenarios **todos** los chequeos
> del loop BDD↔TDD de abajo pasan sin que nada lo diga. Si hay 0 Escenarios, el veredicto
> es **NO AUDITABLE** y la Historia **no deriva Tareas**. Lo mismo vale para cualquier **bloque ausente** de la Historia o de la ficha: ausente no es cumplido.

## Quién la dispara (y quién NO)

> **Es opcional y no frena nada** (decisión de diseño del template). Corre sólo cuando alguien la
> pide —un dev, o quien arma un lote y la quiere—; ni [[sincronizar-backlog]], ni
> [[cargar-a-azure]], ni [[planificar-lote]] la disparan solos, ni buscan su sello para derivar
> Tareas. Exigirla gastaba muchos tokens y volvía a preguntar cosas ya cerradas. Lo que encuentre
> se deja **como pendiente** en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar»).

**No la invoca el funcional. Nunca.** Él arma las Historias con el conocimiento del OKF y
su mockup, pimponeando con la IA lo que falte — ese flujo **no se toca**.

| Quién | Cuándo | Cómo |
|---|---|---|
| **El funcional** | — | **Nunca la invoca.** Su flujo queda igual |
| **El flujo dev** | Al derivar Tareas ([[sincronizar-backlog]]) o al crear una Tarea contra esa Historia ([[cargar-a-azure]] §3b) | **Sólo si se pide**, después del GATE de NIVEL. No corre sola |
| **Un dev, a mano** | Cuando quiera revisar una Historia antes de tocarla | `/auditar-historia` |
| **El modo lote** ([[planificar-lote]]) | Si quien arma el lote la pide: en la preparación, sobre cada Historia padre; o en la auditoría del lote, sobre cada Historia que el lote redacta o corrige | **Sólo si se pide**, un agente por Historia, en paralelo |

Por qué conviene correrla del lado dev, y también al crear la Historia en el lote:
`references/por-que-y-ejemplo.md`.

## Flujo

1. **Leer el sello previo**, si hay, y ver si sigue vigente (`references/sello.md`): con sello
   vigente no se vuelve a auditar.
2. **Conseguir los insumos** (arriba) y acotar lo que no se pueda mirar.
3. **Correr el script** (abajo) y copiar su resultado.
4. **Los chequeos de criterio** que el script no hace (`references/chequeos.md`).
5. **Veredicto** y **sello** en la tarjeta, con [[comentar-tarea]] y su confirmación.
6. **Reportar** como hallazgos y preguntas, con su dueño (tabla «Quién arregla»).

## Primero, el script

Antes de leer nada a mano, esta skill **corre**:

```
python bin/auditar-historia.py --criterios <criterios.html> --descripcion <descripcion.html> --ficha <ficha.md> --flujo F-nn --json
```

Los Criterios y la Descripción van como archivos: en modo lote son los borradores; si no, se
guardan desde el tablero. El script hace lo que es **conteo y forma**:
- que haya Escenarios y que cada uno tenga su Cuando y su Entonces;
- las palabras vagas en el Entonces;
- que cada Escenario cite una regla, y que la regla exista;
- títulos repetidos y Esquemas sin Ejemplos;
- las reglas de la Historia contra las del `[F-nn]` en la ficha;
- el Documento fuente;
- los puntos abiertos citados;
- el formato.

**Eso no se rehace a mano**: su resultado se copia al reporte. Lo que marca HALLAZGO es
hallazgo, y si no corrió, esos chequeos son SIN DATOS. Si la herramienta no puede correr
comandos, se le pide a la persona ese comando exacto. Abajo, la auditoría hace **sólo** lo que el
script lista en «Lo que este script NO mira», y confirma o descarta sus AVISOS.

Los 20 chequeos, uno por uno (1 ficha fuente · A Gherkin 2–10 · B Historia contra ficha 11–14 ·
C bloque de derivación 15–18 · D lo que se afirma sin respaldo 19–20): `references/chequeos.md`
(leerlo antes de auditar).

## El sello

Al terminar, el veredicto **se escribe en la tarjeta** con [[comentar-tarea]] (que pide su
propia confirmación humana —en modo lote, la del cierre—; esta skill no escribe por su cuenta):
el formato, cómo se mide la vigencia (`bin/verificar-sello.sh`) y cuál manda, en
`references/sello.md` (leerlo antes de escribir el sello o de juzgar uno anterior).

## Veredictos

| Veredicto | Cuándo | Qué significa |
|---|---|---|
| **COMPLETA** | Los 20 chequeos pasan | No se encontró nada que falte |
| **CON HUECOS** | Falta cobertura, o un Escenario no es verificable | Lo que falta se deja como **pendiente a confirmar**. Se puede corregir primero —en modo lote, la corrección entra en el mismo lote— o seguir; **no frena la derivación** |
| **NO AUDITABLE** | 0 Escenarios, o una regla citada no existe | Se dice qué no se pudo mirar, y queda como pendiente. Nunca se da por buena una Historia que no se pudo auditar, pero la auditoría **no frena**. (Con 0 Escenarios no se derivan Tareas igual, por el DoR) |

> **La falta de ficha NO da NO AUDITABLE.** Deja los chequeos 11 a 18 sin poder correr, y eso
> se **declara** en el reporte y en el sello («sin ficha: 11–18 no auditables»), pero el
> veredicto sale de los **once** chequeos que sí corrieron. Una Historia armada sobre OKF +
> mockup puede dar **COMPLETA** — con esa limitación escrita a la vista.

**Si se dan las dos** (faltan cosas **y** hay algo que no se pudo verificar), el veredicto es
**CON HUECOS + NO AUDITABLE en «el punto X»** — se reportan las dos, no se elige una. Se
arreglan por caminos distintos: los huecos los cierra quien redacta; lo no auditable exige
**cargar lo que falta en el Cerebro**.

## Quién arregla lo que esta skill encuentra (el hallazgo tiene dueño)

Un hallazgo que no tiene destinatario termina en que alguien **inventa** para
cerrarlo — justo lo que todo este aparato viene a impedir. El reparto es:

| Qué falló | Quién lo arregla |
|---|---|
| Gherkin ausente, vago o mal formado (bloque A) | **[[redactar-tarea]]**, que redacta Historias además de Tareas: toma la Historia existente y cierra sus Criterios de aceptación, preguntando lo que no puede saber |
| `CU-nn` / *Datos y estados* sin cubrir (bloque B) | **[[redactar-tarea]]**, misma pasada |
| Reglas que no existen, o que no dicen lo que se les atribuye (9, 12) | **El equipo funcional**, en el Cerebro. Ninguna skill inventa una regla para destrabar |
| Bloque de derivación incompleto (bloque C) | **`cerebro-analyst` + `cerebro-curator`** con [[cognitive-doc-design]] — proponen, y un humano valida |

> **Si la Historia está congelada** (en un sprint y ya tomada), lo que corrige
> [[redactar-tarea]] no lo carga la IA: va como comentario y **lo carga una persona a mano**
> ([[cambios-en-el-backlog]] §4).

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| `references/chequeos.md` | Antes de auditar: los 20 chequeos de criterio, uno por uno |
| `references/sello.md` | Al empezar (¿hay un sello vigente?) y al dejar el veredicto en la tarjeta |
| `references/por-que-y-ejemplo.md` | Para el porqué de la skill, cuándo conviene correrla, su lugar en el pipeline o un reporte de ejemplo |

## Contexto adicional

- El equivalente un nivel abajo: [[auditar-tarea]]
- Consistencia del conjunto de Tareas: [[analizar-tareas]]
- Cómo se escribe el Gherkin: [[criterios-aceptacion-gherkin]]
- Plantilla y bloques: [[plantillas/historia-de-usuario]]
- Formato del bloque de derivación: [[organizacion-y-trazabilidad]] §5
