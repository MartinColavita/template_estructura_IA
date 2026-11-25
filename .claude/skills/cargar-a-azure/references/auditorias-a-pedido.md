# Auditorías a pedido

Parte de la skill `cargar-a-azure`: se lee cuando alguien pide la auditoría de la Tarea o de su Historia, o [[analizar-tareas]] sobre el conjunto.

### 3b. Segundo chequeo: opcional, a pedido

El checklist de §2b es un **autochequeo del mismo agente que la escribió**, de forma. El
segundo chequeo de fondo —[[auditar-tarea]] sobre la Tarea, [[auditar-historia]] sobre su
Historia padre— **no se encadena solo** (decisión de diseño del template): corre sólo si alguien lo
pide. Encadenarlo gastaba muchos tokens y volvía a preguntar cosas ya cerradas o que no hacían
falta para arrancar.

Al reportar el alta se ofrece en una línea, sin esperar respuesta: *«Si querés, corro la
auditoría de la #NNNN.»* Si se pide, la corre **otro agente**, y lo que encuentre queda **como
pendiente a confirmar** en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar»): no frena
el desarrollo.

**En modo lote** ([[planificar-lote]]), si se pidió la auditoría, corre sobre el borrador. Al
crear la tarjeta se verifica que su texto sea igual al archivo auditado (comparando el texto
sin etiquetas y con los espacios normalizados, con los `[T-nn]` ya reemplazados por su `#ID`):
si es igual, se publica el sello con la revisión que quedó; si no, la tarjeta queda **sin
sello**, y eso no frena nada.

## analizar-tareas sobre el conjunto

- **[[analizar-tareas]] sobre el conjunto: sólo si se pide** (decisión de diseño del template). No
  corre sola ni frena. Si se pide, corre sobre **todas las hermanas** de la Historia, aunque
  se esté cargando una sola Tarea: es el lugar donde se chequea que **cada Escenario de la
  Historia esté cubierto** y que las coberturas parciales sumen. Lo que aparezca sale **como
  pregunta**, y si no se contesta queda como pendiente a confirmar en la tarjeta (en modo
  lote: lo que resuelve una fuente se corrige con la fuente a la vista, y el resto va al
  cierre).
