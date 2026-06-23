package com.example.healthcare.practitioner.model

data class PractitionerAssignmentRequest(
    val taskId: String,
    val patientId: String?,
    val urgencyLevel: String,
    val requiredSpecialties: List<String> = emptyList(),
)
