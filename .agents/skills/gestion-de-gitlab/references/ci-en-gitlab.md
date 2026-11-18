# GitLab CI: lo propio de GitLab que el método general no cubre

> Fuentes: documentación oficial de GitLab CI/CD (referencia del YAML, `include`, componentes, inputs, variables,
> job token, `id_tokens`, caché, ambientes, CI Lint). Detalle en
> `cerebro-digital/devops/fuentes-gitlab.md`.

**El pipeline en general no está acá.** Estructura, fijado de imágenes y acciones, caché, ambientes, OIDC y la
barrera de despliegue son de [[despliegue-continuo]]:
`cerebro-digital/configuracion-ia/skills/despliegue-continuo/references/armar-pipeline.md`, y los verifica
`bin/verificar-pipeline.py`. El YAML es código y entra por [[desarrollo]]. Acá va sólo lo que es propio de GitLab, y
los **ajustes de CI del proyecto**, que no están en el YAML y mide `bin/auditar-gitlab.py proyecto`.

## En el YAML

**Lo que se cuenta ya lo mide `bin/verificar-pipeline.py`**: `include` sin fijar o remoto sin `integrity` y
componentes con `@~latest` (P2), un despliegue a producción cuya única barrera es `when: manual` (P6), `dind` o el
socket de Docker, y `workflow:rules` y `only`/`except` (P8). Qué hacer con cada uno está en
`cerebro-digital/configuracion-ia/skills/despliegue-continuo/references/armar-pipeline.md`; acá no se repite.
`dind`, además, sólo con decisión escrita (`DEC-010`): pide un runner privilegiado
([runners-e-instancia.md](runners-e-instancia.md)).

| Tema | Qué hacer | Por qué | Plan |
|---|---|---|---|
| Componentes en una instancia propia | Un espejo del proyecto del componente en la misma instancia | Un componente sólo se referencia en la misma instancia | Free |
| `spec:inputs` | Preferirlos a las variables de pipeline: tienen tipo y se validan al crear el pipeline | Una variable de pipeline pisa las del YAML | Free |
| Variables | Las de producción, **protegidas** (sólo en refs protegidas) y enmascaradas u ocultas | Un `.gitlab-ci.yml` malicioso expone **también** las enmascaradas y las protegidas de la ref donde corre | Free |
| `tags:` del job | El job con secretos de despliegue, a un runner **protegido** y con su etiqueta | Sin etiqueta, lo toma cualquier runner, incluso uno de instancia | Free |
| `id_tokens` | Un token por job con su `aud`; la confianza del lado del gestor atada a `project_id` y `namespace_id` (no cambian al renombrar), más `ref_protected` y, desde la 18.7, `environment_protected`; nunca `user_login` ni `user_email` como única condición | En Free es la mejor barrera para un secreto de producción: el gestor sólo lo entrega a una ref protegida | Free |
| Job token | Usarlo dentro del pipeline antes que cualquier token personal | Alcanza lo de quien disparó, en endpoints listados, mientras dura el job | Free |
| Congelamiento | Si se usa, el job tiene que mirar `CI_DEPLOY_FREEZE` y frenar | GitLab sólo pone la variable | Free |
| `trigger:` | Sin reenviar las variables de pipeline al de abajo | Lo que entra por variable sigue de largo | Free |
| `release:` | Con `glab` (1.58.0 o más), no con la imagen vieja de `release-cli` | — | Free |
| `secrets:` | Vault, Azure Key Vault, GCP o AWS; GitLab Secrets Manager, desde la 19.5 | En Free no está: `id_tokens` y la línea de comandos del gestor | Premium |

## En los ajustes del proyecto (no en el YAML)

Los mide `bin/auditar-gitlab.py proyecto`; dónde se cambian, en [proyecto-y-grupo.md](proyecto-y-grupo.md).

| Ajuste | Valor | Chequeo |
|---|---|---|
| Rol mínimo para variables de pipeline | `no_one_allowed` (o `maintainer`) | `variables-de-pipeline` |
| Cachés separadas para ramas protegidas (las claves llevan `-protected` o `-non_protected`) | Encendido: apagarlo es quitar una barrera | `caches-separadas` |
| «Prevent outdated deployment jobs»: para volver atrás, un pipeline nuevo sobre el commit anterior | Encendido | `despliegues-viejos` |
| Lista de permitidos del job token; push con job token | Activa; apagado | `job-token-lista`, `job-token-push` |
| Pipelines de forks en el proyecto padre (la interfaz advierte; la API y `/rebase`, no) | Apagado en un proyecto público o interno | `forks-en-el-padre` |
| Runners de instancia en un proyecto que despliega | Apagados, o el job de despliegue con etiqueta de un runner propio | `runners-de-instancia` (AVISO) |
| La ruta del archivo de CI en **otro proyecto** (`ruta@grupo/proyecto:ref`) | Opción para que la IA, Developer en el proyecto, no pueda tocar el job de producción | — (lo decide `DEC-010`) |

## Dónde vive la barrera de producción

Depende del plan: la tabla completa está en [planes-y-barreras.md](planes-y-barreras.md) («La barrera de
producción, según el plan»).
En corto: **en Free**, la rama o el tag protegido (sólo Maintainers llegan), con variables y runners protegidos y,
mejor, `id_tokens`; **en Premium**, el ambiente protegido con aprobación, donde quien dispara no aprueba y **aprobar
no arranca el job**: alguien lo corre después. En los dos, vale mientras la identidad de la IA no sea Maintainer. La
fila del ambiente (nombre exacto, quién aprueba, dónde) va en la ficha de ambientes de [[despliegue-continuo]].

## CI Lint, contra la instancia autorizada

- Valida el YAML **en la misma instancia a la que se empuja** (la de «Destino autorizado»), nunca en gitlab.com si
  el proyecto vive en otra: mandarlo afuera es publicar el pipeline (G4).
- Tres formas: `glab ci lint` (con `--dry-run --include-jobs`), la herramienta de lint del servidor MCP, o la API
  de CI Lint del proyecto. Desde la 19.6 un administrador puede exigir autenticación.
- **La respuesta es JSON**: `valid`, `errors`, `warnings`, `merged_yaml`, `includes` (de dónde vino cada archivo) y
  `jobs` (los jobs ya resueltos). Se guarda en `borrador/gitlab/<fecha>/` y se lee como dato.
- `gitlab-ci-local` corre los jobs en la máquina de la persona: sólo en repositorios propios, y no es parte del
  método.

## Lo que GitLab hace en el pipeline y no decide

En Free, SAST, detección de secretos y escaneo de contenedores dejan un **JSON**: GitLab no frena por ellos. El
veredicto lo da [[seguridad]]. La plantilla administrada de SAST trae sola la última versión de su rama: se mueve con
cada actualización de GitLab; un componente fijado por SHA no se mueve, pero en una instancia propia pide el espejo.
