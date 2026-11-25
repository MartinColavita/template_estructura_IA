# Cuándo se usa planificar-lote

Parte de la skill `planificar-lote`: se lee antes de arrancar, si no está claro que el pedido es de esta skill.

## Cuándo se usa y cuándo no

| Pedido | Skill |
|---|---|
| Las Tareas de **una o más** Historias ("armá las tareas de F-04 a F-08") | **esta** |
| Las Historias de una ficha, con o sin sus Tareas | **esta**, con la cardinalidad 1:1 de [[sincronizar-backlog]] |
| **Un** ítem suelto | [[redactar-tarea]] + [[cargar-a-azure]] |
| La ficha no tiene el bloque `## Derivación a backlog` cerrado | No se deriva: va a curación ([[cognitive-doc-design]]) |
| Corregir una tarjeta congelada | [[comentar-tarea]] (sólo comentario) |
