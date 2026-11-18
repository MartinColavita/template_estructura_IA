---
id: seccion-seguridad
tipo: indice
estado: F-Draft
modulo: general
title: "Seguridad"
description: Portada de la sección transversal de seguridad — la de la aplicación y la de los servidores; cómo se le pide a la IA, las guías del método, los scripts, las decisiones, dónde va lo del proyecto y las fuentes.
tags: [seguridad, indice, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# Seguridad

Cómo se escanea la aplicación, se modelan sus amenazas y se prueba un ambiente; cómo se audita y se endurece un
servidor; cómo se prioriza una vulnerabilidad y cómo se atiende un incidente de seguridad. Esta sección es
**transversal**: guarda el método y las fuentes. Lo que el proyecto decidió y encontró (su política, sus
vulnerabilidades, sus modelos de amenazas) vive en el pilar `seguridad/` de cada módulo (abajo, «Dónde va lo del
proyecto»).

La puerta es la skill `seguridad`; en una sesión propia, `claude --agent orquestador-seguridad`.

## Qué cubre y qué no

**Cubre:**

- La aplicación: análisis estático, dependencias vulnerables y secretos de un repositorio o del diff de una Tarea;
  el modelo de amenazas de un flujo; la prueba dinámica contra un ambiente que corre.
- Los servidores: auditarlos y auditar sus imágenes, y el plan para endurecerlos.
- Priorizar las vulnerabilidades, con su plazo y su registro `V-nnn`.
- Un incidente de seguridad: una intrusión o su sospecha, un proceso o un acceso raro, una clave filtrada.

**No cubre:**

- Escribir código seguro → la skill `desarrollo`.
- La salud de un servidor («¿anda bien?»), una caída sin sospecha de intrusión, el pipeline y su cadena de
  suministro → [[cerebro-digital/devops/index|DevOps]]. Acá la pregunta es «¿está expuesto?».
- Los escáneres de la infraestructura como código (`bin/auditar-iac.py`) → [[cerebro-digital/arquitectura/index|Arquitectura]].
- La red (conectividad, DNS, firewalls de red) → la sección [[cerebro-digital/networking/index|Networking]].

## Cómo se le pide

Qué pedido va a qué guía, con qué script y con qué barrera está en una sola tabla: §«Ruteo: el objeto del pedido
decide» de `cerebro-digital/configuracion-ia/skills/seguridad/SKILL.md` (acá no se copia, para que no se desfase). Por
ejemplo: «escaneá la seguridad del repo», «auditá el servidor» o «se filtró una clave».

## Qué hace la IA sola y qué no

Evalúa y propone; no arregla sola. Lee y escanea lo autorizado; una prueba activa pide un «sí» que nombre la URL, y
nunca va contra producción. Un secreto encontrado no se usa ni se copia, y leer, mostrar o rotar un secreto lo hace
siempre una persona. En un incidente, la IA propone y una persona decide. Las reglas exactas están en [[AGENTS]]:
**GATE de PRUEBA ACTIVA**, **GATE de SERVIDOR** (niveles N0 a N3) y el apartado «Siempre».

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor. Puerta:
`cerebro-digital/configuracion-ia/skills/seguridad/SKILL.md`.

**La aplicación**

- `cerebro-digital/configuracion-ia/skills/seguridad/references/escanear-aplicacion.md` — escanear código, dependencias y secretos, con tres estados por categoría.
- `cerebro-digital/configuracion-ia/skills/seguridad/references/modelar-amenazas.md` — el modelo de amenazas de un flujo; lo que produce son requisitos.
- `cerebro-digital/configuracion-ia/skills/seguridad/references/probar-ambiente.md` — la prueba dinámica contra una aplicación que corre, pasiva y activa.

**Los servidores**

- `cerebro-digital/configuracion-ia/skills/seguridad/references/auditar-servidor.md` — auditar un servidor y sus imágenes, en sólo lectura.
- `cerebro-digital/configuracion-ia/skills/seguridad/references/endurecer-servidor.md` — de los hallazgos a un plan, cambio por cambio.

**Para las dos**

- `cerebro-digital/configuracion-ia/skills/seguridad/references/gestionar-vulnerabilidades.md` — qué se arregla primero, en qué plazo y cómo sale la tarjeta.
- `cerebro-digital/configuracion-ia/skills/seguridad/references/incidente-de-seguridad.md` — evidencia, contención propuesta y escalamiento.

Cómo se escribe código seguro, que estas guías no repiten:
`cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/seguridad-y-datos-sensibles.md`.

## Los scripts

- `bin/escanear-seguridad.py` — análisis estático, dependencias y secretos de un repositorio o del diff de una Tarea, con los escáneres instalados, sin red ni métricas; marca las supresiones sin motivo o vencidas.
- `bin/escanear-ambiente.py` — la prueba dinámica (ZAP) contra la URL exacta del inventario: pasiva por defecto, activa sólo si la fila lo admite, nunca contra producción.
- `bin/priorizar-vulnerabilidades.py` — la prioridad P1 a P4 de cada hallazgo, con KEV y EPSS desde archivos y la exposición del activo en el inventario.
- `bin/auditar-host.py` — la seguridad de un servidor del inventario, en sólo lectura: ssh-audit desde afuera y el reporte de Lynis que trae una persona.
- `bin/escanear-imagenes.py` — el reporte de Trivy o Grype de una imagen, con la antigüedad de la base y si el sistema base tiene soporte.
- `bin/juntar-evidencia.py` — copia sin modificar la evidencia de un incidente a una carpeta fuera del repositorio, con hash y manifiesto de custodia.
- `bin/seguridad/` — el esquema común de hallazgos y el normalizador que comparten los scripts de seguridad.
- `bin/activo-autorizado.py` — si un servidor, un cluster o una URL figura en el inventario autorizado, y hasta qué nivel.
- `bin/gate-operacion.py` — los datos duros antes de aplicar un plan de endurecimiento (N1 o N2).
- `bin/auditar-diff.py` — secretos y posibles datos personales en las líneas agregadas de un diff; el piso que corre sin instalar nada.

## Las decisiones

- `DEC-009` — Seguridad: herramientas, qué frena la entrega, prioridad y plazos, antigüedad de los datos, supresiones y excepciones, qué sale de la máquina, cómo audita la IA un servidor, línea base por sistema operativo, quién autoriza una prueba dinámica, incidente de seguridad. Vive en [[decisiones]], en `⚠` hasta que el equipo la decida; `DEC-005` no la cubre.

## Dónde va lo del proyecto

Lo escribe `cerebro-curator`, con el «sí» de una persona. Lo crudo (la salida de un escáner, la evidencia) nunca
entra: vive en `borrador/` de quien lo corrió.

| Qué | Dónde |
|---|---|
| La política del módulo: alcance, línea base, contactos por rol, registro de auditorías | [[politica]] |
| El registro de vulnerabilidades (`V-nnn`) | [[vulnerabilidades]] |
| Los modelos de amenazas, uno por flujo, en `seguridad/amenazas/` | [[plantilla-modelo-de-amenazas]] |
| Qué se puede tocar y hasta dónde (el alcance de la seguridad también) | [[inventario]] |
| Los incidentes (`INC-nnn`), de seguridad u operativos, en `operacion/incidentes/` | [[plantilla-incidente]] |

El pilar entero del módulo: [[cerebro-digital/modulo-ejemplo/seguridad/index|Seguridad del módulo]].

## Las fuentes

- [[cerebro-digital/seguridad/fuentes-aplicaciones|Fuentes de seguridad de la aplicación]]
- [[cerebro-digital/seguridad/fuentes-servidores|Fuentes de seguridad de los servidores]]

Cada una dice de dónde salió cada idea del método y de los scripts, con su licencia y su fecha, y lo que se miró y no
se tomó.

_Últ. modif.: 2026-11-18 — @equipo — sección nueva del Cerebro (M-062)_
