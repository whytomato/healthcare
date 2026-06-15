from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class MedicationPlanAgent(HospitalAgent):
    name = "medication_plan_agent"
    role = "medication_planning"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        pharmacy = self.previous_result(previous, "pharmacy_safety_agent")
        triage = self.previous_result(previous, "triage_nurse_agent")
        requires_allergy_check = (
            pharmacy.decisions.get("requires_allergy_check", True) if pharmacy else True
        )
        urgency = triage.decisions.get("urgency_level") if triage else "standard"
        plan_status = "requires_pharmacist_review" if requires_allergy_check else "ready"

        return self.ready(
            summary=f"Medication plan is {plan_status}.",
            recommendations=[
                "Confirm allergy history before medication order.",
                "Use physician-reviewed demo recommendations only.",
            ],
            decisions={
                "medication_plan_status": plan_status,
                "requires_pharmacist_review": requires_allergy_check,
                "demo_medication_categories": ["antipyretic", "supportive_care"],
            },
            handoff_to=[
                "disposition_coordinator_agent"
                if urgency == "high"
                else "care_plan_agent"
            ],
            confidence=0.68,
        )
