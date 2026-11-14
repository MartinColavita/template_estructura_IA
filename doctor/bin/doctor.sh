#!/usr/bin/env bash
# Doctor de {{PROYECTO}} — envoltorio para bash / Git Bash / WSL / macOS / Linux.
#
# Es FINO a proposito: toda la logica vive en doctor/doctor.py, una sola vez.
# Mantener dos implementaciones (una en bash y otra en PowerShell) es exactamente
# como se desincronizan las cosas, y este proyecto ya tiene cicatrices de eso.
#
# Uso:
#   doctor/bin/doctor.sh                      informe completo
#   doctor/bin/doctor.sh --json               resumen por consola, sin escribir archivo
#   doctor/bin/doctor.sh --solo espejos,conteos    solo esas sondas
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$AQUI/../doctor.py"

if [ ! -f "$MOTOR" ]; then
  echo "doctor: no encuentro el motor en $MOTOR" >&2
  exit 1
fi

# Se prueba en orden; la primera que exista, gana.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

if [ -z "$PY" ]; then
  echo "doctor: hace falta Python 3 en el PATH (probe python3, python y py)." >&2
  echo "        No hay plan B: el motor es Python, justamente para no duplicarlo en dos shells." >&2
  exit 1
fi

# UTF-8 explicito: sin esto, en Windows la salida con acentos rompe.
PYTHONIOENCODING=utf-8 "$PY" "$MOTOR" "$@"
