package com.example.healthcare.practitioner.service

import com.example.healthcare.practitioner.model.PractitionerAssignment
import com.example.healthcare.practitioner.model.PractitionerAssignmentEntity
import com.example.healthcare.practitioner.model.PractitionerAssignmentRequest
import com.fasterxml.jackson.core.type.TypeReference
import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
class PractitionerAssignmentService(
    private val practitionerRepository: PractitionerRepository,
    private val assignmentRepository: PractitionerAssignmentRepository,
    private val objectMapper: ObjectMapper,
) {
    @Transactional
    fun assign(request: PractitionerAssignmentRequest): PractitionerAssignment {
        val requiredSpecialties = buildList {
            add("emergency_physician")
            if (request.urgencyLevel == "high") {
                add("charge_nurse")
            }
            addAll(request.requiredSpecialties)
        }.distinct()
        val assigned = mutableListOf<String>()
        val unavailable = mutableListOf<String>()
        requiredSpecialties.forEach { specialty ->
            val practitioner = practitionerRepository.findBySpecialtyAndOnShiftTrue(specialty)
                .firstOrNull { it.activeAssignments < it.maxConcurrentAssignments }
            if (practitioner == null) {
                unavailable.add(specialty)
            } else {
                practitioner.activeAssignments += 1
                assigned.add(practitioner.practitionerId)
            }
        }
        val assignmentStatus = when {
            unavailable.isEmpty() -> "assigned"
            assigned.isEmpty() -> "unavailable"
            else -> "partial"
        }
        assignmentRepository.save(
            PractitionerAssignmentEntity(
                taskId = request.taskId,
                patientId = request.patientId,
                assignmentStatus = assignmentStatus,
                assignedPractitioners = objectMapper.writeValueAsString(assigned),
                unavailableSpecialties = objectMapper.writeValueAsString(unavailable),
            )
        )
        return PractitionerAssignment(
            taskId = request.taskId,
            patientId = request.patientId,
            assignmentStatus = assignmentStatus,
            assignedPractitioners = assigned,
            unavailableSpecialties = unavailable,
            message = if (unavailable.isEmpty()) {
                "Emergency practitioner assignment created."
            } else {
                "Emergency practitioner assignment partially created; unavailable specialties: ${unavailable.joinToString()}."
            },
        )
    }

    @Transactional
    fun release(taskId: String): Int {
        var releasedCount = 0
        assignmentRepository.findByTaskId(taskId)
            .filter { it.assignmentStatus != "released" }
            .forEach { assignment ->
                decodeList(assignment.assignedPractitioners).forEach { practitionerId ->
                    practitionerRepository.findById(practitionerId).ifPresent { practitioner ->
                        practitioner.activeAssignments = maxOf(0, practitioner.activeAssignments - 1)
                    }
                }
                assignment.assignmentStatus = "released"
                releasedCount += 1
            }
        return releasedCount
    }

    private fun decodeList(value: String): List<String> =
        objectMapper.readValue(value, object : TypeReference<List<String>>() {})
}
