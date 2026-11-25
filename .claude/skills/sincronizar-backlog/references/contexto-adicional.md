# Contexto adicional

Parte de la skill `sincronizar-backlog`: se lee cuando el proyecto usa el tablero local (`DEC-006`), o cuando hace falta el documento de apoyo de un tema (mapeo, drift, cobertura, setup del MCP) o la skill vecina.

## Tablero local

> **Tablero local (`DEC-006`):** si el proyecto usa el tablero local, «el board» es `cerebro-digital/<modulo>/backlog/`
> y se opera con `bin/tablero-local.py`, con los mismos GATEs y sin MCP (detalle: `backlog/README.md` del módulo).
> Con Azure DevOps, Jira u otro tablero, las operaciones se traducen con la tabla de `integracion-azure-mcp/00-index.md`.
> La bajada 1:1 del árbol la hace `bin/derivar-a-tablero-local.py <ficha>` (idempotente; sin Tareas); esta skill
> redacta cada nodo después, con `redactar-tarea`.

## Contexto adicional

- Mapeo, tags, relaciones y documento fuente: [[organizacion-y-trazabilidad]]
- Actualizar tarjetas desfasadas y avisar al equipo (drift): [[cambios-en-el-backlog]]
- Auditar cobertura y detectar desfases (solo lectura): [[consultar-backlog]]
- Chequear la consistencia del set de Tareas antes de cerrar: [[analizar-tareas]]
- Setup MCP / PAT / seguridad: [[integracion-azure-mcp/00-index]]
- Paso previo (dejar la ficha lista): el Cerebro (`cerebro-digital/`)
- Redacción/escritura de un ticket suelto: [[redactar-tarea]] · [[cargar-a-azure]]
- Aprendizaje del toolkit: [[historial/README]]
