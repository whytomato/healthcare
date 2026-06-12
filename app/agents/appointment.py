from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import URGENT_TERMS, matched_terms


class AppointmentAgent(HospitalAgent):
    name = "appointment_agent"
    role = "appointment_scheduling"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        urgent_terms = matched_terms(context.case_text, URGENT_TERMS)
        encounter_type = "emergency" if urgent_terms else "outpatient"
        return self.ready(
            summary=f"Appointment classified the encounter as {encounter_type}.",
            decisions={
                "encounter_type": encounter_type,
                "priority": "high" if urgent_terms else "routine",
            },
            data={"urgent_terms": urgent_terms},
            handoff_to=["triage_nurse_agent"],
        )
