package com.example.healthcare.emergency.model

data class EmergencyEncounter(
    val taskId: String,
    val patientId: String?,
    val emergencyEncounterId: String,
    val status: String,
    val triageUrgency: String,
    val redFlags: List<String>,
    val resourceReadinessStatus: String,
    val reservedResources: List<String> = emptyList(),
    val message: String,
)
