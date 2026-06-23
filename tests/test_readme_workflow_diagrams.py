from pathlib import Path


def test_readme_documents_demo_chain_and_branched_agent_workflow_diagrams() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "完整 Demo 链路" in readme
    assert "encounter-service" in readme
    assert "triage-service" in readme
    assert "Kafka healthcare.encounter.created" in readme
    assert "Kafka ai.symptom.query" in readme
    assert "Python AI Worker" in readme
    assert "ai.symptom.result" in readme

    assert "Branched Agent Hospital-lite Workflow" in readme
    assert "HospitalWorkflowPlanner" in readme
    assert "TriageNurseAgent" in readme
    assert "EmergencyPhysicianAgent" in readme
    assert "GeneralPractitionerAgent" in readme
    assert "DispositionCoordinatorAgent" in readme
    assert "AIConsultationTool" in readme
    assert "FinalHospitalReportAgent" in readme


def test_readme_documents_agent_tool_workflow_and_backend_boundaries() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "app/agents/" in readme
    assert "app/tools/" in readme
    assert "app/workflows/" in readme
    assert "backend/common-proto/" in readme
    assert "backend/encounter-service/" in readme
    assert "backend/triage-service/" in readme
    assert "PatientHistoryLookupTool" in readme
    assert "ClinicalToolRegistry" in readme
    assert "MedicationInteractionTool" in readme
    assert "BedAvailabilityTool" in readme
    assert "HistoryTool --> HistoryAPI" in readme
    assert "HistoryAPI --> Worker" not in readme
    assert "app/hospital/" not in readme
    assert "app/consultation/" not in readme


def test_readme_mermaid_quotes_route_labels_with_path_parameters() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert 'TaskAPI["GET /api/ai/tasks/{taskId}"]' in readme
    assert "TaskAPI[GET /api/ai/tasks/{taskId}]" not in readme


def test_readme_documents_care_coordination_service_api() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "POST http://localhost:8084/api/care/coordination-plans" in readme
    assert "GET  http://localhost:8084/health" in readme


def test_readme_documents_service_lifecycle_scripts_for_manual_testing() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "scripts\\start-healthcare-services.ps1" in readme
    assert "scripts\\stop-healthcare-services.ps1" in readme
    assert "-CoreOnly" in readme
    assert "-Verify" in readme
    assert "verify-healthcare-services.ps1 -CoreOnly" in readme
    assert "outputs\\service-logs" in readme
    assert "outputs\\healthcare-services.pids.json" in readme


def test_readme_documents_encounter_and_record_service_boundaries() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "encounter service persists `patient_encounters` and realtime `workflow_progress_events`" in readme
    assert "`/api/ai/tasks/{taskId}` returns the Patient Encounter task state" in readme
    assert "not the full workflow result JSON" in readme
    assert "clinical record service persists the complete `workflow_result_records`" in readme
    assert "followUpActions" in readme
    assert "referralActions" in readme
    assert "admissionActions" in readme
