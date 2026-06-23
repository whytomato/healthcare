from __future__ import annotations

from app.agents.base import LlmBackedHospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.workflow_state import selected_specialties
from app.tools import ClinicalToolRegistry
from app.tools.emergency_operations import readiness_status_from_tool_result


class EmergencyPhysicianAgent(LlmBackedHospitalAgent):
    name = "emergency_physician_agent"
    role = "emergency_physician"
    llm_task = "Perform an emergency physician review and identify immediate stabilization actions."

    def __init__(self, llm_client=None, tools: ClinicalToolRegistry | None = None) -> None:
        super().__init__(llm_client)
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        triage = self.previous_result(previous, "triage_nurse_agent")
        red_flags = triage.decisions.get("red_flags", []) if triage else []
        urgency = triage.decisions.get("urgency_level", "high") if triage else "high"
        specialties = selected_specialties(previous)
        task_id = str(context.metadata.get("taskId") or context.metadata.get("task_id") or "workflow-local")
        llm_output, llm_data = self.llm_finding(context, previous)
        actions = [
            "Check vital signs and oxygen saturation immediately.",
            "Arrange same-day clinician reassessment for red-flag symptoms.",
        ]
        if any(term in red_flags for term in ["chest discomfort", "chest pain"]):
            actions.append("Assess acute coronary syndrome risk before routine discharge.")
        if "confusion" in red_flags:
            actions.append("Assess altered mental status and neurological safety signals.")
        emergency_exams = _emergency_exams(red_flags, specialties)
        emergency_encounter = self.tools.emergency_encounter.run(
            task_id=task_id,
            patient_id=context.patient_id,
            triage_urgency=urgency,
            red_flags=red_flags,
        )
        practitioner_assignment = self.tools.practitioner_assignment.run(
            task_id=task_id,
            patient_id=context.patient_id,
            urgency_level=urgency,
            required_specialties=specialties,
        )
        resource_reservation = self.tools.resource_reservation.run(
            task_id=task_id,
            patient_id=context.patient_id,
            urgency_level=urgency,
            required_resources=_emergency_resources(red_flags),
        )
        emergency_readiness_update = self.tools.emergency_encounter.update_readiness(
            task_id=task_id,
            emergency_encounter_id=str(
                emergency_encounter.get("payload", {}).get(
                    "emergencyEncounterId",
                    f"local-{task_id}",
                )
            ),
            resource_readiness_status=readiness_status_from_tool_result(resource_reservation),
            reserved_resources=_reserved_resources(resource_reservation),
        )
        exam_scheduling = self.tools.exam_scheduling.run(
            task_id=task_id,
            patient_id=context.patient_id,
            ordering_agent=self.name,
            requested_exams=emergency_exams,
            urgency_level=urgency,
        )

        return self.ready(
            summary="Emergency physician review prioritized immediate safety actions.",
            findings=[
                llm_output
                or "Emergency review is indicated because triage identified red-flag symptoms."
            ],
            recommendations=actions,
            decisions={
                "emergency_review_required": True,
                "emergency_encounter_status": emergency_encounter.get("payload", {}).get(
                    "status"
                ),
                "emergency_resource_readiness": "confirmed",
                "ordering_agent": self.name,
                "ordered_exams": emergency_exams,
                "immediate_actions": actions,
            },
            data={
                **llm_data,
                "tool_results": [
                    emergency_encounter,
                    practitioner_assignment,
                    resource_reservation,
                    emergency_readiness_update,
                    exam_scheduling,
                ],
            },
            handoff_to=["general_practitioner_agent", "specialist_router_agent"],
            confidence=0.82,
        )


def _emergency_exams(red_flags: list[str], specialties: list[str]) -> list[str]:
    exams = ["CBC", "CRP", "oxygen saturation"]
    if "respiratory" in specialties or "shortness of breath" in red_flags:
        exams.append("chest X-ray")
    if "cardiology" in specialties or any(flag in red_flags for flag in ["chest discomfort", "chest pain"]):
        exams.extend(["ECG", "troponin"])
    if "infectious_disease" in specialties:
        exams.append("blood culture")
    if "neurology" in specialties or "confusion" in red_flags:
        exams.append("head CT if clinically indicated")
    return list(dict.fromkeys(exams))


def _emergency_resources(red_flags: list[str]) -> list[str]:
    resources = ["resuscitation_room", "emergency_observation_bed", "portable_monitor"]
    if "confusion" in red_flags:
        resources.append("neuro_observation_capacity")
    if any(flag in red_flags for flag in ["chest discomfort", "chest pain"]):
        resources.append("cardiac_monitor")
    return list(dict.fromkeys(resources))


def _reserved_resources(tool_result: dict) -> list[str]:
    payload = tool_result.get("payload", {})
    if isinstance(payload, dict):
        resources = payload.get("reservedResources", [])
        if isinstance(resources, list):
            return [str(resource) for resource in resources]
    return []
