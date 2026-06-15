package com.example.healthcare.record.model

import java.time.Instant

data class WorkflowResultRecord(
    val taskId: String,
    val patientId: String? = null,
    val status: String,
    val executedPath: List<String> = emptyList(),
    val workflowDecisions: Any? = null,
    val handoffTimeline: Any? = null,
    val selectedSpecialties: List<String> = emptyList(),
    val carePathway: Any? = null,
    val aiConsultation: Any? = null,
    val finalReport: Any? = null,
    val rawResult: Any? = null,
    val errorMessage: String? = null,
    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now(),
)
