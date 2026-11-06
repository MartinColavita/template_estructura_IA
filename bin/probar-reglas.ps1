# Prueba si un modelo RESPETA las reglas de Azure de este repo. SOLO LECTURA.
#
#   .\bin\probar-reglas.ps1                          (Gemini CLI, todos los casos)
#   .\bin\probar-reglas.ps1 --herramienta claude     (Claude Code)
#   .\bin\probar-reglas.ps1 --modelo <modelo>        (el que acepte la herramienta)
#   .\bin\probar-reglas.ps1 --casos 3,6              (solo esos casos)
#
# Gemelo de probar-reglas.sh: mismos codigos de salida.
#   0 = todos los chequeos OK   1 = alguno FALLA   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/probar-reglas.py, una sola vez (mismo
# patron que el Doctor). ASCII puro, sin acentos: asi no hace falta BOM.
#
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\bin\probar-reglas.ps1 ...

$ErrorActionPreference = 'Stop'

$aqui  = Split-Path -Parent $MyInvocation.MyCommand.Path
$motor = Join-Path $aqui 'probar-reglas.py'

if (-not (Test-Path $motor)) {
    Write-Output "probar-reglas: no encuentro el motor en $motor"
    exit 2
}

# Se prueba en orden; la primera que exista, gana.
$py = $null
foreach ($c in @('python', 'python3', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}

# Sin Python no se pudo medir: SIN DATOS (2), nunca OK.
if (-not $py) {
    Write-Output 'SIN DATOS -- hace falta Python 3 en el PATH (probe python, python3 y py).'
    exit 2
}

$env:PYTHONIOENCODING = 'utf-8'

# 'Continue' alrededor de la llamada, no 'Stop': en Windows PowerShell 5.1, con 'Stop', una
# linea de Python en stderr corta el script con 1 -que aca es FALLA- cuando quien lo llama
# junta la salida con 2>&1. Mismo motivo que en verificar-sello.ps1.
$ErrorActionPreference = 'Continue'
& $py $motor @args
$codigo = $LASTEXITCODE

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo medir.
if ($codigo -ne 0 -and $codigo -ne 1 -and $codigo -ne 2) { exit 2 }
exit $codigo
