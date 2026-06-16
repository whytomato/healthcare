from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.domain.patient_history import has_history, history_list
from app.policies.workflow_state import selected_specialties
from app.tools import PatientHistoryLookupTool


class FinalHospitalReportAgent(LlmBackedHospitalAgent):
    name = "final_hospital_report_agent"
    role = "final_hospital_report"
    llm_task = "Create the final doctor-facing hospital workflow report."

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
        selected = selected_specialties(previous)
        care_plan = self.previous_result(previous, "care_plan_agent")
        follow_up = self.previous_result(previous, "follow_up_agent")
        history_lookup = self.patient_history_tool.run(context.patient_id)
        final_reports = [str(item) for item in history_list(history_lookup, "lastFinalReports")]
        llm_output, llm_data = self.llm_finding(context, previous)
        summary = (
            llm_output
            or "Hospital workflow report assembled with intake, triage, GP review, specialist consultation, AI consultation, lab advice, pharmacy safety, care plan, and follow-up."
        )
        markdown = _final_report_markdown(
            summary=summary,
            selected=selected,
            care_plan=care_plan,
            follow_up=follow_up,
            previous_reports=final_reports,
        )
        return self.ready(
            summary=summary,
            findings=[
                summary,
                f"Selected specialties: {', '.join(selected)}",
                *final_reports[:2],
            ],
            recommendations=(care_plan.recommendations if care_plan else [])[:8],
            decisions={
                "selected_specialties": selected,
                "follow_up_plan": (
                    follow_up.decisions.get("follow_up_plan") if follow_up else None
                ),
            },
            data={
                **llm_data,
                "report_summary": summary,
                "markdown": markdown,
                "patient_history_used": has_history(history_lookup),
                "prior_report_count": len(final_reports),
                "patient_history_lookup": history_lookup,
            },
            confidence=0.8,
        )


def _final_report_markdown(
    summary: str,
    selected: list[str],
    care_plan: HospitalAgentResult | None,
    follow_up: HospitalAgentResult | None,
    previous_reports: list[str],
) -> str:
    specialties = ", ".join(selected) if selected else "None"
    follow_up_plan = (
        follow_up.decisions.get("follow_up_plan")
        if follow_up
        else "Follow-up plan unavailable"
    )
    recommendations = care_plan.recommendations if care_plan else []
    lines = [
        "## Final Hospital Report",
        "",
        summary,
        "",
        "### Workflow Summary",
        f"- **Selected specialties:** {specialties}",
        f"- **Disposition:** {follow_up_plan}",
    ]
    if recommendations:
        lines.extend(["", "### Care Recommendations"])
        lines.extend(f"- {item}" for item in recommendations[:6])
    if previous_reports:
        lines.extend(["", "### Prior Record Context"])
        lines.extend(f"- {item}" for item in previous_reports[:2])
    return "\n".join(lines)
