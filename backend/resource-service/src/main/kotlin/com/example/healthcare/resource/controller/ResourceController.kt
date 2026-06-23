package com.example.healthcare.resource.controller

import com.example.healthcare.resource.model.ResourceReservation
import com.example.healthcare.resource.model.ResourceReservationRequest
import com.example.healthcare.resource.service.ResourceReservationService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class ResourceController(
    private val reservationService: ResourceReservationService,
) {
    @PostMapping("/api/resources/emergency-reservations")
    fun reserveEmergencyResources(
        @RequestBody request: ResourceReservationRequest,
    ): ResourceReservation = reservationService.reserve(request)

    @PostMapping("/api/resources/emergency-reservations/{taskId}/release")
    fun releaseEmergencyResources(@PathVariable taskId: String): Map<String, Any> =
        mapOf("taskId" to taskId, "released" to reservationService.release(taskId))

    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "resource-service", "status" to "ok")
}
