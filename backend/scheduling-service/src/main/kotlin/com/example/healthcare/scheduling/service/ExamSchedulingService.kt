package com.example.healthcare.scheduling.service

import com.example.healthcare.scheduling.model.ExamSchedule
import com.example.healthcare.scheduling.model.ExamSchedulingRequest
import org.springframework.stereotype.Service

@Service
class ExamSchedulingService {
    fun schedule(request: ExamSchedulingRequest): ExamSchedule {
        val prefix = if (request.urgencyLevel == "high") "stat" else "routine"
        return ExamSchedule(
            taskId = request.taskId,
            patientId = request.patientId,
            orderingAgent = request.orderingAgent,
            scheduleStatus = "scheduled",
            scheduledExams = request.requestedExams.map { "$prefix:$it" },
            message = "Emergency exam schedule created.",
        )
    }
}
