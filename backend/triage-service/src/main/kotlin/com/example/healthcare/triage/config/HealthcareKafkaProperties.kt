package com.example.healthcare.triage.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "healthcare.kafka")
data class HealthcareKafkaProperties(
    val enabled: Boolean = false,
    val encounterTopic: String = "healthcare.encounter.created",
    val aiWorkflowTopic: String = "ai.symptom.query",
)
