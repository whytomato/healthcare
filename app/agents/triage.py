from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import assess_patient_encounter
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
        assessment = assess_patient_encounter(context.case_text)
        guideline_lookup = self.tools.guideline_lookup.run(
            context.case_text,
            assessment.red_flags,
        )
        return self.ready(
            summary=f"Triage completed with {assessment.urgency_level} urgency.",
            findings=[f"red flag: {term}" for term in assessment.red_flags],
            recommendations=[
                "Check vital signs and oxygen saturation before routine consultation."
            ],
            decisions={
                "urgency_level": assessment.urgency_level,
                "recommended_department": assessment.recommended_department,
                "red_flags": assessment.red_flags,
            },
            data={"tool_results": [guideline_lookup]},
            handoff_to=["department_router_agent"],
            confidence=0.8,
        )
