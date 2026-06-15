package com.example.healthcare.triage

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.runApplication

@SpringBootApplication
@ConfigurationPropertiesScan
class TriageServiceApplication

fun main(args: Array<String>) {
    runApplication<TriageServiceApplication>(*args)
}
