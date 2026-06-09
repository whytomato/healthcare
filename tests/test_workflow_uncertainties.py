from app.orchestrator import Orchestrator
from app.agents.base import Agent
from app.agents.branch_planner_agent import BranchPlannerAgent
from app.agents.candidate_support_agent import CandidateSupportAgent
from app.agents.coordinator import AgentCoordinator
from app.agents.report_agent import ReportAgent
from app.agents.rag_llm_consistency_agent import RagLlmConsistencyAgent
from app.agents.retrieval_quality_agent import RetrievalQualityAgent
from app.agents.safety_check_agent import SafetyCheckAgent
from app.agents.symptom_extraction_agent import SymptomExtractionAgent
from app.agents.uncertainty_assessment_agent import UncertaintyAssessmentAgent
from app.schemas.message import AgentContext, AgentResult


class FakeMedicalKnowledgeAgent(Agent):
    name = "medical_knowledge_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        return self.ready(
            summary="Fake RAG evidence is ready.",
            data={
                "documents": [
                    {
                        "disease": "pneumonia",
                        "retrieval_score": 2.0,
                        "matched_query_terms": ["fever", "cough"],
                    }
                ],
                "used_previous_agents": ["symptom_extraction_agent"],
            },
        )


class FakeDifferentialDiagnosisAgent(Agent):
    name = "differential_diagnosis_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        return self.ready(
            summary="Fake candidate reasoning is ready.",
            findings=["heart failure should be considered"],
            data={
                "model_output": "heart failure should be considered",
                "used_previous_agents": [
                    "symptom_extraction_agent",
                    "medical_knowledge_agent",
                ],
            },
        )


class FakeWeakMedicalKnowledgeAgent(Agent):
    name = "medical_knowledge_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        return self.ready(
            summary="Fake weak RAG evidence is ready.",
            data={
                "documents": [
                    {
                        "disease": "pneumonia",
                        "retrieval_score": 0.5,
                        "matched_query_terms": ["malaise"],
                    }
                ],
                "used_previous_agents": ["symptom_extraction_agent"],
            },
        )


def test_symptom_query_marks_unsupported_candidate_with_weak_evidence(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    coordinator = AgentCoordinator(
        agents=[
            SymptomExtractionAgent(),
            BranchPlannerAgent(),
            FakeWeakMedicalKnowledgeAgent(),
            RetrievalQualityAgent(),
            FakeDifferentialDiagnosisAgent(),
            CandidateSupportAgent(),
            RagLlmConsistencyAgent(),
            SafetyCheckAgent(),
            UncertaintyAssessmentAgent(),
            ReportAgent(),
        ]
    )

    result = Orchestrator(coordinator=coordinator).run(
        case_text="malaise",
        patient_id="p001",
    )

    results_by_agent = {item["agent"]: item for item in result["results"]}
    candidate_support = results_by_agent["candidate_support_agent"]
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert results_by_agent["retrieval_quality_agent"]["data"]["evidence_state"] == "evidence_weak"
    assert candidate_support["status"] == "ready"
    assert candidate_support["data"]["candidate_support_state"] == "unsupported"
    assert "unsupported_candidate" in uncertainty_types


def test_symptom_query_marks_rag_llm_conflict_as_uncertainty(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    coordinator = AgentCoordinator(
        agents=[
            SymptomExtractionAgent(),
            BranchPlannerAgent(),
            FakeMedicalKnowledgeAgent(),
            RetrievalQualityAgent(),
            FakeDifferentialDiagnosisAgent(),
            RagLlmConsistencyAgent(),
            SafetyCheckAgent(),
            UncertaintyAssessmentAgent(),
            ReportAgent(),
        ]
    )

    result = Orchestrator(coordinator=coordinator).run(
        case_text="fever and cough",
        patient_id="p001",
    )

    results_by_agent = {item["agent"]: item for item in result["results"]}
    consistency = results_by_agent["rag_llm_consistency_agent"]
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    report = results_by_agent["report_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert consistency["status"] == "ready"
    assert consistency["data"]["consistency_state"] == "conflicting"
    assert "agent_conflict" in uncertainty_types
    assert report["data"]["uncertainties"] == uncertainty["data"]["uncertainties"]


def test_symptom_query_marks_empty_retrieval_as_missing_evidence(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "data/health_knowledge_graph.json")

    result = Orchestrator().run(case_text="zzzzunknownsymptom", patient_id="p001")

    results_by_agent = {item["agent"]: item for item in result["results"]}
    retrieval_quality = results_by_agent["retrieval_quality_agent"]
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert retrieval_quality["status"] == "ready"
    assert retrieval_quality["data"]["evidence_state"] == "evidence_missing"
    assert results_by_agent["differential_diagnosis_agent"]["status"] == "skipped"
    assert results_by_agent["candidate_support_agent"]["status"] == "skipped"
    assert results_by_agent["evidence_review_agent"]["status"] == "skipped"
    assert results_by_agent["rag_llm_consistency_agent"]["status"] == "skipped"
    assert "missing_evidence" in uncertainty_types
    assert "branch_skipped" in uncertainty_types


def test_symptom_query_continues_candidate_reasoning_with_weak_evidence(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "data/health_knowledge_graph.json")

    result = Orchestrator().run(case_text="malaise", patient_id="p001")

    results_by_agent = {item["agent"]: item for item in result["results"]}
    retrieval_quality = results_by_agent["retrieval_quality_agent"]
    differential = results_by_agent["differential_diagnosis_agent"]
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert retrieval_quality["data"]["evidence_state"] == "evidence_weak"
    assert differential["status"] != "skipped"
    assert differential["data"]["evidence_state"] == "evidence_weak"
    assert "weak_evidence" in uncertainty_types


def test_symptom_query_flow_reports_missing_real_services(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "")
    result = Orchestrator().run(case_text="real symptom text", patient_id="p001")

    assert result["patient_id"] == "p001"
    assert [item["agent"] for item in result["results"]] == [
        "symptom_extraction_agent",
        "branch_planner_agent",
        "medical_knowledge_agent",
        "retrieval_quality_agent",
        "differential_diagnosis_agent",
        "candidate_support_agent",
        "evidence_review_agent",
        "rag_llm_consistency_agent",
        "safety_check_agent",
        "uncertainty_assessment_agent",
        "report_agent",
    ]
    results_by_agent = {item["agent"]: item for item in result["results"]}
    assert results_by_agent["symptom_extraction_agent"]["status"] == "ready"
    assert results_by_agent["branch_planner_agent"]["status"] == "ready"
    assert results_by_agent["medical_knowledge_agent"]["status"] == "needs_data"
    assert results_by_agent["retrieval_quality_agent"]["status"] == "needs_data"
    assert results_by_agent["differential_diagnosis_agent"]["status"] == "needs_data"
    assert results_by_agent["candidate_support_agent"]["status"] == "needs_data"
    assert results_by_agent["evidence_review_agent"]["status"] == "needs_data"
    assert results_by_agent["rag_llm_consistency_agent"]["status"] == "needs_data"
    assert results_by_agent["safety_check_agent"]["status"] == "ready"
    assert results_by_agent["uncertainty_assessment_agent"]["status"] == "ready"
    assert results_by_agent["report_agent"]["status"] == "needs_data"
    assert results_by_agent["medical_knowledge_agent"]["data"]["used_previous_agents"] == [
        "symptom_extraction_agent"
    ]
    assert "symptom_extraction_agent" in results_by_agent["differential_diagnosis_agent"][
        "data"
    ].get("used_previous_agents", [])
    assert "DifferentialDiagnosisAgent" in results_by_agent["evidence_review_agent"]["summary"]
    assert "symptom_extraction_agent" in results_by_agent["safety_check_agent"]["data"].get(
        "used_previous_agents", []
    )
    assert "MEDICAL_KNOWLEDGE_BASE" in results_by_agent["medical_knowledge_agent"][
        "required_inputs"
    ]
    assert "LLM_API_KEY" in results_by_agent["differential_diagnosis_agent"]["required_inputs"]
    assert results_by_agent["report_agent"]["data"]["agent_handoffs"]


def test_symptom_query_requires_case_text() -> None:
    result = Orchestrator().run(case_text="")

    results_by_agent = {item["agent"]: item for item in result["results"]}

    symptom_result = results_by_agent["symptom_extraction_agent"]
    assert symptom_result["status"] == "needs_data"
    assert "case_text" in symptom_result["required_inputs"]

    branch_plan = results_by_agent["branch_planner_agent"]
    assert branch_plan["status"] == "ready"
    assert branch_plan["data"]["workflow_path"] == "clarification_path"
    assert branch_plan["data"]["branches"]["safety_risk"]["state"] == "active"
    assert branch_plan["data"]["branches"]["candidate_reasoning"]["state"] == "skipped"
    assert results_by_agent["medical_knowledge_agent"]["status"] == "skipped"
    assert results_by_agent["differential_diagnosis_agent"]["status"] == "skipped"
    assert results_by_agent["evidence_review_agent"]["status"] == "skipped"
    assert results_by_agent["safety_check_agent"]["status"] == "ready"

    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}
    assert {"incomplete_input", "branch_skipped"}.issubset(uncertainty_types)


def test_symptom_query_marks_missing_services_as_uncertainty(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "")

    result = Orchestrator().run(case_text="fever and cough", patient_id="p001")

    results_by_agent = {item["agent"]: item for item in result["results"]}
    branch_plan = results_by_agent["branch_planner_agent"]
    assert branch_plan["data"]["workflow_path"] == "analysis_path"
    assert branch_plan["data"]["branches"]["knowledge_retrieval"]["state"] == "active"
    assert branch_plan["data"]["branches"]["candidate_reasoning"]["state"] == "active"
    assert branch_plan["data"]["branches"]["consistency"]["state"] == "active"
    assert results_by_agent["medical_knowledge_agent"]["status"] == "needs_data"
    assert results_by_agent["differential_diagnosis_agent"]["status"] == "needs_data"
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    report = results_by_agent["report_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert {"missing_evidence", "branch_skipped"}.issubset(uncertainty_types)
    assert report["data"]["uncertainties"] == uncertainty["data"]["uncertainties"]


def test_symptom_query_marks_urgent_risk_as_uncertainty(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "")

    result = Orchestrator().run(case_text="fever with severe headache", patient_id="p001")

    results_by_agent = {item["agent"]: item for item in result["results"]}
    safety_result = results_by_agent["safety_check_agent"]
    uncertainty = results_by_agent["uncertainty_assessment_agent"]
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert safety_result["data"]["red_flags"]
    assert "urgent_risk" in uncertainty_types
