---
id: fuentes-seguridad-aplicaciones
tipo: fuentes
estado: F-Draft
modulo: general
title: "Fuentes — seguridad de la aplicación"
description: De dónde salió cada idea de la mitad aplicación de la puerta seguridad (escanear, modelar amenazas, probar un ambiente), de sus scripts y del normalizador; bibliografía con licencia y fecha.
tags: [seguridad, aplicacion, fuentes, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# Referencias externas — seguridad de la aplicación

Esto es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca desde el
repositorio. Dice de dónde salió cada idea de la mitad «aplicación» de la puerta `seguridad` (escanear la aplicación,
modelar amenazas, probar un ambiente), de sus tres scripts, del normalizador `bin/seguridad/` y de la plantilla del
modelo de amenazas. Todo está redactado de nuevo, en español: de las fuentes se tomaron ideas, nunca texto. Sale del
informe de investigación `04 — Seguridad de aplicaciones` (2026-11-14); los formatos de reporte se confirmaron en la
documentación o en el código de cada herramienta el 2026-11-17.

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| OWASP Threat Modeling Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html | CC BY-SA 4.0: se lee, no se copia | 2026-11-14 | Las cuatro preguntas; el diagrama de flujo de datos con fronteras de confianza; STRIDE como disparador por elemento; las respuestas mitigar, eliminar, transferir o aceptar; las mitigaciones como requisitos | `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md`; `cerebro-digital/modulo-ejemplo/seguridad/amenazas/plantilla-modelo-de-amenazas.md` |
| Threat Modeling Manifesto | https://www.threatmodelingmanifesto.org/ | CC BY 4.0 | 2026-11-14 | Las cuatro preguntas y sus antipatrones (la lista genérica que sirve para cualquier sistema) | `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md` |
| OWASP Top 10 para LLM 2025 | https://genai.owasp.org/llm-top-10/ | CC BY-SA 4.0 (sitio) | 2026-11-14 | Las categorías a sumar cuando un componente usa un modelo de lenguaje (inyección de instrucciones, salida sin validar, autonomía excesiva, fuga del prompt, consumo sin límite); y que lo escaneado es dato, no instrucción | `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md`; la categoría `LLMnn` de la plantilla; las barreras de `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` |
| OWASP Top 10 para aplicaciones agénticas 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | CC BY-SA 4.0 (sitio) | 2026-11-14 | Que extiende al de LLM cuando hay un agente; la categoría `ASInn` (los diez nombres no se pudieron leer de la fuente oficial: abajo) | `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md`; la plantilla |
| OWASP ASVS 5.0.0 | https://asvs.owasp.org/ · https://github.com/OWASP/ASVS | CC BY-SA 4.0 | 2026-11-14 | Que una mitigación sale como requisito verificable con su identificador `capítulo.sección.requisito`. Verificar contra ASVS queda para la fase 2 | `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md`; la columna «Requisito» de la plantilla |
| SARIF 2.1.0 (OASIS) | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | Estándar OASIS | 2026-11-14 | `runs[].tool.driver.rules`, `ruleId`/`ruleIndex`, `level` (sin level vale `warning`), `locations`, `suppressions` con su `justification` y su `status`, `baselineState`, `partialFingerprints`, `invocations[].executionSuccessful` | `bin/seguridad/normalizar.py` |
| GitHub: soporte de SARIF en code scanning | https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning | Documentación de GitHub | 2026-11-14 | La convención `security-severity` (los rangos de crítica, alta, media y baja) y la huella `primaryLocationLineHash` | `bin/seguridad/normalizar.py` (severidad y huella) |
| Semgrep CE: referencia de la CLI | https://docs.semgrep.dev/cli-reference | LGPL-2.1 (motor) | 2026-11-14; formato 2026-11-17 | `--metrics=off` (con `auto` manda métricas si las reglas vienen del registro), `--disable-version-check`, `--sarif-output`, `--baseline-commit`; salida 2 o más es error; `--autofix` cambia el código | `bin/escanear-seguridad.py` (opciones y lista negra) |
| Semgrep Rules License v1.0 | https://semgrep.dev/legal/rules-license | Licencia propia de las reglas | 2026-11-14 | Las reglas comunitarias se usan sólo para uso interno y **no se pueden redistribuir**: nunca dentro del template | `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` («Antes de correr») |
| Opengrep | https://github.com/opengrep/opengrep | LGPL-2.1 | 2026-11-14; README 2026-11-17 | Fork de Semgrep compatible con sus reglas; `opengrep scan --sarif-output=<archivo> -f <reglas>`; publica binario de Windows | `bin/escanear-seguridad.py` |
| Bandit: formato SARIF | https://bandit.readthedocs.io/en/latest/formatters/sarif.html · https://github.com/PyCQA/bandit | Apache-2.0 | 2026-11-14; formato 2026-11-17 | El SARIF con `issue_severity` en las propiedades del resultado y `metrics._totals.loc` (líneas analizadas) | `bin/seguridad/normalizar.py` (severidad; cero líneas es `SIN DATOS`) |
| OSV-Scanner: documentación y código | https://google.github.io/osv-scanner/usage/offline-mode/ · `/output/` · `/configuration/` · https://github.com/google/osv-scanner (`pkg/models/results.go`) | Apache-2.0 | 2026-11-14; formato 2026-11-17 | `--offline` (no baja ni manda nada); dónde vive la base sin red (`OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY`, `<carpeta>/<ecosistema>/all.zip`); salidas 0, 1, 127 (error) y 128 (sin paquetes); el JSON (`results`, `packages`, `groups[].max_severity`); las tablas `IgnoredVulns` con `reason` y `effectiveUntil` | `bin/escanear-seguridad.py`; `bin/seguridad/normalizar.py` (lector y supresiones) |
| Gitleaks | https://github.com/gitleaks/gitleaks | MIT | 2026-11-14; README 2026-11-17 | Los comandos `git` y `dir`; `--redact`; `--report-format sarif`; `--exit-code`; las opciones de `git log`; `.gitleaksignore` y `gitleaks:allow`; que está «completo» y sólo recibe parches de seguridad | `bin/escanear-seguridad.py`; `bin/seguridad/normalizar.py` (supresiones) |
| Trivy: documentación y código | https://trivy.dev/latest/docs/references/configuration/cli/trivy_filesystem/ · https://trivy.dev/latest/docs/configuration/filtering/ · https://github.com/aquasecurity/trivy (`pkg/report/sarif.go`) | Apache-2.0 | 2026-11-14; formato 2026-11-17 | `--scanners misconfig`, `--skip-db-update`, `--skip-check-update`, `--disable-telemetry`, `--offline-scan`; en su SARIF, las etiquetas `vulnerability`/`misconfiguration`/`secret`, el `security-severity` y el mensaje con paquete, versión instalada y versión arreglada; `.trivyignore` con `exp:` | `bin/escanear-seguridad.py`; `bin/seguridad/normalizar.py` |
| Aviso de Aqua sobre el ataque a Trivy (19-mar-2026) | https://www.aquasec.com/blog/trivy-supply-chain-attack-what-you-need-to-know/ | — | 2026-11-14 | Un escáner es cadena de suministro: se fija por versión y hash, y las acciones del CI por SHA completo | `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` («Antes de correr»); las filas de `DEC-009` y de `DEPENDENCIAS-EXTERNAS.md` |
| TruffleHog | https://github.com/trufflesecurity/trufflehog | AGPL-3.0 (sólo se ejecuta) | 2026-11-14; README 2026-11-17 | Verifica cada secreto contra el proveedor salvo `--no-verification`; su salida JSON trae el valor (`Raw`), que el lector descarta | `bin/seguridad/normalizar.py`; las barreras de `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` |
| pip-audit | https://github.com/pypa/pip-audit (README y `pip_audit/_format/json.py`) | Apache-2.0 | 2026-11-14; formato 2026-11-17 | Consulta un servicio afuera; su JSON (`dependencies`, `vulns`, `fix_versions`, `aliases`) no trae severidad | `bin/seguridad/normalizar.py`; `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` (no se corre) |
| npm audit | https://docs.npmjs.com/cli/v11/commands/npm-audit | La del CLI de npm (no verificada) | 2026-11-14 | Manda nombres y versiones al registro; `--json` con `auditReportVersion` 2, `vulnerabilities`, `via` y `fixAvailable` | `bin/seguridad/normalizar.py`; `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` (no se corre) |
| ZAP: baseline, full scan y reporte JSON | https://www.zaproxy.org/docs/docker/baseline-scan/ · `/full-scan/` · https://www.zaproxy.org/docs/desktop/addons/report-generation/report-traditional-json/ | Apache-2.0 | 2026-11-14; formato 2026-11-17 | La baseline no ataca y el full scan sí; `-t`, `-J`, `-m`; la imagen y su carpeta `/zap/wrk`; salidas 0, 1, 2 y 3 (otra falla); `-u` baja una configuración de una URL y `-z` pasa opciones arbitrarias (lista negra); el JSON (`site`, `alerts`, `riskcode`, `instances`, `cweid`) | `bin/escanear-ambiente.py`; `bin/seguridad/normalizar.py`; `cerebro-digital/configuracion-ia/skills/seguridad/references/probar-ambiente.md` |
| Nuclei | https://docs.projectdiscovery.io/tools/nuclei/running · https://github.com/projectdiscovery/nuclei (`pkg/output/output.go`) | MIT | 2026-11-14; formato 2026-11-17 | Plantillas de un directorio fijado, sin las no firmadas (`-dut`), límite de pedidos por segundo (150 por defecto); las claves de su salida JSONL (`template-id`, `info`, `matched-at`; `request` y `response`, que no se copian) | `bin/seguridad/normalizar.py`; `cerebro-digital/configuracion-ia/skills/seguridad/references/probar-ambiente.md` |
| EPSS de FIRST | https://www.first.org/epss/ | «Libre y abierto» según la página; licencia formal no verificada | 2026-11-14 | La probabilidad de explotación a 30 días, con su percentil; se baja el archivo diario completo, no se consulta CVE por CVE | `bin/priorizar-vulnerabilidades.py` |
| Catálogo KEV de CISA | https://www.cisa.gov/known-exploited-vulnerabilities-catalog · esquema: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities_schema.json | No la leyó el informe 04 (el 05 la da como CC0 1.0) | 2026-11-14; esquema 2026-11-17 | Lo que ya se explota pesa primero; `vulnerabilities[].cveID`, `dateReleased`, `knownRansomwareCampaignUse` | `bin/priorizar-vulnerabilidades.py` |
| CVSS v4.0 | https://www.first.org/cvss/v4-0/ | Términos de FIRST (no verificados) | 2026-11-14 | «CVSS no es sólo el puntaje Base»: la severidad sola no prioriza | La matriz de `bin/priorizar-vulnerabilidades.py` |
| trailofbits/skills (`fp-check`) | https://github.com/trailofbits/skills | CC BY-SA 4.0: se lee, no se copia | 2026-11-14 | Idea, sin texto: cada hallazgo lo confirma otro, con contexto limpio, preguntando si la entrada la controla un atacante, si hay un control antes y qué gana | `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` |
| Claude Code: seguridad (`/security-review`, plugins `security-guidance` y `claude-security`) | https://code.claude.com/docs/en/security · `/security-guidance.md` · `/claude-security.md` | Términos de Anthropic | 2026-11-14 | «Los escaneos no son deterministas»: un revisor de IA es AVISO para el verificador, nunca puerta | `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` (tabla de momentos) |
| anthropics/claude-code-security-review | https://github.com/anthropics/claude-code-security-review | MIT | 2026-11-14 | Su propio aviso de que no está endurecida contra la inyección de instrucciones: lo que se revisa es dato | Las barreras de `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` |

## Herramientas que se ejecutan (no se copian)

| Herramienta | Origen | Licencia | Para qué | Cómo se fija la versión |
|---|---|---|---|---|
| Opengrep **o** Semgrep CE (una, la que fije `DEC-009`) | https://github.com/opengrep/opengrep · https://github.com/semgrep/semgrep | LGPL-2.1 | Análisis estático (`bin/escanear-seguridad.py`, categoría `sast`) | Binario por máquina o imagen del CI, por versión y hash; las reglas, por proyecto y con su commit fijo |
| Bandit | https://github.com/PyCQA/bandit | Apache-2.0 | Análisis estático de Python | `bandit[sarif]` por versión, con hash |
| OSV-Scanner y su base sin red | https://github.com/google/osv-scanner | Apache-2.0 (los datos de OSV: términos por ecosistema, no verificados) | Dependencias vulnerables (`sca`) | Binario por versión y hash; la base, con su fecha (la edad máxima, `DEC-009`) |
| Gitleaks | https://github.com/gitleaks/gitleaks | MIT | Secretos (`secretos`) | Binario por versión y hash |
| Trivy | https://github.com/aquasecurity/trivy | Apache-2.0 | Configuración que viaja con la aplicación (`config`) | Binario por versión y **hash** (nunca las versiones comprometidas en el incidente) |
| ZAP, en su imagen | https://github.com/zaproxy/zaproxy · `ghcr.io/zaproxy/zaproxy` | Apache-2.0 | Prueba dinámica (`bin/escanear-ambiente.py`) | Imagen por **digest**; el script nunca la baja |
| Docker | El de la máquina | La de la instalación (no verificada) | Correr la imagen de ZAP | El de la máquina; no lo instala ningún script |

**Cuyos reportes se leen, pero ningún script corre**: pip-audit y npm audit (necesitan red), Nuclei (agresivo por
defecto), TruffleHog (AGPL, verifica por defecto) y CodeQL (sólo con la licencia en regla).

## Lo que se miró y no se tomó

- **Vendorizar `semgrep-rules`**: su licencia prohíbe redistribuirlas; el fork `opengrep-rules` está archivado desde el 2025-11-28.
- **`--config auto` de Semgrep**: depende del registro, manda métricas y no es reproducible.
- **CodeQL por defecto**: sus términos prohíben usarlo con código que no es abierto sin licencia paga.
- **La Action `claude-code-security-review` en el núcleo**: sólo GitHub, no endurecida contra inyección, sin cambios desde feb-2026.
- **wshobson/agents y VoltAgent en bloque**: cientos de agentes genéricos; su STRIDE no pide evidencia ni fronteras; VoltAgent no audita lo que publica.
- **El texto de trailofbits/skills**: CC BY-SA 4.0 obligaría a licenciar igual lo adaptado; se tomó sólo la idea.
- **TruffleHog como escáner obligatorio**: AGPL y verifica secretos con red por defecto; Gitleaks (MIT) es el del núcleo.
- **Fijar Betterleaks ya**: su versión 2 está en desarrollo, con otra CLI y otra configuración.
- **DAST en cada commit o activo contra producción**: lento, ruidoso y peligroso.
- **Dependabot fuera de GitHub** y **Renovate**: abren actualizaciones; son otra puerta, no algo que lea el normalizador.
- **El Top 10 de OWASP 2025 como lista de verificación**: es concientización; lo verificable es ASVS (fase 2).
- **SAMM como skill**: mide la madurez de la organización, una vez por año.
- **pytm o Threat Dragon como requisito**: pytm pide Linux o macOS, Java, Graphviz y PlantUML; Threat Dragon es para personas. El Cerebro guarda Mermaid.
- **STRIDE GPT**: genera puntajes y árboles con un modelo; acá no hay puntajes «a ojo».
- **Reemplazar `bin/auditar-diff.py` por Gitleaks**: se perdería el piso que corre sin instalar nada; conviven.
- **NIST SSDF**: sirve para justificar ante una auditoría qué control va en cada etapa; no dejó nada en esta fase.
- **Un puntaje único de seguridad**: esconde lo que hay que arreglar.

## Lo que el informe no pudo verificar

- Los diez nombres oficiales del Top 10 agéntico 2026, y si el Top 10 2025 está marcado como final.
- La fecha del último commit de Opengrep y de Betterleaks.
- En Opengrep: `--sarif-output` sí está en su README (2026-11-17); `--metrics=off` y `--baseline-commit` no, y se pasan por compatibilidad con Semgrep. Si el binario no los acepta, sale con error y la categoría queda `SIN DATOS`.
- La licencia de los datos de EPSS, de OSV, de CVSS y del CLI de npm (la de KEV, según el informe 05, es CC0 1.0).
- La primera línea del CSV de EPSS (`#model_version:…,score_date:…`): la página de datos de FIRST no se pudo leer. Si falta, el script usa la fecha del archivo.
- La estructura completa de `npm audit --json` (la clave `metadata.dependencies.total` sale de fuentes secundarias).
- Si la araña de la baseline de ZAP se queda en el dominio del objetivo: la documentación no lo dice; el script controla después lo que pidió.
- Las etiquetas exactas de las plantillas intrusivas de Nuclei, y si OSV-Scanner, Gitleaks, Trivy y Nuclei publican binario de Windows.
- Que `--log-opts` de Gitleaks y los patrones de `-x` de Bandit se escriban como los arma el script: no se corrió ninguna herramienta.

_Últ. modif.: 2026-11-18 — @equipo — mudada a la sección (M-062)_
