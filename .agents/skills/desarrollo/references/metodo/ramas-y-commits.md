# Ramas, commits y espacios de trabajo

> Prioridad **MEDIA-ALTA**. Complementa el **GATE de WORKTREE** de `AGENTS.md`, que manda.
> Adaptado de `git-workflow` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## Lo que ya está mandado y no se toca

El **GATE de WORKTREE** de `AGENTS.md` es duro y está por encima de todo lo de acá:

- **De qué rama sale se PREGUNTA.** Nunca se infiere, nunca se inventa.
- **Techo de espacios de trabajo por máquina** (el del GATE de WORKTREE de `AGENTS.md`). Al llegar, se frena.
- **Con el árbol sucio, se frena** y se muestra qué hay.
- **Dos Tareas que tocan el mismo archivo se serializan** (⚠ regla candidata, a confirmar por el equipo; así está en `AGENTS.md`).
- **Borrar un espacio con trabajo sin pushear NO lo hace la IA nunca.**

> **Por qué es duro:** salir de la rama equivocada **no falla**. El código se escribe, los
> tests pasan, el Merge Request se abre — y recién ahí aparece que la base era vieja y el diff
> arrastra trabajo ajeno. Es el error más caro, porque no avisa en el momento.

## Una rama por Tarea

El nombre lleva el `#ID`, porque es lo que permite reconstruir la cadena después:

```
task/12345-titulo-corto      Tarea técnica de una Historia
bugfix/12346-titulo-corto    arreglo de un defecto durante el sprint
hotfix/12347-titulo-corto    arreglo crítico en producción
```

Son los prefijos de `metodologia/convenciones-git.md` del Cerebro — o la convención que
fije esa ficha en el nuevo proyecto. Sin `#ID` en la rama, seis meses después nadie puede
contestar por qué existió ese cambio.

## Commits

**Uno por idea, no uno por día.** El mensaje explica **por qué**, no qué — el qué ya está en
el diff:

```
MAL:   "cambios"  ·  "fix"  ·  "avance del día"
MAL:   "agrego validación de fecha"          <- eso lo dice el diff
BIEN:  "rechazar solicitudes con fecha pasada, que entraban por la API (#12345)"
```

Y tres reglas del proyecto que valen acá:

| Regla | |
|---|---|
| **Sólo tu autoría** | Sin `Co-Authored-By`, sin "Generated with" |
| **UTF-8** | El mensaje va por archivo o por heredoc, **nunca** por here-string de PowerShell |
| **Refactor y funcionalidad, separados** | Un commit que mezcla las dos no se puede revisar |
| **Commits agrupados por importancia en el Merge Request** | Uno por cambio lógico; alrededor de 10 por Tarea es una guía, no un techo (pueden ser 15; se evita llegar a 20 o 30 commits chicos). Los commits chicos de TDD son de trabajo, no van al Merge Request, y se reorganizan antes del push con el respaldo `evidencia/<ID>`, que se sube a `origin` sin Merge Request; la rama de la Tarea se mergea sin squash, y ninguna de las dos se borra hasta terminar el sprint (`orquestador-desarrollo.md` §«Commits: de trabajo, y pocos en el Merge Request») |

## Qué NO se commitea

- **Secretos.** Y si se filtró uno, **no alcanza con borrarlo: hay que rotarlo.** Queda en el
  historial para siempre y el historial se clona entero.
- **PHI real**, en ningún archivo, ni en el mensaje del commit.
- **Código comentado** "por las dudas". Para eso está el historial.
- **Lo que genera el build.**

El hook `pre-commit` ya frena algunas cosas: espejos desincronizados, BOM y caracteres de
control invisibles. **No frena secretos ni PHI** — eso lo tiene que mirar quien commitea.

## El pull request

Un Merge Request por Tarea **y por repositorio**. Como el back y los repositorios de front del
proyecto son repositorios separados, una funcionalidad completa son **varios** Merge Requests
—uno por repositorio que toca—, y cada uno dice que los otros existen.

Todo lo demás —tamaño máximo, qué lleva la descripción, checklist, quién revisa— está en
[merge-request.md](merge-request.md).

## Antes de pushear

- [ ] La suite **completa** en verde, no sólo lo nuevo.
- [ ] Sin secretos, sin PHI, sin código comentado.
- [ ] Los commits cuentan una historia legible: **por importancia**, uno por cambio lógico
  (alrededor de 10 por Tarea, como guía). Los de trabajo (`test(rojo)`, «wip») se reorganizan
  antes, con el respaldo `evidencia/<ID>` subido a `origin` y `git diff evidencia/<ID> HEAD`
  vacío.
- [ ] Al día con la rama base, para que el Merge Request muestre **tu** diff y no el de otros.

## Recordatorio del entorno

Si el remoto es interno, **el push necesita la red o la VPN de la organización conectada.**
Si falla, casi siempre es eso antes que un problema de permisos.
