# Preview del árbol y dedup por nodo

Parte de la skill `sincronizar-backlog`: se lee al armar el preview del paso 4, antes de pedir el «sí»: forma del árbol, búsqueda de duplicados por nodo y qué se marca en cada uno.

## Forma del árbol

```
Épica: <título>                         [tag] [doc fuente]
├─ Feature: <título>                    [Parent: Épica]
│  ├─ Historia: <título>                [Parent: Feature] [Related: …]
│  └─ Historia: <título>                [Parent: Feature]
└─ Feature: <título>
   └─ Historia: <título>
```

## Dedup por nodo

Indicar, por nodo: tipo, título, campos clave, etiquetas y relaciones. Marcar qué
es **alta nueva** y qué **ya existe**. **Dedup obligatorio, con evidencia (no solo por
la ficha):** además de los #ID que la ficha ya trae en "Tickets derivados", hacer
**búsqueda activa en el board** por cada nodo propuesto (por **tag temático** — que trae
el subárbol existente — + **documento fuente** + **objetivo**, foco en abiertas),
**comparando por objetivo/alcance, NO por título** (un título distinto no prueba que no
sea duplicado). Cada nodo del árbol lleva su **Bloque de dedup**: consultas corridas +
candidatos (`#ID`+link+estado, o "0") + veredicto, y queda marcado **ALTA NUEVA / YA
EXISTE** (`#ID`+link, reutilizar/actualizar) **/ SOLAPA PARCIAL**. **Ante la duda, es
duplicado:** solapa plausible → marcar posible duplicado y **preguntar**, no crear.
Para cada **YA EXISTE**, correr también la **auditoría de calidad** (checklist del
tipo contra el work item leído completo) y anotar en el árbol qué le falta, si le
falta algo — [[deduplicacion-antes-de-crear]] §Auditoría de calidad. Si un **YA
EXISTE** está en un sprint y ya tomado (en modo equipo), se marca además **CONGELADA**: lo que le falta
se propone como comentario, no como edición ([[cambios-en-el-backlog]] §4). Los
equivalentes no se duplican: se reutilizan/actualizan (completando lo que falte)
y se relacionan. **Sin el Bloque de dedup por nodo, el árbol no se escribe.** Sin acceso al
tablero, el Bloque de dedup de cada nodo dice **SIN DATOS** —nunca «0 candidatos»— y el árbol
no se escribe: se entrega como texto con el aviso *«No busqué duplicados: buscalos vos en el tablero
antes de pegar.»* El "sí"
del paso cubre el contenido, el resultado de dedup y esas actualizaciones de completar
campos, no solo las altas nuevas. Luego **preguntar y esperar el "sí" explícito**.
