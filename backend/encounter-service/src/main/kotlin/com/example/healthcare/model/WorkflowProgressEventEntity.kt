package com.example.healthcare.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "workflow_progress_events")
open class WorkflowProgressEventEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @Column(name = "task_id", nullable = false)
    var taskId: String = "",

    @Column(name = "event_type", nullable = false)
    var eventType: String = "",

    @Column(name = "agent")
    var agent: String? = null,

    @Column(name = "decision")
    var decision: String? = null,

    @Column(name = "decision_scope")
    var decisionScope: String? = null,

    @Column(name = "reason", columnDefinition = "text")
    var reason: String? = null,

    @Column(name = "target_agents_json", columnDefinition = "text")
    var targetAgentsJson: String? = null,

    @Column(name = "parallel_group")
    var parallelGroup: String? = null,

    @Column(name = "payload_json", columnDefinition = "text")
    var payloadJson: String? = null,

    @Column(name = "duration_ms")
    var durationMs: Long? = null,

    @Column(name = "event_index", nullable = false)
    var eventIndex: Int = 0,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
