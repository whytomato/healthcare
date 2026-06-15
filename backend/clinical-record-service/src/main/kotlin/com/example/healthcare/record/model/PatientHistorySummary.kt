package com.example.healthcare.record.model

import java.time.Instant

data class PatientHistorySummary(
    val patientId: String,
    val recentEncounters: List<PatientHistoryEncounter> = emptyList(),
    val knownConditions: List<String> = emptyList(),
    val allergies: List<String> = emptyList(),
    val currentMedications: List<String> = emptyList(),
    val previousDispositions: List<String> = emptyList(),
    val lastFinalReports: List<String> = emptyList(),
)

data class PatientHistoryEncounter(
    val taskId: String,
    val status: String,
    val updatedAt: Instant,
    val selectedSpecialties: List<String> = emptyList(),
    val disposition: String? = null,
    val reportExcerpt: String? = null,
)
