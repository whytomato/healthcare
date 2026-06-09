from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class BranchPlannerAgent(Agent):
    name = "branch_planner_agent"

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        incomplete_input = not context.case_text.strip() or not (
            symptom_result and symptom_result.status == "ready"
        )

        branches = {
            "information_quality": {"state": "active", "reason": "always checked"},
            "safety_risk": {"state": "active", "reason": "safety checks always run"},
            "knowledge_retrieval": {"state": "active", "reason": "case text is available"},
            "candidate_reasoning": {
                "state": "active",
                "reason": "case text is available",
            },
            "consistency": {
                "state": "active",
                "reason": "candidate and evidence comparison may be possible",
            },
        }
        workflow_path = "analysis_path"

        if incomplete_input:
            workflow_path = "clarification_path"
            for branch_name in ("knowledge_retrieval", "candidate_reasoning", "consistency"):
                branches[branch_name] = {
                    "state": "skipped",
                    "reason": "case information is incomplete",
                }

        return self.ready(
            summary="Branch activation plan was produced from explicit workflow rules.",
            data={
                "workflow_path": workflow_path,
                "branches": branches,
                "branch_triggers": ["incomplete_input"] if incomplete_input else [],
            },
            confidence=1.0,
        )
