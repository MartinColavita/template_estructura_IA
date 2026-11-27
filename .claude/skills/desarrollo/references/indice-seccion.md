# Índice de la sección desarrollo

Lo genera `python -I bin/puerta-skills.py --generar` con la primera oración de cada descripción: no se edita a mano.

- `automatizar-e2e`: El rol de QA automatización: escribir y mantener las pruebas de punta a punta de una Historia con el motor que DEC-003 fija según el tipo de aplicación: Playwright para web y Electron (y para el front de una app de escritorio con webview, probado en navegador), WebDriver para Tauri o escritorio...
- `desarrollar-asignadas`: Revisar el tablero (Azure DevOps por MCP, o el tablero local de archivos según DEC-006), tomar las Tareas asignadas sin dependencias pendientes y desarrollarlas en paralelo: un worktree y un worker por tarjeta, con la misión única de armar-mision.py.
- `disenar-pruebas`: El rol de tester: a partir de una Historia con su Gherkin, armar el plan de pruebas de aceptación: qué Escenarios se automatizan de punta a punta y cuáles quedan exploratorios, los bordes y los datos de prueba (sin datos de personas), el ambiente y el estado inicial, y una lista para recorrer a mano...
