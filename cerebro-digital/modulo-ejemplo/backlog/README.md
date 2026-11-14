# backlog — el tablero local (cuando el proyecto no usa Azure DevOps)

Acá viven los work items cuando `DEC-006` fija el **tablero local**: un archivo por ítem, con
frontmatter (`id`, `tipo`, `estado`, `titulo`, `padre`, `etiqueta`, `asignado`, `iteracion`,
`relaciones`) y un `#ID` secuencial. Los crea y los mueve `bin/tablero-local.py`; nadie los edita a
mano salvo para corregir texto.

```bash
python bin/tablero-local.py crear --tipo Historia --titulo "Crear una reserva" --padre 2 --etiqueta reservas
python bin/tablero-local.py listar --estado New
python bin/tablero-local.py tomar 3 --quien martin
python bin/tablero-local.py comentar 3 --texto "Cierre: rama task/3-crear-reserva, MR !7"
python bin/tablero-local.py estado 3 Closed --confirmado
python bin/tablero-local.py buscar "reserva" --abiertos        # deduplicación por objetivo
```

Las skills del pipeline (`redactar-tarea`, `cargar-a-azure`, `tomar-tarea`, `comentar-tarea`,
`consultar-backlog`, `sincronizar-backlog`, `planificar-lote`, `desarrollar-asignadas`) aplican acá
**los mismos GATEs** que con Azure: tablero autorizado (esta carpeta), deduplicación con `buscar`,
confirmación antes de escribir, borrado con dos «sí» (`--confirmado`) y, en modo equipo, nivel y tarjeta congelada
([[tablero-autorizado]]). El
script sólo ejecuta lo que la skill ya confirmó. Las plantillas de cada tipo son las de
`tablero/plantillas/` (el cuerpo del archivo es el mismo texto que iría al campo
Descripción).

Nace vacío. Si el proyecto pasa a Azure DevOps o a otro tablero, cada archivo se carga con
`cargar-a-azure` y acá queda el histórico.
