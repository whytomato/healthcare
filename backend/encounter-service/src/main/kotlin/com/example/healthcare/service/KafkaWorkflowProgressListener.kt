package com.example.healthcare.service

import com.example.healthcare.config.HealthcareKafkaProperties
import com.example.healthcare.model.WorkflowProgressMessage
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.stereotype.Component

@Component
class KafkaWorkflowProgressListener(
    private val properties: HealthcareKafkaProperties,
    private val workflowProgressService: WorkflowProgressService,
) {
    @KafkaListener(
        topics = ["\${healthcare.kafka.workflow-progress-topic}"],
        groupId = "healthcare-backend-progress",
        autoStartup = "\${healthcare.kafka.enabled:false}",
        properties = [
            "spring.json.value.default.type=com.example.healthcare.model.WorkflowProgressMessage",
        ],
    )
    fun onProgress(message: WorkflowProgressMessage) {
        if (!properties.enabled) {
            return
        }
        workflowProgressService.saveProgress(message)
    }
}
