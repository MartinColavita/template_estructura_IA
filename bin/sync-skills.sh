#!/usr/bin/env bash

# {{PROYECTO}} - Sincronizador de Skills (espejos versionados)
# Copia la fuente versionada cerebro-digital/configuracion-ia/skills/
# hacia los DOS espejos versionados (viajan en el clone):
#   .agents/skills/  -> lo lee Antigravity (y opencode lo auto-descubre)
#   .claude/skills/  -> lo lee Claude Code (skills project-scoped, nativas)
# Herramienta del MANTENEDOR: regenera los espejos ANTES de commitear cuando
# cambian las skills. El hook pre-commit (.githooks/) lo verifica al commitear,
# si esta activado (git config core.hooksPath .githooks). El que clona NO
# necesita correr esto. Idempotente: rehace los espejos desde cero en cada corrida.

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/cerebro-digital/configuracion-ia/skills"

echo -e "\033[36m=============================================\033[0m"
echo -e "\033[36m   {{PROYECTO}} - Sincronizador de Skills (espejos)\033[0m"
echo -e "\033[36m=============================================\033[0m"

if [ ! -d "$SRC" ]; then
  echo -e "\033[31mERROR: no existe la fuente: $SRC\033[0m"
  exit 1
fi

for DST in "$ROOT/.agents/skills" "$ROOT/.claude/skills"; do
  rm -rf "$DST"
  mkdir -p "$DST"
  cp -r "$SRC/." "$DST/"
  N=$(find "$DST" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
  echo -e "\033[32mOK: espejo regenerado con $N skills en ${DST#$ROOT/}\033[0m"
done
