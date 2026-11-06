# qa — las pruebas de aceptación de la aplicación

Acá viven las **pruebas de punta a punta** del proyecto, en `qa/<app>-e2e/` (o se enchufa un repositorio aparte, si
existe). No hace falta esperar un repo: [[disenar-pruebas]] arma el plan desde el Gherkin de cada Historia y
[[automatizar-e2e]] escribe las pruebas con el motor que fija `DEC-003` según el tipo de aplicación (Playwright para
web; WebDriver para escritorio; Appium o Maestro para móvil; proceso para línea de comandos; HTTP para API).
`bin/armar-e2e.py` arma el esqueleto de cada Historia y `bin/cobertura-e2e.py` dice qué Escenarios quedaron sin prueba.

```bash
git clone <url-del-repo-de-qa> qa/<nombre-del-repo>
```

Lo clonado **no se versiona acá** (`.gitignore`): sólo viaja este README.

## No es redundante con los tests del código

| Capa | Dónde vive | Qué prueba | Quién la escribe | Cuándo corre |
|---|---|---|---|---|
| **Unitaria y de contrato** | `back/`, `front/` (con `guiar-tdd`) | Que cada módulo haga lo que la Tarea dice: cada `[RN-…]`, cada código del contrato, cada Escenario mapeado en la SDD | El worker que programa, test primero | En cada commit y en el Merge Request |
| **De integración** | `back/`, `front/` (sólo si la Tarea lo declara) | Que una dependencia externa real responda como el contrato dice | Idem | En el Merge Request |
| **De aceptación (punta a punta)** | **`qa/`** (o una carpeta del repo de código, `DEC-003`) | Que **la aplicación desplegada** cumpla los **Escenarios de la Historia**, de afuera, como la usa una persona: pantalla, API y datos juntos | QA, a partir del Gherkin de la Historia | Contra un ambiente desplegado: en cada entrega, por lo menos una vez por día, y antes de cortar a producción |

Las dos primeras prueban **piezas**; la tercera prueba **el sistema**. Un Escenario puede estar
verde en el back y en el front por separado (cada uno simula al otro) y fallar cuando se juntan:
esa costura sólo la ve la capa de aceptación. Por eso el cierre BDD↔TDD de `verificar-tdd` no
reemplaza a QA: lo alimenta.

## Cómo se ata a las Historias

- Cada prueba de aceptación **nombra la Historia** (`#ID`) y el **Escenario** del Gherkin que
  automatiza, con el título textual. Así el Doctor y `consultar-backlog` pueden decir qué
  Escenarios tienen prueba de punta a punta y cuáles no.
- El Gherkin de la Historia es la **fuente**; la prueba no inventa pasos. Si al automatizar
  aparece un hueco, vuelve como pregunta a la Historia (`comentar-tarea`), no se tapa en la prueba.
- Los datos son **sin PHI**: fábricas y marcadores, nunca un registro real de una persona.
- El front expone lo que la prueba necesita para no ser frágil: identificadores estables por
  función (no por apariencia), nombres accesibles y estado de carga como atributo. Es la misma
  inversión que la accesibilidad: `desarrollo/references/metodo/pruebas-de-aceptacion.md`.

## Qué decide el equipo (`DEC-003`)

- Si las pruebas de aceptación viven en un repositorio aparte (acá) o dentro del repo de código.
- La herramienta de punta a punta y el ambiente contra el que corren.
- Cuántas: **pocas y de los flujos que dan plata**. Una suite de punta a punta que tarda una hora
  deja de correrse.

Mientras no esté decidido, la capa de aceptación es `SIN DATOS` en los veredictos de entrega: no
es que la aplicación esté probada de punta a punta, es que nadie lo verificó.

## Si QA ya tiene su repositorio

Se absorbe como cualquier aplicación existente (`absorber-aplicacion`): se inventaría, se lee qué
Historias cubre, se ata cada prueba a su `#ID` y su Escenario, y lo que no cubre queda como
pendiente. No se reescribe lo que ya funciona.
