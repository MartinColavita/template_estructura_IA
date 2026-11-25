# Índice del método: tests, por hito, cuando hace falta e infraestructura

Parte de la skill `desarrollo`: se lee antes de empezar un trabajo de tests, de un hito (funcionalidad, contrato, seguridad, dependencias, observabilidad, base, entrega, migración, ingeniería inversa, adopción), de rendimiento, de un incidente, de leer código ajeno, o cuando el código es infraestructura, un pipeline o toca lo que corre.

### Tests

| Tema | Archivo |
|---|---|
| Qué prueba un test unitario, y qué no | [tests-unitarios.md](metodo/tests-unitarios.md) |
| **Armar la suite**: 7 categorías, **mutación**, propiedades, tests inestables | [armar-la-suite.md](metodo/armar-la-suite.md) |
| **Pruebas de aceptación**: la capa que prueba el sistema desplegado contra los Escenarios de la Historia; qué expone el front; cuándo corre | [pruebas-de-aceptacion.md](metodo/pruebas-de-aceptacion.md) |

### Por hito

| Tema | Archivo |
|---|---|
| **Arrancar una funcionalidad** completa: back y front en paralelo | [arrancar-funcionalidad.md](metodo/arrancar-funcionalidad.md) |
| El **contrato OpenAPI** como fuente | [contrato-openapi.md](metodo/contrato-openapi.md) |
| **Seguridad y datos sensibles** — SAST, PHI, los controles que aplican | [seguridad-y-datos-sensibles.md](metodo/seguridad-y-datos-sensibles.md) |
| **Dependencias, configuración y secretos** | [dependencias-y-config.md](metodo/dependencias-y-config.md) |
| **Observabilidad** — las 4 señales, logs, alertas, chequeos de salud | [observabilidad.md](metodo/observabilidad.md) |
| **Cambiar el esquema de la base** sin romper: expandir/migrar/contraer | [migracion-de-base.md](metodo/migracion-de-base.md) |
| **Entregar** — qué tiene que exigir el pipeline, y volver atrás | [entregar-a-produccion.md](metodo/entregar-a-produccion.md) |
| **Refactor o migración** de una aplicación existente: red primero, caracterización, paridad, estrangulador | [refactor-y-migracion.md](metodo/refactor-y-migracion.md) |
| Ingeniería inversa de una aplicación existente | [ingenieria-inversa.md](metodo/ingenieria-inversa.md) |
| Adoptar un proyecto que ya trabaja con IA (su `CLAUDE.md`, skills, MCP) sin tirar nada ni quemar tokens | [adoptar-proyecto-existente.md](metodo/adoptar-proyecto-existente.md) |

### Cuando hace falta

| Tema | Archivo |
|---|---|
| **Rendimiento** — no se optimiza sin medir. Los 4 sospechosos | [rendimiento.md](metodo/rendimiento.md) |
| **Incidentes** en producción — contener antes de entender | [incidentes.md](metodo/incidentes.md) |
| **Entender código ajeno** — y el arranque de alguien nuevo | [entender-codigo-ajeno.md](metodo/entender-codigo-ajeno.md) |

### Cuando el código es infraestructura, un pipeline o toca lo que corre

El ciclo (rama, test primero donde se pueda, Merge Request, verificador distinto, nada sale sin «sí») es el de acá.
Lo específico lo pone la puerta de cada función, con sus barreras ([[AGENTS]]):

| Tema | Puerta |
|---|---|
| El código de **infraestructura** (IaC, Dockerfile, Compose, manifiestos) y la **arquitectura** que lo decide | [[arquitectura-e-infraestructura]] |
| El **pipeline** de CI/CD y el **despliegue** de una versión | [[despliegue-continuo]] |
| Un **servidor**: su salud, su mantenimiento, un incidente operativo | [[operacion-de-servidores]] |
| **Seguridad**: escanear, modelar amenazas, auditar y endurecer | [[seguridad]] |
| El proyecto en **GitLab**: su configuración, su CI y sus runners | [[gestion-de-gitlab]] |
