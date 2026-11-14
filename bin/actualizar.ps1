# {{PROYECTO}} - Actualizar todo (un solo comando).
# Trae lo ultimo del repo y corre el instalador (bin/instalar.py): hook pre-commit activo,
# espejos de agentes materializados, espejos de skills identicos a la fuente y cada SKILL.md
# dentro de la especificacion. Correr despues de (o en vez de) un 'git pull'. Idempotente.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   {{PROYECTO}} - Actualizar todo"                     -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host "[1/2] Trayendo lo ultimo (git pull)..."
git pull --ff-only   # si la rama local se aparto de la remota, frena: no mezcla en silencio
if ($LASTEXITCODE -ne 0) {
    Write-Host "El git pull no se pudo hacer (rama apartada de la remota, o sin red): no sigo con el instalador." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[2/2] Instalador (hook, espejos de agentes, espejos de skills, especificacion de skills)..."
$Py = $null
foreach ($c in @("python", "py", "python3")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) {
    Write-Host "No encuentro Python 3: instalalo y corre  python -I bin/instalar.py" -ForegroundColor Red
    exit 1
}
& $Py -I bin/instalar.py
exit $LASTEXITCODE
