package com.example.healthcare.service

import com.example.healthcare.config.HealthcareKafkaProperties
import com.example.healthcare.model.AiSymptomResultMessage
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.stereotype.Component

@Component
class KafkaAiResultListener(
    private val properties: HealthcareKafkaProperties,
    private val taskService: AiTaskService,
) {
    @KafkaListener(
        topics = ["\${healthcare.kafka.symptom-result-topic}"],
        groupId = "healthcare-backend",
        autoStartup = "\${healthcare.kafka.enabled:false}",
    )
    fun onResult(message: AiSymptomResultMessage) {
        if (properties.enabled) {
            taskService.applyResult(message)
        }
    }
}
