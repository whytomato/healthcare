param(
    [string]$PidFile = (Join-Path $PSScriptRoot "..\outputs\healthcare-services.pids.json")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "[stop] PID file not found: $PidFile"
    return
}

$entries = Get-Content -Raw -Encoding UTF8 -LiteralPath $PidFile | ConvertFrom-Json
foreach ($entry in @($entries)) {
    $processId = [int]$entry.processId
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Write-Host "[skip] process already stopped: $($entry.name) ($processId)"
        continue
    }
    Write-Host "[stop] $($entry.name) ($processId)"
    Stop-Process -Id $processId -Force
}

Remove-Item -LiteralPath $PidFile -Force
Write-Host "[summary] Healthcare service processes stopped."
