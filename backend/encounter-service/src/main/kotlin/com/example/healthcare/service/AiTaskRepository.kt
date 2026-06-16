package com.example.healthcare.service

import com.example.healthcare.model.AiTask
import com.example.healthcare.model.AiTaskEntity
import org.springframework.stereotype.Repository

@Repository
class AiTaskRepository(
    private val repository: JpaAiTaskRepository,
) {
    fun save(task: AiTask): AiTask {
        return repository.save(task.toEntity()).toModel()
    }

    fun findById(taskId: String): AiTask? =
        repository.findById(taskId).map { it.toModel() }.orElse(null)

    fun findAll(): Collection<AiTask> =
        repository.findAll().map { it.toModel() }
}

private fun AiTask.toEntity(): AiTaskEntity =
    AiTaskEntity(
        taskId = taskId,
        status = status,
        caseText = caseText,
        question = question,
        doctorId = doctorId,
        patientId = patientId,
        language = language,
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )

private fun AiTaskEntity.toModel(): AiTask =
    AiTask(
        taskId = taskId,
        status = status,
        caseText = caseText,
        question = question,
        doctorId = doctorId,
        patientId = patientId,
        language = language,
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )
