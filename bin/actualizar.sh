#!/usr/bin/env bash

# {{PROYECTO}} - Actualizar todo (un solo comando).
# Trae lo ultimo del repo y corre el instalador (bin/instalar.py): hook pre-commit activo,
# espejos de agentes materializados, espejos de skills identicos a la fuente y cada SKILL.md
# dentro de la especificacion. Correr despues de (o en vez de) un 'git pull'. Idempotente.

set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo -e "[36m=============================================[0m"
echo -e "[36m   {{PROYECTO}} - Actualizar todo[0m"
echo -e "[36m=============================================[0m"

echo "[1/2] Trayendo lo ultimo (git pull)..."
git pull

echo "[2/2] Instalador (hook, espejos de agentes, espejos de skills, especificacion de skills)..."
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "No encuentro Python 3: instalalo y corre  python -I bin/instalar.py"
  exit 1
fi
exec "$PY" -I bin/instalar.py
