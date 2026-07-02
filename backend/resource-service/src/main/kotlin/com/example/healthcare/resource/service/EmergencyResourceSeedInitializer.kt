package com.example.healthcare.resource.service

import com.example.healthcare.resource.model.EmergencyResourceEntity
import org.springframework.boot.ApplicationArguments
import org.springframework.boot.ApplicationRunner
import org.springframework.stereotype.Component
import org.springframework.transaction.annotation.Transactional

@Component
class EmergencyResourceSeedInitializer(
    private val resourceRepository: EmergencyResourceRepository,
) : ApplicationRunner {
    private val defaultCapacities = mapOf(
        "resuscitation_room" to 1,
        "emergency_observation_bed" to 2,
        "portable_monitor" to 4,
        "cardiac_monitor" to 2,
        "neuro_observation_capacity" to 1,
        "exam_room" to 3,
    )

    @Transactional
    override fun run(args: ApplicationArguments) {
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
}
