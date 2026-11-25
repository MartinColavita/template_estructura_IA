# Repo destino por tarjeta

Parte de la skill `desarrollar-asignadas`: se lee en el paso 3, para decidir a qué repo va cada tarjeta antes de armar el plan del paso 4.

3. **Repo destino por tarjeta.** La lista de repos no está fija en esta
skill: se descubre en cada corrida, porque van a ir apareciendo más
(`<repo-front-1>`, `<repo-front-2>`, `<repo-infra>`, etc.).

**3.1 Descubrir los repos candidatos.**
- **Primero, la carpeta padre de este repo** (repos hermanos, que es
  como están clonados hoy: por ejemplo `<repo-back>`,
  `<repo-front>`): cada subcarpeta que sea un repo git
  (`git -C <carpeta> rev-parse --is-inside-work-tree`).
- **Después, adentro de este repo**, en `back/*` y `front/*` (mismo
  chequeo). Es la convención documentada en `back/README.md` y
  `front/README.md`: el código se clona en `back/<repo>` y
  `front/<app>`.
- Dónde viven los repos de código es una **decisión abierta** (ver la
  tabla de decisiones abiertas de `references/sin-orca.md`); mientras
  tanto se aceptan las dos ubicaciones, sin aviso.
- De cada uno, anotar la ruta, el nombre de la carpeta y el remoto
  `origin` (el último tramo de la URL es el nombre real del repo en
  GitLab).
- Si un mismo repo (mismo remoto `origin`) aparece en los dos lugares,
  **preguntar** cuál usar.
- `orca repo list --json`: qué repos ya están registrados en Orca y con
  qué `id`. El `--repo id:<id>` del paso 6 sale de acá.
- **Excluir este repositorio** (el del Cerebro): es el del
  conocimiento, no el del código ([[decisiones#DEC-001]]). Solo es
  destino si la tarjeta es explícitamente sobre el Cerebro o las skills.

**3.2 Buscar la evidencia en la tarjeta**, en este orden:
1. El campo **«Componente / repo:»** de la Descripción (plantilla de
   Tarea).
2. El **Área** (Area Path) y la **etiqueta**, si nombran un repo o una
   capa.
3. El **prefijo del título** («Backend -», «API -», «Front -»,
   «Infra -»…).
4. La **Historia padre**: si todas sus Tareas hermanas ya tienen repo, se
   muestra como pista, nunca como prueba.

**3.3 Decidir.**
- **Coincidencia exacta y única** entre la evidencia y el nombre de un
  repo descubierto → repo inferido. En el plan del paso 4 se muestra
  **de dónde salió** (por ejemplo: «Componente / repo: <repo-back>»).
- **Coincidencia aproximada** (un alias o un nombre viejo, por ejemplo
  «backend-monolito» → `<repo-back>`) → se muestra como
  **propuesta ⚠** con el porqué, y se confirma en el paso 4. No se da
  por buena en silencio.
- **Varias opciones, ninguna o evidencia contradictoria** (el título
  dice «Front» y el campo dice back) → **preguntar** por tarjeta, en
  criollo y con los repos descubiertos como opciones. Nunca repartir a
  ciegas.
- **La tarjeta nombra un repo que no está clonado** (ni en la carpeta
  padre ni en `back/` / `front/`) → avisar y preguntar (¿se clona?, ¿se deja para otra corrida?). No
  clonar por cuenta propia.
- **El repo está clonado pero no registrado en Orca** → avisar y
  preguntar antes de `orca repo add`.

Si varias tarjetas del lote van a repos distintos, se reparten en
worktrees de su propio repo. El techo de paralelo (paso 6) es por
máquina, no por repo.
