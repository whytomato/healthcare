package com.example.healthcare.care.model

data class CareCoordinationRequest(
    val taskId: String = "",
    val patientId: String? = null,
    val doctorId: String? = null,
    val disposition: String = "outpatient_follow_up",
    val triageUrgency: String = "standard",
    val selectedSpecialties: List<String> = emptyList(),
    val monitoringPlan: List<String> = emptyList(),
)
