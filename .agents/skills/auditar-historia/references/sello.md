# El sello de auditar-historia: formato y vigencia

Parte de la skill `auditar-historia`: se lee cuando se va a dejar el veredicto en la tarjeta, o al empezar, para saber si un sello anterior sigue vigente.

### El sello (no es un chequeo: es la salida)

```
Auditoria de Historia - auditar-historia
Veredicto: COMPLETA | CON HUECOS | NO AUDITABLE
Fecha: <AAAA-MM-DD>
Rev auditado: <System.Rev al LEER la Historia>   <- el sello mismo suma una revision, y no cuenta
Ficha fuente: <ruta> (ultimo cambio: <fecha>)
Escenarios encontrados: <N>        <- si dice 0, el loop BDD no existe
Hallazgos: <cantidad>
Pendientes a confirmar:
- <hallazgo, una linea, redactado como pendiente>   <- uno por hallazgo; "Ninguno" si no hay
```

**Cómo se mide la vigencia: por lo que cambió, no por cuántas veces se guardó.** En Azure
**toda** escritura directa crea una revisión: el propio sello (un comentario de
[[comentar-tarea]]), asignarla, cambiarle el Estado. Contando `Rev`, el sello **nace
vencido** —sellar ya suma una— y cualquier comentario en la Historia lo vence sin que nadie
haya tocado el Gherkin. Colgarle Tareas hijas **no** lo vence: el vínculo se crea siempre
desde la hija, y un vínculo no es contenido.

La regla: el sello registra **`Rev auditado: N`** (el que tenía al leerla) y queda
**vigente mientras ninguna revisión posterior a `N` haya cambiado Título, Descripción o
Criterios de aceptación**, y la ficha fuente no haya cambiado. Comentarios, Estado, Asignado,
Etiquetas y vínculos no cuentan. **Vence** si cambió alguno de esos tres campos o **la ficha
fuente**. Si no se pudo leer el historial, es **SIN DATOS**, que no es vigente. Lo verifica el
script de solo lectura (el MCP no expone el historial por campo):

```
bash bin/verificar-sello.sh historia <id-historia> <Rev auditado>
```

Sale `0` VIGENTE, `1` VENCIDO o `2` SIN DATOS. Si el SIN DATOS es de **la máquina** (sin
token, sin red, sin Python), el script lo dice y re-auditar **no** lo destraba: se arregla el
acceso. **La ficha fuente la chequea esta skill aparte**: el script mira el board, no el
Cerebro. Se compara la fecha de último cambio de la ficha contra la que anotó el sello. **Agregar «Tickets derivados» o la traza de una derivación no cuenta como cambio de la ficha**: si el único cambio desde el sello es ése (se mira con `git log` de la ficha), el sello sigue vigente.

**Al empezar**, se **lee** si ya hay un sello previo y si sigue vigente con ese criterio.
**Vale solo el más reciente** (el de mayor `Rev auditado`): como un comentario ya no vence
nada, un sello viejo que dijo COMPLETA puede seguir vigente aunque después se haya re-auditado
con CON HUECOS. Manda el último. El sello se postea en HTML ([[comentar-tarea]] §«Formato»): se
lee sobre el texto sin etiquetas.
**El sello no es requisito para derivar Tareas.** Es constancia de lo que se miró y cuándo.
En modo lote, si se pidió la auditoría, vale el veredicto de la preparación (o de la
re-auditoría), y el sello se publica al escribir.

> El sello **no se cuenta como chequeo**: en una primera auditoría siempre faltaría, por
> definición. Que una Historia con Tareas no tenga sello **no es un hallazgo**: la auditoría
> es opcional.
