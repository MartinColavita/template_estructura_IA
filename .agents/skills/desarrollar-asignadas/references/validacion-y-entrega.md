# Validación y entrega: Ajustar y Aprobar

Parte de la skill `desarrollar-asignadas`: se lee en el paso 6.3, cuando el humano responde «Ajustar» o «Aprobar» (o lo fija `DEC-005`), y al armar la pregunta del punto 1.

## Lo que lleva la pregunta del punto 1

- el resumen del worker y la verificación (HALLAZGO y SIN DATOS: el
  humano los manda a ajustar o los acepta), y qué cambió del README;
- los **pendientes a confirmar** de este desarrollo y los que ya había
  sin resolver en la tarjeta ([[comentar-tarea]] §«Antes de cerrar una
  Tarea»);
- lo que va a pasar con el "Aprobar": subir el respaldo `evidencia/<ID>`
  a `origin`, reorganizar la rama **por importancia** (alrededor de 10
  commits, como guía), pushear la rama de la Tarea, y **el comentario de cierre tal como se va a ver**, con el link
  para abrir el Merge Request. Lo único que se completa después, y la
  pregunta lo dice, es el último commit y la cantidad de commits, que
  recién existen al reorganizar.

## Ajustar y Aprobar

2. **Ajustar:** una Tarea nueva para un worker nuevo, del mismo motor y
   **en el mismo worktree**, con lo que hay que cambiar (Claude:
   `task-create` + `worker-start --task <nuevo> --worktree path:<ruta>
   --agent claude --run <run_id> --json`; Gemini: se cierra la pestaña
   anterior, si quedó abierta, y se abre otra con la misión de ajuste).
   Antes de despachar rige la «Base al día» del paso 6, aunque el
   worktree ya exista. Vuelve a pasar por 6.2 y por esta pregunta.
3. **Aprobar:** el orquestador hace, sin volver a preguntar:
   - la reorganización de la rama ([[orquestador-desarrollo]]
     §«Commits: de trabajo, y pocos en el Merge Request»): respaldo
     `evidencia/<ID>` subido a `origin`, commits por importancia (alrededor
     de 10), `git diff evidencia/<ID> HEAD` vacío;
   - el push de la rama de la Tarea;
   - el comentario de cierre en la tarjeta ([[comentar-tarea]]
     §«Comentario de cierre de desarrollo»), sólo el comentario (`System.History`
     en Azure; `bin/tablero-local.py comentar` en el tablero local), con
     el guard de [[tablero-autorizado]];
   - el link para abrir el Merge Request (antes, la «Base al día» del
     paso 6: si `develop` avanzó, se trae con merge y se re-verifica), que **abre el humano** (la IA no
     abre Merge Requests por cuenta propia: muestra el link):
     `https://<host-gitlab>/<grupo>/<proyecto>/-/merge_requests/new?merge_request%5Bsource_branch%5D=<rama>&merge_request%5Btarget_branch%5D=<base>`
     (`<grupo>/<proyecto>` sale de `git remote get-url origin`), con el
     título `feat: [AB#<ID>] <título en español>` y la descripción lista
     para pegar.
4. **El Estado no se cambia**, salvo lo que fije `DEC-005` confirmada («Estado de la tarjeta al
   cerrar»), después del comentario de cierre. Lo demás lo decide una persona; una tarjeta
   congelada sólo se comenta ([[cambios-en-el-backlog]] §4).
5. **Resumen al humano, siempre**, al terminar cada Tarea —entregada,
   frenada o fallida—, con el molde de [[orquestador-desarrollo]]
   §«Resumen al terminar cada Tarea». Al terminar el lote, la tabla con
   todas.
