---
id: pipeline-doc-a-tickets
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: "Pipeline Cerebro Digital → tickets de Azure → histórico (flujo, trazabilidad por referencia, skills y reglas)"
author: equipo
tags: [pipeline, cerebro-digital, azure-devops, trazabilidad, mcp, skills, okf, historial]
last_updated: 2026-10-01
---

# Pipeline: del Cerebro Digital a los tickets de Azure

El paquete no es solo un redactor de tickets: es un **pipeline** de tres etapas encadenadas.

```
Cerebro Digital (documentación .md)  →  tickets en Azure DevOps (vía MCP)  →  histórico (doc ↔ ticket)
        [conocimiento del proyecto]        [Épica/Feature/Historia/Tarea]        [trazabilidad por referencia]
```

La documentación funcional/técnica del proyecto (el **Cerebro Digital**) es la **única fuente de verdad** del dominio. Los tickets **se derivan** de esa documentación, no al revés; y el **histórico** guarda el vínculo entre cada documento y los work items que produjo, siempre **por referencia** (rutas + IDs), nunca copiando contenido.

Agnóstico de dominio: el Cerebro Digital lo aporta el proyecto destino. Los recuadros "Ejemplo (genérico)" son solo ilustrativos.

Relacionados: [[organizacion-y-trazabilidad]] · [[integracion-azure-mcp/00-index]] · [[historias-de-usuario]] · [[mapa-campos-azure]]

---

## 1. El flujo, paso a paso

El pipeline va de una documentación **ya validada** a work items **confirmados** en el board. Nada se escribe en Azure sin un "sí" humano.

### (a) Documento del Cerebro Digital validado
El punto de partida es una ficha del Cerebro Digital (un `.md` en formato OKF: frontmatter YAML + wikilinks) que describe un módulo, un flujo o un desglose técnico y que el equipo **considera vigente**. Si el documento todavía no existe o está incompleto, primero se lo crea/mejora en el Cerebro (`cerebro-digital/` y sus skills). **No se generan tickets desde documentación sin validar**: un ticket es tan bueno como la ficha de la que sale.

### (b) La IA propone los tickets con el mapeo OKF → ADO
A partir de la ficha, la IA **descompone** el contenido en la jerarquía de Azure con el mapeo **Vertical slice→Épica · Capacidad→Feature · Flujo→Historia · Técnico→Tarea** (detalle en [[organizacion-y-trazabilidad]] §5).

La IA (en modo **funcional**) **propone** un **árbol** hasta Historia (Épica → Features → Historias; las **Tareas** son un segundo momento de dev/planning y **no** se proponen acá) con: título sugerido, tipo justificado, campos redactados (descripción, criterios en Gherkin español, reglas `[RN-…]`), **etiqueta temática** sin prefijo, **relaciones** propuestas por título/tema y la línea **Documento fuente** apuntando a la ficha. Todo lo que sea dato duro no confirmado (versión, sprint, `#ID` de padres/relacionadas) va marcado `⚠`. El **conteo** del árbol (cuántas Épicas/Features/Historias) **no lo decide el modelo**: sale **1:1** del bloque enumerado y cerrado `## Derivación a backlog` de la ficha —1 Épica por `[S-nn]`, 1 Feature por `[C-nn]`, 1 Historia por `[F-nn]`, 0 Tareas por default—. La IA **copia** esa lista; no segmenta la prosa a ojo ni re-decide la granularidad. Si la ficha no trae el bloque (o tiene `⚠`), **no se deriva**: se frena y se manda a curar. Ver [[organizacion-y-trazabilidad]] §5 y la «Regla de cardinalidad» del [[AGENTS]].

### (c) Confirmación humana del árbol
La IA muestra el **árbol propuesto completo** (qué work items, con qué jerarquía, qué tags, qué enlaces) y **espera aprobación explícita**. El árbol salió **1:1** del bloque `## Derivación a backlog` de la ficha, así que el humano **no re-decide la granularidad acá** —esa decisión ya la cerró la curación al enumerar—: **la unidad de Historia es el flujo listado en ese bloque, NO la pantalla** (decisión cerrada). El humano confirma el árbol, completa los datos duros `⚠` y da el "dale". **Hasta acá no se tocó Azure.** Este es el punto de control del pipeline: se confirma sobre el **contenido final**, nunca sobre supuestos sin resolver. Ver [[organizacion-y-trazabilidad]] §5 y la «Regla de cardinalidad» del [[AGENTS]].

### (d) Alta / edición por MCP de Azure
Con la confirmación, la IA **crea o actualiza** los work items vía el **MCP de Azure DevOps** (mismo mecanismo que ya usa el equipo): `create_work_item` para altas, `update_work_item` para ediciones, `manage_work_item_link` para materializar los enlaces Parent/Child/Related, y `get_work_item` / `search_work_items` / `list_work_items` para resolver los `#ID` que faltaban. El alta puede ser en lote (toda la jerarquía en una operación), pero **solo tras la confirmación de (c)**. Ver [[integracion-azure-mcp/00-index]].

### (e) Se registran los IDs generados
Azure devuelve el **ID real** de cada work item creado. La IA:
- Estampa en cada ticket la línea **Documento fuente** con la ruta de la ficha (si aún no estaba).
- Deja los **IDs derivados** en la ficha del Cerebro Digital (§2).
- Agrega **una fila en [[historial/INDICE]]** con el vínculo doc ↔ ticket (ruta + IDs + resumen de una línea). Es un log resumido; el `.md` detallado (molde en [[historial/README]]) solo para los `gold`.

Con esto el círculo queda cerrado y trazable en los dos sentidos.

> **Ejemplo (genérico):** la ficha `conocimiento/funcional/cancelacion-de-reserva.md` declara en su bloque `## Derivación a backlog` un slice `[S-01]`, una capacidad `[C-01]` y dos flujos `[F-01]`/`[F-02]`. De ahí la IA deriva **1:1** una Épica "Cancelación de reservas" (=S-01), una Feature por la capacidad (=C-01) y **dos Historias porque la ficha lista dos flujos** ("Solicitar la cancelación desde el rol solicitante" =F-01, "Ejecutar/desestimar la cancelación desde el rol gestor" =F-02), todas con tag `cancelacion`. El equipo confirma el árbol y resuelve el sprint (`⚠`); la IA las crea por MCP, obtiene los IDs y los anota en la ficha y en el historial. Bloque ilustrativo.

---

## 2. Trazabilidad bidireccional **por referencia**

El vínculo doc ↔ ticket se guarda en **los dos sentidos**, y en ambos **por referencia** (una ruta, una lista de IDs), **nunca copiando el cuerpo del documento**.

**Del ticket al documento** — cada work item lleva, dentro de su Descripción, la línea:
```
Documento fuente: <ruta/a/la/ficha.md> (link al repo)
```
Una sola línea. Permite ir del backlog al origen funcional.

**Del documento al ticket** — la ficha del Cerebro Digital lleva un bloque con los **tickets derivados**, solo IDs:
```
Tickets derivados (Azure): #<ID-épica>, #<ID-feature>, #<ID-historia-1>, #<ID-tarea-1> …
```
Permite ir del origen funcional al backlog.

**El historial** — la **fila** en [[historial/INDICE]] guarda el vínculo: ruta del doc + IDs generados + fecha + resumen + estado. Es la memoria/trazabilidad del pipeline, en formato log resumido (el `.md` detallado, solo para `gold`).

### Por qué por referencia: enlazar, no copiar

- **La memoria/histórico NO crece con el tamaño del documento.** El costo de trazar un doc es **constante** (una ruta + unos IDs), sea la ficha de 10 líneas o de 500. Si en cambio se copiara el contenido del documento en cada ticket y en cada registro del historial, todo se infla y el histórico crece proporcional al tamaño de los docs.
- **No se desincroniza.** La referencia apunta siempre a la **versión viva** de la ficha. Si mañana cambia una regla de negocio, se edita el documento en un solo lugar; el ticket y el historial siguen apuntando al mismo sitio, sin arrastrar una copia vieja que contradiga al original.
- **Fuente única de verdad.** El dominio vive en el Cerebro Digital. Duplicarlo en el board crearía dos verdades que se pelean. Regla del paquete: **enlazar, no copiar** (ver [[organizacion-y-trazabilidad]] §3).

> **Ejemplo (genérico):** la Historia "Solicitar la cancelación" lleva `Documento fuente: conocimiento/funcional/cancelacion-de-reserva.md`; la ficha `cancelacion-de-reserva` lleva `Tickets derivados: #<ID-1>, #<ID-2>`; la fila en `historial/INDICE.md` ata las dos puntas (tema, `#ID`, ruta del doc y resumen). Ninguno copia el texto de la ficha. Bloque ilustrativo.

---

## 3. El rol de las skills en el pipeline

El pipeline lo cubren **catorce skills**, unificadas en `cerebro-digital/configuracion-ia/skills/` (frontmatter `name` + `description`). **Ocho no tocan el board** (producen texto/propuestas, analizan o solo consultan); las otras seis **escriben en el board por MCP**, siempre con confirmación humana. **Tres de esas seis son los segundos chequeos** —`analizar-tareas`, `auditar-historia`, `auditar-tarea`— y son **opcionales, a pedido** (decisión del equipo): no corren solas ni frenan el flujo, y lo que encuentran queda como pendiente a confirmar en la tarjeta. El mapa los muestra para que se sepa dónde se pueden pedir. *(Crear/mantener las fichas del Cerebro es tarea del Cerebro `cerebro-digital/`, no de este paquete.)*

| Skill | Etapa del pipeline | Qué hace | ¿Escribe? |
|---|---|---|---|
| [[redactar-tarea]] | (b) un ticket suelto | Toma un pedido pobre / una idea / un ID de Azure y redacta **un** work item profesional (decide tipo, Gherkin, tags, relaciones, documento fuente). **Solo redacta**. | No (texto pegable) |
| [[estimar-story-points]] | (b) apoyo a la redacción | Propone los **Puntos de historia** de un ticket a partir de señales de complejidad + señales de tokens; sugiere partir la historia si da 13 o más. **Solo estima**. | No (propuesta) |
| [[consultar-backlog]] | (lectura/auditoría del board) | Consulta si una funcionalidad ya tiene historia y dónde, audita la cobertura (fichas sin ticket, tickets sin doc fuente) y detecta **desfases** (doc vigente vs. tarjeta). **Solo lee**. | No (solo lectura) |
| [[sincronizar-backlog]] | (b)→(e) desde una ficha, en lote | Baja una **ficha entera** al board: propone el **árbol** (Épica→Features→Historias) con el mapeo OKF→ADO, tags, relaciones y documento fuente; con confirmación **crea/edita por MCP**, materializa enlaces y **registra la traza** (Tickets derivados en la ficha + fila en el historial). También **re-sincroniza** una ficha ya bajada (actualiza los IDs sin duplicar). | Sí, con confirmación |
| [[planificar-lote]] | (b)→(e) varios ítems a la vez | **Modo lote**: deriva las Historias de una ficha, las Tareas de varias Historias, o las dos, con agentes en paralelo y **dos turnos humanos** —el arranque (alcance, nivel y todas las dudas juntas) y el cierre (una tabla con el lote y un "sí" que lo escribe)—. Lo que definen la maqueta o el Cerebro no se pregunta; las auditorías son opcionales y, si se piden, las corre un agente distinto. | Sí, con el "sí" del cierre |
| [[analizar-tareas]] | (c) antes de crear el set de Tareas, **sólo si se pide** | Chequea la **consistencia del conjunto** de Tareas que salió de partir una Historia: contratos que no se pisan, cada `[RN-…]` cubierta, cada **Escenario** del padre con una Tarea que lo cubra y un test que lo verifique, sin huecos ni solapes. **Solo analiza**; lo que encuentra sale como pregunta. | No (análisis) |
| [[auditar-historia]] | (c) antes de derivar Tareas, **sólo si se pide** | **Segundo chequeo del nivel funcional, opcional, por un agente distinto** del que la redactó: que el Gherkin sea verificable, que las reglas citadas existan y digan lo que se les atribuye, y que el documento fuente no las contradiga. **Solo lee**; deja su sello en la tarjeta con confirmación. | No (solo lectura) |
| [[auditar-tarea]] | (d) después de crear la Tarea, **sólo si se pide** (no frena el desarrollo) | **Segundo chequeo técnico, opcional, por un agente distinto**: que a la lista «Tests a escribir PRIMERO» no le falte ningún caso y que cada test pueda ponerse en rojo. Un caso que falta en la lista **no se prueba nunca** y el pipeline queda verde igual. **Solo lee**; deja su sello con confirmación. | No (solo lectura) |
| [[cargar-a-azure]] | (d)-(e) alta de 1 item | Crea/actualiza **un** work item ya redactado por MCP, materializa sus enlaces, resuelve `#ID` y devuelve el ID/link. | Sí, con confirmación |
| [[tomar-tarea]] | (posterior) gestión del board | Se **asigna** una tarjeta y la pasa a **Active**, avisando si ya está tomada por otra persona para **evitar la desincronización**. | Sí (asignación/estado), con confirmación |
| [[comentar-tarea]] | (posterior) gestión del board | Deja (o lee) un comentario en la tarjeta vía `System.History` —avance, duda, decisión, y el **comentario de cierre** al terminar un desarrollo— sin tocar el resto de los campos. Es lo único que entra en una **tarjeta congelada**. | Sí (comentario), con confirmación |

**Tres caminos, según la escala:**
- **De una ficha entera → backlog** (el pipeline): ficha del Cerebro (`cerebro-digital/`) `→ sincronizar-backlog` (propone el árbol, confirmás, crea por MCP y registra la traza).
- **Varios ítems a la vez** (las Tareas de varias Historias, o una ficha con sus Tareas): `planificar-lote` (arranque → redacción en paralelo, y auditorías si se piden → cierre → escritura y traza).
- **De un pedido suelto → un ticket**: `redactar-tarea → (estimar-story-points) → (confirmación) → cargar-a-azure`.

Una vez que el ticket está en el board, `tomar-tarea` y `comentar-tarea` cubren la **gestión** de la tarjeta (asignarse, mover a Active, comentar el avance), y `consultar-backlog` responde consultas y **audita** cobertura y desfases (solo lectura). Cuando un doc cambia y la tarjeta ya existe, el protocolo de [[cambios-en-el-backlog]] coordina el DIFF y el aviso.

**Escriben en el board seis skills**: `sincronizar-backlog` (árbol en lote), `planificar-lote` (varios ítems con un cierre), `cargar-a-azure` (un item), `tomar-tarea` (asignación + estado Active), `desarrollar-asignadas` (toma la tarjeta y deja el comentario de cierre) y `comentar-tarea` (comentario vía `System.History`). Todas, **solo con confirmación humana** (o la autorización escrita de `DEC-005` confirmada: [[AGENTS]], «Autorización permanente»). Una tarjeta **congelada** —en un sprint y ya tomada— sólo se comenta: las otras cuatro frenan y ofrecen dejar el cambio como comentario. Colgarle un hijo nuevo sigue permitido, porque se escribe en el hijo ([[cambios-en-el-backlog]] §4). Las tres de solo lectura —`redactar-tarea`, `estimar-story-points` y `consultar-backlog`— no tocan el board. Las skills comparten las reglas de [[AGENTS]]: el MCP es solo el transporte; las reglas de redacción y trazabilidad siguen valiendo íntegras. Todas están unificadas en `cerebro-digital/configuracion-ia/skills/`.

---

## 4. Reglas del pipeline (no negociables)

Aplican en toda etapa y priman sobre cualquier atajo (ver [[AGENTS]]).

- **No inventar.** Los **datos duros no se inventan jamás**: versión, ambiente, fecha, `#ID` de work items, sprint/iteración, y cualquier regla de negocio o estado del dominio que no esté en el Cerebro Digital. Lo que no está confirmado va `(pendiente)` / `⚠` y **se pregunta**. La IA **propone** estructura, títulos y criterios tentativos; **afirma** solo lo que puede respaldar.
- **Confirmación humana antes de escribir en Azure.** **Lectura libre, escritura con confirmación.** Leer tarjetas por MCP no requiere permiso adicional. Crear o modificar work items es una acción **con efecto e irreversible**: se hace solo con un "sí" explícito sobre el **contenido final** del árbol (etapa c), nunca sobre supuestos `⚠` sin resolver. El alta en lote no es excepción.
- **PHI prohibido.** Nunca datos personales sensibles ni personales reales, **ni en las fichas, ni en los tickets, ni en el historial**. Usar marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<dato-sensible>`. Describir la estructura, no el dato. Si el insumo trae PHI, se reemplaza por marcadores y se avisa.
- **Trazabilidad por referencia.** El vínculo doc ↔ ticket se guarda como ruta + IDs, **nunca copiando el contenido** del documento (§2): así el histórico no crece con el tamaño de los docs y no se desincroniza.
- **Provenance / jerarquía de fuentes.** Lo observado en el sistema real manda sobre la spec, y la spec sobre lo derivado. Ante conflicto, gana lo observado y se reporta el desvío.

> **Ejemplo (genérico):** al bajar un módulo (p. ej. "Cancelación de reservas") al board, la IA no inventa el sprint ni el `#ID` de la Épica madre: los marca `⚠` y pregunta. Reemplaza cualquier `<persona>`/`<documento>` que apareciera en la ficha por marcadores. Muestra el árbol (Épica + Feature por capacidad + Historias, tag `cancelacion`; **sin Tareas** por default — son un segundo momento dev/planning) y espera el "dale" antes de crear nada por MCP. Bloque ilustrativo.

---

## Resumen operativo

1. Ficha del Cerebro Digital **validada** (OKF), creada/mantenida en `cerebro-digital/`.
2. La IA **propone el árbol** con el mapeo Vertical slice→Épica · Capacidad→Feature · Flujo→Historia · Técnico→Tarea — [[sincronizar-backlog]] (para un ticket suelto, [[redactar-tarea]]).
3. **Confirmación humana** del árbol y de los datos duros `⚠`.
4. **Alta/edición por MCP** de Azure con enlaces — [[sincronizar-backlog]] (lote) o [[cargar-a-azure]] (un item).
5. **IDs registrados**: `Documento fuente` en el ticket, `Tickets derivados` en la ficha, fila en `historial/` — todo **por referencia**.
6. **Re-sincronización** cuando la ficha cambia (actualiza los IDs sin duplicar) — [[sincronizar-backlog]].
