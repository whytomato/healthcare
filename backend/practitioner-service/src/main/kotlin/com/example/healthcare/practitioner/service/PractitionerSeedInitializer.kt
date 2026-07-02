package com.example.healthcare.practitioner.service

import com.example.healthcare.practitioner.model.PractitionerEntity
import org.springframework.boot.ApplicationArguments
import org.springframework.boot.ApplicationRunner
import org.springframework.stereotype.Component
import org.springframework.transaction.annotation.Transactional

@Component
class PractitionerSeedInitializer(
    private val practitionerRepository: PractitionerRepository,
) : ApplicationRunner {
    private val defaultPractitioners = listOf(
        PractitionerEntity("er-physician-1", "Emergency physician 1", "emergency_physician", true, 0, 1),
        PractitionerEntity("charge-nurse-1", "Charge nurse 1", "charge_nurse", true, 0, 2),
        PractitionerEntity("respiratory-consultant-1", "Respiratory consultant 1", "respiratory", true, 0, 1),
        PractitionerEntity("cardiology-consultant-1", "Cardiology consultant 1", "cardiology", true, 0, 1),
        PractitionerEntity("infectious-consultant-1", "Infectious disease consultant 1", "infectious_disease", true, 0, 1),
        PractitionerEntity("neurology-consultant-1", "Neurology consultant 1", "neurology", true, 0, 1),
    )

    @Transactional
    override fun run(args: ApplicationArguments) {
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
}
