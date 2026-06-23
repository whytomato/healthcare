package com.example.healthcare.practitioner.model

data class PractitionerAssignment(
    val taskId: String,
    val patientId: String?,
    val assignmentStatus: String,
    val assignedPractitioners: List<String>,
    val unavailableSpecialties: List<String>,
    val message: String,
)
