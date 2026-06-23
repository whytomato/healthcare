package com.example.healthcare.scheduling.model

data class ExamSchedule(
    val taskId: String,
    val patientId: String?,
    val orderingAgent: String,
    val scheduleStatus: String,
    val scheduledExams: List<String>,
    val message: String,
)
