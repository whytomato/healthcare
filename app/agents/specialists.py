from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import SPECIALTY_RECOMMENDATIONS
from app.tools import ClinicalToolRegistry


class SpecialistAgent(LlmBackedHospitalAgent):
    specialty: str
    display_name: str

    def __init__(self, llm_client=None, tools: ClinicalToolRegistry | None = None) -> None:
        super().__init__(llm_client)
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        router = self.previous_result(previous, "specialist_router_agent")
        selected = set(router.decisions.get("selected_specialties", [])) if router else set()
        active = self.specialty in selected
        llm_output, llm_data = self.llm_finding(context, previous)
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level", "standard") if triage else "standard"
        task_id = str(context.metadata.get("taskId") or context.metadata.get("task_id") or "workflow-local")
        requested_exams = _specialist_exams(self.specialty)
        exam_schedule = self.tools.exam_scheduling.run(
            task_id=task_id,
            patient_id=context.patient_id,
            ordering_agent=self.name,
            requested_exams=requested_exams,
            urgency_level=urgency,
        )
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
                ),
                *[f"Order {exam} for {self.specialty} review." for exam in requested_exams],
            ],
            decisions={
                "specialty": self.specialty,
                "selected_by_router": active,
                "ordering_agent": self.name,
                "requested_exams": requested_exams,
                "review_loop": "ordering_clinician_review_required",
            },
            data={
                **llm_data,
                "tool_results": [exam_schedule],
            },
            handoff_to=["lab_result_interpreter_agent", "imaging_interpreter_agent"],
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


def _specialist_exams(specialty: str) -> list[str]:
    exams_by_specialty = {
        "respiratory": ["chest X-ray", "oxygen saturation"],
        "cardiology": ["ECG", "troponin"],
        "infectious_disease": ["CBC", "CRP", "blood culture"],
        "neurology": ["neurological exam", "head CT if clinically indicated"],
    }
    return exams_by_specialty.get(specialty, ["CBC"])
