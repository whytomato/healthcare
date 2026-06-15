from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import selected_specialties
from app.domain.patient_history import history_list
from app.tools import ClinicalToolRegistry, PatientHistoryLookupTool


class FollowUpAgent(HospitalAgent):
    name = "follow_up_agent"
    role = "follow_up"

    def __init__(
        self,
        patient_history_tool: PatientHistoryLookupTool | None = None,
        tools: ClinicalToolRegistry | None = None,
    ) -> None:
        self.patient_history_tool = patient_history_tool or PatientHistoryLookupTool()
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level") if triage else "unknown"
        history_lookup = self.patient_history_tool.run(context.patient_id)
        previous_dispositions = [
            str(item) for item in history_list(history_lookup, "previousDispositions")
        ]
        follow_up = (
            "same-day reassessment or emergency escalation"
            if urgency == "high"
            else "routine follow-up after initial tests"
        )
        specialties = selected_specialties(previous)
        follow_up_scheduling = self.tools.follow_up_scheduling.run(follow_up)
        referral_scheduling = self.tools.referral_scheduling.run(specialties)
        recommendations = [follow_up]
        if previous_dispositions:
            recommendations.append(
                f"Compare this follow-up plan with prior dispositions: {', '.join(previous_dispositions)}."
            )
        return self.ready(
            summary="Follow-up plan generated from triage urgency.",
            recommendations=recommendations,
            decisions={
                "follow_up_plan": follow_up,
                "previous_dispositions": previous_dispositions,
            },
            data={
                "patient_history_lookup": history_lookup,
                "tool_results": [follow_up_scheduling, referral_scheduling],
            },
            handoff_to=["disposition_coordinator_agent"],
        )
