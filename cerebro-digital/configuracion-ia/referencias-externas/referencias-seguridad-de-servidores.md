# Referencias externas — seguridad de los servidores

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca desde el
repositorio. Dice de dónde salió cada idea de la mitad «servidores» de la puerta `seguridad` (auditar, endurecer,
vulnerabilidades e incidentes), de sus tres scripts y de las plantillas del pilar `seguridad/`. Todo está redactado
de nuevo, en español: de las fuentes se tomaron ideas, nunca texto.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| CIS Benchmarks | https://www.cisecurity.org/cis-benchmarks · términos: https://www.cisecurity.org/terms-of-use-for-non-member-cis-products | CC BY-NC-SA 4.0 más términos propios: no redistribuir, no derivar «directamente», **no afirmar un nivel de cumplimiento** | 2026-11-14 | Que la línea base se cita **por número de control**, nunca por su texto, y que nunca se escribe «cumple» | `references/endurecer-servidor.md`; `seguridad/politica.md` (línea base por sistema operativo) |
| ComplianceAsCode/content | https://github.com/ComplianceAsCode/content | BSD-3-Clause | 2026-11-14 | La forma libre de usar perfiles alineados a CIS y STIG, y generar el arreglo como playbook para revisar | `references/endurecer-servidor.md`; la fila «Línea base» de `DEC-009` |
| OpenSCAP: manual | https://static.open-scap.org/openscap-1.3/oscap_user_manual.html | LGPL-2.1 | 2026-11-14 | Evaluar no cambia nada y `--remediate` sí; el arreglo se genera **desde los resultados**, no desde el perfil entero | `references/endurecer-servidor.md` y `references/auditar-servidor.md` |
| ssh-audit | https://github.com/jtesta/ssh-audit (README, `src/ssh_audit/exitcodes.py` y los JSON de ejemplo de `test/docker/expected_results/`) | MIT | 2026-11-14 | Audita SSH **desde afuera**, como un cliente; `--dheat` es un ataque de denegación de servicio y `--conn-rate-test` una ráfaga; la auditoría común corre una prueba de tasa que se saltea con `--skip-rate-test`; los códigos de salida (0 bien, 1 no conectó, 2 aviso, 3 falla); el formato JSON (notas `fail`/`warn` por algoritmo, `cves`, el modo política con `passed` y `errors`) | `bin/auditar-host.py` (lista negra, `--skip-rate-test`, lectura del JSON); `references/auditar-servidor.md` |
| Guía OpenSSH de Mozilla | https://infosec.mozilla.org/guidelines/openssh | Creative Commons (variante no nombrada) | 2026-11-14 | Los principios (ingreso sólo con clave, sin contraseña, sin root, registro detallado); **no** su lista de algoritmos, que es de 2017 | `references/endurecer-servidor.md` |
| Lynis | https://github.com/CISOfy/lynis (`lynis`, `include/functions`, `include/report`) | GPL-3.0 (sólo se ejecuta) | 2026-11-14 | Corre adentro y no cambia la configuración; el formato de `lynis-report.dat` (`warning[]`, `suggestion[]`, `exception_event[]`, `hardening_index`, `report_datetime_end`, `finish=true`); que sin root saltea pruebas con el motivo «This test needs root permissions» **sólo en el log**, no en el reporte | `bin/auditar-host.py` (`--lynis-log` obligatorio para saber si corrió con privilegios); `references/auditar-servidor.md` |
| ansible-lockdown/UBUNTU24-CIS | https://github.com/ansible-lockdown/UBUNTU24-CIS | MIT | 2026-11-14 | Sus propias advertencias: no es una herramienta de auditoría, su `--check` no está soportado y un control puede desinstalar el firewall o el motor de contenedores | `references/endurecer-servidor.md` («Lo que no se hace nunca») |
| Firewall de Ubuntu (ufw) | https://ubuntu.com/server/docs/how-to/security/firewalls/ | No declarada en lo leído | 2026-11-14 | `ufw --dry-run` muestra lo que haría sin aplicarlo | `references/endurecer-servidor.md` (validación entre los dos «sí») |
| Trivy: documentación | https://trivy.dev/latest/docs/configuration/reporting/ · `/others/` · `/filtering/` · `/db/` | Apache-2.0 | 2026-11-14 | Sale 0 aunque haya vulnerabilidades; un sistema sin soporte puede dar cero y lo avisa; `--skip-db-update` para no bajar la base; las supresiones (`ExperimentalModifiedFindings`, con su `Statement`) | `bin/escanear-imagenes.py`; `references/auditar-servidor.md` |
| Trivy: código fuente | https://github.com/aquasecurity/trivy (`pkg/types/report.go`, `pkg/types/finding.go`, `pkg/fanal/types/artifact.go`) · https://github.com/aquasecurity/trivy-db (`pkg/metadata/metadata.go`) | Apache-2.0 | 2026-11-14 | El campo `Metadata.OS.EOSL` del reporte; que la fecha de la base (`UpdatedAt`) no viene en el reporte sino en `metadata.json` del cache o en `trivy version --format json` | `bin/escanear-imagenes.py` (`--base`) |
| Aviso de Aqua sobre el ataque a Trivy | https://www.aquasec.com/blog/trivy-supply-chain-attack-what-you-need-to-know/ | — | 2026-11-14 | Un escáner es cadena de suministro: se fija por versión y hash, nunca por etiqueta; las versiones comprometidas no se usan | La fila de Trivy de `DEPENDENCIAS-EXTERNAS.md` y la de `DEC-009` |
| Grype: documentación | https://oss.anchore.com/docs/reference/grype/cli/ · `/reference/grype/configuration/` · `/guides/vulnerability/eol-detection/` | Apache-2.0 | 2026-11-14 | `--fail-on` sale 2; la base tiene una edad máxima por defecto de 120 horas; el aviso `distro-eol` en `alertsByPackage`; las reglas de ignorar con su `reason` | `bin/escanear-imagenes.py` (tope de 120 h, sin `--fail-on`, sin actualizar la base) |
| Grype: código fuente | https://github.com/anchore/grype (`grype/presenter/models/document.go`, `descriptor.go`, `ignore.go`, `grype/vulnerability/provider.go`) | Apache-2.0 | 2026-11-14 | Dónde viene la fecha de la base (`descriptor.db.status.built`) y si es válida; `ignoredMatches` con `appliedIgnoreRules` | `bin/escanear-imagenes.py` |
| Catálogo KEV de CISA | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | CC0 1.0 | 2026-11-14 | Lo que ya se explota en la práctica pesa primero; se baja el catálogo completo | `references/gestionar-vulnerabilidades.md` |
| BOD 26-04 de CISA | https://www.cisa.gov/news-events/directives/bod-26-04-prioritizing-security-updates-based-risk | Gobierno de EE.UU. | 2026-11-14 | Priorizar por exposición, KEV, automatización e impacto; el plazo más corto es de 3 días. **Obliga sólo a agencias federales de EE.UU.**: es referencia | `references/gestionar-vulnerabilidades.md`; la propuesta ⚠ de plazos de `DEC-009` |
| EPSS de FIRST | https://www.first.org/epss/ | «Libre y abierto» según la página; licencia formal no verificada | 2026-11-14 | La probabilidad de explotación a 30 días; se baja el archivo diario completo, **no se consulta CVE por CVE** | `references/gestionar-vulnerabilidades.md` |
| CVSS v4.0 | https://www.first.org/cvss/v4-0/ | © FIRST | 2026-11-14 | El puntaje se registra con su versión y su vector | `seguridad/vulnerabilidades.md` |
| trailofbits/skills (`cvss-scoring`) | https://github.com/trailofbits/skills | CC-BY-SA-4.0: se lee, no se copia | 2026-11-14 | Idea, sin texto: un CVSS propio se justifica métrica por métrica | `references/gestionar-vulnerabilidades.md` |
| CycloneDX | https://cyclonedx.org/specification/overview/ | Especificación: Apache-2.0 | 2026-11-14 | Formato de SBOM y de VEX; es la recomendación del formato | La fila «Cadena de suministro» de `DEC-007` (el SBOM) |
| NIST SP 800-61 Rev. 3 | https://csrc.nist.gov/pubs/sp/800/61/r3/final | Publicación de NIST | 2026-11-14 | La respuesta como capas (preparación, respuesta, mejora) y las lecciones de todas las etapas | `references/incidente-de-seguridad.md` |
| RFC 3227 (BCP 55) | https://www.rfc-editor.org/rfc/rfc3227 | IETF | 2026-11-14 | El orden de volatilidad; no apagar antes de juntar; no confiar en los programas del equipo comprometido; no cambiar fechas de acceso; cortar la red de golpe puede disparar un borrado; la cadena de custodia | `references/incidente-de-seguridad.md`; `bin/juntar-evidencia.py` |
| OWASP Secrets Management Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html | CC BY-SA 4.0: se lee, no se copia | 2026-11-14 | Ante una fuga: revocar, rotar, borrar el valor sin romper la integridad del registro y registrar quién la usó | `references/incidente-de-seguridad.md` |
| Buenas prácticas de IAM de AWS | https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html | Documentación de AWS | 2026-11-14 | Mínimo privilegio y credenciales temporales: la IA no tiene credenciales de administración permanentes | La fila «Cómo audita la IA un servidor» de `DEC-009` |
| majiayu000/claude-arsenal (`server-security`) | https://github.com/majiayu000/claude-arsenal/blob/main/skills/server-security/SKILL.md | MIT | 2026-11-14 | Ideas, sin texto: la acción reversible más chica, primero evidencia de sólo lectura, cada cambio con su vuelta atrás | `references/endurecer-servidor.md` |

## Herramientas que se ejecutan (no se copian)

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| ssh-audit | https://github.com/jtesta/ssh-audit | MIT | `bin/auditar-host.py --correr-ssh-audit`, desde la máquina de quien audita; nunca `--dheat` ni `--conn-rate-test` | Versión y hash del paquete o binario, en `DEPENDENCIAS-EXTERNAS.md`; nada por etiqueta |
| Lynis | https://github.com/CISOfy/lynis | GPL-3.0 (sólo se ejecuta) | La corre **una persona** en el servidor; `bin/auditar-host.py` lee su `.dat` y su log | La versión queda en el reporte (`lynis_version`); instalarla es un cambio, con su plan |
| Trivy | https://github.com/aquasecurity/trivy | Apache-2.0 | `bin/escanear-imagenes.py --correr trivy`, o su reporte del pipeline | Versión y hash del binario; **nunca** 0.69.4, ni las imágenes 0.69.5 y 0.69.6, ni acciones de CI por etiqueta |
| Grype | https://github.com/anchore/grype | Apache-2.0 | `bin/escanear-imagenes.py --correr grype`, o su reporte del pipeline | Versión y hash del binario |
| Cliente de OpenSSH (`ssh -G`) | El del sistema operativo | La del sistema | `bin/auditar-host.py` resuelve el alias del inventario con la configuración local, **sin conectarse** | El del sistema |

## Lo que se miró y no se tomó

- **kube-hunter**: abandonado por su autor, y su modo activo cambia el cluster. **kube-bench, docker-bench-security
  y Prowler**: auditar un cluster, un host de contenedores o una cuenta de nube es fase 2.
- **tfsec**: absorbido por Trivy. **Checkov, KICS y Hadolint**: miran archivos del repositorio, y eso es
  `bin/auditar-iac.py`, de `arquitectura-e-infraestructura`.
- **gitleaks** sobre toda la historia: ya lo hace `bin/escanear-seguridad.py` sin `--base`. **TruffleHog en modo verificación**: verificar un secreto es usarlo
  contra el proveedor (G4), y su licencia es AGPL-3.0.
- **Falco Talon** y toda respuesta automática disparada por la IA: acciones sobre el cluster sin una persona.
- **Skills y subagentes publicados que endurecen de corrido** (`cholulaa/claude-code-hardening-skill`) o con
  terminal y sin confirmación (`security-engineer` e `incident-responder` de `VoltAgent/awesome-claude-code-subagents`):
  contradicen el GATE de SERVIDOR. Sirven como lista de temas.
- **El paquete `mukul975/Anthropic-Cybersecurity-Skills`**: no es de Anthropic pese al nombre y no describe pruebas
  de sus flujos.
- **Imponer HashiCorp Vault** (BSL 1.1, no OSI): el gestor de secretos lo elige el proyecto en `DEC-009`.
- **Trivy MCP**: versión 0.0.x, sin movimiento desde diciembre de 2025.
- **NIST SP 800-40 Rev. 4**: el parche como mantenimiento preventivo es de `operacion-de-servidores`.
- **dev-sec/linux-baseline**: se corre con InSpec, cuyos términos actuales no se verificaron.

## Lo que el informe no pudo verificar

- La licencia y el acceso público de los STIG de DISA (la página no se pudo leer).
- La tabla completa de plazos de la BOD 26-04 (es una imagen): sólo los cuatro criterios y los 3 días.
- La licencia formal de los datos de EPSS.
- Si hay una versión final de los elementos mínimos de un SBOM de CISA 2025 (sólo se encontró el borrador).
- Los códigos de salida de Lynis y de OpenSCAP (no hacen falta: los scripts leen el reporte).
- Servidores Windows: fuera de esta primera ola; quedan `SIN DATOS` hasta elegir herramienta.
- **Al escribir los scripts** no se pudo confirmar: que Trivy liste en su JSON un resultado `os-pkgs` aunque no
  encuentre nada (si no lo hiciera, una imagen limpia daría `SIN DATOS`, nunca un OK falso); la opción `--quiet` de
  `trivy image`; y la forma del descriptor de la base en las versiones viejas de Grype (se aceptan las dos).
