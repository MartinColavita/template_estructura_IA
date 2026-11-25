# Checklist de cierre (§2b): las once filas

Parte de la skill `cargar-a-azure`: se lee cuando se arma el preview de una Tarea, para llenar la tabla de §2b con lo que dio `bin/auditar-tarea.py`.

**La cuenta la hace el script**, que esta skill corre sola sobre el borrador:
`python bin/auditar-tarea.py <tarea.html> --historia <criterios-del-padre.html>`. Sus chequeos
`2b-n` son las filas de esta tabla. Las filas se llenan con lo que dio el script, no releyendo:
un `HALLAZGO` es `NO`, y si el script no corrió, la fila es `SIN DATOS`. Si la herramienta no
puede correr comandos, se le pide a la persona ese comando exacto. La fila 8 (campos de Azure)
no está en la Descripción: esa se mira a mano. La fila 10 (PHI) el script la mira sólo con una
heurística, así que los nombres, las direcciones y los diagnósticos se leen a mano.

> **Tarea chica de solo UI/config: las filas 4, 5, 6 y 11 se marcan `N/A`, no `NO`.** Esas
> cuatro cuentan tests y Escenarios del bloque SDD, y ese bloque **se borra entero** en una Tarea
> de solo UI/config ([[plantillas/tarea]], [[redactar-tarea]] §3.1). `N/A` es una respuesta
> válida y se escribe; lo que no vale es dejar la fila en blanco. Marcar `NO` ahí obligaría
> a "corregir" algo que tres documentos eximen.

| # | Chequeo (contable, no opinable) | Cómo se verifica |
|---|---|---|
| 1 | **Todas las secciones del esqueleto** están, con el nombre exacto y en orden | Listar los `<h3>` del HTML y compararlos uno a uno contra [[checklists/mapa-campos-azure]]. Se cuentan, no se "revisan". |
| 2 | **Cada `[RN-…]`/`[DEC-…]` citado se usa de verdad acá** | Por cada código citado en *Material de apoyo*, buscarlo en el cuerpo. Si no aparece en ninguna validación, caso de error o test, **sobra**: se saca. Citar la regla de otra Tarea manda al dev al lugar equivocado. |
| 3 | **Cada `#NNNNN` mencionado en el texto tiene su enlace**, y **cada referencia a otra Tarea trae su `#NNNNN`** | Dos direcciones. (a) Extraer los `#NNNNN` del HTML y cotejarlos contra los links del work item: Azure **no** auto-linkea `#NNNNN` dentro de la Descripción, así que sin el Related el dev lo busca a mano. (b) Buscar las menciones **sin número** —«la Tarea de front (Related)», «la Tarea de backend», «ambas en Related»— y reemplazarlas por el `#ID`: la relación existe en Azure pero **no se ve desde el texto**, y un Escenario cubierto en parte no se puede seguir hasta el final. Salió mal en **3 de 3** de las primeras Tareas reales. En modo lote, sobre el borrador, un `[T-nn]` vale como `#ID`; se vuelve a mirar después del reemplazo y de las relaciones. |
| 4 | **Cada número de test aparece en la tabla de Escenarios**, o se declara que no mapea | Comparar el rango de la lista `<ol>` (1..N) contra la unión de la columna «Tests que lo verifican». Un test huérfano es un test que no cierra nada. |
| 5 | **Cada Escenario del padre aparece**: como fila si esta Tarea lo cubre (entero o en parte), o con su título textual en la línea **«No cubre»** al pie de la tabla, con la Tarea que lo cubre | Contar los `Escenario:` del campo Criterios de aceptación del padre, y contar las filas más los títulos de la línea «No cubre». Tienen que dar igual. Una fila «no lo cubre esta Tarea» también vale (es la forma vieja), pero alarga la tarjeta sin agregar nada: la forma corta es la línea al pie ([[plantillas/tarea]]). Que un Escenario no lo cubra **nadie** es otro problema, y lo detecta [[analizar-tareas]] sobre el conjunto, no esta tarjeta. |
| 6 | **Coherencia del test de integración** | Si el Alcance dice `sí`: buscar (a) el test en la lista, (b) la subtarea que lo escribe, (c) el ítem del DoD. Las **tres** o ninguna. |
| 7 | **Toda ruta o documento va como `<a href>`** | Buscar rutas con `/` o `.md` sueltas en el HTML: si no están dentro de un `<a>`, no son clickeables. |
| 8 | **Campos que no quedan nulos en silencio** | `Esfuerzo original` (0 si no hay estimación, nunca vacío), `Actividad`, **un** tag temático, Parent. |
| 9 | **Sin markdown crudo ni escapes rotos** | Buscar fences de código, `**`, `- ` al inicio de línea. Adentro de `<pre>`: `<` y `>` escapados como `&lt;` `&gt;`. |
| 10 | **Sin PHI** | Datos de persona/documento/teléfono reemplazados por marcadores. |
| 11 | **Todo test etiquetado «guardarraíl» trae escrita la frase «se pone en rojo si …»** | Buscar la etiqueta en la lista `<ol>`. Por cada una: ¿está la frase? ¿nombra un cambio que **ningún otro test de la lista** detecte? Si falta la frase, o el cambio ya lo detecta otro test, **se le saca la etiqueta y se le exige su rojo previo**. La exención se gana por escrito, no por costumbre ([[plantillas/tarea]]). |

> **Por qué existe esta tabla.** Se agregó después de que **tres tarjetas seguidas** salieran
> con defectos que se ven recién al releerlas en el board: una regla citada que la Tarea no
> usaba, un `#ID` mencionado sin enlace, un test que no cerraba ningún Escenario y rutas sin
> link. Ninguno era una decisión difícil: los cuatro se detectan **contando**. Releer el
> borrador "con atención" ya se probó y no alcanza — por eso el chequeo es mecánico y va
> **antes** del "sí", no después de escribir.
