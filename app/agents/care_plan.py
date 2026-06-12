from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class CarePlanAgent(LlmBackedHospitalAgent):
    name = "care_plan_agent"
    role = "care_plan"
    llm_task = "Assemble a care plan from triage, GP, specialist, lab, pharmacy, and AI consultation outputs."

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        recommendations = [
            recommendation
            for result in previous
            for recommendation in result.recommendations
        ]
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
                ]
            },
            data=llm_data,
            handoff_to=["follow_up_agent", "final_hospital_report_agent"],
            confidence=0.75,
        )
