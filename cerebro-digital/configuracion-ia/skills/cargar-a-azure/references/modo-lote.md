# Confirmación en modo lote

Parte de la skill `cargar-a-azure`: se lee cuando la carga corre dentro de un lote de [[planificar-lote]].

**En modo lote** ([[planificar-lote]]) el preview de cada ítem es su fila en la tabla del
cierre más su archivo, y el "sí" del cierre vale por esta confirmación para cada ítem de la
tabla. El Bloque de GATES y el checklist de §2b se llenan igual, por ítem, y quedan en el
archivo del lote: se muestran en la tabla como una columna (OK o lo que falló).
