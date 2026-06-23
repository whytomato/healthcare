package com.example.healthcare.practitioner.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Lob
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "practitioner_assignments")
class PractitionerAssignmentEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @Column(name = "task_id", nullable = false)
    var taskId: String = "",

    @Column(name = "patient_id")
    var patientId: String? = null,

    @Column(name = "assignment_status", nullable = false)
    var assignmentStatus: String = "",

    @Lob
    @Column(name = "assigned_practitioners", nullable = false)
    var assignedPractitioners: String = "[]",

    @Lob
    @Column(name = "unavailable_specialties", nullable = false)
    var unavailableSpecialties: String = "[]",

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
