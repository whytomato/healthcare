package com.example.healthcare.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.EnumType
import jakarta.persistence.Enumerated
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "patient_encounters")
open class AiTaskEntity(
    @Id
    @Column(name = "task_id", nullable = false)
    var taskId: String = "",

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    var status: AiTaskStatus = AiTaskStatus.RECEIVED,

    @Column(name = "case_text", nullable = false, columnDefinition = "text")
    var caseText: String = "",

    @Column(nullable = false)
    var question: String = "",

    @Column(name = "doctor_id")
    var doctorId: String? = null,

    @Column(name = "patient_id")
    var patientId: String? = null,

    @Column(nullable = false)
    var language: String = "zh-CN",

    @Column(name = "error_message")
    var errorMessage: String? = null,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),

    @Column(name = "updated_at", nullable = false)
    var updatedAt: Instant = Instant.now(),
)
