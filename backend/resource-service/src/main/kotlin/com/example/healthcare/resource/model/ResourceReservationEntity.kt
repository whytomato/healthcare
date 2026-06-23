package com.example.healthcare.resource.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Lob
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "resource_reservations")
class ResourceReservationEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @Column(name = "task_id", nullable = false)
    var taskId: String = "",

    @Column(name = "patient_id")
    var patientId: String? = null,

    @Column(name = "readiness_status", nullable = false)
    var readinessStatus: String = "",

    @Lob
    @Column(name = "reserved_resources", nullable = false)
    var reservedResources: String = "[]",

    @Lob
    @Column(name = "unavailable_resources", nullable = false)
    var unavailableResources: String = "[]",

    @Column(name = "reservation_status", nullable = false)
    var reservationStatus: String = "reserved",

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
