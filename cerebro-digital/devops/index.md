---
id: seccion-devops
tipo: indice
estado: F-Draft
modulo: general
title: "DevOps: CI/CD, despliegue, operación y GitLab"
description: Portada de la sección transversal de DevOps — el pipeline y el despliegue, la operación de servidores y GitLab como plataforma; cómo se le pide a la IA, las guías del método, los scripts, las decisiones, dónde va lo del proyecto y las fuentes.
tags: [devops, despliegue, operacion, gitlab, indice, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# DevOps: CI/CD, despliegue, operación y GitLab

Cómo llega una versión a un ambiente, cómo se mantiene andando lo que corre y cómo está configurado GitLab. Esta
sección es **transversal**: guarda el método y las fuentes de tres funciones, cada una con su puerta. Lo que el
proyecto tiene (sus ambientes, su inventario, su GitLab, sus runbooks e incidentes) vive en los pilares de cada
módulo (abajo, «Dónde va lo del proyecto»).

| Función | Puerta (skill) | Sesión propia |
|---|---|---|
| CI/CD y despliegue | `despliegue-continuo` | `claude --agent orquestador-despliegue` |
| Operación de servidores | `operacion-de-servidores` | `claude --agent orquestador-operacion` |
| GitLab como plataforma | `gestion-de-gitlab` | `claude --agent orquestador-gitlab` |

## Qué cubre y qué no

**Cubre:**

- El pipeline de un repositorio (GitHub Actions, GitLab CI, Azure Pipelines), la promoción de una versión, su vuelta
  atrás, las migraciones del rango y la cadena de suministro.
- La salud de un servidor, el mantenimiento con plan de cambio (parches, certificados, disco, logs, respaldos,
  reinicios), una caída y los runbooks.
- GitLab como plataforma: proyecto, grupo, runners, instancia propia y qué barreras da el plan.

**No cubre:**

- Escribir la infraestructura como código o diseñar la arquitectura → [[cerebro-digital/arquitectura/index|Arquitectura]].
- «¿Está expuesto?»: escanear, auditar o endurecer un servidor, un incidente de seguridad → [[cerebro-digital/seguridad/index|Seguridad]]. Acá la pregunta es «¿anda bien?».
- La portada de la red es [[cerebro-digital/networking/index|Networking]]; el diagnóstico de la red que ya corre
  («no llega», «no resuelve») está acá (`diagnosticar-red.md`, abajo), y su diseño, en Arquitectura.
- El tablero (Azure DevOps o el local) → `tablero/`.

## Cómo se le pide

Qué pedido va a qué guía, con qué script y con qué barrera está en la tabla §«Ruteo: el objeto del pedido decide» del
`SKILL.md` de cada puerta (acá no se copia, para que no se desfase):

- `cerebro-digital/configuracion-ia/skills/despliegue-continuo/SKILL.md` — por ejemplo «armá el pipeline» o «pasá a
  producción».
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/SKILL.md` — por ejemplo «¿cómo está el servidor?»,
  «renová el certificado» o, de la red, «no llega» y «no resuelve».
- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/SKILL.md` — por ejemplo «¿están protegidas las ramas?» o
  «auditá el runner».

## Qué hace la IA sola y qué no

Lee, mide y prepara; no despliega, no aprueba y no toca la protección de la plataforma. Un servidor se toca sólo si
figura en el inventario autorizado, hasta el nivel que el inventario le da, y el nivel de cada cambio (N0 a N3) fija
cuántos «sí» pide. En GitLab, lee sólo dentro del destino autorizado. Las reglas exactas están en [[AGENTS]]: **GATE
de DESPLIEGUE**, **GATE de SERVIDOR** y **GATE de GITLAB**.

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

**CI/CD y despliegue** — puerta: `cerebro-digital/configuracion-ia/skills/despliegue-continuo/SKILL.md`

- `cerebro-digital/configuracion-ia/skills/despliegue-continuo/references/armar-pipeline.md` — armar o revisar el pipeline de un repositorio para que la IA no pueda bajarle la guardia.
- `cerebro-digital/configuracion-ia/skills/despliegue-continuo/references/desplegar.md` — llevar una versión a un ambiente y volver atrás; las estrategias y las migraciones.
- `cerebro-digital/configuracion-ia/skills/despliegue-continuo/references/cadena-de-suministro.md` — fijado de dependencias del pipeline, SBOM, firma o atestación, actualizaciones automáticas.

**Operación de servidores** — puerta: `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/SKILL.md`

- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/diagnosticar.md` — la salud de un servidor o de un servicio, en sólo lectura.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/mantenimiento.md` — parches, certificados, disco, logs, respaldos y reinicios, con su nivel y su plan de cambio.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/incidente.md` — una caída o una lentitud: lo propio de los servidores.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/diagnosticar-red.md` — «no llega», «no resuelve», «anda lento»: la red de lo que ya corre, en sólo lectura y de a un peldaño, y el nivel de cada cambio de red.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/runbook.md` — cómo se escribe un runbook que sirva a las tres de la mañana.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/acceso.md` — cómo llega la IA a un servidor sin tener una shell: las identidades que instala una persona.
- `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/assets/colector-salud.sh` — el colector de salud que una persona copia al servidor.

**GitLab** — puerta: `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/SKILL.md`

- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/references/proyecto-y-grupo.md` — lo que tiene que estar configurado en un proyecto y un grupo, las identidades y lo que no se escribe.
- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/references/planes-y-barreras.md` — qué barrera da cada plan y qué la reemplaza cuando no está.
- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/references/ci-en-gitlab.md` — lo propio de GitLab CI que el método general no cubre.
- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/references/runners-e-instancia.md` — runners e instancia propia: versión, actualización, respaldo, ajustes.
- `cerebro-digital/configuracion-ia/skills/gestion-de-gitlab/references/llegar-al-servidor.md` — los caminos de GitLab al servidor y su barrera.

El método general que estas guías aplican sin repetir (qué tiene que exigir el pipeline, migraciones, incidentes,
observabilidad) está en `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/`.

## Los scripts

- `bin/verificar-pipeline.py` — el pipeline de un repositorio: permisos, fijado por SHA, disparadores privilegiados, inyección, secretos de larga vida, ambientes contra la ficha, controles que no frenan.
- `bin/gate-despliegue.py` — los datos duros antes de promover una versión: el ambiente en la ficha, su protección, pipeline en verde, mismo artefacto, migraciones, vuelta atrás y ventana de observación.
- `bin/clasificar-migraciones.py` — cada migración SQL nueva del rango: expandir, contraer, mixta, neutra o sin clasificar.
- `bin/activo-autorizado.py` — si un servidor, un cluster o una URL figura en el inventario autorizado, por su alias exacto, y hasta qué nivel.
- `bin/salud-host.py` — la salud de un servidor leída del reporte del colector: disco e inodos, unidades caídas, reinicio pendiente, reloj.
- `bin/vigencia-certificados.py` — por cada URL del inventario, cuánto le queda al certificado, si el nombre coincide y si la cadena valida.
- `bin/gate-operacion.py` — los datos duros antes de un cambio N1 o N2: alias autorizado para ese nivel y un plan con comando, salida esperada, verificación y vuelta atrás.
- `bin/auditar-gitlab.py` — GitLab en sólo lectura: protección y ajustes de CI de un proyecto o grupo, `config.toml` de un runner, versión y ajustes de la instancia, y un texto antes de escribirlo en GitLab.
- `bin/auditar-diff.py` — con `--repo`, los mensajes de commit que cerrarían una tarjeta por afuera de sus barreras.

## Las decisiones

Viven en [[decisiones]], en `⚠` hasta que el equipo las decida. `DEC-005` (el modo desatendido) no cubre ninguna de
estas, salvo el push de la rama de la Tarea y abrir su Merge Request.

- `DEC-007` — Infraestructura, ambientes y entrega: plataforma de CI/CD y dónde vive la aprobación de producción, estrategia de despliegue y vuelta atrás, ambientes y promoción, cadena de suministro, migraciones.
- `DEC-008` — Operación de servidores: alcance de la IA por ambiente, identidades de acceso, registro, umbrales de salud, ventana y canario, parches, respaldos, observabilidad, cuándo hay postmortem.
- `DEC-010` — GitLab: destino autorizado, plan, identidad de la IA, servidor MCP, barrera de producción, cierre automático, runners.

## Dónde va lo del proyecto

Lo escribe `cerebro-curator`, con el «sí» de una persona.

| Qué | Dónde |
|---|---|
| Los ambientes, uno por fila, y quién aprueba en cada uno | [[ambientes]] |
| El GitLab del proyecto: destino autorizado, plan, runners por alias, identidades | [[gitlab]] |
| Los servidores, clusters y URLs que la IA puede tocar, y hasta qué nivel | [[inventario]] |
| Cada cambio N1 o N2 hecho | [[cambios]] |
| Los runbooks (`RB-nnn`), uno por archivo en `operacion/runbooks/` | [[plantilla-runbook]] |
| Los incidentes (`INC-nnn`), uno por archivo en `operacion/incidentes/` | [[plantilla-incidente]] |
| Ramas, commits y Merge Requests del equipo | [[convenciones-git]] |

Los pilares enteros del módulo: [[cerebro-digital/modulo-ejemplo/operacion/index|Operación del módulo]] y
[[cerebro-digital/modulo-ejemplo/arquitectura/index|Arquitectura del módulo]]. Cómo se conecta el MCP de GitLab:
[[cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index|Guía del MCP de GitLab]].

## Las fuentes

- [[cerebro-digital/devops/fuentes-despliegue|Fuentes de CI/CD y despliegue]]
- [[cerebro-digital/devops/fuentes-operacion|Fuentes de operación de servidores]]
- [[cerebro-digital/devops/fuentes-gitlab|Fuentes de gestión de GitLab]]

Cada una dice de dónde salió cada idea del método y de los scripts, con su licencia y su fecha, y lo que se miró y no
se tomó.

_Últ. modif.: 2026-11-18 — @equipo — sección nueva del Cerebro (M-062)_
