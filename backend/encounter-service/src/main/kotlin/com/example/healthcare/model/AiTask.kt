package com.example.healthcare.model

import java.time.Instant

data class AiTask(
    var taskId: String = "",
    var status: AiTaskStatus = AiTaskStatus.RECEIVED,
    var caseText: String = "",
    var question: String = "",
    var doctorId: String? = null,
    var patientId: String? = null,
    var language: String = "zh-CN",
    var errorMessage: String? = null,
    var createdAt: Instant = Instant.now(),
    var updatedAt: Instant = Instant.now(),
)
