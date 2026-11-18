# Dependencias externas de skills — manifiesto

> **Para una auditoría:** este archivo contesta, solo, tres preguntas. Qué material externo
> usan las skills del proyecto, de dónde sale, y en qué condiciones. Para **leerlo** no hace
> falta clonar nada.

---

## Declaración

**Ninguna skill de terceros se copia ni se redistribuye en este repositorio, salvo las de licencia permisiva que se vendorizan con su licencia y su aviso, declaradas abajo en «Herramientas externas».** Todas las skills
de `cerebro-digital/configuracion-ia/skills/` están escritas acá, en español y con las reglas
del proyecto.

Si el proyecto decide **seguir** skills de un tercero (por ejemplo, las de un área de
Arquitectura corporativa), el mecanismo recomendado es el que usó el proyecto de origen de este
template: **no se copian, no se clonan, no se instalan**; se **leen del servidor en el momento de
usarlas** (por un MCP del repositorio que las publica) y se descartan. Lo que queda acá es
**un envoltorio** que las rutea, les aplica encima las correcciones del proyecto y declara quién
gana cuando difieren. Ese envoltorio se escribe como sección de la skill `desarrollo` y la tabla
de abajo se completa.

## Skills externas que el proyecto sigue

| Skill | Origen (repositorio) | Licencia | ¿Se usa? | Hash de árbol verificado | Corrido el |
|---|---|---|---|---|---|
| *(ninguna todavía)* | | | | | |

> **Cómo se llena.** Una fila por skill, con el **hash de árbol de la carpeta completa** de esa
> skill en el commit de referencia (`git rev-parse <commit>:<ruta>`), que es el ancla contra la
> que se detecta deriva. El Doctor lee esta tabla: toda ruta `skills/<nombre>/…` que una skill
> del proyecto cite y que **no esté en disco** se reporta como `SIN DATOS` sólo si la skill figura
> acá con su hash; si no figura, se reporta como referencia rota (HALLAZGO). Se exige el hash
> para que ninguna fila "decorativa" funcione como exención.

## Otro material externo

| Origen | Licencia | Qué se tomó |
|---|---|---|
| [`wshobson/commands`](https://github.com/wshobson/commands) | **MIT** (permite uso y modificación **con atribución**) | **Ideas y estructura, no texto**, para escribir el método de desarrollo en español y con nuestras reglas. Detalle archivo por archivo en `cerebro-digital/configuracion-ia/skills/desarrollo/references/referencias-externas.md` |
| [`DietrichGebert/ponytail`](https://github.com/DietrichGebert/ponytail) | **MIT** (permite uso y modificación **con atribución**) | **Ideas, no texto**: la escalera antes de escribir código, la revisión más allá del diff, la dimensión «lo que sobra», el hallazgo en cuatro partes y la marca `atajo:` (con `bin/atajos.py`). Qué se tomó y dónde nos quedamos con lo nuestro, en el mismo `referencias-externas.md` |

**No se instala ni se invoca nada de ahí.** Es bibliografía, no una dependencia de ejecución.

## Herramientas externas opcionales (por máquina, no del repositorio)

Una herramienta externa entra de una de dos formas: **vendorizada** como skill canónica (si su licencia lo permite, con su licencia y aviso; viaja en el clone) o **instalada por máquina** (nunca copiada a mano en los espejos `.claude/skills` ni `.agents/skills`: los regenera `bin/sync-skills`). No son parte del método: lo que producen es un entregable
de `borrador/` que se promueve con un «sí».

### Skills vendorizadas (copiadas al disco; no se editan)

El Doctor lee esta tabla: las rutas que estas skills citan hacia adentro de sí mismas y sus enlaces de doble corchete no se
reportan como rotos, porque el contenido es de terceros y lo que no viaja (columna «Qué no viaja») se quitó a
propósito. Lo que vigila que no queden viejas es el detector de deriva, con el hash de esta tabla.

| Skill | Origen | Versión | Hash de árbol | Qué no viaja |
|---|---|---|---|---|
| `archify` | [tt-a1i/archify](https://github.com/tt-a1i/archify) | 3.2 | `b1c638776f2bca56` | `examples/` (los JSON de muestra que su SKILL.md cita) |

| Herramienta | Origen | Licencia | Para qué | Cómo se instala | Qué NO hace |
|---|---|---|---|---|---|
| **Archify** | [tt-a1i/archify](https://github.com/tt-a1i/archify) | Apache-2.0 (LICENSE, NOTICE y THIRD_PARTY_NOTICES viajan con la skill) | Diagramas de arquitectura, flujo, secuencia, ERD y estados como HTML interactivo, con evidencia opcional `archivo:líneas`; para **presentar** lo que la radiografía y la lectura encontraron | **Vendorizada** en `cerebro-digital/configuracion-ia/skills/archify/` (versión 3.2, sin `examples/`, hash `b1c638776f2bca56`), así viaja en el clone y en los espejos como cualquier skill; requiere Node para renderizar. Para actualizarla: `npx -y skills add tt-a1i/archify -g -y --copy`, copiar `~/.agents/skills/archify` sin `examples/` sobre la carpeta, `bin/sync-skills`, y anotar acá versión y hash | No reemplaza el Mermaid de `radiografiar-codigo.py --mermaid`, que es lo que entra al Cerebro; su salida va a `borrador/` y se promueve con un «sí» |
| **tbls** / **SchemaCrawler** (opcionales) | [k1LoW/tbls](https://github.com/k1LoW/tbls) · [schemacrawler](https://www.github.com/schemacrawler/SchemaCrawler) | MIT · EPL/GPL/LGPL (sólo se ejecutan) | Documentar el esquema real de una base que no es SQLite (Postgres, MySQL, SQL Server) a Markdown y Mermaid, cuando `bin/esquema-base.py` no alcanza con el DDL exportado | Por máquina, con acceso de **sólo lectura**; nunca se vendorizan | No leen datos: sólo esquema. Lo que entra al Cerebro es el Markdown, de donde salga |
| **Google Stitch** | `stitch.withgoogle.com` | Servicio de Google, con sus términos; no se vendoriza | Diseño UX/UI: generar y pulir pantallas, exportar HTML/CSS y capturas | Por máquina: API key en `STITCH_API_KEY` y el servidor MCP remoto (`integracion-stitch-mcp/00-index.md`); sin MCP, modo manual pegando el prompt | No decide reglas (el Cerebro gana a la maqueta); la clave nunca en un archivo; sin PHI en prompts ni pantallas |

### Herramientas que ejecutan los scripts de las funciones (por máquina, opcionales)

Los scripts de arquitectura, despliegue, operación, seguridad y GitLab **no instalan nada y no bajan nada de
internet**. Una herramienta de esta tabla la corren sólo si está instalada en la máquina y se la piden; si falta, esa
parte del veredicto es `SIN DATOS`, nunca OK. Ninguna se vendoriza. **Se instalan por versión exacta y se verifica su
hash** (en marzo de 2026 publicaron versiones de Trivy comprometidas: un escáner es cadena de suministro como
cualquier otra). **La versión y el hash los fija cada proyecto** (en `DEC-007` y `DEC-009`) y se verifican al
instalar: el template no puede fijarlos por todos. Los scripts informan la versión que corrió y rechazan sólo la de
Trivy comprometida. En el CI, las acciones y las plantillas van por SHA. Qué idea se tomó de cada fuente, en
`cerebro-digital/configuracion-ia/referencias-externas/`.

| Herramienta | Origen | Licencia | La ejecuta | Lo que el script nunca le pasa |
|---|---|---|---|---|
| Terraform **u** OpenTofu | hashicorp/terraform · opentofu/opentofu | BSL 1.1 · MPL-2.0 | `auditar-iac.py` (`fmt -check`, `validate -json`) | `init`, `plan`, `apply`, `test` |
| TFLint | terraform-linters/tflint | MPL-2.0 | `auditar-iac.py` | `--fix`, `--init` |
| Checkov | bridgecrewio/checkov | Apache-2.0 | `auditar-iac.py` | Corre con `--skip-download` |
| Trivy | aquasecurity/trivy | Apache-2.0 | `auditar-iac.py` (`config`), `escanear-imagenes.py` | `--exit-code`; corre sin bajar su base. Nunca la 0.69.4 ni las imágenes 0.69.5 y 0.69.6 |
| hadolint | hadolint/hadolint | GPL-3.0 (sólo se ejecuta) | `auditar-iac.py` | — |
| kubeconform | yannh/kubeconform | Apache-2.0 | `auditar-iac.py` | Sin esquemas locales no corre (bajaría los de internet) |
| zizmor · actionlint · poutine | zizmorcore/zizmor · rhysd/actionlint · boostsecurityio/poutine | MIT · MIT · Apache-2.0 | `verificar-pipeline.py --profundo` (lee sus reportes) | `--fix`; `analyze_org`; un token |
| Opengrep **o** Semgrep CE | opengrep/opengrep · semgrep/semgrep | LGPL-2.1 | `escanear-seguridad.py` | Métricas encendidas; las reglas comunitarias no viajan en el template |
| Bandit | PyCQA/bandit | Apache-2.0 | `escanear-seguridad.py` | — |
| OSV-Scanner | google/osv-scanner | Apache-2.0 (los datos, según cada ecosistema: sin verificar) | `escanear-seguridad.py` | `fix`; la base la baja una persona, con fecha |
| Gitleaks | gitleaks/gitleaks | MIT | `escanear-seguridad.py` | Nada que imprima el secreto: va con `--redact` |
| ZAP (imagen) | zaproxy/zaproxy | Apache-2.0 | `escanear-ambiente.py`, sólo contra la URL del inventario | Una URL que no sea la de la fila; la imagen va por digest, sin bajarla (`--pull never`) |
| Grype | anchore/grype | Apache-2.0 | `escanear-imagenes.py` | `--fail-on`; corre sin actualizar su base |
| ssh-audit | jtesta/ssh-audit | MIT | `auditar-host.py`, desde afuera | `--dheat`, `--conn-rate-test`, `-T` |
| Lynis | CISOfy/lynis | GPL-3.0 (sólo se ejecuta) | **La corre una persona** en el servidor; `auditar-host.py` lee su reporte | — |
| Cliente OpenSSH y las herramientas base del servidor (`df`, `systemctl`, `timedatectl`, `journalctl`…) | Las del sistema | Las del sistema (sin relevar) | `salud-host.py` y el colector `operacion-de-servidores/assets/colector-salud.sh`, que una persona instala en el servidor | Comandos que no sean el colector: la identidad de lectura sólo puede correr ése |
| `@zereight/mcp-gitlab` | zereight/gitlab-mcp | MIT | El MCP de GitLab de cada persona (`integracion-gitlab-mcp/00-index.md`) | Versión `2.3.22` con su `integrity` del registro de npm; el servidor de escritura, nunca en modo `full` |

## Dónde está el resto

| Qué | Dónde |
|---|---|
| El método de desarrollo y sus guardarraíles | `cerebro-digital/configuracion-ia/skills/desarrollo/SKILL.md` |
| La bibliografía del método | `…/desarrollo/references/referencias-externas.md` |
| Las reglas y las barreras | `AGENTS.md` |
| De dónde salió cada idea de las funciones de arquitectura, despliegue, operación, seguridad y GitLab | `cerebro-digital/configuracion-ia/referencias-externas/00-index.md` |
