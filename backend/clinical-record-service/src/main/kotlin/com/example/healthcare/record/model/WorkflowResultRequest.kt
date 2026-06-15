package com.example.healthcare.record.model

data class WorkflowResultRequest(
    val taskId: String,
    val status: String,
    val result: Map<String, Any?>? = null,
    val errorMessage: String? = null,
)
