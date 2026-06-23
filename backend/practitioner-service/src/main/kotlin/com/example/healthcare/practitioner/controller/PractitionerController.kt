package com.example.healthcare.practitioner.controller

import com.example.healthcare.practitioner.model.PractitionerAssignment
import com.example.healthcare.practitioner.model.PractitionerAssignmentRequest
import com.example.healthcare.practitioner.service.PractitionerAssignmentService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class PractitionerController(
    private val assignmentService: PractitionerAssignmentService,
) {
    @PostMapping("/api/practitioners/emergency-assignments")
    fun assignEmergencyPractitioners(
        @RequestBody request: PractitionerAssignmentRequest,
    ): PractitionerAssignment = assignmentService.assign(request)

    @PostMapping("/api/practitioners/emergency-assignments/{taskId}/release")
    fun releaseEmergencyPractitioners(@PathVariable taskId: String): Map<String, Any> =
        mapOf("taskId" to taskId, "released" to assignmentService.release(taskId))

    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "practitioner-service", "status" to "ok")
}
