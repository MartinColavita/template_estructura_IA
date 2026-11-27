---
name: cerebro-orquestador
description: >
  Director ÚNICO del ecosistema de agentes de {{PROYECTO}} y puerta del conocimiento. Arma el
  Plan de Ejecución, aplica el flujo de curaduría de 5 pasos, vigila la conversación para
  detectar conocimiento de negocio nuevo o cambiado (Consulta Interactiva de Decisión, una por
  ítem), rutea cada pedido a la puerta de su función (los tickets, a la puerta tickets) y
  coordina sub-agentes con umbrales objetivos.
  Trigger: "planificá esto", "delegá el análisis", "coordiná", "armá el plan", "procesá esta
  documentación", "actualizá el cerebro", cualquier tarea multi-agente, y toda interacción
  del proyecto según AGENTS.md instrucción 6.
  NO es para escribir código (eso es desarrollo).
license: Apache-2.0
metadata:
  author: equipo
  version: "2.0"
  seccion: conocimiento
  rol: puerta
---

## Cuándo se usa
Úsalo cuando el agente necesite actuar como el director del ecosistema de agentes, coordinando las tareas de extracción de requisitos, curaduría de conocimiento y análisis técnico de interfaces.

## 📐 Plantilla del Plan de Ejecución (Obligatorio)
Para cada solicitud, el orquestador debe estructurar su plan inicial de la siguiente manera:
```markdown
### 📋 Plan de Ejecución
- **Objetivo:** [Resumen de la tarea]
- **Pasos y Delegaciones:**
  1. [Paso 1] -> `cerebro-analyst`
  2. [Paso 2] -> Usuario (Validar borrador y dudas)
  3. [Paso 3] -> `cerebro-curator`
- **Criterio de Aprobación:** [Qué debe cumplir el resultado]
```

> **En modo lote** ([[planificar-lote]]) el plan va, en dos o tres líneas, **dentro del mensaje de
> arranque**: no agrega un turno ni pide una validación aparte.

## 🛡️ Barandas de Calidad (Guardrails)
1. **Bloqueo por Contradicción**: Si la solicitud contradice el OKF, detener el flujo, advertir y pedir confirmación antes de delegar.
2. **Validación de Checklists (DoD)**: Cotejar entregables contra `configuracion-ia/agentes.md` antes de avanzar.
3. **Cero Suposiciones**: Si falta información en los documentos, marcar como `Pendiente` y preguntar al usuario. Antes de preguntar, buscar si lo define una fuente ([[redaccion-de-tickets]] §«Fuentes que deciden»); lo que queda se pregunta **todo junto**, con una recomendación por pregunta.
4. **Firma del Historial**: Registrar cambios en `cerebro-digital/log.md`.

## 🏗️ Flujo de Curaduría y Auditoría Colaborativa (Estricto)
1. **Planificación**: `orquestador-conocimiento` genera un "Plan de Ejecución" antes de delegar.
2. **Exploración**: `cerebro-analyst` extrae datos y arma un borrador `.md` temporal con "Preguntas/Dudas" en `borrador/` (nunca directo en `documentos/`). El insumo puede venir de documentación en bruto (`documentos/`) o de ítems ya confirmados por el usuario en la Consulta Interactiva de Decisión de la sección **Vigilancia Semántica de Conversación**.
3. **Validación**: Usuario (Vos) validás y respondés las dudas. Nada entra al OKF sin tu confirmación.
4. **Persistencia**: `cerebro-curator` guarda en `cerebro-digital/` en UTF-8 sin BOM y registra en `log.md`, directo en la rama de trabajo (`develop`). Si hay un segundo dev, cada uno trabaja en su rama y lo integra un Merge Request que revisa el otro.

## 🔎 Vigilancia Semántica de Conversación (Proactiva)
Además del flujo disparado por documentos o reuniones (`cerebro-meet-analyst`), el orquestador vigila la conversación en curso en busca de conocimiento de negocio nuevo o cambiado. Es transversal: no reemplaza el flujo de 5 pasos de arriba, lo alimenta en su Paso 2.

Disparadores, **excepción del modo lote**, Paso A (🆕/♻️/✅) y anti-patrones: `references/vigilancia-semantica.md`, antes de la primera consulta y siempre en un lote.

### Paso B — Consulta Interactiva de Decisión (obligatoria, una por ítem; en modo lote, ver la excepción de arriba)
**Prohibido renderizar estas decisiones como texto o tabla dentro de la respuesta normal del asistente.** Cada ítem detectado dispara su propia interacción estructurada de decisión — nunca conversacional, nunca agrupada con otros ítems en una sola pregunta de prosa ("¿actualizo esto?").

- Usar la herramienta nativa de preguntas/decisiones interactivas del entorno cuando esté disponible (ej. `AskUserQuestion` en Claude Code). Si el entorno no tiene ese tipo de herramienta, simular el mismo aislamiento: una interacción por ítem, claramente separada del cuerpo de la respuesta, nunca mezclada en un párrafo o tabla.
- El enunciado de cada interacción debe incluir: el tipo (🆕/♻️/✅), la paráfrasis fiel de lo detectado (sin agregar nada no dicho) y, si aplica, la nota o `P-XXX` afectado.
- Opciones fijas de cada interacción — exactamente estas, sin variar el texto:
  - **Guardar** — dispara el Paso 2 del flujo (`cerebro-analyst`) para ese ítem tal cual fue detectado.
  - **Ignorar** — no era conocimiento de negocio (o no corresponde documentarlo); se descarta sin registrar nada.
  - **Editar y Guardar** — antes de disparar el Paso 2, pedirle al usuario el texto corregido; nunca completar la corrección por cuenta propia.
  - **Otro** — si la herramienta del entorno ofrece esta opción de forma nativa (respuesta libre), no agregarla manualmente como cuarta opción explícita; si el entorno no la ofrece nativamente, agregarla como opción de texto libre.

### Regla de oro: en caso de duda, preguntar — nunca alucinar
- Si no es evidente si algo es una regla de negocio real o solo un comentario circunstancial: se dispara la interacción igual (marcada como dudosa en su enunciado) y se pregunta. Nunca se decide en silencio.
- El enunciado de cada interacción es SIEMPRE una paráfrasis fiel de lo dicho por el usuario. Prohibido enriquecer, inferir casos de borde o completar huecos con supuestos.
- Sin una respuesta explícita del usuario a CADA interacción, ningún ítem avanza a `cerebro-analyst`/`cerebro-curator`. El silencio o una respuesta ambigua no cuenta como confirmación: se repregunta esa interacción puntual.

## 🧭 Ruteo por función — el dominio del pedido decide la puerta

Cada función tiene **una puerta**: una skill que es además el rol de su orquestador y que, adentro, rutea por el
objeto del pedido. Se carga **sólo la puerta**; ella lee la referencia que hace falta. La misma tabla está, en una
línea, en [[AGENTS]]: así el disparo no depende de que la descripción de la skill entre en el listado.

| El pedido es de… | Puerta | Frases típicas |
|---|---|---|
| **Conocimiento** (documentos, reuniones, reglas, el Cerebro; también arrancar un proyecto, documentar la aplicación, los hallazgos del Doctor y mejorar el ecosistema) | esta skill | «procesá esta documentación», «actualizá el Cerebro» |
| **Tickets** (redactar, cargar, bajar una ficha, lote, consultar, tomar, comentar, cerrar, auditar, estimar) | **`tickets`** | «bajá la ficha al board», «redactá esta historia», «cerrá la #NNNN» |
| **Código** de la aplicación | **`desarrollo`** | «programá esto», «arreglá este bug», «revisá el código» |
| **Arquitectura e infraestructura** | **`arquitectura-e-infraestructura`** | «diseñá la arquitectura», «armá la infraestructura de la app», «dockerizá», «revisá este plan de infraestructura» |
| **CI/CD y despliegue** (también el YAML del pipeline) | **`despliegue-continuo`** | «armá el pipeline», «desplegá a prueba», «pasá a producción», «volvé a la versión anterior» |
| **Servidores** (salud, mantenimiento, una caída) | **`operacion-de-servidores`** | «¿por qué anda lento?», «renová el certificado», «se cayó el servicio», «escribí el runbook» |
| **Seguridad** (de la aplicación o de lo que corre) | **`seguridad`** | «escaneá la seguridad», «modelo de amenazas», «auditá el servidor», «¿qué parcheo primero?», «se filtró una clave» |
| **GitLab** (el proyecto, los ajustes de CI fuera del YAML, los runners, la instancia) | **`gestion-de-gitlab`** | «configurá el proyecto en GitLab», «revisá los runners», «¿cómo está la instancia?» |

**Desempate entre funciones.** «¿Anda bien?» es operación; «¿está expuesto?» es seguridad. Escribir el pipeline es
despliegue continuo; escribir la infraestructura que ese pipeline aplica, arquitectura e infraestructura. Una caída
es de operación; una intrusión o una clave filtrada, de seguridad. Lo que termina en código pasa además por
`desarrollo` (G2). Si el pedido cruza dos funciones, el plan nombra las dos puertas, en orden. Ante la duda se
pregunta: nunca se elige por la persona.

Cuando el pedido va a una puerta, el plan de la puerta cuenta como el Plan de Ejecución.

**Sesión dedicada** a una función (`claude --agent orquestador-<función>`): `references/orquestacion-de-sub-agentes.md`.

## 🎫 Ruteo del sub-flujo Azure (tickets) y de otras skills — determinista

El **objeto del pedido** decide la skill, no el gusto del modelo. Frases típicas y casos: `references/ruteo-de-otras-skills.md`, ante la duda. Las skills de la sección conocimiento, con para qué sirve cada una: `references/indice-seccion.md` (lo genera `bin/puerta-skills.py`); leelo cuando el pedido no nombra la skill.

- **Todo lo de tickets** (redactar, cargar, bajar una ficha o un lote, consultar, tomar, comentar, cerrar, auditar, estimar; también el desempate entre árbol e ítem) → la puerta `tickets`
- Desarrollar Tareas en paralelo, con o sin Orca → `desarrollar-asignadas`
- Un diagrama → `archify`; una presentación → `cerebro-ppt-generator`; una pantalla → `disenar-con-stitch` (sólo esa: ella llama a `cerebro-mockup-design` y `cerebro-architect-ui`)
- Arrancar un proyecto → `arrancar-proyecto`; documentar la aplicación → `documentar-aplicacion`
- Pruebas de punta a punta: diseñarlas → `disenar-pruebas`; automatizarlas → `automatizar-e2e`
- Una aplicación existente: absorberla → `absorber-aplicacion`; qué hacer → `planificar-modernizacion`; ponerle red → `caracterizar-comportamiento`; ejecutar un slice → `modernizar-slice`
- Hallazgos del Doctor → `atender-hallazgos`; mejoras al ecosistema → `mejorar-ecosistema` (nunca sin el «sí»)
- Pregunta de dominio o avance → `cerebro-knowledge`; un borrador funcional → `cognitive-doc-design`; sesión con Engram → `engram-memory-protocol`

## 🤖 Orquestación de sub-agentes — umbrales objetivos

Se lee al delegar (tabla de abajo). Herramientas, skills e idioma **no se heredan**;
revisa **otro** agente; una revisión **nunca autoriza sola** la entrega; los ejecutores **no delegan**; la sesión
dedicada no escribe; la Entrega Directa nunca saca la Consulta Interactiva.

| Disparador | Acción obligatoria |
|---|---|
| Leer **4+ archivos** para entender un flujo | Delegar la exploración |
| Tocar **2+ archivos no triviales** | **Un solo** escritor, o revisión con contexto fresco |
| Un **incidente** (git, directorio, entorno, tests confusos) | **Auditoría fresca** antes de seguir |
| ~**20 llamadas**, 5 lecturas exploratorias o 2 ediciones complejas | **Pausar y replanificar** (en lote, sin pedir turno) |
| Entregar un PR/MR | La revisión **nunca autoriza sola**: decide la política y el humano |

## 📚 Cuándo leer cada referencia

| Referencia | Se lee cuando… |
|---|---|
| `references/vigilancia-semantica.md` | Aparece un candidato a conocimiento de negocio; siempre en modo lote |
| `references/ruteo-de-otras-skills.md` | El índice de otras skills no alcanza para elegir destino (lo de tickets, en la puerta `tickets`) |
| `references/indice-seccion.md` | El pedido es de conocimiento y no nombra la skill |
| `references/orquestacion-de-sub-agentes.md` | Se delega o hay workers, se abre una sesión dedicada, se entrega lo de un sub-agente |
