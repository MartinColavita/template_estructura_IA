---
id: seccion-networking
tipo: indice
estado: F-Draft
modulo: general
title: Networking — la red de la aplicación
description: Portada de la red en el ecosistema — qué cubre, cómo se le pide a la IA, qué puerta se carga, qué hace sola y qué no, las guías de método, el script, la decisión que lo fija y dónde va lo de cada proyecto.
tags: [networking, red, dns, tls, firewall, indice, okf]
last_updated: 2026-11-18
author: "equipo"
---

# Networking — la red de la aplicación

Esta sección es **la portada**: no tiene reglas propias ni datos del proyecto. Dice dónde está cada cosa de la red y
quién la hace. La red **no tiene una skill propia**: entra por dos puertas que ya existen, según si se **diseña**
(antes de que corra) o se **diagnostica** (lo que ya corre).

## Qué cubre y qué no

| Cubre | No cubre (y dónde está) |
|---|---|
| Las zonas de cada ambiente, qué se expone y a quién, los puertos con su motivo | Probar una aplicación que corre (prueba dinámica): `seguridad`. Escanear los puertos de un servidor o de un rango: la IA no lo hace, lo hace una persona |
| DNS: registros, zonas pública y privada, cambios seguros con TTL | Los protocolos y cifrados de TLS: `seguridad` |
| Dónde termina TLS y que los certificados se renueven solos | Renovar un certificado en un servidor: `operacion-de-servidores` (mantenimiento) |
| Firewall y grupos de seguridad escritos como código | El pipeline que los aplica: `despliegue-continuo` |
| Acceso administrativo (acceso administrado, bastión, VPN) | Dar o sacar accesos a personas: lo hace siempre una persona |
| Balanceadores y proxies inversos; la red en Kubernetes (Service, Ingress, NetworkPolicy) | La red de la oficina o de la organización: fuera del ecosistema |
| Diagnóstico de conectividad en sólo lectura: nombre, camino, TLS, demora | Los runners y la instancia de GitLab: `gestion-de-gitlab` |

## Cómo se le pide a la IA

| Si decís… | Se carga | Y la guía |
|---|---|---|
| «diseñá la red», «qué puertos abro», «armá la VPC» (o la VNet), «configurá el DNS», «dónde termino TLS», «cómo entramos a administrar» | `arquitectura-e-infraestructura` | `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-red.md` |
| «no llega», «no resuelve», «no conecta», «¿es la red?», «¿qué nivel tiene cambiar el DNS o el firewall?» | `operacion-de-servidores` | `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/diagnosticar-red.md` |
| «revisá este cambio de red», «¿está para el Merge Request?» | `arquitectura-e-infraestructura` | `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/auditar-infraestructura.md` |
| «¿qué puertos tenemos expuestos?» | `arquitectura-e-infraestructura` | Se contesta leyendo la ficha [[red]] y el código con `bin/auditar-iac.py` (regla `RED-ABIERTA`); escanear los puertos de un servidor o de un rango no lo hace la IA, lo hace una persona |

Ante la duda entre diseñar y diagnosticar, la IA pregunta: nunca elige por la persona.

## Qué hace sola y qué no

La IA lee y mide sólo lo que figura en [[inventario]], y escribe la red como código en la rama de la Tarea; la red
real la aplica el pipeline. Los niveles no se copian acá, están escritos una vez:

- **Las barreras** (GATE de SERVIDOR, de INFRAESTRUCTURA y de PRUEBA ACTIVA, y los niveles N0 a N3): [[AGENTS]],
  sección «Infraestructura, despliegue, servidores, seguridad y GitLab — barreras». Valen aunque no se cargue ninguna
  skill.
- **El nivel de cada cambio de red** (un registro DNS, un puerto, el firewall del sistema operativo, el balanceador):
  la tabla «Un cambio de red: su nivel» de
  `cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/diagnosticar-red.md`.
- **Escanear los puertos** de un servidor o de un rango: la IA no lo hace, lo hace una persona.

## El script y la regla

- `bin/auditar-iac.py`, regla **`RED-ABIERTA`**: un ingreso abierto a todo internet hacia un puerto de administración
  o de base en los grupos de seguridad y firewalls de Terraform u OpenTofu, y un `Service` `LoadBalancer` de
  Kubernetes sin rango de origen. Qué puertos son lo dicen el script (su ayuda) y
  `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-red.md` §«Exposición
  mínima»; lo que no ve (reglas por variable o con `dynamic`) lo avisa y queda para el criterio.
- `bin/vigencia-certificados.py`: el nombre, el camino y el certificado de las URL del inventario; distingue «no
  resuelve», «no contestó» y «rechazó la conexión».
- `bin/activo-autorizado.py`: si un destino está en el inventario y hasta qué nivel (`--prueba pasivo` para un pedido a
  la aplicación).

## La decisión que lo fija

[[decisiones#DEC-007]] — Infraestructura, ambientes y entrega: las zonas por ambiente, el acceso administrativo,
dónde termina TLS, quién administra el DNS y la salida a internet. Mientras un tema esté en `⚠`, lo que dependa de él
es `SIN DATOS`.

## Dónde va lo de cada proyecto

- **La red de cada ambiente** (zonas, puertos con su motivo, DNS, TLS, cómo se administra): la ficha [[red]] del pilar
  `arquitectura/` del módulo, sin direcciones reales.
- **Los recursos y la vista de despliegue**: [[infraestructura]]. **Lo que la IA puede tocar**: [[inventario]].
- **El código**: en su repositorio, por la skill `desarrollo`; nunca en este (`DEC-001`).
- **Diagnósticos y planes de cambio en curso**: `borrador/operacion/` (nunca se versiona).

## De dónde salió cada idea

La bibliografía, con licencia y fecha de cada fuente, lo que no se tomó y lo que no se pudo verificar:
[[networking/fuentes]].

_Últ. modif.: 2026-11-18 — @equipo — sección nueva (M-063)_
