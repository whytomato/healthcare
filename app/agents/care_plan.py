from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.domain.patient_history import history_list
from app.tools import PatientHistoryLookupTool


class CarePlanAgent(LlmBackedHospitalAgent):
    name = "care_plan_agent"
    role = "care_plan"
    llm_task = "Assemble a care plan from triage, GP, specialist, lab, pharmacy, and AI consultation outputs."

    def __init__(
        self,
        llm_client=None,
        patient_history_tool: PatientHistoryLookupTool | None = None,
    ) -> None:
        super().__init__(llm_client)
        self.patient_history_tool = patient_history_tool or PatientHistoryLookupTool()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        history_lookup = self.patient_history_tool.run(context.patient_id)
        previous_dispositions = [
            str(item) for item in history_list(history_lookup, "previousDispositions")
        ]
        recommendations = [
            recommendation
            for result in previous
            for recommendation in result.recommendations
        ]
        if previous_dispositions:
            recommendations.append(
                f"Review prior dispositions before finalizing care plan: {', '.join(previous_dispositions)}."
            )
        llm_output, llm_data = self.llm_finding(context, previous)
        return self.ready(
            summary="Care plan assembled from triage, GP, specialist, lab, and pharmacy inputs.",
            findings=[llm_output] if llm_output else [],
            recommendations=recommendations[:12],
            decisions={
                "care_plan_sections": [
                    "triage",
                    "specialist_consultation",
                    "diagnostic_workup",
                    "safety_review",
                    "patient_history_review",
                ]
            },
            data={**llm_data, "patient_history_lookup": history_lookup},
            handoff_to=["follow_up_agent"],
            confidence=0.75,
        )
