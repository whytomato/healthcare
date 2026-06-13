from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class EmergencyPhysicianAgent(LlmBackedHospitalAgent):
    name = "emergency_physician_agent"
    role = "emergency_physician"
    llm_task = "Perform an emergency physician review and identify immediate stabilization actions."

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        red_flags = triage.decisions.get("red_flags", []) if triage else []
        llm_output, llm_data = self.llm_finding(context, previous)
        actions = [
            "Check vital signs and oxygen saturation immediately.",
            "Arrange same-day clinician reassessment for red-flag symptoms.",
        ]
        if any(term in red_flags for term in ["chest discomfort", "chest pain"]):
            actions.append("Assess acute coronary syndrome risk before routine discharge.")
        if "confusion" in red_flags:
            actions.append("Assess altered mental status and neurological safety signals.")

        return self.ready(
            summary="Emergency physician review prioritized immediate safety actions.",
            findings=[
                llm_output
                or "Emergency review is indicated because triage identified red-flag symptoms."
            ],
            recommendations=actions,
            decisions={
                "emergency_review_required": True,
                "immediate_actions": actions,
            },
            data=llm_data,
            handoff_to=["general_practitioner_agent", "specialist_router_agent"],
            confidence=0.82,
        )
