from __future__ import annotations

from collections.abc import Callable

from app.agents.base import Agent
from app.agents.differential_diagnosis_agent import DifferentialDiagnosisAgent
from app.agents.evidence_review_agent import EvidenceReviewAgent
from app.agents.medical_knowledge_agent import MedicalKnowledgeAgent
from app.agents.report_agent import ReportAgent
from app.agents.safety_check_agent import SafetyCheckAgent
from app.agents.symptom_extraction_agent import SymptomExtractionAgent
from app.schemas.message import AgentContext, AgentResult


class AgentCoordinator:
    def __init__(self, agents: list[Agent] | None = None) -> None:
        self.agents = agents or [
            SymptomExtractionAgent(),
            MedicalKnowledgeAgent(),
            DifferentialDiagnosisAgent(),
            EvidenceReviewAgent(),
            SafetyCheckAgent(),
            ReportAgent(),
        ]

    def run_case(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        question: str = "What diseases or conditions should be considered for these symptoms?",
        language: str = "zh-CN",
        progress_callback: Callable[[str, AgentResult | None], None] | None = None,
    ) -> list[AgentResult]:
        context = AgentContext(
            case_text=case_text,
            patient_id=patient_id,
            doctor_id=doctor_id,
            question=question,
            language=language,
        )
        results: list[AgentResult] = []
        for agent in self.agents:
            if progress_callback:
                progress_callback(agent.name, None)
            result = agent.run(context, results)
            results.append(result)
            if progress_callback:
                progress_callback(agent.name, result)
        return results
