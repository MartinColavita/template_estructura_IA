---
id: decisiones
tipo: decisiones
estado: F-Draft
modulo: modulo-ejemplo
title: Decisiones Formalizadas — modulo-ejemplo
description: Decisiones arquitectónicas y funcionales confirmadas por el equipo, una por sección, con su estado, su fuente y su footer de trazabilidad.
tags: [decisiones, arquitectura, modulo-ejemplo]
last_updated: 2026-10-22
author: "equipo"
---

# Decisiones Formalizadas — modulo-ejemplo

> Una decisión por sección, con código `DEC-nnn` consecutivo. Cada una dice **qué se decidió**,
> **por qué**, **qué queda afuera** y **de dónde salió** (reunión, documento o chat). Una decisión
> **no se borra**: si cambia, se escribe la nueva y la vieja queda como superada, con el link.
> Lo que todavía no está decidido va con `⚠` y una pregunta en `pendientes.md`.
> Las dos primeras vienen con el template; la tercera es la primera que el equipo tiene que tomar.

## DEC-001 — El código de la aplicación no vive en este repositorio

**Estado:** Confirmado (viene con el template)

Este repositorio es **solo conocimiento y agentes**: el Cerebro Digital, las reglas, las skills y
los scripts. El código de la aplicación vive en **repositorios propios** (uno de back, uno o más
de front, uno por aplicación), que se **clonan adentro** de `back/<repo>` y `front/<app>` para que
un asistente lea en una sola sesión el Cerebro, las reglas, la Tarea y el código. Lo clonado no se
versiona acá (`.gitignore`).

**Por qué:** separa el ciclo de vida del conocimiento (fichas, decisiones, el «sí» por ítem)
del ciclo de vida del código (ramas `task/*`, Merge Requests). Y evita que el repositorio del
Cerebro reciba código por accidente.

**Lo que define:** las skills de desarrollo (`guiar-tdd`, `verificar-tdd`, `auditar-codigo`,
`armar-swagger`, `consultar-cerebro`, `diagnosticar-repo`) viven en `back/` y `front/` y aplican
a lo que se clone adentro; el orquestador de desarrollo vive acá.

_Últ. modif.: 2026-10-22 — @equipo — decisión heredada del template_

## DEC-002 — Arquitectura del código por módulos de dominio con capas

**Estado:** **Confirmado (2026-11-02).** Vale para cualquier lenguaje del back (`DEC-003` lo fija por proyecto): las capas son carpetas o paquetes con esos nombres, en Java, Python, Go, .NET, Node o el que sea.

El back se organiza como **monolito modular por módulos de dominio**: cada módulo es dueño de un
concepto de negocio y de sus tablas, y adentro tiene cuatro capas más la de errores:

```
<modulo>/
├─ api/           lo que habla HTTP: traduce la entrada a un comando y llama al caso de uso. No decide
├─ application/   un caso de uso por clase (recibe un comando, nunca un DTO de api); declara las
│                 interfaces hacia afuera (sistemas externos, base propia)
├─ domain/        las reglas de negocio. Sin dependencias del framework
├─ exceptions/    los errores del módulo (extienden los de shared/)
└─ infra/         las implementaciones: clientes de sistemas externos, repositorios, configuración
shared/           lo transversal: formato único de error, errores base, configuración. No depende de ningún módulo
```

**Reglas de dependencia:** `api → application, domain` · `application → domain` ·
`infra → application, domain` · `domain →` nada · `exceptions/` la usan todas y sólo depende de
`shared`. **Entre módulos** se llama sólo a la `application` del otro (sus casos de uso) y se
pueden importar los tipos que esos casos de uso devuelven o lanzan; importar `<otro>.api` o
`<otro>.infra` está prohibido. Entidades de otro módulo se referencian por id. **Una Tarea
modifica un solo módulo.** El código HTTP de un error lo decide **un único** traductor de errores
en `shared`, con un formato de error único para toda la API; ningún adaptador HTTP mapea errores.
Sin carpetas por tipo técnico (`util`, `model`, `service`, `impl`); las implementaciones se
nombran por lo que son.

**Por qué:** permite trabajar Tareas en paralelo sin pisarse (cada una vive en un módulo), hace
que un módulo se entienda sin leer los otros, y deja los límites verificables por una fitness
function de arquitectura en el build. Estas reglas son las que el verificador chequea una por una
(`configuracion-ia/orquestador-desarrollo.md` §«Convenciones del Cerebro»).

**Qué falta decidir (⚠):** cómo se materializa en el stack elegido (`DEC-003`), el nombre del
paquete/carpeta base y las subcarpetas de cada capa. Se documenta en [[esqueleto-proyectos]].

_Últ. modif.: 2026-10-22 — @equipo — propuesta heredada del template_

## DEC-003 — Stack técnico del back, del front y del despliegue

**Estado:** ⚠ **A definir por el equipo.** Hasta que exista, toda skill que dependa del stack
reporta `SIN DATOS` en lo que no pueda verificar.

| Tema | Decisión | Estado |
|---|---|---|
| Lenguaje y framework del back | — | ⚠ a definir |
| Herramienta de build y runner de tests del back | — | ⚠ a definir |
| Lenguaje y framework del front | — | ⚠ a definir |
| Runner de tests y simulación de la API en el front | — | ⚠ a definir |
| Motor de base de datos y versión mínima soportada | — | ⚠ a definir |
| Herramienta de migraciones de base | — | ⚠ a definir |
| Analizador de seguridad (SAST/SCA) que frena la entrega | — | ⚠ a definir |
| Umbral de cobertura exigido por el build | — | ⚠ a definir |
| Observabilidad (métricas, trazas, logs estructurados, chequeos de salud) | — | ⚠ a definir |
| Plataforma de despliegue | — | ⚠ a definir |
| Tipo de aplicación (web, Electron, escritorio con webview, escritorio nativo, móvil, línea de comandos, API) y el motor de pruebas de punta a punta que le corresponde (Playwright, WebDriver, Appium o Maestro, proceso, HTTP), con el atributo de identificación estable (`data-testid` o `automation-id`) | — | ⚠ a definir |
| Pruebas de aceptación: dónde viven (`qa/<app>-e2e/` o en el repo de código), ambiente contra el que corren y si frenan la entrega | — | ⚠ a definir |

**Al decidirlo:** se completa esta tabla, se escribe [[esqueleto-proyectos]] y se completan
`tdd-stack-back.md` y `tdd-stack-front.md` de la skill `desarrollo`, y las tablas «Stack» de
`back/README.md` y `front/README.md`.

_Últ. modif.: 2026-10-22 — @equipo — abierta al instanciar el template_

## DEC-004 — Refactor o migración de la aplicación existente (si la hay)

**Estado:** ⚠ **No aplica todavía / a decidir por quien instanció (modo solo) o por el equipo.** Sólo existe si
el proyecto arranca de una aplicación que ya funciona. La decide la persona con la tabla de estrategias de la
skill `planificar-modernizacion` a la vista (las filas medibles las trae `bin/inventariar-codigo.py`) y la
escribe `cerebro-curator` con su «sí».

| Qué se decide | Opción | Por qué |
|---|---|---|
| Estrategia: refactor en el lugar · migración por estrangulador (slice por slice) · corrida en paralelo · subir de versión (framework o lenguaje) · no tocarla. Gran explosión no es opción | — | — |
| Qué reglas candidatas se MIGRAN, cuáles se DESCARTAN y cuáles quedan en DECIDE EL HUMANO (tabla de curaduría de `planificar-modernizacion`) | — | — |
| Orden de módulos o slices | — | — |
| Qué queda fuera de las reglas `C1…C8` mientras tanto, y en qué orden se trae | — | — |
| Cuándo se apaga la aplicación vieja (migración) | — | — |

Método de cada Tarea: `configuracion-ia/skills/desarrollo/references/metodo/refactor-y-migracion.md`. El avance por slice
y la barrera del corte: `aplicacion/modernizacion.md` con `bin/mapa-modernizacion.py`.

_Últ. modif.: 2026-10-30 — @equipo — plantilla heredada del template_

## DEC-005 — Modo desatendido (autorizaciones permanentes del flujo de desarrollo)

**Estado:** ⚠ **Sin firmar** <se firma al instanciar en modo solo>. La firma quien arranca el proyecto en
modo solo, si acepta el modo desatendido (`bin/instanciar.py --desatendido`, o la pregunta de
`arrancar-proyecto`), y queda la fecha y su nombre; sin firma no autoriza nada y todo se pregunta. Para el
modo equipo sigue ⚠ a confirmar por el equipo. Con la columna que aplique **confirmada**, el GATE de WORKTREE y los pasos de plan de
`desarrollar-asignadas` **toman estos valores y los citan** en vez de preguntar: una autorización escrita por
una persona vale como su «sí». Lo que la tabla no fija, se sigue preguntando. Cambiarla es cambiar esta
decisión, con su footer. El modo lo fija `DEC-006`.

| Qué fija | Modo solo | Modo equipo (⚠ propuesta) |
|---|---|---|
| Base de los worktrees | `develop` al día con `origin` (si avanzó, merge; nunca rebase); sin remoto, `develop` local | Igual |
| Techo de worktrees por máquina | 6 | 6 |
| Carpeta de los worktrees | `<carpeta padre del repositorio>/worktrees/<ID>-<slug>` | Igual |
| Motor que programa | **Claude Code** | Lo elige quien despacha, por lote |
| Quién verifica | **Otro agente de Claude Code, contexto limpio, sólo lectura**, declarado en el veredicto («Verificado por: Claude Code · sub-agente de sólo lectura»). Si hay otro motor instalado, se prefiere | El otro motor; sin él, esa Tarea no se despacha |
| Permisos del worker | Claude: el modo de la sesión del orquestador; Gemini (si se usa): `auto_edit` | Igual |
| Commits locales de trabajo | Autorizados en la rama de la Tarea; nunca push sin el Aprobar | Igual |
| Tomar la tarjeta | Automático: `bin/tablero-local.py tomar` (o `tomar-tarea` en Azure) sin preguntar | Con el plan |
| Push y Merge Request | Con el Aprobar; el Merge Request lo abre quien instanció (o se trabaja sin MR: merge local a `develop` con la suite en verde) | Con el Aprobar; lo abre `<persona o cuenta técnica>` |
| Auto-«Aprobar» | **Sí**, sólo si BLOQUEANTES = 0 y `SIN DATOS (no se pudo mirar)` = 0; con pendientes declarados se aprueba y se listan en el cierre | ⚠ a decidir |
| Comentario de cierre | Automático, con los datos de `datos-cierre.py` | Con el Aprobar |
| Estado de la tarjeta al cerrar | `Resolved` automático; `Closed` lo decide una persona (`--confirmado`) | Lo decide una persona |
| Repositorios de infraestructura | Fuera de alcance salvo pedido explícito | Igual |
| Dos Tareas sobre el mismo archivo | En serie | En serie (regla candidata) |

_Últ. modif.: 2026-11-13 — el template la trae sin firmar: una autorización vale si la firmó alguien de este proyecto (Claude único, verificación por otro agente del mismo motor). La columna de modo equipo se completa **sólo si un proyecto arranca diciendo que habrá equipo**; mientras tanto no se usa y no frena nada._

## DEC-006 — Modo de trabajo y tablero

**Estado:** **Se fija al instanciar** con `bin/instanciar.py --modo solo|equipo --tablero local|azure` y queda
escrito acá. ⚠ <se fija al instanciar>

| | Modo **solo** | Modo **equipo** |
|---|---|---|
| Tablero | **Local**: `cerebro-digital/<modulo>/backlog/` por `bin/tablero-local.py`; una ficha validada baja 1:1 con `bin/derivar-a-tablero-local.py` (o Azure si se elige) | Azure DevOps, **Jira u otro tablero del mercado**, por su MCP (`--tablero azure|jira|otro`; la tabla de herramientas por función de `integracion-azure-mcp/00-index.md` traduce las operaciones y el método del toolkit `tablero/` vale para cualquiera) |
| Quién escribe el Cerebro | Quien instanció, directo a `develop`, por `cerebro-curator` con su «sí» | Igual; si son dos, cada uno en su rama y lo integra un Merge Request que revisa el otro |
| Quién firma | El instanciador (`--autor`): su nombre va en las diferencias aceptadas y en «Corte aprobado por» | Cada persona con su nombre |
| Verificación del código | Otro agente del mismo motor (DEC-005, modo solo) | El otro motor |
| Confirmaciones | Las que deja DEC-005 modo solo | Todas las de los GATEs |
| GATE de NIVEL, sprints y tarjeta congelada | No aplican (no hay otra persona ni sprint) | Aplican |

**Por qué se pregunta en cada proyecto:** el mismo esqueleto sirve para un desarrollo personal y para un equipo,
y los flujos cambian (quién confirma, dónde vive el tablero, cómo entra el conocimiento). Elegirlo al instanciar,
y dejarlo escrito acá, evita que cada sesión lo adivine.

_Últ. modif.: 2026-11-02 — @equipo — decisión nueva del template; el valor lo fija cada proyecto al instanciar_
