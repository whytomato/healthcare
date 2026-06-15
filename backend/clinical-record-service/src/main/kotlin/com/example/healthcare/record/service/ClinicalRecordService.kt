package com.example.healthcare.record.service

import com.fasterxml.jackson.databind.ObjectMapper
import com.example.healthcare.record.model.PatientHistoryEncounter
import com.example.healthcare.record.model.PatientHistorySummary
import com.example.healthcare.record.model.WorkflowResultRecord
import com.example.healthcare.record.model.WorkflowResultRecordEntity
import com.example.healthcare.record.model.WorkflowResultRequest
import org.springframework.stereotype.Service
import java.time.Instant

@Service
class ClinicalRecordService(
    private val repository: JpaWorkflowResultRecordRepository,
    private val objectMapper: ObjectMapper,
) {
    fun saveWorkflowResult(request: WorkflowResultRequest): WorkflowResultRecord {
        val result = request.result.orEmpty()
        val record = WorkflowResultRecord(
            taskId = request.taskId,
            patientId = result["patient_id"]?.toString(),
            status = request.status,
            executedPath = result["executed_path"].asStringList(),
            workflowDecisions = result["workflow_decisions"],
            handoffTimeline = result["handoff_timeline"],
            selectedSpecialties = result["selected_specialties"].asStringList(),
            carePathway = result["care_pathway"],
            aiConsultation = result["ai_consultation"],
            finalReport = result["final_report"],
            rawResult = request.result,
            errorMessage = request.errorMessage,
            updatedAt = Instant.now(),
        )
        return repository.save(record.toEntity(objectMapper)).toModel(objectMapper)
    }

    fun getWorkflowResult(taskId: String): WorkflowResultRecord =
        repository.findById(taskId)
            .map { it.toModel(objectMapper) }
            .orElseThrow { NoSuchElementException("Workflow result not found: $taskId") }

    fun getPatientHistory(patientId: String): PatientHistorySummary {
        val records = repository.findByPatientIdOrderByUpdatedAtDesc(patientId)
            .map { it.toModel(objectMapper) }
        return PatientHistorySummary(
            patientId = patientId,
            recentEncounters = records.take(5).map { it.toHistoryEncounter() },
            knownConditions = records.flatMap { it.carePathway.extractStrings("known_conditions") }.distinct(),
            allergies = records.flatMap { it.carePathway.extractStrings("allergies") }.distinct(),
            currentMedications = records.flatMap { it.carePathway.extractStrings("current_medications") }.distinct(),
            previousDispositions = records.mapNotNull { it.dispositionText() }.distinct(),
            lastFinalReports = records.mapNotNull { it.finalReportText() }.take(3),
        )
    }

    private fun Any?.asStringList(): List<String> =
        when (this) {
            is List<*> -> this.mapNotNull { it?.toString() }
            else -> emptyList()
        }
}

private fun WorkflowResultRecord.toEntity(objectMapper: ObjectMapper): WorkflowResultRecordEntity =
    WorkflowResultRecordEntity(
        taskId = taskId,
        status = status,
        patientId = patientId,
        executedPathJson = objectMapper.writeValueAsString(executedPath),
        workflowDecisionsJson = workflowDecisions.toJsonOrNull(objectMapper),
        handoffTimelineJson = handoffTimeline.toJsonOrNull(objectMapper),
        selectedSpecialtiesJson = objectMapper.writeValueAsString(selectedSpecialties),
        carePathwayJson = carePathway.toJsonOrNull(objectMapper),
        aiConsultationJson = aiConsultation.toJsonOrNull(objectMapper),
        finalReportJson = finalReport.toJsonOrNull(objectMapper),
        rawResultJson = rawResult.toJsonOrNull(objectMapper),
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )

private fun WorkflowResultRecordEntity.toModel(objectMapper: ObjectMapper): WorkflowResultRecord =
    WorkflowResultRecord(
        taskId = taskId,
        patientId = patientId,
        status = status,
        executedPath = executedPathJson.toStringList(objectMapper),
        workflowDecisions = workflowDecisionsJson.toAnyOrNull(objectMapper),
        handoffTimeline = handoffTimelineJson.toAnyOrNull(objectMapper),
        selectedSpecialties = selectedSpecialtiesJson.toStringList(objectMapper),
        carePathway = carePathwayJson.toAnyOrNull(objectMapper),
        aiConsultation = aiConsultationJson.toAnyOrNull(objectMapper),
        finalReport = finalReportJson.toAnyOrNull(objectMapper),
        rawResult = rawResultJson.toAnyOrNull(objectMapper),
        errorMessage = errorMessage,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )

private fun Any?.toJsonOrNull(objectMapper: ObjectMapper): String? =
    this?.let { objectMapper.writeValueAsString(it) }

private fun String?.toAnyOrNull(objectMapper: ObjectMapper): Any? =
    this?.let { objectMapper.readValue(it, Any::class.java) }

private fun String?.toStringList(objectMapper: ObjectMapper): List<String> =
    when (val value = toAnyOrNull(objectMapper)) {
        is List<*> -> value.mapNotNull { it?.toString() }
        else -> emptyList()
    }

private fun WorkflowResultRecord.toHistoryEncounter(): PatientHistoryEncounter =
    PatientHistoryEncounter(
        taskId = taskId,
        status = status,
        updatedAt = updatedAt,
        selectedSpecialties = selectedSpecialties,
        disposition = dispositionText(),
        reportExcerpt = finalReportText(),
    )

private fun WorkflowResultRecord.dispositionText(): String? =
    when (val raw = rawResult.extract("disposition")) {
        is Map<*, *> -> (raw["decision"] ?: raw["disposition"] ?: raw["status"])?.toString()
        is String -> raw
        else -> null
    }

private fun WorkflowResultRecord.finalReportText(): String? =
    finalReport.extractReportText()?.takeIf { it.isNotBlank() }

private fun Any?.extract(path: String): Any? =
    when (this) {
        is Map<*, *> -> this[path]
        else -> null
    }

private fun Any?.extractStrings(key: String): List<String> =
    when (val value = extract(key)) {
        is List<*> -> value.mapNotNull { it?.toString() }
        is String -> listOf(value)
        else -> emptyList()
    }

private fun Any?.extractReportText(): String? {
    val value = this as? Map<*, *> ?: return this as? String
    for (key in listOf("summary", "report_summary", "markdown", "content", "text")) {
        val candidate = value[key]
        if (candidate is String) {
            return candidate
        }
    }
    val data = value["data"] as? Map<*, *>
    if (data != null) {
        for (key in listOf("report_summary", "summary", "markdown", "content", "text")) {
            val candidate = data[key]
            if (candidate is String) {
                return candidate
            }
        }
    }
    val findings = value["findings"] as? List<*>
    return findings?.firstOrNull()?.toString()
}
