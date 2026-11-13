---
id: orquestador-desarrollo
tipo: guia
estado: F-Draft
modulo: general
title: "Orquestador de Desarrollo — diseño"
tags: [agentes, orquestacion, desarrollo, tdd]
last_updated: 2026-10-08
author: "equipo"
---

# Orquestador de Desarrollo — diseño

## Propósito

Toma **Tareas ya listas** del tablero y las hace **programar en paralelo** por varios
agentes, cada uno aislado, con disciplina de test-primero y una **verificación
independiente** al final. Termina en un Merge Request por Tarea, y con un comentario de cierre
en cada Tarea que cuenta qué rama, qué Merge Request y qué se hizo.

> **No confundir con [[cerebro-orquestador]]**, que coordina el **conocimiento**
> (documento → Cerebro Digital → tickets). Este arranca **donde aquel termina**: agarra
> las tarjetas listas y las convierte en código.

## Precondición (dura)

Solo entran Tareas que pasaron el **DoR de "lista para desarrollar"** (con su «Modo de pruebas» declarado: TDD por defecto) (ver
[[redactar-tarea]] §3.1), que son **cuatro** piezas: **contrato cerrado**,
**«Especificación cerrada (SDD)»** con la tabla que mapea los Escenarios del Gherkin de la
Historia padre a los tests, la **lista numerada de "Tests a escribir PRIMERO"** y el bloque
**«Modos de falla evaluados»**.
Una Tarea sin esas piezas **no se despacha** — se devuelve al armado de la tarjeta. Un `⚠`
declarado en «Datos a confirmar» **no** la deja afuera: se despacha, y lo que depende de ese
punto queda como pendiente.

**La auditoría no es precondición** (decisión de diseño). [[auditar-tarea]] y
[[auditar-historia]] son opcionales: corren sólo si alguien las pide, y su sello no se busca
antes de despachar. Exigirlas gastaba muchos tokens y volvía a preguntar cosas ya cerradas o
que no hacían falta para arrancar. Un hueco o un gris que aparezca al programar **no frena ni
se vuelve a preguntar**: el worker no lo inventa, hace lo demás y lo devuelve como pendiente,
que queda en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar») y se revisa antes de cerrarla.

## Entradas y salidas

| Entra | Sale |
|---|---|
| Tareas listas del tablero | Un Merge Request por Tarea |
| Contrato consolidado del slice (`openapi.yaml`) | Evidencia de rojo/verde **auditada** |
| Repositorios de código (back / front) | Reporte de lo que **no** cumplió, como hallazgos |
| | Un **comentario de cierre** en cada Tarea: rama, Merge Request y resumen técnico |

## Ciclo por Tarea

| # | Paso | Quién |
|---|---|---|
| 1 | Tomar la Tarea (asignar y pasar a Active). Si **ya es de quien la va a programar** y está en Active, no se escribe nada. Si la tiene **otra persona**, está en el sprint y su Estado no es `New`, está congelada: se frena y se coordina, no se reasigna | orquestador — ver [[tomar-tarea]] |
| 2 | Abrir un **espacio de trabajo aislado** (un worktree por Tarea), con los datos duros de `bin/gate-worktree.py` a la vista | orquestador |
| 3 | Despachar el worker con **misión autocontenida** (la arma `bin/armar-mision.py`: una sola plantilla para Orca e IntelliJ, con la Tarea completa, el Gherkin del padre y las convenciones copiadas) + sus skills **explícitas**. Antes, **base al día**: `fetch` y, si `develop` avanzó, se trae con merge (§«Reglas de diseño») | orquestador |
| 4 | Ciclo rojo → verde → refactor, con **evidencia del rojo** | worker (`guiar-tdd`) |
| 5 | **Auditoría independiente** de la evidencia: ¿el ciclo ocurrió? | otro agente (`verificar-tdd`) |
| 5-bis | **Calidad del código** (corrección, limpieza, convenciones) | otro agente, con `code-review.md` de `desarrollo` (revisión por dimensiones) en cualquier motor; en Claude Code `/code-review` es un atajo válido |
| 5-ter | **Chequeos de entrega**: contrato de la Tarea, límites de módulo, tests cubiertos, **sin PHI ni secretos** | otro agente (`auditar-codigo`) |
| 5-quater | **Convenciones del Cerebro**, una por una (§«Convenciones del Cerebro: reglas que se chequean») | el mismo verificador |
| 6 | Merge Request; decide el humano | orquestador + humano |
| 7 | **Comentario de cierre** en la Tarea: rama, Merge Request y resumen técnico, con los veredictos de 5, 5-bis, 5-ter y 5-quater, y los **pendientes a confirmar** que devolvió el worker | orquestador, con el resumen del worker — ver [[comentar-tarea]] §«Comentario de cierre de desarrollo» |
| 7-bis | **Retroalimentación al Cerebro**, cada cosa a su lugar y nada se queda en el chat. (a) Lo que la Tarea **confirmó o descubrió del negocio** (una respuesta del humano a un pendiente, una regla que el código tuvo que precisar, un estado que no estaba escrito) pasa por la Consulta Interactiva de Decisión de [[cerebro-orquestador]] y, con el «sí», lo persiste `cerebro-curator` en `funcional/` o `decisiones.md`. (b) Lo que mostró de **la aplicación** va a `<modulo>/aplicacion/`: la fila de `mapa.md` (módulo tocado, qué expone, `#ID`, Merge Request; los datos salen de `datos-cierre.py`, no de memoria), un `AP-nnn` en `aprendizajes.md` si hubo un bug con causa, una trampa del stack o un patrón que conviene repetir, y un `DT-nnn` en `deuda.md` por lo que se dejó a propósito. (c) Lo que mostró del **ecosistema** va a [[mejorar-ecosistema]] | orquestador + humano |
| 8 | **Resumen al humano**: qué se hizo y qué quedó pendiente, siempre, termine bien o mal | orquestador — ver §«Resumen al terminar cada Tarea» |

> **El paso 7 no cambia el Estado de la Tarea.** Desde el paso 1 la Tarea está en un sprint y
> tomada, o sea **congelada**: sólo se comenta ([[cambios-en-el-backlog]] §4). Pasarla a
> *Resolved* o *Closed* lo decide una persona, y antes se le muestran los pendientes sin
> resolver de los comentarios ([[comentar-tarea]] §«Antes de cerrar una Tarea»). La única
> excepción es *Resolved* en modo solo con `DEC-005` confirmada ([[desarrollar-asignadas]] 6.3). Y los **datos duros** del comentario salen del
> repositorio —`git`, el Merge Request leído de GitLab en sólo lectura, los veredictos que
> devolvieron los controles—, nunca de la memoria del worker. Del resumen del worker sale sólo
> la prosa, y sólo si no hay Merge Request de donde leerla. Lo que no se pudo leer va
> `⚠ sin dato`.

**Quién contesta qué (tabla única; las skills la citan, no la copian):**

| Quién | La pregunta que contesta |
|---|---|
| `verificar-tdd` | **¿El ciclo ocurrió?** Hubo rojo en la aserción antes del código; el verde pasa hoy |
| `code-review.md` (`/code-review` en Claude Code) | **¿El código está bien escrito?** Corrección, limpieza, reuso, convenciones |
| `auditar-codigo` | **¿La entrega cumple lo que este pipeline exige?** Contrato de la Tarea, límites del módulo, tests cubiertos, sin PHI ni secretos |
| `diagnosticar-repo` | **¿El repo está sano?** Árbol en reposo, capa de skills, tendencia |
| `auditar-tarea` / `auditar-historia` | **¿La tarjeta está bien escrita?** Le falta un test / el Gherkin es verificable (a pedido) |

> **Los tres controles responden preguntas distintas y no se reemplazan.** `verificar-tdd`
> contesta *¿el ciclo ocurrió?* (hubo rojo en la aserción antes del código, el verde pasa hoy).
> `/code-review` contesta *¿el código está bien escrito?*. `auditar-codigo` contesta *¿la entrega
> cumple lo que este pipeline exige?* — contrato de la Tarea, límites del módulo, cobertura de la
> lista de tests y **PHI/secretos en el diff**, que es lo único que ningún revisor genérico puede
> mirar, porque no conoce la Tarea ni los marcadores.
>
> Un cambio puede tener **TDD impecable, estar bien escrito y no cumplir la entrega** — por
> ejemplo, con un `<persona>` real filtrado en un fixture. Por eso son tres preguntas, no una.
> **El 5-ter no se saltea aunque el 5-bis haya salido limpio.**

> **El Doctor (`diagnosticar-repo`) NO entra en este ciclo.** Es **periódico y manual** (por hito),
> nunca por Tarea. Cablearlo acá lo convertiría en el mayor consumidor del pipeline: se ejecutaría
> una vez por cada Tarea despachada. Contesta una tercera pregunta — *¿el repo está sano?* — que es
> sobre el árbol en reposo, no sobre un cambio.

> **Al cerrar un slice o la aplicación** (no por Tarea), [[documentar-aplicacion]] genera desde el Cerebro la guía de
> uso y la documentación técnica y funcional (`bin/generar-documentacion.py`), con las pantallas de Stitch y los
> diagramas de Archify. Es el entregable de cierre, junto con el informe del Doctor.

## Formato del veredicto (canónico, para toda la cadena)

Los cinco controles y el resumen usan **un solo bloque**, que `desarrollar-asignadas` (en sus dos modos, con y sin Orca)
lee tal cual de la salida del verificador; `bin/armar-mision.py` se lo pide así al verificador:

```
VEREDICTO-INICIO
5        verificar-tdd   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <OK/HALLAZGO/SIN DATOS>, criterio: <…>
5-bis    code-review     : OK | HALLAZGO | SIN DATOS (<motivo>)
5-ter    auditar-codigo  : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <…>
5-quater C1..C8          : C1 <OK|HALLAZGO|SIN DATOS|N/A> · C2 … · C8 SIN DATOS (pendiente DEC-003)
5-quinquies paridad      : OK | HALLAZGO | SIN DATOS (<motivo>) | N/A (la Tarea no es de un slice en modernización)   -- script: paridad.py comparar
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <motor> v<versión> · <modelo>
VEREDICTO-FIN
```

Debajo, un hallazgo por línea: `archivo:línea — qué — por qué frena o no`, y para el control 5 una línea por ítem de la
lista con la aserción citada. **`N/A`** vale para un control o una convención que la Tarea no toca (C5 sin capa
`api`; el chequeo del fragmento OpenAPI en una Tarea de `domain`): no es `SIN DATOS` ni `OK`, y no frena. **Dos clases de `SIN DATOS`:**
«no se pudo mirar» (el script no corrió, la suite no se ejecutó, falta la evidencia) **frena**; «pendiente
declarado» (C8, SAST, cobertura, la guía del stack sin completar: lo que una `DEC-nnn` todavía no fijó) **se
lista y no frena**, porque ya está a la vista en el Cerebro y frenar por eso dejaría todo parado hasta
`DEC-003`. Sin esta distinción ninguna Tarea se aprobaría nunca en automático. Cada pregunta tiene **un solo
control**: el ciclo TDD lo mira 5 y nadie más; la calidad, 5-bis; la entrega, 5-ter; las convenciones, 5-quater.

## Commits: de trabajo, y pocos en el Merge Request

**En el Merge Request los commits se agrupan por importancia: uno por cambio lógico.** Por
ejemplo: el dominio con sus tests, el endpoint con sus tests, la migración, el componente de
front, el README. Cada mensaje es **específico** y explica por qué (`metodo/ramas-y-commits.md`
de [[desarrollo]]): nunca «wip», «avance» ni un commit por test.

**Alrededor de 10 commits por Tarea es una guía, no un techo obligatorio** (decisión de diseño). Si la Tarea lo pide pueden ser 15; si se cuenta bien en 3,
son 3. Lo que se evita es una rama con 20 o 30 commits chicos: un cambio chico se junta con el
resto de su cambio lógico.

La evidencia del rojo no se pierde por eso. Va así:

1. **Mientras programa**, el worker hace los commits chicos de TDD (`test(rojo): …` y su verde)
   en su rama: son commits de trabajo y **no van al Merge Request**.
2. **La verificación** (`verificar-tdd`) corre sobre ese historial de trabajo, antes de tocarlo,
   y la hace un agente distinto del que programó.
3. **Con el "Aprobar" del humano, antes del push**, se reorganiza la rama. El "sí" lo nombra:
   *«…subo el respaldo `evidencia/<ID>`, reorganizo la rama en N commits y pusheo la rama de la
   Tarea»*.
   - se guarda el historial de trabajo en una rama de respaldo, `git branch evidencia/<ID> HEAD`,
     y **se sube a `origin`** (`git push -u origin evidencia/<ID>`), **sin Merge Request**: así
     quien revisa puede ver cada `test(rojo)`. Si ya existe —una segunda entrega de la misma
     Tarea—, va `evidencia/<ID>-2`, `-3`…: **nunca** `-f`, que pisaría la evidencia;
   - se confirma que la base es ancestro de la rama (`git merge-base --is-ancestor <sha-base>
     HEAD`); si no lo es, se frena y se avisa: reorganizar arrastraría trabajo ajeno;
   - se rehace la rama desde la base: `git reset --mixed <sha-base>`, y se commitea **por
     cambio lógico** (`git add <archivos de ese cambio>` + commit), alrededor de 10;
   - **chequeo obligatorio:** `git diff evidencia/<ID> HEAD` tiene que salir **vacío**. Si no,
     se perdió o se agregó algo al reorganizar: se frena, se vuelve a `evidencia/<ID>` y se
     avisa.
4. **La rama de la Tarea** (`task/<ID>-…`) se pushea y se mergea a `develop` **sin squash**.
5. El comentario de cierre y la descripción del Merge Request dicen el veredicto de
   `verificar-tdd`, cuántos commits de trabajo tenía la rama y en qué rama de respaldo están
   (`evidencia/<ID>`, en `origin`).

**Sólo se reorganiza lo que nunca se pusheó.** Una rama ya subida no se reescribe. Si hay un
**ajuste después del push** (por ejemplo, de la revisión del Merge Request), los commits de TDD
nuevos se verifican sobre su tramo, `origin/<rama>..<rama>`, y **sólo ese tramo** se reorganiza
antes del siguiente push, con su propio respaldo `evidencia/<ID>-2`, también en `origin`. La
evidencia de lo anterior sigue en `<sha-base>..evidencia/<ID>`.

**Antes de abrir o actualizar el Merge Request, la rama contiene lo último de la base.** Rige
la «Base al día» ([[desarrollar-asignadas]] §6, [[desarrollar-asignadas]] §«Modo sin Orca» §7): `fetch`, y si
`develop` avanzó se trae **con merge, nunca rebase** (la rama ya se pusheó), con la suite
completa y un nuevo SHA de base; el audit pasa a ser `<nuevo-sha-base>..<rama>`.

**La rama de la Tarea y sus ramas `evidencia/<ID>` no se borran del servidor hasta que termina
el sprint.** Borrarlas lo decide una persona, con un "sí" sobre lo mostrado: qué ramas son, de qué
Tarea, que el Merge Request ya se mergeó y que **al borrar `evidencia/<ID>` el historial de
trabajo con los `test(rojo)` se pierde**.



## Convenciones del Cerebro: reglas que se chequean

La misión de cada worker **no** le pasa las convenciones «para leer»: se las pasa como **reglas
duras**, una por línea, y el verificador las chequea **una por una** (control 5-quater). Sin esto,
el worker lee, interpreta y cada uno estructura distinto. Salen de
`arquitectura/esqueleto-proyectos.md` §«Convenciones de código» (back y front); si cambian ahí, cambian acá.

| # | Regla | Cómo se chequea |
|---|---|---|
| C1 | Estructura del módulo ([[decisiones#DEC-002]]): `<modulo>/{api,application,domain,infra,exceptions}` + `shared/`. Toda regla de negocio en `<modulo>/domain`; `application` con una clase por caso de uso (recibe un comando, nunca un DTO de `api`), las interfaces a externos y a la base propia declaradas en `application` e implementadas en `infra`; `domain` sin dependencias del framework. Sin carpetas por tipo técnico (`util`, `model`, `service`, `impl`) | Una regla de negocio fuera de `domain`, un caso de uso que recibe un DTO de `api`, o un paquete por tipo técnico, es HALLAZGO |
| C2 | Los errores del módulo viven en `<modulo>/exceptions` y el código de respuesta HTTP lo decide **un único** traductor de errores transversal (`shared`), con un formato de error único para toda la API; ningún adaptador HTTP mapea errores por su cuenta | Una excepción en otro paquete, o un adaptador que traduce errores a códigos HTTP, es HALLAZGO |
| C3 | Idioma de los nombres: en español **sólo** los sustantivos del negocio que están en la base; verbos, roles técnicos y técnica en inglés. Nombres de tests con la misma regla; los textos visibles, los comentarios y los mensajes, en español. Campos del contrato y de la base, en español. Sin tildes ni ñ en los nombres. Si el contrato de la Tarea fija un nombre, gana el contrato; si el esqueleto del repo ya nombra en español, manda el esqueleto (y el contrato lo sigue), y ese estilo cubre **todo el archivo**, también las funciones privadas: coherencia antes que regla. Las descripciones de los tests (`it('…')`, nombres legibles del reporte) y las docstrings son texto visible: en español | Un sustantivo del negocio en inglés, un verbo técnico en español, una tilde o ñ en un nombre, o un comentario en inglés, es HALLAZGO |
| C4 | Documentación resumida en español (1 a 3 líneas) arriba de cada clase de producción: qué es, para qué está en el módulo y qué `[RN-…]` o decisión implementa. Los métodos largos o complejos llevan una línea; las clases de test, una línea con qué prueban; los endpoints y métodos simples, nada | Una clase sin su resumen, un resumen en inglés o uno que repite el nombre, es HALLAZGO menor. Un atajo deliberado se marca con **una** línea `atajo: <límite>; cuando <disparador> <#ID o DT-nnn>` (`refactor.md` de `desarrollo`, §«Deuda técnica») y, además, va a la descripción del Merge Request y como pendiente a confirmar en la tarjeta. En las líneas que agrega el diff, una marca sin límite o sin `cuando …` es HALLAZGO menor |
| C5 | Un solo contrato: el `openapi.yaml` acordado; la documentación viva de la API sirve ese mismo archivo | Un endpoint o campo distinto entre el código y el `openapi.yaml` es HALLAZGO. Se valida con el linter de OpenAPI (Spectral) y el ruleset `bin/spectral-oas.yaml` del repositorio del Cerebro |
| C6 | Si el repo contradice al Cerebro, manda el Cerebro | Un `docs/ARCHITECTURE.md` o `README.md` que diga otra cosa es HALLAZGO, y se corrige en el mismo Merge Request |
| C7 | Una Tarea **modifica un solo módulo** (puede **usar** otro, sólo por su `application`). Entre módulos se llama sólo a `<otro>.application`; se pueden importar los tipos que esos casos de uso devuelven o lanzan (`<otro>.domain`, `<otro>.exceptions`); entidades de otro módulo se referencian por id ([[decisiones#DEC-002]]) | Un import de `api` o `infra` de otro módulo, o un diff que modifica dos módulos, es HALLAZGO |
| C8 | ⚠ **A completar por el equipo con las convenciones propias del stack** (anotaciones permitidas, inyección de dependencias, tareas programadas, política de librerías de utilidad). Se escriben en `arquitectura/esqueleto-proyectos.md` §«Convenciones de código» y se copian acá una vez decididas | Hasta que exista, el verificador reporta C8 como `SIN DATOS (pendiente DEC-003)`: se lista y no frena; nunca OK |

En el **front** valen C3 a C6 y las reglas que el equipo escriba en `arquitectura/frontend/` (si el proyecto tiene front).

**Antes de despachar** el orquestador también chequea:
- que el Cerebro de `develop` esté al día con `main` (`git fetch` y después `git log --oneline
  origin/develop..origin/main -- cerebro-digital` vacío). Si no, se avisa: los workers leerían reglas viejas;
- que el `docs/ARCHITECTURE.md` del repo destino no contradiga estas reglas (C6). Si contradice,
  se avisa y la Tarea lo corrige;
- que dos Tareas del lote no toquen los mismos archivos (por lo que declara cada una: componente,
  clases, endpoints). Si los tocan, van en serie, o se avisa del conflicto;
- que ninguna Tarea vaya a superar los 20 archivos del método: si sí, se avisa (conviene partirla).

## Resumen al terminar cada Tarea

**Cuando termina el trabajo de cada Tarea, el orquestador le da al humano un resumen, siempre**:
termine bien, se frene o falle. Y al terminar el lote, una tabla con todas. Es lo que el humano
lee para saber qué pasó sin abrir el worktree ni la tarjeta:

> **#NNNN ‹título›** — terminada · frenada · falló
> - **Qué se hizo:** rama, Merge Request (o «todavía no abierto»), cantidad de commits, tests
>   «N de M» de la lista, archivos o capas tocadas, qué cambió del README.
> - **Verificación:** quién verificó, siempre con el formato «‹motor› v‹versión› · ‹modelo o worktree›» —por ejemplo,
>   «Gemini CLI v0.62.0 · gemini-2.5-pro»— y el veredicto de cada control
>   (`verificar-tdd`, revisión de código, `auditar-codigo`): OK · HALLAZGO · SIN DATOS.
> - **Pendientes a confirmar:** los de este desarrollo y los que ya había sin resolver en la
>   tarjeta, uno por línea; o «Ninguno».
> - **Qué falta:** lo que sigue y quién lo hace (revisar y mergear el Merge Request, pasar la
>   Tarea a otro Estado —lo decide una persona—, Tareas bloqueadas que se destraban).
> - **Mejoras detectadas:** lo que esta Tarea mostró del propio ecosistema (una convención que no se
>   pudo cumplir, un control siempre `SIN DATOS`, una pregunta repetida), registrado como propuesta en
>   `configuracion-ia/mejoras.md` por [[mejorar-ecosistema]]; o «Ninguna». Se pregunta aparte, de a una.
> - **Conocimiento para el Cerebro:** lo que esta Tarea confirmó o descubrió del negocio, un renglón
>   por ítem con su destino (ficha, decisión, pendiente resuelto), para la Consulta Interactiva de
>   Decisión; o «Nada nuevo».
> - **Memoria de la aplicación:** la fila de `aplicacion/mapa.md` (módulo, qué expone, `#ID`, Merge
>   Request) y, si los hubo, el `AP-nnn` (qué pasó, causa, qué cambió) y el `DT-nnn` (qué se dejó,
>   cuándo se paga); o «Sin cambios en el mapa».

Los datos salen del repositorio, de GitLab y de los veredictos, no de la memoria del worker; lo
que no se pudo leer va `⚠ sin dato`.

## Reglas de diseño (cerradas)

| Regla | Por qué |
|---|---|
| **El orquestador coordina, no ejecuta** | Rutea y adjudica; el trabajo lo hacen los workers ([[cerebro-orquestador]] §«Orquestación de sub-agentes») |
| **Misión autocontenida** | El worker recibe objetivo + rutas + resultado esperado; el padre recibe solo el resumen final. Evita inflar el contexto |
| **Las skills se pasan explícitamente** | No se heredan al delegar. Un worker sin `guiar-tdd` trabaja sin disciplina y **todo parece correcto igual** ([[cerebro-orquestador]] §«Herramientas y skills NO se heredan») |
| **Paralelo solo si es independiente** | Las dependencias van en serie. Back y front pueden ir en paralelo **porque el contrato ya está cerrado en la Tarea** |
| **Quien verifica ≠ quien produce** | Si el mismo agente codea y se aprueba, no hay control: hay una declaración. Verifica otro agente, en sólo lectura y sobre el mismo worktree: el otro LLM si hay dos; uno del mismo motor con contexto limpio si hay uno (`DEC-005`) |
| **El orquestador queda atento** | Delegar no es irse: escucha a los workers hasta que el último termina, contesta sus preguntas al llegar y le avisa al humano de cada uno que termina. Si deja de escuchar, el aviso de terminado se pierde y el flujo se corta |
| **Base al día antes de enviar** | Todo lo que se envía contempla lo último de la base, sin importar cuándo se empezó: antes de despachar un worker o verificador (también sobre un worktree existente) y antes de abrir o actualizar el MR se hace `fetch`, y si `develop` avanzó se trae con merge —nunca rebase—, se corre la suite completa y se anota el nuevo SHA de base. Si el conflicto cambia comportamiento o la suite se pone en rojo, se frena. Caso real: un ajuste sobre una rama con base vieja dejó el MR en conflicto con otro ya mergeado ([[desarrollar-asignadas]] §6, [[desarrollar-asignadas]] §«Modo sin Orca» §7) |
| **Todo en español** | Cada misión lo dice: un sub-agente no hereda el idioma de la conversación |
| **Umbrales de parada** | Cuándo delegar, auditar o replanificar sale de [[cerebro-orquestador]] §«Orquestación de sub-agentes», no del criterio del momento |

## Lo que NO hace

- **No escribe código de producción** — eso es del worker.
- **No autoriza la entrega.** La evidencia no reemplaza al humano ni a la política del repo.
- **No crea ni modifica Tareas** — eso vive del lado tarjeta ([[redactar-tarea]], [[sincronizar-backlog]]).
  Sobre la tarjeta escribe **dos veces y nada más**: al tomarla (paso 1) y el comentario de
  cierre (paso 7). Si alguien pide una auditoría, su sello lo postea [[auditar-tarea]], no el
  orquestador.
- **No consulta el Cerebro Digital** salvo pedido explícito (para eso está `consultar-cerebro`
  en cada repo de código, que trae **una** ficha).

## Dudas y Preguntas

- ✅ **¿Dónde se instala?** **CERRADO: repositorios separados** — uno de back y uno o más
  de front, uno por aplicación. Cada uno se clona adentro de la carpeta que le
  corresponde (`back/<nombre>`, `front/<nombre-de-la-app>`), y ahí el orquestador trabaja con
  el código, las reglas del proyecto y la Tarea a la vista en una sola sesión.
  *Lo que esto define:* el orquestador vive en el repositorio raíz, no adentro de cada repo de
  código. Las skills scoped (`guiar-tdd`, `verificar-tdd`, `auditar-codigo`) sí viven en cada
  carpeta y aplican a lo que se clone adentro.
- ✅ **¿Cuántos workers en paralelo por máquina?** **CERRADO: entre 4 y 8, nunca más.**
  Pasado ese punto la máquina se arrastra y los runners de test compiten entre sí: el
  paralelismo empieza a costar más de lo que ahorra. El asistente dice cuántos hay abiertos
  antes de crear otro, y **frena en el noveno**.
  *Detalle y el resto de las barreras:* **GATE de WORKTREE** en `AGENTS.md`.
- ✅ **¿Cómo se persiste la evidencia del rojo?** **CERRADO: un commit por paso rojo, local.**
  El worker commitea `test(rojo): <n.º de ítem> <resumen>` con **solo el test**, y después
  el commit de la implementación. `verificar-tdd` lo comprueba con `git log`: el commit del
  test tiene que ser **anterior** al de su implementación. **Actualización:** esos
  commits son de trabajo y no van al Merge Request; antes del push la rama se reorganiza por
  importancia (alrededor de 10 commits, como guía) y el historial de trabajo queda en la rama
  `evidencia/<ID>`, subida a `origin` sin Merge Request (§«Commits: de trabajo, y pocos en el Merge Request»).
  *Por qué esta y no las otras tres opciones:* archivo en el worktree, comentario en la
  Tarea o artefacto del pipeline son las tres **texto pegado**, y un texto pegado es
  indistinguible de un rojo fabricado — comentar la implementación, correr el runner, pegar
  la salida roja y descomentar produce el mismo artefacto. El orden de los commits es un
  **dato duro del repo**, no se puede escribir desde el chat, y verificarlo es una línea de
  comando en vez de criterio de un modelo. No necesita nada de Infraestructura.
  *Lo que sí cambia:* los devs commitean más seguido **en local**. Se reorganiza antes del push,
  **nunca antes de que `verificar-tdd` haya corrido**, y con el respaldo `evidencia/<ID>`.
- ⚠ **¿Qué pasa si dos Tareas tocan el mismo archivo?** Regla candidata: serializarlas
  (dejan de ser independientes). A confirmar con el equipo. Queda escrita como candidata en el
  **GATE de WORKTREE** de `AGENTS.md`, para que si se aplica sea por decisión y no por olvido.
