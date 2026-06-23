package com.example.healthcare.emergency.model

data class EmergencyEncounterRequest(
    val taskId: String,
    val patientId: String? = null,
    val triageUrgency: String,
    val redFlags: List<String> = emptyList(),
)
