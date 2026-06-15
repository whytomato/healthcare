package com.example.healthcare.service

import com.fasterxml.jackson.databind.ObjectMapper
import com.example.healthcare.model.WorkflowProgressEvent
import com.example.healthcare.model.WorkflowProgressEventEntity
import com.example.healthcare.model.WorkflowProgressMessage
import org.springframework.stereotype.Service
import java.time.Instant

@Service
class WorkflowProgressService(
    private val repository: JpaWorkflowProgressEventRepository,
    private val objectMapper: ObjectMapper,
) {
    fun saveProgress(message: WorkflowProgressMessage): WorkflowProgressEvent {
        val event = WorkflowProgressEvent(
            taskId = message.taskId,
            eventType = message.eventType,
            agent = message.agent,
            decision = message.decision,
            decisionScope = message.decisionScope,
            reason = message.reason,
            targetAgents = message.targetAgents,
            parallelGroup = message.parallelGroup,
            payload = message.payload,
            durationMs = message.durationMs,
            eventIndex = message.eventIndex,
        )
        return repository.save(event.toEntity(objectMapper)).toModel(objectMapper)
    }

    fun getProgress(taskId: String): List<WorkflowProgressEvent> =
        repository.findByTaskIdOrderByEventIndexAsc(taskId).map { it.toModel(objectMapper) }
}

private fun WorkflowProgressEvent.toEntity(objectMapper: ObjectMapper): WorkflowProgressEventEntity =
    WorkflowProgressEventEntity(
        taskId = taskId,
        eventType = eventType,
        agent = agent,
        decision = decision,
        decisionScope = decisionScope,
        reason = reason,
        targetAgentsJson = objectMapper.writeValueAsString(targetAgents),
        parallelGroup = parallelGroup,
        payloadJson = payload?.let { objectMapper.writeValueAsString(it) },
        durationMs = durationMs,
        eventIndex = eventIndex,
        createdAt = createdAt,
    )

private fun WorkflowProgressEventEntity.toModel(objectMapper: ObjectMapper): WorkflowProgressEvent =
    WorkflowProgressEvent(
        taskId = taskId,
        eventType = eventType,
        agent = agent,
        decision = decision,
        decisionScope = decisionScope,
        reason = reason,
        targetAgents = targetAgentsJson.toStringList(objectMapper),
        parallelGroup = parallelGroup,
        payload = payloadJson?.let { objectMapper.readValue(it, Any::class.java) },
        durationMs = durationMs,
        eventIndex = eventIndex,
        createdAt = createdAt,
    )

private fun String?.toStringList(objectMapper: ObjectMapper): List<String> =
    when (val value = this?.let { objectMapper.readValue(it, Any::class.java) }) {
        is List<*> -> value.mapNotNull { it?.toString() }
        else -> emptyList()
    }
