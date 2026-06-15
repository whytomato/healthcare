package com.example.healthcare.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "healthcare.kafka")
data class HealthcareKafkaProperties(
    val enabled: Boolean = false,
    val encounterTopic: String = "healthcare.encounter.created",
    val symptomResultTopic: String = "ai.symptom.result",
    val workflowProgressTopic: String = "ai.workflow.progress",
)
