# Por qué existe, cuándo conviene correrla, dónde entra y un ejemplo

Parte de la skill `auditar-historia`: se lee cuando hace falta el porqué de la skill, por qué conviene correrla del lado dev, su lugar en el pipeline o un reporte de ejemplo.

> **Por qué existe esta skill.** Todo el aparato que protege el nivel Tarea son **conteos
> contra artefactos que produce la Historia** (los `Escenario:` del Gherkin, las `[RN-…]`
> que declara) **o la ficha** (el bloque enumerado). Si esos artefactos están vacíos o mal,
> el aparato de abajo **no falla: da verde**. Se construyó un verificador de precisión
> apoyado sobre un insumo que nadie medía.
>
> Y el costo es asimétrico: un hueco en una Tarea cuesta **una Tarea**. Un hueco en el
> Gherkin o en el bloque de derivación se multiplica por **todas sus Tareas** y —por la
> Regla de cardinalidad, que obliga a copiar la enumeración sin criterio propio— se
> reproduce **idéntico en las cuatro herramientas del ecosistema**. Es el único punto del
> pipeline donde el determinismo juega **en contra**: un flujo que quedó fuera de la
> enumeración no puede volverse Historia **nunca**, en ninguna herramienta.

## Cuándo conviene correrla

Si se pide, conviene correrla **del lado dev**, en el momento en que la calidad del
Gherkin empieza a importar de verdad: **cuando se van a derivar Tareas de esa Historia**.
Ahí los Escenarios dejan de ser texto y pasan a ser **tests**, y un `Entonces` que no se
puede observar se convierte en un test que nadie puede escribir.

> **Por qué en el lote también corre al crear la Historia.** Las dudas de una Historia aparecen
> cuando se auditan, y si eso pasa recién al derivar Tareas, se pregunta en la reunión con los
> devs lo que se podría haber cerrado antes (el 2026-09-30, dos auditorías dieron decenas de dudas
> en plena planificación). Si la Historia cambia después, el sello vence; re-auditarla es opcional.

> **Por qué, si se pide, conviene correrla acá y no cuando se escribe la Historia.** Poner la auditoría
> en el momento del funcional obligaría a que él invoque algo — y no invoca nada, ni tiene
> por qué. Además sería prematuro: una Historia recién escrita todavía va a cambiar. El
> momento correcto es **el último instante antes de que alguien la use para programar**.
> Si ya hay sello vigente, no se vuelve a auditar.

## Dónde entra en el flujo

```
ficha del Cerebro (con su bloque de derivacion)
   -> sincronizar-backlog: propone Epica/Feature/Historia, crea con confirmacion
   -> [auditar-historia]  (2do chequeo del nivel funcional, OPCIONAL, a pedido)  <- esta skill
   -> redactar-tarea (DoR) -> [analizar-tareas, a pedido] -> cargar-a-azure
   -> [auditar-tarea]     (2do chequeo del nivel tecnico, OPCIONAL, a pedido)
   -> guiar-tdd -> verificar-tdd
```

---

### Ejemplo (genérico)

> Una Historia declara 3 Escenarios; uno dice *«Entonces el sistema procesa correctamente
> la solicitud»*. La ficha fuente enumera 3 flujos, y en su prosa hay un cuarto camino
> («el supervisor también puede ejecutarlo sin solicitud previa») que no está enumerado ni
> declarado fuera de alcance.
>
> La auditoría reporta **CON HUECOS**:
> - *Chequeo 3:* el `Entonces` del Escenario 2 usa «correctamente». No se puede convertir en
>   test; el dev tendría que inventar el criterio. **Pregunta:** ¿qué resultado observable
>   distingue «procesado» de «no procesado»?
> - *Chequeo 14:* el camino del supervisor está en la prosa y no en la enumeración. Por la
>   Regla de cardinalidad **no puede volverse Historia nunca**. **Pregunta:** ¿se agrega como
>   `[F-04]` o se declara fuera de alcance con motivo?
>
> No corrige la ficha ni la Historia: deja los dos ítems redactados para que el humano
> decida y la skill que corresponda los cargue en otro turno.
