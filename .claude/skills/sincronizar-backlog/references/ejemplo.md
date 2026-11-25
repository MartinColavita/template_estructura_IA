# Ejemplo de sincronización

Parte de la skill `sincronizar-backlog`: se lee cuando hace falta ver el flujo entero aplicado a una ficha.

### Ejemplo (genérico)

> Recuadro ilustrativo de un dominio de ejemplo; es solo un
> ejemplo, el tema real lo pone el proyecto destino.
>
> El usuario pide "bajá al board la ficha de Reservas". La ficha
> `cerebro-digital/.../<ficha-reservas>.md` declara en su bloque `## Derivación a
> backlog`: `[S-01]` Reservas · `[C-01]` Reserva de salas · `[F-01]`
> Crear una reserva con validación de disponibilidad · `[F-02]` Cancelar una reserva
> desde el panel. La skill copia eso **1:1** → **Épica** "Reservas" (=S-01) →
> **Feature** "Reserva de salas" (=C-01) → **Historias** F-01 y F-02 (la
> de cancelación Related con "Notificar la cancelación al solicitante"). Todos con tag
> `<etiqueta-tematica>` — **uno solo, sin etiqueta de versión ni de producto, y sin el nombre del slice** — y **Documento fuente** = la ruta
> de la ficha (referencia). Muestra el árbol, pregunta "¿Creo estos **4 work items**
> (1 Épica + 1 Feature + 2 Historias = S-01+C-01+F-01+F-02) con estos enlaces?", y
> recién con el "sí" llama a `create_work_item` +
> `manage_work_item_link`. Devuelve los `#ID`, los anota en el bloque **Tickets
> derivados** de la ficha y agrega una fila en [[historial/INDICE]] con el tema, los
> `#ID` y el `documento_fuente` — sin copiar el contenido de la ficha ni de los tickets. Si el
> PAT fuera de solo lectura, entrega el árbol como texto para cargar a mano.
