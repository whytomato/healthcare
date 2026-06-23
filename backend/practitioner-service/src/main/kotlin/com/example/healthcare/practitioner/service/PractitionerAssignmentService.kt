package com.example.healthcare.practitioner.service

import com.example.healthcare.practitioner.model.PractitionerAssignment
import com.example.healthcare.practitioner.model.PractitionerAssignmentEntity
import com.example.healthcare.practitioner.model.PractitionerAssignmentRequest
import com.example.healthcare.practitioner.model.PractitionerEntity
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
    private val defaultPractitioners = listOf(
        PractitionerEntity("er-physician-1", "Emergency physician 1", "emergency_physician", true, 0, 1),
        PractitionerEntity("charge-nurse-1", "Charge nurse 1", "charge_nurse", true, 0, 2),
        PractitionerEntity("respiratory-consultant-1", "Respiratory consultant 1", "respiratory", true, 0, 1),
        PractitionerEntity("cardiology-consultant-1", "Cardiology consultant 1", "cardiology", true, 0, 1),
        PractitionerEntity("infectious-consultant-1", "Infectious disease consultant 1", "infectious_disease", true, 0, 1),
        PractitionerEntity("neurology-consultant-1", "Neurology consultant 1", "neurology", true, 0, 1),
    )

    @Transactional
    fun assign(request: PractitionerAssignmentRequest): PractitionerAssignment {
        seedDefaultPractitioners()
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

    private fun seedDefaultPractitioners() {
        defaultPractitioners.forEach { practitioner ->
            if (!practitionerRepository.existsById(practitioner.practitionerId)) {
                practitionerRepository.save(
                    PractitionerEntity(
                        practitionerId = practitioner.practitionerId,
                        displayName = practitioner.displayName,
                        specialty = practitioner.specialty,
                        onShift = practitioner.onShift,
                        activeAssignments = practitioner.activeAssignments,
                        maxConcurrentAssignments = practitioner.maxConcurrentAssignments,
                    )
                )
            }
        }
    }

    private fun decodeList(value: String): List<String> =
        objectMapper.readValue(value, object : TypeReference<List<String>>() {})
}
