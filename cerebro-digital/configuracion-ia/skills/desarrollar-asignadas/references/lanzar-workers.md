# Lanzar workers

Parte de la skill `desarrollar-asignadas`: se lee en el paso 0, para elegir el modo, y en el paso 6, antes de despachar cada worker.

## Elegir el modo (paso 0)

Un solo flujo, dos formas de lanzar los workers. Orca define en cada sesión que abre la
variable de entorno `ORCA_APP_VERSION`; fuera de Orca no existe. Lo primero es mirarla:

```
echo "${ORCA_APP_VERSION:-}"      # Bash
$env:ORCA_APP_VERSION             # PowerShell
```

- **Vacía → modo sin Orca** (`references/sin-orca.md`): los mismos pasos, con worktrees de
  git y `claude -p` / `gemini -p` en segundo plano. No se intenta abrir Orca ni "simularlo".
- **Con valor → modo Orca**, y en el plan del paso 4 se informa la versión de Orca.

## Modo sin Orca (IntelliJ o terminal) y tablero local

Sin la variable `ORCA_APP_VERSION` el flujo es **el mismo** con otro lanzador: los worktrees se abren con `git
worktree add` después del `bin/gate-worktree.py`; cada worker se lanza con `claude -p "Leé y seguí la misión de
<archivo>" --add-dir <núcleo>` (o `gemini -p … --include-directories`) parado en su worktree, y se reanuda con
`--resume`; el verificador igual, en sólo lectura (Claude: `claude -p` con `--disallowedTools "Edit" "Write"
"NotebookEdit"`; Gemini:
`--approval-mode plan --policy bin/gemini-verificador-solo-lectura.toml`). Los diffs se miran en el IDE. Lo
operativo, paso a paso, y las decisiones abiertas de ese modo están en `references/sin-orca.md`.

El tablero local (`DEC-006`) está en `relevar-y-dependencias.md`.

## En Orca

- `orca status --json` y `orca orchestration run-create --objective
  "<lote>" --json` → `run_id` para todo el lote.
- Por cada Tarea se anota el **SHA de la base** (`git -C <repo>
  rev-parse <base confirmada>`): lo que se verifica son los commits
  `<sha-base>..<rama>`.
- **Si programa Claude** (worker supervisado de Orca):
  - `orca orchestration task-create --spec "<la misión del punto 6.1>"
    --task-title "#<ID> <título>" --run <run_id> --json` → `task_id`.
  - `orca orchestration worker-start --task <task_id> --worktree
    new-top-level --repo id:<id del repo, del paso 3.1> --name
    <ID>-<slug> --base-branch <base confirmada> --agent claude --run
    <run_id> --json`. Crea el worktree, abre la ventana y deja al worker
    **supervisado**: su aviso de terminado le llega al orquestador.
  - **Se confirma que arrancó:** `orca orchestration worker-read
    --dispatch <dispatch_id> --source auto --json`. Si la misión quedó
    cargada sin enviarse, se avisa y se sigue la referencia `recovery-and-cleanup` de la skill `orchestration` de Orca
    (`orca skills get orchestration`).
  - Si `worker-start` sale distinto de 0, **no se relanza**: se lee el
    recibo (`failedStage`, `residualResources`) y la misma receta.
- **Si programa Gemini** (Orca no lo lanza como worker supervisado):
  - `orca worktree create --repo id:<id> --name <ID>-<slug>
    --base-branch <base confirmada> --no-parent --json` (Orca abre además
    una terminal vacía: se cierra con `orca terminal close`), y en ese worktree una
    pestaña a la vista: `orca terminal create --worktree path:<ruta>
    --title "Programa Gemini #<ID>" --command "gemini -i 'Leé y seguí la
    misión de <archivo de misión>' --approval-mode
    <el del plan> --include-directories <ruta del repositorio del Cerebro>,<carpeta
    de la misión>" --json`. La misión (la del 6.1) va en un archivo fuera
    de los repos.
  - El orquestador lo sigue **leyendo esa terminal**, no por el inbox:
    `orca terminal wait --terminal <identificador> --for tui-idle
    --timeout-ms 60000 --json` y `orca terminal read --terminal
    <identificador> --json`, en segundo plano. La misión le pide cerrar
    con una línea `TAREA-TERMINADA` (o `TAREA-FALLIDA`) y su resumen, y
    escribir `PREGUNTA-ORQUESTADOR: …` cuando tiene una duda bloqueante;
    el orquestador la contesta con `orca terminal send --terminal
    <identificador> --text "<respuesta>" --enter --json`. Los marcadores
    se buscan **al principio de una línea**, y ante la duda se confirman
    con `orca terminal read --screen` (la consola sale en pedazos y la
    misión misma los menciona).
  - **Si la pestaña espera una aprobación** (con `auto_edit`, Gemini pide
    permiso en la pestaña para cada comando: commits, tests), el
    orquestador lo ve con `orca terminal read --screen` y **le avisa al
    humano en ese momento**, con la Tarea y el comando: la aprobación la
    da el humano en la pestaña, no el orquestador.
