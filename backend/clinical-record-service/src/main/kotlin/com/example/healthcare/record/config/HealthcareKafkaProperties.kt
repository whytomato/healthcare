package com.example.healthcare.record.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "healthcare.kafka")
data class HealthcareKafkaProperties(
    val enabled: Boolean = false,
    val symptomResultTopic: String = "ai.symptom.result",
)
