from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.branch_planner_agent import BranchPlannerAgent
from app.agents.candidate_support_agent import CandidateSupportAgent
from app.agents.coordinator import AgentCoordinator
from app.agents.rag_llm_consistency_agent import RagLlmConsistencyAgent
from app.agents.retrieval_quality_agent import RetrievalQualityAgent
from app.agents.safety_check_agent import SafetyCheckAgent
from app.agents.symptom_extraction_agent import SymptomExtractionAgent
from app.agents.uncertainty_assessment_agent import UncertaintyAssessmentAgent
from app.orchestrator import Orchestrator
from app.scenario.agents import (
    ScenarioDifferentialDiagnosisAgent,
    ScenarioEvidenceReviewAgent,
    ScenarioMedicalKnowledgeAgent,
    ScenarioReportAgent,
)


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
