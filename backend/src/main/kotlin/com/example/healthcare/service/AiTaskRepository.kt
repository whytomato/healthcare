package com.example.healthcare.service

import com.example.healthcare.model.AiTask
import org.springframework.stereotype.Repository
import java.util.concurrent.ConcurrentHashMap

@Repository
class AiTaskRepository {
    private val tasks = ConcurrentHashMap<String, AiTask>()

    fun save(task: AiTask): AiTask {
        tasks[task.taskId] = task
        return task
    }

    fun findById(taskId: String): AiTask? = tasks[taskId]

    fun findAll(): Collection<AiTask> = tasks.values
}
