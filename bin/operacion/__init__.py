"""Lo comun de los scripts que tocan algo que CORRE: servidores, clusters, URLs de ambientes, imagenes.

Por que existe. El GATE de SERVIDOR de AGENTS.md dice que un activo que no figura en el inventario
autorizado no existe para la IA, ni siquiera para leerlo. Si cada script leyera el inventario a su
manera, cada uno autorizaria distinto. Aca hay un solo lector y una sola regla.

Reglas de la casa, iguales a las de bin/auditoria/:
- Solo biblioteca estandar. ASCII puro en los .py.
- SOLO LECTURA: nada de este paquete se conecta a un servidor ni escribe en el Cerebro.
- Tres estados, nunca dos: OK, FRENA (no esta autorizado) y SIN DATOS (no se pudo saber).
  Un inventario ausente o vacio NUNCA da OK (Regla del cero).

Modulos:
- inventario.py  Lee la tabla de cerebro-digital/<modulo>/operacion/inventario.md y decide si un alias
                 esta autorizado, hasta que nivel, y si admite pruebas dinamicas.
"""
