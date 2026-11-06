"""Auditorias MECANICAS del pipeline de tickets (Historias y Tareas de Azure DevOps).

Por que existe. Los chequeos que son CONTEO (secciones, numeracion, Escenarios del padre
contra las filas de la tabla, reglas citadas que existen, enlaces, formato HTML) los hacia un
modelo leyendo la tarjeta entera: tardaba, gastaba tokens y cada sesion contaba distinto. Un
script cuenta igual siempre. Al auditor (el modelo) le queda SOLO lo que pide criterio, y el
reporte de cada script dice cuales son esos chequeos.

Reglas de la casa, iguales a las de verificar-sello.py y el Doctor:
- Solo biblioteca estandar. ASCII puro en los .py (los acentos se comparan normalizados).
- SOLO LECTURA: ningun script de este paquete escribe en Azure, en GitLab ni en el Cerebro.
  Escriben, como mucho, archivos de reporte dentro de borrador/.
- Tres estados, nunca dos: 0 = sin hallazgos   1 = hay hallazgos   2 = SIN DATOS
  (no se pudo leer el insumo). Un insumo vacio NUNCA da 0 (Regla del cero).

Modulos:
- texto.py    HTML -> texto plano, secciones <h3>, listas, tablas, enlaces, comparacion.
- reporte.py  Hallazgos, avisos, NO AUDITABLE, salida markdown/json y codigo de salida.
- cerebro.py  Indice de reglas del Cerebro y lectura de una ficha (frontmatter + bloque de
              derivacion).
"""
