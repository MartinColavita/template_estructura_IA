# Script y archivos del lote

Parte de la skill `planificar-lote`: se lee en la fase 0, al preparar el lote, y cada vez que hay que correr `bin/lote.py`.

## La carpeta del lote (fase 0, paso 6)

6. `python bin/lote.py preparar` (paso 0) crea `borrador/lote-<AAAAMMDD>-<tema>/` con el esqueleto de `CONTEXTO.md`, `items.json` y `tiempos.json`. Cada ítem se anota con `python bin/lote.py item <carpeta> --clave T-01 --tipo Tarea --accion ALTA --titulo "…" --padre "#NNNNN" …`. En `CONTEXTO.md` van el alcance, las fuentes leídas (rutas), lo decidido por F y R con su fuente, las P con su recomendación, la dedup por ítem y el estado de cada tarjeta a editar.

**El lote lo maneja el script, no la memoria de la sesión.** Las carpetas, las misiones de los sub-agentes, las auditorías mecánicas (si se piden), la tabla del cierre y la verificación antes de sellar salen de `bin/lote.py`. Así dos sesiones distintas hacen el mismo lote igual. Cada fase se marca con `python bin/lote.py tiempos <carpeta> <fase> inicio|fin` —las fases son `preparar`, `arranque`, `redactar`, `auditar`, `cierre` y `escribir`—, y el informe de tiempos va al reporte final. La skill corre estos comandos sola; sólo si la herramienta no tiene terminal le pasa a la persona el comando exacto.

## Archivos del lote (`borrador/lote-<AAAAMMDD>-<tema>/`, nunca versionado)

| Archivo | Qué es |
|---|---|
| `CONTEXTO.md` | El brief común: alcance, fuentes, decisiones y su fuente, preguntas |
| `items.json` | Los ítems del lote (lo arma `lote.py item`; `--desde-json` lo completa con `<clave>.json`) |
| `<clave>.html`, `<clave>-criterios.html`, `<clave>.json` | Cada ítem, tal como se va a escribir, y sus datos (título, puntos, actividad, relaciones) |
| `<clave>.final.html`, `<clave>-criterios.final.html` | Los mismos, con los `#ID` reemplazados (`lote.py ids`): es lo que se carga |
| `auditorias/<clave>.md`, `.json`, `.huella.json` | El chequeo mecánico del script y la huella de lo que auditó |
| `auditorias/set-<padre>.md` | El chequeo mecánico del conjunto de Tareas de una Historia |
| `auditorias/<clave>-auditor.md`, `auditorias/set-<padre>-auditor.md` | El informe del auditor (agente), con los F y los P y sus líneas `Veredicto:` y `Huella:` |
| `antes/<id>.html` | Lo que había en cada tarjeta que se pisa |
| `CIERRE.md` | La tabla del cierre, igual a la que se mostró (`lote.py cierre`) |
| `mapa-ids.json` | `[T-nn]` / `[H-nn]` → `#ID`, después de escribir |
| `tiempos.json` | Inicio y fin de cada fase (`lote.py tiempos`) |
