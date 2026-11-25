# Relevar y armar el grafo de dependencias

Parte de la skill `desarrollar-asignadas`: se lee en los pasos 1 y 2, al traer las tarjetas del tablero.

## Prerrequisito

Lo fija `DEC-006`. Con **tablero local** no hace falta nada: `bin/tablero-local.py` lee y
escribe los archivos del módulo. Con **Azure DevOps, Jira u otro tablero por MCP**, el MCP tiene
que estar conectado (`/mcp` lo muestra activo); si no lo está, avisar y derivar a
`cerebro-digital/configuracion-ia/integracion-azure-mcp/00-index.md` en vez de intentar leer el board.

**Tablero local (`DEC-006`).** Si el proyecto usa el tablero local, «el tablero» es `cerebro-digital/<modulo>/backlog/`
y se opera con `bin/tablero-local.py`, mismos GATEs, sin MCP (detalle: `backlog/README.md` del módulo).

## Pasos 1 y 2

1. **Relevar.** Con tablero local: `bin/tablero-local.py listar --asignado <yo> --json` y se
   descartan los estados terminales. Con Azure: `search_work_items` / `list_work_items` filtrando por el
   tablero autorizado ([[tablero-autorizado]]: org `{{AZURE_ORG}}`, proyecto
   `{{AZURE_PROYECTO}}`, team `{{AZURE_TEAM}}`) +
   `AssignedTo = @Me` + estado no terminal (no `Done`/`Closed`/`Removed`).

2. **Armar el grafo de dependencias.** Por cada tarjeta traída: `get_work_item`
   (relaciones *Related*) + leer en la descripción el campo/texto donde se
   declaran dependencias explícitas ("depende de #NNNN"). Clasificar cada
   una en:
   - **Libre**: sin dependencia pendiente dentro del lote relevado.
   - **Bloqueada**: depende de otra tarjeta del mismo lote que todavía no
     está validada/cerrada. Registrar de qué `#ID` depende.
