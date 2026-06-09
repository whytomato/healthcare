from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class UncertaintyAssessmentAgent(Agent):
    name = "uncertainty_assessment_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        uncertainties: list[dict[str, object]] = []

        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        if not context.case_text.strip() or (
            symptom_result and symptom_result.status == "needs_data"
        ):
            uncertainties.append(
                {
                    "type": "incomplete_input",
                    "source_agents": ["symptom_extraction_agent"],
                    "severity": "high",
                    "impact": "full candidate reasoning should not run",
                }
            )

        branch_plan = self.previous_result(previous, "branch_planner_agent")
        skipped_branches: list[str] = []
        if branch_plan:
            branches = branch_plan.data.get("branches", {})
            if isinstance(branches, dict):
                skipped_branches = [
                    name
                    for name, branch in branches.items()
                    if isinstance(branch, dict) and branch.get("state") == "skipped"
                ]
        if skipped_branches:
            uncertainties.append(
                {
                    "type": "branch_skipped",
                    "source_agents": ["branch_planner_agent"],
                    "severity": "medium",
                    "impact": "some workflow branches did not run",
                    "branches": skipped_branches,
                }
            )

        runtime_skipped_branches = [
            str(result.data["skipped_branch"])
            for result in previous
            if result.status == "skipped" and "skipped_branch" in result.data
        ]
        if runtime_skipped_branches and not skipped_branches:
            uncertainties.append(
                {
                    "type": "branch_skipped",
                    "source_agents": [
                        result.agent for result in previous if result.status == "skipped"
                    ],
                    "severity": "medium",
                    "impact": "some workflow branches were skipped at runtime",
                    "branches": sorted(set(runtime_skipped_branches)),
                }
            )

        medical_knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        if medical_knowledge_result and medical_knowledge_result.status == "needs_data":
            required_inputs = set(medical_knowledge_result.required_inputs)
            if "MEDICAL_KNOWLEDGE_BASE" in required_inputs:
                uncertainties.append(
                    {
                        "type": "missing_evidence",
                        "source_agents": ["medical_knowledge_agent"],
                        "severity": "high",
                        "impact": "retrieval-backed evidence is unavailable",
                    }
                )

        retrieval_quality_result = self.previous_result(previous, "retrieval_quality_agent")
        if retrieval_quality_result and retrieval_quality_result.status == "ready":
            evidence_state = retrieval_quality_result.data.get("evidence_state")
            if evidence_state == "evidence_missing":
                uncertainties.append(
                    {
                        "type": "missing_evidence",
                        "source_agents": ["retrieval_quality_agent"],
                        "severity": "high",
                        "impact": "no retrieved disease-symptom evidence supports downstream reasoning",
                    }
                )
            elif evidence_state == "evidence_weak":
                uncertainties.append(
                    {
                        "type": "weak_evidence",
                        "source_agents": ["retrieval_quality_agent"],
                        "severity": "medium",
                        "impact": "downstream candidate reasoning should preserve weak evidence",
                    }
                )

        blocked_branches = self._blocked_branches(previous)
        if blocked_branches and not skipped_branches:
            uncertainties.append(
                {
                    "type": "branch_skipped",
                    "source_agents": [result.agent for result in previous if result.status == "needs_data"],
                    "severity": "medium",
                    "impact": "some workflow branches could not complete because dependencies were missing",
                    "branches": blocked_branches,
                }
            )

        safety_result = self.previous_result(previous, "safety_check_agent")
        red_flags = safety_result.data.get("red_flags", []) if safety_result else []
        if red_flags:
            uncertainties.append(
                {
                    "type": "urgent_risk",
                    "source_agents": ["safety_check_agent"],
                    "severity": "high",
                    "impact": "final report should prioritize urgent safety risk",
                    "red_flags": red_flags,
                }
            )

        consistency_result = self.previous_result(previous, "rag_llm_consistency_agent")
        if (
            consistency_result
            and consistency_result.status == "ready"
            and consistency_result.data.get("consistency_state") == "conflicting"
        ):
            uncertainties.append(
                {
                    "type": "agent_conflict",
                    "source_agents": ["rag_llm_consistency_agent"],
                    "severity": "high",
                    "impact": "retrieved evidence and LLM candidate output disagree",
                    "consistency_state": "conflicting",
                }
            )

        candidate_support_result = self.previous_result(previous, "candidate_support_agent")
        if (
            candidate_support_result
            and candidate_support_result.status == "ready"
            and candidate_support_result.data.get("candidate_support_state") == "unsupported"
        ):
            uncertainties.append(
                {
                    "type": "unsupported_candidate",
                    "source_agents": ["candidate_support_agent"],
                    "severity": "medium",
                    "impact": "LLM candidate output lacks direct support from retrieved evidence",
                    "candidate_support_state": "unsupported",
                }
            )

        return self.ready(
            summary="Workflow uncertainty signals were collected from agent and branch states.",
            data={"uncertainties": uncertainties},
            confidence=1.0 if not uncertainties else 0.7,
        )

    def _blocked_branches(self, previous: list[AgentResult]) -> list[str]:
        blocked: list[str] = []
        agents_by_name = {result.agent: result for result in previous}
        if agents_by_name.get("medical_knowledge_agent", None) and agents_by_name[
            "medical_knowledge_agent"
        ].status == "needs_data":
            blocked.append("knowledge_retrieval")
        if agents_by_name.get("retrieval_quality_agent", None) and agents_by_name[
            "retrieval_quality_agent"
        ].status == "needs_data":
            blocked.append("knowledge_retrieval")
        if agents_by_name.get("differential_diagnosis_agent", None) and agents_by_name[
            "differential_diagnosis_agent"
        ].status == "needs_data":
            blocked.append("candidate_reasoning")
        if agents_by_name.get("evidence_review_agent", None) and agents_by_name[
            "evidence_review_agent"
        ].status == "needs_data":
            blocked.append("consistency")
        return blocked
