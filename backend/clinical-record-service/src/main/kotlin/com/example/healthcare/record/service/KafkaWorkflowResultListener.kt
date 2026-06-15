package com.example.healthcare.record.service

import com.example.healthcare.record.config.HealthcareKafkaProperties
import com.example.healthcare.record.model.AiSymptomResultMessage
import com.example.healthcare.record.model.WorkflowResultRequest
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.stereotype.Component

@Component
class KafkaWorkflowResultListener(
    private val properties: HealthcareKafkaProperties,
    private val clinicalRecordService: ClinicalRecordService,
) {
    @KafkaListener(
        topics = ["\${healthcare.kafka.symptom-result-topic}"],
        groupId = "healthcare-clinical-record-service",
        autoStartup = "\${healthcare.kafka.enabled:false}",
    )
    fun onWorkflowResult(message: AiSymptomResultMessage) {
        if (!properties.enabled) {
            return
        }
        clinicalRecordService.saveWorkflowResult(
            WorkflowResultRequest(
                taskId = message.taskId,
                status = message.status,
                result = message.result,
                errorMessage = message.errorMessage,
            )
        )
    }
}
