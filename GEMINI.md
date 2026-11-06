# GEMINI.md — reglas del repo (Gemini CLI)

Gemini CLI lee `GEMINI.md` por defecto, y `AGENTS.md` sólo si cada persona lo agrega a `context.fileName` en su `settings.json`; por eso se importa desde acá, con el **mismo patrón** que usa `CLAUDE.md`. Sin este archivo, la herramienta trabaja sin las reglas del proyecto y tiende a **duplicar el conocimiento** en vez de apuntar a la fuente única.

El `AGENTS.md` de la raíz ya incluye el **núcleo** + las **reglas de redacción/carga de tickets Azure**, así que con este único import quedan cargadas todas las **reglas**.

@AGENTS.md

## Skills

Las skills viven en `cerebro-digital/configuracion-ia/skills/` (**fuente canónica**) y se reflejan en dos espejos versionados: `.agents/skills/` y `.claude/skills/`. Un hook pre-commit (`.githooks/`) verifica que los espejos queden idénticos a la fuente.

`.agents/skills/` es el alias documentado de `.gemini/skills/`: Gemini CLI lo descubre solo, y `gemini skills list` (o `/skills` en la sesión) muestra lo que cargó. Si el entorno **no auto-descubre** ninguno de los dos espejos, las skills se usan **leyendo el `SKILL.md`** que corresponda y siguiendo sus instrucciones — el contenido es el mismo y no depende de la herramienta. El índice de skills está en `AGENTS.md`.

## Regla de neutralidad

Todo lo que se escriba en reglas y skills debe funcionar igual en **Claude Code, opencode, Antigravity y Gemini**: referirse a "la herramienta nativa de lectura/escritura del entorno", nunca al nombre de una herramienta puntual. Si una skill necesita un acceso que este entorno no tiene (por ejemplo, leer el tablero de Azure), debe **decir que no pudo verificarlo** — nunca darlo por cumplido ni reconstruir el dato de memoria.
