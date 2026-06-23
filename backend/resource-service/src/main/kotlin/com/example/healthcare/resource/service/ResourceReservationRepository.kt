package com.example.healthcare.resource.service

import com.example.healthcare.resource.model.ResourceReservationEntity
import org.springframework.data.jpa.repository.JpaRepository

interface ResourceReservationRepository : JpaRepository<ResourceReservationEntity, Long> {
    fun findByTaskId(taskId: String): List<ResourceReservationEntity>
}
