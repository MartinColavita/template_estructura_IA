# Ejemplo de carga

Parte de la skill `cargar-a-azure`: se lee cuando hace falta ver el flujo entero aplicado a un caso.

### Ejemplo (genérico)

> Tras redactar el bug de un listado, el usuario pide "cargalo al tablero". La skill
> arma el preview: tipo **Bug**, título, *Pasos para
> reproducir*, *Gravedad `2-High`*, con `<documento>` como marcador. Pregunta
> "¿Creo la tarjeta con estos campos?". Recién con el "sí" llama a
> `create_work_item` y devuelve el `#ID` y la URL. Si el PAT del usuario fuera solo
> de lectura, en cambio, no escribe: entrega el texto para pegar a mano.
