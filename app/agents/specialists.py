from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import SPECIALTY_RECOMMENDATIONS


class SpecialistAgent(LlmBackedHospitalAgent):
    specialty: str
    display_name: str

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        router = self.previous_result(previous, "specialist_router_agent")
        selected = set(router.decisions.get("selected_specialties", [])) if router else set()
        active = self.specialty in selected
        llm_output, llm_data = self.llm_finding(context, previous)
        return self.ready(
            summary=(
                f"{self.display_name} consultation completed."
                if active
                else f"{self.display_name} consultation completed as low-priority review."
            ),
            findings=[
                llm_output
                or f"{self.display_name} reviewed the encounter from a {self.specialty} perspective."
            ],
            recommendations=[
                SPECIALTY_RECOMMENDATIONS.get(
                    self.specialty,
                    "Preserve specialist concern in the final care plan.",
                )
            ],
            decisions={"specialty": self.specialty, "selected_by_router": active},
            data=llm_data,
            handoff_to=["lab_advisor_agent"],
            confidence=0.65 if active else 0.45,
        )


class RespiratorySpecialistAgent(SpecialistAgent):
    name = "respiratory_specialist_agent"
    role = "respiratory_specialist"
    specialty = "respiratory"
    display_name = "Respiratory specialist"
    llm_task = "Review the case from respiratory medicine perspective."


class CardiologySpecialistAgent(SpecialistAgent):
    name = "cardiology_specialist_agent"
    role = "cardiology_specialist"
    specialty = "cardiology"
    display_name = "Cardiology specialist"
    llm_task = "Review the case from cardiology perspective."


class InfectiousDiseaseSpecialistAgent(SpecialistAgent):
    name = "infectious_disease_specialist_agent"
    role = "infectious_disease_specialist"
    specialty = "infectious_disease"
    display_name = "Infectious disease specialist"
    llm_task = "Review the case from infectious disease perspective."


class NeurologySpecialistAgent(SpecialistAgent):
    name = "neurology_specialist_agent"
    role = "neurology_specialist"
    specialty = "neurology"
    display_name = "Neurology specialist"
    llm_task = "Review the case from neurology perspective."
