package com.example.healthcare.emergency.controller

import com.example.healthcare.emergency.model.EmergencyEncounter
import com.example.healthcare.emergency.model.EmergencyEncounterRequest
import com.example.healthcare.emergency.model.EmergencyReadinessUpdateRequest
import com.example.healthcare.emergency.service.EmergencyEncounterService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class EmergencyEncounterController(
    private val emergencyEncounterService: EmergencyEncounterService,
) {
    @PostMapping("/api/emergency/encounters")
    fun openEmergencyEncounter(
        @RequestBody request: EmergencyEncounterRequest,
    ): EmergencyEncounter = emergencyEncounterService.open(request)

    @PostMapping("/api/emergency/encounters/readiness")
    fun updateResourceReadiness(
        @RequestBody request: EmergencyReadinessUpdateRequest,
    ): EmergencyEncounter = emergencyEncounterService.updateReadiness(request)

    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "emergency-encounter-service", "status" to "ok")
}
