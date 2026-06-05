package com.example.healthcare.service

import com.example.healthcare.config.HealthcareKafkaProperties
import com.example.healthcare.model.AiSymptomQueryMessage
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.stereotype.Component

@Component
class KafkaAiTaskPublisher(
    private val properties: HealthcareKafkaProperties,
    private val kafkaTemplate: KafkaTemplate<String, Any>,
) {
    fun publishSymptomQuery(message: AiSymptomQueryMessage): Boolean {
        if (!properties.enabled) {
            return false
        }
        kafkaTemplate.send(properties.symptomQueryTopic, message.taskId, message)
        return true
    }
}
