#!/usr/bin/env bash
# Analisis MECANICO del SET de Tareas de una Historia (Escenarios del padre contra las filas
# de todas las Tareas, punteros "es de #X", reglas, contratos, dependencias, test de integracion).
# SOLO LECTURA.
#
#   bash bin/analizar-tareas.sh --historia <criterios.html> <tarea1.html> [<tarea2.html> ...]
#                               [--ids <mapa.json>] [--descripcion <descripcion.html>] [--json] [--salida <archivo>]
#
# Tres estados, nunca dos:  0 = sin hallazgos   1 = hallazgos o no auditables   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/analizar-tareas.py, una sola vez (mismo
# patron que el Doctor y verificar-sello). El porque, en el encabezado de ese archivo.
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$AQUI/analizar-tareas.py"

if [ ! -f "$MOTOR" ]; then
  echo "analizar-tareas: no encuentro el motor en $MOTOR" >&2
  exit 2
fi

# Se prueba en orden; la primera que exista, gana.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

# Sin Python no se pudo mirar: SIN DATOS (2), nunca "sin hallazgos".
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
