from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.workflow_state import selected_specialties
from app.tools import ClinicalToolRegistry


class DispositionCoordinatorAgent(HospitalAgent):
    name = "disposition_coordinator_agent"
    role = "disposition_coordinator"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level") if triage else "unknown"
        if urgency == "high":
            decision = "emergency_reassessment"
            reason = "High triage urgency requires same-day reassessment before routine follow-up."
            monitoring = [
                "Monitor vital signs and oxygen saturation.",
                "Escalate if chest symptoms, confusion, or breathing difficulty worsen.",
            ]
        else:
            decision = "outpatient_follow_up"
            reason = "No high-risk triage signal was identified in this demo workflow."
            monitoring = [
                "Review test results when available.",
                "Return for reassessment if red-flag symptoms develop.",
            ]
        review_request = self.tools.human_review_request.run(
            urgency,
            selected_specialties(previous),
        )

        return self.ready(
            summary=f"Disposition coordinator selected {decision}.",
            recommendations=[reason, *monitoring],
            decisions={
                "disposition": {
                    "decision": decision,
                    "reason": reason,
                },
                "monitoring_plan": monitoring,
            },
            data={"tool_results": [review_request]},
            handoff_to=["admission_coordinator_agent"],
            confidence=0.78,
        )
