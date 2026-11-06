---
id: integracion-azure-mcp-05-seguridad-phi
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Seguridad del token y PHI"
author: equipo
tags: [seguridad, pat, phi, privacidad, auditoria, rotacion]
last_updated: 2026-08-26
---

# Seguridad del token y PHI

Dos temas que no se negocian: cómo cuidar el **token** y por qué **nunca** van datos personales reales (PHI) a una tarjeta.

## El token es una contraseña

Tratá el PAT como lo que es: una **contraseña técnica** que actúa en tu nombre en Azure DevOps.

- **Read-only por defecto.** Salvo que estés automatizando el alta/edición, tu PAT debe tener sólo scopes de **lectura** ([[01-crear-pat-azure]]). Menos permiso = menos daño posible.
- **Per-user (auditoría).** Cada persona usa **su** token. Así, si algo pasa en el board, queda registrado **quién** lo hizo. Nunca compartas el tuyo ni uses el de otro.
- **Con caducidad.** Poné vencimiento corto (30/90 días) y renoválo. Nada de tokens eternos.
- **Rotar si se expone.** Si el token quedó en un log, en el chat, en un archivo versionado, en una captura, o se lo pasaste a alguien: **revocalo en Azure y creá uno nuevo** de inmediato. No esperes "a ver si pasa algo".
- **Nunca en texto que la IA lea.** El valor vive sólo en la variable de entorno `AZDO_PAT` ([[02-guardar-token-envvar]]); en los archivos va la referencia `${AZDO_PAT}`. Así el valor **no entra al contexto** del modelo.

### Cómo rotar (si se expone)

1. Azure DevOps → **User settings → Personal Access Tokens**.
2. Ubicá el token comprometido → **Revoke**.
3. Creá uno nuevo ([[01-crear-pat-azure]]) y actualizá tu variable de entorno ([[02-guardar-token-envvar]]).
4. Reiniciá la herramienta de IA para que tome el valor nuevo.

## PHI prohibido (regla del núcleo)

El PHI real (nombre, documento, identificador, dato sensible del dominio, teléfono, dirección) **nunca** va a una tarjeta de Azure ni al prompt: las tarjetas quedan registradas y meterlo lo filtra. Se usan **marcadores** que describen la estructura, no el dato: `<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`, `<telefono>`, `<direccion>`. Es la **regla de oro #2 de `AGENTS.md`** (con su tabla de marcadores) — vale íntegra acá. Si una tarjeta ya trae PHI real, se reemplaza por marcadores al mejorarla; no se pegan capturas/logs con datos reales; ante la duda, tratar como PHI y **no inventar**.

## Recuadro — Ejemplo (genérico)

En un producto de ejemplo, la skill de redacción tiene la regla PHI incorporada: al reescribir un bug, si aparece el nombre o la identificador de una persona, los reemplaza por `<persona>` / `<identificador>` antes de proponer el texto. El token del MCP `azure-devops` es per-user, read-only por defecto, y los secretos (incluido el PAT) van por variable de entorno / `secrets.env` gitignored — nunca a un `.md` que la IA lea.

## Siguiente paso

Resolver errores comunes → [[06-troubleshooting]].
