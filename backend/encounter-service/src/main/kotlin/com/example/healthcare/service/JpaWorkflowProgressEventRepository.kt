package com.example.healthcare.service

import com.example.healthcare.model.WorkflowProgressEventEntity
import org.springframework.data.jpa.repository.JpaRepository

interface JpaWorkflowProgressEventRepository : JpaRepository<WorkflowProgressEventEntity, Long> {
    fun findByTaskIdOrderByEventIndexAsc(taskId: String): List<WorkflowProgressEventEntity>
}
