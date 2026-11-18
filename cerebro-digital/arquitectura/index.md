---
id: seccion-arquitectura
tipo: indice
estado: F-Draft
modulo: general
title: "Arquitectura e infraestructura"
description: Portada de la sección transversal de arquitectura e infraestructura — qué cubre, cómo se le pide a la IA, las guías del método, los scripts, las decisiones, dónde va lo del proyecto y las fuentes.
tags: [arquitectura, infraestructura, indice, seccion]
last_updated: 2026-11-18
author: "equipo"
---

# Arquitectura e infraestructura

Cómo se diseña la arquitectura de la aplicación y cómo se escribe su infraestructura como código. Esta sección es
**transversal**: guarda el método y las fuentes, que valen para cualquier módulo. Lo que el proyecto decidió y lo
que tiene (los recursos, los ambientes) vive en el pilar `arquitectura/` de cada módulo (abajo, «Dónde va lo del
proyecto»).

La puerta es la skill `arquitectura-e-infraestructura`; en una sesión propia, `claude --agent orquestador-arquitectura`.

## Qué cubre y qué no

**Cubre:**

- La vista C4 (contexto, contenedores, despliegue) y los atributos de calidad.
- Una decisión técnica, desde las opciones hasta su `DEC-nnn`.
- La infraestructura como código: Terraform u OpenTofu, Bicep, Dockerfile, Compose, Kubernetes.
- Auditar un cambio de infraestructura y explicar su plan antes de aprobarlo.

**No cubre:**

- El pipeline, la promoción de una versión y su vuelta atrás; lo que ya corre (salud, parches, incidentes de un
  servidor) → [[cerebro-digital/devops/index|DevOps]].
- Escanear la aplicación, auditar o endurecer un servidor → [[cerebro-digital/seguridad/index|Seguridad]].
- La portada de la red es [[cerebro-digital/networking/index|Networking]]; el diseño de la red está acá
  (`disenar-red.md`, abajo), y el diagnóstico de la que ya corre, en DevOps.
- El código de la aplicación → la skill `desarrollo`.

## Cómo se le pide

Qué pedido va a qué guía, con qué script y con qué barrera está en una sola tabla: §«Ruteo: el objeto del pedido
decide» de `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/SKILL.md` (acá no se copia, para
que no se desfase). Por ejemplo: «diseñá la arquitectura», «armá la infraestructura», «diseñá la red» o «revisá este
plan de infraestructura».

## Qué hace la IA sola y qué no

Escribe el código de infraestructura y corre lo que no toca la nube (formato, validación, linters, pruebas con
proveedores simulados). El plan contra un ambiente real y el `apply` los corre el pipeline y los aprueba una persona;
lo que borra o toca el estado, nunca la IA. Las reglas exactas están en el **GATE de INFRAESTRUCTURA** de [[AGENTS]].

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/SKILL.md` — la puerta: qué pedido va a qué guía y con qué barrera.
- `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-arquitectura.md` — diseñar o documentar la arquitectura (C4, atributos de calidad) y conducir una decisión técnica hasta su `DEC`.
- `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/armar-infraestructura.md` — escribir la infraestructura como código: estructura del repositorio, qué se fija, el estado, los secretos y cómo se prueba sin tocar la nube.
- `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-red.md` — diseñar la red de cada ambiente y escribirla como código: flujos, zonas, exposición mínima, salida, DNS, TLS y acceso administrativo.
- `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/auditar-infraestructura.md` — la auditoría de un cambio de infraestructura por otro agente, y el resumen de su plan.

## Los scripts

- `bin/auditar-iac.py` — lo estático de la infraestructura como código: estado o planes versionados, versiones sin fijar, secretos escritos tal cual, imágenes `latest`, usuario root, ingresos abiertos a todo internet hacia un puerto de administración o de base (`RED-ABIERTA`); con `--herramientas` suma fmt, validate, TFLint, Checkov, Trivy, hadolint y kubeconform.
- `bin/resumir-plan.py` — el plan de Terraform u OpenTofu contado por recurso (crear, cambiar, reemplazar, borrar), lo que guarda datos primero, y la frase de la pregunta de aprobación; nunca imprime valores.
- `bin/radiografiar-codigo.py --mermaid` — si la aplicación ya existe, el punto de partida de la vista C4.

## Las decisiones

- `DEC-007` — Infraestructura, ambientes y entrega: plataforma, herramienta de infraestructura, estado, identidad del pipeline, gestor de secretos, cómo corre la aplicación, escáneres, y los temas de red (zonas por ambiente, acceso administrativo, dónde termina TLS, quién administra el DNS, salida a internet). Vive en [[decisiones]], en `⚠` hasta que el equipo la decida.

## Dónde va lo del proyecto

Lo escribe `cerebro-curator`, con el «sí» de una persona.

| Qué | Dónde |
|---|---|
| Las decisiones técnicas (`DEC-nnn`) | [[decisiones]] |
| Los recursos de cada ambiente, el estado, los secretos y la vista de despliegue | [[infraestructura]] |
| Los ambientes, uno por fila, y quién aprueba en cada uno | [[ambientes]] |
| La estructura de los repositorios y las convenciones de código | [[esqueleto-proyectos]] |

El pilar entero del módulo: [[cerebro-digital/modulo-ejemplo/arquitectura/index|Arquitectura del módulo]].

## Las fuentes

[[cerebro-digital/arquitectura/fuentes|Fuentes de arquitectura e infraestructura]]: de dónde salió cada idea del
método y de los scripts, con su licencia y su fecha, y lo que se miró y no se tomó.

_Últ. modif.: 2026-11-18 — @equipo — sección nueva del Cerebro (M-062)_
