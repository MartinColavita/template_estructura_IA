# Referencias externas — orquestadores por función, repositorios de skills y Obsidian

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca. Dice de
dónde salió cada idea de los orquestadores por función, del chequeo de ruteo y de la configuración de Obsidian.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| Documentación de Claude Code: subagentes, skills, hooks, referencia de la línea de comandos y ajustes | https://code.claude.com/docs/en/sub-agents · `/skills` · `/hooks` · `/cli-reference` · `/settings` · `/headless` · `/agent-teams` | Documentación oficial | 2026-11-14 | Que un subagente nunca puede preguntarle a la persona, y por eso **el orquestador es la sesión principal** (`claude --agent`) con un primer turno automático que carga su rol; que el listado de skills tiene un cupo del 1 % del contexto y, al desbordarse, **saca las descripciones de las menos usadas** y deja el nombre | `cerebro-digital/configuracion-ia/agentes/orquestador-*.md`; el chequeo de ruteo escrito de `bin/verificar-skills.py`; `INSTALACION.md` §«Un orquestador por función» |
| BMAD-METHOD | https://github.com/bmad-code-org/BMAD-METHOD | MIT | 2026-11-14 | «El agente es una skill que carga un rol en la sesión», y el modo de reserva cuando no hay subagentes | Cada puerta es el rol de su orquestador; la sección «Cómo se trabaja» de cada puerta trae el modo sin subagentes |
| wshobson/agents | https://github.com/wshobson/agents | MIT | 2026-11-14 | Un orquestador **por flujo de dominio** que corre en la sesión principal, con puntos de control donde pregunta | El ruteo por función de `cerebro-orquestador` y la tabla «el objeto del pedido decide» de cada puerta |
| akin-ozer/cc-devops-skills | https://github.com/akin-ozer/cc-devops-skills | Apache-2.0 | 2026-11-14 | Los pares generador y validador: es «quien produce no aprueba» | Los workers `nucleo-productor` y `nucleo-verificador` |
| obra/superpowers | https://github.com/obra/superpowers | MIT | 2026-11-14 | Un implementador nuevo por tarea, con su revisión | Confirma el criterio que ya tenía `orquestador-desarrollo`; no cambió nada |
| Ayuda oficial de Obsidian | https://obsidian.md/help/manage-vaults · `/data-storage` · `/settings` · `/plugins/graph` · `/plugins/search` · `/links` | Documentación oficial | 2026-11-14 | Abrir una carpeta existente como bóveda; qué guarda `.obsidian/`; archivos excluidos (ocultan, no evitan indexar); grupos de color del grafo con la sintaxis de búsqueda | `.obsidian/app.json`, `.obsidian/graph.json`, `.gitignore` e `INSTALACION.md` §«Ver el Cerebro en Obsidian» |
| Bóveda pública de referencia | https://github.com/kepano/kepano-obsidian | No relevada | 2026-11-14 | Qué archivos de `.obsidian/` conviene versionar y cuáles son de cada máquina | La lista de `.gitignore` (se versionan sólo `app.json` y `graph.json`) |

## Lo que se miró y no se tomó

- **Instalar una colección de skills o de subagentes de terceros** (`VoltAgent/awesome-claude-code-subagents`,
  `davila7/claude-code-templates`, `Jeffallan/claude-skills`, `vijaythecoder/awesome-claude-agents`, todas MIT):
  catálogos desparejos, y en los registros públicos hay skills maliciosas. Sirven para leer ideas de prompts de
  rol. Varios de sus «orquestadores» no pueden delegar: no tienen la herramienta de subagentes.
- **`trailofbits/skills`** (CC-BY-SA-4.0): calidad alta, pero la licencia obliga a redistribuir lo derivado con la
  misma licencia. Se estudia; no se copia. **`hashicorp/agent-skills`** (MPL-2.0): copyleft por archivo.
- **`ruvnet/claude-flow`** (MIT): instala un arnés externo completo, y eso choca con el guardarraíl G5.
- **`anthropics/skills`** (cada skill con su licencia; las revisadas, Apache-2.0): es la referencia de formato, y no
  cubre estos dominios. **`anthropics/claude-plugins-official`** (Apache-2.0) y
  **`anthropics/claude-code-security-review`** (MIT): complementos por máquina; no son parte del método.
- **Los equipos de agentes de Claude Code**: experimentales y apagados por defecto. No sirven de base.
- **Listas blancas de herramientas en los orquestadores**: le quitarían los servidores MCP a un rol que los
  necesita. Se usa una lista negra corta (no escriben archivos).
- **Dataview** (MIT, plugin de la comunidad de Obsidian): no indexa encabezados y su rama principal no tiene
  cambios desde el 2025-04-08. Para tablas conviene Bases, que es oficial, o un script de `bin/`.
- **Un MCP para que la IA lea o escriba la bóveda** (`coddingtonbear/obsidian-local-rest-api`, MIT;
  `MarkusPfundstein/mcp-obsidian`, MIT; `cyanheads/obsidian-mcp-server`, Apache-2.0): sería un segundo camino de
  escritura que saltea a `cerebro-curator`, con más superficie de ataque. La bóveda es el repositorio y la IA ya lo lee.
- **Cambiar los enlaces del Cerebro para Obsidian** (alias en los `SKILL.md`, rutas completas en los enlaces con
  ruta parcial, ids de bloque en las decisiones): no se tocó nada sin haberlo probado en una instalación real.

## Lo que la investigación no pudo verificar

- Que una sesión abierta con `claude --agent` tenga la herramienta nativa de preguntas. Por eso cada puerta dice
  qué hacer si no está: preguntar en el texto y esperar.
- El formato de `graph.json` y de la lista de carpetas ocultas de `app.json`: sale de fuentes de terceros que
  coinciden entre sí, no de la ayuda oficial.
- Si Obsidian resuelve un enlace con ruta parcial (`[[checklists/mapa-campos-azure]]`) y a dónde salta un ancla
  que no coincide con el encabezado (`[[decisiones#DEC-002]]`). La receta para probarlo: abrir la raíz del
  repositorio como bóveda y correr `obsidian unresolved verbose format=json` con la aplicación abierta.
- Nada de lo de Obsidian se probó en una instalación real: no había Obsidian en la máquina donde se armó.
