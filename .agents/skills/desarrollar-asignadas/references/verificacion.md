# Verificación: cómo se lanza y se lee

Parte de la skill `desarrollar-asignadas`: se lee en el paso 6.2, cuando termina una Tarea.

- **Si programó Claude, verifica Gemini, en una pestaña de Orca** sobre
  el worktree de la Tarea: `orca terminal create --worktree
  path:<ruta> --title "Verifica Gemini #<ID>" --command "gemini -i 'Leé
  y seguí la misión de <archivo de misión>' --approval-mode plan --policy <ruta del repositorio del Cerebro>/bin/gemini-verificador-solo-lectura.toml
  --include-directories <ruta del repositorio del Cerebro>,<carpeta de la
  misión>" --json`. Comillas simples adentro: las dobles escapadas rompen
  el comando en PowerShell.
  - **La política es obligatoria.** El modo `plan` solo no alcanza: sin
    interacción pasa a modo automático, en la pestaña cualquiera puede
    cambiar de modo, y deja escribir `.md` sueltos. La política prohíbe
    cambiar de modo, escribir, guardar memoria, usar servidores MCP,
    encadenar comandos y publicar, y deja sólo git de lectura, los tests
    y Spectral. Si la pestaña dice `Policy file error`, Gemini corrió
    **sin** ella: se cierra y el veredicto es SIN DATOS.
  - El orquestador lee el veredicto con `orca terminal wait` y `orca
    terminal read` (siguiendo el `nextCursor`), hasta el bloque
    `VEREDICTO-INICIO` … `VEREDICTO-FIN`, con techo de 20 minutos: si no
    aparece, es SIN DATOS y se avisa. Al leer el veredicto, la pestaña se
    cierra (`orca terminal close`), siempre antes de la entrega.
- **Si programó Gemini, verifica Claude**, como sub-agente de **sólo
  lectura** del orquestador (sin herramientas de edición ni escritura),
  con la misión del verificador y la ruta del worktree. No escribe, no
  commitea, no corre nada que modifique y no escribe por MCP. No se ve en
  una pestaña: el control es la foto de abajo.
- **La misión del verificador** la arma `bin/armar-mision.py` (`--rol verificador --entorno orca
  --motor <el otro>`): la Tarea completa con el Gherkin del padre (el verificador no lee el
  tablero), el worktree, la rama y el SHA de base, las skills por ruta absoluta (`verificar-tdd`,
  `code-review.md`, `auditar-codigo`), los comandos exactos de `verificar-tdd.py` (con el `--modo`
  de la Tarea) y `auditar-diff.py`, el control 5-quater con C1 a C8 (un veredicto por regla), el
  linter de OpenAPI con `bin/spectral-oas.yaml`, las dos clases de `SIN DATOS` y el bloque
  `VEREDICTO-INICIO … FIN`. Si el front no tiene dependencias instaladas, el **verificador** corre
  el comando de instalación del stack en su worktree antes de verificar (el orquestador coordina,
  no ejecuta).
- **Cómo se sabe quién verificó:** la pestaña muestra `Gemini CLI
  v<versión>` y el modo `plan`; el comentario de cierre y el resumen lo
  registran como «‹motor› v‹versión› · ‹modelo›».
