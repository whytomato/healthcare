package com.example.healthcare.scheduling

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class SchedulingServiceApplication

fun main(args: Array<String>) {
    runApplication<SchedulingServiceApplication>(*args)
}
