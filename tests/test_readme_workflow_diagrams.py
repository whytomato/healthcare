from pathlib import Path


def test_readme_documents_demo_chain_and_branched_agent_workflow_diagrams() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "完整 Demo 链路" in readme
    assert "Spring Boot Backend" in readme
    assert "Kafka ai.symptom.query" in readme
    assert "Python AI Worker" in readme
    assert "ai.symptom.result" in readme

    assert "Branched Agent Hospital-lite Workflow" in readme
    assert "TriageNurseAgent" in readme
    assert "EmergencyPhysicianAgent" in readme
    assert "GeneralPractitionerAgent" in readme
    assert "DispositionCoordinatorAgent" in readme
    assert "AIConsultationTool" in readme
    assert "FinalHospitalReportAgent" in readme


def test_readme_documents_agent_tool_workflow_boundaries() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "app/agents/" in readme
    assert "app/tools/" in readme
    assert "app/workflows/" in readme
    assert "app/hospital/" not in readme
    assert "app/consultation/" not in readme


def test_readme_mermaid_quotes_route_labels_with_path_parameters() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert 'TaskAPI["GET /api/ai/tasks/{taskId}"]' in readme
    assert "TaskAPI[GET /api/ai/tasks/{taskId}]" not in readme
