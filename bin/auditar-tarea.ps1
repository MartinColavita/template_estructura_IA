# Auditoria MECANICA de UNA Tarea (secciones, numeracion, Escenarios del padre contra la
# tabla, reglas, enlaces, HTML, guardarrailes, Modos de falla, Datos a confirmar, tamano).
# SOLO LECTURA.
#
#   .\bin\auditar-tarea.ps1 <tarea.html> [--historia <criterios.html>] [--json] [--salida <archivo>]
#
# Gemelo de auditar-tarea.sh: mismos codigos de salida.
#   0 = sin hallazgos   1 = hallazgos o no auditables   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/auditar-tarea.py, una sola vez (mismo
# patron que el Doctor y verificar-sello). ASCII puro, sin acentos: asi no hace falta BOM.
#
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\bin\auditar-tarea.ps1 ...

$ErrorActionPreference = 'Stop'

$aqui  = Split-Path -Parent $MyInvocation.MyCommand.Path
$motor = Join-Path $aqui 'auditar-tarea.py'

if (-not (Test-Path $motor)) {
    Write-Output "auditar-tarea: no encuentro el motor en $motor"
    exit 2
}

# Se prueba en orden; la primera que exista, gana.
$py = $null
foreach ($c in @('python', 'python3', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}

# Sin Python no se pudo mirar: SIN DATOS (2), nunca "sin hallazgos".
if (-not $py) {
    Write-Output 'SIN DATOS -- hace falta Python 3 en el PATH (probe python, python3 y py).'
    exit 2
}

$env:PYTHONIOENCODING = 'utf-8'

# 'Continue' alrededor de la llamada, no 'Stop': en Windows PowerShell 5.1, con 'Stop', una
# linea de Python en stderr (un error de uso) corta el script con 1 -que es "hay hallazgos"-
# cuando quien lo llama junta la salida con 2>&1. Mismo motivo que en verificar-sello.ps1.
$ErrorActionPreference = 'Continue'
& $py $motor @args
$codigo = $LASTEXITCODE

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo mirar.
if ($codigo -ne 0 -and $codigo -ne 1 -and $codigo -ne 2) { exit 2 }
exit $codigo
