---
id: integracion-azure-mcp-02-guardar-token
tipo: guia
estado: F-Draft
modulo: integracion-azure-mcp
title: "Guardar el token como variable de entorno"
author: equipo
tags: [azure-devops, pat, env-var, secretos, seguridad, setx]
last_updated: 2026-08-26
---

# Guardar el token como variable de entorno

Ya tenés el PAT copiado de [[01-crear-pat-azure]]. Ahora hay que guardarlo de forma que **la IA nunca lo vea** pero el **servidor MCP sí lo pueda leer** al arrancar. La forma correcta es una **variable de entorno** llamada `AZDO_PAT`.

## Por qué así (y no en un archivo)

- El servidor MCP lee la variable de entorno **en cada corrida**: no necesita que el valor esté escrito en ningún `.md`, `.json` ni en el chat.
- Si el token estuviera en un archivo que la IA lee (un CLAUDE.md, un doc, un prompt), **entraría al contexto** del modelo — y eso es exactamente lo que hay que evitar. El valor no debe entrar al contexto de la IA nunca.
- En la config del MCP (paso [[03-configurar-mcp]]) sólo se escribe **`${AZDO_PAT}`** (una referencia), no el valor. Así el archivo de config es seguro para compartir o versionar.

> Regla: en los archivos que la IA lee va la **referencia** `${AZDO_PAT}`; el **valor real** vive sólo en la variable de entorno de tu máquina.

## Opción A — Windows con `setx` (persistente)

`setx` guarda la variable de forma permanente para tu usuario:

```powershell
setx AZDO_PAT "PEGA-AQUI-TU-TOKEN"
```

Importante:
- `setx` afecta a las **terminales nuevas**, no a la que tenés abierta. Cerrá y volvé a abrir la terminal (o reiniciá la herramienta de IA) para que tome el valor.
- Verificá en una terminal **nueva** que quedó cargada (sin imprimir el valor completo si hay gente mirando):

```powershell
if ($env:AZDO_PAT) { "AZDO_PAT cargada (longitud: $($env:AZDO_PAT.Length))" } else { "NO cargada" }
```

- Solo si tu red intercepta el TLS de `dev.azure.com` (no es lo habitual), necesitarías además la variable opcional `CA_CERT_INTERNO` apuntando al certificado de tu red (ver [[03-configurar-mcp]]):

```powershell
setx CA_CERT_INTERNO "C:\ruta\a\ca-bundle-interno.pem"
```

## Opción B — `secrets.env` + loader (multiplataforma)

Si preferís juntar tus secretos en un archivo local (fuera de todo repo, **gitignored**), usá un `secrets.env`:

```
# secrets.env  — archivo LOCAL, NUNCA se versiona ni se comparte
AZDO_PAT=PEGA-AQUI-TU-TOKEN
# CA_CERT_INTERNO solo si tu red intercepta el TLS (opcional, normalmente no hace falta):
# CA_CERT_INTERNO=/ruta/a/certificado-de-tu-red.pem
```

Y lo cargás con un **loader** antes de levantar la IA:

- Bash / Linux / macOS:

```bash
set -a; source ./secrets.env; set +a
```

- PowerShell:

```powershell
Get-Content .\secrets.env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
  $k, $v = $_ -split '=', 2
  Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim()
}
```

Reglas para el `secrets.env`:
- Va en `.gitignore` (o en `.git/info/exclude`) **siempre**. Nunca al repo.
- No lo pegues en el chat ni se lo pases a la IA como archivo a leer.
- Es **por usuario**: cada persona tiene el suyo con su propio PAT.

## Lo que NO hay que hacer (nunca)

- Escribir el token en un `.mcp.json`, `CLAUDE.md`, `AGENTS.md`, un doc de `conocimiento/` o cualquier archivo que la IA pueda leer.
- Pegar el token en el chat para "que la IA lo use". El MCP lo lee de la variable de entorno, no del chat.
- Guardarlo en texto plano en un lugar compartido (Teams, mail, wiki).
- Reusar el mismo token entre varias personas.

## Recuadro — Ejemplo (genérico)

En un workspace de ejemplo, los secretos por usuario viven en un `secrets.env` en la raíz, **gitignored**, cargado por un loader antes de abrir la herramienta. El ZIP que se comparte a mano con el otro dev se arma **sin** ese `secrets.env` (los tokens son personales). En la config del MCP sólo figura `${AZDO_PAT}` — nunca el valor.

## Siguiente paso

Registrar el servidor MCP en tu herramienta → [[03-configurar-mcp]].
