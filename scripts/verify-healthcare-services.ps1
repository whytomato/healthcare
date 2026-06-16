param(
    [string]$EncounterBaseUrl = "http://localhost:8081",
    [string]$TriageBaseUrl = "http://localhost:8082",
    [string]$RecordBaseUrl = "http://localhost:8083",
    [string]$CareBaseUrl = "http://localhost:8084"
)

$ErrorActionPreference = "Stop"
$failed = $false

function Invoke-Check {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )

    try {
        $parameters = @{
            Method = $Method
            Uri = $Url
            TimeoutSec = 8
            Headers = @{ "Content-Type" = "application/json" }
        }
        if ($null -ne $Body) {
            $parameters.Body = ($Body | ConvertTo-Json -Depth 8)
        }

        $response = Invoke-RestMethod @parameters
        Write-Host "[ok] $Name -> $Url"
        return $response
    }
    catch {
        Write-Host "[failed] $Name -> $Url"
        Write-Host $_.Exception.Message
        $script:failed = $true
        return $null
    }
}

Invoke-Check "encounter health" "GET" "$EncounterBaseUrl/api/ai/health" | Out-Null
Invoke-Check "triage health" "GET" "$TriageBaseUrl/api/triage/health" | Out-Null
Invoke-Check "clinical record health" "GET" "$RecordBaseUrl/api/records/health" | Out-Null
Invoke-Check "care coordination health" "GET" "$CareBaseUrl/health" | Out-Null

Invoke-Check "triage assessment" "POST" "$TriageBaseUrl/api/triage/assess" @{
    encounterId = "verify-encounter"
    patientId = "verify-patient"
    caseText = "A patient reports cough and fever with no chest pain or confusion."
} | Out-Null

Invoke-Check "care coordination plan" "POST" "$CareBaseUrl/api/care/coordination-plans" @{
    taskId = "verify-task"
    patientId = "verify-patient"
    doctorId = "verify-doctor"
    disposition = "outpatient_follow_up"
    triageUrgency = "standard"
    selectedSpecialties = @("respiratory")
    monitoringPlan = @("Review test results when available.")
} | Out-Null

if ($failed) {
    Write-Host "[summary] One or more healthcare services failed verification."
    Exit 1
}

Write-Host "[summary] Healthcare service verification passed."
