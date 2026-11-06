# entregables/especificaciones-tecnicas/

Especificaciones técnicas que produce `cerebro-architect` (skill `cerebro-architect-ui`) a partir
de una maqueta validada y de las reglas del Cerebro.

Cada spec detalla, por componente: props, estados, eventos y comportamientos, el mapeo de **cada
control a su regla `[RN-…]`** con wikilink (y la trazabilidad inversa: toda regla del módulo tiene
un componente que la materializa), y las APIs/endpoints que la pantalla consume.

Los repositorios de código la **referencian por ruta**; no la copian (`DEC-001`). Una Tarea del
tablero que cierre un contrato linkea la spec y pega sólo el fragmento puntual.
