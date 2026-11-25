# Qué lleva cada tipo de ticket

Parte de la skill `redactar-tarea`: se lee antes de redactar, una vez decidido el tipo (§3 de la skill).

- **Historia (los 4 bloques, ver [[plantillas/historia-de-usuario]]):** (1)
  **Funcionalidad** "Como `<rol>` quiero `<qué>` para `<para qué>`" + contexto +
  alcance; (2) **Criterios de aceptación** en Gherkin español (Dado/Cuando/Entonces);
  (3) **Reglas de negocio** con **referencia al OKF** (ruta#ancla) por cada `[RN-…]`;
  (4) **Casos de uso** (alcance de pruebas, mapeados a `[RN-…]`). Siempre la línea
  **Documento fuente**. Y las **Notas para QA** con sus cinco líneas fijas (pantalla y ruta, rol y usuario de
  prueba, datos iniciales con marcadores, identificadores estables que expone el front, ambiente): es lo que la
  prueba de punta a punta necesita y el Gherkin no dice; lo que no se sabe va `⚠`, no se inventa. Debe servir a
  Desarrollo y a Testing sin que nadie tenga que volver a preguntar.
- **Bug:** el cuerpo lleve SIEMPRE los tres bloques:
  1. **Resultado esperado** — qué debería pasar.
  2. **Resultado obtenido** — qué pasa hoy.
  3. **Por qué / contexto** — pasos para reproducir, ambiente, alcance.
  Más severidad/gravedad si el board la usa.
- **Tarea / Habilitador (el detalle que necesita el dev, según la complejidad):**
  siempre el **objetivo**, el **alcance**, la **Definición de terminado** y el
  **Parent**. **Solo para desarrollo pesado** sumá el **vertical slice** + **capa**
  (`api`/`application`/`domain`/`infra`, o front), el **Contrato técnico (entrada/salida)**
  —que para capa `api` se escribe como **fragmento OpenAPI (YAML), no en prosa**—, la
  **especificación cerrada (SDD)** con sus `[RN-…]`, la **lista de "Tests a escribir
  PRIMERO" (TDD test-first)** y si **requiere test de integración**. Para una tarea
  chica **no infles** con secciones que no aplican (ver [[plantillas/tarea]]).
