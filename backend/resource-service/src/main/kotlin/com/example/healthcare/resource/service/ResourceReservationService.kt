package com.example.healthcare.resource.service

import com.example.healthcare.resource.model.EmergencyResourceEntity
import com.example.healthcare.resource.model.ResourceReservation
import com.example.healthcare.resource.model.ResourceReservationEntity
import com.example.healthcare.resource.model.ResourceReservationRequest
import com.fasterxml.jackson.core.type.TypeReference
import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
class ResourceReservationService(
    private val resourceRepository: EmergencyResourceRepository,
    private val reservationRepository: ResourceReservationRepository,
    private val objectMapper: ObjectMapper,
) {
    private val defaultCapacities = mapOf(
        "resuscitation_room" to 1,
        "emergency_observation_bed" to 2,
        "portable_monitor" to 4,
        "cardiac_monitor" to 2,
        "neuro_observation_capacity" to 1,
        "exam_room" to 3,
    )

    @Transactional
    fun reserve(request: ResourceReservationRequest): ResourceReservation {
        seedDefaultInventory()
        val required = request.requiredResources.ifEmpty {
            if (request.urgencyLevel == "high") {
                listOf("resuscitation_room", "emergency_observation_bed", "portable_monitor")
            } else {
                listOf("exam_room")
            }
        }
        val reserved = mutableListOf<String>()
        val unavailable = mutableListOf<String>()
        required.distinct().forEach { resourceType ->
            val resource = resourceRepository.findByResourceType(resourceType)
            if (resource != null && resource.availableUnits > 0) {
                resource.availableUnits -= 1
                reserved.add(resourceType)
            } else {
                unavailable.add(resourceType)
            }
        }
        val readinessStatus = when {
            unavailable.isEmpty() -> "ready"
            reserved.isEmpty() -> "unavailable"
            else -> "partial"
        }
        reservationRepository.save(
            ResourceReservationEntity(
                taskId = request.taskId,
                patientId = request.patientId,
                readinessStatus = readinessStatus,
                reservedResources = objectMapper.writeValueAsString(reserved),
                unavailableResources = objectMapper.writeValueAsString(unavailable),
                reservationStatus = if (reserved.isEmpty()) "unavailable" else "reserved",
            )
        )
        return ResourceReservation(
            taskId = request.taskId,
            patientId = request.patientId,
            readinessStatus = readinessStatus,
            reservedResources = reserved,
            unavailableResources = unavailable,
            message = if (unavailable.isEmpty()) {
                "Emergency resource readiness reserved."
            } else {
                "Emergency resource readiness partially reserved; unavailable resources: ${unavailable.joinToString()}."
            },
        )
    }

    @Transactional
    fun release(taskId: String): Int {
        var releasedCount = 0
        reservationRepository.findByTaskId(taskId)
            .filter { it.reservationStatus != "released" }
            .forEach { reservation ->
                decodeList(reservation.reservedResources).forEach { resourceType ->
                    val resource = resourceRepository.findByResourceType(resourceType)
                    if (resource != null) {
                        resource.availableUnits = minOf(resource.totalUnits, resource.availableUnits + 1)
                    }
                }
                reservation.reservationStatus = "released"
                releasedCount += 1
            }
        return releasedCount
    }

    private fun seedDefaultInventory() {
        defaultCapacities.forEach { (resourceType, capacity) ->
            if (!resourceRepository.existsById(resourceType)) {
                resourceRepository.save(
                    EmergencyResourceEntity(
                        resourceType = resourceType,
                        displayName = resourceType.replace("_", " "),
                        totalUnits = capacity,
                        availableUnits = capacity,
                    )
                )
            }
        }
    }

    private fun decodeList(value: String): List<String> =
        objectMapper.readValue(value, object : TypeReference<List<String>>() {})
}
