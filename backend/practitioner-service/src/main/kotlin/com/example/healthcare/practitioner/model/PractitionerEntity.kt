package com.example.healthcare.practitioner.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import jakarta.persistence.Version

@Entity
@Table(name = "practitioners")
class PractitionerEntity(
    @Id
    @Column(name = "practitioner_id", nullable = false)
    var practitionerId: String = "",

    @Column(name = "display_name", nullable = false)
    var displayName: String = "",

    @Column(name = "specialty", nullable = false)
    var specialty: String = "",

    @Column(name = "on_shift", nullable = false)
    var onShift: Boolean = true,

    @Column(name = "active_assignments", nullable = false)
    var activeAssignments: Int = 0,

    @Column(name = "max_concurrent_assignments", nullable = false)
    var maxConcurrentAssignments: Int = 1,

    @Version
    @Column(name = "version", nullable = false)
    var version: Long = 0,
)
