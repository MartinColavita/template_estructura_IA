# Trazabilidad de cada nodo y registro de la traza

Parte de la skill `sincronizar-backlog`: se lee cuando se arman el tag, las relaciones y el documento fuente de cada nodo (paso 3), y cuando se registra la traza después del alta (paso 6).

## Enlazar, no copiar (regla de oro)

- **Enlazar, no copiar.** La traza doc↔ticket se guarda **por referencia** (ruta
  del doc + #ID de tickets), nunca duplicando el contenido de la ficha ni el del
  ticket. Así la memoria/historial NO crece con el tamaño de los documentos.

## 3. Adjuntar trazabilidad a cada nodo

A todos los tickets del árbol:

- **Un solo tag temático en CADA nodo, techo duro** (Épica, Feature, Historia **y**
  Tarea — **no solo la Épica**): el **mismo y único** tag temático sin prefijo,
  escrito siempre igual ([[organizacion-y-trazabilidad]] §1). **No** se agrega tag
  de slice ni de sub-flujo (el slice es la Épica), y **nunca** el nombre del
  producto/repo (ej. `<producto>`, `<repositorio>`) como tag adicional.
- **Relaciones** ([[organizacion-y-trazabilidad]] §2): jerárquicas
  Épica→Feature→Historia (Parent/Child) y **Related** entre tickets del mismo tema
  que se tocan. Los vínculos se **proponen** por título/tema; los `#ID` van `⚠`
  hasta materializarse.
- **Documento fuente**: la **ruta/URL de la ficha** (referencia, no contenido;
  [[organizacion-y-trazabilidad]] §3).

## 6. Registrar la traza (por referencia) — en la ficha y en el historial

Cerrado el alta:

- **En la ficha del Cerebro Digital:** completar el bloque **"Tickets derivados"**
  con los `#ID`/URL creados (solo los identificadores; nunca copiar el cuerpo de los
  tickets). Esto da la traza doc → tickets.
- **En el historial** ([[historial/INDICE]]): agregar **una fila por ticket** (o una
  por el lote) con tema, `#ID`, documento fuente (ruta de la ficha), resumen de una
  línea y puntos si aplica. Es un **log resumido e indexable**: **referencia, no
  contenido** (ni el cuerpo de la ficha ni el del ticket se copian). El `.md`
  detallado se crea **solo** si el ticket se promueve a `gold`.
