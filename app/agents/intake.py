from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class IntakeAgent(HospitalAgent):
    name = "intake_agent"
    role = "patient_intake"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        text = context.case_text.strip()
        return self.ready(
            summary="Patient intake captured the encounter complaint.",
            findings=[text] if text else [],
            decisions={"intake_complete": bool(text), "patient_id": context.patient_id},
            data={"case_text": text},
            handoff_to=["appointment_agent", "triage_nurse_agent"],
        )
