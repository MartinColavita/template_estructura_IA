# Pruebas de aceptación — la capa que prueba el sistema, no las piezas

> Método propio. Complementa [armar-la-suite.md](armar-la-suite.md) (la pirámide) y
> [tdd-ciclo-y-evidencia.md](tdd-ciclo-y-evidencia.md) (el ciclo por Tarea). Dónde viven estas
> pruebas y con qué herramienta lo decide el equipo (`DEC-003`); la carpeta `qa/` de este
> repositorio es el lugar donde se enchufa el repo de QA si está aparte.

## La pregunta que contesta esta capa

**¿La aplicación desplegada hace lo que la Historia pidió, de afuera, como la usa una persona?**

Los tests del código contestan otra cosa: que cada pieza cumpla su contrato. Un Escenario puede
estar verde en el back (con el front simulado) y en el front (con el back simulado) y romperse
cuando se juntan: distinto formato de fecha, un código de error que uno devuelve y el otro no
maneja, una pantalla que espera un campo que el contrato cambió. Esa costura **sólo se ve
ejecutando el sistema entero**. Por eso esta capa **no es redundante**: es la única que mira lo
que las otras no pueden.

## Qué se automatiza (y cuánto)

| Se automatiza | No se automatiza acá |
|---|---|
| **Los Escenarios del Gherkin de la Historia**, con su título textual y el `#ID` | Casos que ya cubre un test unitario y no cruzan piezas |
| Los **flujos que dan plata**: los que, si fallan, el negocio se frena | Variantes de borde de un solo módulo (van en el unitario) |
| El **camino feliz y el error visible** de cada flujo principal | El estilo visual (va a revisión humana) |

**Pocas y rápidas.** La pirámide manda: muchos unitarios, menos de integración, poquísimos de
punta a punta. ⚠ *Propuesta del método, a confirmar por el equipo:* la suite de aceptación
entera corre en **menos de 15 minutos**; si crece más, se parte por slice y corre por partes.

## La trazabilidad: Historia → Escenario → prueba

Cada prueba de aceptación lleva, en su nombre o en una etiqueta, el **`#ID` de la Historia** y el
**título del Escenario** tal como está en el campo Criterios de aceptación. Es lo que permite
contestar sin abrir nada: *"¿qué Escenarios de la #NNNN tienen prueba de punta a punta?"*.

- El Gherkin es la **fuente**. La prueba no inventa pasos ni resultados: si para automatizar hace
  falta un dato que el Escenario no dice, es un hueco de la Historia y vuelve como pregunta
  ([[comentar-tarea]]), no se resuelve en la prueba.
- Un Escenario **cubierto en parte** por dos Tareas (la tabla SDD lo dice) recién está **cerrado**
  cuando su prueba de aceptación está verde contra el ambiente desplegado.
- La prueba de aceptación **no reemplaza** la evidencia del rojo de las Tareas: es otra capa, con
  otra pregunta.

## Lo que el front tiene que exponer (para que las pruebas no sean frágiles)

Las pruebas de punta a punta leen la interfaz igual que un lector de pantalla y que una persona.
Para que no se rompan con cada cambio de estilo, el front expone:

| Qué | Cómo | Por qué |
|---|---|---|
| **Identificadores estables** en cada control interactivo y en cada región que carga datos | Un atributo de automatización con un nombre **por función**, no por apariencia (⚠ el patrón exacto lo fija el equipo en `arquitectura/frontend/reglas-generales.md`) | Un selector por clase CSS o por texto cambia con el diseño; uno por función, no |
| **Nombre accesible** en todo elemento | Etiqueta asociada, texto del botón, nombre del ícono | Buscar por rol y nombre es a la vez accesibilidad y prueba estable |
| **Estados como atributo**, no sólo como color o animación | Cargando, deshabilitado, inválido, expandido | La prueba espera "terminó de cargar" sin dormir segundos fijos |

Es la misma inversión que [accesibilidad.md](accesibilidad.md): lo que ve un lector de pantalla
es lo que ve la prueba.

## Datos y ambientes

- **Nunca PHI.** Fábricas de datos y marcadores (`<persona>`, `<documento>`, …). Un registro real
  en una prueba de aceptación queda en el repositorio para siempre y corre en un ambiente que ve
  más gente que el código.
- **Cada corrida arranca de un estado conocido** (datos de siembra propios de la suite); una prueba
  no depende de lo que dejó la anterior.
- **El ambiente contra el que corre se declara** y los secretos van por variable de entorno
  ([dependencias-y-config.md](dependencias-y-config.md)).

## Cuándo corre y qué frena

| Momento | Qué corre | ¿Frena? |
|---|---|---|
| En el Merge Request | Los unitarios, de contrato e integración del repo de código | Sí |
| Al desplegar a un ambiente de prueba | La suite de aceptación entera, o la del slice tocado | **Sí, la entrega a producción** ⚠ a confirmar por el equipo |
| Una vez por día, contra el ambiente de prueba | La suite entera | No frena, pero abre un hallazgo |
| Antes de cortar tráfico a producción (migración) | Paridad + aceptación del slice | Sí |

**Un test inestable no se marca y se sigue: se arregla o se saca** ([armar-la-suite.md](armar-la-suite.md)).
Una suite de aceptación en la que "a veces falla" entrena al equipo a ignorar el rojo.

## Quién lo hace y con qué

El plan lo arma [[disenar-pruebas]] y las pruebas las escribe [[automatizar-e2e]], con el motor del tipo de
aplicación (`DEC-003`): Playwright no es la única herramienta, es la de las apps web y Electron. El esqueleto sale
de `bin/armar-e2e.py` y la cobertura por Escenario de `bin/cobertura-e2e.py`.

## Si QA ya tiene su propio repositorio

Se trata como una aplicación existente: [[absorber-aplicacion]] lo inventaría, se lee qué
Historias y Escenarios cubre, se ata cada prueba a su `#ID` y lo que no cubre queda como
pendiente. No se reescribe lo que ya funciona; se le agrega la trazabilidad que le falte.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Los Escenarios de la Historia tienen su prueba de aceptación, trazada, y pasó contra el ambiente desplegado |
| **HALLAZGO** | Un Escenario sin prueba de aceptación en un flujo principal, una prueba sin `#ID`, o una prueba que inventa pasos que el Gherkin no dice |
| **SIN DATOS** | **No hay capa de aceptación decidida (`DEC-003`) o no se corrió** contra un ambiente. No es "está probado de punta a punta": es que nadie lo verificó |
