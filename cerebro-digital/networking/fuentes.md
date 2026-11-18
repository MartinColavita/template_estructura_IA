---
id: fuentes-networking
tipo: fuentes
estado: F-Draft
modulo: general
title: Fuentes de la sección Networking
description: De dónde salió cada idea de la red — fuente, URL, licencia, fecha de consulta, qué se tomó y a dónde fue; lo que se miró y no se tomó, y lo que no se pudo verificar.
tags: [networking, red, fuentes, bibliografia, okf]
last_updated: 2026-11-18
author: "equipo"
---

# Fuentes de la sección Networking

Es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca. Se tomaron
**ideas**, escritas con palabras propias; los controles de CIS se citan sólo por número. La portada de la sección es
[[networking/index]].

## Fuentes consultadas

| Fuente | Origen (URL) | Licencia | Consultado el | Qué se tomó (idea) | A dónde fue |
|---|---|---|---|---|---|
| NIST SP 800-41 Rev. 1, *Guidelines on Firewalls and Firewall Policy* (2009, final) | https://csrc.nist.gov/pubs/sp/800/41/r1/final | Obra del gobierno de EE.UU. (dominio público en EE.UU.) | 2026-11-18 | Negar por defecto, en las dos direcciones, lo que la política no permite por escrito; la política de firewall como documento | `disenar-red.md` («Exposición mínima»); la tabla «Qué se expone y a quién» de [[red]] |
| NIST SP 800-207, *Zero Trust Architecture* (2020, final) | https://csrc.nist.gov/pubs/sp/800/207/final | Obra del gobierno de EE.UU. (dominio público en EE.UU.) | 2026-11-18 | No dar confianza por la ubicación en la red: el acceso se autoriza por identidad y por sesión | `disenar-red.md` («Acceso administrativo»: el acceso sin puerto abierto primero) |
| AWS Well-Architected, pilar de seguridad, *Protecting networks* (SEC05-BP01 a BP04) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html | Términos del sitio de AWS (no se verificó una licencia abierta) | 2026-11-18 | Capas de red, controlar el tráfico en cada capa, automatizar la protección (red como código) | `disenar-red.md` («Zonas por ambiente», «Escribirla como código») |
| Azure Well-Architected, *Networking and connectivity* (SE:06) | https://learn.microsoft.com/en-us/azure/well-architected/security/networking | Microsoft Learn (licencia de esta página no verificada) | 2026-11-18 | Clasificar flujos (entra y sale de internet contra entre piezas propias); publicar los menos nombres DNS posibles; puntos de acceso privados para servicios administrados; la salida de una red virtual está abierta por defecto y conviene un punto único; un 53 abierto también saca datos; acceso administrado sin dirección pública | `disenar-red.md` («Primero los flujos», «Salida», «DNS», «Acceso administrativo») |
| OWASP *Network Segmentation Cheat Sheet* | https://cheatsheetseries.owasp.org/cheatsheets/Network_Segmentation_Cheat_Sheet.html | CC BY-SA 4.0 (se leyó, **no se copió**: obliga a redistribuir lo derivado con la misma licencia) | 2026-11-18 | Separar en zonas de borde, aplicación y datos; una base sólo se alcanza desde su aplicación; la política de acceso escrita y legible | `disenar-red.md` (la tabla de zonas, redactada aparte); [[red]] |
| Kubernetes, *Network Policies* | https://kubernetes.io/docs/concepts/services-networking/network-policies/ | CC BY 4.0 (pie de página verificado) | 2026-11-18 | Los Pods no están aislados hasta que una política los elige; política que niega todo por espacio de nombres; sin un plugin que las aplique no hacen nada | `disenar-red.md` («Zonas por ambiente», verificador) |
| Google Kubernetes Engine, *Automatically created firewall rules* | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/firewall-rules | Documentación de Google Cloud (licencia de la página no verificada) | 2026-11-18 | Un `Service` `LoadBalancer` sin `loadBalancerSourceRanges` toma `0.0.0.0/0` y `::/0` por defecto | `bin/auditar-iac.py` (regla `RED-ABIERTA`, parte de Kubernetes); `disenar-red.md` |
| Documentación de los proveedores de Terraform: `aws_vpc_security_group_ingress_rule`, `azurerm_network_security_rule`, `google_compute_firewall` | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/vpc_security_group_ingress_rule.html.markdown · https://github.com/hashicorp/terraform-provider-azurerm/blob/main/website/docs/r/network_security_rule.html.markdown · https://github.com/hashicorp/terraform-provider-google/blob/main/website/docs/r/compute_firewall.html.markdown | MPL-2.0 (los repositorios de los proveedores) | 2026-11-18 | El significado de cada campo: protocolo `-1` es todos los protocolos y puertos; `*` y la etiqueta `Internet` como origen; `allow` sin `ports` es todos los puertos; `direction` vale `INGRESS` por defecto y para `INGRESS` pide uno de `source_ranges`, `source_tags` o `source_service_accounts`; la recomendación de una regla por recurso y de no mezclar formas | `bin/auditar-iac.py` (`RED-ABIERTA`); `disenar-red.md` («Escribirla como código») |
| Google Cloud, *VPC firewall rules* | https://docs.cloud.google.com/firewall/docs/firewalls | Documentación de Google Cloud (licencia de la página no verificada) | 2026-11-18 | Una regla de ingreso sin origen toma `0.0.0.0/0` (cualquier dirección IPv4) | `bin/auditar-iac.py` (`RED-ABIERTA`: un `google_compute_firewall` de ingreso sin origen cuenta como abierto) |
| Amazon Route 53, *Values for simple records* (TTL) | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-basic.html | Términos del sitio de AWS | 2026-11-18 | Antes de cambiar un registro en uso, bajar el TTL (por ejemplo a 300 s) y subirlo después de verificar | `disenar-red.md` («DNS»); `diagnosticar-red.md`; [[red]] |
| RFC 8659, *DNS Certification Authority Authorization (CAA) Resource Record* (2019) | https://www.rfc-editor.org/rfc/rfc8659 | IETF Trust | 2026-11-18 | Un registro `CAA` dice qué autoridades pueden emitir certificados para el dominio | `disenar-red.md` («DNS») |
| CIS Amazon Web Services Foundations Benchmark v3.0.0, controles **5.2** y **5.3** (sólo el número) | https://www.cisecurity.org/benchmark/amazon_web_services | Licencia propia de CIS (no se copia texto) | 2026-11-18 | Que un grupo de seguridad no admita ingreso desde `0.0.0.0/0` ni `::/0` a los puertos de administración remota | `bin/auditar-iac.py` (`RED-ABIERTA`, que además suma los puertos de base) |

## Herramientas que se ejecutan (no se copian)

Ninguna nueva. `RED-ABIERTA` es una regla propia de `bin/auditar-iac.py`, de biblioteca estándar, para que el chequeo
exista sin instalar nada. Los comandos de diagnóstico de `diagnosticar-red.md` (`nslookup`, `Resolve-DnsName`,
`Test-NetConnection`, `nc`, `curl`, `tracert`, `traceroute`, `mtr`) son del sistema operativo o de quien opera y no
los corre ningún script.

## Lo que se miró y no se tomó

- **Skills públicas de redes para agentes**: `network-engineer` de `sickn33/agentic-awesome-skills` (un agregador la
  lista como MIT), `network-engineer` de `rmyndharis/antigravity-skills` (MIT según un agregador),
  `network-engineering` de `aiskillstore/marketplace` y `dns-networking` de `thcjp/hermes-skills` (sin licencia
  visible), `network-diagnostics` de `jackspace/ClaudeSkillz` (generada automáticamente). Lo bueno: la escalera de
  diagnóstico (nombre, puerto, HTTP, certificado) de `dns-networking` y las listas por nube de `network-engineer`,
  que coinciden con lo que ya está. **Por qué no**: son guías generales sin barreras (ni inventario, ni niveles, ni
  sólo lectura), varias sin licencia clara, y en los registros públicos hay skills maliciosas: no se instala ni se
  copia ninguna.
- **Las reglas equivalentes de Checkov y Trivy** (que `bin/auditar-iac.py` ya sabe correr si están instaladas): no se
  copian; `RED-ABIERTA` existe para que el chequeo no dependa de una herramienta externa.
- **Las guías de configuración TLS** (protocolos y cifrados): no aplican a esta sección; son de la skill `seguridad`.
- **Escanear puertos** (por ejemplo `nmap`) como paso de diagnóstico: la IA no escanea puertos de servidores ni de
  rangos, lo hace una persona (el GATE de PRUEBA ACTIVA es para la URL de una aplicación). «¿Qué puertos tenemos
  expuestos?» se contesta leyendo la ficha [[red]] y el código con `bin/auditar-iac.py` (regla `RED-ABIERTA`).

## Lo que no se pudo verificar

- **NIST SP 800-41**: se leyó la página de la publicación y la definición de «negar por defecto» del glosario de NIST
  que la cita; el PDF no se leyó entero.
- **El texto oficial de Kubernetes sobre `loadBalancerSourceRanges`**: la página de Services no lo mostró en la
  lectura; el valor por defecto se confirmó en la documentación de GKE. En otras plataformas el comportamiento puede
  ser distinto (en una hay un pedido público porque el firewall de los nodos queda abierto a todo internet sin importar
  el rango): por eso la regla pide el rango escrito y no lo da por cumplido.
- **Los números de los controles de CIS** se confirmaron por catálogos de terceros que publican el benchmark v3.0.0,
  no por el PDF oficial de CIS.
- **Las licencias de las páginas de AWS, Microsoft Learn y Google Cloud** no se confirmaron: se tomaron ideas, sin
  texto.
- **Python 3.7**: no hay uno instalado en la máquina donde se construyó; se verificó que el script y su prueba usan
  sólo la gramática de 3.7 y se corrieron con 3.13.

_Últ. modif.: 2026-11-18 — @equipo — sección nueva (M-063)_
