from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import selected_specialties


class FinalHospitalReportAgent(LlmBackedHospitalAgent):
    name = "final_hospital_report_agent"
    role = "final_hospital_report"
    llm_task = "Create the final doctor-facing hospital workflow report."

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        selected = selected_specialties(previous)
        care_plan = self.previous_result(previous, "care_plan_agent")
        follow_up = self.previous_result(previous, "follow_up_agent")
        llm_output, llm_data = self.llm_finding(context, previous)
        summary = (
            llm_output
            or "Hospital workflow report assembled with intake, triage, GP review, specialist consultation, AI consultation, lab advice, pharmacy safety, care plan, and follow-up."
        )
        return self.ready(
            summary=summary,
            findings=[summary, f"Selected specialties: {', '.join(selected)}"],
            recommendations=(care_plan.recommendations if care_plan else [])[:8],
            decisions={
                "selected_specialties": selected,
                "follow_up_plan": (
                    follow_up.decisions.get("follow_up_plan") if follow_up else None
                ),
            },
            data={**llm_data, "report_summary": summary},
            confidence=0.8,
        )
