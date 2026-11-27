---
name: sincronizar-backlog
description: >-
  Tomar una ficha del Cerebro Digital (cerebro-digital/) y DERIVAR de ella el árbol
  de tickets de Azure DevOps: Épica → Features → Historias (las Tareas quedan para Dev/planning). Usar cuando
  se pida "bajá esta ficha/módulo al board", "derivá los tickets de esta doc",
  "creá la épica y las historias de X", "sincronizá el backlog con la documentación",
  "armá el backlog de este módulo", "/sincronizar-backlog". Aplica el mapeo OKF→ADO,
  la etiqueta temática, las relaciones (Parent/Related) y el documento fuente por
  referencia. PROPONE el árbol y lo crea por MCP SOLO con confirmación humana
  explícita (escribir en el board es IRREVERSIBLE). Registra los #ID en la ficha
  ("Tickets derivados") y en el historial, siempre POR REFERENCIA. TODO en español;
  PHI PROHIBIDO; no inventa (los #ID son dato duro, ⚠ hasta confirmar).
metadata:
  seccion: tickets
---

# Sincronizar backlog

> **Tablero local (`DEC-006`):** mismos GATEs, sin MCP: [contexto-adicional](references/contexto-adicional.md).

> **El método de redacción** —las reglas de oro, «Fuentes que deciden», el modo lote y la regla de cardinalidad— está en
> [[redaccion-de-tickets]]: se lee antes de redactar o derivar. Las barreras de escritura, en [[AGENTS]].

Toma una **ficha del Cerebro Digital** (`cerebro-digital/`) y baja
de ella el **árbol de work items** al board de Azure DevOps. Es la skill que
**conecta la documentación con el backlog**: doc → tickets → historial.

Escribe en un sistema externo, así que el control humano es obligatorio: **propone
el árbol y solo crea con un "sí" explícito**. La redacción fina de un ticket suelto
la cubre [[redactar-tarea]]; la escritura de un único work item ya redactado, la
cubre [[cargar-a-azure]]. Esta skill orquesta el **alta en lote coherente** desde
una ficha.

**Con más de una Historia, o con Tareas**: método de [[planificar-lote]], mismas reglas ([modo-lote](references/modo-lote.md)).

## Regla de oro (cultura del equipo)

- **Confirmación humana antes de escribir.** El árbol se muestra completo y se
  espera un "sí" del usuario. Sin confirmación no se llama a ninguna herramienta de
  escritura del MCP. Crear/editar es **irreversible** desde acá.
- **NO INVENTAR.** La estructura (qué Épica, qué Features, qué Historias) sale
  **1:1 del bloque `## Derivación a backlog`** de la ficha — no se segmenta la prosa
  «a ojo». Los **#ID son dato duro** (`⚠` hasta que el MCP los devuelva o el usuario
  los confirme). El conteo lo fija la **ficha enumerada**, no el modelo (ver
  [[organizacion-y-trazabilidad]] §5).
- **PHI PROHIBIDO.** Nada de datos reales al board: marcadores `<persona>`,
  `<documento>`, `<identificador>`, `<dato-sensible>`, `<telefono>`, `<direccion>`.
- **Enlazar, no copiar:** la traza va por referencia, nunca copiando la ficha ni el ticket ([trazabilidad](references/trazabilidad.md)).
- **Español (Argentina)**, sin emojis como íconos.

## Barreras (no negociables)

Las barreras de escritura son las de [[AGENTS]] («Automatización por MCP — barreras»), que se cargan en cada
sesión: TABLERO, TARJETA CONGELADA (en modo equipo, y se chequea antes que las demás), deduplicación,
confirmación, NIVEL y BORRADO / EDICIÓN DESTRUCTIVA. Valen como están escritas ahí; esta skill no las repite,
dice cómo las aplica.

- **Tablero: se verifica una vez, antes del primer `create_work_item`**; si el destino no es el autorizado o no se
  puede saber, **se aborta el árbol entero** ([[tablero-autorizado]]).
- **Tarjeta congelada (en modo equipo), nodo por nodo:** antes de cada `update_work_item` del árbol se leen
  `System.IterationPath` y `System.State`; si no se pueden leer, está congelada y lo que se quería cambiar va como
  comentario con el DIFF ([[comentar-tarea]], [[cambios-en-el-backlog]] §4).
- **Dedup por nodo:** cada nodo lleva su **Bloque de dedup** en el árbol del preview ([[deduplicacion-antes-de-crear]]);
  sin el de un nodo, el árbol no se escribe. Los equivalentes se reutilizan o se actualizan y se relacionan.
- **GATE de EXISTENCIA (bloqueante — encontrar ≠ crear igual).** Para **cada nodo** marcado `YA EXISTE`: queda **PROHIBIDO `create_work_item`** de ese nodo. Encontrarlo obliga a **frenar** ese nodo, no a crear un paralelo: se presenta el existente (`#ID` + link + estado) y se **pregunta** si ACTUALIZAR (`update_work_item`) o modificar, esperando el "sí" (en modo lote, esa pregunta va en el arranque, junto con las demás). Un lote **nunca** crea nodos nuevos en paralelo a los que la búsqueda ya encontró — aunque la ficha traiga otros nodos que sí son alta nueva, los `YA EXISTE` se excluyen del `create`. Buscar y encontrar sin frenar es exactamente la falla que este gate prohíbe.
- **NIVEL — profundidad y amplitud** (el GATE de [[AGENTS]]). *Profundidad:* por default el árbol baja **hasta Historia** (Épica → Feature → Historia); las **Tareas NO se crean**. En modo equipo, bajar a Tareas pide la confirmación del GATE (en modo lote, en el arranque, nombrando las Historias): *«¿esto es contexto dev/planning y estas Tareas son técnicas, para un dev?»*; sin ella, el árbol se queda en Historias. Si se confirma dev/planning, la IA **deriva las Tareas de la Historia** por su estructura técnica (por endpoint/caso de uso y **capa afectada** `api`/`application`/`domain`/`infra` + front, más una Tarea de test de integración si toca una dependencia externa) — el desglose es **juicio técnico de la reunión de devs, NO sale 1:1 de la ficha** como los niveles de arriba.
  Cada Tarea, con la plantilla detallada y su DoR: [tareas-derivadas](references/tareas-derivadas.md), al redactarla.
  **Las auditorías son opcionales y a pedido** (decisión de diseño del template): [[auditar-historia]] antes de derivar, [[analizar-tareas]] sobre el conjunto y [[auditar-tarea]] sobre cada Tarea **no corren solas** y su sello **no** es requisito para derivar ni para desarrollar. Si alguien las pide, corren como se describe a continuación, y lo que encuentren queda **como pendiente a confirmar** en la tarjeta ([[comentar-tarea]] §«Pendientes a confirmar»), sin frenar.
  Cómo corren cuando se piden: [auditorias-a-pedido](references/auditorias-a-pedido.md).
  **Sin auditoría se derivan Tareas igual**; lo único que no se deriva es una Historia **sin ningún Escenario** —eso no es auditoría, es el DoR: sin Escenarios no hay qué mapear a tests—.
  *Amplitud:* el conteo de Épicas/Features/Historias sale **1:1 del bloque `## Derivación a backlog`** de la ficha — **default 1 Épica**; crear >1 Épica exige que la ficha declare **>1 slice**. Nunca inferir el rol ni multiplicar nodos; ante ambigüedad, preguntar.
- **Proponer y crear son turnos distintos:** el paso 4 (mostrar el árbol) **cierra el turno**; el paso 5 (escribir), sólo con un «sí» nuevo.
- **Solo para bajar una ficha/módulo ENTERO.** Esta skill arma el árbol en lote. Si
  el pedido es **un** ticket suelto, NO se usa esta skill: se usa
  [[redactar-tarea]] + [[cargar-a-azure]]. Nunca convertir un pedido de un ítem en
  un árbol de muchos.
- **No inventar #ID ni estructura como si fuera dato.** Propuesta + confirmación.
- **PHI prohibido** en lo que se escribe al board.
- **Provenance/autoría:** la escritura queda auditada por el dueño del PAT; no usar
  un PAT ajeno. El token es una password: si se expone, se rota.
- **Si la ficha tiene `⚠ (pendiente)` que afectan el alcance, no se deriva:** se
  vuelve al Cerebro (`cerebro-digital/`) a cerrarlos.

## Precondiciones

> **El árbol lo cuenta un script.** Antes de redactar un solo nodo se corre
> `python bin/derivar-arbol.py <ficha>`: devuelve las Épicas, Features e Historias 1:1 con sus padres,
> reglas, la etiqueta única y el documento fuente, o dice por qué la ficha **no se deriva** (sin bloque,
> con `⚠`, incoherente). Lo que el script no lista, no se crea; lo que lista, no se funde ni se parte.

1. **Ficha con bloque `## Derivación a backlog` enumerado y cerrado**, sin `⚠` que afecte el alcance y sin
   referencias colgadas; si no, **no se deriva**. Al verificarla: [leer-la-ficha](references/leer-la-ficha.md).
2. **MCP de Azure configurado y PAT con escritura** (Work Items Read & Write).
   Setup: [[integracion-azure-mcp/00-index]]. Si falta el MCP o el PAT es de solo
   lectura → **no se escribe**: se entrega el árbol propuesto como texto pegable y
   se le dice al usuario que lo cargue a mano.

## Flujo

### 1. Leer la ficha y su bloque de derivación
Qué se extrae y cuándo se frena: [leer-la-ficha](references/leer-la-ficha.md).

### 2. Aplicar el mapeo por vertical slices → ADO
Mapeo **1:1** con el bloque y cada nodo con su plantilla: [mapeo-y-cardinalidad](references/mapeo-y-cardinalidad.md).

### 3. Adjuntar trazabilidad a cada nodo
Tag único, relaciones y documento fuente de cada nodo: [trazabilidad](references/trazabilidad.md).

### 4. Proponer el árbol y esperar confirmación (obligatorio)
Mostrar el **árbol completo** antes de tocar nada:
forma del árbol y **Bloque de dedup por nodo** (tag + documento fuente + objetivo; objetivo, no título; **ante la
duda, es duplicado**), con cada nodo marcado ALTA NUEVA / YA EXISTE / SOLAPA PARCIAL / CONGELADA: [preview-y-dedup-por-nodo](references/preview-y-dedup-por-nodo.md).
**Sin el Bloque de dedup de un nodo, o sin acceso al tablero (SIN DATOS), el árbol no se escribe.** El «sí» cubre
contenido, dedup y lo que se completa en los YA EXISTE. Luego **preguntar y esperar el "sí" explícito**.

### 5. Crear/actualizar por MCP
**Verificar primero el tablero autorizado** ([[tablero-autorizado]]): todo el lote va a org `{{AZURE_ORG}}` / proyecto `{{AZURE_PROYECTO}}` / team `{{AZURE_TEAM}}`. Si el destino fuera otro o no se puede determinar, **abortar el lote** con la advertencia — no se escribe nada.

Con el "sí" dado, ejecutar en orden padre→hijo:

- `create_work_item` para las altas; `update_work_item` para las ediciones.
- Vínculos con `manage_work_item_link`, **siempre desde la hija; nunca se edita el padre para colgarle un hijo**:
  [parent-y-related](references/parent-y-related.md).
- **Al actualizar una tarjeta que está asignada o seguida** (re-sincronización tras
  un cambio del doc), disparar el **protocolo de aviso**: comentario con @mención
  de qué cambió, para que quien la trabaja no
  siga sobre una versión vieja. Detalle: [[cambios-en-el-backlog]].
- **Una tarjeta congelada** (en un sprint y ya tomada, en modo equipo) **sale del lote de ediciones**: no
  lleva `update_work_item`. Su DIFF va **como comentario** con @mención, y el
  preview del paso 4 ya la mostró marcada `CONGELADA` para que el "sí" no la incluya por
  error. Detalle: [[cambios-en-el-backlog]] §4.

Escribir el árbol confirmado; no encadenar altas nuevas no incluidas en el "sí".

### 6. Registrar la traza (por referencia) — en la ficha y en el historial
Los `#ID` a «Tickets derivados» de la ficha y una fila a [[historial/INDICE]], por referencia:
[trazabilidad](references/trazabilidad.md), cerrado el alta.

### 7. Reportar
Devolver los **#ID/URL** creados o actualizados y qué quedó enlazado. Silencio al
entregar: al grano.

## Cuándo leer cada referencia

| Referencia | Cuándo |
|---|---|
| [leer-la-ficha](references/leer-la-ficha.md) | Precondición 1 y paso 1 |
| [mapeo-y-cardinalidad](references/mapeo-y-cardinalidad.md) | Paso 2 |
| [trazabilidad](references/trazabilidad.md) | Pasos 3 y 6 |
| [preview-y-dedup-por-nodo](references/preview-y-dedup-por-nodo.md) | Paso 4, antes del «sí» |
| [parent-y-related](references/parent-y-related.md) | Paso 5 |
| [tareas-derivadas](references/tareas-derivadas.md) | NIVEL confirmado: cada Tarea |
| [auditorias-a-pedido](references/auditorias-a-pedido.md) | Si se pide una auditoría |
| [modo-lote](references/modo-lote.md) | Más de una Historia, o con Tareas |
| [contexto-adicional](references/contexto-adicional.md) | Tablero local; documento de apoyo |
| [ejemplo](references/ejemplo.md) | Ver el flujo aplicado |
