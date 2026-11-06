---
id: index
tipo: indice
estado: F-Verified
modulo: general
title: Cerebro Digital de {{PROYECTO}}
description: Cerebro digital del proyecto {{PROYECTO}} para {{ORGANIZACION}}. Organizado por módulos de negocio (OKF).
tags: [okf, indice]
last_updated: 2026-10-22
author: "equipo"
---

# {{PROYECTO}} — Cerebro Digital

## 📖 ¿De qué trata el proyecto? (Resumen de negocio)

<completar: dos o tres oraciones en criollo. Qué hace el producto {{PRODUCTO}}, para quién y qué
problema resuelve. El detalle va en [[contexto]].>

---

## 🗂️ Catálogo de `tipo` y `estado` (frontmatter)

Vocabulario cerrado para el frontmatter de todo archivo del OKF (`cerebro-digital/`, sin `configuracion-ia/`). No usar valores fuera de esta lista — si hace falta un `tipo` nuevo, se agrega acá primero.

**`estado:`** — 2 valores:
- `F-Draft`: contenido en revisión, sujeto a cambios.
- `F-Verified`: validado por el equipo funcional/técnico (o gate de proceso explícito, como una prueba puntual — dejarlo aclarado en el propio documento si aplica).

**`tipo:`** — 16 valores en uso:
`guia`, `contexto`, `diseno`, `fuentes`, `indice`, `log`, `concepto`, `reporte`, `roadmap`, `decisiones`, `extraccion-reunion`, `funcional`, `flujo`, `reglas-de-negocio`, `pendientes`, `aplicacion`.
El toolkit `tablero/` (que no es parte del Cerebro) usa además `plantilla`, `checklist` y `referencia`.

**`modulo:`** — `general`, `diseno`, o el slug de un módulo (`modulo-ejemplo`; se agregan acá al crear uno nuevo).

## 🧷 Footer de trazabilidad por regla

Toda regla de negocio (`RN-...`) o decisión (`DEC-...`) que se agregue o modifique cierra con una línea:

```
_Últ. modif.: YYYY-MM-DD — @autor — motivo en 5-8 palabras_
```

Va inmediatamente después del contenido de esa regla/decisión puntual (no al final del archivo). Permite leer "qué cambió y por qué" regla por regla sin inferirlo del diff completo. **No se backfillea retroactivamente** sobre reglas cuyo motivo de última modificación no se conoce con certeza (evita inventar historia).

## 🔢 Códigos

- **Reglas de negocio:** `RN-<MODULO>-nnn` (prefijo de 3-4 letras del módulo, p. ej. `RN-MOD-001`); nunca `RN-nnn` suelto, para que dos módulos no colisionen en el mismo número.
- **Decisiones:** `DEC-nnn`, consecutivas en `arquitectura/decisiones.md` del módulo.
- **Pendientes:** `P-nnn`, consecutivas en `pendientes.md` del módulo. Una ficha nunca repite el enunciado de una pregunta abierta: linkea `[[pendientes#P-nnn]]`.
- **Fuentes:** `[DOC-nn]`, consecutivas en [[fuentes]].
- **Aprendizajes de la aplicación:** `AP-nnn`, consecutivos en `aplicacion/aprendizajes.md` del módulo; cada uno con su fuente y con lo que cambió.
- **Deuda técnica:** `DT-nnn`, consecutivos en `aplicacion/deuda.md` del módulo; cada una con cuándo se paga.

## 🧠 Estructura del Cerebro Digital (OKF)

El conocimiento validado se organiza por módulos funcionales dentro de `cerebro-digital/`:

### Configuración general
- **`contexto.md`**: origen del proyecto, organización, producto, alcance y equipo.
- **`roadmap.md`**: tablero de control de avance de la documentación y del desarrollo.
- **`fuentes.md`**: registro oficial de fuentes de información y trazabilidad de origen.
- **`log.md`**: historial de cambios global del Cerebro.
- **`configuracion-ia/agentes.md`**: roles de los agentes de IA y sus checklists de entrega.
- **`configuracion-ia/orquestador-desarrollo.md`**: diseño del orquestador de código.
- **`configuracion-ia/mejoras.md`**: registro de propuestas de mejora del ecosistema (autocorrección consultada).
- **`configuracion-ia/integracion-azure-mcp/`**, **`integracion-gitlab-mcp/`** e **`integracion-stitch-mcp/`**: setup de los MCP (tablero, repositorios, diseño UX/UI).

### 📦 Módulo: `modulo-ejemplo` (renombrar al instanciar)
-   **`modulo-ejemplo/funcional/`**: el **qué**: reglas de negocio, glosario, flujos y pantallas. Una ficha por flujo, con su bloque `## Derivación a backlog`.
-   **`modulo-ejemplo/metodologia/`**: el **cómo trabaja el equipo**: ramas, commits, Merge Requests, DoR/DoD.
-   **`modulo-ejemplo/arquitectura/`**: el **cómo se construye**: `decisiones.md` (DEC-nnn) y `esqueleto-proyectos.md` (estructura de los repos, convenciones de código, derivación a backlog).
-   **`modulo-ejemplo/aplicacion/`**: la **memoria viva de la aplicación construida**: `mapa.md` (qué existe hoy, módulo por módulo, con sus Historias y su estado), `aprendizajes.md` (`AP-nnn`: bugs y sus causas, trampas del stack, patrones, decisiones revertidas) y `deuda.md` (`DT-nnn`). Lo alimentan el cierre de cada Tarea, la absorción y los hallazgos aceptados del Doctor; nace vacío.
-   **`modulo-ejemplo/extraccion-reuniones/`**: insumo crudo de reuniones, sin consolidar (se promueve a los pilares cuando corresponde).
-   **`modulo-ejemplo/pendientes.md`**: preguntas abiertas del módulo, transversal a los pilares (la deuda técnica no va acá: va a `aplicacion/deuda.md`).

Un segundo módulo se crea copiando esta misma estructura con otro slug y agregándolo acá y en el catálogo de `modulo:`.

### 🎨 Sistema de diseño visual
-   **`diseno/diseno-sistema.md`**: tokens y componentes visuales del producto (documento descriptivo; la skill `cerebro-mockup-design` es la prescriptiva).

---

### 🛠️ Skills de automatización

**Cerebro Digital (9):**
-   `configuracion-ia/skills/cerebro-knowledge/`: instrucciones para que las IA consulten este OKF.
-   `configuracion-ia/skills/cerebro-orquestador/`: coordinación del ecosistema, plan de ejecución, vigilancia semántica y ruteo de tickets.
-   `configuracion-ia/skills/cerebro-architect-ui/`: mapeo UI ↔ reglas del arquitecto.
-   `configuracion-ia/skills/cerebro-ppt-generator/`: presentaciones interactivas en HTML.
-   `configuracion-ia/skills/cerebro-mockup-design/`: design system y tokens para mockups HTML.
-   `configuracion-ia/skills/cerebro-meet-analyst/`: análisis de transcripciones de reuniones y extracción al OKF.
-   `configuracion-ia/skills/cognitive-doc-design/`: patrones de documentación cognitiva.
-   `configuracion-ia/skills/engram-memory-protocol/`: protocolo de persistencia estructurada en Engram.

**Pipeline Azure DevOps (14):**
-   `configuracion-ia/skills/redactar-tarea/`: redacta un ticket suelto (Historia/Tarea/Bug/Habilitador); no toca el board.
-   `configuracion-ia/skills/estimar-story-points/`: calcula los Puntos de historia; no toca el board.
-   `configuracion-ia/skills/consultar-backlog/`: consulta y audita el board (cobertura, desfase); sólo lectura. Es el motor de deduplicación.
-   `configuracion-ia/skills/analizar-tareas/`: consistencia del set de Tareas antes de crearlas; opcional, a pedido.
-   `configuracion-ia/skills/auditar-historia/`: segundo chequeo independiente de una Historia; opcional, a pedido.
-   `configuracion-ia/skills/auditar-tarea/`: segundo chequeo independiente de la lista de tests de una Tarea; opcional, a pedido.
-   `configuracion-ia/skills/sincronizar-backlog/`: deriva una ficha entera al árbol Épica→Feature→Historia; escribe con confirmación.
-   `configuracion-ia/skills/planificar-lote/`: modo lote con agentes en paralelo y dos turnos humanos; escribe con el "sí" del cierre.
-   `configuracion-ia/skills/cargar-a-azure/`: crea o actualiza un work item; escribe con confirmación.
-   `configuracion-ia/skills/tomar-tarea/`: asigna la tarjeta y la pasa a Active; escribe con confirmación.
-   `configuracion-ia/skills/comentar-tarea/`: comenta la tarjeta; escribe con confirmación.
-   `configuracion-ia/skills/desarrollar-asignadas/`: desarrolla en paralelo las Tareas asignadas, con Orca o sin Orca (`references/sin-orca.md`), sobre Azure o el tablero local; escribe con confirmación o según `DEC-005`.
-   `configuracion-ia/skills/atender-hallazgos/`: recorre los hallazgos del Doctor uno por uno, con decisión humana en cada uno.

**Desarrollo, QA y evolución (10):**
-   `configuracion-ia/skills/desarrollo/`: punto de entrada único al código: el método completo (TDD con evidencia, endpoints, contrato, revisión, entrega) y los guardarraíles. Lo específico del stack se completa en `references/metodo/tdd-stack-back.md` y `tdd-stack-front.md`.
-   `configuracion-ia/skills/absorber-aplicacion/`: absorbe una aplicación existente al Cerebro (inventario por script, lectura ítem por ítem) y decide con el humano refactor o migración (`DEC-004`).
-   `configuracion-ia/skills/planificar-modernizacion/`: con el Cerebro poblado, compara estrategias con lo medido, cura cada regla y escribe `DEC-004` con el «sí»; arma las fichas por slice.
-   `configuracion-ia/skills/caracterizar-comportamiento/`: la red antes de tocar: corpus y golden contra la aplicación vieja (`bin/armar-corpus.py`, `bin/paridad.py`), tests de caracterización.
-   `configuracion-ia/skills/modernizar-slice/`: ejecuta un slice: contrato, construcción, paridad, corte con barrera (`bin/mapa-modernizacion.py corte`), apagado.
-   `configuracion-ia/skills/mejorar-ecosistema/`: autocorrección consultada: propone mejoras al ecosistema de a una, registradas en `configuracion-ia/mejoras.md`; nunca las aplica sola.
-   `configuracion-ia/skills/arrancar-proyecto/`: la puerta de entrada: pregunta lo básico del proyecto en un mensaje y, con el «sí», lo arranca por script (`bin/arrancar-proyecto.py`).
-   `configuracion-ia/skills/disenar-con-stitch/`: diseño de pantallas en Google Stitch (MCP o manual) desde la ficha; la exportación es la maqueta vigente (`fuente_maqueta`) y baja al front por `cerebro-architect-ui`.
-   `configuracion-ia/skills/disenar-pruebas/`: el tester: plan de pruebas de aceptación desde el Gherkin de una Historia, sin depender de la herramienta.
-   `configuracion-ia/skills/automatizar-e2e/`: QA automatización: pruebas de punta a punta con el motor del tipo de aplicación (`DEC-003`); esqueleto por `bin/armar-e2e.py`, cobertura por `bin/cobertura-e2e.py`.
-   `configuracion-ia/skills/documentar-aplicacion/`: la guía de uso y la documentación técnica y funcional de la aplicación, generadas desde el Cerebro (`bin/generar-documentacion.py`) al cerrar un slice o la app.
-   `configuracion-ia/skills/archify/`: skill externa vendorizada (Apache-2.0, Node, versión 3.2): diagramas interactivos HTML de arquitectura, flujos, secuencias, ERD y estados; entregable de `borrador/`, el Cerebro guarda Mermaid.
