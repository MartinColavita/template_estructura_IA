# Formato: que se lea bien en Azure

Parte de la skill `comentar-tarea`: se lee al redactar todo comentario, antes de mostrarlo: etiquetas HTML, marcadores, @menciones y el sello de auditoría.

## Formato: que se lea bien en Azure

**Azure toma el comentario como HTML.** Un texto plano con saltos de línea llega **pegado en un
solo renglón**: Azure descarta los saltos. Y el markdown (`**`, `-`, `#`, las comillas
invertidas) se ve literal. Por eso todo comentario se arma en HTML, con las mismas etiquetas que
la Descripción ([[checklists/mapa-campos-azure]]):

| Para | Se usa | No se usa |
|---|---|---|
| El renglón de arriba, que dice de qué se trata | `<p><b>…</b></p>` | `<h1>` / `<h2>`: Azure ya pone el título de la tarjeta |
| Secciones | `<h3>`, con un `<hr>` antes de cada `<h3>` **que viene después de otro contenido** | Secciones pegadas: sin el `<hr>` no se ve dónde termina una |
| Prosa | `<p>` | Texto suelto entre etiquetas |
| Datos cortos (rama, commit, veredicto) | `<ul><li><b>Nombre:</b> valor</li></ul>` | Una línea larga con todo separado por `·` |
| Comparar cosas en columnas | `<table>`, con `<th>` en la fila de títulos | Espacios para alinear: en HTML se pierden |
| Líneas que lee una máquina (el sello) | Una por renglón, separadas con `<br>` | Cambiarles el texto |
| Marcadores (`<persona>`, `<veredicto>`) | `&lt;persona&gt;` | `<persona>` sin escapar: **el navegador se lo come** y desaparece sin aviso |

**Nada de estilos inline** (`style=`, colores, tamaños de letra): Azure los filtra o los muestra
distinto según el tema, claro u oscuro.

**En los moldes, todo lo que va entre `&lt; &gt;` se reemplaza** por el dato real. Antes de
mostrar el comentario se revisa que no quede ninguno: **un marcador sin reemplazar no se
postea**, porque en la tarjeta se lee como si fuera el dato. La excepción son los marcadores
de PHI (`&lt;persona&gt;`, `&lt;documento&gt;`…): ésos van a propósito, en lugar del dato real.

**Las @menciones.** Escribir `@Nombre` como texto **no avisa a nadie**: Azure sólo notifica si
la mención va como enlace con el identificador de la persona,
`<a href="#" data-vss-mention="version:2.0,&lt;id-de-la-persona&gt;">@Nombre</a>`. El
identificador sale del campo `System.AssignedTo` que devuelve el MCP. Si no se puede obtener,
se escribe el nombre en negrita y **se avisa que la notificación no sale**, para que se le
avise por otro lado. ⚠ A confirmar en el primer uso real que el MCP devuelve ese identificador.

**El sello de auditoría** ([[auditar-tarea]], [[auditar-historia]]), cuando se pidió una
auditoría, llega como bloque de texto plano. Es constancia, no barrera: nadie lo exige para
arrancar el desarrollo. **No se reescribe**: `bin/verificar-sello` lo lee buscando líneas
exactas, como `Rev auditado: N`, **sobre el texto sin etiquetas**. Sólo se lo formatea para que no quede
en un renglón: la primera línea en `<p><b>…</b></p>` y el resto una por renglón con `<br>`,
**con el mismo texto, espacios incluidos**. Lo único que no se postea es lo que en el bloque de
la skill va después de `<-`: son notas para quien lee la skill, no para la tarjeta. Ejemplo
lleno, del sello de [[auditar-tarea]]:

```html
<p><b>Auditoria de Tarea - auditar-tarea</b></p>
<p>Veredicto: COMPLETA<br>
Fecha: AAAA-MM-DD<br>
Rev de la Tarea auditada: 7<br>
Historia padre: #<ID><br>
Rev de la Historia padre:  12<br>
Escenarios del padre encontrados: 4<br>
Hallazgos: 0  (el detalle, en el reporte)<br>
Pendientes a confirmar:<br>
- Ninguno</p>
```
