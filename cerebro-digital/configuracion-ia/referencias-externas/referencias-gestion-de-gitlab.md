# Referencias externas — Gestión de GitLab

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca desde el
repositorio. Dice de dónde salió cada idea de la puerta [[gestion-de-gitlab]], de `bin/auditar-gitlab.py`, de la ficha
«GitLab del proyecto» y de la guía del MCP de GitLab. De la documentación se tomaron ideas y datos, no texto.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| Roles, subgrupos y visibilidad | https://docs.gitlab.com/user/permissions/ · `/user/group/subgroups/` · `/user/public_access/` | Doc. oficial | 2026-11-14 | Rol mínimo por acción; Planner; la membresía se hereda y no se baja en un subgrupo | `references/proyecto-y-grupo.md`, `references/planes-y-barreras.md` |
| Ramas y tags protegidos (y su API) | https://docs.gitlab.com/user/project/repository/branches/protected/ · `/api/protected_branches/` · `/user/project/protected_tags/` | Doc. oficial | 2026-11-14 | Qué es Free y qué Premium; niveles 0/30/40/60; force push; CODEOWNERS exigido en la regla | Chequeos `rama-defecto-protegida`, `push-directo`, `merge-a-rama-defecto`, `force-push`, `tags-protegidos`, `codeowners-exigido` |
| Aprobaciones de Merge Request (y su API) | https://docs.gitlab.com/user/project/merge_requests/approvals/ · `/api/merge_request_approvals/` | Doc. oficial | 2026-11-14 | En Free son opcionales; atributos `merge_requests_author_approval`, `merge_requests_disable_committers_approval`, `approvals_required` | `aprobaciones-requeridas`, `autor-no-aprueba`; `references/planes-y-barreras.md` |
| CODEOWNERS · push rules (y su API) | https://docs.gitlab.com/user/project/codeowners/ · `/user/project/repository/push_rules/` · `/api/project_push_rules/` | Doc. oficial | 2026-11-14 | Plan Premium; `prevent_secrets`; sin push rules la API del proyecto responde `null` y la del grupo 404; no cubren los commits por la interfaz o la API | `assets/CODEOWNERS.ejemplo`, `push-rules-secretos`, `push-rules-de-grupo` |
| Plantillas, acciones rápidas, cierre automático, opciones de push | https://docs.gitlab.com/user/project/description_templates/ · `/user/project/quick_actions/` · `/user/project/issues/managing_issues/` · `/topics/git/commit/` | Doc. oficial | 2026-11-14 | Las palabras de cierre y lo que alcanzan; las acciones rápidas se ejecutan al guardar; las opciones que saltean un control | `assets/merge-request-default.md`, modo `texto`, `cierre-automatico`; las opciones de push que saltean un control, `references/proyecto-y-grupo.md` |
| API de proyectos, grupos, ajustes y metadatos | https://docs.gitlab.com/api/projects/ · `/api/groups/` · `/api/settings/` · `/api/metadata/` · `/api/project_job_token_scopes/` · `/api/protected_environments/` | Doc. oficial | 2026-11-14 | Los nombres exactos de los atributos de la lista blanca y quién los ve (algunos sólo un Owner o un administrador) | `bin/auditar-gitlab.py` (`LISTA_BLANCA`) |
| GitLab CI/CD: YAML, `include`, componentes, inputs, variables, job token, forks, caché, ambientes, `id_tokens`, CI Lint | https://docs.gitlab.com/ci/yaml/ · `/ci/yaml/includes/` · `/ci/components/` · `/ci/inputs/` · `/ci/variables/` · `/ci/jobs/ci_job_token/` · `/ci/pipelines/merge_request_pipelines/` · `/ci/caching/` · `/ci/environments/` · `/ci/secrets/id_token_authentication/` · `/api/lint/` | Doc. oficial | 2026-11-14 | Lo propio de GitLab que el método general no cubre; los valores de `ci_pipeline_variables_minimum_override_role` | `references/ci-en-gitlab.md`; chequeos de CI del modo `proyecto` |
| Ambientes protegidos, aprobación y seguridad del despliegue; jobs manuales; congelamiento | https://docs.gitlab.com/ci/environments/protected_environments/ · `/ci/environments/deployment_approvals/` · `/ci/environments/deployment_safety/` · `/ci/jobs/job_control/` · `/user/project/releases/` | Doc. oficial | 2026-11-14 | La barrera de producción según el plan; aprobar no arranca el job; `when: manual` y `CI_DEPLOY_FREEZE` no son barrera | `references/planes-y-barreras.md`, `produccion-protegida` |
| GitLab Runner: seguridad, ejecutores, `config.toml`, registro, alcances, construir imágenes | https://docs.gitlab.com/runner/security/ · `/runner/executors/` · `/runner/configuration/advanced-configuration/` · `/ci/runners/new_creation_workflow/` · `/ci/runners/runners_scope/` · `/ci/docker/using_docker_build/` | Doc. oficial | 2026-11-14 | Los riesgos de `shell`, `privileged` y el socket de Docker; las listas permitidas; el token `glrt-` | `references/runners-e-instancia.md`, modo `runner` |
| Integración con servidores | https://docs.gitlab.com/ci/jobs/ssh_keys/ · `/user/project/deploy_keys/` · `/user/project/deploy_tokens/` · `/user/clusters/agent/` · `/user/clusters/agent/gitops/` · `/user/infrastructure/iac/` | Doc. oficial | 2026-11-14 | Los cinco caminos, cuál no recomienda GitLab para producción, el estado de OpenTofu que baja un Developer | `references/llegar-al-servidor.md` |
| `sshd(8)`, formato de `authorized_keys` | https://man.openbsd.org/sshd.8 | BSD (página de manual) | 2026-11-14 | `restrict`, `command=`, `from=` | `references/llegar-al-servidor.md` |
| Instancia propia: mantenimiento, camino de actualización, respaldo, tareas Rake, chequeos de salud, endurecimiento, 2FA, restricciones de registro | https://docs.gitlab.com/policy/maintenance/ · `/update/upgrade_paths/` · `/administration/backup_restore/backup_gitlab/` · `/administration/raketasks/maintenance/` · `/administration/monitoring/health_check/` · `/security/hardening/` · `/security/two_factor_authentication/` · `/administration/settings/sign_up_restrictions/` | Doc. oficial | 2026-11-14 | Ventana de mantenimiento; paradas obligatorias; el respaldo no incluye el archivo de secretos; qué chequeos leen y cuáles cambian; los ajustes que mide el modo `instancia` | `references/runners-e-instancia.md`, modo `instancia` |
| Avisos de parche crítico de GitLab 2025-2026 | https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-5-4-released/ (y los de 19.3.2, 19.0.9, 19.4.1, 19.4.2, 19.5.1 y 17.9.2) | Doc. oficial | 2026-11-14 | Por qué parchear rápido y que las barreras valen lo que vale el parche (CVE citados por número) | `references/runners-e-instancia.md`, `references/planes-y-barreras.md` |
| Catálogo KEV de CISA | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | CC0 1.0 | 2026-11-14 | El plazo de tres días de CVE-2026-97229 | `references/runners-e-instancia.md` |
| Tokens: panorama y prefijos, personales, de permisos finos, de proyecto, cuentas de servicio | https://docs.gitlab.com/security/tokens/ · `/user/profile/personal_access_tokens/` · `/auth/tokens/fine_grained_access_tokens/` · `/user/project/settings/project_access_tokens/` · `/user/profile/service_accounts/` | Doc. oficial | 2026-11-14 | La identidad de la IA en el token; un token clásico alcanza todo lo de la persona; la tabla de prefijos | `references/proyecto-y-grupo.md`, patrón `TOKEN_GITLAB` del modo `texto`, guía del MCP |
| Servidor MCP de GitLab y sus herramientas | https://docs.gitlab.com/user/model_context_protocol/mcp_server/ · `/user/model_context_protocol/mcp_server_tools/` | Doc. oficial | 2026-11-14 | Versión y plan, autenticación, cabeceras de herramientas, que no tiene modo de sólo lectura, `403 insufficient_scope` | `cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md` |
| `zereight/gitlab-mcp` (referencia de variables) y el registro de npm | https://github.com/zereight/gitlab-mcp · https://registry.npmjs.org/@zereight/mcp-gitlab | MIT | 2026-11-14 | Modos `readonly`, `modify` y `full` (el valor por defecto); el conjunto `api` saltea filtros; el `integrity` de la 2.3.22 | `cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md` |
| MCP en Claude Code | https://code.claude.com/docs/en/mcp | Doc. oficial | 2026-11-14 | `claude mcp add --transport http … --header` | `cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md` |
| Precios y planes | https://about.gitlab.com/pricing/ | — | 2026-11-14 | Free, Premium y Ultimate, iguales en GitLab.com y en una instancia propia | `references/planes-y-barreras.md` |

## Herramientas que se ejecutan (no se copian)

Ninguna la ejecuta `bin/auditar-gitlab.py`: el script sólo habla con la API v4 por `urllib`. Las corre una persona o
la sesión, por máquina; sin ellas, lo que depende de ellas es `SIN DATOS`.

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| Servidor MCP de GitLab (oficial) | Parte de GitLab (19.5 o más), en `/api/v4/mcp` | Servicio de la instancia | Leer Merge Requests, pipelines y work items | Va con la versión de GitLab; se anota la lista de herramientas habilitada |
| `@zereight/mcp-gitlab` | https://github.com/zereight/gitlab-mcp | MIT | Lo mismo, donde el oficial no está | Versión exacta **y** `integrity` de npm; instalación con lockfile y `npm ci` |
| `glab` (opcional) | https://gitlab.com/gitlab-org/cli | MIT | `glab ci lint` contra la instancia autorizada | Binario por máquina, versión fijada |
| `gitlabcis` (opcional) | https://gitlab.com/gitlab-org/govern/compliance/engineering/cis/gitlabcis | MIT | Segunda opinión contra el CIS GitLab Benchmark, en sólo lectura | `pip` con versión y hash |
| GitLab Runner | https://docs.gitlab.com/runner/ | ⚠ no verificada | Ejecutar los jobs | Lo instala y lo actualiza una persona, con la versión de GitLab |

## Lo que se miró y no se tomó

- **Un orquestador o un paquete de skills «de GitLab», una por tema**: duplicaría pipeline, despliegue, servidores
  y tablero. Va una puerta; el orquestador por función lo decidió el dueño y carga esa misma puerta.
- **`wshobson/agents`, skill `gitlab-ci-patterns`** (MIT): su primer ejemplo despliega a producción sin paso manual,
  usa un token estático y `docker:dind` sin advertir que pide privilegio. Sirvió como lista de lo que no hacer.
- **`akin-ozer/cc-devops-skills`, `gitlab-ci-generator` y `gitlab-ci-validator`** (Apache-2.0): como plan B manda el
  YAML al lint de gitlab.com sin avisar; usa `when: manual` como barrera.
- **`VoltAgent/awesome-claude-code-subagents`** (MIT): no trae nada de GitLab.
- **to-be-continuous** (licencia sin verificar): adoptarlo es depender de un marco entero.
- **Componentes de `gitlab.com/components`**: varios sin actividad reciente; en una instancia propia piden espejo.
  Se usan, si se usan, fijados por SHA.
- **Proveedor de OpenTofu/Terraform de GitLab** (MPL-2.0) y **GitLabForm** (MIT): configuración como código, fase 2.
  El proveedor no tiene soporte de GitLab; GitLabForm pide un token de administrador.
- **`gitlab-ci-local`** (MIT): ejecuta el pipeline en la máquina de la persona.
- **Skill oficial de `glab`**: experimental, enseña la herramienta y no trae barreras.
- **Claude Code en GitLab CI/CD** (beta) y **los flujos de GitLab Duo**: instalan con `curl … | bash`, corren con
  edición aceptada y no tienen paso humano.
- **El texto del CIS GitLab Benchmark**: se cita sólo por número de control; nunca «cumple CIS». Sus términos de uso no se pudieron leer (informe 07, «Lo que no pude verificar»).

## Lo que el informe no pudo verificar

- Permisos por rol: la tabla vigente dice **Owner** para variables, runners de proyecto y ambientes protegidos; las
  páginas de cada función, **Maintainer**.
- Si el MCP oficial con un token de permisos finos exige el permiso del recurso en cada herramienta, y cómo se le
  pasa ese token al endpoint.
- Si los tokens de permisos finos tienen un prefijo propio (la tabla de prefijos no lo dice).
- Qué alcanza exactamente el scope `read_api` de un token clásico (en particular, las variables).
- `GITLAB_TOOLS` del MCP de la comunidad: si reemplaza o se suma al conjunto por defecto.
- La fuente oficial legible por máquina de las versiones vigentes (por eso el script la recibe por archivo).
- Los atributos `enforce_ci_inbound_job_token_scope_enabled` (lista de permitidos del job token exigida en toda la
  instancia) y el de registro dinámico de clientes OAuth no figuran en la API de ajustes: el modo `instancia` no
  los mira.
- La licencia de GitLab Runner, de to-be-continuous y de cada componente de `gitlab.com/components`.
- GitLab Dedicated, runners en Windows y la instalación por Helm: no se investigaron.
