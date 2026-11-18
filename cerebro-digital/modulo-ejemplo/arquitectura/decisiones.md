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
versiona acá (`.gitignore`). **Excepción:** las pruebas de punta a punta viven en `qa/` y se versionan acá (M-045).

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

_Últ. modif.: 2026-11-13 — @equipo — confirmada (2026-11-02); cómo se materializa en el stack queda ⚠ hasta `DEC-003`_

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
| Herramienta de migraciones de base y la carpeta donde viven las migraciones | — | ⚠ a definir |
| Analizador de seguridad (SAST/SCA) que frena la entrega (lo detalla `DEC-009`) | — | ⚠ a definir |
| Umbral de cobertura exigido por el build | — | ⚠ a definir |
| Observabilidad (métricas, trazas, logs estructurados, chequeos de salud; lo de los servidores, en `DEC-008`) | — | ⚠ a definir |
| Plataforma de despliegue (la detalla `DEC-007`) | — | ⚠ a definir |
| Tipo de aplicación (web, Electron, escritorio con webview, escritorio nativo, móvil, línea de comandos, API) y el motor de pruebas de punta a punta que le corresponde (Playwright, WebDriver, Appium o Maestro, proceso, HTTP), con el atributo de identificación estable (`data-testid` o `automation-id`) | — | ⚠ a definir |
| Pruebas de aceptación: herramienta, ambiente contra el que corren y si frenan la entrega (viven en `qa/`, M-045) | — | ⚠ a definir |

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

**Estado:** ⚠ **Sin firmar** <la firma quien arranca el proyecto en modo solo, con `bin/instanciar.py
--desatendido` o la pregunta de `arrancar-proyecto`; sin firma no autoriza nada>. Para el modo equipo sigue ⚠ a
confirmar por el equipo. Con la columna que aplique **confirmada**, vale como el «sí» de los GATEs que nombra
`AGENTS.md` («Autorización permanente»). Cambiarla es cambiar esta decisión, con su footer. El modo lo fija
`DEC-006`.

| Qué fija | Modo solo | Modo equipo (⚠ propuesta) |
|---|---|---|
| Base de los worktrees | `develop` al día con `origin` (si avanzó, merge; nunca rebase); sin remoto, `develop` local | Igual |
| Techo de worktrees por máquina | El del GATE de WORKTREE (`AGENTS.md`: 10) | Igual |
| Carpeta de los worktrees | `<carpeta padre del repositorio>/worktrees/<ID>-<slug>` | Igual |
| Motor que programa | **Claude Code** | Lo elige quien despacha, por lote |
| Quién verifica | **Otro agente de Claude Code, contexto limpio, sólo lectura**, declarado en el veredicto («Verificado por: Claude Code · sólo lectura, contexto limpio»). Si hay otro motor instalado, se prefiere | El otro motor; sin él, esa Tarea no se despacha |
| Permisos del worker | Claude: el modo de la sesión del orquestador; Gemini (si se usa): `auto_edit` | Igual |
| Commits locales de trabajo | Autorizados en la rama de la Tarea; nunca push sin el Aprobar | Igual |
| Tomar la tarjeta | Automático: `bin/tablero-local.py tomar` (o `tomar-tarea` en Azure) sin preguntar | Con el plan |
| Push y Merge Request | Con el Aprobar; el Merge Request lo abre quien instanció (o se trabaja sin MR: merge local a `develop` con la suite en verde) | Con el Aprobar; lo abre `<persona o cuenta técnica>` |
| Auto-«Aprobar» | **Sí**, sólo si ninguna línea del veredicto da HALLAZGO ni `SIN DATOS (no se pudo mirar)`. Con pendientes declarados se aprueba y se listan en el cierre | ⚠ a decidir |
| Comentario de cierre | Automático, con los datos de `datos-cierre.py` | Con el Aprobar |
| Estado de la tarjeta al cerrar | `Resolved` automático sólo si el tablero lo tiene para una Tarea (el local sí; en Azure, sólo el proceso CMMI), la verificación quedó toda en OK o N/A y la tarjeta no tiene pendientes sin resolver; si no, lo decide una persona con la lista a la vista. `Closed`, siempre una persona (`--confirmado`) | Lo decide una persona |
| Infraestructura, despliegue, servidores, seguridad y GitLab | **Esta DEC no autoriza nada**: rigen las barreras de `AGENTS.md` y `DEC-007` a `DEC-010`. Lo único que sigue cubierto es lo del ciclo de la Tarea: el push de su rama y abrir su Merge Request | Igual |
| Dos Tareas sobre el mismo archivo | En serie | En serie (regla candidata) |

_Últ. modif.: 2026-11-13 — sale sin firmar del template (M-027). La columna de modo equipo se completa **sólo si un proyecto arranca diciendo que habrá equipo**; mientras tanto no se usa y no frena nada._

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

## DEC-007 — Infraestructura, ambientes y entrega

**Estado:** ⚠ **A decidir: propuesta del template.** La decide el equipo (o quien instanció, en modo solo) y la
escribe `cerebro-curator` con su «sí». Mientras una fila esté en `⚠`, lo que dependa de ella es `SIN DATOS`, y los
scripts usan el valor por defecto que declaran y lo dicen. **`DEC-005` no autoriza nada de lo que esta decisión fija.**

| Tema | Recomendación (⚠ a decidir) | Decisión |
|---|---|---|
| Plataforma destino | La que ya use la organización (una nube, varias, on-premise o PaaS); el template no tiene preferencia | — |
| Herramienta de infraestructura como código | Una sola por proyecto: Terraform (licencia BSL), OpenTofu (MPL-2.0, libre y para más de una nube), Bicep (sólo Azure) o Pulumi | — |
| Dónde vive el código de infraestructura | En un repositorio propio, nunca en el del Cerebro (`DEC-001`) | — |
| Estado | Uno por ambiente, con bloqueo, acceso por identidad, versionado y cifrado; `prevent_destroy` en todo lo que guarda datos | — |
| Identidad del pipeline | Federada (sin secretos guardados), una por ambiente, autorizada pipeline por pipeline | — |
| Gestor de secretos | El de la plataforma en ejecución; SOPS con age sólo para el secreto que tiene que viajar en git; Vault tiene licencia BSL, OpenBao es la alternativa libre | — |
| Módulos | Propios sólo por capacidad que la arquitectura nombra; de registro, con versión exacta; de git, con SHA | — |
| Cómo corre la aplicación | Lo más simple que cumpla los atributos de calidad (PaaS, contenedores administrados, máquinas virtuales); Kubernetes sólo con un motivo escrito | — |
| Zonas de red por ambiente | Borde, aplicación, datos y administración, con una red por ambiente; datos sin dirección pública ni salida a internet; producción sin conexión directa con desarrollo ni con prueba. El detalle, en [[red]] | — |
| Acceso administrativo | Primero el acceso administrado de la plataforma, sin puerto abierto (por identidad y con registro); si no hay, un bastión con origen acotado; la VPN, tercera opción. Nunca SSH ni escritorio remoto abiertos a todo internet (lo marca `bin/auditar-iac.py`, regla `RED-ABIERTA`) | — |
| TLS y DNS | TLS termina en el borde (balanceador o proxy), re-cifrado hasta la aplicación si viajan datos de personas; certificados con renovación automática. Zona DNS pública mínima y una privada para lo interno; registros como código si el proveedor lo permite; registro `CAA` | — |
| Salida a internet | Datos sin salida; la aplicación sale por un punto controlado, con lista de destinos si el riesgo lo pide | — |
| Red en Kubernetes (sólo si se elige Kubernetes) | Un plugin de red que aplique NetworkPolicy; negar todo por defecto en cada espacio de nombres; lo público entra por Ingress o Gateway | — |
| Escáneres de infraestructura que frenan | TFLint, más Checkov **o** Trivy (uno solo), más hadolint; todos fijados por versión y hash | — |
| Plataforma de CI/CD y dónde vive la aprobación de producción | En la plataforma, nunca en el YAML: GitHub (en repositorios privados, los revisores de un ambiente sólo con Enterprise), GitLab (ambientes protegidos desde Premium; en Free, lo que fija `DEC-010`) o Azure Pipelines (las aprobaciones del ambiente). Si el plan no la trae, se elige otra barrera de la plataforma y se escribe acá | — |
| Identidad de la IA en la plataforma | Lee; quién abre el Merge Request lo fija `DEC-005`. No aprueba, no cambia la protección, no toca secretos; disparar un pipeline que llega a un ambiente protegido, como dice el GATE de DESPLIEGUE de `AGENTS.md` | — |
| Estrategia de despliegue y vuelta atrás, por servicio | «Una vez», y se vuelve desplegando la versión anterior; por tandas, azul y verde o canario sólo con un motivo escrito; GitOps sólo con Kubernetes | — |
| Ambientes y promoción | Desarrollo, Prueba y Producción, uno por fila en [[ambientes]]; se promueve el mismo artefacto; producción la aprueba siempre una persona | — |
| Cadena de suministro | Acciones y plantillas del CI por SHA (o lockfile); SLSA nivel 2 con la atestación de la plataforma; SBOM en CycloneDX; una sola herramienta de actualización de dependencias, con espera antes de proponer una versión | — |
| Migraciones de base | La herramienta y la carpeta donde viven las fija `DEC-003` (la carpeta la usa `bin/clasificar-migraciones.py`) | — |
Los ambientes, uno por fila, viven en [[ambientes]]; los recursos de cada uno, en [[infraestructura]]. El método, en la
skill `arquitectura-e-infraestructura` y en `despliegue-continuo`.

_Últ. modif.: 2026-11-17 — @equipo — propuesta del template, a decidir (M-047, M-048)_

## DEC-008 — Operación de servidores

**Estado:** ⚠ **A decidir: propuesta del template.** La decide el equipo (o quien instanció, en modo solo) y la
escribe `cerebro-curator` con su «sí». Mientras una fila esté en `⚠`, lo que dependa de ella es `SIN DATOS`, y los
scripts usan el valor por defecto que declaran y lo dicen. **`DEC-005` no autoriza nada de lo que esta decisión fija.**

| Tema | Recomendación (⚠ a decidir) | Decisión |
|---|---|---|
| Alcance de la IA y nivel por ambiente | Por alias, en [[inventario]]: hasta N2 en prueba y en producción; en producción, sólo con la identidad de cambio instalada. Sin identidades, todo N0 con los reportes que trae una persona | — |
| Identidades de acceso | `ia-lectura`: sólo puede correr el colector (comando forzado). `ia-cambio`: un certificado de 1 h que firma una persona, con `sudoers` de comandos exactos. Nunca root ni `sudo` sin límite | — |
| Registro de lo que se hizo | En el servidor (SSH y `sudo` con entrada y salida), copiado al recolector de logs; el resumen, en `operacion/cambios.md`; la retención, la de la organización | — |
| Umbrales de salud | Disco e inodos 90 %, reinicio pendiente 7 días, un reporte del colector de más de 24 h es viejo; certificado con menos de un tercio de su vida o menos de 14 días (los valores por defecto de los scripts) | — |
| Ventana y canario | La ventana, por alias en el inventario. El primer servidor es el canario: 1 h en prueba y 1 día en producción antes del siguiente | — |
| Parches | Automáticos, sólo los de seguridad, sin reinicio automático en producción | — |
| Respaldos | 3-2-1 más una copia fuera de línea o inmutable; chequeo semanal y restauración de prueba mensual; podar o borrar respaldos lo hace siempre una persona | — |
| Observabilidad | Lo que la organización ya tenga; si no hay nada, OpenTelemetry Collector (o Alloy) con Prometheus, Alertmanager, Loki y Grafana | — |
| Cuándo hay postmortem | Corte visible para la gente, pérdida de datos, un cambio de urgencia en producción o más de 1 h de incidente | — |

El método, en la skill `operacion-de-servidores`.

_Últ. modif.: 2026-11-17 — @equipo — propuesta del template, a decidir (M-049)_

## DEC-009 — Seguridad

**Estado:** ⚠ **A decidir: propuesta del template.** La decide el equipo (o quien instanció, en modo solo) y la
escribe `cerebro-curator` con su «sí». Mientras una fila esté en `⚠`, lo que dependa de ella es `SIN DATOS`, y los
scripts usan el valor por defecto que declaran y lo dicen. **`DEC-005` no autoriza nada de lo que esta decisión fija.**

| Tema | Recomendación (⚠ a decidir) | Decisión |
|---|---|---|
| Herramientas | Aplicación: Opengrep (o Semgrep CE), Bandit si hay Python, OSV-Scanner, Gitleaks y ZAP para la prueba dinámica. Imágenes: Trivy **o** Grype, uno solo. Todas fijadas por versión y hash (ZAP, por digest); nunca las versiones de Trivy del incidente de marzo de 2026 | — |
| Qué frena la entrega | Una vulnerabilidad CRÍTICA o ALTA nueva, sin supresión vigente; un secreto, siempre. MEDIA, con plazo | — |
| Prioridad y plazos (una sola tabla para la aplicación y los servidores) | P1 frena y se arregla ya (un secreto se rota); P2 frena el Merge Request; P3 con plazo; P4 se registra. EPSS en el percentil 0,90 o más sube a P2. **Propuesta de días, no dato:** en el catálogo KEV y expuesto, 3; en KEV y no expuesto, 14; crítica con EPSS alto, 30; el resto, la próxima ventana | — |
| Antigüedad de los datos | La base de vulnerabilidades, KEV y EPSS, 7 días (la de imágenes, 120 h); un informe de Lynis, 7 días. Más viejo vale como ausente: `SIN DATOS` | — |
| Supresiones y excepciones | Las aprueba una persona que no escribió el cambio, con motivo, su nombre y vencimiento obligatorio (`vence: AAAA-MM-DD`); la línea de base del código heredado, versionada en su repositorio y aceptada por Merge Request | — |
| Qué sale de la máquina | Las métricas de los escáneres, apagadas; KEV, EPSS y la base de OSV se bajan enteros, nunca CVE por CVE; pip-audit y npm audit sólo si se acepta mandar los nombres de los paquetes; un revisor de IA en el CI, sólo como aviso | — |
| Cómo audita la IA un servidor | Desde afuera y sin cuenta (el protocolo SSH); lo de adentro lo genera una persona y se lo pasa. Nunca con la cuenta de una persona ni como root | — |
| Línea base por sistema operativo | El perfil de ComplianceAsCode alineado a CIS nivel 1, citado por número de control (nunca «cumple CIS»); STIG sólo si un contrato lo exige | — |
| Quién autoriza una fila de prueba dinámica en el inventario | Un rol de seguridad o de infraestructura; no el equipo de desarrollo solo | — |
| Incidente de seguridad | Responsable y suplente, por rol. La evidencia, fuera del repositorio, donde y por cuánto lo fijen el equipo y legales. Quién comunica afuera y qué hay que notificar, lo definen el equipo y legales: la IA no lo infiere ni comunica | — |

El método, en la skill `seguridad`; la política del módulo, en `seguridad/politica.md`.

_Últ. modif.: 2026-11-17 — @equipo — propuesta del template, a decidir (M-050)_

## DEC-010 — GitLab: instancia, plan, identidad y barreras

**Estado:** ⚠ **A decidir: propuesta del template.** La decide el equipo (o quien instanció, en modo solo) y la
escribe `cerebro-curator` con su «sí». Mientras una fila esté en `⚠`, lo que dependa de ella es `SIN DATOS`, y los
scripts usan el valor por defecto que declaran y lo dicen. **`DEC-005` no autoriza nada de lo que esta decisión fija.**

| Tema | Recomendación (⚠ a decidir) | Decisión |
|---|---|---|
| Destino autorizado | La tabla «Destino autorizado» de [[gitlab]] (instancia y rutas exactas); esta decisión no repite los valores. Sin una fila ahí, la IA no lee ni escribe en GitLab | — |
| Ofrecimiento y plan | Lo que haya (GitLab.com, instancia propia o Dedicated; Free, Premium o Ultimate), anotado en la ficha: el plan decide qué barreras existen | — |
| Identidad de la IA | Token de permisos finos, uno por persona, sólo los proyectos del destino y sin el recurso de variables (donde no los hay, uno de acceso de proyecto: Reporter para leer, Developer para escribir); rol máximo Developer (Planner si sólo escribe en el tablero); nunca el token de una persona con más rol | — |
| Servidor MCP | El oficial, con la versión 19.5 o más y habilitado; si no, el de la comunidad, fijado y en sólo lectura; el de escritura en modo `modify`, nunca `full` | — |
| Barrera de producción | La que dé el plan: ambiente protegido con aprobación (Premium) o rama y tag protegidos con variables y runners protegidos (Free); se enlaza con la fila de ambientes de `DEC-007` | — |
| Cierre automático de issues | El ajuste del proyecto, apagado | — |
| Runners | De proyecto, protegidos y con etiqueta para desplegar; sin ejecutor `shell` compartido; sin `privileged` salvo decisión escrita | — |

El método, en la skill `gestion-de-gitlab`.

_Últ. modif.: 2026-11-17 — @equipo — propuesta del template, a decidir (M-051)_
