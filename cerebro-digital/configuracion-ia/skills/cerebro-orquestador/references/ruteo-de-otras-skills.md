# Ruteo de otras skills

Parte de la skill `cerebro-orquestador`: se lee cuando el índice de `SKILL.md` no alcanza para elegir la skill (frases típicas, casos borde, qué hace cada destino) o antes de cargar la elegida.

## Ruteo por el objeto del pedido — determinista

Todo lo de tickets (redactar, cargar, bajar una ficha o un lote, consultar, tomar, comentar, cerrar, auditar, estimar, y el desempate entre árbol e ítem) va a la puerta **`tickets`**, que tiene su ruteo. Acá, el resto:

- **Desarrollar Tareas en paralelo** → lo decide el ENTORNO, no la frase del pedido: con la variable `ORCA_APP_VERSION` definida (sesión de Orca) → **`desarrollar-asignadas`**; sin ella (IntelliJ u otra terminal) → **la misma `desarrollar-asignadas` en modo sin Orca** (`cerebro-digital/configuracion-ia/skills/desarrollar-asignadas/references/sin-orca.md`). La skill mira la variable en su paso 0 y elige el modo sola.
- **Un diagrama** (arquitectura, flujo, secuencia, ERD, estados, "dibujame cómo…") → **`archify`**, con salida en `borrador/diagramas/`; lo que entra al Cerebro es el Mermaid de `bin/radiografiar-codigo.py --mermaid`. Una presentación → **`cerebro-ppt-generator`**. Una pantalla: la línea de abajo.
- **Arrancar un proyecto** («arrancá un proyecto», «instanciá el template», «agarrá el proyecto X», «sumale el template a mi carpeta») → **`arrancar-proyecto`**: pregunta lo básico en un mensaje y corre `bin/arrancar-proyecto.py` con el «sí».
- **Una pantalla o un diseño UX/UI** («diseñá la pantalla de X», «pasá la ficha a Stitch», «exportá las pantallas») → **`disenar-con-stitch`** (Google Stitch por MCP, o modo manual). **Se carga sólo esa skill**: ella llama a `cerebro-mockup-design` (design system, revisión de la exportación) y a `cerebro-architect-ui` (bajada a especificación) en sus pasos 7 y 8, no se cargan las tres de entrada.
- **Probar de punta a punta** («diseñá las pruebas de la Historia X», «qué probamos a mano», «plan de pruebas») → **`disenar-pruebas`**; («automatizá la Historia X», «escribí las pruebas e2e», «qué cobertura de punta a punta tenemos») → **`automatizar-e2e`** (`bin/armar-e2e.py`, `bin/cobertura-e2e.py`; el motor lo fija `DEC-003` por tipo de aplicación).
- **Documentar la aplicación** («armá el manual», «la guía de uso», «la bitácora técnica», «el entregable de documentación») → **`documentar-aplicacion`**, que corre primero `bin/generar-documentacion.py`.
- **Una aplicación que ya existe** ("absorbé este repo", "sacá todo lo que hace", "documentá esta app") → **`absorber-aplicacion`**: inventario y radiografía por script, Cerebro ítem por ítem, matriz de cobertura. Termina ahí.
- **Qué hacer con esa aplicación** ("¿refactorizo o migro?", "planificá la migración", "armá el plan de modernización") → **`planificar-modernizacion`**: compara estrategias con lo medido, cura cada regla, escribe `DEC-004` con el «sí», ordena los slices.
- **Ponerle red a un módulo o slice** ("grabá cómo responde hoy", "armá el corpus de paridad", "test de caracterización") → **`caracterizar-comportamiento`** (`bin/armar-corpus.py`, `bin/paridad.py grabar`).
- **Ejecutar un slice** ("migrá el slice X", "seguí con la migración", "refactorizá el módulo X", "cortá el tráfico de X") → **`modernizar-slice`**: contrato, construcción por el pipeline normal, `bin/paridad.py comparar`, corte sólo con `bin/mapa-modernizacion.py corte` en OK.
- **Los hallazgos del Doctor** («atendé los hallazgos», «arreglá lo que marcó el Doctor») → **`atender-hallazgos`**.
- **Mejoras al propio ecosistema** ("¿qué mejorarías?", una señal repetida del Doctor o de los cierres) → **`mejorar-ecosistema`**: una propuesta por vez, registrada en `configuracion-ia/mejoras.md`, nunca aplicada sin el "sí".
- **Una pregunta sobre el dominio, una regla, una decisión, un pendiente o el avance** → **`cerebro-knowledge`** (qué se lee del Cerebro, en qué orden y cómo se cita). **Redactar o corregir un borrador funcional** para que se entienda → **`cognitive-doc-design`**. **Retomar o cerrar una sesión con Engram** → **`engram-memory-protocol`** (continuidad, nunca fuente de reglas: gana el Cerebro).
