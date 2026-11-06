<#
.SYNOPSIS
    Extrae el texto de un archivo .docx de transcripción de Teams y lo deja
    listo para ser analizado por el agente cerebro-meet-analyst.

.DESCRIPTION
    Descomprime el .docx (que internamente es un ZIP), parsea el XML de Word
    y produce un archivo .txt limpio en la carpeta scratch del proyecto.

.PARAMETER DocxPath
    Ruta absoluta al archivo .docx de la transcripción.

.PARAMETER OutputDir
    Carpeta de salida. Por defecto: .\scratch\

.EXAMPLE
    .\bin\extraer-reunion.ps1 ".\Reunion de equipo - 2026_08_05.docx"
    .\bin\extraer-reunion.ps1 "C:\ruta\reunion.docx" -OutputDir "C:\ruta\salida\"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [string]$OutputDir = ".\scratch\"
)

$ErrorActionPreference = "Stop"

# --- Validaciones ---
if (-not (Test-Path $DocxPath)) {
    Write-Error "No se encontro el archivo: $DocxPath"
    exit 1
}

$docxName = [System.IO.Path]::GetFileNameWithoutExtension($DocxPath)

# Extraer fecha del nombre si tiene formato YYYY_MM_DD
$fechaMatch = [regex]::Match($docxName, '(\d{4})_(\d{2})_(\d{2})')
if ($fechaMatch.Success) {
    $fecha = "$($fechaMatch.Groups[1].Value)-$($fechaMatch.Groups[2].Value)-$($fechaMatch.Groups[3].Value)"
} else {
    $fecha = Get-Date -Format "yyyy-MM-dd"
}

$outputFile = Join-Path $OutputDir "transcript-$fecha.txt"

# --- Crear carpeta de salida si no existe ---
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# --- Copiar como ZIP y descomprimir ---
$tempZip = [System.IO.Path]::GetTempFileName() + ".zip"
$tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName())

try {
    Copy-Item $DocxPath $tempZip
    Expand-Archive -Path $tempZip -DestinationPath $tempDir -Force

    $xmlPath = Join-Path $tempDir "word\document.xml"
    if (-not (Test-Path $xmlPath)) {
        Write-Error "No se encontro document.xml dentro del docx. ¿Es un archivo Word valido?"
        exit 1
    }

    # --- Parsear XML y extraer texto ---
    $xmlContent = Get-Content $xmlPath -Raw -Encoding UTF8

    # Extraer contenido de etiquetas <w:t>
    $matches = [regex]::Matches($xmlContent, '<w:t[^>]*>([^<]+)</w:t>')
    $lines = $matches | ForEach-Object { $_.Groups[1].Value }

    # Limpiar entidades HTML comunes
    $text = ($lines -join "`n") `
        -replace '&quot;', '"' `
        -replace '&amp;',  '&' `
        -replace '&lt;',   '<' `
        -replace '&gt;',   '>' `
        -replace '&apos;', "'"

    # Guardar resultado
    $text | Out-File -FilePath $outputFile -Encoding UTF8 -NoNewline

    $sizeKB = [math]::Round((Get-Item $outputFile).Length / 1KB, 1)
    Write-Host ""
    Write-Host "Extraccion completada:" -ForegroundColor Green
    Write-Host "  Archivo fuente : $DocxPath"
    Write-Host "  Texto extraido : $outputFile ($sizeKB KB)"
    Write-Host "  Fecha detectada: $fecha"
    Write-Host ""
    Write-Host "Siguiente paso: indicarle al agente que analice $outputFile con la skill cerebro-meet-analyst" -ForegroundColor Cyan

} finally {
    # Limpiar temporales
    if (Test-Path $tempZip) { Remove-Item $tempZip -Force }
    if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
}
