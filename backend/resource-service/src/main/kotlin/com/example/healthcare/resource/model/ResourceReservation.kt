package com.example.healthcare.resource.model

data class ResourceReservation(
    val taskId: String,
    val patientId: String?,
    val readinessStatus: String,
    val reservedResources: List<String>,
    val unavailableResources: List<String>,
    val message: String,
)
