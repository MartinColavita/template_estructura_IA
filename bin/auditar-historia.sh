#!/usr/bin/env bash
# Auditoria MECANICA de una Historia de usuario (lo que de auditar-historia es conteo). SOLO LECTURA.
#
#   bash bin/auditar-historia.sh --criterios <criterios.html> [--descripcion <descripcion.html>]
#                                [--ficha <ruta.md>] [--flujo F-nn] [--json] [--salida <archivo>]
#
# Tres estados, nunca dos:  0 = SIN HALLAZGOS   1 = CON HALLAZGOS (o NO AUDITABLE)   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/auditar-historia.py, una sola vez (mismo
# patron que el Doctor). El porque de cada chequeo, en el encabezado de ese archivo.
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$AQUI/auditar-historia.py"

if [ ! -f "$MOTOR" ]; then
  echo "auditar-historia: no encuentro el motor en $MOTOR" >&2
  exit 2
fi

# Se prueba en orden; la primera que exista, gana.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

# Sin Python no se pudo mirar: SIN DATOS (2), nunca SIN HALLAZGOS.
if [ -z "$PY" ]; then
  echo "SIN DATOS -- hace falta Python 3 en el PATH (probe python3, python y py)." >&2
  exit 2
fi

PYTHONIOENCODING=utf-8 "$PY" "$MOTOR" "$@"
CODIGO=$?

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo mirar.
case "$CODIGO" in
  0|1|2) exit "$CODIGO" ;;
  *)     exit 2 ;;
esac
