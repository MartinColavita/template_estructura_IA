---
id: plantilla-tarea
tipo: plantilla
estado: F-Draft
modulo: integracion-azure-devops
title: "Plantilla — Tarea (Azure DevOps)"
author: equipo
tags: [azure-devops, tarea, task, plantilla, redaccion]
last_updated: 2026-10-01
---

# Plantilla — Tarea (Task)

Plantilla rellenable para escribir una Tarea profesional en Azure DevOps: una unidad de trabajo técnica, concreta y verificable, que siempre cuelga de una Historia (o Característica) padre. Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[historia-de-usuario]] · [[habilitador-tecnico]] · [[bug]] · [[mapa-campos-azure]]

---

## Cuándo usar esta plantilla

Una **Tarea** es una unidad de trabajo **técnica y acotada** que contribuye a una Historia de usuario. No describe valor de negocio (eso lo hace la Historia); describe **qué hay que hacer, cómo se sabe que está hecho y cuánto lleva**.

- Si lo que escribís tiene **rol / necesidad / beneficio** ("Como usuario quiero... para...") → es una **Historia**, no una Tarea. Ver [[historia-de-usuario]].
- Si es una **migración / reestructuración** o una **investigación acotada (spike)** → usá [[habilitador-tecnico]].
- Si es un **defecto** → usá [[bug]].

> **Regla anti-patrón:** **nunca** dejes la Descripción como "solo un link de Figma / GitLab". El link va como **apoyo**; el alcance se escribe igual, en texto, aunque el diseño esté en Figma.

---

## Tamaño y forma (que se lea, y que salga rápido)

Una Tarea completa no es una Tarea larga. En una prueba del proyecto de origen, un lote de 13 Tareas salió con 511 tests y unos 378.000 caracteres (una sola tenía 119 tests): nadie lee eso entero, y redactarlo, auditarlo y corregirlo fue la mayor parte de la planificación. La completitud **no se negocia** (se puede auditar a pedido con [[auditar-tarea]]); lo que se controla es el tamaño de cada Tarea y que nada se escriba dos veces.

| Regla | Cómo |
|---|---|
| **30 tests o menos por Tarea** | Si la lista completa no entra, la Tarea es demasiado grande: **se parte** (por endpoint, por componente o por capa), igual que una estimación de 13 o más. **No se recorta la lista**: un caso que falta no se prueba nunca |
| **Una línea por test** | `N. <entrada o condición> → <resultado esperado> [RN-…] (⚠ P-nnn)` (en un Esquema, una línea por fila). Sin prosa que explique el test: si hace falta explicar, falta un dato en la entrada. **El resultado esperado va entero en el test** —código y payload o mensaje—, aunque también figure en «Casos de error»: es lo que comparan [[auditar-tarea]] y `verificar-tdd` |
| **Esquema** | Si varios casos comparten la **misma condición** y sólo cambian los datos, van en **un** ítem: `N. Esquema — <condición>:` y debajo una lista **con viñetas** (en HTML `<ul>`, nunca `<ol>`: rompería la numeración que cuentan [[cargar-a-azure]] §2b fila 4 y [[auditar-tarea]] chequeo 15), una fila `<entrada> → <resultado esperado>` por caso. `guiar-tdd` lo escribe como un test parametrizado con esas filas. Si cambia la condición, son ítems distintos |
| **Datos base, una vez** | Un párrafo «Datos base» al principio de la lista, con los datos de prueba comunes; cada test dice sólo lo que cambia |
| **Cada texto, una vez** | Los textos literales, las listas de valores y los mensajes van **en el test que los verifica**, y el «Comportamiento exacto» no los repite: queda para lo que ningún test fija. La excepción es el resultado esperado, que va siempre entero en su test (ver arriba) |
| **Escenarios no cubiertos, en una línea** | La tabla de Escenarios lista sólo los que esta Tarea cubre (entero o en parte). Los demás van en la línea «No cubre» al pie, con su título textual y la Tarea que los cubre |
| **Enlazar, no copiar** | La maqueta, la ficha y el contrato de otra Tarea se enlazan; se copia sólo el fragmento puntual que el test necesita |
| **Cada test con un rojo posible** | La lista se diseña por **triangulación**: cada test agrega un caso que la implementación anterior todavía no cumple. Un caso que la implementación natural ya cumple no es un test de TDD: es un guardarraíl, y los guardarraíles son la excepción, no la mitad de la lista (en una Tarea del proyecto de origen fueron 7 de 19) |
| **20 archivos o menos por Merge Request** | Si la Tarea va a tocar más de 20 archivos, se parte al planificar. Un Merge Request más grande no se revisa bien (en dos Tareas del proyecto de origen fueron 22 y 24) |

---

## Campos de Azure DevOps (mapa)

| Campo visible (Azure) | Referencia interna | Qué poner acá |
|---|---|---|
| Título | `System.Title` | Módulo/dominio + acción concreta |
| Descripción | `System.Description` (HTML) | Objetivo, alcance técnico, subtareas, material de apoyo, resultado entregable, Definición de terminado. **Si la capa es `api`/`application`/`domain`, además el bloque obligatorio**: Contrato técnico (fragmento OpenAPI si es `api`), Validaciones, Casos de error, Dependencias, **Especificación cerrada (SDD)** con la tabla de Escenarios de la Historia, **Tests a escribir PRIMERO** numerados y **Modos de falla evaluados** |
| Actividad | `Microsoft.VSTS.Common.Activity` | Development / Testing / Design / Documentation / Deployment / Requirements |
| Esfuerzo original | `Microsoft.VSTS.Scheduling.OriginalEstimate` | Horas estimadas |
| Prioridad | `Microsoft.VSTS.Common.Priority` | 1 (máxima) … 4 (mínima) |
| Enlace Primario/Parent (+ Related) | (links) | Historia/Característica de la que cuelga; Related a tareas del mismo tema |
| Ruta de iteración | `System.IterationPath` | `<Proyecto>\<Equipo> - Sprint NN` |
| Etiquetas (solo temática) | `System.Tags` | `<tema>` — **una sola, techo duro**: sin tag de slice, sin producto/repo |

Detalle de campos y valores válidos: [[mapa-campos-azure]].

---

## PLANTILLA (copiar y rellenar)

### Título
```
<Modulo/dominio> - <accion concreta en infinitivo>
```
<!-- Ejemplos:
     "Reservas - Implementar validacion del campo <documento> en el alta"
     "Listados - Agregar columna 'Estado' a la grilla"
     Usá prefijo de módulo consistente. Sin typos. Infinitivo, no gerundio. -->

### Descripción

**Objetivo concreto**
<!-- Una o dos oraciones: qué se busca lograr con esta tarea. NO el porqué de negocio (eso va en la Historia). -->
<que hay que construir/modificar y para que, en terminos tecnicos>

**Alcance técnico**
<!-- La arquitectura es de módulos de dominio (DEC-002): cada Tarea modifica UN solo módulo; el slice es la Épica del backlog. -->
- **Vertical slice / dominio:** <slice, de los declarados en contexto-proyecto>
- **Componente / repo:** <nombre del repo de código, de los declarados en contexto-proyecto>
- **Capa afectada:** backend → `<api | application | domain | infra>` del módulo · frontend → `<capa o tipo de componente según el stack>`
- Endpoints o entidades involucradas: <si aplica>
- **No cruza módulos del código** (decisión de límites de módulo del Cerebro, `[DEC-…]`): modifica **un solo módulo**; si necesita otro, llama a su `application` (sus casos de uso) y puede usar los tipos que devuelven o lanzan (`<otro>.domain`, `<otro>.exceptions`). **Nunca** importa `<otro>.api` ni `<otro>.infra`.
- Fuera de alcance: <lo que explicitamente NO entra>
- **Requiere test de integración:** `<si | no>` — *sí* sólo si toca una dependencia externa real
- **Modo de pruebas:** `<TDD | test-después: <motivo> | sin tests: <motivo> | caracterización primero>` — TDD por defecto; los otros sólo con motivo escrito (esqueleto, configuración, migración, UI puramente visual, spike, código existente sin red) y con la red mínima que cada modo exige

> **Todo lo que sigue, hasta "Subtareas / pasos", es UN bloque: OBLIGATORIO si la capa es `api`, `application` o `domain`** (si otro código —humano o IA— va a **llamar** esto) — incluye Contrato técnico (fragmento OpenAPI si es `api`), Validaciones, Casos de error, Dependencias, Especificación cerrada (SDD) y los Tests a escribir primero (TDD test-first). **OPCIONAL/borrable entero** si la tarea es chica y de solo UI/config (p. ej. "agregar una columna a una grilla", "corregir un texto"): no infles el ticket con secciones que no aplican. Si aplica, es el corazón de la tarea — es lo que permite codear sin ida y vuelta.

**Contrato técnico (entrada/salida)**
> Si la Tarea es de **front**, el contrato incluye los **identificadores estables** de cada control que crea (`data-testid` o el
> que fije `DEC-003`), nombrados por función (`lista-reservas`, `cancelar-{id}`): son los que las Notas para QA de la Historia
> citan y los que la prueba de punta a punta busca.
<!-- Si ya existe un spec de arquitectura (cerebro-architect, en entregables/especificaciones-tecnicas/) con este contrato, LINKEALO y pegá solo el fragmento puntual — no copies todo el documento (enlazar, no copiar). Si no existe, esta tarea es el lugar donde se cierra. -->

*Si la capa es `api` (endpoint HTTP) — escribilo como FRAGMENTO OpenAPI (YAML), NO en prosa:*
<!-- Este fragmento es PARSEABLE: la skill armar-swagger (en el repo de back) lo consolida
     en openapi.yaml, lo pasa por un linter y publica la documentación del contrato. Un `paths:` por
     endpoint de esta Tarea. El back lo implementa y valida; el front lo simula (simulación generada desde el contrato). -->
```yaml
paths:
  <ruta>:                       # p. ej. /api/<recurso>/{id}/<accion>
    <método>:                   # get | post | put | delete
      summary: <qué hace en una línea>
      parameters:               # borrar si no hay parámetros de ruta/query
        - { name: <id>, in: path, required: true, schema: { type: integer } }
      requestBody:              # borrar si el endpoint no lleva body
        required: true
        content:
          application/json:
            schema:
              type: object
              properties: { <campo>: { type: <tipo> } }
      responses:
        '<2xx>': { description: <éxito> }
        '<4xx>': { description: <CODIGO_ERROR> }   # una por cada fila de "Casos de error"
```

*Si la capa es `application`/`domain` (comando o función pública, sin HTTP):*
- **Firma:** `<NombreComando/Función>(<parámetro>: <tipo>, ...): <tipoRetorno>`
- **Entrada:** <forma del Command (un objeto de comando inmutable; el caso de uso nunca recibe un DTO de `api`), campo por campo> · **Salida:** <forma del resultado> · **Excepciones que puede lanzar:** `<TipoExcepcion>` (cuándo)

*Si la capa es `infra` (integración con recurso externo: BD, cola, servicio externo):*
- **Recurso:** <tabla/cola/servicio> · **Operación:** <query/mensaje/llamada exacta> · **Contrato del recurso externo:** <qué espera y qué devuelve, o link a su documentación>

**Validaciones**
<!-- Una línea por campo/regla. Sin esto, "válido" es una opinión. -->
- `<campo>`: <regla de validación exacta> `[RN-…]` (si aplica)

**Casos de error**
<!-- Todo código de error que el contrato puede devolver, con su forma exacta. -->
| Condición | Código (HTTP/excepción) | Payload / mensaje | Regla |
|---|---|---|---|
| <p. ej. body sin `<campo>` obligatorio> | `400` | `{ "error": "<CODIGO>", "message": "<...>" }` | `[RN-…]` |
| <p. ej. entidad no encontrada> | `404` | `{ "error": "<CODIGO>", "message": "<...>" }` | — |

**Dependencias**
<!-- Qué necesita YA existir para poder construir esto, y a quién le importa que esto cambie. -->
- **Depende de:** <endpoint/tabla/servicio ya existente que esta tarea consume> — ⚠ si no existe todavía, esta tarea está bloqueada
- **De esto depende:** <otra tarea/historia que consume lo que esta tarea entrega> (Related)

**Especificación cerrada (SDD)**
<!-- La especificación y el criterio de aceptación se cierran ANTES de tocar código (evita interpretaciones distintas entre agentes en paralelo). El "Contrato técnico" de arriba YA es parte de esta especificación. -->
- Comportamiento exacto + reglas `[RN-…]` que aplican: <...>

*Escenarios de la Historia que esta Tarea cubre* — **la bisagra entre BDD y TDD:**
<!-- La Historia trae el Gherkin (loop externo, BDD). Esta Tarea trae los tests (loop interno, TDD).
     Esta tabla es lo único que los une: sin ella nadie puede responder si escribir los tests
     de la Tarea alcanza para cerrar un Escenario de la Historia.
     El título del Escenario se copia TEXTUAL del campo Criterios de aceptación del padre:
     si no coincide palabra por palabra, no sirve para rastrear. -->

| Escenario de la Historia `#<ID>` | Qué parte cubre esta Tarea | Tests que lo verifican |
|---|---|---|
| `<título textual del Escenario>` | `<la porción que le toca a esta Tarea>` | `<n.º de los tests de la lista de abajo>` |

**No cubre:** `<título textual del Escenario>` (`#<ID de la Tarea que lo cubre>`) · `<título textual>` (`#<ID>`) · …
<!-- Una sola línea con los Escenarios del padre que esta Tarea no toca. Filas + títulos de esta línea = Escenarios del padre (lo cuentan cargar-a-azure §2b fila 5 y auditar-tarea chequeo 5). Si la Tarea los cubre todos, la línea se borra. -->

> Si un Escenario del padre **no** lo cubre ninguna Tarea, es un **hueco**: lo detecta [[analizar-tareas]] y se pregunta, no se tapa.
> Si esta Tarea cubre solo **parte** de un Escenario (p. ej. el back de un flujo que también necesita front), decilo en la columna del medio y nombrá la otra Tarea en *Dependencias*.

**Tests a escribir PRIMERO (TDD test-first)**
<!-- La LISTA de tests que se escriben ANTES del código — no el código de los tests (eso lo escribe la skill guiar-tdd al desarrollar, en el repo de código). Un caso por cada validación y por cada fila de "Casos de error" de arriba, no solo la invariante de negocio. Es el contrato ejecutable que guiar-tdd consume en orden Red-Green-Refactor y que sincroniza a los sub-agentes (desarrollo, base de datos, testing).
     NUMERADOS (1., 2., 3.) y no con viñetas: la tabla de Escenarios de arriba los referencia por número.
     UNA LÍNEA por test y 30 o menos (ver «Tamaño y forma»). Si hay datos de prueba comunes, van una vez en «Datos base». -->
**Datos base:** <los datos de prueba comunes a todos los tests; cada test dice sólo lo que cambia> *(borrar si no hay)*
1. Caso feliz: <input de ejemplo> → `<código éxito>` + `<forma de la salida>`
2. `<validación 1>` → `<código>` + `<payload de error>` `[RN-…]`
3. `<caso de error de la tabla>` → `<código>` + `<payload>`
4. Invariante de negocio protegida: <p. ej. "una reserva cancelada no admite usos con fecha >= hoy"> `[RN-…]`
5. **Guardarraíl (nace verde — EXENTO del rojo previo):** <qué decisión protege> — **se pone en rojo si** <el cambio concreto que lo haría fallar> `[RN-…]` · *si no hay ninguno de verdad, borrá este renglón: inventarlo es peor que no tenerlo.*
6. **Integración:** <qué se prueba contra la dependencia externa real> — **obligatorio si arriba pusiste «Requiere test de integración: sí»**; si pusiste «no», borrá este renglón.

> **El guardarraíl es la ÚNICA excepción al rojo previo, y se gana por escrito.** Es un test
> que **nace en verde a propósito** porque protege contra una regresión futura, no contra el
> bug de hoy: por eso `guiar-tdd` no le escribe commit de rojo y `verificar-tdd` no se lo
> exige. Como **suprime la evidencia del ciclo**, la etiqueta hay que ganársela con tres cosas:
> - **Afirma sobre la FUENTE** — una constante, un catálogo, la estructura del módulo, las
>   dependencias del slice. No sobre el DOM renderizado ni sobre el cuerpo de una respuesta
>   que otro test ya asegura.
> - **Ningún otro test de la lista lo implica.** Si el test 1 dice «se ven **exactamente** estas
>   tres opciones», uno que diga «no aparece esta cuarta» **no puede ponerse en rojo con el 1 en
>   verde**: es redundancia, no guardarraíl.
> - **Trae escrita la frase «se pone en rojo si …»**, nombrando el cambio concreto. Si esa frase
>   no se puede escribir, **no es un guardarraíl**: va sin etiqueta y con su rojo previo como
>   cualquier otro test.
>
> **No lo confundas con la «Invariante de negocio» del punto 4.** La invariante falla cuando
> alguien rompe una **regla de negocio** y lleva rojo previo **como todos**. El guardarraíl falla
> cuando alguien rompe una **decisión que hoy ya se cumple**. Lo chequea [[auditar-tarea]]
> (chequeo 8).
>
> *Por qué existe este renglón.* En el proyecto de origen se auditaron las cuatro primeras Tareas reales del board con
> [[auditar-tarea]], **un agente distinto por tarjeta**, y cada una trató el guardarraíl de una
> manera diferente: una lo declaró bien (análisis estático sobre las dependencias del slice),
> **una lo declaró mal** —redundante con su propio test 1, así que se cobró una exención a
> cambio de nada y se ahorró un rojo que sí existía—, dos no lo reclamaron y acertaron, y en una
> de esas dos **falta** el guardarraíl que sí correspondía: el límite de slice está exigido en el
> DoD sin un solo test que lo sostenga. Cuatro tratamientos distintos del mismo concepto no son
> descuido de quien redacta: **no había forma canónica que copiar**, porque este renglón no
> existía y el esqueleto solo ofrecía «Invariante protegida», que es otra cosa.

> **Dos cosas que el ítem tiene que traer ADENTRO, no en otra sección de la tarjeta.**
> - **El `#ID` de la Tarea complementaria.** Si un Escenario se cubre en parte, escribí el
>   número: «lo completa la Tarea de front **#NNNNN**», nunca «la Tarea de front (Related)».
>   La relación de Azure existe, pero quien lee la tarjeta no la ve desde el texto y no puede
>   seguir el Escenario hasta el final.
> - **La marca del pendiente.** Si un test depende de algo del bloque «Datos a confirmar», la
>   `⚠` va **en el ítem del test**, no solo en el bloque. Quien escribe los tests lee la
>   lista, no la tarjeta entera: sin la marca ahí **inventa el valor**, y ese valor inventado
>   queda como si fuera la especificación.
>
> Las dos salieron mal en **las tres** primeras Tareas técnicas reales del proyecto de origen — auditadas
> con [[auditar-tarea]], un agente distinto por tarjeta (chequeos 5 y 14). Detectarlas una por
> una después sale más caro que escribirlas bien la primera vez.

> **Coherencia obligatoria del test de integración.** Si en *Alcance técnico* declaraste «Requiere test de integración: **sí**», entonces **tiene que haber (a) al menos un test de integración en esta lista, (b) una subtarea que lo escriba y (c) un ítem propio en la Definición de terminado**. Declararlo arriba y no pedirlo abajo es el defecto silencioso más común: el dev cierra la tarea con puros dobles y nadie lo nota. Lo chequea [[analizar-tareas]].

**Modos de falla evaluados**
<!-- Una linea por familia: o queda cubierta por un test de arriba, o se descarta CON EL MOTIVO. Nunca ausente. Un "no aplica porque..." escrito es una afirmacion auditable; el silencio no lo es. Lo chequea auditar-tarea (chequeo 11), y en las tres primeras Tareas reales del proyecto de origen este bloque no existia: entre las tres dejaron trece familias en silencio, incluida la autorizacion de un endpoint que devuelve datos sensibles. -->
- **Estado:** <la entidad en un estado que no admite la operación> / no aplica porque …
- **Concurrencia:** <dos operaciones simultáneas sobre la misma entidad> / no aplica porque …
- **Autorización:** <quién puede operar sobre esa entidad> / no aplica porque …
- **Dependencia caída:** <el servicio o la base no responden> / no aplica porque …
- **Límites:** <tamaño, cantidad, rango de fechas, largo de los textos> / no aplica porque …
- **Idempotencia:** <repetir la misma llamada> / no aplica porque …

**Subtareas / pasos**
<!-- Lista chequeable de lo que hay que hacer, en orden. -->
1. <paso 1>
2. <paso 2>
3. <paso 3>

**Material de apoyo (opcional)**
<!-- Los links van ACÁ, como apoyo. El alcance ya quedó escrito arriba. -->
- Diseño (Figma): <link> — (el link es apoyo, no reemplaza el alcance escrito)
- Repo / rama (GitLab self-hosted): <link>
- Documento fuente: <ruta/al/documento.md> (link al repo) — referencia, no contenido (ver organizacion-y-trazabilidad §3)

**Resultado entregable**
<!-- Qué queda cuando la tarea termina, algo tangible y verificable. -->
<p.ej. "Merge Request mergeado en develop con la validación funcionando en <ambiente de prueba>">

**Definición de terminado (DoD)**
<!-- Checklist que cierra la tarea. Adaptá según sea front o back. -->
- [ ] El cambio compila / buildea sin errores.
- [ ] **El contrato de entrada/salida implementado coincide EXACTO con "Contrato técnico"** de esta tarea (probado con el ejemplo real, no solo "compila") — si aplica esa sección.
- [ ] **El test de la invariante `[RN-…]` existe y pasa** (TDD); hay tests que cubren el cambio — si aplica esa sección.
- [ ] **La tabla de «Especificación cerrada (SDD)» se contrastó contra el campo Criterios de aceptación de la Historia padre** —no contra sí misma— y cada Escenario que esta Tarea declara cubrir quedó verde con sus tests; los que cubre solo en parte tienen nombrada la Tarea complementaria. Lo audita `verificar-tdd`, no el que escribió el código — si aplica esa sección.
- [ ] **Todo test etiquetado «guardarraíl» trae escrita su frase «se pone en rojo si …»** y está EXENTO del rojo previo; los demás tienen su rojo registrado. Sin esa frase la etiqueta no vale y el test se trata como cualquier otro — si aplica esa sección.
- [ ] **El test de integración existe y pasa** — obligatorio si arriba declaraste «Requiere test de integración: sí»; no alcanza con dobles.
- [ ] **Respeta los límites de módulo** (decisión de límites de módulo del Cerebro, `[DEC-…]`): a otro módulo sólo por su `application` (y sus tipos de `domain`/`exceptions`), nunca por su `api` ni su `infra`; el test de arquitectura que lo verifica pasa.
- [ ] Pasa los gates que apliquen (calidad de código: cobertura, duplicación, complejidad, code smells; seguridad: SAST/SCA) sin nuevos hallazgos propios.
- [ ] Respeta convenciones del proyecto y el design system del proyecto si toca UI.
- [ ] Build publicado en el registry del ambiente y verificado en el ambiente que corresponda.
- [ ] Merge Request con descripción y enlazado a la Historia/Característica padre.
- [ ] Si el cambio agrega o modifica una dependencia a instalar, una variable de entorno o un comando para levantar/probar el proyecto, el README.md del repo quedó actualizado en el mismo Merge Request.

**⚠ Datos a confirmar**
<!-- OBLIGATORIA. Si no hay pendientes se escribe "Ninguno." y la seccion se deja igual: una seccion ausente no se distingue de "nadie la miro", que es justo el modo de falla que el chequeo 14 de auditar-tarea existe para tapar. Cada item de aca que afecte a un test tiene que aparecer TAMBIEN marcado con ⚠ adentro del item del test: el que escribe los tests lee la lista, no la tarjeta entera. -->
- <pregunta concreta que tiene que responder un humano, y qué test o validación queda bloqueado hasta que la responda>
- <la que sigue>
<!-- o, si de verdad no hay ninguna, esta linea sola: -->
Ninguno.

### Actividad
```
<Development | Testing | Design | Documentation | Deployment | Requirements>
```

### Esfuerzo original (horas)
```
<N> h
```
<!-- Estimación honesta en horas. Si no lo sabés con certeza, marcá (pendiente) y estimá un rango.
     NUNCA dejes el campo de Azure vacío en silencio: un campo nulo no se distingue de "nadie lo miró"
     y no suma al sprint. Si no hay estimación, escribí 0 en el campo Y dejá la pregunta
     en "Datos a confirmar" — así el hueco es visible en el board, no solo en el texto. -->

### Prioridad
```
<1 | 2 | 3 | 4>
```

### Etiquetas
```
<tema>
```
<!-- UN solo tag, techo duro (<tema>, sin prefijo, siempre igual).
     NO se pone tag de slice: el slice es la Épica.
     NUNCA producto/repo ni versión como tag (si hace falta, va como campo de contenido).
     Ver organizacion-y-trazabilidad §1. -->

### Relaciones / Enlaces
```
- Primario/Parent: <#ID de la Historia/Caracteristica> — <titulo>
- Relacionadas (Related): <#ID de tareas del mismo tema, si aplica>
```
<!-- Toda Tarea debe colgar de una Historia/Característica (Parent). Si no existe, primero creá/identificá la Historia. Los #ID reales son dato duro: se confirman o se resuelven por MCP. Ver organizacion-y-trazabilidad §2. -->

---

## Ejemplo 1 (genérico — tarea simple de UI, sin contrato técnico)

> Recuadro ilustrativo con un dominio neutro (reservas). Es solo un ejemplo; la plantilla de arriba es la que se usa. Al ser una validación de UI sin capa `api`/`application`/`domain`, el bloque "Contrato técnico" se **borra** (opcional, ver nota arriba de esa sección).
>
> **Título:** `Reservas - Validar formato de <documento> en el alta de una reserva`
> **Objetivo:** impedir el alta con `<documento>` de formato inválido, mostrando el error en el campo.
> **Alcance técnico:** aplicación de front (`<repo-front>`), formulario de alta de reserva; validación en cliente.
> **Etiquetas:** `reservas` (una sola).
> **Actividad:** Development · **Esfuerzo:** 6 h · **Prioridad:** 2 · **Parent:** Historia #<ID>.

---

## Ejemplo 2 (genérico — tarea de capa `api`, CON contrato técnico completo)

> Mismo dominio neutro (reservas). Acá la tarea SÍ construye algo que otro código va a llamar (un endpoint), así que el bloque "Contrato técnico" es obligatorio y se completa entero — es lo que le permite a un dev (o a una IA que desarrolla) codear sin ida y vuelta.
>
> **Título:** `Reservas - Crear el endpoint POST /api/reservas/confirmar`
>
> **Objetivo:** exponer el endpoint que confirma una reserva pendiente, devolviendo el estado actualizado o un conflicto si el recurso ya no está disponible.
>
> **Alcance técnico:**
> - Vertical slice / dominio: `reservas`
> - Componente / repo: `<repo-back>` (dentro del slice `reservas`)
> - Capa afectada: backend → `api`
> - Endpoints o entidades involucradas: `POST /api/reservas/confirmar` (ver contrato abajo)
> - No cruza módulos: si necesita datos del recurso, los pide a un caso de uso de la `application` del módulo que lo maneja
> - Fuera de alcance: la lógica de asignación automática de un recurso alternativo si el original ya no está disponible (es otra tarea)
> - Requiere test de integración: `no`
>
> **Contrato técnico (entrada/salida):** — como **fragmento OpenAPI**, que es lo que `armar-swagger` consolida (en prosa no se puede parsear):
>
> ```yaml
> paths:
>   /api/reservas/confirmar:
>     post:
>       summary: Confirma una reserva pendiente sobre un recurso disponible
>       requestBody:
>         required: true
>         content:
>           application/json:
>             schema:
>               type: object
>               properties:
>                 reservaId: { type: integer }
>                 recursoId: { type: integer }
>       responses:
>         '200':
>           description: Reserva confirmada
>           content:
>             application/json:
>               schema:
>                 type: object
>                 properties:
>                   reservaId: { type: integer }
>                   estado:    { type: string }
>         '404': { description: RESERVA_NO_ENCONTRADA }
>         '409': { description: RECURSO_NO_DISPONIBLE }
> ```
>
> **Validaciones:**
> - `reservaId`: obligatorio, entero, debe existir y estar en estado `pendiente` `[RN-RES-0x]` ⚠ número a confirmar
> - `recursoId`: obligatorio, entero, debe existir y estar disponible en el horario de la reserva
>
> **Casos de error:**
> | Condición | Código | Payload | Regla |
> |---|---|---|---|
> | `reservaId` inexistente | `404` | `{ "error": "RESERVA_NO_ENCONTRADA" }` | — |
> | `recursoId` ya no disponible | `409` | `{ "error": "RECURSO_NO_DISPONIBLE" }` | `[RN-RES-0x]` |
>
> **Dependencias:** depende de la tabla `reservas` y `recursos` ya existentes · **de esto depende la Tarea de front `Reservas - Mostrar el resultado de la confirmación` #`<ID>` (Related)**, que es la que cubre la otra mitad del Escenario "Intento de confirmar con un recurso ya tomado" (el mensaje al usuario).
>
> **Especificación cerrada (SDD):**
> - Comportamiento exacto: confirmar una reserva en estado `pendiente` la pasa a `confirmada` y reserva el recurso; si el recurso dejó de estar disponible entre el alta y la confirmación, no se confirma nada `[RN-RES-0x]` ⚠ número a confirmar.
>
> *Escenarios de la Historia que esta Tarea cubre* — la bisagra entre BDD y TDD:
>
> | Escenario de la Historia `#<ID>` | Qué parte cubre esta Tarea | Tests que lo verifican |
> |---|---|---|
> | Confirmación de una reserva pendiente | Todo el escenario: es un flujo puramente de backend | 1, 4 |
> | Intento de confirmar con un recurso ya tomado | El lado servidor (el `409`). El mensaje al usuario lo pinta la Tarea de front | 3 |
> | Confirmación de una reserva inexistente | Todo el escenario | 2 |
>
> **Tests a escribir PRIMERO (TDD test-first):**
> 1. Caso feliz: reserva pendiente + recurso disponible → `200` + `estado: "confirmada"`
> 2. `reservaId` inexistente → `404` + `RESERVA_NO_ENCONTRADA`
> 3. Recurso ya no disponible → `409` + `RECURSO_NO_DISPONIBLE`
> 4. Invariante de negocio protegida: "una reserva ya confirmada no puede volver a confirmarse" `[RN-RES-0x]` ⚠ número a confirmar
>
> **Modos de falla evaluados:**
> - **Estado:** cubierto por el test 4 — una reserva ya confirmada no vuelve a confirmarse.
> - **Concurrencia:** ⚠ sin definir — dos confirmaciones simultáneas de la misma reserva. A confirmar con el equipo antes de codear.
> - **Autorización:** ⚠ sin definir — quién puede confirmar una reserva ajena.
> - **Dependencia caída:** no aplica — el Alcance declara «Requiere test de integración: `no`»; solo lee tablas propias.
> - **Límites:** no aplica — la entrada es un único identificador, sin listas ni rangos.
> - **Idempotencia:** cubierta por el test 4 — confirmar dos veces no produce un segundo efecto.
>
> *(No lleva test de integración porque el Alcance técnico declara «Requiere test de integración: `no`» — no toca ninguna dependencia externa. Si dijera `sí`, acá iría el test 5, más su subtarea y su ítem en el DoD.)*
>
> *(**Tampoco lleva guardarraíl, y es a propósito.** Los cuatro tests salen del contrato y de las
> reglas: los cuatro pueden estar en rojo antes de que exista el endpoint, así que ninguno
> necesita la exención. El punto 4 es una **invariante de negocio**, no un guardarraíl: lleva su
> rojo previo como los otros tres. Una Tarea sin guardarraíl es lo normal; agregar uno para
> "completar la plantilla" es exactamente el error que [[auditar-tarea]] marca.)*
>
> **Resultado entregable:** Merge Request mergeado con el endpoint funcionando en <ambiente de prueba> y el fragmento OpenAPI publicado en el `openapi.yaml` del slice.
>
> **Etiquetas:** `reservas` (una sola) · **Actividad:** Development · **Esfuerzo:** 8 h · **Prioridad:** 2 · **Parent:** Historia #<ID>.
