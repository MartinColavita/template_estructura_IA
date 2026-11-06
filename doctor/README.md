# Doctor de {{PROYECTO}}

Diagnóstico de salud del proyecto. **Solo lee: no modifica un solo archivo.**

Devuelve un **informe HTML** que se abre con doble clic —con gráficos, secciones y filtros— en
vez de un muro de texto en la consola.

**Requisito único: Python 3 en el PATH.** Nada más — sin Docker, sin `npm install`, sin
servicios externos, sin conexión.

### Índice

| | Sección | Para qué |
|---|---|---|
| **1** | [Cómo se usa](#1-cómo-se-usa) | **Todos los comandos, para copiar y pegar** |
| **2** | [Qué hace hoy](#2-qué-hace-hoy) | Las 23 sondas, una por una |
| **3** | [El histórico](#3-el-histórico) | Dónde queda cada corrida y el reporte de arreglos |
| **4** | [Cómo se usa en los repos](#4-cómo-se-usa-en-los-repos) | Dónde se clonan `back/` y `front/` |
| **5** | [Qué le falta](#5-qué-le-falta) | Lo no hecho, y de quién depende |
| **6** | [Por qué está armado así](#6-por-qué-está-armado-así) | Las decisiones de diseño |
| **7** | [Estructura](#7-estructura) | Qué archivo hace qué |
| **8** | [Cuando algo falla](#8-cuando-algo-falla) | **Síntoma → causa → qué hacer** |
| **9** | [Cómo se agrega o se arregla una sonda](#9-cómo-se-agrega-o-se-arregla-una-sonda) | **Los pasos, con el contrato** |

---

## 1. Cómo se usa

Se corre **desde la raíz del repositorio**, cuando vos querés. No se dispara solo, no está
enganchado a ningún hook y no corre en cada cambio.

### Todos los comandos

Completos, para copiar y pegar. En PowerShell, cambiá `bash doctor/bin/doctor.sh` por
`.\doctor\bin\doctor.ps1` — **los argumentos son idénticos en los dos**.

| Para | Comando |
|---|---|
| **Correr el diagnóstico** y escribir el informe | `bash doctor/bin/doctor.sh` |
| Correr y además **comparar con la corrida anterior** | `bash doctor/bin/doctor.sh --comparar` |
| Mirar **un solo repositorio** | `bash doctor/bin/doctor.sh --repo back` |
| Correr **solo algunas sondas**, para iterar rápido | `bash doctor/bin/doctor.sh --solo espejos,limites` |
| **Resumen por consola**, sin escribir archivo | `bash doctor/bin/doctor.sh --json` |
| Ver por qué una corrida acotada no midió | el panel *Repos conectados* lo explica |
| Abrir el último informe | `doctor/salida/informe.html` — doble clic |
| Abrir el **tablero** (el resumen de un vistazo) | `doctor/salida/tablero.html` — doble clic |
| Ver la historia de corridas | `doctor/salida/historico/INDICE.md` |

Los mismos, en PowerShell:

```powershell
.\doctor\bin\doctor.ps1
.\doctor\bin\doctor.ps1 --comparar
.\doctor\bin\doctor.ps1 --repo back
.\doctor\bin\doctor.ps1 --solo espejos,limites
.\doctor\bin\doctor.ps1 --json
```

Si PowerShell bloquea el script por política de ejecución:

```powershell
powershell -ExecutionPolicy Bypass -File .\doctor\bin\doctor.ps1
```

### Qué hace cada opción

| Opción | Qué hace |
|---|---|
| *(ninguna)* | Corre las sondas y escribe el informe en `doctor/salida/` |
| `--comparar` | Además del informe, genera el **reporte de arreglos**: qué mejoró, qué empeoró y qué quedó igual desde la corrida anterior (§3) |
| `--repo <carpeta>` | Acota a esa carpeta y escribe su propio informe, sin pisar el del proyecto entero (ver abajo) |
| `--solo a,b,c` | Corre solo esas sondas. Útil para iterar sin esperar todo. **No toca el histórico**: escribe el informe pero deja intactas la foto del día y la línea de base de `--comparar` |
| `--json` | Resumen por consola en JSON. **No escribe archivo** — es el modo para encadenar con otra herramienta o pasarle el estado a un agente |

Nombres válidos de `--solo`:

- **Proyecto** — `guardarrailes`, `espejos`, `conteos`, `referencias`, `wikilinks`,
  `estructura`, `asimetria`, `gemelas`, `andamiaje`, `tamano`, `deuda`
- **Código** — `repos`, `limites`, `contrato`, `costura`, `trazabilidad`, `duplicacion`, `dependencias`,
  `seguridad`, `calidad`, `practicas`

El **autocontrol corre siempre**, incluso con `--solo`: es el que avisa si el informe se
contradice.

### Acotar a un repositorio

```bash
bash doctor/bin/doctor.sh --repo back
```

Mira solo esa carpeta y escribe su propio informe (`informe-back.html`), sin pisar el del
proyecto entero.

**Acepta cualquier carpeta del repositorio**, no una lista fija: hoy los repos de código son
`back/` y `front/`, pero mañana pueden ser otros o más de dos. Si el nombre no existe, el
Doctor lista las carpetas disponibles en vez de fallar seco.

**Tres sondas quedan afuera**: `conteos`, `asimetria` y `gemelas`. Las dos últimas **comparan
back contra front**, así que con un lado solo no hay nada que comparar; la primera mide
documentos de la raíz.

> Quedan **excluidas**, no en SIN DATOS. La diferencia importa: SIN DATOS significa *"no se pudo
> medir"* y se lee como un pendiente. Estas no es que no se pudieron — es que **no aplican**.
> **La consola dice cuáles fueron** al terminar la corrida.

### Dónde quedan el informe y el tablero

```
doctor/salida/informe.html     el informe completo: qué pasa y qué hago
doctor/salida/tablero.html     el tablero: cómo estamos, de un vistazo
```

Los dos se abren con doble clic y salen de la **misma corrida**. **No están versionados**
(`doctor/salida/` está en el `.gitignore`): son artefactos derivados, se regeneran cuando haga
falta y no tiene sentido guardar su historia.

### El tablero, y qué contesta que el informe no

El informe contesta **«qué pasa y qué hago»**: es largo a propósito, porque un hallazgo sin su
porqué y sin sus pasos deja al lector igual que antes. El tablero contesta otra cosa,
**«cómo estamos»**, y tiene que hacerlo sin leer: una pantalla, de reojo, antes de decidir si
vale la pena abrir el informe.

Sale de la **misma corrida y de los mismos datos** — no vuelve a medir nada. Si el tablero y el
informe dijeran cosas distintas, eso no es una diferencia de criterio: es un bug del Doctor.

| Lo que muestra | De dónde sale |
|---|---|
| Cuántas sondas en orden, con hallazgo y sin datos, y cuántos pasos propuestos | el estado de cada sonda de esta corrida |
| El semáforo, una celda por sonda — cada una **linkea a su panel** en el informe | ídem, agrupado en documentación y código |
| **Cómo venimos**: columnas apiladas por estado, una por corrida guardada | el histórico, el mismo que usa `--comparar` |
| Los **números duros** (deuda declarada, tokens que pesan siempre, chequeos de autocontrol) | la columna de la tabla de esa sonda, sumada, sin redondear |
| **Costo de contexto**: las ocho skills más grandes, con el umbral marcado | la tabla de esa sonda, ordenada por lo que la barra mide |

Arranca **oscuro** y tiene interruptor a claro; la elección se recuerda en el navegador, y si el
navegador no deja guardarla el tablero funciona igual. En claro usa la paleta del informe, para
que abrir uno y otro se sienta la misma herramienta.

> **El color nunca va solo, y no es una preferencia.** Verde y naranja tienen **ΔE 4.2 en
> protanopia** — medido con el validador de paleta, no estimado — y re-escalonarlos lo
> *empeora* (2.7). Un semáforo que distingue los estados solo por color es ilegible para una de
> cada doce personas. Por eso cada estado lleva **siempre** su forma y su palabra al lado: un
> tilde y «En orden», un triángulo y «Hallazgo», un círculo tachado y «Sin datos». Sacarle la
> etiqueta «para que se vea más limpio» es romperlo. En oscuro los tres colores están
> re-escalonados aparte — no es el claro invertido — y ahí sí pasan: ΔE 9.3.

> **Un número que no se puede calcular se muestra, no se saltea.** Los duros salen de una
> **columna con nombre** de la tabla de su sonda. Si alguien la renombra, el módulo deja de
> encontrarla — y la reacción natural, saltear la fila, hace que el número se evapore del
> tablero sin una sola línea de aviso. Nadie lo nota, porque nadie se acuerda de que ahí iba un
> número. Así que la fila **aparece igual**, en gris, diciendo qué columna falta. Una sonda que
> directamente **no corrió** es otra cosa y no se reporta: en una corrida acotada faltan sondas a
> propósito, y gritar por eso sería gritar por todo. Y un **cero se muestra**: cero deuda es una
> buena noticia, no un faltante.

**Una corrida parcial (`--solo`) no entra en la tendencia**, por el mismo motivo por el que no
toca el histórico: dibujar dos sondas como un punto más se lee como si el proyecto se hubiera
desplomado de catorce a dos. El tablero igual se escribe — con los números de esa corrida — y
avisa arriba que está mirando media foto.

Como el informe: un solo archivo, CSS y JavaScript adentro, gráficos en SVG escrito a mano.
**Cero librerías, cero CDN, cero red.**

---

## 2. Qué hace hoy

**Veintitrés sondas**, en dos grupos: trece miran el **proyecto** —documentación, configuración,
skills— y **diez** miran el **código** de los repositorios clonados en `back/` y `front/`.

Cada una devuelve **uno** de tres estados:

| Estado | Cuándo |
|---|---|
| **OK** | Se midió y no hay nada que corregir |
| **HALLAZGO** | Se midió y hay algo que arreglar o decidir |
| **SIN DATOS** | No se pudo medir todavía — típicamente, porque no hay código |

### Las trece del proyecto

| # | Sonda | Qué mira |
|---|---|---|
| 1 | **Guardarraíles** | Que el hook esté activo en este clone y que tenga sus cinco guardas. La guarda de BOM **exime a los `.ps1`**: PowerShell 5.1 necesita el BOM para leer UTF-8, así que ahí no es un descuido |
| 2 | **Espejos de skills** | Que `.agents/skills/` y `.claude/skills/` sean idénticos a la fuente |
| 3 | **Conteos declarados** | Que cuando un documento dice "23 skills" haya 23, **y que las nombre a todas** |
| 4 | **Referencias a archivos** | Rutas que las skills citan en su texto y que no existen |
| 5 | **Wikilinks** | Enlaces `[[x]]` que no resuelven a ningún archivo |
| 6 | **Estructura** | Qué existe hoy del árbol prometido en los README |
| 7 | **Asimetría back/front** | Qué skill **existe** de un lado y no del otro |
| 8 | **Gemelas back vs. front** | De las que existen en los dos, si **divergieron en estructura** — una perdió una sección que la otra tiene |
| 9 | **Andamiaje obsoleto** | `.gitkeep` en carpetas que ya tienen contenido |
| 10 | **Costo de contexto** | Tokens por skill, en dos cifras (ver abajo) |
| 11 | **Deuda declarada** | Marcas de pendiente, y qué archivos con pendientes nadie toca hace meses |
| 12 | **Cómo venimos** | Si los hallazgos **subieron o bajaron** respecto de la corrida anterior. Sale del histórico, y no corre con `--solo` |
| 13 | **Autocontrol del informe** | El Doctor revisándose a sí mismo (ver abajo) |

> **Asimetría y Gemelas contestan preguntas distintas.** La primera: *¿la skill existe de los
> dos lados?*. La segunda: *¿dicen lo mismo?*. La segunda es la que muerde, porque el defecto
> solo aparece cuando comparás — de cada lado todo parece estar bien. Ya pasó una vez:
> `verificar-tdd` del front había perdido un chequeo que el back sí tenía.

### Las diez del código

Miden el código de los repositorios clonados en `back/` y `front/`. **Cómo encuentra los
repositorios**: no tiene una lista de nombres. Busca las carpetas que ya tienen su espejo de
skills scoped —que es como este ecosistema declara *"acá va a vivir un repo con sus reglas de
desarrollo"*— y adentro de cada una, la raíz de cada unidad de código por su **marcador de
build**: `pom.xml`, `build.gradle` / `build.gradle.kts` o `package.json`. Si mañana hay tres
fronts, el Doctor no se entera de nada.

> **Calibradas para esos stacks.** La detección de unidades de código se hace por los
> marcadores de build conocidos, y lo que se mide después —extensiones, capas, herramientas de
> calidad— está calibrado para ellos. Para otro stack hay que **ampliar las tablas de
> `codigo.py`**: `MARCAS`, `EXTENSIONES` y `CALIDAD_*`. Sin eso, el Doctor no encuentra la unidad
> de código y las sondas quedan en SIN DATOS, que no es aprobado.

| # | Sonda | Qué mira | Stack |
|---|---|---|---|
| 14 | **Repos conectados** | Qué repositorios están clonados hoy, con qué stack y qué slices. Corre **siempre**: es la que explica a las otras ocho | ambos |
| 15 | **Límites del diseño** | En el back, las reglas de dependencia del monolito modular (DEC-002): adentro del módulo `api → application, domain` · `application → domain` · `infra → application, domain` · `domain →` nada · `exceptions/` la usan todas y solo depende de `shared.exceptions`. Entre módulos se llama a la `application` del otro y se usan sus tipos de `domain` y `exceptions`; entrar a su `api` o su `infra` es HALLAZGO. `shared` lo usa cualquiera y no depende de ningún módulo. En el front, que ningún slice entre a otro salvo por su `index` o su `api/` | ambos |
| 16 | **Contrato vs. código** | Que los endpoints del `openapi.yaml` y los del código digan lo mismo | back |
| 17 | **La costura back ↔ front** | Que los mocks del front y los tests de API del back estén hablando del **mismo** `openapi.yaml`. Es el único punto donde los dos repositorios se tocan | ambos |
| 18 | **Trazabilidad test ↔ Tarea** | Que cada archivo de test diga a qué Tarea del tablero pertenece. El cruce completo contra la lista de «Tests a escribir PRIMERO» lo hace el **pedido** del panel, porque esa lista vive en Azure y el Doctor no sale de la máquina | ambos |
| 19 | **Duplicación entre slices** | Bloques de 10 líneas repetidos en dos slices distintos | ambos |
| 20 | **Dependencias sin usar** | Paquetes declarados que ningún archivo importa | ambos |
| 21 | **Puerta de seguridad** | Que SAST esté en el pipeline, que **frene** la entrega, que las supresiones traigan su motivo, y que no haya credenciales escritas | ambos |
| 22 | **Puerta de calidad** | Linter, análisis estático y cobertura: **declarados** y, sobre todo, **exigidos por el build** | ambos |
| 23 | **Prácticas y patrones** | Un puñado corto de cosas que el linter no mira y cuestan caro | ambos |

> **Ninguna de las diez aprueba sobre cero mediciones.** Un repositorio clonado pero vacío,
> o todavía sin ordenar en módulos y capas, devuelve **SIN DATOS**, no OK. Es la regla del
> cero: decir «cero problemas» sobre cero archivos es mentir con verde.

**Sin código clonado, nueve de las diez se saltean** y sólo corre *Repos conectados*, que las
nombra una por una y explica por qué. Nueve paneles idénticos diciendo "no hay código" no
informan nada; una sonda que lo dice bien, sí.

#### Qué NO hacen, y por qué importa entenderlo

El Doctor **no reemplaza a SAST ni a un analizador estático, y no intenta hacerlo.**

> Esas herramientas hacen **fallar el build**, que es una barrera muchísimo más fuerte que un
> informe que alguien tiene que acordarse de leer. Competir con ellas sería escribir peor lo
> que ya está bien hecho.

Entonces el Doctor mide **lo que ellas no cubren**, que es de dos clases:

- **Las reglas propias de este proyecto**, que ninguna herramienta de estantería conoce: los
  límites entre módulos, el contrato contra el código, la trazabilidad del test al ticket.
- **Que la puerta esté puesta.** No compite con SAST: compite con el **olvido de
  enchufarlo**. Un repositorio sin el paso en el pipeline pasa meses sin analizarse y se entera
  el día de la entrega, que es el peor momento posible.

Y tampoco miran **estilo**. Indentación, comillas y punto y coma son del formateador. La lista
de *Prácticas y patrones* es corta a propósito: cada una tiene que cumplir dos condiciones —
que casi no dé falsos positivos, y que el linter no la cubra ya.

> **El camino natural de un hallazgo de código es dejar de estar acá.** Cuando una regla se
> repite lo suficiente, se mueve a la fitness function de arquitectura o al linter, donde **frena el build**. El Doctor
> sirve para **descubrir cuáles valen la pena escribir**; no para ser su casa definitiva.

### Dos reglas de lectura que no son negociables

**No hay puntaje único.** Nada de "82/100". Un número resume de más, da falsa objetividad y
esconde justo lo que hay que arreglar. El encabezado dice *"N de M sondas con datos"* y listo — y la M cambia segun el alcance,
porque las sondas que no aplican quedan afuera en vez de contarse como buenas.

**SIN DATOS no es aprobado.** Un repositorio vacío no es un repositorio sano: decir "0 problemas"
sobre 0 líneas de código es mentir con verde. Por eso el semáforo ignora las SIN DATOS en vez de
contarlas como buenas, y las muestra aparte.

### Los dos números de tokens, y por qué son dos

La sonda de costo de contexto da **dos** cifras por skill, porque se pagan en momentos
distintos:

| Número | Cuándo se paga | Por qué importa |
|---|---|---|
| **Tokens que pesan siempre** | En **cada** consulta, se use o no la skill | Es la descripción del frontmatter: el asistente la lee siempre para decidir qué cargar. Es el número a vigilar |
| **Tokens al invocarla** | Solo cuando esa skill se usa | Es el archivo entero. Se paga una vez, y solo si hacía falta |

Por eso **una skill grande no es automáticamente mala**: si su descripción es corta y precisa,
se carga poco, y cuando se carga es porque sirve. Lo que conviene mirar primero es la columna
de "pesan siempre".

> **Son una estimación, no una medición.** Se calculan a razón de **3,6 caracteres por token**,
> que es lo típico para prosa en español con algo de código. El tokenizador real depende del
> modelo y traerlo sería una dependencia externa, que acá no se admite. Sirven para **comparar
> skills entre sí** y tener un orden de magnitud — no para facturar.

### El pedido a la inteligencia artificial

Cada sonda **con hallazgo** trae un texto listo para copiar y pegarle a un asistente, con el
repositorio abierto. No es genérico: **ya incluye los datos del hallazgo**, así que quien lo
pega no tiene que explicar nada. El de wikilinks, por ejemplo, lleva la lista completa de
enlaces rotos con su archivo.

Va **dentro del panel del hallazgo**, no en una sección aparte. Separarlo obligaría a
correlacionar a mano cuál pedido corresponde a cuál problema, y con veintitrés sondas eso se
equivoca solo.

> **Todos terminan igual**, y no es formalidad: *«No edites nada todavía: mostrame los cambios
> que proponés, uno por uno, y espero mi confirmación.»* Un informe que genera texto para
> pegarle a una IA es también una forma muy cómoda de romper cosas rápido. La IA propone, la
> persona decide — el mismo principio que rige en todo el resto del ecosistema.

**Si el botón de copiar no funciona**, el informe **selecciona el texto** para que lo copies con
Ctrl+C. Pasa en archivos abiertos con doble clic: algunos navegadores consideran `file://` un
contexto inseguro y bloquean el portapapeles. Seleccionar siempre se puede.

### La tendencia: una foto no es un signo vital

El informe dice *«223 marcas de deuda»*. Eso solo **no decide nada**: no se sabe si la
semana pasada eran 180 o 260. La sonda *Cómo venimos* compara esta corrida con la anterior
y dice, sonda por sonda, si los hallazgos subieron o bajaron.

Sale del histórico que el Doctor ya venía guardando en cada corrida completa — el dato
estaba y nadie lo leía. **Un cambio de veredicto pesa más que un cambio de conteo**: pasar
de OK a hallazgo importa aunque sea por una sola fila.

> **Dos cosas que NO significa.** Primero: esta sonda **mide el informe, no el proyecto**.
> Que todo baje no quiere decir que esté bien — quiere decir que hoy hay menos que ayer.
> Segundo: el histórico es **de cada máquina**, así que la tendencia que ves es la tuya, no
> la del equipo. Y no corre con `--solo`, por el mismo motivo por el que una corrida
> parcial no toca el histórico: compararía dos sondas contra todas las demás.

> **Una sola implementación, dos vistas.** La comparación la hace `comparar.py` — el mismo
> código que arma el reporte de arreglos de `--comparar`. Lo que cambia entre las dos no es
> el cálculo, es **cuándo se mira**: este panel contesta *«¿cómo venimos?»* en cada corrida;
> el reporte de arreglos, *«¿sirvió lo que acabo de tocar?»* después de arreglar algo.
>
> La primera versión de esta sonda tenía su propia comparación, y las dos vistas llegaron a
> decir **1 empeoró contra 2 empeoraron** sobre los mismos datos — porque una excluía las
> sondas que miran el informe y la otra no. Una regla con dos dueños se separa sola.

### El autocontrol: qué promete y qué no

La última sonda revisa a **todas las demás**, incluida la tendencia. Chequea que ninguna diga **OK** teniendo filas en
hallazgo, que toda sonda con hallazgo diga **qué hacer**, que todas se expliquen, y que ninguna
tabla tenga filas corridas respecto de su encabezado.

**Se pagó solo en su primera corrida**: encontró que la sonda de asimetría daba veredicto OK
mientras una de sus filas decía HALLAZGO. El veredicto estaba bien —era una asimetría
declarada— pero la fila mentía.

> **Lo que NO puede hacer.** El Doctor revisándose a sí mismo detecta errores de **coherencia**.
> **No** detecta que una sonda **mida mal**, porque para eso usaría el mismo código que produjo
> el error. Ese segundo chequeo lo tiene que hacer alguien distinto — es el mismo principio que
> rige en las tarjetas: **el que produce nunca es el que aprueba**.

### Las sondas de código no traen banco de pruebas

> **Estado, y conviene saberlo antes de confiar en ellas.** Las sondas del proyecto se prueban
> solas: corren sobre este mismo repositorio, que tiene documentación de verdad, y si miden mal
> se nota enseguida. **Las del código no tienen esa suerte** mientras no haya código clonado.

**Se puede armar un banco de pruebas con un defecto plantado por sonda**: un repositorio de
mentira —uno por stack, con su marcador de build— donde cada sonda tenga **un** defecto puesto a
propósito y, al lado, el caso legítimo que se le parece; y un `doctor/probar.py` (⚠ no existe todavía en el template: se arma cuando haya código clonado) que corra las
sondas sobre él y verifique que cada una encuentre el suyo (`espera`) y no marque lo que está
bien (`no_espera`). Conviene armarlo cuando haya código real clonado en `back/` o `front/`, que
es cuando se sabe qué stack calibrar (§5).

> **Qué se pierde mientras no está.** Una prueba así verifica **las dos direcciones**: que la sonda
> **encuentre** el defecto y que **no marque** lo que está bien. Contra un repositorio real se
> puede verificar la segunda sola — la primera necesita defectos puestos a propósito. Y la
> segunda es la que más importa: una sonda que grita lobo es peor que no tenerla, porque se deja
> de leer el informe entero, incluido lo que sí era cierto.

---

## 3. El histórico

Cada corrida deja tres cosas:

```
doctor/salida/
├─ informe.html                        siempre el último (la ruta no cambia)
└─ historico/
    ├─ reporte-15-09-2026.html         copia fechada, para leer
    ├─ reporte-15-09-2026.json         las medidas, para comparar entre días
    └─ INDICE.md                       una fila por corrida, la más nueva arriba
```

El nombre va en **día-mes-año**. Dos corridas del mismo día **pisan la del día**: es a propósito,
para que el histórico sea una foto por jornada y no una pila de archivos casi iguales.

El `.json` existe porque comparar dos días parseando HTML es frágil. Es el insumo de la
**tendencia entre corridas**, que todavía no está hecha pero ya tiene de dónde leer.

> **El histórico no se versiona**, igual que el informe. Es de cada máquina. Si el equipo
> quiere una historia compartida hay que decidir **dónde se publica** — y no se resuelve
> sacándolo del `.gitignore`, porque un informe por día por persona ensucia el repositorio.

---

### El reporte de arreglos

El informe contesta *"¿cómo está el proyecto hoy?"*. Esa **no** es la pregunta que uno tiene
después de arreglar algo — ahí la pregunta es *"¿sirvió lo que hice?"*, y para contestarla hay
que comparar dos momentos.

```bash
bash doctor/bin/doctor.sh --comparar
```

Deja `historico/arreglos-DD-MM-AAAA.html`: arriba el resumen (cuántas sondas mejoraron,
cuántas empeoraron, cuántas quedaron igual) y abajo el detalle de cada una que cambió, con el
**antes y el después** lado a lado.

**Funciona igual si el arreglo lo hizo una persona a mano o un comando**: compara estados, no le
importa quién los produjo.

> **Una sonda cuenta como mejorada también si bajó la cantidad de hallazgos sin llegar a OK.**
> Ir de doce enlaces rotos a tres es progreso, y un informe que solo mira el color no lo
> muestra. Y *"sin cambios"* no quiere decir que esté bien: quiere decir que ahí no se tocó nada.

Para poder comparar **dos corridas del mismo día**, además del archivo fechado se guarda el par
`ultimo.json` / `previo.json`, que conserva los dos últimos estados sea cuando sea.

---

## 4. Cómo se usa en los repos

El Doctor corre **desde la raíz** y cubre el proyecto entero, incluidos `back/` y `front/`. No
hace falta instalarlo adentro de cada repo ni copiarlo a ningún lado.

### Dónde vive el código

El backend y **cada** front viven en su propio repositorio de git, y se **clonan adentro** de
`back/` y `front/`:

```bash
git clone <url-del-back>     back/<nombre-del-repo>
git clone <url-de-esa-app>   front/<nombre-de-la-app>
```

**Siempre en una subcarpeta**, nunca en `back/` o `front/` directo: esas dos carpetas ya tienen
adentro su README y sus espejos de skills, y `git clone` se niega a escribir en un directorio
que no está vacío. El Doctor encuentra la raíz de cada repositorio por su marcador de build
(`pom.xml`, `build.gradle` o `package.json`; para otro stack hay que ampliar las tablas de
`codigo.py`, §2), así que el nombre de la subcarpeta es libre.

Lo clonado **no se versiona acá** —ya tiene su repositorio—: el `.gitignore` de la raíz ignora
todo `back/` y `front/` salvo el README de la carpeta y los espejos de skills. Sin esa regla, el
primer `git status` después de clonar muestra miles de archivos ajenos y alguien termina
commiteando un `target/` entero.

**Por qué adentro y no al lado.** Con el código adentro, un asistente lee en una sola sesión el
Cerebro Digital, las reglas del proyecto, la Tarea y el código que la implementa. Al lado, cada
una de esas cosas es un salto de contexto, y el que se saltea es siempre el mismo: el
conocimiento funcional.

- **Hoy** `back/` y `front/` solo tienen su `README.md` y sus skills. Las sondas que miran
  estructura los reportan como **SIN DATOS**, con la etiqueta *"prometido: todavía sin código"* —
  gris, no rojo. Sin esa distinción la primera corrida sale toda roja y nadie vuelve a abrirla.
- **Cuando exista código**, esas mismas sondas empiezan a devolver datos y **se encienden solas
  las ocho de código**, sin instalar ni configurar nada.

### Cuándo conviene correrlo

- Antes de un cambio grande, para tener la foto de dónde se parte.
- Después de una tanda de trabajo, para ver qué se movió.
- Cuando alguien pregunta *"¿cómo está esto hoy?"* y no queremos contestar de memoria.

**No** en cada commit: para eso está el hook, que es instantáneo y bloquea. El Doctor es lento,
es panorámico y es para leer.

---

## 5. Qué le falta

Escrito acá para que no se pierda, y marcado como lo que es: **todavía no hecho**.

| Pendiente | Por qué importa | De quién depende |
|---|---|---|
| **Probar las sondas de código, y después calibrarlas** | No traen banco de pruebas propio y hoy **ninguna prueba las verifica** (§2). Cuando haya un repositorio clonado conviene armarlo —un defecto plantado por sonda— y de paso calibrarlas: los marcadores de build del stack, el umbral de duplicación, qué cuenta como salto de capa y qué dependencias son legítimamente no importables se terminan de ajustar viendo un repositorio de verdad | del equipo, cuando clone |

| **Trazabilidad completa contra el tablero** | La sonda mide la *costura* —que el test nombre su Tarea— porque la lista de «Tests a escribir PRIMERO» vive en Azure y el Doctor no sale de la máquina. El cruce completo lo hace hoy el **pedido** del panel, que se le copia a un asistente con acceso al tablero | decisión del equipo |
| **Elegir UNA forma de trazar el test a la Tarea** | La sonda acepta cuatro formas distintas justamente porque el equipo todavía no eligió. Cuando elija, se deja la suya y se sacan las otras, y queda escrito en `guiar-tdd` de cada repo | del equipo |

### Dos preguntas que quedaron contestadas, y conviene que no se vuelvan a abrir

**El aviso de costo antes de correr: hace falta, y ahora está medido.** ~7 ms por archivo: con
3000 clases la corrida queda en el orden de **los minutos**, no de los segundos. No es
caro en dinero —no hay modelo ni red de por medio— pero sí en paciencia, y el README no puede
seguir diciendo "segundos" sin aclararlo.

Lo que sí quedó descartado es que fuera caro **en tokens**: las diez sondas de código son **lectura estática de
archivos locales**, sin red, sin Azure y sin modelo. Lo caro habría sido mandarle el código a un
modelo, y no lo hacen. El recorrido está acotado a 20.000 archivos y nunca entra a `target/`,
`node_modules/` ni `dist/`.

**Qué queda para el análisis estático de verdad: casi todo lo que el build pueda frenar.**
La fitness function de arquitectura para los límites, el linter para las dependencias y el estilo, SAST para la
seguridad. Todos ésos **hacen fallar el build**, que frena muchísimo más que un informe. El
Doctor mide lo que ellos no cubren —las reglas propias del proyecto— y **que la puerta esté
puesta**.

> **El camino natural de un hallazgo de código es dejar de estar acá.** Cuando una regla se
> repite lo suficiente, se mueve a la fitness function de arquitectura o al linter y el Doctor deja de tener que
> reportarla. Que una sonda de código se vuelva innecesaria **no es perder el trabajo**: es
> exactamente para lo que se escribió.

---

## 6. Por qué está armado así

**Un solo motor, en Python.** `doctor.py` tiene toda la lógica; `bin/doctor.sh` y
`bin/doctor.ps1` son envoltorios de quince líneas que solo lo llaman. Mantener dos
implementaciones —una en bash y otra en PowerShell— es exactamente cómo se desincronizan las
cosas, y este proyecto ya tiene cicatrices de eso.

**Sin dependencias externas, ni en el informe.** El HTML lleva su CSS y su JavaScript adentro, y
los gráficos son SVG generado a mano. Ninguna librería de terceros, ningún CDN, ninguna llamada
de red. El informe puede contener rutas y nombres internos: **no sale de la máquina**, y se abre
igual sin conexión.

**No modifica nada.** Ni un archivo, ni el Cerebro Digital, ni el tablero. Si encuentra algo,
lo reporta; arreglarlo es decisión de una persona.

---

## 7. Estructura

```
doctor/
├─ README.md               este archivo
├─ doctor.py               el motor: las 13 sondas del proyecto y el orquestado
├─ codigo.py               las 10 sondas del código
├─ comparar.py             el reporte de arreglos (--comparar)
├─ plantilla.py            inyecta los datos de la corrida en las dos plantillas
├─ informe/
│   ├─ plantilla.html      el diseño del informe (CSS y JS adentro)
│   └─ tablero.html        el diseño del tablero (CSS y JS adentro)
├─ bin/
│   ├─ doctor.sh           envoltorio bash
│   └─ doctor.ps1          envoltorio PowerShell
└─ salida/                 informe y tablero generados — NO versionado
```

### Por qué las sondas de código viven en otro archivo

No es para que `doctor.py` sea más corto. Son **dos cosas distintas**: las trece del proyecto
miden documentación y configuración y corren siempre; las diez de código miden repositorios
ajenos que pueden no estar. Separarlas deja esa diferencia escrita en la estructura y no sólo en
un comentario.

`codigo.py` **no importa nada de `doctor.py`** —no habría forma sin un ciclo, y peor: `doctor.py`
corre como `__main__`, así que un `import doctor` cargaría una **segunda copia** del módulo con
su propio alcance y las sondas leerían el valor equivocado. En vez de eso, `doctor.py` le deja en
`CTX` lo que necesita, justo antes de correr. Es **una línea de acoplamiento, explícita y en un
solo lugar**.

### El contrato entre el motor y el diseño

`doctor.py` no sabe nada de HTML y `plantilla.html` no sabe nada de sondas. Los une **un
objeto JSON**, y nada más:

```js
{ rama, fecha, sondas: [ { id, titulo, estado, resumen, sp, cols, filas } ] }
```

El informe **deriva todo lo demás de ahí**: infiere qué columnas son numéricas, arma los
gráficos, calcula los repartos y construye el índice. Agregar una sonda es agregar una función
en `doctor.py`; no hay que tocar una línea del diseño.

> **El `id` es estable a propósito**, y sale del nombre de la función, no del título. El informe
> engancha los gráficos por `id`: si alguien reescribe un título, el gráfico no se cae.

### Relación con la skill `diagnosticar-repo`

La skill es **la puerta de entrada para un agente**: explica el alcance, el gate de costo y cómo
leer el resultado. El motor real es este. La skill invoca `doctor/bin/doctor.*`; no reimplementa
las sondas.

> Si alguna vez las dos empiezan a decir cosas distintas, **manda este README** — acá está lo que
> el código realmente hace.

---

## 8. Cuando algo falla

Síntoma, causa y qué hacer. De lo más común a lo más raro.

| Síntoma | Qué pasó | Qué hacer |
|---|---|---|
| `doctor: hace falta Python 3 en el PATH` | No hay Python. **No hay plan B silencioso**: el motor es Python justamente para no duplicarlo en dos shells | Instalá Python 3 y volvé a abrir la consola |
| PowerShell no deja correr el `.ps1` | Política de ejecución de la máquina | `powershell -ExecutionPolicy Bypass -File .\doctor\bin\doctor.ps1` |
| Una sonda sale **SIN DATOS** | **No se pudo medir. No es aprobado.** Casi siempre: falta el código clonado, o la carpeta que mira se movió | El panel de esa sonda dice cuál de las dos es, y trae los pasos |
| El informe se abre **en blanco** | El JavaScript no corrió: el cuerpo se construye con JS a partir del objeto de datos | Bajá y leé el bloque `<noscript>`: trae el veredicto de cada sonda en HTML plano. No es el informe, pero contesta lo esencial |
| Una sonda sale **SIN DATOS** diciendo «La sonda falló: …» | Esa sonda reventó. **No tumba el informe**: se reporta como lo que es, un aspecto sin revisar | Corré esa sola para ver el error entero: `bash doctor/bin/doctor.sh --solo <nombre>` |
| **Autocontrol en HALLAZGO** | El informe **se contradice a sí mismo**. Es un bug del Doctor, no del proyecto | Miralo **antes** que el resto del informe: su tabla nombra la sonda y el chequeo que falla |
| Una sonda de código **marca algo que está bien** | Falso positivo. Es el peor defecto que puede tener el Doctor: se deja de leer el informe entero | §9 — se escribe primero el caso legítimo que se marcó de más, y recién ahí se toca la sonda |
| `doctor: no existe la carpeta 'x/'` | `--repo` con un nombre que no está | El propio mensaje lista las carpetas disponibles |
| El `--comparar` dice «sin reporte de arreglos» | No hay corrida anterior con la cual comparar | Corré una vez sin `--comparar`, hacé los cambios, y después sí |

> **SIN DATOS nunca es un aprobado.** Un repositorio vacío no es un repositorio sano: decir
> «cero problemas» sobre cero líneas de código es mentir con verde. Si una sonda queda en SIN
> DATOS, ese aspecto **quedó sin revisar** — es un pendiente, no una tilde.

---

## 9. Cómo se agrega o se arregla una sonda

### Dónde va

| Si mide… | Va en | Y se registra en |
|---|---|---|
| documentación, configuración, skills | `doctor.py` | la lista `SONDAS` del final |
| el código de `back/` o `front/` | `codigo.py` | la lista `SONDAS` **y** `SOLO_CON_CODIGO` |

### El contrato: una función, un diccionario

Una sonda es **una función sin argumentos** que devuelve `res(...)`. El `id` sale del **nombre
de la función** —`sonda_limites` → `limites`— y no del título, porque el informe engancha los
gráficos por `id`: si alguien reescribe un título, el gráfico no se cae.

```python
def sonda_lo_que_sea():
    filas = [["algo", "un dato", "por qué está mal", "HALLAZGO"]]
    return res("Título visible", "HALLAZGO", "Una línea de resumen.",
               (["Cosa", "Dato", "Detalle", "Estado"], filas),
               significa="Qué mide, en criollo, para alguien que no la escribió.",
               importa="Qué se rompe si no se arregla.",
               acciones=[{"paso": "Qué hacer.", "comando": "opcional"}],
               pedido="El texto con los datos adentro, para copiarle a un asistente.")
```

**Cuatro reglas que el autocontrol te va a exigir igual**, así que conviene cumplirlas de
entrada:

1. Si el veredicto es **OK**, ninguna fila puede decir `HALLAZGO`. Si dice, el veredicto miente
   y alguien va a pasar de largo un problema real.
2. Si el veredicto es **HALLAZGO**, tiene que haber `acciones`. Reportar un problema sin salida
   deja al lector igual que antes de leerlo.
3. **Siempre** `significa` e `importa`. Sin eso vuelve a ser un número suelto.
4. Toda fila tiene **exactamente** tantas celdas como columnas el encabezado, y la última es el
   estado. Una fila corrida se dibuja mal y el dato se lee peor.

### Los pasos

1. **Escribí primero el caso, no la sonda.** Plantá el defecto que querés detectar **y, al
   lado, el caso legítimo que se le parece**, en el banco de pruebas (§2) o en el repositorio
   clonado sobre el que vaya a correr.
2. Agregá la expectativa a la prueba: qué tiene que encontrar (`espera`), qué **no** puede
   marcar (`no_espera`), y la frase **«se pone en rojo si…»**. Si la prueba no existe todavía,
   armala: un `doctor/probar.py` (⚠ no existe todavía en el template: se arma cuando haya código clonado) que corra las sondas sobre el banco y compare contra esas dos
   listas.
3. Corré `python doctor/probar.py`. **Tiene que fallar**, y por el motivo correcto.
4. Escribí la sonda. Corré de nuevo hasta que pase.
5. Si la tabla merece gráfico, agregá el `id` en `esqueletoGraficos` de
   `informe/plantilla.html` y el ancho en `SPAN` de `plantilla.py`. **Nada más**: el dibujo sale
   solo de la forma de la tabla.
6. Corré el Doctor entero y mirá que el **autocontrol siga en OK**.

> **El paso 1 no es ceremonia.** Las sondas de código se escribieron sin código sobre el cual
> correrlas, y un banco de pruebas destapó tres bugs de una: el parseo del contrato se comía las
> rutas con parámetro, `--repo` anidado moría al final, y una unidad deducía mal su carpeta.
> Ninguno se habría visto leyendo el código.

### Si lo que hay que arreglar es un falso positivo

**No toques el umbral primero.** El orden es al revés:

1. Agregá el caso legítimo que se marcó de más al repositorio contra el que corrés la prueba.
2. Agregalo a `no_espera` en `probar.py`. Ahora la prueba **falla**.
3. Recién ahí ajustá la sonda hasta que pase, sin romper lo que ya detectaba.

Así el falso positivo **no puede volver**. Bajar un umbral a ojo lo tapa hasta la próxima vez.

### Si la diferencia es legítima y va a quedar

Entonces no es un bug: es una **decisión**, y se declara por escrito donde la sonda la lea —
como `ESPERADAS` en la sonda de asimetría o `PROPIAS` en la de gemelas.

> Una diferencia declarada es una decisión; una sin declarar es un descuido. **Desde afuera se
> ven iguales**, y por eso la lista es explícita y nunca se infiere.
