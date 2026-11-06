# Revisión de código por dimensiones

> Método propio.
> Estructura de dimensiones y severidades adaptada de `wshobson/commands` (MIT) —
> ver [referencias-externas.md](../referencias-externas.md).

## La regla que ordena todo

**Quien escribió el código no lo revisa.** La revisión la corre un agente distinto. No es
desconfianza: es que el que escribió ya decidió que estaba bien, y va a leer buscando
confirmarlo.

## Las cinco dimensiones

Se revisa **una dimensión por vez**, no todo junto. Mirar todo a la vez produce una lista de
cosas obvias y ninguna profunda.

| # | Dimensión | Qué busca |
|---|---|---|
| 1 | **Corrección** | Que haga lo que la Tarea dice. Casos borde, valores nulos, colecciones vacías, límites |
| 2 | **Seguridad** | Inyección, autenticación, autorización, datos sensibles en logs. Detalle y chequeos en [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md) |
| 3 | **Arquitectura** | Acoplamiento, cohesión, y **los límites de módulo** — que es lo que más se rompe acá |
| 4 | **Rendimiento** | Consultas en bucle (N+1), lecturas completas de tabla, ausencia de índices, cargas innecesarias |
| 5 | **Tests** | Que cubran los casos de la Tarea, que cada uno **pueda fallar**, y que ninguno tenga dos condiciones |

## Los chequeos de arquitectura, que son los nuestros

Éstos no están en ninguna guía genérica — salen de cómo está armado este proyecto:

Fuente: [[decisiones#DEC-002]] y `arquitectura/esqueleto-proyectos.md` del Cerebro.

- **Ninguna clase importa la `api` ni la `infra` de otro módulo.** Si necesita otro módulo,
  lo llama sólo por su `application` (sus casos de uso); puede importar los tipos que esos
  casos de uso devuelven o lanzan (`<otro>.domain`, `<otro>.exceptions`). Es el límite que
  sostiene la arquitectura entera.
- **Una Tarea modifica un solo módulo.** Si el diff abarca dos, o la Tarea estaba mal partida
  o el código se desbordó. Las dos cosas se avisan.
- **Dentro del módulo, las dependencias van hacia el núcleo:** `api → application, domain` ·
  `application → domain` · `infra → application, domain` · `domain → (nada)`. Nadie depende
  de `api` ni de `infra`. `domain` sin framework, sin HTTP ni acceso a datos (qué mapeo de
  persistencia admite la entidad lo fija [[decisiones#DEC-002]]).
- **La lógica va en un caso de uso** (en `application`, uno por unidad), que recibe un
  **Command**, nunca un DTO de `api`. No hay «servicios» genéricos que junten varios casos de
  uso. La entidad persistida **es** el modelo de dominio: un mapper entre ella y otro modelo
  de dominio es hallazgo.
- **Ninguna entrada HTTP mapea errores.** El status HTTP lo decide el manejador de errores
  único de `shared/`, con el formato de error que declara el contrato; las excepciones del
  módulo van en `<modulo>/exceptions`.
- **El contrato manda.** Si el código devuelve algo que el `openapi.yaml` no declara, el
  hallazgo es del código, no del contrato. Ver [contrato-openapi.md](contrato-openapi.md).
- **La estructura es por módulo, no por capa técnica.** Si aparece un `business/`,
  `repository/`, `model/` o `util/` global, salió de la plantilla genérica de algún
  framework, no del esqueleto del proyecto.

## Severidad — tres niveles, y sólo uno frena

| Nivel | Qué es | ¿Frena la entrega? |
|---|---|---|
| **BLOQUEANTE** | Vulnerabilidad, comportamiento incorrecto, límite de módulo roto, evidencia del rojo ausente o inválida | **Sí** |
| **RECOMENDACIÓN** | Problema de rendimiento, test que no puede fallar, duplicación real | No, pero se responde |
| **SUGERENCIA** | Nombres, forma, documentación | No |

**La severidad la fija el daño, no la comodidad.** Y un hallazgo bloqueante no se negocia
bajando su nivel: se arregla, o se declara aceptado **con el motivo escrito en el código**,
no sólo en el chat.

## Veredicto de tres estados

Igual que en todo el resto del método:

| Estado | Significa |
|---|---|
| **OK** | Se miró la dimensión y está bien |
| **HALLAZGO** | Se miró y hay algo — con archivo y línea |
| **SIN DATOS** | **No se pudo mirar** esa dimensión. **No es OK** |

Una dimensión que no se pudo revisar —porque falta el contrato, porque no corre el build,
porque no está la evidencia— se reporta `SIN DATOS`. **Nunca se omite en silencio**, que es
la forma más común de que una revisión parezca completa sin serlo.

## Cómo se entrega

> Dentro de la cadena de verificación de una Tarea, esto se entrega como **la línea `5-bis code-review` del bloque
> canónico más sus hallazgos** (`orquestador-desarrollo.md` §«Formato del veredicto»); el bloque largo de abajo es
> para una revisión suelta, fuera de la cadena.

```
REVISIÓN — <Tarea #NNNN> — <rama o diff>

  Revisado por: <agente distinto del que programó>

  1. Corrección .......... OK / HALLAZGO(n) / SIN DATOS
  2. Seguridad ........... OK / HALLAZGO(n) / SIN DATOS
  3. Arquitectura ........ OK / HALLAZGO(n) / SIN DATOS
  4. Rendimiento ......... OK / HALLAZGO(n) / SIN DATOS
  5. Tests ............... OK / HALLAZGO(n) / SIN DATOS

  BLOQUEANTES: n     <- uno por línea, archivo:línea, y qué rompe
  RECOMENDACIONES: n
  SUGERENCIAS: n

  Veredicto: APROBADO sólo con 0 bloqueantes y 0 SIN DATOS de los que no se pudieron mirar
             (un SIN DATOS por pendiente declarado en una DEC-nnn se lista y no frena).
  El cumplimiento del ciclo TDD no se revisa acá: es el control 5 (verificar-tdd), una sola vez.
  Formato canónico de toda la cadena: orquestador-desarrollo.md §«Formato del veredicto».
```

## Antes del Merge Request

Las dos puertas que no se saltean, y ninguna es opcional:

1. **SAST** — ⚠ **pendiente de definir.** La intención es que corra en el pipeline y
   **frene** la entrega, con cada supresión llevando su motivo escrito al lado (una supresión
   sin justificación es un hallazgo tapado). Qué analizador de seguridad corre lo define el
   equipo / la organización del nuevo proyecto y se anota en `arquitectura/decisiones.md` del
   Cerebro; **mientras no esté configurado en el pipeline**, el ítem se reporta `SIN DATOS`,
   nunca `OK`. Ver [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).
2. **Puerta de calidad**: cobertura, análisis estático y tests **exigidos por el build**.

Una herramienta configurada que el build no corre es decoración: da la sensación de que la
calidad está cubierta sin cubrir nada.
