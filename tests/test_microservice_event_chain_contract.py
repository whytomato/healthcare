from pathlib import Path

from app.contracts import SymptomQueryTask
from app.worker import kafka_worker


class FakeHospitalOrchestrator:
    last_metadata: dict | None = None

    def run(
        self,
        case_text: str,
        patient_id: str | None,
        doctor_id: str | None,
        language: str,
        progress_publisher=None,
        metadata=None,
    ) -> dict:
        self.__class__.last_metadata = metadata
        if progress_publisher is not None:
            progress_publisher(
                {
                    "event_type": "agent_completed",
                    "agent": "registration_agent",
                    "event_index": 0,
                }
            )
        return {
            "workflow": "agent_hospital_lite",
            "agent_results": [{"agent": "final_hospital_report_agent", "status": "ready"}],
        }


def test_encounter_service_publishes_patient_encounter_event_not_ai_workflow_task() -> None:
    properties = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/config/HealthcareKafkaProperties.kt"
    ).read_text(encoding="utf-8")
    publisher = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/KafkaAiTaskPublisher.kt"
    ).read_text(encoding="utf-8")
    task_service = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/AiTaskService.kt"
    ).read_text(encoding="utf-8")

    assert 'encounterTopic: String = "healthcare.encounter.created"' in properties
    assert "publishPatientEncounter" in publisher
    assert "properties.encounterTopic" in publisher
    assert "PatientEncounterMessage" in task_service
    assert "publishPatientEncounter" in task_service
    assert "publishSymptomQuery" not in task_service


def test_triage_service_consumes_encounter_event_and_publishes_ai_workflow_task() -> None:
    listener = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/service/KafkaEncounterListener.kt"
    ).read_text(encoding="utf-8")
    publisher = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/service/KafkaAiWorkflowPublisher.kt"
    ).read_text(encoding="utf-8")
    model = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/model/AiWorkflowTaskMessage.kt"
    ).read_text(encoding="utf-8")

    assert '@KafkaListener(topics = ["\\${healthcare.kafka.encounter-topic}"]' in listener
    assert "triageAssessmentService.assess" in listener
    assert "publishAiWorkflowTask" in publisher
    assert "properties.aiWorkflowTopic" in publisher
    assert "triageAssessment" in model
    assert 'source" to "triage-service"' in listener


def test_kafka_json_messages_do_not_depend_on_java_type_headers_across_services() -> None:
    encounter_yml = Path("backend/encounter-service/src/main/resources/application.yml").read_text(
        encoding="utf-8"
    )
    triage_yml = Path("backend/triage-service/src/main/resources/application.yml").read_text(
        encoding="utf-8"
    )
    record_yml = Path(
        "backend/clinical-record-service/src/main/resources/application.yml"
    ).read_text(encoding="utf-8")

    assert "spring.json.add.type.headers: false" in encounter_yml
    assert "spring.json.use.type.headers: false" in triage_yml
    assert "spring.json.add.type.headers: false" in triage_yml
    assert "spring.json.use.type.headers: false" in encounter_yml
    assert "spring.json.use.type.headers: false" in record_yml


def test_python_worker_accepts_triage_metadata_from_ai_workflow_task() -> None:
    worker = Path("app/worker/kafka_worker.py").read_text(encoding="utf-8")
    contracts = Path("app/contracts.py").read_text(encoding="utf-8")

    assert "metadata: dict[str, Any]" in contracts
    assert 'result["input_metadata"] = task.metadata' in worker
    assert "load_patient_history" not in worker


def test_python_worker_preserves_triage_metadata_in_workflow_result(monkeypatch) -> None:
    monkeypatch.setattr(kafka_worker, "HospitalOrchestrator", FakeHospitalOrchestrator)

    result = kafka_worker.process_task(
        SymptomQueryTask(
            task_id="t001",
            case_text="fever and cough",
            question="Run hospital workflow",
            patient_id="p001",
            doctor_id="d001",
            metadata={
                "source": "triage-service",
                "triageUrgencyLevel": "standard",
                "triageRecommendedDepartment": "general_medicine",
            },
        )
    )

    assert result.status == "ready"
    assert result.result is not None
    assert result.result["input_metadata"]["source"] == "triage-service"
    assert result.result["input_metadata"]["triageUrgencyLevel"] == "standard"
    assert FakeHospitalOrchestrator.last_metadata is not None
    assert FakeHospitalOrchestrator.last_metadata["taskId"] == "t001"
    assert FakeHospitalOrchestrator.last_metadata["task_id"] == "t001"
    assert FakeHospitalOrchestrator.last_metadata["source"] == "triage-service"


def test_python_worker_leaves_patient_history_lookup_to_hospital_agents(monkeypatch) -> None:
    monkeypatch.setattr(kafka_worker, "HospitalOrchestrator", FakeHospitalOrchestrator)

    class FakePatientHistoryClient:
        def get_patient_history(self, patient_id: str) -> dict:
            raise AssertionError("worker should not prefetch patient history")

    result = kafka_worker.process_task(
        SymptomQueryTask(
            task_id="t-history",
            case_text="follow-up cough visit",
            question="Run hospital workflow",
            patient_id="p-history-001",
            doctor_id="d001",
        ),
        patient_history_client=FakePatientHistoryClient(),
    )

    assert result.status == "ready"
    assert result.result is not None
    assert "patient_history" not in result.result
    assert FakeHospitalOrchestrator.last_metadata is not None
    assert FakeHospitalOrchestrator.last_metadata["taskId"] == "t-history"


def test_python_worker_can_emit_realtime_agent_progress(monkeypatch) -> None:
    monkeypatch.setattr(kafka_worker, "HospitalOrchestrator", FakeHospitalOrchestrator)
    progress_events: list[dict] = []

    result = kafka_worker.process_task(
        SymptomQueryTask(
            task_id="t-progress",
            case_text="fever and cough",
            question="Run hospital workflow",
            patient_id="p001",
            doctor_id="d001",
        ),
        progress_publisher=progress_events.append,
    )

    assert result.status == "ready"
    assert progress_events[0]["taskId"] == "t-progress"
    assert progress_events[0]["eventType"] == "agent_completed"
    assert progress_events[0]["agent"] == "registration_agent"
    assert progress_events[0]["eventIndex"] == 0
    assert progress_events[0]["targetAgents"] == []


def test_python_worker_maps_agent_tool_use_to_realtime_progress_payload() -> None:
    payload = kafka_worker.to_backend_progress_payload(
        "t-tool",
        {
            "event_type": "tool_invoked",
            "agent": "registration_agent",
            "decision": "patient_history_lookup",
            "decision_scope": "tool_use",
            "reason": "identify whether this is a new or returning patient",
            "payload": {
                "tool": "patient_history_lookup",
                "status": "ready",
                "patientId": "p001",
            },
            "event_index": 2,
        },
    )

    assert payload["taskId"] == "t-tool"
    assert payload["eventType"] == "tool_invoked"
    assert payload["agent"] == "registration_agent"
    assert payload["decision"] == "patient_history_lookup"
    assert payload["decisionScope"] == "tool_use"
    assert payload["payload"]["tool"] == "patient_history_lookup"
    assert payload["eventIndex"] == 2


def test_python_kafka_worker_publishes_realtime_agent_progress_topic() -> None:
    worker = Path("app/worker/kafka_worker.py").read_text(encoding="utf-8")

    assert 'DEFAULT_PROGRESS_TOPIC = "ai.workflow.progress"' in worker
    assert 'parser.add_argument("--progress-topic", default=DEFAULT_PROGRESS_TOPIC)' in worker
    assert "progress_topic: str" in worker
    assert "producer.send(progress_topic" in worker


def test_encounter_service_stores_realtime_agent_progress_events() -> None:
    properties = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/config/HealthcareKafkaProperties.kt"
    ).read_text(encoding="utf-8")
    application_yml = Path("backend/encounter-service/src/main/resources/application.yml").read_text(
        encoding="utf-8"
    )
    controller = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/controller/AiTaskController.kt"
    ).read_text(encoding="utf-8")
    listener = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/KafkaWorkflowProgressListener.kt"
    )
    entity = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/model/WorkflowProgressEventEntity.kt"
    )
    service = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/WorkflowProgressService.kt"
    )

    assert 'workflowProgressTopic: String = "ai.workflow.progress"' in properties
    assert "workflow-progress-topic: ai.workflow.progress" in application_yml
    assert '@GetMapping("/tasks/{taskId}/progress")' in controller
    assert "workflowProgressService.getProgress(taskId)" in controller
    assert listener.is_file()
    assert "WorkflowProgressMessage" in listener.read_text(encoding="utf-8")
    assert "workflow-progress-topic" in listener.read_text(encoding="utf-8")
    assert "spring.json.value.default.type=com.example.healthcare.model.WorkflowProgressMessage" in listener.read_text(encoding="utf-8")
    assert entity.is_file()
    assert '@Table(name = "workflow_progress_events")' in entity.read_text(encoding="utf-8")
    assert service.is_file()
    assert "findByTaskIdOrderByEventIndexAsc" in service.read_text(encoding="utf-8")


def test_encounter_service_uses_listener_specific_kafka_json_types_for_result_and_progress() -> None:
    application_yml = Path("backend/encounter-service/src/main/resources/application.yml").read_text(
        encoding="utf-8"
    )
    result_listener = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/KafkaAiResultListener.kt"
    ).read_text(encoding="utf-8")
    progress_listener = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/KafkaWorkflowProgressListener.kt"
    ).read_text(encoding="utf-8")

    assert "spring.json.value.default.type:" not in application_yml
    assert "spring.json.value.default.type=com.example.healthcare.model.AiSymptomResultMessage" in result_listener
    assert "spring.json.value.default.type=com.example.healthcare.model.WorkflowProgressMessage" in progress_listener


def test_encounter_service_tracks_result_status_without_persisting_workflow_result() -> None:
    entity = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/model/AiTaskEntity.kt"
    ).read_text(encoding="utf-8")
    model = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/model/AiTask.kt"
    ).read_text(encoding="utf-8")
    repository = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/AiTaskRepository.kt"
    ).read_text(encoding="utf-8")
    task_service = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/AiTaskService.kt"
    ).read_text(encoding="utf-8")
    record_service = Path(
        "backend/clinical-record-service/src/main/kotlin/com/example/healthcare/record/service/ClinicalRecordService.kt"
    ).read_text(encoding="utf-8")
    docs = Path("docs/BUSINESS_FLOW.md").read_text(encoding="utf-8")

    assert "resultJson" not in entity
    assert "result: Any?" not in model
    assert "task.result =" not in task_service
    assert "resultJson =" not in repository
    assert "result = resultJson" not in repository
    assert "rawResultJson" in record_service
    assert "encounter-service 只维护 task 状态" in docs
    assert "clinical-record-service 负责完整 Workflow Record" in docs
