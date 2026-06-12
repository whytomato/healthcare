from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import select_specialties


class SpecialistRouterAgent(HospitalAgent):
    name = "specialist_router_agent"
    role = "specialist_router"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        gp = self.previous_result(previous, "general_practitioner_agent")
        selected = (
            list(gp.decisions.get("suggested_specialties", []))
            if gp
            else select_specialties(context.case_text)
        )
        if not selected:
            selected = ["respiratory"]
        return self.ready(
            summary="Specialist routing selected role-based consultation agents.",
            decisions={"selected_specialties": selected},
            data={"routing_basis": "rule_based_demo_keywords"},
            handoff_to=[f"{specialty}_specialist_agent" for specialty in selected],
            confidence=0.75,
        )
