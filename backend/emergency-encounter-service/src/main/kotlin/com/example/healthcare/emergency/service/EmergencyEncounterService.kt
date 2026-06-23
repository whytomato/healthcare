package com.example.healthcare.emergency.service

import com.example.healthcare.emergency.model.EmergencyEncounter
import com.example.healthcare.emergency.model.EmergencyEncounterRequest
import com.example.healthcare.emergency.model.EmergencyReadinessUpdateRequest
import org.springframework.stereotype.Service

@Service
class EmergencyEncounterService {
    fun open(request: EmergencyEncounterRequest): EmergencyEncounter {
        val status = if (request.triageUrgency == "high") {
            "opened"
        } else {
            "observation_opened"
        }
        return EmergencyEncounter(
            taskId = request.taskId,
            patientId = request.patientId,
            emergencyEncounterId = "er-${request.taskId}",
            status = status,
            triageUrgency = request.triageUrgency,
            redFlags = request.redFlags.distinct(),
            resourceReadinessStatus = "pending",
            reservedResources = emptyList(),
            message = "Emergency encounter opened for acute-care coordination.",
        )
    }

    fun updateReadiness(request: EmergencyReadinessUpdateRequest): EmergencyEncounter =
        EmergencyEncounter(
            taskId = request.taskId,
            patientId = null,
            emergencyEncounterId = request.emergencyEncounterId,
            status = "readiness_confirmed",
            triageUrgency = "high",
            redFlags = emptyList(),
            resourceReadinessStatus = request.resourceReadinessStatus,
            reservedResources = request.reservedResources.distinct(),
            message = "Emergency resource readiness recorded: ${request.reservedResources.distinct().joinToString()}",
        )
}
