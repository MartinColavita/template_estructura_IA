# Plantilla de las Tareas derivadas

Parte de la skill `sincronizar-backlog`: se lee cuando el GATE de NIVEL confirmó dev/planning y se redactan las Tareas de una Historia. Es la continuación del bullet de NIVEL de «Barreras».

**Cada Tarea usa la plantilla detallada** ([[plantillas/tarea]]) con **Contrato técnico (entrada/salida)** —que para capa `api` va como fragmento OpenAPI (YAML)—, validaciones, casos de error, **Especificación cerrada (SDD)** con la tabla que mapea los **Escenarios del Gherkin de la Historia** a los tests, la **lista de "Tests a escribir PRIMERO" (test-first)** numerada y el bloque **Modos de falla evaluados** (una línea por familia: cubierta por un test, o descartada con su motivo) (obligatorio si capa `api`/`application`/`domain`; DoR en [[redactar-tarea]] §3.1) — no Tareas de una línea.
