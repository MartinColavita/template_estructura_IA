# entregables/

Artefactos generados por los agentes **y ya promovidos** desde `borrador/` con un pedido explícito
del usuario. Nada entra acá por iniciativa propia de un agente.

| Carpeta | Qué va | Se versiona |
|---|---|---|
| `disenos/` | Mockups HTML validados (la **maqueta vigente** es la que cita cada ficha funcional en `fuente_maqueta`), más el logo del producto (`logo.png`) que usan las presentaciones | Sí |
| `especificaciones-tecnicas/` | Specs que produce `cerebro-architect` a partir de maquetas y reglas: props, estados, eventos y mapeo a `[RN-…]` | Sí |
| `presentaciones/` | Presentaciones HTML autocontenidas (`cerebro-ppt-generator`) | **No** (`.gitignore`): quedan en local |

El código de la aplicación **no** vive en este repositorio (`DEC-001`): las specs se referencian
desde los repos de código por ruta, no se copian.
