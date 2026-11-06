# CLAUDE.md — reglas del repo (Claude Code)

Claude Code lee `AGENTS.md` por sí solo únicamente cuando no existe ningún `CLAUDE.md` (desde la v2.1.277); como este archivo existe, lo importa explícitamente, y así funciona igual en toda versión y aunque alguien tenga un `CLAUDE.local.md`. El `AGENTS.md` de la raíz ya incluye el **núcleo** + las **reglas de redacción/carga de tickets Azure**, así que con este único import quedan cargadas todas las **reglas**. Las **skills** SÍ se auto-descubren de forma **nativa y project-scoped** desde `.claude/skills/` (espejo versionado de la fuente canónica) — invocables con `/nombre-de-la-skill` en cualquier clone, sin configuración adicional.

Detalle de instalación, qué es canónico vs. espejo, y cómo actualizar los espejos de skills: ver [`INSTALACION.md`](INSTALACION.md) en la raíz.

@AGENTS.md
