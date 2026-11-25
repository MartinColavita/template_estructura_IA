# Fase 5: escribir y verificar

Parte de la skill `planificar-lote`: se lee en la fase 5, con el «sí» del cierre, antes de escribir. Los pasos 1 y 11 y lo que pasa si una escritura falla siguen en SKILL.md.

2. **Ediciones** (filas PISA), con el ANTES ya guardado.
3. **Altas de Épicas, Features e Historias**, padre antes que hijo.
4. **Si hubo auditoría, verificar y sellar cada Historia** auditada en el lote cuya columna «Auditoría» trae un veredicto (no *no se pidió* ni NO SE SELLA): su texto en Azure tiene que ser igual al borrador auditado (comparando el texto **sin etiquetas** y con los espacios normalizados: Azure reescribe el HTML), y el `Rev auditado` es la revisión verificada. Una Historia que el lote no tocó se sella con la revisión que leyó la auditoría, y sólo si no cambió desde entonces.
5. **Altas de Tareas** (`create_work_item` con `parentId`); en paralelo.
6. **Reemplazar `[T-nn]`/`[H-nn]`** por su `#ID` en las Descripciones: es el mismo contenido mostrado, con el número que faltaba. Lo hace `python bin/lote.py ids <carpeta> --mapa mapa-ids.json`, que escribe `<archivo>.final.html`: ése es el texto que se carga.
7. **Relaciones** (`manage_work_item_link`), siempre desde la tarjeta nueva.
8. **Si hubo auditoría, verificar y sellar cada Tarea** cuya columna «Auditoría» trae un veredicto (no *no se pidió* ni NO SE SELLA), con la misma comparación del paso 4 (en los dos pasos, se sella sólo si `python bin/lote.py comparar <auditado> <guardado-de-azure> --mapa mapa-ids.json` sale 0; si lo guardado es el JSON del work item, se agrega `--campo System.Description`): `Rev de la Tarea auditada` es la revisión verificada y `Rev de la Historia padre`, la del paso 4.
9. **Pendientes en las tarjetas:** las preguntas del arranque que quedaron sin contestar ya van como `⚠` en «Datos a confirmar» de la propia tarjeta, sin comentario aparte. Las **P de las auditorías** de una tarjeta, tal como se listaron en el punto 5 del cierre, van en su sello si lo lleva; si no lo lleva (NO SE SELLA), en un comentario «Pendientes a confirmar» ([[comentar-tarea]] §«Pendientes a confirmar»). Nada que no estuviera en el cierre.
10. **Traza:** «Tickets derivados» en la ficha y, en el Cerebro, **sólo** el «Conocimiento para el Cerebro» del cierre que el humano no tachó, escrito por `cerebro-curator`. Lo aplicado por recomendación técnica (R) **no** se escribe en el Cerebro como decisión: si no, el lote siguiente lo tomaría como fuente. Más una fila en [[historial/INDICE]] y la firma en `cerebro-digital/log.md`, en una rama `develop` (o la rama propia, si son dos); commit y push sólo si se piden.

**Si una tarjeta auditada no pasa la verificación, no se sella:** va al reporte, y re-auditarla
es opcional. Sin sello se puede desarrollar igual.
