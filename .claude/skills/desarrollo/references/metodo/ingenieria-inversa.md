# Ingeniería inversa de una aplicación — sacarle todo lo que sabe

> Método propio. Es el "cómo" de la lectura de [[absorber-aplicacion]] (fases 1 y 2), y vale solo: se
> puede usar para **documentar** una aplicación sin tocarla, sin decidir refactor ni migración. Lo que
> sigue después (caracterización, paridad, estrangulador) está en
> [refactor-y-migracion.md](refactor-y-migracion.md). Toma la forma que hoy usan los frameworks de
> *reverse documentation* para agentes (reconocimiento → excavación por módulo → interpretación → revisión,
> con marca de confianza por afirmación y trazabilidad al código en los dos sentidos), con dos
> diferencias: los hechos los saca un script, y nada entra al Cerebro sin un "sí" por ítem.

## La pregunta que contesta

**¿Qué sabe esta aplicación que nadie escribió?** Reglas que viven en un `if`, estados que sólo
existen en un `enum`, integraciones que sólo aparecen en un `application.yml`, permisos que sólo
están en una anotación, umbrales que son una constante con nombre. Todo eso es conocimiento del
negocio, y la única copia está en el código.

## Las fuentes, en orden

| # | Fuente | Qué da | Quién lo saca | Qué NO se hace |
|---|---|---|---|---|
| 1 | **Inventario** | Qué hay: lenguajes, build, pipeline, contratos, migraciones, tests, deuda | `bin/inventariar-codigo.py` | Describirlo de memoria |
| 2 | **Radiografía** | Dónde mirar: endpoints, entidades y tablas, enums y campos de estado, pantallas, reglas candidatas, integraciones, permisos, dependencias entre módulos; **cada hecho con `archivo:línea`** | `bin/radiografiar-codigo.py` | Tomar una regla candidata por regla |
| 3 | **Lectura por módulo** | Qué hace cada cosa: el flujo entero (api → application → domain → infra), los tests, el historial | La skill, con [entender-codigo-ajeno.md](entender-codigo-ajeno.md), **empezando por lo que la radiografía señaló** | Leer todo antes de empezar; resumir un módulo sin abrirlo |
| 4 | **Contrato y tests existentes** | Lo que la aplicación promete y lo que alguien consideró importante | Lectura; los tests son la única documentación que no envejece | Inventar un contrato: si no hay, se saca del código viejo |
| 5 | **Base de datos** | Estados **reales** (valores distintos de una columna de estado), volúmenes, tablas que nadie usa, columnas vacías | Consultas de **esquema y conteo** acordadas con una persona | Copiar filas, exportar datos, mirar una tabla con datos de personas; **nunca PHI** |
| 6 | **Runtime: logs, tráfico, métricas** | Qué endpoints se usan de verdad, qué errores pasan, qué jobs corren | Lo que quien administre el ambiente pueda dar, agregado (en modo solo, vos) | Pedir accesos de producción por iniciativa propia |
| 7 | **Personas** | El porqué, lo que el código no contesta | Las preguntas que salen de 1–6, **juntas y numeradas** | Preguntar lo que el historial de git ya contesta |

Las fuentes 5 y 6 son opcionales y **requieren un "sí"** antes de tocarlas; sin ellas el veredicto de
esa parte es `SIN DATOS`, no "no se usa".

## La marca de confianza, por afirmación

Cada afirmación del borrador lleva una de tres marcas, y la marca decide qué puede pasar con ella:

| Marca | Qué significa | Cómo entra al Cerebro |
|---|---|---|
| **CONFIRMADO** | Sale directo del código y se cita con `archivo:línea` (o del DDL, el contrato o un test) | Puede entrar como dato o como `RN-<MOD>-nnn` **con el "sí"**, con la fuente `[DOC-nn] Código de <app>, commit <sha>` en `fuentes.md` |
| **INFERIDO** | Se deduce de un patrón (un nombre, una convención, una ausencia) y puede estar mal | Entra sólo como candidata `⚠`, con la pregunta que la cierra |
| **HUECO** | El código no lo contesta (una rama muerta, un comportamiento sin test, un módulo que nadie leyó) | `pendientes.md` como `P-nnn`; **nunca** se rellena con una suposición |

**Un módulo que la radiografía lista y nadie leyó es HUECO, no "sin reglas".** Es la diferencia
entre "no hay" y "no miré", y la matriz de cobertura (abajo) lo hace visible.

## La evidencia de una regla candidata

Una regla sacada del código se presenta así, siempre, antes de la Consulta Interactiva de Decisión:

```
Regla candidata RC-nn  ⚠ INFERIDO
Qué dice:      <en criollo: "una reserva no puede superar 30 días">
Dónde:         src/.../ReservaResource.java:17  (y la constante MAX_DIAS, :8)
Fragmento:     <10 a 20 líneas, las suficientes para que una persona la lea sin abrir el archivo>
Test que la cubre:  <ReservaResourceTest.noSuperaTreintaDias, o "sin test">
Lo que no sé:  <si el 30 es una regla del negocio o un parche; si aplica a todas las sucursales>
Pregunta:      <una sola, cerrada>
```

Sin fragmento y sin `archivo:línea` **no es una regla candidata: es una impresión**, y no se presenta.
Una regla con test se confía más que una sin test, pero **ninguna se confirma sola**: el código puede
estar mal, y alguien puede depender de ese error.

## Trazabilidad en los dos sentidos

- **Del Cerebro al código:** cada `RN`, `DEC` o dato que salió de la absorción cita `[DOC-nn]` (el
  commit inventariado) y el `archivo:línea`. Así, cuando el código cambie, se sabe qué ficha mirar.
- **Del código al Cerebro: la matriz de cobertura.** Una tabla con **cada módulo de la radiografía**
  y qué pasó con él: leído (qué borrador), parcialmente leído (qué quedó afuera), no leído (HUECO).
  Es el entregable que dice si la ingeniería inversa terminó o se cansó.

| Módulo (radiografía) | Archivos | Endpoints | Entidades | Reglas candidatas | Borrador | Estado |
|---|---|---|---|---|---|---|
| `reservas` | 42 | 6 | 3 | 11 | `02-reservas.md` | leído |
| `reportes` | 17 | 2 | 0 | 4 | — | **HUECO: no leído** |

## Qué sale, y adónde va

| Lo que se encontró | Dónde queda en el Cerebro |
|---|---|
| Entidades, estados, roles, flujos, reglas confirmadas | `funcional/<ficha>.md` (con `## Derivación a backlog` propuesto `⚠`) |
| Reglas candidatas sin confirmar, huecos | `pendientes.md` (`P-nnn`) |
| Integraciones y ambientes reales, módulos y qué expone cada uno | `aplicacion/mapa.md` |
| Decisiones implícitas (estructura, patrones, librerías) | `arquitectura/decisiones.md` como `DEC-nnn` `⚠` |
| Deuda, secretos en el repo, cruces de capa, ciclos | `aplicacion/deuda.md` (`DT-nnn`) |
| Trampas del stack y bugs con causa que la lectura reveló | `aplicacion/aprendizajes.md` (`AP-nnn`) |
| Preguntas a las personas | El turno de preguntas, numeradas; lo que no se contesta, `P-nnn` |

## Lo que NO se hace

- **No se modifica la aplicación, ni se instala nada en ella.** Si se clona, afuera de este repositorio.
- **No se copian datos.** De la base salen esquemas, conteos y valores distintos de columnas de
  estado, acordados; de los logs, agregados. Nada que identifique a una persona.
- **No se infiere una regla de un bug.** Un comportamiento raro es una pregunta.
- **No se "resume" un módulo sin abrirlo.** La radiografía señala; no reemplaza la lectura.
- **No se arranca a leer antes de que la radiografía corra.** Sin ella, la lectura es a ciegas y la
  cobertura no se puede medir: `SIN DATOS`.

## Cuándo conviene una herramienta de afuera

La radiografía propia es biblioteca estándar, corre en segundos y alcanza para arrancar en cualquier
stack con expresiones regulares. Conviene algo más cuando la aplicación es grande y hace falta un
**grafo real** (llamadas, no sólo imports) o **diagramas** generados:

| Necesidad | Tipo de herramienta | Qué mirar antes de usarla |
|---|---|---|
| Grafo de dependencias y endpoints con análisis sintáctico real, deriva de arquitectura entre dos commits | Servidores MCP de arquitectura sobre tree-sitter (p. ej. Ridge, CodeGraphContext) | Lenguajes que soporta; qué se manda afuera |
| Pipeline completo de agentes que produce especificaciones (inventario, diccionario de datos, máquinas de estado, permisos, diagramas C4, matriz de trazabilidad, huecos y preguntas) | Frameworks de *reverse documentation* (p. ej. Reversa, `document-project` de BMAD) | Necesitan Node; sus salidas son un **borrador más**, que pasa por la Consulta Interactiva igual |
| Esquema de base documentado | Generadores de diagramas desde la base (lectura) | Acceso de sólo lectura, sin datos |
| Diagramas de arquitectura interactivos para presentar (HTML), con evidencia opcional `archivo:líneas` | Skills de diagramado para agentes (p. ej. Archify, Apache-2.0, Node) | El agente describe la arquitectura en JSON y la herramienta valida y dibuja: el dibujo vale lo que valga la lectura. **Lo que va al Cerebro es texto**: `radiografiar-codigo.py --mermaid` (módulos, cruces de capa, ER del DDL) se versiona y se renderiza en GitLab; el HTML es un entregable de `borrador/` |

Cualquiera de ellas entra por `DEPENDENCIAS-EXTERNAS.md` con su licencia, y **no reemplaza** la marca
de confianza ni el "sí" por ítem: produce candidatos más rápido, no verdades.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Inventario y radiografía corridos, todos los módulos de la matriz leídos o declarados HUECO con motivo, cada afirmación con su marca y cada regla candidata con su evidencia |
| **HALLAZGO** | Una regla sin `archivo:línea`, un módulo "resumido" sin borrador, datos de personas en un borrador, una afirmación sin marca |
| **SIN DATOS** | La radiografía no corrió, o la base/el runtime no se pudieron consultar: se dice, no se completa |
