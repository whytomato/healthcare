package com.example.healthcare.resource.model

data class ResourceReservationRequest(
    val taskId: String,
    val patientId: String?,
    val urgencyLevel: String,
    val requiredResources: List<String> = emptyList(),
)
