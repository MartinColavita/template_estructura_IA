#!/usr/bin/env bash
# Modo lote (planificar-lote): la parte MECANICA, igual en cada sesion. No escribe en el board.
#
#   bash bin/lote.sh preparar <tema> --ficha <ruta.md> [--fecha AAAAMMDD] [--raiz-output <dir>]
#   bash bin/lote.sh item <carpeta> --clave T-01 --tipo Tarea --accion ALTA --titulo "..." [...]
#   bash bin/lote.sh mision <carpeta> redactar|auditar|corregir <clave> [<clave> ...]
#   bash bin/lote.sh auditar <carpeta>
#   bash bin/lote.sh cierre <carpeta>
#   bash bin/lote.sh ids <carpeta> [--mapa mapa-ids.json]
#   bash bin/lote.sh comparar <archivo_auditado> <archivo_azure> [--mapa mapa-ids.json]
#   bash bin/lote.sh tiempos <carpeta> [<fase> inicio|fin]
#   bash bin/lote.sh estado <carpeta>
#
# Codigos:  0 = listo   1 = hay algo que arreglar   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/lote.py, una sola vez (mismo patron que
# verificar-sello). El porque y el detalle de cada subcomando, en el encabezado de ese archivo.
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$AQUI/lote.py"

if [ ! -f "$MOTOR" ]; then
  echo "lote: no encuentro el motor en $MOTOR" >&2
  exit 2
fi

# Se prueba en orden; la primera que exista, gana.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

# Sin Python no se pudo hacer nada: SIN DATOS (2), nunca listo.
if [ -z "$PY" ]; then
  echo "SIN DATOS -- hace falta Python 3 en el PATH (probe python3, python y py)." >&2
  exit 2
fi

PYTHONIOENCODING=utf-8 "$PY" -B "$MOTOR" "$@"
CODIGO=$?

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo hacer.
case "$CODIGO" in
  0|1|2) exit "$CODIGO" ;;
  *)     exit 2 ;;
esac
