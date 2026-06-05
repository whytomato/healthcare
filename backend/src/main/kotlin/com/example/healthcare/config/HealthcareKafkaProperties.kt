package com.example.healthcare.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "healthcare.kafka")
data class HealthcareKafkaProperties(
    val enabled: Boolean = false,
    val symptomQueryTopic: String = "ai.symptom.query",
    val symptomResultTopic: String = "ai.symptom.result",
)
