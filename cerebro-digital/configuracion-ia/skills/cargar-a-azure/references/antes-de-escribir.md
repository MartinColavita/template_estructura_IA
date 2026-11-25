# Precondiciones, alta o edición y contexto

Parte de la skill `cargar-a-azure`: se lee antes de intentar la carga (MCP y PAT), al decidir si es alta o edición (paso 1), y cuando hace falta el setup o el mapa de campos.

## Tablero local

> **Tablero local (`DEC-006`):** si el proyecto usa el tablero local, «el board» es `cerebro-digital/<modulo>/backlog/`
> y se opera con `bin/tablero-local.py`, con los mismos GATEs y sin MCP (detalle: `backlog/README.md` del módulo).
> Con Azure DevOps, Jira u otro tablero, las operaciones se traducen con la tabla de `integracion-azure-mcp/00-index.md`.

## Precondiciones (verificar antes de intentar)

1. **MCP configurado.** Servidor `@tiberriver256/mcp-server-azure-devops` vía
   `npx -y`, con las env vars cargadas. Detalle y setup: [[integracion-azure-mcp/00-index]].
2. **PAT con scope de ESCRITURA.** Alta/edición requiere **Work Items (Read & Write)**.
   El PAT lo crea **cada usuario el suyo** (auditoría por persona), con caducidad y
   mínimo scope, y vive como **env var** (`AZDO_PAT`) — **nunca** en un `.md` que la
   IA lea ni pegado en el chat.
3. Si falta el MCP o el PAT es de solo lectura → **no se escribe**: se entrega el
   texto pegable y se le dice al usuario que lo cargue a mano (copiá y pegá). Arriba de
   todo va el aviso *«No busqué duplicados: buscalos vos en el tablero antes de pegar.»*,
   y en el Bloque de GATES la dedup y la tarjeta congelada dicen **SIN DATOS**, nunca OK.

## Paso 1: alta o edición

Determinar si es **alta** (nuevo) o **edición** (existe `#ID`):
- Alta → `create_work_item` (proyecto, tipo, título, campos).
- Edición → `update_work_item` (ID + campos a cambiar). Antes de editar, leer el
  estado actual con `get_work_item` para armar el diff real y no pisar datos.
  **Si está en un sprint y ya tomada, está congelada (en modo equipo): no se edita.** Se frena, se avisa en
  criollo y se ofrece dejar el DIFF como comentario ([[cambios-en-el-backlog]] §4).

## Contexto adicional

- Setup del MCP y el PAT: [[integracion-azure-mcp/00-index]]
- Mapa de campos del board (qué campo del ticket va a qué campo de Azure):
  [[checklists/mapa-campos-azure]]
- Redacción previa del ticket: [[redactar-tarea]]
