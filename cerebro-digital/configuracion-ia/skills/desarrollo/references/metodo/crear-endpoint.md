# Crear un endpoint, de punta a punta

> Método propio.
> Taxonomía de errores y checklist adaptadas de `wshobson/commands` — **con el orden
> invertido**, ver abajo. MIT, [referencias-externas.md](../referencias-externas.md).

## El orden, que es lo que más importa

```
1. CONTRATO     el fragmento OpenAPI, con TODOS los códigos de respuesta
2. TESTS        uno por cada código y cada validación. Todos en ROJO
3. FIRMA        lo mínimo que compile, para que el rojo llegue a la aserción
4. CÓDIGO       el mínimo que pone los tests en verde
5. REFACTOR     con la suite entera en verde después de cada paso
6. EVIDENCIA    la audita otro agente
```

> **Por qué este orden y no otro.** El comando de referencia de `wshobson` hace lo contrario:
> elige framework, arma la estructura, define los modelos, **y recién al final genera el
> schema y los tests**. Ahí el contrato es un subproducto de la implementación, así que no
> puede contradecirla nunca — y un contrato que no puede estar en desacuerdo con el código no
> sirve para que otro equipo programe contra él.
>
> Acá el contrato viene primero **porque el front programa contra él sin esperarnos**.

## Paso 1 — El contrato

El fragmento OpenAPI de la Tarea. Sin esto no se escribe una línea.

Tiene que declarar, como mínimo:

| | |
|---|---|
| **Todos los códigos de respuesta** | No sólo el `200`. Cada `4xx` y `5xx` que el endpoint puede devolver |
| **La forma del cuerpo**, en éxito y en error | Incluido el formato del error |
| **Campos obligatorios** y cuáles pueden venir nulos | Es la mitad de los tests de validación |
| **Límites**: largos máximos, formatos, rangos | La otra mitad |

Si el endpoint no está en el contrato, **eso bloquea la Tarea**. No se inventa. Ver
[contrato-openapi.md](contrato-openapi.md).

## Paso 2 — Los tests, todos en rojo

Uno por cada cosa de esta lista. Si algo no tiene test, es un hueco, y un hueco no avisa:

- Cada **código de respuesta** del contrato.
- Cada **validación** declarada.
- Cada fila de la tabla de **Casos de error** de la Tarea.
- Cada regla `[RN-…]` que la Tarea cita.
- Cada **Escenario** del Gherkin de la Historia padre.

**Una condición por test.** Un "devuelve 400 o 422" pierde una rama en silencio.

### Familias de error que siempre hay que considerar

Adaptado de la taxonomía del comando de referencia, que en eso es buena:

| Familia | Qué se responde |
|---|---|
| **Entrada inválida** | `400`, con el detalle a nivel campo — no un mensaje genérico |
| **No autenticado** | `401` |
| **Autenticado pero sin permiso** | `403`. No se confunde con el anterior |
| **No existe** | `404` |
| **Conflicto de estado** (duplicado, ya procesado) | `409` |
| **Regla de negocio incumplida** | El código que el contrato declare, con la regla identificada |
| **Dependencia externa caída** | `502` / `503`, **nunca un `500` mudo** |

Cada una que aplique va al contrato **y** lleva su test. Las que no apliquen se declaran
descartadas con su motivo, en el bloque «Modos de falla evaluados» de la Tarea.

## Paso 3 — La firma mínima

El truco para que el rojo sirva: creá la clase y el método —o el módulo y la función, según
el stack— devolviendo lo más neutro que compile o cargue (`null`, `0`, lista vacía). Así el
test **llega hasta su aserción** y falla comparando, en vez de fallar por compilación.

Un rojo por un símbolo que no existe no prueba nada. Ver
[tdd-ciclo-y-evidencia.md](tdd-ciclo-y-evidencia.md).

## Paso 4 — El código

El mínimo que pone los tests en verde. Nada de adelantarse a casos que ningún test pide.

**Dónde va cada cosa** (esto es lo que más se rompe). Una línea por capa; el detalle está en
[[decisiones#DEC-002]]:

```
<modulo>/
├─ api/           la entrada HTTP: un punto de entrada por recurso REST (no por front) que traduce HTTP -> Command y llama al caso de uso, sin lógica de negocio; sus DTOs de entrada y de salida van acá
├─ application/   los casos de uso (reciben un Command, nunca un DTO de api; orquestan, no deciden) y las interfaces hacia afuera: gateways a sistemas externos, que devuelven tipos de domain, y repositorios de la base propia
├─ domain/        el modelo y sus reglas, juntos: la entidad, sus valores, sus enums y sus reglas; sin framework, sin HTTP, sin acceso a datos. Plano hasta 8 tipos y un concepto; si no, una carpeta por concepto
├─ exceptions/    las excepciones del módulo (extienden las de shared/exceptions)
└─ infra/         lo que implementa las interfaces de application: el cliente real de cada sistema externo (con el modelo del proveedor), su mock mientras no exista el real, los repositorios, y la configuración que elige mock o real

<carpeta de tests>/<modulo>/support/   dobles y datos de ejemplo que reusan varios tests
```

Las carpetas valen aunque tengan un solo archivo, pero se crean recién cuando hay algo que
poner. Las implementaciones se nombran por lo que son, nunca `Impl`, y no hay carpetas por
tipo técnico (`enums`, `util`, `model`, `service`, `impl`…). Estructura completa, la tabla de
nombres y carpetas, y su porqué: [[decisiones#DEC-002]] y `arquitectura/esqueleto-proyectos.md`
del Cerebro. Dónde cae cada archivo en el stack elegido: [tdd-stack-back.md](tdd-stack-back.md).

**Los errores no se mapean en la `api` de cada módulo.** El caso de uso lanza la excepción del
módulo y el status HTTP lo decide **un único** manejador de errores compartido (`shared/`),
con el formato de error que declara el contrato.

**Una Tarea modifica un solo módulo.** Si necesita otro, lo llama **sólo por su
`application`** (sus casos de uso) — nunca importando su `api` o su `infra`.

> ⚠ Las plantillas genéricas de muchos frameworks proponen `business/`, `repository/`,
> `model/`, `util/` **globales**. Acá gana la estructura por módulo del proyecto.

## Paso 5 — Refactor

Con la suite entera en verde. Si algo se pone en rojo, se vuelve atrás: no se ajusta el test
para que pase.

## Paso 6 — Checklist antes del Merge Request

Ninguno de éstos es opcional:

- [ ] El contrato consolida y valida (`armar-swagger`).
- [ ] **Todos** los códigos del contrato tienen test.
- [ ] Evidencia del **rojo** guardada, y falló **en la aserción**.
- [ ] Evidencia del **verde**, de la suite completa.
- [ ] Ningún import de `api` / `infra` de otro módulo.
- [ ] El diff modifica **un solo módulo**.
- [ ] Las extensiones obligatorias del stack presentes (salud, métricas, trazas, logs en JSON,
      documentación del contrato). ⚠ Cuáles son lo define el equipo / la organización del
      nuevo proyecto; se anota en `arquitectura/esqueleto-proyectos.md` del Cerebro.
- [ ] **Sin PHI** en código, tests, fixtures, logs ni mensajes de error.
- [ ] **SAST** corrió y frena la entrega. ⚠ **Pendiente de definir**: qué analizador de
      seguridad corre lo fija el equipo / la organización del nuevo proyecto; mientras no esté
      configurado en el pipeline, este ítem es `SIN DATOS` — no se tilda. Ver
      [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).
- [ ] La verificación la hizo **otro agente**.

Un ítem que no se pudo verificar es `SIN DATOS`, **no** es un tilde.

## Lo que este método NO decide

- **El lenguaje, el framework y sus versiones**: ⚠ los define el equipo / la organización del
  nuevo proyecto; se anotan en `arquitectura/esqueleto-proyectos.md` y en
  `arquitectura/decisiones.md` del Cerebro, y lo específico del runner y del layout va en
  [tdd-stack-back.md](tdd-stack-back.md).
- **El umbral de cobertura**: se mide sobre el **código nuevo**, no sobre el repositorio
  entero. ⚠ El número lo fija el equipo / la organización del nuevo proyecto y se anota en
  `arquitectura/decisiones.md`.
- **Cómo se parte una Historia en Tareas**: eso sale del juicio técnico de la reunión de
  devs, y si se pide lo controla `analizar-tareas`.
