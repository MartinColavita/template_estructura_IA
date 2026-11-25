# Fase 3: auditar (opcional)

Parte de la skill `planificar-lote`: se lee en la fase 3, sólo si se pidió auditoría.

| Qué | Skill | Sobre |
|---|---|---|
| Cada Tarea | [[auditar-tarea]] | El archivo del borrador + la Historia padre como va a quedar + las reglas |
| El set de cada Historia | [[analizar-tareas]] | Todas sus Tareas, nuevas y ya cargadas |
| Cada Historia redactada o corregida en el lote | [[auditar-historia]] | El borrador + la ficha |

- **Primero el script:** `python bin/lote.py auditar <carpeta>` corre `auditar-tarea.py`, `auditar-historia.py` y `analizar-tareas.py` sobre todos los borradores, en orden fijo, y deja `auditorias/<clave>.md`. Lo que cuenta el script no lo vuelve a contar un agente.
- **Después, un agente auditor por ítem**, con la misión de `python bin/lote.py mision <carpeta> auditar <clave>`. Revisa **sólo** lo que el script lista en «Lo que este script NO mira» y confirma o descarta sus AVISOS. Su informe va a `auditorias/<clave>-auditor.md`, con una línea `Veredicto:` y una `Huella:`: si el archivo cambió después, el cierre marca la fila **NO SE SELLA** (se escribe igual, sin sello) hasta que se re-audite.
- **Y un auditor por conjunto** (las Tareas de cada Historia), con `python bin/lote.py mision <carpeta> auditar set-<padre>`, que deja `auditorias/set-<padre>-auditor.md`. Las Tareas que ya están en el tablero entran al conjunto con `lote.py item … --accion EXISTE --archivo <guardado>`: se analizan, pero no se escriben. Si el conjunto dio hallazgos, las Tareas lo dicen en la columna «Auditoría» y los hallazgos van como pendientes; si el análisis del conjunto no cierra (sin informe, vencido, SIN DATOS), sus Tareas salen **NO SE SELLA**. Ninguno de los dos frena la fila.
- Cada hallazgo sale marcado **F** o **P**. Los **F** los corrige el agente que redactó (no el auditor), sin preguntar, con la misión de `lote.py mision <carpeta> corregir <clave>`, y quedan listados en el cierre. Los **P** van al cierre.
- **Re-auditoría:** sólo de lo que cambió, por un agente distinto, **una vez**. Si sigue CON HUECOS, va así al cierre, marcado: se carga igual, su sello dirá CON HUECOS y sus hallazgos van como pendientes a confirmar. **No frena el desarrollo.**
- **Ninguna auditoría frena una fila.** Si una auditoría pedida no cierra —quedó vieja porque el archivo cambió, el informe no dice veredicto, o el auditor contradice al script—, la fila dice **NO SE SELLA**: se escribe igual, sin sello.
