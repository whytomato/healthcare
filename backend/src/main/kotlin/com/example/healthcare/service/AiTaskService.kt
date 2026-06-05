package com.example.healthcare.service

import com.example.healthcare.model.AiSymptomQueryMessage
import com.example.healthcare.model.AiSymptomResultMessage
import com.example.healthcare.model.AiTask
import com.example.healthcare.model.AiTaskStatus
import com.example.healthcare.model.SymptomQueryRequest
import org.springframework.stereotype.Service
import java.time.Instant
import java.util.UUID

@Service
class AiTaskService(
    private val repository: AiTaskRepository,
    private val publisher: KafkaAiTaskPublisher,
) {
    fun createSymptomQueryTask(request: SymptomQueryRequest): AiTask {
        val now = Instant.now()
        val task = AiTask(
            taskId = UUID.randomUUID().toString(),
            status = AiTaskStatus.RECEIVED,
            caseText = request.caseText,
            question = request.question.blankToDefault(DEFAULT_QUESTION),
            doctorId = request.doctorId,
            patientId = request.patientId,
            language = request.language.blankToDefault("zh-CN"),
            createdAt = now,
            updatedAt = now,
        )
        repository.save(task)

        val message = AiSymptomQueryMessage(
            taskId = task.taskId,
            doctorId = task.doctorId,
            patientId = task.patientId,
            caseText = task.caseText,
            question = task.question,
            language = task.language,
            metadata = mapOf("source" to "springboot-backend"),
        )
        if (publisher.publishSymptomQuery(message)) {
            task.status = AiTaskStatus.PUBLISHED
            task.updatedAt = Instant.now()
            repository.save(task)
        }
        return task
    }

    fun applyResult(message: AiSymptomResultMessage): AiTask {
        val task = repository.findById(message.taskId)
            ?: throw NoSuchElementException("AI task not found: ${message.taskId}")
        task.result = message.result
        task.errorMessage = message.errorMessage
        task.status = mapWorkerStatus(message.status)
        task.updatedAt = Instant.now()
        return repository.save(task)
    }

    fun getTask(taskId: String): AiTask =
        repository.findById(taskId) ?: throw NoSuchElementException("AI task not found: $taskId")

    fun listTasks(): List<AiTask> = repository.findAll().toList()

    private fun mapWorkerStatus(status: String): AiTaskStatus =
        when (status.lowercase()) {
            "ready", "completed" -> AiTaskStatus.COMPLETED
            "needs_data" -> AiTaskStatus.NEEDS_DATA
            else -> AiTaskStatus.FAILED
        }

    private fun String?.blankToDefault(defaultValue: String): String =
        if (this.isNullOrBlank()) defaultValue else this

    companion object {
        private const val DEFAULT_QUESTION = "What diseases or conditions should be considered?"
    }
}
