package com.example.healthcare.scheduling.model

data class ExamSchedulingRequest(
    val taskId: String,
    val patientId: String?,
    val orderingAgent: String,
    val requestedExams: List<String> = emptyList(),
    val urgencyLevel: String,
)
