---
name: comentar-tarea
description: >-
  Agregar un comentario a un work item de Azure DevOps (queda en el Historial /
  Discusión de la tarjeta) y, si hace falta, leer los comentarios existentes. Usar
  cuando se pida "comentá en la #NNNN", "dejá una nota en la tarjeta", "respondé el
  comentario de X", "/comentar-tarea", al TERMINAR UN DESARROLLO (el comentario de
  cierre: rama, Merge Request, resumen técnico y pendientes a confirmar), para dejar un
  hueco o un gris como pendiente, y ANTES DE CERRAR una Tarea (revisar en sus comentarios
  los pendientes sin resolver). Es la
  única escritura que entra en una tarjeta congelada (en un sprint y ya tomada). Leer
  comentarios no requiere permiso; escribir el comentario se hace con confirmación.
  Español (Argentina), sin PHI.
metadata:
  seccion: tickets
---

# Comentar tarea (comentarios en Azure)

> **Tablero local (`DEC-006`):** el board es `backlog/` del módulo, con los mismos GATEs y sin MCP: [contexto](references/contexto.md).

Permite **leer** y **dejar** comentarios en un work item. En Azure DevOps el
comentario de una tarjeta se escribe en el campo **Historial / Discusión**
(`System.History`).

## Regla de oro
- **Las barreras de escritura son las de [[AGENTS]]** («Automatización por MCP — barreras»): antes de postear en
  `System.History` se verifica que la tarjeta sea del tablero autorizado ([[tablero-autorizado]]).
- **Leer es libre; escribir con confirmación.** Antes de postear, mostrar el texto y a qué `#ID` va, y esperar tu OK — mostrar y postear son pasos distintos, no el mismo turno. **Los sellos de auditoría de un lote** ([[planificar-lote]]) se publican con el "sí" del cierre del lote: la tabla del cierre muestra el veredicto de cada tarjeta, y el sello es el molde fijo de `references/formato.md` con esos valores.
- **Sin PHI** en el comentario (marcadores `<persona>`, `<identificador>`… en su lugar). **Español.**
- **No inventar:** si el comentario afirma un dato duro sin confirmar, marcarlo `⚠`.
- **Un comentario es sólo un comentario.** La escritura lleva `System.History` y **ningún otro
  campo**. Colar un cambio de Estado, de Etiquetas o de Descripción en la misma llamada es
  editar la tarjeta con otro nombre, y en una **tarjeta congelada** eso está prohibido
  ([[cambios-en-el-backlog]] §4).
- **Bien formateado, siempre** (ver «Formato», abajo). Un comentario que se lee como un muro
  no lo lee nadie, y entonces no avisa nada.

## Flujo
1. (Opcional) **Leer el hilo:** `get_work_item_comments` del `#ID`.
2. **Redactar** el comentario en español, sin PHI, **en HTML** con el molde que corresponda.
3. **Mostrar** el comentario **como se va a ver** —no el HTML crudo, que nadie puede evaluar— y
   la tarjeta destino (`#ID`).
4. Con tu **OK**, **postear**: `update_work_item` sobre el campo `System.History` —y sólo ese— (así queda en la discusión de la tarjeta).

> Nota: si el servidor MCP expone una herramienta específica para comentar un work
> item, se usa esa; si no, el mecanismo estándar de Azure es `System.History` vía
> `update_work_item`.

## Tarjeta congelada: acá sí se escribe

Una tarjeta **en un sprint y ya tomada** (Estado distinto de `New`) queda congelada: no se le
edita nada, sólo se comenta. Esta skill es por donde pasa todo lo que la IA quería cambiar
sobre ella: el DIFF propuesto va **como comentario**, con @mención a quien la tiene, y
aplicarlo lo decide una persona. Detalle: [[cambios-en-el-backlog]] §4.

Sirve para cualquier motivo: que cambió el documento funcional, que una auditoría encontró un
hueco, o que a un equivalente le falta completar un campo.

El molde del cambio propuesto, con su ejemplo lleno: [moldes](references/moldes.md), al redactarlo.

## Comentario de cierre de desarrollo

> **Los datos duros los lee un script.** `bin/datos-cierre.py --repo <worktree> --base <base> --id <ID>`
> devuelve rama, último commit, cantidad de commits, archivos y carpetas tocadas, si está pusheada, el
> respaldo `evidencia/<ID>` y el link para abrir el Merge Request; lo que no pudo leer lo dice. La prosa
> del resumen técnico la pone esta skill con el resumen del worker; los datos no se escriben de memoria.

> **Lo aprendido no se queda en el comentario:** lo del negocio va al Cerebro y lo de la aplicación a
> `<modulo>/aplicacion/`; cómo, al redactar el cierre: [comentario-de-cierre](references/comentario-de-cierre.md).

Cuando termina el desarrollo de una Tarea, **quien lo terminó deja constancia en la tarjeta**:
qué rama, qué Merge Request y qué se hizo. Así la tarjeta cuenta sola cómo se resolvió, sin
tener que ir a buscarlo al código.

| | |
|---|---|
| **Cuándo** | Cuando la Tarea llega al Merge Request —o se pushea la rama, si el equipo mergea en local—: paso 7 del [[orquestador-desarrollo]], o al preparar la entrega en un desarrollo a mano ([[desarrollo]]). **Después** de que corrieron las verificaciones, porque el comentario informa su veredicto |
| **En qué tarjetas** | En **cada Tarea** que ese desarrollo cerró. La Historia padre no se comenta: el comentario ya la nombra, y repetirlo en el padre llena su hilo de ruido |
| **Quién lo postea** | Quien tiene el tablero: el orquestador, con el resumen del worker; en un desarrollo a mano, la misma sesión que programó |
| **Confirmación** | La de siempre: se muestra y se espera el "sí". Si terminan varias Tareas juntas, se muestran todos los comentarios juntos y **un "sí" cubre exactamente ese lote**, como en [[sincronizar-backlog]] |

**Los datos duros salen del repositorio, nunca de la memoria.** La rama y el último commit, de
`git`. El link del Merge Request, leído de GitLab por el MCP, **sólo lectura**: el comentario
**nunca abre ni toca un Merge Request**. Los tests, de la lista «Tests a escribir PRIMERO» y de
los commits `test(rojo)` del historial de trabajo (la rama `evidencia/<ID>`, subida a `origin`). Los
veredictos, de lo que devolvieron las verificaciones.

**La parte en prosa** —qué se hizo, cambios que rompen, lo que quedó afuera— sale de la
**descripción del Merge Request**, que ya tiene esos bloques ([[desarrollo]],
`merge-request.md`). Si no hay Merge Request, sale del **resumen final del worker**, y el
comentario lo dice: *«según el resumen del desarrollo»*. **Lo que no se pudo leer se escribe
`⚠ sin dato`**: una línea vacía no se rellena con lo esperable.

El molde y cómo se llenan los casos que no son el feliz: [comentario-de-cierre](references/comentario-de-cierre.md), al redactar el comentario.

**«Ninguno» y «Nada» son datos, no valores por defecto.** Se escriben sólo si la descripción
del Merge Request o el resumen del desarrollo lo dicen. Si no lo dice nadie, va `⚠ sin dato`:
un «ninguno» que nadie afirmó es una afirmación inventada. Lo mismo con «Qué se hizo»: se
copia de la fuente, no se redacta a partir del título de la Tarea.

**Barreras del cierre.**

- **Un veredicto que no corrió es `SIN DATOS`, no aprobado.** Si una verificación dio
  hallazgos, el comentario **lo dice**: no se omite para que la tarjeta quede prolija.
- **El comentario no cambia el Estado**: sólo escribe `System.History` (cerrar: §«Antes de cerrar una
  Tarea»).
- **Sin PHI, sin secretos, sin tokens**, y sin logs pegados: es el mismo cuidado que en la
  descripción del Merge Request, y el comentario queda en Azure para siempre.

## Pendientes a confirmar

Un **hueco o un gris** de una Tarea —un dato que falta, una decisión `⚠` que el Cerebro no
cerró, un caso que la lista de tests no cubre, un hallazgo de una auditoría que alguien pidió—
**no frena el desarrollo** y **no se vuelve a preguntar** en el momento. Se deja escrito en la
tarjeta, para que se resuelva más adelante y se vea al cerrarla (decisión de diseño del template).

| | |
|---|---|
| **Qué hace quien programa** | Lo que no depende del gris lo hace. Lo que depende de él **no lo inventa**: lo deja afuera, o toma el camino que la Tarea ya escribe, y lo anota como pendiente. Frena sólo si el gris impide **toda** la Tarea |
| **Dónde queda** | En la sección «Pendientes a confirmar» del **comentario de cierre** (molde de arriba), que ya pide su "sí" y no suma un turno. Si no hay comentario de cierre —el desarrollo se cortó, o el pendiente sale de una auditoría—, va en un comentario propio con el molde de abajo |
| **Qué lleva cada uno** | Qué es el gris · qué se hizo mientras tanto · qué hace falta para cerrarlo y quién lo define. Si ya tiene `P-nnn` en el Cerebro, se cita |

El molde del pendiente suelto: [moldes](references/moldes.md), al redactarlo.

Un pendiente que se resuelve se responde en otro comentario —*«Pendiente resuelto: ‹cuál›,
‹cómo›»*—: el original no se edita, así queda la traza.

### Antes de cerrar una Tarea: revisar los pendientes

Cuando se va a **cerrar** una Tarea —pasarla a *Resolved* o *Closed*, o al estado de revisión
al terminar un desarrollo—, **antes** se leen sus
comentarios (`get_work_item_comments`, lectura libre) y su Descripción, y se listan los
**pendientes que no tienen su «Pendiente resuelto»**:

- los de los comentarios «Pendientes a confirmar» y del comentario de cierre;
- de los sellos de auditoría, **sólo el más reciente** (uno posterior deja sin efecto al viejo);
- los `⚠` que siguen en «Datos a confirmar» de la Descripción.

La lista va **en el primer aviso** del cierre:

> *«Antes de cerrar la #NNNN: quedan 2 pendientes sin resolver en sus comentarios — ‹uno›,
> ‹otro›. ¿Querés cerrarla igual?»*

- **No frena el cierre**: lo decide la persona, pero con los pendientes a la vista.
- **El cierre sigue el GATE de edición destructiva de [[AGENTS]]** (con sus excepciones: `DEC-005`, y en modo
  solo un «sí» para cerrar la propia Tarea), y la lista de pendientes va en el primer aviso. Si la Tarea está **congelada**
  (en un sprint y ya tomada), la cierra una persona ([[cambios-en-el-backlog]] §4).
- **Sin pendientes**, se dice: *«No quedan pendientes en los comentarios.»*
- **Si no se pudieron leer los comentarios**, es **SIN DATOS**, y se dice: no es «no hay
  pendientes».
- Si no hubo ninguna auditoría y ningún pendiente, no pasa nada: el chequeo da vacío y se sigue.

## Formato: que se lea bien en Azure

Todo comentario va **en HTML** (Azure descarta los saltos y muestra el markdown literal), sin estilos inline;
**un marcador sin reemplazar no se postea**, y el sello de auditoría **no se reescribe**, sólo se formatea.
Etiquetas, marcadores, @menciones y el sello con su ejemplo, antes de mostrar todo comentario: [formato](references/formato.md).

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| [formato](references/formato.md) | Antes de mostrar todo comentario: HTML, marcadores, @menciones, sello |
| [moldes](references/moldes.md) | Al redactar un cambio propuesto (tarjeta congelada) o un pendiente suelto |
| [comentario-de-cierre](references/comentario-de-cierre.md) | Al redactar el comentario de cierre de desarrollo |
| [contexto](references/contexto.md) | Con tablero local; para el documento de apoyo de un tema |

---

### Ejemplo (genérico)
> "Dejá una nota en la #NNNN avisando que falta confirmar la versión." La skill
> redacta el comentario —`<p>Queda ⚠ pendiente confirmar la versión afectada antes de pasar
> a QA.</p>`—, lo muestra como se va a ver, y con tu OK lo postea en el Historial de la
> tarjeta. Sin datos reales de por medio.
