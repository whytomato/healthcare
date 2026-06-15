from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import selected_specialties
from app.tools import ClinicalToolRegistry


class AdmissionCoordinatorAgent(HospitalAgent):
    name = "admission_coordinator_agent"
    role = "admission_coordination"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        urgency = triage.decisions.get("urgency_level") if triage else "standard"
        if urgency == "high":
            pathway = {
                "decision": "emergency_observation_or_admission_review",
                "level": "emergency_observation",
                "reason": "High urgency and multi-system risk require observation/admission review.",
            }
        else:
            pathway = {
                "decision": "no_admission_required",
                "level": "outpatient",
                "reason": "Standard urgency is appropriate for outpatient follow-up in the demo.",
            }
        bed_availability = self.tools.bed_availability.run(urgency)
        disposition = self.previous_result(previous, "disposition_coordinator_agent")
        disposition_decision = (
            disposition.decisions.get("disposition", {}).get("decision")
            if disposition
            else pathway["decision"]
        )
        monitoring_plan = (
            disposition.decisions.get("monitoring_plan", []) if disposition else []
        )
        care_coordination = self.tools.care_coordination.run(
            task_id=str(context.metadata.get("taskId") or context.metadata.get("task_id") or "workflow-local"),
            patient_id=context.patient_id,
            doctor_id=context.doctor_id,
            disposition=disposition_decision,
            triage_urgency=urgency,
            selected_specialties=selected_specialties(previous),
            monitoring_plan=monitoring_plan,
        )

        return self.ready(
            summary=f"Admission coordinator selected {pathway['level']}.",
            decisions={"admission_pathway": pathway},
            recommendations=[
                "Coordinate bed or observation area only after physician confirmation."
                if urgency == "high"
                else "Provide outpatient return precautions."
            ],
            data={
                "care_coordination_plan": care_coordination["payload"],
                "tool_results": [bed_availability, care_coordination],
            },
            handoff_to=["final_hospital_report_agent"],
            confidence=0.75,
        )
