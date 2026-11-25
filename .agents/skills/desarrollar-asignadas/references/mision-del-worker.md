# Misión que recibe cada worker

Parte de la skill `desarrollar-asignadas`: se lee en el paso 6.1, antes de despachar un worker.

**La arma `bin/armar-mision.py`** (`--rol worker --entorno orca --motor <claude|gemini>`), la
misma plantilla que usa `references/sin-orca.md`: la Tarea **completa** pegada (el orquestador
la lee del tablero y la guarda en un `.md` fuera de los repos, con el Gherkin de la Historia
padre), el worktree y el SHA de base, `AGENTS.md`, el método (`tdd-ciclo-y-evidencia.md`,
`crear-endpoint.md`, `contrato-openapi.md`, la guía del stack), las skills por ruta absoluta
(`guiar-tdd` y, en back, `armar-swagger`; **no** `auditar-codigo`, que es del verificador), la
arquitectura (`esqueleto-proyectos.md`, `decisiones.md`, `aplicacion/`), las convenciones C1 a
C8 **copiadas del orquestador**, los límites (un módulo, sin PHI, sin push ni Merge Request ni
tablero ni Cerebro; lo gris va como pendiente a confirmar, no se inventa), el modo de pruebas de
la Tarea, el resultado esperado y el canal (Claude: `ask` y `worker_done`; Gemini: una línea
`PREGUNTA-ORQUESTADOR: …` y `TAREA-TERMINADA` / `TAREA-FALLIDA`). Todo en español. El texto de
la misión **no vive acá**: si hay que cambiarlo, se cambia el script y su prueba. La rama se
crea con la convención real (`metodologia/convenciones-git.md`): `task/<ID>-<slug>`,
`bugfix/<ID>-<slug>`, `hotfix/<ID>-<slug>`, antes del primer commit. **No se exige ni se corre
[[auditar-tarea]]**: es opcional y sólo corre si alguien la pide.
