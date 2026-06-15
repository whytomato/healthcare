package com.example.healthcare.triage.model

data class TriageAssessmentResponse(
    val encounterId: String? = null,
    val patientId: String? = null,
    val urgencyLevel: String,
    val recommendedDepartment: String,
    val redFlags: List<String>,
)
