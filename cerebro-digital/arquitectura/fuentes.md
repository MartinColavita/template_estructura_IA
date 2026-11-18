---
id: fuentes-arquitectura
tipo: fuentes
estado: F-Draft
modulo: general
title: "Fuentes — arquitectura e infraestructura"
description: De dónde salió cada idea de la puerta arquitectura-e-infraestructura, de sus referencias y de sus scripts; bibliografía con licencia y fecha, nada se instala ni se copia.
tags: [arquitectura, infraestructura, fuentes, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# Referencias externas — arquitectura e infraestructura

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca. Dice de
dónde salió cada idea de la puerta `arquitectura-e-infraestructura`, de sus tres referencias, de la ficha
`arquitectura/infraestructura.md` y de los scripts `bin/auditar-iac.py` y `bin/resumir-plan.py`.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| Modelo C4 y su checklist de revisión | https://c4model.com/ · https://c4model.com/diagrams/checklist | CC BY 4.0 | 2026-11-14 | Los niveles (contexto, contenedores, despliegue; componentes sólo si hace falta) y el chequeo de cada diagrama: título, cada elemento con tipo, tecnología y descripción, cada relación con etiqueta | `disenar-arquitectura.md`; la vista de despliegue de la ficha |
| Mermaid, diagramas C4 | https://mermaid.js.org/syntax/c4.html | MIT | 2026-11-14 | La sintaxis `C4Context`, `C4Container`, `C4Deployment`, y sus huecos declarados (sin leyenda, etiquetas ni `Lay_*`): por eso cada diagrama va con su tabla de elementos | `disenar-arquitectura.md`; la ficha |
| MADR 4.0 | https://adr.github.io/madr/ · https://github.com/adr/madr | MIT OR CC0-1.0 | 2026-11-14 | Las partes de una decisión: impulsores, opciones consideradas con pros y contras, consecuencias y **cómo se confirma** | `disenar-arquitectura.md` §«Conducir una decisión técnica» |
| ADR (organización) | https://adr.github.io/ | — | 2026-11-14 | Decisión y requisito arquitectónicamente significativo; el registro de decisiones (acá, `decisiones.md`) | `disenar-arquitectura.md` (atributos de calidad como escenarios medibles) |
| architecture-decision-record (J. P. Henderson) | https://github.com/architecture-decision-record/architecture-decision-record | CC BY-NC-SA 4.0 (no comercial) | 2026-11-14 | **Sólo la idea** de preguntarse si una decisión merece registro; ningún texto | `disenar-arquitectura.md` §«¿Merece una DEC?» |
| wshobson/agents (`c4-architecture`) | https://github.com/wshobson/agents | MIT | 2026-11-14 | C4 de abajo hacia arriba: código, componentes, contenedores, contexto | `disenar-arquitectura.md` §«Antes de empezar» (desde la radiografía) |
| Guía de estilo de Terraform (HashiCorp) | https://developer.hashicorp.com/terraform/language/style | — | 2026-11-14 | Archivos con nombre fijo, una carpeta por ambiente con su estado (no *workspaces*), versiones fijadas, lock versionado, no versionar estado ni planes, variables con tipo y descripción, sin `provider` en los módulos | `armar-infraestructura.md`; reglas `TF-*` de `bin/auditar-iac.py` |
| `terraform test` | https://developer.hashicorp.com/terraform/language/tests | — | 2026-11-14 | `command = plan` con proveedores simulados no crea nada: es el rojo de la infraestructura | `armar-infraestructura.md` §«Cómo se prueba sin tocar la nube» |
| OpenTofu y su cifrado de estado | https://github.com/opentofu/opentofu · https://opentofu.org/docs/language/state/encryption/ | MPL-2.0 (CNCF) | 2026-11-14 | La alternativa libre a Terraform; cifrar estado y plan | `armar-infraestructura.md`; las filas de `DEC-007` |
| AWS Prescriptive Guidance — Terraform | https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/introduction.html | — | 2026-11-14 | Módulos por capacidad, reutilizables con `>=` y raíz con `~>`, git con `?ref=<SHA>`, bloques `moved`/`removed`/`import` en vez de comandos de estado, etiquetas por defecto, nombres | `armar-infraestructura.md`; `TF-MODULO-VERSION` |
| Google Cloud — buenas prácticas de Terraform | https://docs.cloud.google.com/docs/terraform/best-practices/general-style-structure | — | 2026-11-14 | Estructura de módulos, nombres, `prevent_destroy` en lo que guarda datos | `armar-infraestructura.md`; criterio de `auditar-infraestructura.md` |
| Bicep — buenas prácticas (Microsoft Learn) | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/best-practices | — | 2026-11-14 | `@secure()` en las salidas sensibles | `BICEP-OUTPUT-SEGURO` de `bin/auditar-iac.py` |
| Estado de Terraform en un almacenamiento remoto (Microsoft Learn) | https://learn.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage | — | 2026-11-14 | El estado es texto plano y puede tener secretos; backend con bloqueo y cifrado en reposo (idea general, sin dar por hecha una nube) | `armar-infraestructura.md` §«El estado»; la ficha |
| Conexión de servicio con identidad federada (Microsoft Learn) | https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure | — | 2026-11-14 | El pipeline entra sin secretos guardados, una identidad por ambiente, autorizada pipeline por pipeline (idea general) | `armar-infraestructura.md` §«Ambientes y secretos»; la ficha; `DEC-007` |
| Docker — buenas prácticas de build | https://docs.docker.com/build/building/best-practices/ | — | 2026-11-14 | Multi-etapa, base fijada por *digest*, `.dockerignore`, usuario no root | `armar-infraestructura.md`; `DOCKER-FROM`, `DOCKER-USER`, `DOCKER-IGNORE` |
| Compose — secretos | https://docs.docker.com/compose/how-tos/use-secrets/ | Apache-2.0 (Compose) | 2026-11-14 | Secretos montados en `/run/secrets/<nombre>`, preferidos a `environment:` | `armar-infraestructura.md`; el falso positivo `*_FILE` de `SECRETO-LITERAL` |
| Kubernetes — buenas prácticas de configuración | https://kubernetes.io/docs/concepts/configuration/overview/ | — | 2026-11-14 | Nada de `latest` ni de Pods sueltos, etiquetas recomendadas | `armar-infraestructura.md`; `IMAGEN-LATEST` |
| Kustomize | https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/ | Apache-2.0 | 2026-11-14 | Base y capas por ambiente; `secretGenerator` produce Base64, no cifra | `armar-infraestructura.md` (Kustomize no lo mira `auditar-iac.py`) |
| 12-factor — III. Configuración | https://12factor.net/config | CC BY 4.0 | 2026-11-14 | Configuración por variable de entorno; la prueba de publicar el código sin exponer credenciales; el anti-patrón de los «ambientes con nombre» | `armar-infraestructura.md` §«Ambientes y secretos» |
| SOPS | https://getsops.io/docs/ | MPL-2.0 | 2026-11-14 | Cifrar sólo el secreto que tiene que viajar en git; un `Secret` con `sops:` y valores `ENC[` está cifrado | `armar-infraestructura.md`; el falso positivo de `K8S-SECRET` |
| Vault · OpenBao | https://github.com/hashicorp/vault · https://github.com/openbao/openbao | BSL 1.1 · MPL-2.0 | 2026-11-14 | La alternativa libre del gestor de secretos | Las filas de `DEC-007` |
| External Secrets Operator | https://github.com/external-secrets/external-secrets | Apache-2.0 | 2026-11-14 | En Kubernetes, el secreto viene de un gestor externo | `armar-infraestructura.md` §«Contenedores» |
| akin-ozer/cc-devops-skills | https://github.com/akin-ozer/cc-devops-skills | Apache-2.0 | 2026-11-14 | Validadores que corren herramientas reales y dicen cuándo no pudieron | `--herramientas` de `bin/auditar-iac.py`, con `SIN DATOS` si falta una |
| hashicorp/agent-skills · Terraform MCP Server | https://github.com/hashicorp/agent-skills · https://github.com/hashicorp/terraform-mcp-server | MPL-2.0 | 2026-11-14 | Leer la documentación real del proveedor reduce los argumentos inventados | `armar-infraestructura.md` (un MCP de documentación, si está, como dato) |
| Aqua Security — ataque a Trivy | https://www.aquasec.com/blog/trivy-supply-chain-attack/ | — | 2026-11-14 | En marzo de 2026 reescribieron etiquetas de versión de acciones de Trivy: toda herramienta se fija por versión y hash, y las acciones por SHA | `auditar-infraestructura.md` §«Las herramientas externas»; la tabla de abajo |

### Formatos confirmados para leer reportes (no son ideas: son lo que los scripts leen)

| Formato | Origen | Consultado el | Lo usa |
|---|---|---|---|
| JSON de un plan (`show -json`): `format_version`, `resource_changes`, `actions`, `action_reason` | https://developer.hashicorp.com/terraform/internals/json-format · https://opentofu.org/docs/internals/json-format/ · `internal/command/jsonplan/plan.go` de cada proyecto | 2026-11-14 | `bin/resumir-plan.py` |
| JSON de `validate -json` | https://developer.hashicorp.com/terraform/cli/commands/validate | 2026-11-14 | `bin/auditar-iac.py` |
| JSON de TFLint, hadolint, Checkov, Trivy y kubeconform | El código de cada herramienta (`formatter/json.go`, `Formatter/Json.hs` y `Rule.hs`, `report.py` y `runner_registry.py`, `pkg/types/`, `pkg/output/json.go`) y las referencias de línea de comandos de Trivy y Checkov | 2026-11-14 y 2026-11-17 | `bin/auditar-iac.py` |

## Herramientas que se ejecutan (no se copian)

Ninguna viene con el template. `bin/auditar-iac.py` las corre **sólo si están instaladas y se piden**; si no, esa
parte es `SIN DATOS`. Nunca les pasa una opción que cambie algo.

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| Terraform **u** OpenTofu (la que fije `DEC-007`) | https://github.com/hashicorp/terraform · https://github.com/opentofu/opentofu | BSL 1.1 · MPL-2.0 | `fmt -check` y `validate -json`; el plan lo corre el pipeline | `required_version` en el código; el binario, por versión exacta y su checksum publicado |
| TFLint | https://github.com/terraform-linters/tflint | MPL-2.0 | Linter de Terraform | Versión exacta y checksum; sus complementos los instala una persona |
| Checkov | https://github.com/bridgecrewio/checkov | Apache-2.0 | Configuración insegura en infraestructura como código | Versión exacta, instalada con hash |
| Trivy | https://github.com/aquasecurity/trivy | Apache-2.0 | Configuración insegura (`trivy config`) | Versión exacta y checksum, **nunca una de las del incidente de marzo de 2026**; en el pipeline, la acción por SHA |
| hadolint | https://github.com/hadolint/hadolint | GPL-3.0 (sólo se ejecuta) | Linter de Dockerfile | Versión exacta y checksum |
| kubeconform | https://github.com/yannh/kubeconform | Apache-2.0 | Manifiestos de Kubernetes contra esquemas **locales** | Versión exacta y checksum; los esquemas, en una carpeta fijada |

## Lo que se miró y no se tomó

- **arc42** (CC BY-SA 4.0): obliga a redistribuir lo derivado con la misma licencia. La idea de sus 12 secciones
  queda para la fase 2 (la cobertura de `vista-arquitectura.py`); no se copió texto.
- **Structurizr**: se reorganizó en 2026 (dos repositorios archivados) y el servidor con binarios pide licencia.
  **LikeC4, D2, PlantUML, C4-PlantUML y Diagrams**: piden Node, Java, Graphviz o un binario. El Mermaid no pide nada.
- **adr-tools** y **log4brains**: estancados desde 2024. El registro de decisiones ya es `decisiones.md`.
- **Instalar o vendorizar colecciones** (`wshobson/agents`, `VoltAgent/awesome-claude-code-subagents`,
  `antonbabenko/terraform-skill`, `hashicorp/agent-skills`): un segundo método en inglés con reglas propias (G2,
  G3). Si el equipo quiere seguir alguna, va por G5, leída del servidor y con hash.
- **`microsoft/azure-skills`**: están hechas para que el agente despliegue; chocan con el GATE de INFRAESTRUCTURA.
- **Skills de registros públicos**: un estudio de USENIX Security 2026 (https://arxiv.org/abs/2602.06547) confirmó
  157 maliciosas entre 98.380; el de Snyk (ToxicSkills) apunta igual, con los números de un proveedor comercial.
- **Una nube por defecto** (Azure Verified Modules, Azure Landing Zones, las tareas de Terraform para Azure
  Pipelines): el informe se inclinaba por Azure porque el proyecto de origen la usa. El template es neutral: si
  `DEC-007` elige esa nube, se leen como guía de esa nube. Las tareas de Azure Pipelines son, además, de DevLabs, sin
  soporte del fabricante.
- **Terragrunt**: una herramienta más para un problema (muchos estados y cuentas) que una aplicación chica no tiene.
- **Kubernetes por defecto, Compose en producción, *workspaces* para separar ambientes**: ver
  `armar-infraestructura.md`.
- **terraform-docs, pre-commit-terraform e Infracost**: útiles, pero no los corre ningún script de la fase 1.
- **El libro «Terraform Best Practices»** (Apache-2.0) y las **buenas prácticas de Helm** (Apache-2.0): confirman lo
  de las guías oficiales; no agregaron una regla. En la fase 1 no se miran charts de Helm.

## Lo que el informe no pudo verificar

- Si la wiki de Azure DevOps (y otros visores) renderiza el C4 de Mermaid: hasta probarlo, `SIN DATOS`.
- El formato del JSON de `az deployment … what-if` (Bicep): por eso `bin/resumir-plan.py` no lo lee.
- Si Infracost pide cuenta o clave; la licencia de age; la última actividad de D2.
- La licencia de cada skill de `anthropics/skills`; `microsoft/skills` y `MicrosoftDocs/Agent-Skills` no se
  revisaron a fondo.
- **De esta construcción:** ninguna herramienta externa se ejecutó (no hay ninguna instalada en la máquina donde se
  escribió): los lectores de reportes se probaron con reportes plantados, armados según el formato documentado. La
  documentación de Checkov no dice si manda datos sin clave de la plataforma (el script le pasa `--skip-download`);
  la de Trivy no dice qué pasa con `--skip-check-update` sin chequeos en el cache.

_Últ. modif.: 2026-11-18 — @equipo — mudada a la sección (M-062)_
