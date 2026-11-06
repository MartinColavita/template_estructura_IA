# Auditoria MECANICA de una Historia de usuario (lo que de auditar-historia es conteo). SOLO LECTURA.
#
#   .\bin\auditar-historia.ps1 --criterios <criterios.html> [--descripcion <descripcion.html>]
#                              [--ficha <ruta.md>] [--flujo F-nn] [--json] [--salida <archivo>]
#
# Gemelo de auditar-historia.sh: mismos codigos de salida.
#   0 = SIN HALLAZGOS   1 = CON HALLAZGOS (o NO AUDITABLE)   2 = SIN DATOS
#
# Es FINO a proposito: toda la logica vive en bin/auditar-historia.py, una sola vez (mismo
# patron que el Doctor). ASCII puro, sin acentos: asi no hace falta BOM.
#
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\bin\auditar-historia.ps1 ...

$ErrorActionPreference = 'Stop'

$aqui  = Split-Path -Parent $MyInvocation.MyCommand.Path
$motor = Join-Path $aqui 'auditar-historia.py'

if (-not (Test-Path $motor)) {
    Write-Output "auditar-historia: no encuentro el motor en $motor"
    exit 2
}

# Se prueba en orden; la primera que exista, gana.
$py = $null
foreach ($c in @('python', 'python3', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}

# Sin Python no se pudo mirar: SIN DATOS (2), nunca SIN HALLAZGOS.
if (-not $py) {
    Write-Output 'SIN DATOS -- hace falta Python 3 en el PATH (probe python, python3 y py).'
    exit 2
}

$env:PYTHONIOENCODING = 'utf-8'

# 'Continue' alrededor de la llamada, no 'Stop': en Windows PowerShell 5.1, con 'Stop', una
# linea de Python en stderr (un error de uso) corta el script con 1 -que es CON HALLAZGOS-
# cuando quien lo llama junta la salida con 2>&1 (mismo caso que verificar-sello.ps1).
$ErrorActionPreference = 'Continue'
& $py $motor @args
$codigo = $LASTEXITCODE

# Solo 0, 1 y 2 significan algo. Cualquier otro codigo es que no se pudo mirar.
if ($codigo -ne 0 -and $codigo -ne 1 -and $codigo -ne 2) { exit 2 }
exit $codigo
