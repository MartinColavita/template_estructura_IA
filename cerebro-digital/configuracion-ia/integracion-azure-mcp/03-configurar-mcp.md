---
id: integracion-azure-mcp-03-configurar-mcp
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Configurar el servidor MCP de Azure DevOps"
author: equipo
tags: [azure-devops, mcp, claude-code, opencode, antigravity, configuracion]
last_updated: 2026-08-26
---

# Configurar el servidor MCP de Azure DevOps

Con el PAT ya guardado como variable de entorno ([[02-guardar-token-envvar]]), falta **registrar el servidor MCP** en tu herramienta. Usamos el server público **`@tiberriver256/mcp-server-azure-devops`**, que se ejecuta con `npx` (no hay que instalar nada a mano).

## Las 3 variables que necesita

Todas las herramientas usan el mismo bloque de variables de entorno para el server:

| Variable | Valor | Qué es |
|---|---|---|
| `AZURE_DEVOPS_ORG_URL` | `https://dev.azure.com/<org>` | URL de tu organización de Azure DevOps |
| `AZURE_DEVOPS_AUTH_METHOD` | `pat` | Método de autenticación: token personal |
| `AZURE_DEVOPS_PAT` | `${AZDO_PAT}` | **Referencia** a tu token (no el valor) |

> Fijate que `AZURE_DEVOPS_PAT` toma una **referencia** (`${AZDO_PAT}`), no el valor literal. El valor real vive en la variable de entorno.

### ¿Hace falta un certificado? (normalmente no)

La conexión es a **Azure DevOps en la nube** (`dev.azure.com`), que tiene un certificado público válido: con las 3 variables de arriba alcanza. **Solo** si tu red corporativa intercepta el tráfico seguro (algunas configuraciones internas) verías errores tipo `SELF_SIGNED_CERT_IN_CHAIN` o `UNABLE_TO_VERIFY_LEAF_SIGNATURE` (ver [[06-troubleshooting]]); en ese caso agregás una variable opcional más, `NODE_EXTRA_CA_CERTS`, apuntando al certificado de tu red (`.pem`/`.crt`). Para el caso normal no se usa.

## Claude Code

### Opción 1 — archivo `.mcp.json` (en la raíz del proyecto)

> Hay un esqueleto listo en **`.mcp.json.example`** (en esta misma carpeta): copialo a un `.mcp.json` en la raíz del proyecto y reemplazá sólo la organización: **`${AZDO_PAT}` va tal cual** (si ponés el valor, el token queda escrito en un archivo). El `.mcp.json` real no se versiona (queda per-host).

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@tiberriver256/mcp-server-azure-devops"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/<org>",
        "AZURE_DEVOPS_AUTH_METHOD": "pat",
        "AZURE_DEVOPS_PAT": "${AZDO_PAT}"
      }
    }
  }
}
```

### Opción 2 — comando `claude mcp add` (en una sola línea)

```bash
claude mcp add azure-devops --env AZURE_DEVOPS_ORG_URL=https://dev.azure.com/<org> --env AZURE_DEVOPS_AUTH_METHOD=pat --env 'AZURE_DEVOPS_PAT=${AZDO_PAT}' -- npx -y @tiberriver256/mcp-server-azure-devops
```

> **Las comillas simples son a propósito.** Sin ellas, bash reemplaza `${AZDO_PAT}` por el valor y el token
> queda escrito en tu configuración, y PowerShell la toma como una variable propia (vacía) y el token queda
> en blanco. Con comillas simples queda la referencia, y Claude Code la completa al arrancar el servidor.
> Corrélo en **PowerShell o bash**, no en el «Símbolo del sistema» (cmd), que deja las comillas pegadas. Si
> PowerShell responde con un error de argumentos, escribí el `--` entre comillas simples: `'--'`.
>
> **Si ya lo habías registrado con la versión anterior de esta guía** (sin comillas), el token quedó escrito
> en tu configuración: corré `claude mcp remove azure-devops` desde la misma carpeta donde lo agregaste,
> registralo de nuevo con el comando de arriba y **revocá ese token en Azure** ([[05-seguridad-y-phi]]).

Verificá con `claude mcp list` o el comando `/mcp` dentro de una sesión: el server `azure-devops` debe figurar **conectado**, sin aviso de variable faltante.

## opencode

En la config de MCP de opencode (su `opencode.json` / archivo de configuración), agregá el server como proceso local:

```json
{
  "mcp": {
    "azure-devops": {
      "type": "local",
      "command": ["npx", "-y", "@tiberriver256/mcp-server-azure-devops"],
      "enabled": true,
      "environment": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/<org>",
        "AZURE_DEVOPS_AUTH_METHOD": "pat",
        "AZURE_DEVOPS_PAT": "${AZDO_PAT}"
      }
    }
  }
}
```

> El nombre exacto de las claves puede variar según la versión de opencode. Si tu versión usa otro esquema, mantené los mismos valores de entorno y marcá como **a confirmar** cualquier campo que no coincida con tu instalación.

## Antigravity

En la configuración de MCP de Antigravity (panel de MCP servers / archivo de configuración MCP), registrá un server nuevo con el mismo patrón:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@tiberriver256/mcp-server-azure-devops"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/<org>",
        "AZURE_DEVOPS_AUTH_METHOD": "pat",
        "AZURE_DEVOPS_PAT": "${AZDO_PAT}"
      }
    }
  }
}
```

Después de guardar, reiniciá/recargá los MCP servers en Antigravity y confirmá que el server aparece activo.

## Gemini CLI

En `~/.gemini/settings.json` (por máquina; el token sigue saliendo de la variable de entorno, nunca del archivo):

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@tiberriver256/mcp-server-azure-devops"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/{{AZURE_ORG}}",
        "AZURE_DEVOPS_AUTH_METHOD": "pat",
        "AZURE_DEVOPS_PAT": "$AZDO_PAT"
      }
    }
  }
}
```

Se verifica con `/mcp` dentro de la sesión. Si el `$AZDO_PAT` no se expande en tu versión, usá la variante con `env` del sistema (ver [[06-troubleshooting]]).

## Método alternativo: con tu cuenta logueada (Azure CLI, SIN PAT)

El MCP soporta **3 métodos** de `AZURE_DEVOPS_AUTH_METHOD`. El de arriba es `pat` (token guardado). Los otros dos **no usan un token**: usan tu **cuenta ya logueada** vía Azure CLI.

| Método | Qué usa | Requisito | Dónde funciona |
|---|---|---|---|
| `pat` | Token guardado (`AZDO_PAT`) | Crear/guardar/rotar el PAT | Cloud **y** on-prem (Azure DevOps Server) |
| `azure-cli` | Tu sesión de Azure CLI | `az login` hecho (CLI instalada) | Solo cloud (`dev.azure.com`) |
| `azure-identity` | DefaultAzureCredential (cadena env → managed identity → CLI → browser) | En la práctica, `az login` | Solo cloud |

Config sin token (Claude Code) — reemplaza al bloque `pat` (fijate que **no** lleva `AZURE_DEVOPS_PAT`):

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@tiberriver256/mcp-server-azure-devops"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/<org>",
        "AZURE_DEVOPS_AUTH_METHOD": "azure-cli"
      }
    }
  }
}
```

Antes de usarlo: instalá **Azure CLI** y hacé `az login` (abre el navegador → login corporativo con MFA). No necesitás `AZDO_PAT` ni los pasos [[01-crear-pat-azure]] / [[02-guardar-token-envvar]].

> **¿Cuál conviene?** En dos líneas: **para un funcional en su máquina (interactivo) → `azure-cli`** (usa tu cuenta, sin token que guardar/rotar, con MFA/SSO); **para automatización headless / CI / cron o Azure DevOps Server on-prem → `pat`**.

## Checklist de verificación

- [ ] La variable `AZDO_PAT` está cargada en el entorno (terminal nueva).
- [ ] La config del MCP usa `${AZDO_PAT}` (referencia, **no** el valor).
- [ ] `AZURE_DEVOPS_ORG_URL` apunta a tu organización real (`<org>` reemplazado).
- [ ] El server `azure-devops` figura **conectado** en tu herramienta.
- [ ] Una prueba de lectura funciona: pedile a la IA "listá los proyectos" o "traé la tarjeta N".

## Recuadro — Ejemplo (genérico)

En un workspace de ejemplo, el server figura en `.mcp.json` como `azure-devops` y expone herramientas de lectura (`list_work_items`, `get_work_item`, `search_work_items`, `get_work_item_comments`, `list_projects`) que las skills usan **read-only** sobre los boards `<board>`. Con las 3 variables alcanza; el certificado (`NODE_EXTRA_CA_CERTS`) solo haría falta si la red interceptara el TLS de `dev.azure.com`.

## Siguiente paso

Usar la integración en el día a día → [[04-automatizar-con-ia]].
