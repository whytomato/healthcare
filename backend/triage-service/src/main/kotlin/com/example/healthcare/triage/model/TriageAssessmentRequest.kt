package com.example.healthcare.triage.model

import jakarta.validation.constraints.NotBlank

data class TriageAssessmentRequest(
    val encounterId: String? = null,
    val patientId: String? = null,
    @field:NotBlank
    val caseText: String,
    val language: String = "zh-CN",
)
