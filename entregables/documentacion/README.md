# entregables/documentacion — la guía de uso y la documentación técnica, promovidas

Acá quedan, **con un «sí» explícito**, los dos entregables de cierre que produce la skill
`documentar-aplicacion` a partir del Cerebro:

- `guia-de-uso.html`: para las personas que usan la aplicación. Empezar en pocos pasos, cada flujo con su
  pantalla y su paso a paso dibujado, glosario, preguntas frecuentes, qué hacer si algo no sale.
- `documentacion-tecnica.html`: para el equipo. Resumen, módulos y arquitectura (con el grafo del código),
  modelo de datos, API, flujos, catálogo de reglas, integraciones, decisiones, pruebas, pendientes y deuda,
  aprendizajes, bitácora, glosario y diagramas.

Los borradores nacen en `borrador/documentacion/` con `python -B bin/generar-documentacion.py --tipo manual`
y `--tipo tecnica --app <repo>`; se pulen sólo con lo que está en el Cerebro (lo que falta queda marcado,
no inventado) y se promueven acá. Se regeneran después de cada slice: el documento se reemplaza, no se
parchea a mano. Las pantallas son las que cada ficha cita en `fuente_maqueta` (`entregables/disenos/`);
los diagramas interactivos, los de `archify`.
