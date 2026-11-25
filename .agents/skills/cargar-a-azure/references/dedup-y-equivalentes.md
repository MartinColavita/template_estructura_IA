# Bloque de dedup y equivalentes

Parte de la skill `cargar-a-azure`: se lee cuando se arma el Bloque de dedup (§1b) y cuando la búsqueda encontró un equivalente o un solapamiento (§1c).

## Cómo se busca (§1b)

Antes del preview, buscar en el board si el ítem **ya existe**, usando
`search_work_items` / `list_work_items`, por **tag temático** (trae el subárbol del
tema) + **documento fuente** + **objetivo** (textual), foco en abiertas. **Comparar por
objetivo/alcance, NO por título:** un título distinto no prueba que no sea duplicado
(es la causa #1 de repetidos). **Ante la duda, es duplicado:** cualquier abierto del
mismo tema/doc cuyo objetivo se solape → **posible duplicado → preguntar**, nunca crear
en automático.

## Qué produce la búsqueda (§1b)

Esta búsqueda produce el **Bloque de dedup** que va **sí o sí** en el preview del paso 2
(consultas corridas · candidatos `#ID`+link+estado · veredicto por candidato). Si hay
un **equivalente**, **no crear**: avisar con `#ID`+link y proponer **reutilizar/
actualizar** + **relacionar** (Related). Si hay **solapamiento parcial**, informar y
esperar decisión. Si no se pudo consultar el board (MCP/PAT), **no se escribe**: se
avisa que no se pudo verificar dedup. Detalle: [[deduplicacion-antes-de-crear]].

## Qué lleva el Bloque en el preview (§2)

- **Bloque de dedup (arriba de todo, obligatorio):** consultas corridas (tag ·
  objetivo · doc fuente) · candidatos `#ID`+link+estado (o "0 candidatos") · veredicto
  por candidato (`equivalente`/`solapa`/`distinto` + por qué). **Sin este bloque el
  preview es inválido y NO se escribe** — da igual que el resto esté perfecto.

### 1c. Auditar calidad del equivalente (si 1b encontró uno)
Leer el work item completo (`get_work_item`) y correr el checklist del tipo
([[checklists/checklist-historia]] / [[checklists/checklist-bug]] /
[[checklists/checklist-habilitador]] + [[definicion-preparado-terminado]]).
Para **Épica** va [[checklists/checklist-epica]] y para **Feature**
[[checklists/checklist-caracteristica]]. Son justo los dos nodos que más se reutilizan
(siempre existen, siempre se marcan YA EXISTE), así que este paso es el que más corre:
antes no había checklist para ellos y se evaporaba en silencio. Si
cumple, sigue como "reutilizar/relacionar" sin tocar nada. Si le falta algo, el
preview del paso 2 pasa de "no se crea nada" a un preview de **edición**
(`update_work_item`) con los campos concretos a completar — mismo GATE de
confirmación que un alta. Si el equivalente está **congelado**, lo que le falta va como
comentario, no como edición. Detalle: [[deduplicacion-antes-de-crear]] §Auditoría
de calidad.
