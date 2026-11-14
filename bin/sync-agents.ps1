# {{PROYECTO}} - Sincronizador de Agentes (espejos)
# Regenera .agents/agents/ y .claude/agents/ (no se versionan) desde cerebro-digital/configuracion-ia/agentes/.
# Herramienta del MANTENEDOR. Envoltorio de bin/sync-espejos.py (el como, en su encabezado); necesita Python 3.

$Root = Split-Path -Parent $PSScriptRoot
foreach ($c in @("python", "py", "python3")) {
    # que ande de verdad: sin Python instalado, "python" puede ser el atajo de la Microsoft Store (sale 9009)
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $c -I (Join-Path $Root "bin/sync-espejos.py") agentes @args
            exit $LASTEXITCODE
        }
    }
}
Write-Host "ERROR: hace falta Python 3 para regenerar los espejos (bin/sync-espejos.py)." -ForegroundColor Red
exit 2
