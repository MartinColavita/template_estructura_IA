---
id: seccion-desarrollo
tipo: indice
estado: F-Draft
modulo: general
title: "Desarrollo: el método para escribir código"
description: Portada de la sección transversal de desarrollo — qué cubre, cómo se le pide a la IA, las guías del método, los scripts, las decisiones, los seis guardarraíles, dónde va lo del proyecto y las fuentes.
tags: [desarrollo, codigo, tdd, metodo, indice, seccion]
last_updated: 2026-11-27
author: "equipo"
---

# Desarrollo: el método para escribir código

Cómo se escribe, se revisa y se entrega el código de la aplicación. Esta sección es **transversal**: guarda la
portada del método y sus fuentes, que valen para cualquier módulo. El método vive en la skill; lo que el proyecto
decidió (el stack, la estructura de los repositorios, lo que ya está construido) vive en los pilares de cada módulo
(abajo, «Dónde va lo del proyecto»). El código en sí no vive en este repositorio (`DEC-001`).

La puerta es la skill `desarrollo`: todo lo que es código entra por ahí. Para desarrollar en paralelo las Tareas
asignadas, `desarrollar-asignadas`, con el diseño de
[[cerebro-digital/configuracion-ia/orquestador-desarrollo|Orquestador de desarrollo]].

## Qué cubre y qué no

**Cubre:**

- El ciclo de una Tarea: contrato primero, test en rojo con evidencia, código, refactor, revisión por otro agente,
  Merge Request y entrega.
- Arreglar un bug, depurar, refactorizar, revisar código, migrar el esquema de la base, dependencias y secretos,
  observabilidad, rendimiento, accesibilidad, incidentes en el código.
- Lo específico del stack del back y del front, que cada proyecto completa al decidir `DEC-003`.

**No cubre:**

- Las pruebas de punta a punta de la aplicación desplegada → [[cerebro-digital/qa/index|QA y pruebas]].
- Absorber o modernizar una aplicación existente → [[cerebro-digital/modernizacion/index|Modernización]] (el método de
  refactor y migración está acá; la decisión y los slices, allá).
- La infraestructura, el pipeline, los servidores y la seguridad: el ciclo es el de acá, pero lo específico lo pone la
  puerta de cada función → [[cerebro-digital/arquitectura/index|Arquitectura]], [[cerebro-digital/devops/index|DevOps]]
  y [[cerebro-digital/seguridad/index|Seguridad]].
- Redactar o cargar la Tarea → [[cerebro-digital/tickets/index|Tickets]]. La Tarea dice **qué**; esto, **cómo** (G1).

## Cómo se le pide

Por ejemplo: «programá esto», «hacé el endpoint», «escribí los tests», «revisá el código», «arreglá este bug», «por qué
falla», «migrá la base», o «desarrollá mis tareas asignadas». Qué pedido va a qué guía está en las tablas
§«El método — organizado por cuándo lo vas a usar» de `cerebro-digital/configuracion-ia/skills/desarrollo/SKILL.md`
(acá no se copian, para que no se desfasen).

## Qué hace la IA sola y qué no

Programa en la rama de la Tarea, en un espacio de trabajo aparte, con test primero; **no se aprueba a sí misma**: la
verifica otro agente, en sólo lectura. Nada sale del repositorio sin un «sí» (o lo que fije `DEC-005`). Las reglas
exactas están en [[AGENTS]]: **GATE de WORKTREE**, **GATE de BORRADO de worktree** y «Skills de desarrollo — cómo se
usan».

## Los seis guardarraíles

G1 a G6 (el código y el conocimiento no se mezclan, punto de entrada único, precedencia escrita, nada sale sin
un «sí», lo externo se declara, el lenguaje lo pone el repositorio): enteros en `AGENTS.md` §«Skills de desarrollo» y en
la skill `desarrollo`. Acá no se copian, para que no se desfasen.

## Las guías del método

Obsidian no las muestra (la carpeta de skills está oculta en el vault): se abren desde el editor.

- `cerebro-digital/configuracion-ia/skills/desarrollo/SKILL.md` — la puerta: la idea en tres frases, los guardarraíles y qué guía se lee en cada momento.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/` — las guías, una por tema: el ciclo rojo-verde y su evidencia, crear un endpoint, arreglar un bug, depurar, refactor, revisión de código, Merge Request, ramas y commits, el stack del back y del front, simular la API, accesibilidad, tests unitarios, la suite, pruebas de aceptación, contrato OpenAPI, seguridad y datos sensibles, dependencias, observabilidad, migración de base, entrega, refactor y migración, ingeniería inversa, adoptar un proyecto, rendimiento, incidentes y código ajeno.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/indice-del-metodo.md` — qué guía se lee antes de un trabajo de tests, de un hito, de rendimiento, de un incidente o de infraestructura.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/skills-de-los-repos.md` — las skills que ejecutan dentro del código (`guiar-tdd`, `verificar-tdd`, `auditar-codigo`, `armar-swagger`, `diagnosticar-repo`, `consultar-cerebro`) y por qué las que auditan viven en `back/` y `front/`.
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/tabla-de-precedencia.md` — quién gana cuando una guía externa y el proyecto chocan (G3).
- `cerebro-digital/configuracion-ia/skills/desarrollo/references/lo-que-exige-el-metodo.md` — lo que el método pide y una guía genérica no: evidencia del rojo, verificador distinto, tres estados, regla del cero.

## Los scripts

- `bin/verificar-tdd.py` — la mitad mecánica de `verificar-tdd`: por ítem, rojo sólo con tests y antes del verde, leído de `git log`.
- `bin/auditar-diff.py` — secretos y posibles datos personales en las líneas agregadas del diff; con `--repo`, los mensajes de commit que cerrarían una tarjeta por afuera de sus barreras.
- `bin/atajos.py` — las marcas `atajo:` del código, y las que no dicen cuándo se mejoran.
- `bin/gate-worktree.py` — los datos duros del GATE de WORKTREE: worktrees abiertos, árbol sucio, rama ya usada, base al día.
- `bin/armar-mision.py` — la misión del worker o del verificador, una sola plantilla.
- `bin/datos-cierre.py` — rama, commits, archivos y Merge Request, leídos del repositorio para el comentario de cierre.
- `bin/clasificar-migraciones.py` — cada migración SQL nueva del rango: expandir, contraer, mixta, neutra o sin clasificar.
- `bin/adoptar-proyecto.py` — enchufa una carpeta de proyecto existente a `back/` o `front/` en un comando.

## Las decisiones

Viven en [[decisiones]].

- `DEC-001` — El código de la aplicación no vive en este repositorio: vive en repositorios propios, que se clonan adentro de `back/` y `front/`; la excepción son las pruebas de punta a punta, en `qa/`.
- `DEC-002` — Arquitectura del código por módulos de dominio con capas; vale para cualquier lenguaje.
- `DEC-003` — Stack técnico del back, del front y del despliegue; hasta que exista, lo que dependa del stack es `SIN DATOS`.
- `DEC-005` — Modo desatendido: lo que cuenta como el «sí» de los GATEs del ciclo de la Tarea (worktrees, verificador, push y Merge Request).

## Dónde va lo del proyecto

Lo escribe `cerebro-curator`, con el «sí» de una persona.

| Qué | Dónde |
|---|---|
| La estructura de los repositorios y las convenciones de código | [[esqueleto-proyectos]] |
| Ramas, commits y Merge Requests del equipo | [[convenciones-git]] |
| Qué existe hoy de la aplicación, módulo por módulo | [[mapa]] |
| Bugs y sus causas, trampas del stack, patrones (`AP-nnn`) | [[aprendizajes]] |
| La deuda técnica (`DT-nnn`), con cuándo se paga | [[deuda]] |
| El stack del back y del front (comandos, rojo válido) | `tdd-stack-back.md` y `tdd-stack-front.md`, al decidir `DEC-003` |
| El código | En su repositorio (`back/`, `front/`), nunca en este |

El pilar entero del módulo: [[cerebro-digital/modulo-ejemplo/aplicacion/index|La aplicación construida]].

## Las fuentes

[[cerebro-digital/desarrollo/fuentes|Fuentes del método de desarrollo]]: de dónde salió cada idea del método, con su
licencia y su fecha, dónde nos quedamos con lo nuestro y lo que no se tomó.

_Últ. modif.: 2026-11-27 — @equipo — sección nueva del Cerebro_
