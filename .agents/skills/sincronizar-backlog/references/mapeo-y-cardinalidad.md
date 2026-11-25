# Mapeo por vertical slices y cardinalidad

Parte de la skill `sincronizar-backlog`: se lee cuando se arma el árbol (paso 2) y se completa cada nodo con su plantilla.

## 2. Aplicar el mapeo por vertical slices → ADO

Descomponer según la arquitectura (**monolito modular por vertical slices**; ver [[organizacion-y-trazabilidad]] §5):

| En el dominio / arquitectura | En Azure DevOps |
|---|---|
| **Vertical slice / dominio** (los slices declarados en [[contexto-proyecto]]) | **Épica** |
| **Capacidad / caso de uso** dentro del slice | **Feature** |
| **Flujo / acción de negocio** | **Historia de usuario** |
| **Desglose técnico** dentro del slice (capas `api`/`application`/`domain`/`infra`) | **Tarea** — *momento dev/planning; NO en el árbol funcional por default* |

**Cardinalidad 1:1 (no segmentar «a ojo»).** El conteo sale del bloque `## Derivación
a backlog` de la ficha: **1 Épica por cada `[S-nn]`** (default 1; nunca inferir slices
no listados), **1 Feature por cada `[C-nn]`** (Parent = Épica de su slice), **1
Historia por cada `[F-nn]`** (Parent = Feature de su capacidad) y **0 Tareas** por
default. Ningún nodo fuera de la enumeración; no se parte ni se fusiona un flujo por
criterio propio. La **unidad de Historia es el flujo listado, NO la pantalla**
(decisión cerrada; ver [[organizacion-y-trazabilidad]] §5).

Completar **cada** work item según su plantilla, **no solo el título**: la **Épica**
([[plantillas/epica]]) y la **Feature** ([[plantillas/caracteristica]]) con objetivo +
alcance + criterios de alto nivel; las **Historias** con criterios en Gherkin
referenciando las `[RN-…]`. La Descripción **y los Criterios de aceptación** se arman
en **HTML** para que se vean bien formateados en el board — los Criterios (Gherkin) con
**todas las keywords en negrita** (`Dado`/`Cuando`/`Entonces`/`Y`/`Pero`), pasos
sangrados y un `<p>` por escenario (si no, se ven como un muro). Esqueleto:
[[checklists/mapa-campos-azure]] §"Esqueleto HTML".
