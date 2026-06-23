package com.example.healthcare.scheduling.controller

import com.example.healthcare.scheduling.model.ExamSchedule
import com.example.healthcare.scheduling.model.ExamSchedulingRequest
import com.example.healthcare.scheduling.service.ExamSchedulingService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class SchedulingController(
    private val schedulingService: ExamSchedulingService,
) {
    @PostMapping("/api/schedules/emergency-exams")
    fun scheduleEmergencyExams(@RequestBody request: ExamSchedulingRequest): ExamSchedule =
        schedulingService.schedule(request)

    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "scheduling-service", "status" to "ok")
}
