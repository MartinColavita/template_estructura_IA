# Parent y Related, desde la hija

Parte de la skill `cargar-a-azure`: se lee al escribir (paso 3) un alta que lleva Parent o Related.

**El Parent va en el alta, desde la hija**: `create_work_item` con `parentId`. Nunca se
edita la Historia para colgarle la Tarea: el MCP escribe sobre el ítem de origen, y así no se
escribe en una tarjeta que no es la que se está cargando. (No vence ningún sello: un vínculo
no es contenido.) Lo mismo con Related: desde la Tarea nueva, no desde una hermana que ya
tiene su sello. Detalle: [[sincronizar-backlog]] §5.
