---
name: desarrollar-asignadas
description: >-
  Revisar el tablero (Azure DevOps por MCP, o el tablero local de archivos según DEC-006),
  tomar las Tareas asignadas sin dependencias pendientes y desarrollarlas en paralelo: un
  worktree y un worker por tarjeta, con la misión única de armar-mision.py. Dos modos de
  lanzamiento con el mismo flujo: dentro de Orca (variable ORCA_APP_VERSION; workers en
  pestañas) o sin Orca (IntelliJ o terminal: worktrees de git y claude -p / gemini -p;
  references/sin-orca.md). Verifica siempre otro agente en sólo lectura: otro motor si hay, o
  uno del mismo motor con contexto limpio (DEC-005). El orquestador queda atento hasta que la
  última termina. Con DEC-005 confirmada las respuestas del plan salen de la decisión; si no,
  se piden: el plan (que cubre tomar las tarjetas) y un "Aprobar" por Tarea. Usar cuando se pida "desarrollá
  mis tareas asignadas", "arrancá con lo que tengo asignado", "poné a trabajar el tablero",
  "/desarrollar-asignadas". Español (Argentina); no inventa: #ID, estados y dependencias son
  dato duro.
---

# Desarrollar asignadas (Orca o sin Orca + tablero)

Orquesta el desarrollo de las tarjetas asignadas al usuario en el tablero
autorizado, respetando las dependencias declaradas entre ellas, disparando
en paralelo lo que está libre en worktrees separados (una ventana o un
worker por tarjeta), con una verificación independiente, y pidiendo un "Aprobar"
humano (o el que fije `DEC-005`) antes de cerrar el ciclo de cada una (push, comentario de cierre y
link del MR).

## Barreras

- **Los datos del GATE de WORKTREE los da `bin/gate-worktree.py`** (worktrees abiertos en la máquina,
  árbol sucio, rama ya con worktree, base atrás de `origin`) y los del cierre, `bin/datos-cierre.py`.
  La pregunta al humano se hace con esos números a la vista; un script que no corrió es `SIN DATOS`.

- **Dos modos, un flujo.** Con `ORCA_APP_VERSION` los workers van en pestañas de Orca;
  sin ella, en worktrees de git con `claude -p` / `gemini -p` (`references/sin-orca.md`,
  paso 0). Nunca un sub-agente interno **para programar**.
- **Gate de tablero.** Todo lo que lee/escribe se acota al tablero
  autorizado ([[tablero-autorizado]]); si el destino no coincide, no se
  escribe y se avisa.
- **No asumir dependencias ni repo destino.** Si el texto de la tarjeta no
  deja claro de qué depende, o el Area Path no permite inferir el repo, se
  pregunta — nunca se completa el hueco por cuenta propia.
- **Dos confirmaciones, ni una más:** el plan (paso 4), que cubre tomar las
  tarjetas que lista (paso 5), y el "Aprobar" de cada Tarea (6.3), que cubre todo lo que se
  escribe después: reorganizar, pushear y el comentario de cierre. Una tarjeta que ya tiene otra
  persona se pregunta aparte. Con `DEC-005`
  confirmada, sólo las que ella no fija.
- **Quien verifica no es quien programó** (`DEC-005`): el otro motor si hay dos; otro
  agente del mismo motor, con contexto limpio, si hay uno.
- **El orquestador queda atento (6.0)** hasta que la última Tarea termina,
  y avisa de cada una.
- **Fuera de pasarla a Active al tomarla (paso 5) y de 6.3 punto 4, el Estado
  de la tarjeta no lo cambia este flujo.**
- **Todo trabajo que escribe en un worktree va a la vista:** un worker
  supervisado de Orca, una pestaña, o un `claude -p` con su registro en
  `borrador/`. **Prohibido** usar un
  sub-agente interno para escribir en un worktree; los sub-agentes internos
  se usan **sólo** para leer: la verificación de Claude y auditorías.
- **Sin la verificación independiente no se pide el "Aprobar".** SIN
  DATOS no es aprobado: se declara, no se da por bueno.
- **Commits por importancia en el Merge Request** (alrededor de 10 por
  Tarea, como guía); los de TDD quedan en `evidencia/<ID>`, subida a
  `origin` sin Merge Request. Esa rama y la de la Tarea no se borran hasta
  terminar el sprint.
- **Siempre por `desarrollo`.** El método de desarrollo se aplica tal cual, al programar y
  al revisar.
- **Todo en español (Argentina)**, sin PHI, al grano.

## 0. Elegir el modo de lanzamiento (antes que nada)

`ORCA_APP_VERSION` vacía: modo sin Orca (`references/sin-orca.md`); con valor: modo Orca, y su versión
va al plan. Cómo se mira y cómo se lanza: `references/lanzar-workers.md`.

## Flujo

**Antes del paso 1, leé `references/relevar-y-dependencias.md`** (prerrequisito, tablero local y comandos).

1. **Relevar** las Tareas asignadas y no terminales del tablero autorizado ([[tablero-autorizado]]; el local
   o uno por MCP, según `DEC-006`).
2. **Armar el grafo de dependencias**: cada tarjeta, **libre** o **bloqueada** (con el `#ID` del que depende).
3. **Repo destino por tarjeta**, descubierto en cada corrida con la evidencia de la tarjeta:
   `references/repo-destino.md`.

4. **Mostrar el plan y confirmar.** Si `DEC-005` (modo desatendido) está **confirmada** en
   `decisiones.md`, las respuestas de este paso (base, motor, permisos, autorización de commits)
   salen de la DEC y se citan en el plan; sólo lo que la DEC no fija se pregunta. Si no, antes de
   tocar Azure u Orca, presentar
   en un solo mensaje, y pedir confirmación explícita (Sí / ajustar) —nunca
   arrancar en silencio—:
   - la versión de Orca (paso 0), libres (con repo inferido) vs bloqueadas
     (con su dependencia);
   - por cada libre, **de qué rama sale**, con el porqué de la propuesta
     (GATE de WORKTREE de [[AGENTS]]: la base se pregunta, nunca se
     infiere), y **cuántos worktrees hay abiertos** en la máquina;
   - **con qué motor se programa y quién verifica**, según `DEC-005`: con motor
     único (modo solo) programa Claude y verifica otro agente del mismo motor con
     contexto limpio, sin preguntar; con dos motores instalados, el humano elige
     cuál programa y verifica el otro (punto 6.2). Se corre `claude --version` (y
     `gemini --version` si aplica): si el que hace falta no responde, se dice acá y
     esa Tarea no se despacha;
   - que los workers hacen **commits locales de trabajo** (la evidencia
     TDD) y no pushean: entra en el mismo "sí" del plan;
   - **qué tarjetas se toman** (pasan a Asignada a vos y Active; en un sprint, quedan
     congeladas): entra en el mismo "sí" del plan (paso 5);
   - el modo de permisos de Gemini y los **avisos**: `references/plan-detalle.md`.

5. **Tomar cada tarjeta libre.** Delegar en [[tomar-tarea]] para cada una, con el «sí» del plan, que
   ya las lista (pasa a Assigned+Active). Una que ya tiene otra persona sí se pregunta aparte: es su
   gate.

6. **Orquestar en Orca.** Se usa la guía de la versión instalada (`orca
   skills get orchestration`) y el mismo ejecutable `orca` para toda la
   corrida.
   - **Tantas Tareas en simultáneo como deje el techo de worktrees por máquina** (GATE de
     WORKTREE de [[AGENTS]]), contando los que ya están abiertos. Las que
     no entran quedan pendientes para la próxima corrida (no se lanzan a
     ciegas).
   - **Base al día antes de despachar (regla dura).** Todo lo que se envía
     contempla lo último de la rama base, sin importar cuándo se empezó el
     trabajo. Antes de despachar **cualquier** worker o verificador —también
     sobre un worktree que ya existe (ajuste, retoma, verificación)— y antes
     de abrir o actualizar un MR: `git -C <worktree> fetch origin` y
     `git -C <worktree> rev-list --count HEAD..origin/<base>`. Si es mayor
     que 0, se trae `origin/<base>` a la rama **con merge, nunca rebase** (ya
     se pusheó: no se reescribe historia), se resuelven los conflictos, se
     corre la suite completa (el comando de la suite completa del stack) y,
     si hay `openapi.yaml`, Spectral, y se anota el **nuevo SHA de base** (el
     audit pasa a ser `<nuevo-sha-base>..<rama>`). Si el conflicto cambia
     comportamiento o la suite queda en rojo por lo traído, se frena y se
     avisa en criollo: no se despacha. La misión del worker y la del
     verificador dicen que la rama ya contiene la base al día y con qué SHA.
     Sin eso la misión no sale.
   - Cómo se lanza cada worker (Claude o Gemini): `references/lanzar-workers.md`.
   - **Nunca** `orca worktree create` + `orchestration dispatch` para un
     worker de Claude: queda sin supervisión, su aviso de terminado no le
     llega a nadie y el flujo se pierde.

   ### 6.0 El orquestador queda atento (regla dura)

   Lanzada la tanda, el orquestador **no se va**: queda escuchando hasta
   que la última Tarea termine, y le avisa al humano de cada cosa que pasa.

   - Cómo se espera y qué se hace con cada mensaje: `references/orquestador-atento.md`.
   - **Una espera vacía o vencida no es una falla**: es un punto de control.
     Después de tres seguidas, `orca orchestration worker-list --run
     <run_id> --json` y se actúa según `projection.attention` y
     `projection.nextAction`. Sin prueba positiva de que un worker se cortó,
     nunca se lo frena, abandona ni relanza.

   ### 6.1 Misión que recibe cada worker

   La arma `bin/armar-mision.py`; qué lleva: `references/mision-del-worker.md`.

   ### 6.2 Verificación: otro agente, en sólo lectura

   Quien programa no se aprueba a sí mismo: **verifica otro agente** (el otro
   motor si hay dos; si no, uno del mismo motor con contexto limpio, `DEC-005`), con
   contexto nuevo y en **sólo lectura**, sobre el **mismo worktree** de la
   Tarea. Así no se suman worktrees y entran tantas Tareas como deje el techo.

   - Cómo se lanza (con la política de sólo lectura de Gemini) y se lee: `references/verificacion.md`.
   - **Foto antes y después:** `git -C <worktree> status --porcelain` y
     `git rev-parse HEAD` del worktree y del repositorio del Cerebro. Si el
     verificador dejó algo cambiado, se frena y decide el humano.
   - Sin verificador independiente no hay verificación: la Tarea no se despacha (paso
     4). Si falla a mitad de camino, el control queda **SIN DATOS**, y SIN
     DATOS no es aprobado.

   ### 6.3 Validación y entrega: un "Aprobar" por Tarea

   0. **Con `DEC-005` confirmada y su fila «Auto-Aprobar» cumplida** (la cuenta el orquestador línea por
      línea del veredicto, no el total que declara el verificador), no se pregunta: se hace el punto 3, y
      lo que la pregunta iba a mostrar va en el resumen del punto 5.
   1. **Una sola pregunta por Tarea**, apenas está la verificación: *«¿Validás
      la #NNNN?»* (Aprobar / Ajustar). Lleva, para que el "Aprobar" cubra todo
      lo que se va a escribir:
      - el resumen y la verificación, los pendientes, y lo que pasa con el "Aprobar", con el comentario
        de cierre tal como se va a ver: `references/validacion-y-entrega.md`.
   2. a 5. **Ajustar**, **Aprobar** (el link del Merge Request lo abre el humano), el **Estado** (no se
      cambia, salvo `DEC-005`) y el **resumen al humano**, siempre: `references/validacion-y-entrega.md`.

7. **Bloqueadas.** No se disparan en esta corrida. Quedan listadas con su
   dependencia. Cuando el humano aprueba la tarjeta que las bloqueaba, el
   orquestador —que sigue atento— lo avisa y las vuelve a proponer por el
   paso 4 (aprobada no es mergeada: la base se pregunta de nuevo). Con el «Aprobar» automático de
   `DEC-005`, la dependiente se libera recién cuando la que la bloqueaba está mergeada en la base.

## Cuándo leer cada referencia

| Referencia (`references/`) | Se lee |
|---|---|
| `relevar-y-dependencias.md` | Pasos 1 y 2 (y el prerrequisito) |
| `repo-destino.md` | Paso 3 |
| `plan-detalle.md` | Paso 4 (permisos de Gemini, avisos, motor único) |
| `lanzar-workers.md` | Paso 0 y paso 6, antes de despachar |
| `orquestador-atento.md` | 6.0, apenas sale la tanda |
| `mision-del-worker.md` | 6.1, al armar la misión |
| `verificacion.md` | 6.2, cuando termina una Tarea |
| `validacion-y-entrega.md` | 6.3, pregunta y respuesta |
| `sin-orca.md` | Sin `ORCA_APP_VERSION`, todo el flujo |
| `contexto-adicional.md` | Skills y fichas relacionadas |
