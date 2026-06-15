package com.example.healthcare.record.service

import com.example.healthcare.record.model.WorkflowResultRecordEntity
import org.springframework.data.jpa.repository.JpaRepository

interface JpaWorkflowResultRecordRepository : JpaRepository<WorkflowResultRecordEntity, String> {
    fun findByPatientIdOrderByUpdatedAtDesc(patientId: String): List<WorkflowResultRecordEntity>
}
