from __future__ import annotations

from typing import Any

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


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
                "handoff_to": [
                    "retrieval_quality_agent",
                    "differential_diagnosis_agent",
                    "evidence_review_agent",
                    "rag_llm_consistency_agent",
                ],
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
                "handoff_to": [
                    "candidate_support_agent",
                    "evidence_review_agent",
                    "rag_llm_consistency_agent",
                    "safety_check_agent",
                    "report_agent",
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
                "handoff_to": ["safety_check_agent", "report_agent"],
            },
        )


class ScenarioReportAgent(Agent):
    name = "report_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")
        evidence_result = self.previous_result(previous, "evidence_review_agent")
        safety_result = self.previous_result(previous, "safety_check_agent")
        uncertainty_result = self.previous_result(previous, "uncertainty_assessment_agent")
        uncertainties = []
        if uncertainty_result is not None:
            uncertainties = uncertainty_result.data.get("uncertainties", [])
        agent_handoffs = [
            {
                "agent": result.agent,
                "used_previous_agents": result.data.get("used_previous_agents", []),
                "handoff_to": result.data.get("handoff_to", []),
            }
            for result in previous
        ]
        return self.ready(
            summary="Scenario report assembled without live LLM.",
            data={
                "uncertainties": uncertainties,
                "scenario_controlled": True,
                "used_previous_agents": [item.agent for item in previous],
                "agent_handoffs": agent_handoffs,
                "symptom_candidates": (
                    symptom_result.data.get("symptom_candidates", []) if symptom_result else []
                ),
                "retrieved_documents": (
                    knowledge_result.data.get("documents", []) if knowledge_result else []
                ),
                "candidate_output": (
                    differential_result.data.get("model_output", "")
                    if differential_result
                    else ""
                ),
                "evidence_review_output": (
                    evidence_result.data.get("model_output", "") if evidence_result else ""
                ),
                "red_flags": safety_result.data.get("red_flags", []) if safety_result else [],
            },
        )
