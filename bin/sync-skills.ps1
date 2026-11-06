# {{PROYECTO}} - Sincronizador de Skills (espejos versionados)
# Copia la fuente versionada cerebro-digital/configuracion-ia/skills/
# hacia los DOS espejos versionados (viajan en el clone):
#   .agents/skills/  -> lo lee Antigravity (y opencode lo auto-descubre)
#   .claude/skills/  -> lo lee Claude Code (skills project-scoped, nativas)
# Herramienta del MANTENEDOR: regenera los espejos ANTES de commitear cuando
# cambian las skills. El hook pre-commit (.githooks/) lo verifica al commitear,
# si esta activado (git config core.hooksPath .githooks). El que clona NO
# necesita correr esto. Idempotente: rehace los espejos desde cero en cada corrida.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Src  = Join-Path $Root "cerebro-digital/configuracion-ia/skills"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   {{PROYECTO}} - Sincronizador de Skills (espejos)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not (Test-Path $Src)) {
    Write-Host "ERROR: no existe la fuente: $Src" -ForegroundColor Red
    exit 1
}

$Destinos = @(".agents/skills", ".claude/skills")
foreach ($rel in $Destinos) {
    $Dst = Join-Path $Root $rel
    if (Test-Path $Dst) { Remove-Item -Recurse -Force $Dst }
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Src "*") $Dst
    $N = (Get-ChildItem -Directory $Dst).Count
    Write-Host "OK: espejo regenerado con $N skills en $rel/" -ForegroundColor Green
}
