# Parent y Related, desde la hija

Parte de la skill `sincronizar-backlog`: se lee en el paso 5, al materializar los vínculos del árbol.

- `manage_work_item_link` para materializar Parent/Child y Related. **El Parent se crea
  siempre desde la hija**: `create_work_item` con `parentId`, o `manage_work_item_link` con
  la hija como origen y tipo Parent. **Nunca se edita el padre para colgarle un hijo.** No
  es por el sello —un vínculo no es contenido y no vence ninguno—: es porque el MCP escribe
  sobre el ítem de origen, y así no se escribe en una tarjeta que no es la que se está
  cargando. Lo mismo con
  Related entre Tareas: desde la nueva, no desde la que ya está sellada.
- Resolver los #ID de relaciones con `search_work_items` / `list_work_items` cuando
  haga falta.
