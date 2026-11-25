# Fase 4: el mensaje del cierre

Parte de la skill `planificar-lote`: se lee en la fase 4, al armar el mensaje del cierre (lo escribe `bin/lote.py cierre`).

1. **La tabla del lote:**

   | # | Acción | Ítem | Padre | Puntos | GATES y §2b | Auditoría | `⚠` abiertos | Dedup | Archivo |
   |---|---|---|---|---|---|---|---|---|---|
   | 1 | ALTA / **PISA** / RELACIÓN | título | `#ID` o `[H-nn]` | n | OK / FRENA: cuál / no aplica / SIN DATOS | no se pidió / COMPLETA / CON HUECOS / NO SE SELLA: por qué | P-nnn | N consultas · 0 cand. / N consultas · `#ID=veredicto` | ruta |

   «GATES y §2b» resume el Bloque de GATES y el checklist de cierre de [[cargar-a-azure]] de ese
   ítem; el detalle queda en su archivo. Una fila con FRENA o SIN DATOS no se escribe.

2. **Aplicado sin preguntar:** una línea por decisión, con su fuente (maqueta, regla, respuesta del arranque, recomendación).
3. **Lo que se pisa:** por cada fila PISA, qué cambia en dos líneas y dónde quedó el ANTES (`borrador/lote-…/antes/<id>.html`).
4. **Conocimiento para el Cerebro:** lo que fijaron las respuestas del arranque (decisiones del día, reglas, pendientes nuevos o resueltos), con su destino. El "sí" lo guarda; lo que el humano tache, no.
5. **Preguntas que quedaron** (P de las auditorías, si corrieron), con recomendación, **por tarjeta**. Las que no se contesten quedan como **pendientes a confirmar** en su tarjeta: no frenan. Esta lista es exactamente lo que se postea en el paso 9 de la fase 5.
6. Una línea sobre los sellos: *«Las tarjetas con auditoría llevan su sello, y sus hallazgos van como pendientes a confirmar (molde de [[comentar-tarea]]).»*, o *«Auditoría: no se pidió. Ninguna tarjeta lleva sello.»*
7. La pregunta: *«¿Escribo todo el lote?»*
