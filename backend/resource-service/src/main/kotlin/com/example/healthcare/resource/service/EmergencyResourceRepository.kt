package com.example.healthcare.resource.service

import com.example.healthcare.resource.model.EmergencyResourceEntity
import jakarta.persistence.LockModeType
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Lock

interface EmergencyResourceRepository : JpaRepository<EmergencyResourceEntity, String> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    fun findByResourceType(resourceType: String): EmergencyResourceEntity?
}
