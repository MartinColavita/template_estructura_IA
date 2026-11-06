# Modo lote (planificar-lote): la parte MECANICA, igual en cada sesion. No escribe en el board.
#
#   .\bin\lote.ps1 preparar <tema> --ficha <ruta.md> [--fecha AAAAMMDD] [--raiz-output <dir>]
#   .\bin\lote.ps1 item <carpeta> --clave T-01 --tipo Tarea --accion ALTA --titulo "..." [...]
#   .\bin\lote.ps1 mision <carpeta> redactar|auditar|corregir <clave> [<clave> ...]
#   .\bin\lote.ps1 auditar <carpeta>
#   .\bin\lote.ps1 cierre <carpeta>
#   .\bin\lote.ps1 ids <carpeta> [--mapa mapa-ids.json]
#   .\bin\lote.ps1 comparar <archivo_auditado> <archivo_azure> [--mapa mapa-ids.json]
#   .\bin\lote.ps1 tiempos <carpeta> [<fase> inicio|fin]
#   .\bin\lote.ps1 estado <carpeta>
#
# Gemelo de lote.sh: mismos codigos de salida.
#   0 = listo   1 = hay algo que arreglar   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/lote.py, una sola vez (mismo patron que
# verificar-sello). ASCII puro, sin acentos: asi no hace falta BOM.
#
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\bin\lote.ps1 ...

$ErrorActionPreference = 'Stop'

$aqui  = Split-Path -Parent $MyInvocation.MyCommand.Path
$motor = Join-Path $aqui 'lote.py'

if (-not (Test-Path $motor)) {
    Write-Output "lote: no encuentro el motor en $motor"
    exit 2
}

# Se prueba en orden; la primera que exista, gana.
$py = $null
foreach ($c in @('python', 'python3', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}

# Sin Python no se pudo hacer nada: SIN DATOS (2), nunca listo.
if (-not $py) {
    Write-Output 'SIN DATOS -- hace falta Python 3 en el PATH (probe python, python3 y py).'
    exit 2
}

$env:PYTHONIOENCODING = 'utf-8'

# 'Continue' alrededor de la llamada, no 'Stop': en Windows PowerShell 5.1, con 'Stop', una
# linea de Python en stderr (un error de uso) corta el script con 1 -que es 'hay algo que
# arreglar'- cuando quien lo llama junta la salida con 2>&1 (postmortem del 24/09/2026).
$ErrorActionPreference = 'Continue'
& $py -B $motor @args
$codigo = $LASTEXITCODE

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo hacer.
if ($codigo -ne 0 -and $codigo -ne 1 -and $codigo -ne 2) { exit 2 }
exit $codigo
