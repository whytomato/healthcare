from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import select_specialties
from app.tools import AIConsultationTool


class GeneralPractitionerAgent(LlmBackedHospitalAgent):
    name = "general_practitioner_agent"
    role = "general_practitioner"
    llm_task = "Produce the GP initial assessment and whether specialist consultation is needed."

    def __init__(
        self,
        llm_client=None,
        consultation_tool: AIConsultationTool | None = None,
    ) -> None:
        super().__init__(llm_client)
        self.consultation_tool = consultation_tool or AIConsultationTool()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        selected = select_specialties(context.case_text)
        llm_output, llm_data = self.llm_finding(context, previous)
        consultation_result = self.consultation_tool.run(
            case_text=context.case_text,
            patient_id=context.patient_id,
            doctor_id=context.doctor_id,
            language=context.language,
        )
        return self.ready(
            summary="General practitioner produced an initial assessment.",
            findings=[
                llm_output
                or "Initial assessment should consider respiratory infection, cardiac risk, and neurological safety signals when indicated."
            ],
            recommendations=["Request specialist review for high-risk or cross-system symptoms."],
            decisions={
                "specialist_needed": bool(selected),
                "suggested_specialties": selected,
                "triage_urgency": triage.decisions.get("urgency_level") if triage else "unknown",
                "ai_consultation_tool_status": consultation_result.get("status", "unknown"),
            },
            data={**llm_data, "ai_consultation_tool": consultation_result},
            handoff_to=["specialist_router_agent"],
        )
