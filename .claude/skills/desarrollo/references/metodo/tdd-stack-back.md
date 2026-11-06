# TDD en el back — lo específico del stack (plantilla a completar)

> **El ciclo y la evidencia viven en [tdd-ciclo-y-evidencia.md](tdd-ciclo-y-evidencia.md)**
> y no cambian con el stack: rojo en la aserción, verde con la suite completa, refactor con la
> red puesta, evidencia verificada por otro agente, veredicto de tres estados. **Este archivo
> es lo único que cambia con el stack.** Se completa cuando el proyecto elige el suyo y deja
> la decisión en `arquitectura/decisiones.md`; cada `<completar: …>` que quede sin llenar deja
> en `SIN DATOS` lo que dependa de él.

## El stack, decidido

| Tema | Decisión |
|---|---|
| Lenguaje y framework | `<completar: lenguaje + framework del back>` |
| Build | `<completar: herramienta de build y de gestión de dependencias>` |
| Harness de test | `<completar: runner + librería de aserciones + cliente HTTP para los tests de endpoint>` |
| Arquitectura | **Monolito modular: un módulo por dominio, con capas verificadas por un test de arquitectura** ([[decisiones#DEC-002]]). Esto lo fija el método, no el stack |
| Versión del lenguaje | `<completar: versión, y por qué ésa>` |
| Versión del framework | `<completar: se fija mirando qué sirve el registro autorizado, no eligiendo un número de memoria>` |
| Versiones de los plugins del build | `<completar: se fijan en el primer build y se pinnean; no se dejan flotando>` |

Lo que la organización ya tenga decidido para su stack —versión mínima del lenguaje, modo de
ejecución, librerías obligatorias— se toma tal cual y se anota en
`arquitectura/esqueleto-proyectos.md`. Lo que no esté decidido se pregunta, no se elige.

## Dónde va cada cosa — esto es lo que más se rompe

```
<raiz-del-codigo>/
├─ shared/{api/error,exceptions,infra/config}/
├─ <modulo-a>/{api,application,domain,exceptions,infra}/
└─ <modulo-b>/{api,application,domain,exceptions,infra}/
```

Detalle de cada capa y sus subcarpetas: [crear-endpoint.md](crear-endpoint.md) §«Paso 4» y
[[decisiones#DEC-002]]. Qué módulos hay —y cuáles están en duda— lo dice el Cerebro del
proyecto, no este archivo.

**Una Tarea modifica un solo módulo.** No importa la `api` ni la `infra` de otro: si necesita
otro módulo, lo llama sólo por su `application`.

> ⚠ Los generadores y las guías de casi todos los frameworks proponen **paquetes globales por
> capa** (`api`, `model`, `business`, `repository`, `config`, `util`…). Acá gana el proyecto:
> **un módulo por dominio, y las capas adentro**. Si en un diff aparece una carpeta global por
> tipo técnico, salió de una plantilla ajena al método.
>
> Ojo con `api`: existe en los dos esquemas y significa cosas distintas. En el esquema por
> capas es **un** paquete global; acá es **uno por módulo**.

**Qué test para qué capa** ([[decisiones#DEC-002]]):

| Capa | Con qué se prueba |
|---|---|
| `api` | `<completar: test de endpoint, con el servicio levantado y un cliente HTTP de test>` |
| `application` | `<completar: test con dobles para los puertos (gateways y repositorios)>` |
| `domain` | `<completar: test unitario puro, sin levantar el framework>` |
| Estructura | `<completar: test de arquitectura que verifica las dependencias entre capas y entre módulos>` |

## Cómo se ve un rojo válido

> Si la clase o la función no existe, primero un commit `chore(firma): …` con las firmas vacías (sin comportamiento) y
> después el `test(rojo)`: así el rojo falla en la aserción y el commit del test trae sólo el test. Está en `guiar-tdd`.

Lo único que cuenta es **fallar en la aserción**: el test corrió hasta el final, comparó lo
esperado con lo obtenido, y no coincidió.

| Cómo falló | ¿Es rojo válido? |
|---|---|
| «Esperaba un `400` y obtuvo un `200`» | **SÍ.** Llegó a la aserción |
| «Esperaba el estado *rechazada* y encontró *aprobada*» | **SÍ.** Idem |
| No compila: un símbolo, una clase o un tipo que no existe | **NO.** Probás que falta una clase |
| Falta el método que el test llama | **NO** |
| La clase ni cargó, o falta una dependencia | **NO** |
| El contexto de la aplicación no arrancó, o falló la configuración del test | **NO.** Ni siquiera corrió |

Los cuatro de abajo **no son rojo válido**. El test todavía no existe: existe su esqueleto.

**Truco para llegar a la aserción antes de que exista la implementación:** creá la firma
devolviendo el valor más neutro que compile (nulo, cero, lista vacía) y dejá que el test corra
hasta el final y falle comparando. Ahí sí el rojo prueba algo.

`<completar: cómo se ve, en el runner elegido, el mensaje de una aserción fallida, y cómo se
ven un error de compilación y uno de carga — para que el verificador los distinga de un
vistazo>`

## Qué nivel para qué

| Tipo | Cuándo | Con qué |
|---|---|---|
| **Unitario** | Por defecto. Lógica de `domain` y `application` | `<completar: runner puro, sin levantar el framework>` |
| **De endpoint** | Capa `api`: códigos de respuesta, forma del cuerpo, validaciones | `<completar: servicio levantado + cliente HTTP de test>` |
| **De integración** | **Sólo si la Tarea lo declara** (dependencia externa real) | `<completar: servicio levantado + la dependencia real>` |

> Muchas guías mandan test de integración **siempre**. Acá manda **la Tarea**: un test de
> integración que no hace falta es lento, inestable y termina ignorado — y un test ignorado es
> peor que ninguno, porque figura como cobertura.

## Qué se simula

- **Se simula**: cualquier llamada saliente (otro servicio, un sistema externo, una API de
  terceros).
- **No se simula jamás**: la lógica de negocio. Si simulás la regla que ibas a probar,
  probás tu simulación.
- **Se fijan**: reloj, valores aleatorios, IDs generados.

## Comandos

```text
<completar: comando que corre sólo los unitarios>
<completar: comando que corre la suite completa>        # la que vale para el verde
<completar: comando que corre un solo test, por nombre>  # para el rojo
```

**El verde se declara con la suite completa.** El verde de uno con el rojo de otros tres no
es verde.

## Antes del Merge Request

1. **Analizador de seguridad (SAST/SCA)** — ⚠ **a definir por el equipo.** La intención es
   que corra en el pipeline y **frene** la entrega, con toda supresión llevando su motivo
   escrito al lado (sin motivo = hallazgo tapado). Mientras no esté configurado no se tilda
   como si hubiera corrido, y sin su resultado el ítem queda en `SIN DATOS`. Ver
   [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).
2. **Puerta de calidad**: cobertura (`<completar: herramienta de cobertura del stack>`),
   análisis estático y tests **exigidos por el build**, no sólo configurados.
3. **El contrato consolidado y validado.** Ver [contrato-openapi.md](contrato-openapi.md).
4. **Evidencia del rojo y del verde, auditada por otro agente.**
