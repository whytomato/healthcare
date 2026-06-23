package com.example.healthcare.practitioner

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class PractitionerServiceApplication

fun main(args: Array<String>) {
    runApplication<PractitionerServiceApplication>(*args)
}
