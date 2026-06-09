from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.base import Agent
from app.agents.branch_planner_agent import BranchPlannerAgent
from app.agents.candidate_support_agent import CandidateSupportAgent
from app.agents.coordinator import AgentCoordinator
from app.agents.rag_llm_consistency_agent import RagLlmConsistencyAgent
from app.agents.retrieval_quality_agent import RetrievalQualityAgent
from app.agents.safety_check_agent import SafetyCheckAgent
from app.agents.symptom_extraction_agent import SymptomExtractionAgent
from app.agents.uncertainty_assessment_agent import UncertaintyAssessmentAgent
from app.orchestrator import Orchestrator
from app.schemas.message import AgentContext, AgentResult


def run_uncertainty_scenario(path: Path, scenario_name: str) -> dict[str, Any]:
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    scenario = next(item for item in scenarios if item["name"] == scenario_name)
    coordinator = AgentCoordinator(
        agents=[
            SymptomExtractionAgent(),
            BranchPlannerAgent(),
            ScenarioMedicalKnowledgeAgent(scenario),
            RetrievalQualityAgent(),
            ScenarioDifferentialDiagnosisAgent(scenario),
            CandidateSupportAgent(),
            ScenarioEvidenceReviewAgent(scenario),
            RagLlmConsistencyAgent(),
            SafetyCheckAgent(),
            UncertaintyAssessmentAgent(),
            ScenarioReportAgent(),
        ]
    )
    return Orchestrator(coordinator=coordinator).run(
        case_text=scenario["case_text"],
        patient_id=scenario.get("patient_id"),
        doctor_id=scenario.get("doctor_id"),
        question=scenario.get("question", "What diseases or conditions should be considered?"),
        language=scenario.get("language", "zh-CN"),
    )


class ScenarioMedicalKnowledgeAgent(Agent):
    name = "medical_knowledge_agent"

    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        return self.ready(
            summary="Scenario RAG evidence is ready.",
            data={
                "documents": self.scenario.get("mock_rag_documents", []),
                "used_previous_agents": ["symptom_extraction_agent"],
            },
        )


class ScenarioDifferentialDiagnosisAgent(Agent):
    name = "differential_diagnosis_agent"

    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        output = self.scenario.get("mock_llm_output")
        if output is None:
            return self.needs_data("Scenario LLM output is not provided.")
        return self.ready(
            summary="Scenario candidate reasoning is ready.",
            findings=[str(output)],
            data={
                "model_output": str(output),
                "used_previous_agents": [
                    "symptom_extraction_agent",
                    "medical_knowledge_agent",
                ],
            },
        )


class ScenarioEvidenceReviewAgent(Agent):
    name = "evidence_review_agent"

    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        output = self.scenario.get("mock_evidence_review_output", "")
        return self.ready(
            summary="Scenario evidence review is ready.",
            findings=[str(output)] if output else [],
            data={
                "model_output": str(output),
                "scenario_controlled": True,
                "used_previous_agents": [
                    "medical_knowledge_agent",
                    "differential_diagnosis_agent",
                ],
            },
        )


class ScenarioReportAgent(Agent):
    name = "report_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        uncertainty_result = next(
            (
                item
                for item in previous
                if item.agent == "uncertainty_assessment_agent"
            ),
            None,
        )
        uncertainties = []
        if uncertainty_result is not None:
            uncertainties = uncertainty_result.data.get("uncertainties", [])
        return self.ready(
            summary="Scenario report assembled without live LLM.",
            data={
                "uncertainties": uncertainties,
                "scenario_controlled": True,
                "used_previous_agents": ["uncertainty_assessment_agent"],
            },
        )
