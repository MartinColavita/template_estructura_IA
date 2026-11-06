#!/usr/bin/env bash

# {{PROYECTO}} - Sincronizador de Agentes (espejos versionados)
# Copia la fuente versionada cerebro-digital/configuracion-ia/agentes/
# hacia los DOS espejos locales (NO versionados: cada dev los genera una vez
# despues de clonar; ver INSTALACION.md):
#   .agents/agents/  -> lo lee Antigravity (y opencode lo auto-descubre)
#   .claude/agents/  -> lo lee Claude Code (subagentes project-scoped)
# Mismo mecanismo que sync-skills.sh. Herramienta del MANTENEDOR: regenera
# los espejos ANTES de commitear cuando cambian los agentes. El hook
# pre-commit (.githooks/) lo verifica al commitear, si esta activado
# (git config core.hooksPath .githooks). El que clona NO necesita correr
# esto. Idempotente: rehace los espejos desde cero en cada corrida.

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/cerebro-digital/configuracion-ia/agentes"

echo -e "\033[36m=============================================\033[0m"
echo -e "\033[36m   {{PROYECTO}} - Sincronizador de Agentes (espejos)\033[0m"
echo -e "\033[36m=============================================\033[0m"

if [ ! -d "$SRC" ]; then
  echo -e "\033[31mERROR: no existe la fuente: $SRC\033[0m"
  exit 1
fi

for DST in "$ROOT/.agents/agents" "$ROOT/.claude/agents"; do
  rm -rf "$DST"
  mkdir -p "$DST"
  cp -r "$SRC/." "$DST/"
  N=$(find "$DST" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
  echo -e "\033[32mOK: espejo regenerado con $N agentes en ${DST#$ROOT/}\033[0m"
done
