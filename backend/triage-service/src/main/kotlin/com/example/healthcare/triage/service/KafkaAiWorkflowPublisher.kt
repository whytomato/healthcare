package com.example.healthcare.triage.service

import com.example.healthcare.triage.config.HealthcareKafkaProperties
import com.example.healthcare.triage.model.AiWorkflowTaskMessage
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.stereotype.Component

@Component
class KafkaAiWorkflowPublisher(
    private val properties: HealthcareKafkaProperties,
    private val kafkaTemplate: KafkaTemplate<String, Any>,
) {
    fun publishAiWorkflowTask(message: AiWorkflowTaskMessage): Boolean {
        if (!properties.enabled) {
            return false
        }
        kafkaTemplate.send(properties.aiWorkflowTopic, message.taskId, message)
        return true
    }
}
