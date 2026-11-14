#!/usr/bin/env bash

# {{PROYECTO}} - Sincronizador de Agentes (espejos)
# Regenera .agents/agents/ y .claude/agents/ (no se versionan) desde cerebro-digital/configuracion-ia/agentes/.
# Herramienta del MANTENEDOR. Envoltorio de bin/sync-espejos.py (el como, en su encabezado); necesita Python 3.

set -o pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' >/dev/null 2>&1; then
    exec "$c" -I "$ROOT/bin/sync-espejos.py" agentes "$@"
  fi
done
echo "ERROR: hace falta Python 3 para regenerar los espejos (bin/sync-espejos.py)."
exit 2
