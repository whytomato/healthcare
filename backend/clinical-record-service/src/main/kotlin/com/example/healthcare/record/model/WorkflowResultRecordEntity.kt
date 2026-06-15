package com.example.healthcare.record.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "workflow_result_records")
open class WorkflowResultRecordEntity(
    @Id
    @Column(name = "task_id", nullable = false)
    var taskId: String = "",

    @Column(nullable = false)
    var status: String = "",

    @Column(name = "patient_id")
    var patientId: String? = null,

    @Column(name = "executed_path_json", columnDefinition = "text")
    var executedPathJson: String? = null,

    @Column(name = "workflow_decisions_json", columnDefinition = "text")
    var workflowDecisionsJson: String? = null,

    @Column(name = "handoff_timeline_json", columnDefinition = "text")
    var handoffTimelineJson: String? = null,

    @Column(name = "selected_specialties_json", columnDefinition = "text")
    var selectedSpecialtiesJson: String? = null,

    @Column(name = "care_pathway_json", columnDefinition = "text")
    var carePathwayJson: String? = null,

    @Column(name = "ai_consultation_json", columnDefinition = "text")
    var aiConsultationJson: String? = null,

    @Column(name = "final_report_json", columnDefinition = "text")
    var finalReportJson: String? = null,

    @Column(name = "raw_result_json", columnDefinition = "text")
    var rawResultJson: String? = null,

    @Column(name = "error_message")
    var errorMessage: String? = null,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),

    @Column(name = "updated_at", nullable = false)
    var updatedAt: Instant = Instant.now(),
)
