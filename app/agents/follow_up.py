from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class FollowUpAgent(HospitalAgent):
    name = "follow_up_agent"
    role = "follow_up"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level") if triage else "unknown"
        follow_up = (
            "same-day reassessment or emergency escalation"
            if urgency == "high"
            else "routine follow-up after initial tests"
        )
        return self.ready(
            summary="Follow-up plan generated from triage urgency.",
            recommendations=[follow_up],
            decisions={"follow_up_plan": follow_up},
            handoff_to=["final_hospital_report_agent"],
        )
