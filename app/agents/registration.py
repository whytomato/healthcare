from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.domain.patient_history import has_history, history_list
from app.tools import PatientHistoryLookupTool


class RegistrationAgent(HospitalAgent):
    name = "registration_agent"
    role = "registration"

    def __init__(self, patient_history_tool: PatientHistoryLookupTool | None = None) -> None:
        self.patient_history_tool = patient_history_tool or PatientHistoryLookupTool()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        history_lookup = self.patient_history_tool.run(context.patient_id)
        prior_encounters = history_list(history_lookup, "recentEncounters")
        known_patient = bool(context.patient_id) and (
            bool(prior_encounters) or has_history(history_lookup)
        )
        visit_type = "returning_patient" if known_patient else "new_patient"
        missing = []
        if not context.patient_id:
            missing.append("patient_id")
        if not context.doctor_id:
            missing.append("doctor_id")

        return self.ready(
            summary=f"Registration completed for {visit_type}.",
            findings=[
                f"Visit type: {visit_type}",
                f"Prior encounters available: {len(prior_encounters)}",
                *([f"Missing administrative fields: {', '.join(missing)}"] if missing else []),
            ],
            decisions={
                "registration_status": "complete" if not missing else "incomplete",
                "visit_type": visit_type,
                "prior_encounter_count": len(prior_encounters),
                "missing_fields": missing,
            },
            data={
                "patient_id": context.patient_id,
                "doctor_id": context.doctor_id,
                "patient_history_lookup": history_lookup,
            },
            handoff_to=["intake_agent", "nurse_vitals_agent"],
            confidence=0.82,
        )
