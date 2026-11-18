---
id: red
tipo: guia
estado: F-Draft
modulo: modulo-ejemplo
title: Red — modulo-ejemplo
description: La red de la aplicación por ambiente — zonas, qué se expone y a quién, puertos abiertos con su motivo, DNS, dónde termina TLS, la salida a internet y cómo se administra. El código que la crea vive en su repositorio y cita esta ficha.
tags: [arquitectura, red, networking, dns, tls, modulo-ejemplo]
last_updated: 2026-11-18
author: "equipo"
---

# Red — modulo-ejemplo

> Lo que la red **es**, en palabras: el código que la crea vive en su repositorio (`DEC-001`) y **cita** esta ficha,
> no la copia. Nace **con una fila de molde** entre `<...>` en cada tabla: mientras una tabla no tenga filas
> cargadas, lo que dependa de ella es `SIN DATOS`. **Sin direcciones ni nombres reales**: alias (los de [[inventario]]
> y [[ambientes]]) y `<rango>`; los rangos de verdad viven en el código, por variable. La completa una persona, o
> `cerebro-curator` con su «sí»; cada cambio, con su firma en [[log]]. La política (zonas, acceso administrativo,
> TLS, DNS, salida) la fija [[decisiones#DEC-007]]; lo que esté `⚠` ahí, acá también. Cómo se diseña: la skill
> `arquitectura-e-infraestructura`; cómo se diagnostica lo que ya corre: la skill `operacion-de-servidores`; la
> portada: [[networking/index]].

## Zonas por ambiente

Los ambientes, con sus nombres exactos, están en [[ambientes]]; un ambiente que no figura ahí no tiene red.

| Ambiente | Zona | Qué vive ahí (rol) | Rango | Dirección pública | Salida a internet |
|---|---|---|---|---|---|
| `<ambiente>` | `<borde · aplicacion · datos · administracion>` | `<el balanceador>` | `<rango>` | `<sí o no>` | `<ninguna · por el punto controlado · libre>` |

- La zona de **datos** no tiene dirección pública ni salida a internet.
- Producción no se conecta directo con desarrollo ni con prueba, salvo lo que fije `DEC-007`.

## Qué se expone y a quién

Una fila por flujo permitido. Lo que no está acá, no se abre.

| Ambiente | Origen | Destino (zona y rol) | Puerto y protocolo | Motivo | Estado |
|---|---|---|---|---|---|
| `<ambiente>` | `<internet · zona · grupo · rango de la organización>` | `<borde: el balanceador>` | `<443/tcp>` | `<la entrada pública de la aplicación>` | `⚠ a confirmar` |

- **A todo internet se abre sólo el borde.** Qué puertos no se abren nunca a todo internet lo fija
  `cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-red.md` §«Exposición
  mínima», y lo cuenta `bin/auditar-iac.py` (regla `RED-ABIERTA`).
- El **origen** se escribe como grupo o zona siempre que se pueda, no como dirección suelta.

## DNS

| Ambiente | Nombre | Tipo | Zona (pública o privada) | Apunta a (rol) | TTL | Quién lo administra (rol) |
|---|---|---|---|---|---|---|
| `<ambiente>` | `<nombre>` | `<A · AAAA · CNAME>` | `<pública>` | `<el balanceador>` | `<3600>` | `<rol>` |

Lo interno resuelve en la zona privada y no se publica en la pública. Cómo se cambia un registro sin cortar a
nadie (el TTL y la vuelta atrás):
`cerebro-digital/configuracion-ia/skills/arquitectura-e-infraestructura/references/disenar-red.md` §«DNS»; su nivel, la tabla «Un cambio de red: su nivel» de
`cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/diagnosticar-red.md`.

## Dónde termina TLS

| Ambiente | Nombre | Termina en | Re-cifrado hasta la aplicación | Certificado: de dónde sale | Renovación |
|---|---|---|---|---|---|
| `<ambiente>` | `<nombre>` | `<el balanceador>` | `<sí o no>` | `<la autoridad o el gestor de DEC-007>` | `<automática>` |

La vigencia la mide `bin/vigencia-certificados.py` contra las URL de [[inventario]]. La clave privada no se anota
ni se copia nunca.

## Cómo se administra

| Ambiente | Vía (acceso administrado, bastión o VPN) | Desde dónde | Con qué identidad | Dónde queda el registro de sesiones |
|---|---|---|---|---|
| `<ambiente>` | `<la de DEC-007>` | `<rango de la organización>` | `<identidad por persona>` | `<dónde>` |

Configurar quién entra es **tocar accesos**: lo hace una persona ([[AGENTS]]).

## Lo que esta ficha no guarda

- **Los recursos que implementan la red y la vista de despliegue**: [[infraestructura]].
- **Los servidores y las URL que la IA puede tocar**: [[inventario]].
- **Direcciones reales, credenciales, claves de VPN o de certificados**: en el código por variable, en el gestor de
  secretos o en la plataforma; nunca acá.

_Últ. modif.: 2026-11-18 — @equipo — sección nueva (M-063)_
