from __future__ import annotations

from collections.abc import Callable

from app.agents.base import Agent
from app.agents.branch_planner_agent import BranchPlannerAgent
from app.agents.candidate_support_agent import CandidateSupportAgent
from app.agents.differential_diagnosis_agent import DifferentialDiagnosisAgent
from app.agents.evidence_review_agent import EvidenceReviewAgent
from app.agents.medical_knowledge_agent import MedicalKnowledgeAgent
from app.agents.rag_llm_consistency_agent import RagLlmConsistencyAgent
from app.agents.report_agent import ReportAgent
from app.agents.retrieval_quality_agent import RetrievalQualityAgent
from app.agents.safety_check_agent import SafetyCheckAgent
from app.agents.symptom_extraction_agent import SymptomExtractionAgent
from app.agents.uncertainty_assessment_agent import UncertaintyAssessmentAgent
from app.schemas.message import AgentContext, AgentResult


class AgentCoordinator:
    def __init__(self, agents: list[Agent] | None = None) -> None:
        self.agents = agents or [
            SymptomExtractionAgent(),
            BranchPlannerAgent(),
            MedicalKnowledgeAgent(),
            RetrievalQualityAgent(),
            DifferentialDiagnosisAgent(),
            CandidateSupportAgent(),
            EvidenceReviewAgent(),
            RagLlmConsistencyAgent(),
            SafetyCheckAgent(),
            UncertaintyAssessmentAgent(),
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
            skipped_branch = self._skipped_branch_for(agent, results)
            if skipped_branch:
                result = agent.skipped(
                    f"{agent.name} skipped because {skipped_branch} branch is inactive.",
                    data={"skipped_branch": skipped_branch},
                )
            else:
                result = agent.run(context, results)
            results.append(result)
            if progress_callback:
                progress_callback(agent.name, result)
        return results

    def _skipped_branch_for(self, agent: Agent, results: list[AgentResult]) -> str | None:
        branch_by_agent = {
            "medical_knowledge_agent": "knowledge_retrieval",
            "retrieval_quality_agent": "knowledge_retrieval",
            "differential_diagnosis_agent": "candidate_reasoning",
            "candidate_support_agent": "candidate_reasoning",
            "evidence_review_agent": "consistency",
            "rag_llm_consistency_agent": "consistency",
        }
        branch_name = branch_by_agent.get(agent.name)
        if not branch_name:
            return None

        evidence_skip = self._evidence_missing_skip_for(branch_name, results)
        if evidence_skip:
            return evidence_skip

        branch_plan = next(
            (result for result in results if result.agent == "branch_planner_agent"),
            None,
        )
        if not branch_plan:
            return None

        branches = branch_plan.data.get("branches", {})
        branch = branches.get(branch_name) if isinstance(branches, dict) else None
        if isinstance(branch, dict) and branch.get("state") == "skipped":
            return branch_name
        return None

    def _evidence_missing_skip_for(
        self,
        branch_name: str,
        results: list[AgentResult],
    ) -> str | None:
        if branch_name not in {"candidate_reasoning", "consistency"}:
            return None

        retrieval_quality = next(
            (result for result in results if result.agent == "retrieval_quality_agent"),
            None,
        )
        if (
            retrieval_quality
            and retrieval_quality.status == "ready"
            and retrieval_quality.data.get("evidence_state") == "evidence_missing"
        ):
            return branch_name
        return None
