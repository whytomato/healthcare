package com.example.healthcare.record.controller

import com.example.healthcare.record.model.WorkflowResultRecord
import com.example.healthcare.record.model.WorkflowResultRequest
import com.example.healthcare.record.model.PatientHistorySummary
import com.example.healthcare.record.service.ClinicalRecordService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/records")
class ClinicalRecordController(
    private val clinicalRecordService: ClinicalRecordService,
) {
    @GetMapping("/health")
    fun health(): Map<String, String> =
        mapOf("service" to "clinical-record-service", "status" to "ok")

    @PostMapping("/workflow-results")
    fun saveWorkflowResult(@RequestBody request: WorkflowResultRequest): WorkflowResultRecord =
        clinicalRecordService.saveWorkflowResult(request)

    @GetMapping("/{taskId}")
    fun getWorkflowResult(@PathVariable taskId: String): WorkflowResultRecord =
        clinicalRecordService.getWorkflowResult(taskId)

    @GetMapping("/patients/{patientId}/history")
    fun getPatientHistory(@PathVariable patientId: String): PatientHistorySummary =
        clinicalRecordService.getPatientHistory(patientId)
}
