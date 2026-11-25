# El orquestador queda atento

Parte de la skill `desarrollar-asignadas`: se lee en el paso 6.0, apenas sale la tanda: cómo se espera y qué se hace con cada mensaje.

- **La espera está siempre corriendo**, en segundo plano: `orca
  orchestration check --wait --types "worker_done,escalation,question"
  --timeout-ms 900000 --json` para los workers de Claude, y la lectura de
  la terminal para los de Gemini. En Claude Code van como comandos en
  segundo plano, que despiertan al orquestador y siguen corriendo aunque
  esté esperando al humano.
- **Cada mensaje se procesa al llegar**, se confirma (`check --ack
  <delivery_id> --wait …`) y se vuelve a esperar. Orca repite el mismo
  mensaje hasta el `--ack`, así que ninguno queda sin confirmar mientras
  se espera al humano: se anota y se sigue escuchando.
  - **Pregunta de un worker:** si es técnica y tiene una recomendación
    clara (un nombre interno, un mecanismo del framework, dónde va un
    archivo), la contesta el orquestador (`orca orchestration reply --id
    <message_id> --body "<respuesta>" --json`, o `terminal send` si es
    Gemini) y se la lista al humano para que la vete (fuente 5 de
    [[redaccion-de-tickets]]). Si es un dato duro o una regla de negocio sin fuente,
    se le trae al humano **en ese momento** y su respuesta vuelve
    después. Ningún worker queda más de unos minutos sin respuesta sin
    que el humano lo sepa.
  - **Escalamiento o bloqueo:** se le avisa al humano en ese momento.
  - **Terminó una Tarea** (`worker_done` o `TAREA-TERMINADA`): **se le
    avisa al humano en ese momento** —*«Terminó la #NNNN: ‹resumen›.
    Arranco la verificación con ‹el verificador›.»*— y se sigue con el
    6.2. El worker de Claude se libera antes del `--ack` (`orca
    orchestration worker-release --dispatch <dispatch_id> --json`), y la
    pestaña de Gemini se cierra (`orca terminal close --terminal
    <identificador> --json`): el trabajo queda en el worktree.
  - **Falló** (`--outcome failed` o `TAREA-FALLIDA`): se avisa con lo
    que dijo el worker, no va a la verificación, el worktree queda
    intacto para que decida el humano, y se da el resumen del 6.3.
- **No se da por terminado** mientras quede una Tarea abierta: `worker-list
  --run <run_id> --json` sin filas `active`, `reclaimable` ni `retained`,
  ninguna pestaña de Gemini del lote abierta (`orca terminal list`), y
  cada Tarea con su resultado dicho al humano.
