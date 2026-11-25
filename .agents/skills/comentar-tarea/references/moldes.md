# Moldes de comentario

Parte de la skill `comentar-tarea`: se lee cuando se redacta un cambio propuesto sobre una tarjeta congelada o un pendiente suelto. Las @menciones y el sello de auditoría, en [formato.md](formato.md).

## Molde del cambio propuesto (tarjeta congelada)

**Molde del cambio propuesto:**

```html
<p><b>Cambio propuesto</b> · la tarjeta está en el sprint y ya tomada, así que no se editó</p>
<p><a href="#" data-vss-mention="version:2.0,&lt;id-de-la-persona&gt;">@&lt;persona&gt;</a>, &lt;por qué hace falta el cambio: cambió el documento funcional · la auditoría encontró un hueco · le falta un campo&gt;. Revisalo antes de seguir trabajando sobre esta tarjeta.</p>
<hr>
<h3>Qué cambiaría</h3>
<ul>
<li><b>Se agrega:</b> &lt;qué, con su regla [RN-…]&gt;</li>
<li><b>Se modifica:</b> &lt;qué: valor actual → valor nuevo, con su regla&gt;</li>
<li><b>Se quita:</b> &lt;qué, o «nada»&gt;</li>
</ul>
<hr>
<h3>De dónde sale</h3>
<p>&lt;documento y versión, auditoría o pedido que lo origina&gt;</p>
<p><b>Aplicarlo o no lo decide una persona:</b> a mano en Azure, o en un ítem nuevo si lo que cambió es el pedido.</p>
```

Se escribe «se agrega / se modifica / se quita», no `+ ~ -`: los símbolos le sirven al que ya
sabe leer un DIFF, y esta tarjeta la lee un funcional también. Las tres líneas van siempre,
aunque alguna diga «nada»: así se ve que se revisó.

> **Ejemplo lleno** del renglón de la @mención y de una línea: *«@‹persona›, cambió el
> documento funcional. Revisalo antes de seguir trabajando sobre esta tarjeta.»* · *«Se
> modifica: código por defecto 02 → 03 [RN-RES-013]»*.

## Molde del pendiente suelto

**Molde del pendiente suelto:**

```html
<p><b>Pendientes a confirmar</b> · Tarea #&lt;id&gt;</p>
<ul>
<li>⚠ &lt;el hueco o el gris&gt; · &lt;qué se hizo mientras tanto&gt; · &lt;qué hace falta para cerrarlo, y quién lo define&gt;</li>
</ul>
```
