package com.example.healthcare.model

data class WorkflowProgressMessage(
    val taskId: String = "",
    val eventType: String = "",
    val agent: String? = null,
    val decision: String? = null,
    val decisionScope: String? = null,
    val reason: String? = null,
    val targetAgents: List<String> = emptyList(),
    val parallelGroup: String? = null,
    val payload: Any? = null,
    val durationMs: Long? = null,
    val eventIndex: Int = 0,
)
