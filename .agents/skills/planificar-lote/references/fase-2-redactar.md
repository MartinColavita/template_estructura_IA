# Fase 2: redactar

Parte de la skill `planificar-lote`: se lee en la fase 2, al lanzar a los agentes redactores.

- **Misión de cada agente:** es la que imprime `python bin/lote.py mision <carpeta> redactar <clave>`, y no se escribe a mano. El molde (`misiones/redactar.md`) ya trae el objetivo y las rutas (`CONTEXTO.md`, ficha, maqueta, Historia padre). También trae las skills, que no se heredan y hay que pasarlas; la lista la fija `SKILLS_DE` de `bin/lote.py` (la skill [[redactar-tarea]] con sus referencias, el método, la plantilla, el mapa de campos y la estimación); se mira ahí, no se copia acá.
- **Salida** en la carpeta del lote: `<clave>.html` (Descripción) y, si es Historia, `<clave>-criterios.html`; más `<clave>.json` con título, tipo, padre, puntos, actividad y relaciones.
- Lo que todavía no existe se referencia con **`[T-nn]`** o **`[H-nn]`**: en la fase 5 se reemplaza por el `#ID`.
- Las Tareas siguen el tamaño de [[plantillas/tarea]] §«Tamaño y forma»: **30 tests o menos** (si no alcanza, se parte la Tarea), **una línea por test**, sin repetir texto entre secciones.
- **Si el lote también redacta o pisa la Historia**, sus Tareas se redactan **después** del borrador de la Historia (y, si se pidió auditoría, después de que [[auditar-historia]] corrió sobre él y se aplicaron sus F): las Tareas mapean sus Escenarios.
- **El chequeo de forma §2b** de [[cargar-a-azure]] lo corre la sesión que coordina el lote cuando vuelve cada redactor, sobre su borrador (`python bin/auditar-tarea.py` para una Tarea), y anota el resultado con `lote.py item <carpeta> --clave <clave> --gates "OK"`, `--gates "FRENA: <cuál>"`; `--gates "no aplica"`, sólo en una fila que no escribe contenido (RELACIÓN, EXISTE). El redactor no lo corre: su misión (`misiones/redactar.md`) no se lo pide y no puede tocar `items.json`. No es la auditoría opcional: es el chequeo de forma de lo que se va a escribir, y sin él la columna «GATES y §2b» sale SIN DATOS.
- **Si la herramienta no tiene sub-agentes**, las fases 2 y 3 corren en serie, y cada auditoría con contexto propio, sin el de la redacción. Los F los corrige quien redactó o, si ya no está, otro agente que no auditó esa pieza.
