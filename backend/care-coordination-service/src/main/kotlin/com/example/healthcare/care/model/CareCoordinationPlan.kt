package com.example.healthcare.care.model

data class CareCoordinationPlan(
    val taskId: String,
    val patientId: String?,
    val status: String,
    val disposition: String,
    val followUpActions: List<String>,
    val referralActions: List<String>,
    val admissionActions: List<String>,
    val humanReviewRequired: Boolean,
)
