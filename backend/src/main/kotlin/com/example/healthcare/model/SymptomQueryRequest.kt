package com.example.healthcare.model

import jakarta.validation.constraints.NotBlank

data class SymptomQueryRequest(
    @field:NotBlank
    val caseText: String,
    val question: String? = null,
    val doctorId: String? = null,
    val patientId: String? = null,
    val language: String? = null,
)
