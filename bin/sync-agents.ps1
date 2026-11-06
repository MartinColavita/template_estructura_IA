# {{PROYECTO}} - Sincronizador de Agentes (espejos versionados)
# Copia la fuente versionada cerebro-digital/configuracion-ia/agentes/
# hacia los DOS espejos locales (NO versionados: cada dev los genera una vez despues de clonar; ver INSTALACION.md):
#   .agents/agents/  -> lo lee Antigravity (y opencode lo auto-descubre)
#   .claude/agents/  -> lo lee Claude Code (subagentes project-scoped)
# Mismo mecanismo que sync-skills.ps1. Herramienta del MANTENEDOR: regenera
# los espejos ANTES de commitear cuando cambian los agentes. El hook
# pre-commit (.githooks/) lo verifica al commitear, si esta activado
# (git config core.hooksPath .githooks). El que clona NO necesita correr
# esto. Idempotente: rehace los espejos desde cero en cada corrida.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Src  = Join-Path $Root "cerebro-digital/configuracion-ia/agentes"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   {{PROYECTO}} - Sincronizador de Agentes (espejos)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not (Test-Path $Src)) {
    Write-Host "ERROR: no existe la fuente: $Src" -ForegroundColor Red
    exit 1
}

$Destinos = @(".agents/agents", ".claude/agents")
foreach ($rel in $Destinos) {
    $Dst = Join-Path $Root $rel
    if (Test-Path $Dst) { Remove-Item -Recurse -Force $Dst }
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Src "*") $Dst
    $N = (Get-ChildItem -File -Filter "*.md" $Dst).Count
    Write-Host "OK: espejo regenerado con $N agentes en $rel/" -ForegroundColor Green
}
