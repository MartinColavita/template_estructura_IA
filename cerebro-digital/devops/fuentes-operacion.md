---
id: fuentes-devops-operacion
tipo: fuentes
estado: F-Draft
modulo: general
title: "Fuentes — operación y mantenimiento de servidores"
description: De dónde salió cada idea de la puerta operacion-de-servidores, de su colector, de sus scripts y de las plantillas del pilar operacion; bibliografía con licencia y fecha.
tags: [devops, operacion, servidores, fuentes, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# Referencias externas — operación y mantenimiento de servidores

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca desde el
repositorio. Dice de dónde salió cada idea de la skill `operacion-de-servidores`, de su colector, de sus scripts y de
las plantillas del pilar `operacion/`. Todo está redactado de nuevo, en español; de los libros de Google (sin obras
derivadas) se tomaron ideas, nunca texto. Las rutas `skills/…` son relativas a `cerebro-digital/configuracion-ia/`.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| Google, *Site Reliability Engineering*: introducción | https://sre.google/sre-book/introduction/ | CC BY-NC-ND 4.0: no se adapta texto | 2026-11-14 | Un procedimiento escrito acelera mucho la recuperación frente a improvisar; la mayoría de las caídas vienen de cambios en un sistema vivo | `skills/operacion-de-servidores/references/runbook.md`; «¿qué cambió?» y `operacion/cambios.md` |
| Google, *SRE*: «Monitoring Distributed Systems» | https://sre.google/sre-book/monitoring-distributed-systems/ | CC BY-NC-ND 4.0 | 2026-11-14 | Síntoma antes que causa | `skills/operacion-de-servidores/references/diagnosticar.md` (el detalle de las señales queda en `observabilidad.md` de `desarrollo`) |
| Google, *SRE*: «Managing Incidents» | https://sre.google/sre-book/managing-incidents/ | CC BY-NC-ND 4.0 | 2026-11-14 | Los cuatro papeles (sólo «operación» toca el sistema), el documento vivo, el traspaso explícito y declarar temprano, con sus tres preguntas | `skills/operacion-de-servidores/references/incidente.md` |
| Google, *SRE*: «Postmortem Culture» y el postmortem de ejemplo | https://sre.google/sre-book/postmortem-culture/ · https://sre.google/sre-book/example-postmortem/ | CC BY-NC-ND 4.0 | 2026-11-14 | Sin culpa; disparadores definidos antes; las partes del postmortem (resumen, impacto, detección, acciones, lo que salió bien, mal y por suerte, línea de tiempo); nada que identifique a un usuario | `skills/operacion-de-servidores/references/incidente.md`; `operacion/incidentes/plantilla-incidente.md` |
| Google, *Building Secure & Reliable Systems*, cap. 5 | https://google.github.io/building-secure-and-reliable-systems/raw/ch05.html | CC BY 4.0 (LICENSE del repositorio) | 2026-11-14 | Interfaces chicas mejor que una sesión SSH; acceso temporal; emergencia vigilada; auditoría | `skills/operacion-de-servidores/references/acceso.md`; el colector como única «interfaz» de lectura |
| PagerDuty, guía de postmortems | https://github.com/PagerDuty/postmortem-docs | Apache-2.0 | 2026-11-14 | Factores que contribuyeron y no una causa raíz; la acción de una persona nunca es causa; la línea de tiempo empieza antes, con hechos y sin juicio | `skills/operacion-de-servidores/references/incidente.md`; `plantilla-incidente.md` |
| Prometheus, reglas de alerta | https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ | Apache-2.0 | 2026-11-14 | Las anotaciones de una alerta enlazan a su runbook | `skills/operacion-de-servidores/references/runbook.md`; el campo `alertas` de `plantilla-runbook.md` |
| `prometheus/node_exporter` | https://github.com/prometheus/node_exporter | Apache-2.0 | 2026-11-14 | Qué conviene medir de un host: disco, inodos, memoria, carga, unidades de systemd y reloj | Las secciones de `skills/operacion-de-servidores/assets/colector-salud.sh` |
| `samber/awesome-prometheus-alerts` (host y hardware) | https://samber.github.io/awesome-prometheus-alerts/rules/basic-resource-monitoring/host-and-hardware/ | Reglas CC BY 4.0, sitio MIT | 2026-11-14 | Disco casi lleno, servicio de systemd caído y reloj desfasado como señales del host. No se copió ninguna regla | Los chequeos y los umbrales por defecto de `bin/salud-host.py` |
| Debian, *UnattendedUpgrades*, y Ubuntu, actualizaciones automáticas | https://wiki.debian.org/UnattendedUpgrades · https://ubuntu.com/server/docs/how-to/software/automatic-updates/ | Wiki de Debian · documentación de Canonical | 2026-11-14 | Automático, sólo seguridad; sin reinicio automático por defecto | `skills/operacion-de-servidores/references/mantenimiento.md` (parches) |
| `dnf-automatic` | https://dnf.readthedocs.io/en/stable/automatic.html | ⚠ licencia de dnf sin verificar | 2026-11-14 | `dnf-automatic-install.timer` instala aunque la configuración diga otra cosa | `skills/operacion-de-servidores/references/mantenimiento.md` (parches) |
| CISA, *Data Backup Options* y guía *#StopRansomware* | https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf · https://www.cisa.gov/stopransomware/ransomware-guide | Publicaciones del gobierno de EE.UU. | 2026-11-14 | La regla 3-2-1; respaldos fuera de línea y cifrados; probar la restauración | `skills/operacion-de-servidores/references/mantenimiento.md` (respaldos) |
| restic `check` y borg `check` | https://restic.readthedocs.io/en/stable/045_working_with_repos.html · https://borgbackup.readthedocs.io/en/stable/usage/check.html | BSD-2-Clause · BSD-3-Clause | 2026-11-14 | Chequear por partes (`--read-data-subset`); `--repair` puede perder datos | `skills/operacion-de-servidores/references/mantenimiento.md`: chequear es N0, reparar o podar es N3 |
| `logrotate` | https://github.com/logrotate/logrotate | GPL-2.0 | 2026-11-14 | `-d` simula sin cambiar nada | `skills/operacion-de-servidores/references/mantenimiento.md` (logs) |
| `journald.conf` | https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html | Documentación de systemd | 2026-11-14 | El tope de disco del journal (`SystemMaxUse`) es su retención | `skills/operacion-de-servidores/references/mantenimiento.md` (disco) |
| Let's Encrypt: fin de los avisos por mail, y de 90 a 45 días | https://letsencrypt.org/2025/01/22/ending-expiration-emails/ · https://letsencrypt.org/2025/12/02/from-90-to-45/ | Blog oficial | 2026-11-14 | Sin avisos por mail desde 2025; vida de 64 días en 2027 y 45 en 2028; renovar a unos dos tercios; renovar a mano no se recomienda | `bin/vigencia-certificados.py` (fracción de vida); `skills/operacion-de-servidores/references/mantenimiento.md` |
| Ansible, modo de chequeo | https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html | GPL-3.0 (repositorio) | 2026-11-14 | `--check` es sólo una simulación; `--diff` puede mostrar un secreto (`diff: false`) | `skills/operacion-de-servidores/references/mantenimiento.md` |
| OWASP LLM06:2025 *Excessive Agency* | https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ | CC BY-SA 4.0 | 2026-11-14 | Poca funcionalidad, pocos permisos, nada de shell abierta, aprobación humana para lo de alto impacto, autorización chequeada en el sistema de destino | `skills/operacion-de-servidores/references/acceso.md`; las barreras de la puerta |
| Documentación de Claude Code: permisos | https://code.claude.com/docs/en/permissions | Documentación oficial | 2026-11-14 | Las reglas las aplica el programa, no el modelo; una regla sobre comandos no es una frontera de seguridad | `skills/operacion-de-servidores/references/acceso.md` («la barrera vive en el servidor») |
| OpenBSD `sshd(8)`, formato de `authorized_keys` | https://man.openbsd.org/sshd.8 | ISC/BSD | 2026-11-14 | `command=`, `restrict`, `from=`, `expiry-time=`; el comando que pide el cliente se ignora | `skills/operacion-de-servidores/references/acceso.md`; el encabezado del colector |
| OpenBSD `ssh-keygen(1)`, certificados | https://man.openbsd.org/ssh-keygen.1 | ISC/BSD | 2026-11-14 | Certificados firmados por una autoridad, con principal, validez corta (`-V`) y origen fijo; sin `-V` valen para siempre | `skills/operacion-de-servidores/references/acceso.md` (identidad de cambio) |
| `sudoers(5)` | https://www.sudo.ws/docs/man/sudoers.man/ | ISC | 2026-11-14 | Registro de entrada y salida (`log_input`, `log_output`); cuidado con los comodines en los argumentos | `skills/operacion-de-servidores/references/acceso.md` |
| `wshobson/agents` (`plugins/incident-response`) | https://github.com/wshobson/agents | MIT | 2026-11-14 | El runbook «para las tres de la mañana»; por paso, precondición, salida esperada y «si esto falla»; simulación antes de lo destructivo; vuelta atrás siempre | `skills/operacion-de-servidores/references/runbook.md`; `plantilla-runbook.md` |
| `anthropics/knowledge-work-plugins`, skill `incident-response` | https://github.com/anthropics/knowledge-work-plugins | Apache-2.0 | 2026-11-14 | El aviso en cuatro partes (qué pasa, a quién afecta, qué hacemos, cuándo hay novedades); escribir mientras pasa | `skills/operacion-de-servidores/references/incidente.md` |
| `k8sgpt-ai/k8sgpt` | https://github.com/k8sgpt-ai/k8sgpt | Apache-2.0 | 2026-11-14 | Analizadores deterministas primero, y el modelo explica después | «Primero el script, después el criterio» en `skills/operacion-de-servidores/references/diagnosticar.md` |
| `grafana/mcp-grafana` | https://github.com/grafana/mcp-grafana | Apache-2.0 | 2026-11-14 | Se puede conectar en sólo lectura (`--disable-write`) | `skills/operacion-de-servidores/references/acceso.md`; los logs de `skills/operacion-de-servidores/references/diagnosticar.md` |

## Herramientas que se ejecutan (no se copian)

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| Cliente OpenSSH (`ssh`) | https://www.openssh.com/ | BSD (⚠ no relevada en el informe) | `bin/salud-host.py --ssh`: entra con la identidad de lectura, sin mandar comandos, sin terminal y sin preguntar | La de la máquina de quien opera; sólo usa opciones de larga data (`BatchMode`, `StrictHostKeyChecking`, `ConnectTimeout`) |
| `df`, `date`, `timeout`, `uname`, `getconf`, `awk`, `sed`, `sort` | El sistema operativo del servidor (GNU coreutils y afines) | GPL (⚠ no relevada en el informe) | Las cifras del colector: disco, inodos, fecha, núcleo, CPU | La del servidor; lo que falta, el colector lo informa como `sin_dato` |
| `systemctl`, `timedatectl`, `journalctl` | systemd, en el servidor | LGPL (⚠ no relevada en el informe) | Unidades caídas, reloj sincronizado y tamaño del journal, en el colector | La del servidor; `timedatectl show` existe desde systemd 239, y si no, se lee su estado en texto |
| `needs-restarting -r` (opcional) | `dnf-plugins-core`, en servidores de la familia RHEL | ⚠ no relevada en el informe | Si hace falta reiniciar, en el colector | La del servidor; si no está, el colector usa otro método o informa `sin_dato` |

Ninguna se instala desde el repositorio: el colector lo copia una persona al servidor, y usa lo que el servidor ya
trae.

## Documentación consultada sólo para confirmar un formato

No aporta ideas: se leyó para que el código lea bien lo que devuelven estas herramientas.

| Qué se confirmó | Origen | Consultado el |
|---|---|---|
| El diccionario de `getpeercert()`, `cert_time_to_seconds()` y `SSLCertVerificationError` | https://docs.python.org/3/library/ssl.html | 2026-11-17 |
| `systemctl is-system-running` (sus estados) y `list-units --state=failed --plain` | https://www.freedesktop.org/software/systemd/man/latest/systemctl.html | 2026-11-17 |
| `timedatectl show -p … --value` (desde la versión 239) y la línea «System clock synchronized» | https://www.freedesktop.org/software/systemd/man/latest/timedatectl.html | 2026-11-17 |
| `needs-restarting -r`: sale 1 si hace falta reiniciar, 0 si no | https://dnf-plugins-core.readthedocs.io/en/latest/needs_restarting.html | 2026-11-17 |

## Lo que se miró y no se tomó

- **Copiar texto de los libros de Google**: su licencia no permite obras derivadas. Se tomaron ideas.
- **La guía de respuesta a incidentes de PagerDuty** (`PagerDuty/incident-response-docs`, Apache-2.0): la escala de
  severidad ya está en `incidentes.md` de `desarrollo`, y la guardia es una decisión de organización, no de método. Su
  sitio nuevo dice «All rights reserved»: si algún día se toma algo, es del repositorio.
- **Los «5 porqués» hacia una sola causa raíz** de la skill `incident-response` de Anthropic: chocan con los factores
  que contribuyeron. Tampoco su «crear el incidente y paginar» sin confirmación.
- **Instalar subagentes genéricos de SRE** (`VoltAgent/awesome-claude-code-subagents`, los agentes de
  `wshobson/agents`): terminal y escritura sin niveles, metas inventadas y apuro. Sólo ideas, con atribución.
- **HolmesGPT** (Apache-2.0): trae herramientas que escriben y rinde con Kubernetes; para servidores sueltos es
  pesado. Queda como referencia de diseño (separar leer de remediar).
- **El modo autónomo de Azure SRE Agent** y **el caso Replit** (julio de 2025): confirman la barrera (revisión
  humana, separar producción, vuelta atrás), no agregan una pieza nueva.
- **Las alertas de varias ventanas sobre el presupuesto de errores** (*Site Reliability Workbook*, Sloth, Pyrra,
  OpenSLO), **`needrestart`**, **Windows Server (hotpatch, WSUS)** y el **MCP de PagerDuty**: son de la fase 2 o
  quedan fuera de la fase 1.
- **Prometheus, Alertmanager, Loki, Grafana, OpenTelemetry Collector y Alloy** como pila de observabilidad: la elige
  cada proyecto en `DEC-008`. Loki y Grafana son AGPL-3.0: usarlos tal cual está bien; modificarlos y ofrecerlos
  como servicio pide revisión legal.

## Lo que el informe no pudo verificar

- El detalle del **OWASP Top 10 para aplicaciones agénticas 2026**: el PDF no se leyó entero; los nombres de los
  riesgos salen de cobertura secundaria. No se usó en lo construido.
- La **licencia de dnf**.
- El **servidor remoto** al que pasó el MCP de PagerDuty (el repositorio quedó deprecado): sin evaluar.
- En **RHEL**, que `needs-restarting -r` sea la forma de saber si hace falta reiniciar: el informe lo dejó en ⚠. La
  documentación confirma los códigos de salida; no dice si necesita permisos de administrador.

_Últ. modif.: 2026-11-18 — @equipo — mudada a la sección (M-062)_
