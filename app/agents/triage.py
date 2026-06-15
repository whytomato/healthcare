from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import URGENT_TERMS, matched_terms
from app.tools import ClinicalToolRegistry


class TriageNurseAgent(HospitalAgent):
    name = "triage_nurse_agent"
    role = "triage_nurse"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        red_flags = matched_terms(context.case_text, URGENT_TERMS)
        urgency_level = "high" if red_flags else "standard"
        department = "emergency" if red_flags else "general_medicine"
        guideline_lookup = self.tools.guideline_lookup.run(context.case_text, red_flags)
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
            data={"tool_results": [guideline_lookup]},
            handoff_to=["department_router_agent"],
            confidence=0.8,
        )
