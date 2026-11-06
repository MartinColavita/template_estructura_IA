#!/usr/bin/env bash
# Prueba si un modelo RESPETA las reglas de Azure de este repo. SOLO LECTURA.
#
#   bash bin/probar-reglas.sh                         (Gemini CLI, todos los casos)
#   bash bin/probar-reglas.sh --herramienta claude    (Claude Code)
#   bash bin/probar-reglas.sh --modelo <modelo>       (el que acepte la herramienta)
#   bash bin/probar-reglas.sh --casos 3,6             (solo esos casos)
#
# Tres estados, nunca dos:  0 = todos los chequeos OK   1 = alguno FALLA   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/probar-reglas.py, una sola vez (mismo
# patron que el Doctor). El porque, en el encabezado de ese archivo.
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$AQUI/probar-reglas.py"

if [ ! -f "$MOTOR" ]; then
  echo "probar-reglas: no encuentro el motor en $MOTOR" >&2
  exit 2
fi

# Se prueba en orden; la primera que exista, gana.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

# Sin Python no se pudo medir: SIN DATOS (2), nunca OK.
if [ -z "$PY" ]; then
  echo "SIN DATOS -- hace falta Python 3 en el PATH (probe python3, python y py)." >&2
  exit 2
fi

PYTHONIOENCODING=utf-8 "$PY" "$MOTOR" "$@"
CODIGO=$?

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo medir.
case "$CODIGO" in
  0|1|2) exit "$CODIGO" ;;
  *)     exit 2 ;;
esac
