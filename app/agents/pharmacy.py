from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.domain.patient_history import history_list
from app.tools import ClinicalToolRegistry, PatientHistoryLookupTool


class PharmacySafetyAgent(HospitalAgent):
    name = "pharmacy_safety_agent"
    role = "pharmacy_safety"

    def __init__(
        self,
        patient_history_tool: PatientHistoryLookupTool | None = None,
        tools: ClinicalToolRegistry | None = None,
    ) -> None:
        self.patient_history_tool = patient_history_tool or PatientHistoryLookupTool()
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        history_lookup = self.patient_history_tool.run(context.patient_id)
        allergies = [str(item) for item in history_list(history_lookup, "allergies")]
        medications = [str(item) for item in history_list(history_lookup, "currentMedications")]
        interaction_screening = self.tools.medication_interaction.run(
            ["antipyretic", "supportive_care"],
            allergies,
            medications,
        )
        medication_note = (
            f"Reconcile current medications from history: {', '.join(medications)}."
            if medications
            else "Confirm medication history before medication order."
        )
        return self.ready(
            summary="Pharmacy safety review completed at demo level.",
            findings=[
                "Medication suggestions require allergy and medication-history confirmation.",
                *([f"Known allergy from patient history: {item}" for item in allergies]),
            ],
            recommendations=[
                medication_note,
                "Confirm allergy history before antibiotics or analgesics.",
                "Avoid presenting medication advice as a final prescription.",
            ],
            decisions={
                "requires_allergy_check": True,
                "known_allergies": allergies,
                "current_medications": medications,
            },
            data={
                "patient_history_lookup": history_lookup,
                "tool_results": [interaction_screening],
            },
            handoff_to=["medication_plan_agent"],
        )
