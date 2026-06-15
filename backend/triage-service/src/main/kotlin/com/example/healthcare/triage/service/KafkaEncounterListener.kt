package com.example.healthcare.triage.service

import com.example.healthcare.triage.config.HealthcareKafkaProperties
import com.example.healthcare.triage.model.AiWorkflowTaskMessage
import com.example.healthcare.triage.model.PatientEncounterMessage
import com.example.healthcare.triage.model.TriageAssessmentRequest
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.stereotype.Component

@Component
class KafkaEncounterListener(
    private val properties: HealthcareKafkaProperties,
    private val triageAssessmentService: TriageAssessmentService,
    private val aiWorkflowPublisher: KafkaAiWorkflowPublisher,
) {
    @KafkaListener(topics = ["\${healthcare.kafka.encounter-topic}"], autoStartup = "\${healthcare.kafka.enabled:false}")
    fun onPatientEncounter(message: PatientEncounterMessage) {
        if (!properties.enabled) {
            return
        }
        val triageAssessment = triageAssessmentService.assess(
            TriageAssessmentRequest(
                encounterId = message.taskId,
                patientId = message.patientId,
                caseText = message.caseText,
                language = message.language,
            )
        )
        aiWorkflowPublisher.publishAiWorkflowTask(
            AiWorkflowTaskMessage(
                taskId = message.taskId,
                doctorId = message.doctorId,
                patientId = message.patientId,
                caseText = message.caseText,
                question = message.question,
                language = message.language,
                metadata = message.metadata + mapOf(
                    "source" to "triage-service",
                    "triageUrgencyLevel" to triageAssessment.urgencyLevel,
                    "triageRecommendedDepartment" to triageAssessment.recommendedDepartment,
                    "triageRedFlags" to triageAssessment.redFlags,
                ),
                triageAssessment = triageAssessment,
            )
        )
    }
}
