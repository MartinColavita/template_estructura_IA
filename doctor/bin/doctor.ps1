# Doctor de {{PROYECTO}} - envoltorio para PowerShell (el shell primario del equipo).
#
# Es FINO a proposito: toda la logica vive en doctor/doctor.py, una sola vez.
# Mantener dos implementaciones (una en bash y otra en PowerShell) es exactamente
# como se desincronizan las cosas, y este proyecto ya tiene cicatrices de eso.
#
# Uso:
#   .\doctor\bin\doctor.ps1                           informe completo
#   .\doctor\bin\doctor.ps1 --json                    resumen por consola
#   .\doctor\bin\doctor.ps1 --solo espejos,conteos    solo esas sondas
#
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\doctor\bin\doctor.ps1

$ErrorActionPreference = 'Stop'

$aqui  = Split-Path -Parent $MyInvocation.MyCommand.Path
$motor = Join-Path $aqui '..\doctor.py'

if (-not (Test-Path $motor)) {
    Write-Error "doctor: no encuentro el motor en $motor"
    exit 1
}

# Se prueba en orden; la primera que exista, gana.
$py = $null
foreach ($c in @('python', 'python3', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}

if (-not $py) {
    Write-Error @'
doctor: hace falta Python 3 en el PATH (probe python, python3 y py).
        No hay plan B: el motor es Python, justamente para no duplicarlo en dos shells.
'@
    exit 1
}

# UTF-8 explicito: sin esto la salida con acentos sale rota en la consola de Windows.
$env:PYTHONIOENCODING = 'utf-8'

& $py $motor @args
exit $LASTEXITCODE
