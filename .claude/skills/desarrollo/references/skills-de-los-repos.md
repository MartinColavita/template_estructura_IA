# Skills de los repositorios de código

Parte de la skill `desarrollo`: se lee cuando se trabaja dentro de `back/` o `front/`, cuando se arma la misión de un worker o de un verificador, o cuando se cuentan las skills del proyecto.

### Las skills que viven en los repositorios de código

Esta skill es el **método**; la **ejecución** dentro del código la hacen las skills de `back/` y
`front/`, que actúan dentro del repositorio clonado:

| Skill | Dónde vive | Qué hace | Relación con ésta |
|---|---|---|---|
| `guiar-tdd` | `back/` y `front/` | Conduce el ciclo rojo-verde **mientras se programa** | Aplica [tdd-ciclo-y-evidencia.md](metodo/tdd-ciclo-y-evidencia.md) |
| `verificar-tdd` | `back/` y `front/` | **Audita la evidencia** — la corre otro agente | Es el paso 5 del ciclo por Tarea. **No puede vivir acá**: quien produce nunca aprueba |
| `auditar-codigo` | `back/` y `front/` | **¿La entrega cumple lo que el pipeline exige?** Contrato de la Tarea, límites del módulo, tests cubiertos, sin PHI ni secretos | Distinta de [code-review.md](metodo/code-review.md), que mira si el código está bien escrito |
| `armar-swagger` | **sólo `back/`** | Consolida y valida el `openapi.yaml` | Es el paso obligatorio de [contrato-openapi.md](metodo/contrato-openapi.md) |
| `diagnosticar-repo` | `back/` y `front/` | Corre el Doctor sobre el repositorio clonado | Independiente |
| `consultar-cerebro` | `back/` y `front/` | Lectura del Cerebro, una ficha por vez | Independiente |

**El reparto, en una línea: acá está el MÉTODO; allá está la EJECUCIÓN dentro del código.**

- **`verificar-tdd` y `auditar-codigo` están afuera a propósito.** Si vivieran acá, el mismo
  agente que produjo leería la guía de cómo auditarse — y se pierde la independencia, que es la
  regla más fuerte del método.
- **`armar-swagger` sólo existe en `back/`.** En el front, ese ítem se verifica contra el contrato
  que consolidó el back.

> **Ojo con los conteos.** Cuando el proyecto cuenta sus skills (el número vive en `AGENTS.md` y lo
> verifica el hook), habla de las de
> `cerebro-digital/configuracion-ia/skills/`. Las de `back/` y `front/` **no entran en ese
> número**, pero **sí se versionan y sí las verifica el hook**: compara el par `.claude/skills`
> contra `.agents/skills` de cada uno y frena el commit si difieren.
