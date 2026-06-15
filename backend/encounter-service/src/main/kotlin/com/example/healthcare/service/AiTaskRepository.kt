package com.example.healthcare.service

import com.fasterxml.jackson.databind.ObjectMapper
import com.example.healthcare.model.AiTask
import com.example.healthcare.model.AiTaskEntity
import org.springframework.stereotype.Repository

@Repository
class AiTaskRepository(
    private val repository: JpaAiTaskRepository,
    private val objectMapper: ObjectMapper,
) {
    fun save(task: AiTask): AiTask {
        return repository.save(task.toEntity(objectMapper)).toModel(objectMapper)
    }

    fun findById(taskId: String): AiTask? =
        repository.findById(taskId).map { it.toModel(objectMapper) }.orElse(null)

    fun findAll(): Collection<AiTask> =
        repository.findAll().map { it.toModel(objectMapper) }
}

private fun AiTask.toEntity(objectMapper: ObjectMapper): AiTaskEntity =
    AiTaskEntity(
        taskId = taskId,
        status = status,
        caseText = caseText,
        question = question,
        doctorId = doctorId,
        patientId = patientId,
        language = language,
        resultJson = result?.let { objectMapper.writeValueAsString(it) },
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )

private fun AiTaskEntity.toModel(objectMapper: ObjectMapper): AiTask =
    AiTask(
        taskId = taskId,
        status = status,
        caseText = caseText,
        question = question,
        doctorId = doctorId,
        patientId = patientId,
        language = language,
        result = resultJson?.let { objectMapper.readValue(it, Any::class.java) },
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )
