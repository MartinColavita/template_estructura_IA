# MCP de GitLab — leer (y, si el equipo lo habilita, comentar) los Merge Requests

Este MCP existe para que el asistente pueda **leer los Merge Requests y sus notas de revisión**
de los repositorios de código, sin salir de la sesión. Es lo que usan el comentario de cierre de
una Tarea ([[comentar-tarea]]), el orquestador de desarrollo y la revisión de un Merge Request.

> Si además el proyecto sigue skills de un tercero publicadas en un repositorio de GitLab, este
> mismo MCP es el que las lee en el momento de usarlas (ver `DEPENDENCIAS-EXTERNAS.md`).

---

## Qué necesitás

| | |
|---|---|
| Un **token de API de GitLab**, de tu usuario | Ver abajo |
| Red de la organización o VPN, si el servidor es interno | Casi siempre lo es |
| El token en una **variable de entorno**, nunca en un archivo del repo | Ver abajo |

---

## 1. El token

En `https://<host-gitlab>` → tu perfil → **Access Tokens**.

| Campo | Valor |
|---|---|
| Nombre | algo que se entienda, p. ej. `lectura-merge-requests` |
| Vencimiento | el más corto que te sirva |
| **Scopes** | **`read_api`** y **`read_repository`** para leer. **`api`** sólo si el equipo decidió que el asistente **comente** Merge Requests (segundo servidor, abajo) |

**Dos servidores, dos tokens.** Por defecto se configura **uno de sólo lectura**. Si el equipo
habilita que el asistente cree o comente Merge Requests, se configura **un segundo servidor**
con un token de escritura y `GITLAB_PERMISSION_MODE` sin `readonly`; nunca se "sube" el permiso
del primero. Dos barreras, no una.

> El token es **tuyo y personal**. No se comparte, no se pega en un chat, no se manda por
> correo. Si se filtró, se revoca y se saca uno nuevo — borrarlo del lugar donde se filtró no
> alcanza.

## 2. Guardarlo

**Windows (PowerShell), permanente para tu usuario:**

```powershell
[Environment]::SetEnvironmentVariable("GITLAB_TOKEN", "<tu-token>", "User")
```

Cerrá y abrí **el programa entero** desde el que corrés el asistente (IDE, terminal suelta). La
terminal integrada de un IDE hereda las variables que el IDE tenía **al abrirse**: cerrar sólo la
pestaña de la terminal **no alcanza**. Es la causa más común de «de la nada dice que falta el token».

**Linux / macOS**, en tu `~/.bashrc` o `~/.zshrc`:

```bash
export GITLAB_TOKEN="<tu-token>"
```

**Verificar que quedó** (esto **no** muestra el valor):

```bash
[ -n "$GITLAB_TOKEN" ] && echo "OK, definida (${#GITLAB_TOKEN} caracteres)" || echo "NO definida"
```

## 3. Configurar el servidor MCP

**La configuración de MCP NO se versiona** — es la convención de este repositorio, igual que con
el de Azure DevOps. `.mcp.json` y `.agents/mcp_config.json` están en el `.gitignore` a propósito.
Lo que se versiona es **este documento**; el archivo lo arma cada uno en su máquina.

### Gemini CLI — `~/.gemini/settings.json`

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@zereight/mcp-gitlab@2.3.22"],
      "env": {
        "GITLAB_API_URL": "https://<host-gitlab>/api/v4",
        "GITLAB_PERSONAL_ACCESS_TOKEN": "$GITLAB_TOKEN",
        "GITLAB_PERMISSION_MODE": "readonly",
        "NODE_EXTRA_CA_CERTS": "$CA_CERT_INTERNO",
        "PORT": "3002"
      }
    }
  }
}
```

> **Ojo con Gemini CLI:** por seguridad **no hereda el entorno del shell** y redacta las variables
> que parecen secretos. Por eso el token se declara explícitamente en `env` con expansión
> `"$GITLAB_TOKEN"` — **nunca con el valor escrito**.

> **La versión va fija** (`@2.3.22`): `npx -y` sin versión baja y corre la última publicada en cada arranque, con tu token en el entorno. Para subir de versión, mirá qué cambió en el repositorio del paquete y cambiá el número.

### Claude Code — a nivel usuario (recomendado)

```bash
claude mcp add-json --scope user gitlab '{"command":"npx","args":["-y","@zereight/mcp-gitlab@2.3.22"],"env":{"GITLAB_API_URL":"https://<host-gitlab>/api/v4","GITLAB_PERSONAL_ACCESS_TOKEN":"${GITLAB_TOKEN}","GITLAB_PERMISSION_MODE":"readonly","NODE_EXTRA_CA_CERTS":"${CA_CERT_INTERNO}","PORT":"3002"}}'
```

Queda en `~/.claude.json`, que no se versiona, y anda **desde cualquier carpeta**: este repo, la
carpeta que agrupa los repos o un worktree de código.

**Alternativa:** el mismo bloque dentro de un `.mcp.json` en la raíz de este repo (no versionado).
Así **sólo** aparece si abrís el asistente parado en este repo.

### Las tres variables que no son obvias

| Variable | Por qué va |
|---|---|
| Token **por referencia** (`${GITLAB_TOKEN}` / `$GITLAB_TOKEN`) | Nunca el valor escrito: si el token se renueva, la configuración sigue andando, y no queda copiado en un archivo |
| `NODE_EXTRA_CA_CERTS` | Sólo si el GitLab usa un certificado de una autoridad interna. Node **no** usa el almacén de certificados del sistema: sin esto da `SELF_SIGNED_CERT_IN_CHAIN`, que en la sesión se ve como «fetch failed». Apunta al mismo `.pem` de `CA_CERT_INTERNO` ([[02-guardar-token-envvar]] del MCP de Azure). Si el certificado es público, se omite |
| `PORT` | El servidor valida esta variable aunque trabaje por stdio. La terminal de algunos IDE trae `PORT=0`, y con eso el servidor no arranca («Connection closed»). `3002` es su valor por defecto |

**Si conectar tarda:** `npx -y` baja el paquete en el primer arranque y puede pasarse del tiempo
de espera del asistente. Dos salidas: instalarlo una vez de forma global y usar `"command": "node"`
con la ruta a su `build/index.js`, o subir el tiempo de espera de Claude con `MCP_TIMEOUT=60000`.

**`GITLAB_PERMISSION_MODE=readonly` no es decorativo:** aunque el token se equivoque y tenga
permisos de más, el servidor no expone herramientas de escritura.

### Alternativa: el MCP oficial de GitLab

GitLab tiene su propio servidor MCP en `https://<host-gitlab>/api/v4/mcp`, con autenticación
OAuth, en las versiones recientes. Depende de qué versión corra la instancia — ⚠ confirmarlo con
quien administra GitLab. Mientras tanto, el de la comunidad.

## 4. Probar que anda

En el asistente, `/mcp` tiene que decir *connected* para `gitlab`, y una consulta de prueba
(por ejemplo, «¿quién soy en GitLab?» o «listá los Merge Requests abiertos de `<repo>`») tiene
que responder.

---

## Si no anda

| Síntoma | Casi siempre es |
|---|---|
| `404 Project Not Found` | **Falta el token o está mal.** GitLab esconde los repos privados con un 404, no con un 403 |
| `401 Unauthorized` | Token vencido o revocado. Pasa «de un día para el otro» el día que vence: mirá la fecha en **Access Tokens** |
| `Missing environment variables`, o el MCP dice que falta el token | El programa se abrió **antes** de cargar la variable: reiniciá el IDE entero, no sólo la terminal |
| El MCP de GitLab no aparece en la lista | Está en el `.mcp.json` de este repo y abriste el asistente desde otra carpeta: configuralo a nivel usuario |
| `Connection closed` apenas arranca | `PORT=0` heredado de la terminal del IDE (fijá `PORT`), o `npx` tardó más que el tiempo de espera |
| `fetch failed` o `SELF_SIGNED_CERT_IN_CHAIN` | Falta `NODE_EXTRA_CA_CERTS` con el certificado interno |
| `403 Forbidden` | Al token le falta `read_api` / `read_repository` |
| Se cuelga o no resuelve el host | **No estás en la red de la organización ni en la VPN** |

## Qué pasa si no lo configurás

**El proyecto funciona igual.** Los Merge Requests se abren y se leen a mano en GitLab, y el
comentario de cierre de una Tarea lleva el link que arma el orquestador. Lo que dependa de leer
el servidor y no se pudo leer va `⚠ sin dato` o `SIN DATOS`, nunca inventado.

---

## Barreras

- **Sólo lectura por defecto.** Escribir en GitLab (crear o comentar un Merge Request) exige el
  segundo servidor, la decisión del equipo y un "sí" explícito por cada escritura.
- **El token nunca en un archivo versionado**, ni en un log, ni en un mensaje de commit, ni en
  la descripción de un Merge Request. **Y tampoco escrito tal cual en tu configuración local**:
  siempre por referencia a la variable.
- **Un token por persona.** Nada de un token compartido de equipo: se pierde la trazabilidad de
  quién leyó qué, y revocarlo afecta a todos.
- **Nunca se pega contenido de un repositorio de terceros dentro de este repositorio.** Se lee,
  se usa, se descarta.
