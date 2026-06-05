package com.example.healthcare.controller

import com.example.healthcare.model.AiSymptomResultMessage
import com.example.healthcare.model.AiTask
import com.example.healthcare.model.SymptomQueryRequest
import com.example.healthcare.service.AiTaskService
import jakarta.validation.Valid
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/ai")
class AiTaskController(
    private val taskService: AiTaskService,
) {
    @GetMapping("/health")
    fun health(): Map<String, String> = mapOf("status" to "ok")

    @PostMapping("/symptom-query")
    fun createSymptomQuery(@Valid @RequestBody request: SymptomQueryRequest): AiTask =
        taskService.createSymptomQueryTask(request)

    @GetMapping("/tasks/{taskId}")
    fun getTask(@PathVariable taskId: String): AiTask = taskService.getTask(taskId)

    @GetMapping("/tasks")
    fun listTasks(): List<AiTask> = taskService.listTasks()

    @PostMapping("/tasks/{taskId}/result")
    fun applyResult(
        @PathVariable taskId: String,
        @RequestBody message: AiSymptomResultMessage,
    ): AiTask = taskService.applyResult(
        AiSymptomResultMessage(
            taskId = taskId,
            status = message.status,
            result = message.result,
            errorMessage = message.errorMessage,
        )
    )
}
