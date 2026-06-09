from pathlib import Path


def test_readme_documents_demo_chain_and_agent_workflow_diagrams() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "完整 Demo 链路" in readme
    assert "Spring Boot Backend" in readme
    assert "Kafka ai.symptom.query" in readme
    assert "Python AI Worker" in readme
    assert "ai.symptom.result" in readme

    assert "Agent Workflow" in readme
    assert "EvidenceReviewAgent" in readme
    assert "UncertaintyAssessmentAgent" in readme
    assert "Scenario Replay" in readme
    assert "ScenarioMedicalKnowledgeAgent" in readme


def test_readme_mermaid_quotes_route_labels_with_path_parameters() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert 'TaskAPI["GET /api/ai/tasks/{taskId}"]' in readme
    assert "TaskAPI[GET /api/ai/tasks/{taskId}]" not in readme
