from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import URGENT_TERMS, matched_terms


class TriageNurseAgent(HospitalAgent):
    name = "triage_nurse_agent"
    role = "triage_nurse"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        red_flags = matched_terms(context.case_text, URGENT_TERMS)
        urgency_level = "high" if red_flags else "standard"
        department = "emergency" if red_flags else "general_medicine"
        return self.ready(
            summary=f"Triage completed with {urgency_level} urgency.",
            findings=[f"red flag: {term}" for term in red_flags],
            recommendations=[
                "Check vital signs and oxygen saturation before routine consultation."
            ],
            decisions={
                "urgency_level": urgency_level,
                "recommended_department": department,
                "red_flags": red_flags,
            },
            handoff_to=["general_practitioner_agent"],
            confidence=0.8,
        )
