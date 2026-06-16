from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import select_specialties


class DepartmentRouterAgent(HospitalAgent):
    name = "department_router_agent"
    role = "department_routing"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level") if triage else "standard"
        specialties = select_specialties(context.case_text)
        if urgency == "high":
            primary_department = "emergency"
        elif specialties:
            primary_department = specialties[0]
        else:
            primary_department = "general_medicine"

        return self.ready(
            summary=f"Department router selected {primary_department}.",
            findings=[f"Candidate specialty: {item}" for item in specialties],
            decisions={
                "primary_department": primary_department,
                "candidate_departments": ["emergency", *specialties]
                if urgency == "high"
                else specialties or ["general_medicine"],
                "urgency_level": urgency,
            },
            handoff_to=["emergency_physician_agent" if urgency == "high" else "general_practitioner_agent"],
            confidence=0.8,
        )
