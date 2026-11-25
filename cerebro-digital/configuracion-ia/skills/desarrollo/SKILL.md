---
name: desarrollo
description: >-
  Punto de entrada ÚNICO para escribir, revisar o migrar código del proyecto —back, front, base
  de datos, seguridad, entrega—. Trae el método propio completo: TDD con evidencia del rojo,
  endpoints con el contrato primero, simular la API, armar la suite, depurar, refactor,
  revisión por dimensiones, accesibilidad, observabilidad, migraciones, dependencias y
  secretos, Merge Request y entrega. Lo específico del stack vive en
  references/metodo/tdd-stack-back.md y tdd-stack-front.md (DEC-003). Guardarraíles: el código
  y el conocimiento no se mezclan, nada sale del repositorio sin un "sí", el lenguaje lo pone
  el repositorio; lo que no se puede verificar es SIN DATOS, que no es aprobado. Usar cuando se
  pida "programá esto", "hacé el endpoint", "escribí los tests", "revisá el código", "arreglá
  este bug", "por qué falla", "migrá la base", "/desarrollo". Español (Argentina).
---

# Desarrollo — el método propio del proyecto

Esta skill es **la puerta** a todo lo que es código. No escribe la solución por vos: fija **cómo**
se escribe, qué cuenta como evidencia, quién verifica y qué frena la entrega. Lo que una Tarea
del tablero define (**qué** hay que hacer: contrato, Escenarios, tests a escribir primero) manda
antes; recién después entra esto.

## La idea, en tres frases

1. **El contrato primero, el test después, el código al final.** Así el front y el back trabajan
   en paralelo y el test tiene algo concreto que verificar.
2. **Un ciclo que no deja evidencia no ocurrió.** El rojo tiene que haber fallado **en su
   aserción**, antes del código, y lo verifica **otro agente**.
3. **Tres estados, nunca dos.** OK / HALLAZGO / **SIN DATOS**, y SIN DATOS no es aprobado.

**Todos los comandos de esta skill se corren parados en la raíz del repositorio del Cerebro.**
Las rutas son relativas a ella.

---

## REGLA DE ORO: punto de entrada único

**Ninguna guía de desarrollo —propia o de terceros— se aplica sin pasar por acá.** No es
burocracia: una guía ajena aplicada suelta puede imponer una estructura de paquetes por capa
técnica que **rompe los límites de módulo** del proyecto ([[decisiones#DEC-002]]), y eso se
descubre recién cuando el código ya está escrito.

Si una sesión aplicó otra guía sin pasar por acá, **eso es un hallazgo**: se avisa y se revisa lo
que produjo contra la tabla de precedencia.

### Si la organización tiene un estándar corporativo

Se **envuelve**, no se copia ni se instala: se lee del servidor en el momento de usarlo (por el
MCP del repositorio que lo publica), se le aplica encima la **tabla de precedencia** de abajo, y
se descarta. Queda declarado en `DEPENDENCIAS-EXTERNAS.md` con el hash de árbol contra el que se
lo revisó. **Sin acceso al servidor el veredicto es `SIN DATOS`**: no se improvisa lo que el
estándar diría, porque eso es inventar un estándar ajeno.

---

## Los seis guardarraíles

### G1 — El código y el conocimiento no se mezclan

Un pedido de **código** activa esta skill y las de verificación de los repos. **No** activa las
del Cerebro ni las del pipeline de Azure. Y al revés: redactar una Tarea, auditar una Historia o
bajar una ficha al tablero **no** activa esta skill.

El cruce a evitar es concreto: una sesión de código que se pone a escribir fichas de negocio, o
una sesión de tickets que se pone a generar código.

**Zona gris declarada:** el momento en que una Tarea se vuelve código. Ahí mandan las dos, en
este orden: la Tarea define **qué** hay que hacer (contrato, tests a escribir primero), y recién
después esta skill define **cómo** se escribe. Nunca simultáneo.

La **ejecución** dentro del código la hacen las skills de `back/` y `front/` (`guiar-tdd`, `verificar-tdd`,
`auditar-codigo`, `armar-swagger`, `diagnosticar-repo`, `consultar-cerebro`): qué hace cada una y por qué las que
auditan viven afuera, en `references/skills-de-los-repos.md`, que se lee al trabajar en un repo de código o al armar
una misión.

### G2 — Punto de entrada único

Ya dicho arriba. Se repite acá porque sostiene a los otros cinco: si alguien entra por la puerta
de atrás, ninguna corrección se aplica.

### G3 — La precedencia está escrita, no se deduce

Cuando una guía externa y este proyecto dicen cosas distintas, **no se resuelve por criterio del
modelo**: se resuelve por la tabla de abajo. Lo que no esté en la tabla y choque, **se frena y se
pregunta**, no se elige. **Una fila de la tabla puede decir "se pregunta"**: estar en la tabla no
significa estar resuelto; significa que ya se miró.

### G4 — Nada sale del repositorio

**Nada sale de este repositorio hacia afuera sin un "sí" explícito sobre lo que se va a
publicar.** Publicar en un repositorio ajeno (una propuesta de mejora a un estándar corporativo,
un issue, un Merge Request) es un turno aparte: primero se muestra el contenido exacto y se
termina el turno; recién un "sí" nuevo habilita escribir afuera (con `DEC-005` confirmada, lo que ella fija:
[[AGENTS]], «Autorización permanente»). Y si el token disponible es de sólo lectura, directamente no está en el alcance.

### G5 — Lo externo se declara, con hash y detector de deriva

**Sólo aplica si el proyecto envuelve un estándar externo**; el template no trae el detector: se agrega
junto con la primera dependencia declarada, como dice `DEPENDENCIAS-EXTERNAS.md`. Si el proyecto sigue
skills de terceros, se declaran en `DEPENDENCIAS-EXTERNAS.md` con el hash
de árbol de cada una. **Importa más con el mecanismo de "leer del servidor", no menos:** como el
contenido se lee siempre actualizado, lo que puede quedar viejo son **nuestras correcciones**. Un
detector de deriva (comparar los hashes de hoy contra el ancla declarada) se corre una vez por
mes y devuelve **OK / HALLAZGO / SIN DATOS**; `SIN DATOS` no es OK. El ancla vive en el
manifiesto y en el script que compara: actualizarla es actualizar los dos.

### G6 — El lenguaje lo pone el repositorio

En los repos de la aplicación se escribe en el lenguaje y con las herramientas que el repo ya
usa (los que fija `DEC-003` y documentan `tdd-stack-back.md` / `tdd-stack-front.md`). Eso incluye
los tests de lo que no es la app (el pipeline, scripts, configuración): van al runner de tests del
repo, no a uno aparte.

- **Permitido sin preguntar:** `sh` adentro de un job del pipeline y el `Dockerfile`, porque es
  lo que trae la imagen.
- **Si con el lenguaje del repo se puede, se hace así.** Si otro lenguaje tenía ventajas, se
  anota en el Merge Request qué ganaría y qué sumaría, sin escribirlo.
- **Si con el lenguaje del repo no se puede, se frena y se pregunta antes de escribir una
  línea:** por qué no se puede, qué lenguaje se propone y qué agrega (herramienta a instalar,
  dependencias, jobs del template que se activan).

No aplica al repositorio del Cerebro: ahí `bin/` es Python a propósito.

> **Por qué.** En el proyecto de origen de este template entraron dos scripts en otro lenguaje
> para probar el pipeline: sumaron un requisito más, activaron un job del template que falló y
> quedaron fuera del runner de tests, así que no protegían nada.

---

## Barreras

- **Lo que no esté en la tabla de precedencia y choque, se pregunta.** No se elige.
- **Si no se puede leer una fuente externa, se reporta `SIN DATOS` y se dice qué falta** (red,
  token). No se improvisa lo que esa fuente diría. Todo `metodo/` funciona igual: es propio y no
  depende de nada.
- **Nunca se pega contenido de terceros dentro de este repositorio.** Se lee, se usa, se descarta
  (G5). Las citas mínimas con atribución van en `references/referencias-externas.md`.
- **Los comentarios del código, en español** (back y front). Se comenta poco —el código se explica
  por sus nombres, donde sólo los sustantivos del negocio que están en la base van en español y
  los verbos, roles técnicos y técnica en inglés (`arquitectura/esqueleto-proyectos.md`)—, pero el
  comentario que hace falta se escribe en español, igual que la documentación y los mensajes de
  commit.
- **Sin PHI** en nada que se versione o se publique. Marcadores: `<persona>`, `<documento>`,
  `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.

## Tabla de precedencia

La tabla de G3 vive en `references/tabla-de-precedencia.md`: se lee **cada vez que una guía externa y el proyecto
chocan**. Mientras no haya estándar externo, gana el proyecto en todo.

---

## El método — organizado por cuándo lo vas a usar

### Todos los días

| Tema | Archivo |
|---|---|
| **Crear un endpoint** de punta a punta: contrato → tests → código → checklist | [crear-endpoint.md](references/metodo/crear-endpoint.md) |
| El ciclo rojo-verde y **qué cuenta como evidencia del rojo** | [tdd-ciclo-y-evidencia.md](references/metodo/tdd-ciclo-y-evidencia.md) |
| **Arreglar un bug** — el ciclo, y los tres tipos que no se parecen | [arreglar-un-bug.md](references/metodo/arreglar-un-bug.md) |
| **Depurar** — causa vs. síntoma, `trace_id`, qué nunca va en un log | [depurar.md](references/metodo/depurar.md) |
| **Refactor** y deuda técnica — la fase 3, y qué no se refactoriza | [refactor.md](references/metodo/refactor.md) |
| Revisión de código **por 6 dimensiones**, con severidad, mirando también lo que el diff no toca | [code-review.md](references/metodo/code-review.md) |
| **El Merge Request**: tamaño, descripción, checklist, quién revisa | [merge-request.md](references/metodo/merge-request.md) |
| Ramas, commits y espacios de trabajo | [ramas-y-commits.md](references/metodo/ramas-y-commits.md) |

### Según el stack (⚠ se completan al decidir `DEC-003`)

| Tema | Archivo |
|---|---|
| Back: dónde va cada cosa, cómo se ve un rojo válido en el runner, comandos | [tdd-stack-back.md](references/metodo/tdd-stack-back.md) |
| Front: idem, más la simulación de la API | [tdd-stack-front.md](references/metodo/tdd-stack-front.md) |
| **Simular la API en el front** desde el contrato | [simular-api-desde-el-contrato.md](references/metodo/simular-api-desde-el-contrato.md) |
| **Accesibilidad** — los 4 chequeos que cubren casi todo | [accesibilidad.md](references/metodo/accesibilidad.md) |

### Tests, por hito, cuando hace falta e infraestructura

El resto del índice —tests (unitarios, la suite, aceptación); por hito (arrancar una funcionalidad, contrato OpenAPI,
seguridad y datos sensibles, dependencias y secretos, observabilidad, migración de base, entrega, refactor o
migración, ingeniería inversa, adoptar un proyecto); cuando hace falta (rendimiento, incidentes, código ajeno), y la
puerta de cada función cuando el código es infraestructura, un pipeline o toca lo que corre
([[arquitectura-e-infraestructura]], [[despliegue-continuo]], [[operacion-de-servidores]], [[seguridad]],
[[gestion-de-gitlab]])— está en `references/indice-del-metodo.md`: se lee **antes de empezar** cualquiera de esos trabajos.

Bibliografía (ideas tomadas con atribución, nunca texto): [referencias-externas.md](references/referencias-externas.md).

Lo que este método exige y una guía genérica no (evidencia del rojo, verificador distinto, tres estados, regla del
cero, límites de módulo, PHI): `references/lo-que-exige-el-metodo.md`, cuando haya que justificarlo.

---

## Cuándo leer cada referencia

| Referencia | Se lee cuando… |
|---|---|
| `references/metodo/*.md` | Lo dice la tabla del método, según el momento |
| `references/indice-del-metodo.md` | Antes de un trabajo de tests, de un hito, de rendimiento, de un incidente o de infraestructura |
| `references/skills-de-los-repos.md` | Se trabaja en `back/` o `front/`, o se arma la misión de un worker o verificador |
| `references/tabla-de-precedencia.md` | Una guía externa y el proyecto chocan (G3) |
| `references/lo-que-exige-el-metodo.md` | Hay que justificar por qué el método pide más que una guía genérica |
| `references/referencias-externas.md` | Se cita una idea ajena (con atribución, nunca texto) |
