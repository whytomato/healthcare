param(
    [string]$EncounterBaseUrl = "http://localhost:8081",
    [string]$TriageBaseUrl = "http://localhost:8082",
    [string]$RecordBaseUrl = "http://localhost:8083",
    [string]$CareBaseUrl = "http://localhost:8084",
    [string]$PractitionerBaseUrl = "http://localhost:8085",
    [string]$ResourceBaseUrl = "http://localhost:8086",
    [string]$SchedulingBaseUrl = "http://localhost:8087",
    [string]$EmergencyEncounterBaseUrl = "http://localhost:8088",
    [switch]$CoreOnly
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

if (-not $CoreOnly) {
    Invoke-Check "practitioner health" "GET" "$PractitionerBaseUrl/health" | Out-Null
    Invoke-Check "resource health" "GET" "$ResourceBaseUrl/health" | Out-Null
    Invoke-Check "scheduling health" "GET" "$SchedulingBaseUrl/health" | Out-Null
    Invoke-Check "emergency encounter health" "GET" "$EmergencyEncounterBaseUrl/health" | Out-Null

    Invoke-Check "emergency encounter" "POST" "$EmergencyEncounterBaseUrl/api/emergency/encounters" @{
        taskId = "verify-task"
        patientId = "verify-patient"
        triageUrgency = "high"
        redFlags = @("chest pain", "shortness of breath")
    } | Out-Null

    Invoke-Check "emergency readiness update" "POST" "$EmergencyEncounterBaseUrl/api/emergency/encounters/readiness" @{
        taskId = "verify-task"
        emergencyEncounterId = "er-verify-task"
        resourceReadinessStatus = "ready"
        reservedResources = @("resuscitation_room", "portable_monitor")
    } | Out-Null

    Invoke-Check "practitioner assignment" "POST" "$PractitionerBaseUrl/api/practitioners/emergency-assignments" @{
        taskId = "verify-task"
        patientId = "verify-patient"
        urgencyLevel = "high"
        requiredSpecialties = @("respiratory", "cardiology")
    } | Out-Null

    Invoke-Check "resource reservation" "POST" "$ResourceBaseUrl/api/resources/emergency-reservations" @{
        taskId = "verify-task"
        patientId = "verify-patient"
        urgencyLevel = "high"
        requiredResources = @("resuscitation_room", "emergency_observation_bed")
    } | Out-Null

    Invoke-Check "emergency exam scheduling" "POST" "$SchedulingBaseUrl/api/schedules/emergency-exams" @{
        taskId = "verify-task"
        patientId = "verify-patient"
        orderingAgent = "emergency_physician_agent"
        requestedExams = @("CBC", "chest X-ray")
        urgencyLevel = "high"
    } | Out-Null
}

if ($failed) {
    Write-Host "[summary] One or more healthcare services failed verification."
    Exit 1
}

Write-Host "[summary] Healthcare service verification passed."
