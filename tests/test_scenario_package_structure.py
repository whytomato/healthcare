from app.scenario import generate_mock_scenario, run_uncertainty_scenario
from app.scenario.agents import (
    ScenarioDifferentialDiagnosisAgent,
    ScenarioEvidenceReviewAgent,
    ScenarioMedicalKnowledgeAgent,
    ScenarioReportAgent,
)


def test_scenario_replay_has_a_dedicated_public_package() -> None:
    assert callable(run_uncertainty_scenario)
    assert callable(generate_mock_scenario)
    assert ScenarioMedicalKnowledgeAgent.name == "medical_knowledge_agent"
    assert ScenarioDifferentialDiagnosisAgent.name == "differential_diagnosis_agent"
    assert ScenarioEvidenceReviewAgent.name == "evidence_review_agent"
    assert ScenarioReportAgent.name == "report_agent"
