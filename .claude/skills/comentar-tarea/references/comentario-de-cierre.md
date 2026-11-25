# Comentario de cierre de desarrollo: molde y casos

Parte de la skill `comentar-tarea`: se lee cuando se redacta el comentario de cierre de una Tarea, después de correr `bin/datos-cierre.py`.

> **Lo aprendido no se queda en el comentario.** Si el desarrollo confirmó o descubrió algo del
> negocio (una respuesta a un pendiente, una regla precisada), eso va al Cerebro por la Consulta
> Interactiva de Decisión de [[cerebro-orquestador]], no sólo a la tarjeta. El comentario lo lista
> en «Pendientes a confirmar» o en «Conocimiento para el Cerebro»; el Cerebro lo guarda. Y lo que
> el desarrollo mostró de **la aplicación** —qué módulo quedó construido y qué expone, un bug con su
> causa, una deuda aceptada— va a `<modulo>/aplicacion/` (`mapa.md`, `aprendizajes.md`, `deuda.md`),
> con el `#ID` y el Merge Request como fuente.

**Molde:**

```html
<p><b>Desarrollo terminado</b> · Tarea #&lt;id&gt; · Historia #&lt;id-del-padre&gt;</p>
<ul>
<li><b>Rama:</b> &lt;rama&gt; (&lt;pusheada | ⚠ sin pushear&gt;)</li>
<li><b>Merge Request:</b> <a href="&lt;link-del-merge-request&gt;">!&lt;número&gt;</a></li>
<li><b>Último commit:</b> &lt;hash corto&gt;</li>
<li><b>Fecha:</b> &lt;AAAA-MM-DD&gt;</li>
</ul>
<hr>
<h3>Qué se hizo</h3>
<p>&lt;dos o tres líneas en criollo: qué cambia para el que usa el sistema&gt;</p>
<hr>
<h3>Resumen técnico</h3>
<ul>
<li><b>Slice:</b> &lt;slice&gt;</li>
<li><b>Contrato:</b> &lt;endpoints tocados, y qué cambió en el openapi.yaml&gt;</li>
<li><b>Tests:</b> &lt;N&gt; de &lt;M&gt; ítems de «Tests a escribir PRIMERO», cada uno con su rojo antes del verde, verificado sobre el historial de trabajo</li>
<li><b>Commits:</b> &lt;cantidad, agrupados por importancia (alrededor de 10)&gt; en el Merge Request (último commit &lt;hash corto&gt; de la rama de la Tarea) · &lt;N&gt; commits de trabajo, verificados antes de reorganizar, en la rama evidencia/&lt;ID&gt; de origin</li>
<li><b>Cambios que rompen:</b> &lt;ninguno | cuáles | ⚠ sin dato&gt;</li>
<li><b>Dependencias nuevas:</b> &lt;ninguna | cuáles | ⚠ sin dato&gt;</li>
</ul>
<hr>
<h3>Verificaciones</h3>
<table>
<tr><th>Control</th><th>Qué contesta</th><th>Veredicto</th></tr>
<tr><td>Quién verificó</td><td>¿Otro agente que el que programó (DEC-005)?</td><td>&lt;motor&gt; v&lt;versión&gt; · &lt;modelo o worktree&gt;</td></tr>
<tr><td>verificar-tdd</td><td>¿Hubo rojo antes del verde?</td><td>&lt;veredicto&gt;</td></tr>
<tr><td>Revisión de código</td><td>¿Está bien escrito?</td><td>&lt;veredicto&gt;</td></tr>
<tr><td>auditar-codigo</td><td>¿Cumple la Tarea, sin PHI ni secretos?</td><td>&lt;veredicto&gt;</td></tr>
</table>
<hr>
<h3>Lo que quedó afuera</h3>
<ul>
<li>&lt;qué no se hizo, y por qué | «Nada» | ⚠ sin dato&gt;</li>
</ul>
<hr>
<h3>Pendientes a confirmar</h3>
<ul>
<li>⚠ &lt;el hueco o el gris&gt; · &lt;qué se hizo mientras tanto&gt; · &lt;qué hace falta para cerrarlo, y quién lo define&gt;</li>
</ul>
```

**Cómo se llenan los casos que no son el feliz**, sin cambiar la forma:

| Si… | Se escribe |
|---|---|
| La rama no se pusheó | `(⚠ sin pushear)` en lugar de `(pusheada)` |
| El desarrollo tocó dos slices | Los dos, y el motivo: `<slice-1> y <slice-2>, porque …` |
| El contrato no cambió | `sin cambios en el contrato` |
| No se cubrieron todos los ítems de la lista | `<N> de <M>`, y abajo cuáles faltan. **No es un desarrollo terminado**: se dice |
| No hay Merge Request | `todavía no abierto` en lugar del link, y la prosa lleva *«según el resumen del desarrollo»* |
| Un control no corrió | `SIN DATOS` en su fila. No es aprobado |
| Un control dio hallazgos | `HALLAZGO` y, en una línea abajo de la tabla, cuántos y cuál es el bloqueante |
| La fuente dice que no quedó nada afuera | `<li>Nada</li>`. La sección no se borra: su ausencia no dice si se revisó |
| No se pudo leer un dato | `⚠ sin dato` |
| Hay número de Merge Request pero no su link | `!15 (⚠ sin link)`, **sin** `<a>`: un enlace con `href` vacío o inventado lleva a ningún lado |
| No se sabe el slice | `⚠ sin dato`. El slice es uno de los declarados en [[contexto-proyecto]] (`<slice-1>` · `<slice-2>` · `<slice-n>`); **nunca** el nombre del producto |
| No quedó ningún pendiente | `<li>Ninguno</li>`, si el worker lo dijo. La sección no se borra |
