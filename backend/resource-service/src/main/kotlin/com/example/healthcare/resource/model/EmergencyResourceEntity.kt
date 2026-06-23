package com.example.healthcare.resource.model

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import jakarta.persistence.Version

@Entity
@Table(name = "emergency_resources")
class EmergencyResourceEntity(
    @Id
    @Column(name = "resource_type", nullable = false)
    var resourceType: String = "",

    @Column(name = "display_name", nullable = false)
    var displayName: String = "",

    @Column(name = "total_units", nullable = false)
    var totalUnits: Int = 0,

    @Column(name = "available_units", nullable = false)
    var availableUnits: Int = 0,

    @Version
    @Column(name = "version", nullable = false)
    var version: Long = 0,
)
