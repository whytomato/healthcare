package com.example.healthcare.record

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.runApplication

@SpringBootApplication
@ConfigurationPropertiesScan
class ClinicalRecordServiceApplication

fun main(args: Array<String>) {
    runApplication<ClinicalRecordServiceApplication>(*args)
}
