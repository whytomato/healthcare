package com.example.healthcare.care.service

import com.example.healthcare.care.model.CareCoordinationPlan
import com.example.healthcare.care.model.CareCoordinationRequest
import org.springframework.stereotype.Service

@Service
class CareCoordinationService {
    fun coordinate(request: CareCoordinationRequest): CareCoordinationPlan {
        val highUrgency = request.triageUrgency == "high" ||
            request.disposition.contains("emergency", ignoreCase = true)
        val referralActions = request.selectedSpecialties.map {
            "Schedule ${it.replace("_", " ")} review for task ${request.taskId}."
        }
        val followUpActions = if (highUrgency) {
            listOf("Arrange same-day reassessment after emergency review.")
        } else {
            listOf("Arrange routine outpatient follow-up after initial results are reviewed.")
        } + request.monitoringPlan
        val admissionActions = if (highUrgency) {
            listOf("Check emergency observation or admission capacity.", "Prepare admission handoff if physician confirms.")
        } else {
            listOf("No admission coordination required for outpatient pathway.")
        }

        return CareCoordinationPlan(
            taskId = request.taskId,
            patientId = request.patientId,
            status = "ready",
            disposition = request.disposition,
            followUpActions = followUpActions,
            referralActions = referralActions,
            admissionActions = admissionActions,
            humanReviewRequired = highUrgency || request.selectedSpecialties.size >= 3,
        )
    }
}
