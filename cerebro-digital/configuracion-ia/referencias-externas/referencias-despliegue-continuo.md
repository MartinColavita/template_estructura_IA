# Referencias externas — CI/CD y despliegue continuo

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca desde el
repositorio. Dice de dónde salió cada idea de la puerta [[despliegue-continuo]], de sus tres referencias y de
`bin/verificar-pipeline.py`, `bin/gate-despliegue.py` y `bin/clasificar-migraciones.py`. Sale del informe de
investigación de M-048; las páginas de documentación se leyeron, no se copió texto.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| GitHub, «Secure use reference» y su página de inyección de scripts | https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions | Doc. oficial | 2026-11-14 | Token con permisos mínimos y escritura sólo en el job; fijar por SHA completo verificado en el repositorio de la acción (no en un fork); `pull_request_target` y `workflow_run` con checkout del PR; la lista de terminaciones de los datos del evento que controla un tercero | P1, P3 y P4 de `verificar-pipeline.py`; `armar-pipeline.md`; `cadena-de-suministro.md`; el fijado de `.github/workflows/verificar.yml` (los SHA se confirmaron en la API pública de cada acción) |
| GitHub, política que exige el fijado por SHA | https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/ | Doc. oficial | 2026-11-14 | Que la plataforma puede exigir el fijado | `cadena-de-suministro.md` |
| GitHub, lockfiles de workflows (anuncio y concepto) | https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/ · https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles | Doc. oficial | 2026-11-14 | `actions.lock` cubre las dependencias transitivas pero no `jobs.<id>.uses`; sus dos secciones (`workflows`, `dependencies`) | P2 de `verificar-pipeline.py` (`leer_lock`); `cadena-de-suministro.md` |
| GitHub, OIDC (general y contra Azure) | https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect · https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure | Doc. oficial | 2026-11-14 | Identidad federada en lugar de secretos de larga vida | P5; `armar-pipeline.md` |
| GitHub, ambientes y su disponibilidad por plan | https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment · https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | Doc. oficial | 2026-11-14 | Revisores, «no aprobar la propia corrida», secretos por ambiente; en privados, los revisores no están en Free, Pro ni Team | `armar-pipeline.md` (dónde vive la aprobación); `desplegar.md` (modo solo y equipo) |
| GitHub, atestaciones de artefactos | https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds | Doc. oficial | 2026-11-14 | Atestación de la plataforma, sus permisos y `gh attestation verify` | `cadena-de-suministro.md` |
| GitHub, Dependabot | https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates | Doc. oficial | 2026-11-14 | Actualiza acciones y workflows reutilizables, con espera antes de proponer | `cadena-de-suministro.md` |
| GitLab, componentes de CI/CD | https://docs.gitlab.com/ci/components/ | Doc. oficial | 2026-11-14 | Componentes por SHA o versión; evitar `~latest` | P2 (GitLab) |
| GitLab, `id_tokens` | https://docs.gitlab.com/ci/secrets/id_token_authentication/ | Doc. oficial | 2026-11-14 | Identidad federada con su `aud`; ramas y ambientes protegidos en los claims | `armar-pipeline.md` |
| GitLab, ambientes protegidos y aprobaciones | https://docs.gitlab.com/ci/environments/protected_environments/ · https://docs.gitlab.com/ci/environments/deployment_approvals/ | Doc. oficial | 2026-11-14 | Son de los planes pagos; quien dispara no aprueba; aprobar no arranca el job | `armar-pipeline.md` |
| GitLab, seguridad del pipeline | https://docs.gitlab.com/ci/pipeline_security/ | Doc. oficial | 2026-11-14 | Imágenes por digest, `include` fijado, variables protegidas | P2 y P5 (GitLab) |
| GitLab, referencia del YAML | https://docs.gitlab.com/ci/yaml/ | Doc. oficial | 2026-11-14 | `resource_group`, `environment:deployment_tier`, `rules` | P6 y P8 (GitLab) |
| GitLab, migraciones sin corte | https://docs.gitlab.com/development/database/avoiding_downtime_in_migrations/ | Doc. oficial | 2026-11-14 | Borrar una columna son tres versiones; `NOT NULL` después del código | `clasificar-migraciones.py`; `desplegar.md` |
| GitLab, API de CI Lint (**no está en el informe**: se leyó para confirmar el formato que pidió `gestion-de-gitlab`) | https://docs.gitlab.com/api/lint/ | Doc. oficial | 2026-11-17 | La forma de la respuesta: `valid` (a veces como texto), `errors`, `includes` con `type`, `location` y `extra` | P10 de `verificar-pipeline.py` |
| Azure Pipelines, aprobaciones y chequeos | https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals | Doc. oficial | 2026-11-14 | No viven en el YAML y quien edita el YAML no los toca | `armar-pipeline.md`; `desplegar.md` |
| Azure Pipelines, ambientes | https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments | Doc. oficial | 2026-11-14 | Un ambiente mal escrito se crea solo desde el editor web | P6 (el nombre contra la ficha) |
| Azure Pipelines, jobs de despliegue | https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs | Doc. oficial | 2026-11-14 | `deployment` con `environment`; `runOnce`, `rolling`, `canary`; el gancho de falla | P6 (Azure); `desplegar.md` (estrategias) |
| Azure DevOps, identidad federada en las conexiones de servicio | https://learn.microsoft.com/en-us/azure/devops/pipelines/release/configure-workload-identity | Doc. oficial | 2026-11-14 | Conexión de servicio sin secretos | P5; `armar-pipeline.md` |
| Martin Fowler: azul y verde, canario, cambio en paralelo, interruptores | https://martinfowler.com/bliki/BlueGreenDeployment.html · https://martinfowler.com/bliki/CanaryRelease.html · https://martinfowler.com/bliki/ParallelChange.html · https://martinfowler.com/articles/feature-toggles.html | — | 2026-11-14 | Las estrategias; la base tiene que soportar las dos versiones; el interruptor con fecha de retiro | `desplegar.md`; `clasificar-migraciones.py` |
| Argo Rollouts | https://argoproj.github.io/argo-rollouts/ | Apache-2.0 | 2026-11-14 | La vuelta atrás automática está bien adentro de un despliegue aprobado y medido | `desplegar.md` |
| Principios GitOps, Argo CD, Flux | https://opengitops.dev/ · https://argo-cd.readthedocs.io/en/stable/ · https://fluxcd.io/flux/ | Apache-2.0 (Argo CD, Flux) | 2026-11-14 | GitOps conviene sólo con Kubernetes; mergear al repositorio de configuración es desplegar | `desplegar.md` |
| SLSA v1.2 y sus niveles | https://slsa.dev/spec/v1.2/ · https://slsa.dev/spec/v1.1/levels | — | 2026-11-14 | Pista de build: L2 como objetivo de arranque, L3 más adelante | `cadena-de-suministro.md` |
| Syft y CycloneDX | https://github.com/anchore/syft · https://cyclonedx.org/ | Apache-2.0 · estándar abierto | 2026-11-14 | Una herramienta alcanza para el SBOM; CycloneDX es estándar | `cadena-de-suministro.md` |
| cosign | https://docs.sigstore.dev/cosign/signing/overview/ | Apache-2.0 | 2026-11-14 | Firma sin claves, con la identidad federada del pipeline | `cadena-de-suministro.md` |
| Renovate | https://docs.renovatebot.com/ | AGPL-3.0 | 2026-11-14 | Actualiza en Azure Repos y GitLab, donde Dependabot no es nativo | `cadena-de-suministro.md` |
| Alerta de CISA por `tj-actions/changed-files` y `reviewdog` | https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066-and-reviewdogaction | — | 2026-11-14 | Una acción por etiqueta expuso secretos; revisar qué versión corrió y rotar todo | `cadena-de-suministro.md` («Por qué: lo que pasó») |
| zizmor (`docs/usage.md`) | https://github.com/zizmorcore/zizmor | MIT | 2026-11-14 | Su reporte JSON (severidad, ubicación con fila desde cero), el modo sin red y que `--fix` modifica archivos | `--profundo` de `verificar-pipeline.py` (lee el reporte; `--fix` está en la lista negra) |
| actionlint (`docs/usage.md`, `error.go`) | https://github.com/rhysd/actionlint | MIT | 2026-11-14 | Los campos del JSON (`filepath`, `line`, `kind`, `message`) | `--profundo` |
| poutine (`README.md`, `results/results.go`, `opa/rego/poutine/format/json.rego`) | https://github.com/boostsecurityio/poutine | Apache-2.0 | 2026-11-14 | Cubre las tres plataformas; su JSON (`findings` con `rule_id` y `meta`, `rules` con `level`); que consulta versiones nuevas una vez por día salvo `--disable-version-check` | `--profundo` |
| pinact | https://github.com/suzuki-shunsuke/pinact | MIT | 2026-11-14 | Fijar por SHA con la versión en un comentario | `cadena-de-suministro.md` |
| Agentes publicados de CI/CD: `wshobson/agents`, `VoltAgent/awesome-claude-code-subagents`, `github/awesome-copilot` | https://github.com/wshobson/agents · https://github.com/VoltAgent/awesome-claude-code-subagents · https://github.com/github/awesome-copilot | MIT | 2026-11-14 | Sólo como índice de temas (SLSA, SBOM, firma, GitOps, migraciones aditivas primero); nada de su texto ni de sus agentes | La lista de temas de las tres referencias |

## Herramientas que se ejecutan (no se copian)

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| **zizmor** | https://github.com/zizmorcore/zizmor | MIT | Análisis profundo de GitHub Actions, con `verificar-pipeline.py --profundo`, sin red (`--offline`) | Binario por máquina en la versión que declare `DEPENDENCIAS-EXTERNAS.md`; en un pipeline, por SHA |
| **actionlint** | https://github.com/rhysd/actionlint | MIT | Sintaxis y expresiones de GitHub Actions, con `--profundo` | Igual |
| **poutine** | https://github.com/boostsecurityio/poutine | Apache-2.0 | Las tres plataformas, con `--profundo` (`analyze_local`, sin la consulta de versión) | Igual |
| **pinact** o la extensión `gh actions-lock` | https://github.com/suzuki-shunsuke/pinact | MIT · GitHub | Fijar acciones por SHA o generar `actions.lock` (por máquina, a pedido de una persona) | Versión fijada por máquina |
| **Syft** | https://github.com/anchore/syft | Apache-2.0 | SBOM en el pipeline de la aplicación | Paso del pipeline, por SHA o digest |
| **cosign** o la atestación de GitHub | https://github.com/sigstore/cosign | Apache-2.0 · GitHub | Firmar o atestar el artefacto; verificarlo antes de promover | Paso del pipeline, por SHA o digest |
| **Renovate** o **Dependabot** | https://github.com/renovatebot/renovate | AGPL-3.0 (se ejecuta, no se modifica) · GitHub | Actualizaciones con espera, una sola de las dos | Configuración en el repositorio de la aplicación |

## Lo que se miró y no se tomó

- **Los agentes de `wshobson/agents` y `VoltAgent`, tal cual**: despliegan y vuelven atrás sin persona, fijan por
  etiqueta, usan claves estáticas y traen metas DORA como lista de control.
- **La barrera de producción en el YAML** (`when: manual`, un disparador a mano): la IA edita el YAML.
- **checkov para Azure Pipelines**: su línea de comandos no lo lista (la licencia de checkov es Apache-2.0).
- **OpenSSF Scorecard** como auditor de GitLab o de Azure: casi todos sus chequeos de pipeline son de GitHub.
- **harden-runner**: opcional; no suma a la barrera.
- **Claude Code adentro del job de despliegue**: sirve, a lo sumo, para revisar.
- **La extensión de terceros de Dependabot para Azure DevOps**: con reservas; licencia no verificada.
- **OpenFeature**: sólo si el proyecto usa interruptores; no se construyó nada para eso.
- **Las métricas DORA** (guía de DORA, API de despliegues, métricas de GitLab) quedan para la fase 2. El chequeo de `Fixes AB#` en los
  commits ya está: `bin/auditar-diff.py`, con el criterio de `bin/auditoria/cierre.py`.
- **La nota de prensa sobre los lockfiles** (InfoQ): fuente secundaria; se usó la documentación oficial.

## Lo que el informe no pudo verificar

- Si los lockfiles de workflows ya están disponibles en general: lo dice una fuente secundaria.
- Las páginas de identidad federada de Azure DevOps se vieron en una búsqueda, no completas.
- La licencia de la extensión de Dependabot para Azure.
- La guía de Claude Code en GitLab CI/CD se vio en una búsqueda.
- Azul y verde con los «slots» de una plataforma como servicio no se verificó.
- En el lockfile, la documentación muestra el commit como un marcador (`sha1-...`): el script acepta el SHA con o sin
  ese prefijo.
