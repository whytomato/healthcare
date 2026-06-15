package com.example.healthcare.triage.controller

import com.example.healthcare.triage.model.TriageAssessmentRequest
import com.example.healthcare.triage.model.TriageAssessmentResponse
import com.example.healthcare.triage.service.TriageAssessmentService
import jakarta.validation.Valid
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/triage")
class TriageAssessmentController(
    private val triageAssessmentService: TriageAssessmentService,
) {
    @GetMapping("/health")
    fun health(): Map<String, String> = mapOf("service" to "triage-service", "status" to "ok")

    @PostMapping("/assess")
    fun assess(@Valid @RequestBody request: TriageAssessmentRequest): TriageAssessmentResponse =
        triageAssessmentService.assess(request)
}
