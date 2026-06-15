package com.example.healthcare.triage.model

data class AiWorkflowTaskMessage(
    val taskId: String,
    val doctorId: String? = null,
    val patientId: String? = null,
    val caseText: String,
    val question: String,
    val language: String = "zh-CN",
    val metadata: Map<String, Any?> = emptyMap(),
    val triageAssessment: TriageAssessmentResponse,
)
