param(
    [string]$BackendDir = (Join-Path $PSScriptRoot "..\backend"),
    [string]$LogDir = (Join-Path $PSScriptRoot "..\outputs\service-logs"),
    [string]$PidFile = (Join-Path $PSScriptRoot "..\outputs\healthcare-services.pids.json"),
    [switch]$CoreOnly,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

Write-Host "[start-healthcare-services] preparing Spring Boot service processes"

$coreServices = @(
    @{ Name = "encounter-service"; Module = "encounter-service"; Port = 8081 },
    @{ Name = "triage-service"; Module = "triage-service"; Port = 8082 },
    @{ Name = "clinical-record-service"; Module = "clinical-record-service"; Port = 8083 },
    @{ Name = "care-coordination-service"; Module = "care-coordination-service"; Port = 8084 }
)

$erServices = @(
    @{ Name = "practitioner-service"; Module = "practitioner-service"; Port = 8085 },
    @{ Name = "resource-service"; Module = "resource-service"; Port = 8086 },
    @{ Name = "scheduling-service"; Module = "scheduling-service"; Port = 8087 },
    @{ Name = "emergency-encounter-service"; Module = "emergency-encounter-service"; Port = 8088 }
)

$services = if ($CoreOnly) {
    $coreServices
} else {
    $coreServices + $erServices
}

$mvn = Get-Command mvn -ErrorAction SilentlyContinue
if ($null -eq $mvn) {
    throw "mvn was not found on PATH. Start services from IDEA, or add Maven to PATH before running this script."
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PidFile) | Out-Null

$processes = @()
foreach ($service in $services) {
    $logPath = Join-Path $LogDir "$($service.Name).log"
    $errorLogPath = Join-Path $LogDir "$($service.Name).err.log"
    $arguments = @("-pl", $service.Module, "spring-boot:run")
    $command = "mvn $($arguments -join ' ')"
    Write-Host "[start] $($service.Name) on port $($service.Port)"
    $process = Start-Process `
        -FilePath $mvn.Source `
        -ArgumentList $arguments `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $logPath `
        -RedirectStandardError $errorLogPath `
        -WindowStyle Hidden `
        -PassThru
    $processes += [pscustomobject]@{
        name = $service.Name
        module = $service.Module
        port = $service.Port
        processId = $process.Id
        logPath = $logPath
        errorLogPath = $errorLogPath
        command = $command
    }
}

$processes | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -Path $PidFile
Write-Host "[summary] Started $($processes.Count) service processes. PID file: $PidFile"

if ($Verify) {
    Write-Host "[verify] waiting before service verification"
    Start-Sleep -Seconds 20
    & (Join-Path $PSScriptRoot "verify-healthcare-services.ps1") -CoreOnly:$CoreOnly
}
