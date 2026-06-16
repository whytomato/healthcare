from pathlib import Path


def test_clinical_record_service_exposes_workflow_result_storage_contract() -> None:
    pom = Path("backend/clinical-record-service/pom.xml").read_text(encoding="utf-8")
    application_yml = Path(
        "backend/clinical-record-service/src/main/resources/application.yml"
    ).read_text(encoding="utf-8")
    controller = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/controller/ClinicalRecordController.kt"
    ).read_text(encoding="utf-8")
    record = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/WorkflowResultRecord.kt"
    ).read_text(encoding="utf-8")
    entity = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/WorkflowResultRecordEntity.kt"
    ).read_text(encoding="utf-8")
    repository = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/JpaWorkflowResultRecordRepository.kt"
    ).read_text(encoding="utf-8")
    service = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/ClinicalRecordService.kt"
    ).read_text(encoding="utf-8")

    assert "spring-boot-starter-data-jpa" in pom
    assert "<artifactId>postgresql</artifactId>" in pom
    assert "jdbc:postgresql://localhost:5432/healthcare" in application_yml
    assert "ddl-auto: update" in application_yml
    assert '@RequestMapping("/api/records")' in controller
    assert '@PostMapping("/workflow-results")' in controller
    assert '@GetMapping("/{taskId}")' in controller
    assert "taskId: String" in record
    assert "executedPath: List<String>" in record
    assert "workflowDecisions: Any?" in record
    assert "handoffTimeline: Any?" in record
    assert "carePathway: Any?" in record
    assert "aiConsultation: Any?" in record
    assert 'handoffTimeline = result["handoff_timeline"]' in service
    assert '@Table(name = "workflow_result_records")' in entity
    assert "handoffTimelineJson" in entity
    assert "rawResultJson" in entity
    assert (
        "interface JpaWorkflowResultRecordRepository : "
        "JpaRepository<WorkflowResultRecordEntity, String>"
    ) in repository
    assert "private val repository: JpaWorkflowResultRecordRepository" in service
    assert "repository.save" in service
    assert "repository.findById" in service
    assert "ConcurrentHashMap" not in service


def test_clinical_record_service_consumes_workflow_results_from_kafka() -> None:
    application = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/ClinicalRecordServiceApplication.kt"
    ).read_text(encoding="utf-8")
    config = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/config/HealthcareKafkaProperties.kt"
    ).read_text(encoding="utf-8")
    listener = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/KafkaWorkflowResultListener.kt"
    ).read_text(encoding="utf-8")
    model = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/AiSymptomResultMessage.kt"
    ).read_text(encoding="utf-8")
    application_yml = Path(
        "backend/clinical-record-service/src/main/resources/application.yml"
    ).read_text(encoding="utf-8")

    assert "@ConfigurationPropertiesScan" in application
    assert 'symptomResultTopic: String = "ai.symptom.result"' in config
    assert '@KafkaListener(' in listener
    assert 'topics = ["\\${healthcare.kafka.symptom-result-topic}"]' in listener
    assert "clinicalRecordService.saveWorkflowResult" in listener
    assert "WorkflowResultRequest(" in listener
    assert "result: Map<String, Any?>?" in model
    assert "symptom-result-topic: ai.symptom.result" in application_yml
    assert "healthcare-clinical-record-service" in application_yml


def test_clinical_record_service_exposes_patient_history_summary_by_patient_id() -> None:
    controller = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/controller/ClinicalRecordController.kt"
    ).read_text(encoding="utf-8")
    record = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/WorkflowResultRecord.kt"
    ).read_text(encoding="utf-8")
    entity = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/WorkflowResultRecordEntity.kt"
    ).read_text(encoding="utf-8")
    repository = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/JpaWorkflowResultRecordRepository.kt"
    ).read_text(encoding="utf-8")
    service = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/ClinicalRecordService.kt"
    ).read_text(encoding="utf-8")
    summary = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/model/PatientHistorySummary.kt"
    )

    assert summary.exists()
    summary_text = summary.read_text(encoding="utf-8")

    assert '@GetMapping("/patients/{patientId}/history")' in controller
    assert "getPatientHistory(@PathVariable patientId: String): PatientHistorySummary" in controller
    assert "patientId: String?" in record
    assert '@Column(name = "patient_id")' in entity
    assert "var patientId: String? = null" in entity
    assert "findByPatientIdOrderByUpdatedAtDesc" in repository
    assert "fun getPatientHistory(patientId: String): PatientHistorySummary" in service
    assert 'patientId = result["patient_id"]?.toString()' in service
    assert "data class PatientHistorySummary" in summary_text
    assert "recentEncounters: List<PatientHistoryEncounter>" in summary_text
    assert "knownConditions: List<String>" in summary_text
    assert "allergies: List<String>" in summary_text
    assert "currentMedications: List<String>" in summary_text
    assert "previousDispositions: List<String>" in summary_text
    assert "lastFinalReports: List<String>" in summary_text
    assert "extractStructuredJsonSummary" in service
    assert "stripJsonFence" in service
    assert "lines.first().trim().lowercase() in setOf(\"```json\", \"```\")" in service
