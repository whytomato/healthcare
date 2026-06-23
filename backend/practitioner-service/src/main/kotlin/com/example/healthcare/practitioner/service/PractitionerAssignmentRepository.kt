package com.example.healthcare.practitioner.service

import com.example.healthcare.practitioner.model.PractitionerAssignmentEntity
import org.springframework.data.jpa.repository.JpaRepository

interface PractitionerAssignmentRepository : JpaRepository<PractitionerAssignmentEntity, Long> {
    fun findByTaskId(taskId: String): List<PractitionerAssignmentEntity>
}
