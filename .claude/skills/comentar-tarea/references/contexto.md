# Tablero local y contexto adicional

Parte de la skill `comentar-tarea`: se lee cuando el proyecto usa el tablero local (`DEC-006`) o hace falta el documento de apoyo de un tema (MCP, etiquetas HTML, tarjeta congelada, drift).

## Tablero local

> **Tablero local (`DEC-006`):** si el proyecto usa el tablero local, «el board» es `cerebro-digital/<modulo>/backlog/`
> y se opera con `bin/tablero-local.py`, con los mismos GATEs y sin MCP (detalle: `backlog/README.md` del módulo).
> Con Azure DevOps, Jira u otro tablero, las operaciones se traducen con la tabla de `integracion-azure-mcp/00-index.md`.

## Contexto adicional
- Herramientas MCP y flujo de escritura con confirmación: [[integracion-azure-mcp/04-automatizar-con-ia]] · [[integracion-azure-mcp/00-index]].
- Etiquetas HTML que acepta Azure, con los esqueletos de la Descripción: [[checklists/mapa-campos-azure]].
- **Tarjeta congelada** (en un sprint y ya tomada): [[cambios-en-el-backlog]] §4.
- **Pendientes a confirmar** y su revisión antes de cerrar: §«Pendientes a confirmar», arriba.
- **Aviso de cambios (drift):** el protocolo de [[cambios-en-el-backlog]] usa esta skill para el comentario con @mención cuando un doc cambió y hay que avisar a quien trabaja la tarjeta (el acuse: [[cambios-en-el-backlog]] §2).
