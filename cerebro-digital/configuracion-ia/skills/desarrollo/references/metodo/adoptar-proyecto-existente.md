# Adoptar un proyecto que ya trabaja con IA (Claude Code, Gemini, Cursor…)

> Método propio. Es el caso «ya tengo un proyecto andando, con su `CLAUDE.md`, sus skills y su
> memoria, y quiero que salga de este template sin tirar nada ni quemar tokens». Complementa
> [ingenieria-inversa.md](ingenieria-inversa.md) (leer el código) y
> [refactor-y-migracion.md](refactor-y-migracion.md) (cambiarlo). Acá va sólo lo que es distinto
> cuando el proyecto **ya tiene configuración de IA**.

## La idea en una línea

**El repositorio del proyecto no se muda: se enchufa.** Se clona adentro de `back/` o `front/` del
núcleo (o queda al lado, si ya vive en otra carpeta), conserva sus reglas locales de build y test, y
el Cerebro pasa a ser la fuente de verdad de lo durable: decisiones, convenciones, aprendizajes,
deuda. Lo que el `CLAUDE.md` del proyecto decía «para que la IA se acuerde» se lee **una sola vez**,
se vuelca al lugar que corresponde del Cerebro, y el `CLAUDE.md` queda corto.

## Los pasos (y lo que cuesta cada uno en tokens)

Los pasos 1 a 3 los hace **un solo comando**, `bin/arrancar-proyecto.py --existente <carpeta>` (o
`bin/adoptar-proyecto.py <carpeta>` sobre un núcleo ya instanciado): enlaza, releva, inventaría y deja los
informes en `borrador/adopcion/`. La tabla explica qué hace cada paso, no pide hacerlos a mano.

| # | Paso | Herramienta | Tokens |
|---|---|---|---|
| 1 | **Clonar o enchufar** el repo adentro de `back/`, `front/` o al lado. No se toca nada suyo | `git clone` | 0 |
| 2 | **Relevar la configuración de IA**: qué instrucciones tiene, qué comandos de build y test declara, qué reglas duras, si pide inglés, qué skills, comandos, agentes y servidores MCP trae, y qué colisiona con el núcleo | `bin/relevar-config-ia.py <repo> --nucleo <núcleo>` | 0 |
| 3 | **Inventario y radiografía** del código | `bin/inventariar-codigo.py` · `bin/radiografiar-codigo.py` | 0 |
| 4 | **Decidir qué gana** (tabla de abajo), en un turno, con una persona | la skill `absorber-aplicacion` (Fase 0) | pocos: se lee lo que el relevamiento señaló, no todo |
| 5 | **Volcar lo durable al Cerebro** ítem por ítem, con el «sí» | `cerebro-curator` por la Consulta Interactiva | los del borrador |
| 6 | **Enlazar las reglas** para que cualquier sesión las vea (abajo) | una línea en el `CLAUDE.md` del repo | 0 |
| 7 | Si se quiere refactorizar o migrar: `DEC-004` y el pipeline normal | `absorber-aplicacion` Fases 3 y 4 | los de siempre |

Si el relevamiento devuelve `SIN DATOS`, el proyecto no tiene configuración de IA: es una
aplicación común y se absorbe con [ingenieria-inversa.md](ingenieria-inversa.md) sin este paso.

## Qué va adónde (lo que el relevamiento encuentra)

| Lo que trae el proyecto | Adónde va | Qué queda en el repo |
|---|---|---|
| Comandos de build, test y lint del `CLAUDE.md` | `tdd-stack-back.md` / `tdd-stack-front.md` de la skill `desarrollo` (el verificador los necesita) | El `README.md` del repo, que ya los tenía o los recibe |
| Reglas duras («siempre», «nunca», «no uses») | `arquitectura/esqueleto-proyectos.md` §Convenciones (la fila **C8**) o `decisiones.md` como `DEC-nnn` | Nada: se leen del Cerebro |
| Decisiones de arquitectura ya tomadas (estructura, librerías, patrones) | `decisiones.md` como `DEC-nnn` **heredada**, con fecha y «de dónde sale» | Nada |
| Trampas y lecciones («ojo con…», «no funciona si…») | `aplicacion/aprendizajes.md` como `AP-nnn`, con su fuente | Nada |
| Lo que el proyecto sabe que debe (TODO, «deuda», «provisorio») | `aplicacion/deuda.md` como `DT-nnn` | Nada |
| Skills propias (`.claude/skills`, `.agents/skills`) | Se quedan en el repo como skills **scoped**: Claude Code las carga al tocar un archivo de ahí | Todas, salvo colisión de nombre con el núcleo: la del repo se **renombra** (dos skills con el mismo nombre y distinto contenido dejan de ser deterministas) |
| Comandos y agentes de Claude (`.claude/commands`, `.claude/agents`) | Se quedan; los que dupliquen una skill del núcleo se retiran | Los que no duplican |
| Servidores MCP (`.mcp.json`) | Por máquina, documentados en `integracion-*/` del Cerebro; nunca con tokens adentro | El `.mcp.json` sin secretos, o nada |
| La memoria del asistente (auto memory, notas) | **No se migra.** El Cerebro es la memoria compartida; lo durable ya fue a aprendizajes o decisiones | Nada |
| Una regla que **choca** con el template (p. ej. «escribí en inglés» contra «todo en español») | Se decide en el encuadre: o el proyecto adopta la regla del núcleo, o se escribe la excepción como `DEC-nnn` y se cita en C3 | Lo que la DEC diga |

**Regla de precedencia:** si el repo contradice al Cerebro, manda el Cerebro (C6), **pero primero se
decide**: una regla heredada no se pisa en silencio, se vuelca y se confirma.

## Enlazar las reglas (para que cualquier sesión las vea)

Dos formas, según desde dónde se abra el asistente:

1. **Desde el núcleo** (recomendado, es como corre `desarrollar-asignadas`): el orquestador vive en
   el repositorio del Cerebro y le pasa al worker `--add-dir <núcleo>`; el worker ve `AGENTS.md`,
   el Cerebro y las skills scoped del repo. No hay que tocar nada.
2. **Desde el repo del proyecto** (abrir Claude Code adentro de `back/<repo>`): su `CLAUDE.md`
   agrega **una línea** que importa las reglas del núcleo por ruta relativa, y la sesión arranca con
   `--add-dir <núcleo>` para poder leer el Cerebro:

```markdown
@../../AGENTS.md
```

   (ajustar los `../` a donde quedó el repo; Claude Code expande el import). Gemini CLI hace lo mismo
   desde `GEMINI.md`; opencode lee `AGENTS.md` del núcleo si se lo apunta en `opencode.json`.

El `CLAUDE.md` del proyecto queda con **lo local**: cómo se construye, cómo se corren los tests, dos
o tres convenciones que sólo valen ahí. Todo lo demás vive en el Cerebro y se cita.

## Lo que NO se hace

- **No se borra** el `CLAUDE.md` ni las skills del proyecto: se achican después de volcar, no antes.
- **No se lee todo el repo**: se lee lo que el relevamiento y la radiografía señalan.
- **No se copian reglas al Cerebro en bloque**: cada una es un ítem con su «sí».
- **No se migra la memoria del asistente** ni se intenta «entender» qué recordaba: lo durable está en
  los archivos; lo demás no era fuente de verdad.
- **No se mezclan tableros**: si el proyecto usa otro (Notion, Miro, un markdown), se decide en
  `DEC-006` cuál manda; el pipeline funciona sobre el tablero local (`bin/tablero-local.py`) o sobre
  Azure por MCP, no sobre los dos.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Relevamiento corrido, cada ítem con destino decidido, el `CLAUDE.md` importa las reglas del núcleo (o se trabaja desde el núcleo), colisiones de nombre resueltas |
| **HALLAZGO** | Dos skills con el mismo nombre y distinto contenido; una regla heredada pisada sin decidir; un `.mcp.json` con un token adentro |
| **SIN DATOS** | El relevamiento no corrió, o el proyecto no tiene configuración de IA (entonces es ingeniería inversa común) |
