package com.example.healthcare.emergency.model

data class EmergencyReadinessUpdateRequest(
    val taskId: String,
    val emergencyEncounterId: String,
    val resourceReadinessStatus: String,
    val reservedResources: List<String> = emptyList(),
)
