package com.example.healthcare.care.controller

import com.example.healthcare.care.model.CareCoordinationPlan
import com.example.healthcare.care.model.CareCoordinationRequest
import com.example.healthcare.care.service.CareCoordinationService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class CareCoordinationController(
    private val careCoordinationService: CareCoordinationService,
) {
    @PostMapping("/api/care/coordination-plans")
    fun createPlan(@RequestBody request: CareCoordinationRequest): CareCoordinationPlan =
        careCoordinationService.coordinate(request)

    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "care-coordination-service", "status" to "ok")
}
