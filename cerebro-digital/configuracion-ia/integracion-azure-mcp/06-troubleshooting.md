---
id: integracion-azure-mcp-06-troubleshooting
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Troubleshooting de la integración Azure MCP"
author: equipo
tags: [azure-devops, mcp, troubleshooting, tls, ca, pat, errores]
last_updated: 2026-08-26
---

# Troubleshooting de la integración Azure MCP

Errores típicos al conectar el MCP de Azure DevOps y cómo resolverlos. Empezá siempre por lo simple: variable cargada, terminal nueva, server conectado.

## 1. Error de certificado / TLS (solo si tu red intercepta el tráfico)

> **En la mayoría de las redes esto NO pasa:** Azure DevOps en la nube (`dev.azure.com`) tiene certificado público válido y la conexión funciona con las 3 variables normales. Este punto aplica solo si tu red corporativa intercepta el tráfico seguro.

**Síntoma:** al arrancar el MCP o hacer la primera llamada, algo como:

```
SELF_SIGNED_CERT_IN_CHAIN
UNABLE_TO_VERIFY_LEAF_SIGNATURE
unable to get local issuer certificate
```

**Causa:** tu red reemplaza el certificado de `dev.azure.com` por uno propio y Node no conoce esa autoridad certificadora.

**Solución (solo en ese caso):**
- Conseguí el certificado (`.pem`/`.crt`) de tu red y agregá la variable opcional `NODE_EXTRA_CA_CERTS` apuntando a ese archivo ([[03-configurar-mcp]]).
- Reiniciá la herramienta de IA tras corregir.
- No desactives la verificación TLS como "solución": es un riesgo de seguridad.

## 2. PAT vencido o revocado

**Síntoma:** `401 Unauthorized`, "TF400813", o "the user is not authorized".

**Causa:** el token caducó, fue revocado, o la variable `AZDO_PAT` está vacía/mal cargada.

**Solución:**
- Verificá que la variable esté cargada en una terminal **nueva** (ver [[02-guardar-token-envvar]]).
- Si venció, creá un PAT nuevo ([[01-crear-pat-azure]]) y actualizá `AZDO_PAT`.
- Reiniciá la herramienta para que el MCP lea el valor nuevo.

## 3. Scope insuficiente (no puede escribir)

**Síntoma:** la lectura anda, pero al **crear/editar** una tarjeta da `403 Forbidden` o "access denied".

**Causa:** el PAT tiene sólo **Work Items (Read)**, no **Read & Write**.

**Solución:**
- Creá (o recreá) el PAT con **Work Items (Read & Write)** ([[01-crear-pat-azure]]).
- Actualizá `AZDO_PAT` y reiniciá.
- Recordá: la escritura siempre requiere tu **confirmación humana** ([[04-automatizar-con-ia]]).

## 4. Org URL incorrecta

**Síntoma:** "project not found", "organization not found", 404, o el server conecta pero no lista nada.

**Causa:** `AZURE_DEVOPS_ORG_URL` tiene mal la organización (quedó el `<org>` sin reemplazar, o un typo).

**Solución:**
- Corregí `AZURE_DEVOPS_ORG_URL` a `https://dev.azure.com/<org>` con tu organización **real**.
- Verificá que tu usuario tenga acceso a esa organización/proyecto en el navegador.

## 5. El MCP no levanta

**Síntoma:** el server `azure-devops` figura **desconectado** o no aparece.

**Causas y soluciones:**
- **Node/npx no disponible:** confirmá con `node --version` y `npx --version`. Si faltan, instalá Node.js.
- **Primera corrida lenta:** `npx -y` descarga el paquete la primera vez; puede tardar. Esperá y reintentá.
- **Sin salida a internet para npm:** si la red bloquea el registry npm, el `npx` falla al bajar el paquete. Consultá con infra por el proxy/registry interno (**pendiente** según tu red).
- **JSON de config mal formado:** revisá comas y llaves en `.mcp.json` / config equivalente.
- **Variables no expandidas:** si tu herramienta no expande `${AZDO_PAT}`, confirmá que las variables estén en el entorno **antes** de abrir la IA (loader / `setx` + terminal nueva).

## 6. Cómo diagnosticar rápido

- Probá una llamada de **lectura** simple: "listá los proyectos" (`list_projects`). Si anda, el token y la conexión están bien.
- Verificá el estado del server: `claude mcp list` / `/mcp` (Claude Code), o el panel de MCP de tu herramienta.
- Chequeá que las variables estén cargadas en la terminal **desde la que abriste la IA** (no en otra).
- Aislá el problema: ¿falla la lectura (token/URL) o sólo la escritura (permisos del token)?

## Recuadro — Ejemplo (genérico)

Saliendo directo a `dev.azure.com` (nube), la lectura de work items (`get_work_item`, `list_work_items`) funciona con las 3 variables normales, sin certificado. Solo en redes que interceptan el TLS aparece el error de certificado, que se resuelve con la variable opcional `NODE_EXTRA_CA_CERTS`.

## Volver al índice

[[00-index]]
