from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext


class PharmacySafetyAgent(HospitalAgent):
    name = "pharmacy_safety_agent"
    role = "pharmacy_safety"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        return self.ready(
            summary="Pharmacy safety review completed at demo level.",
            findings=["Medication suggestions require allergy and medication-history confirmation."],
            recommendations=[
                "Confirm allergy history before antibiotics or analgesics.",
                "Avoid presenting medication advice as a final prescription.",
            ],
            decisions={"requires_allergy_check": True},
            handoff_to=["care_plan_agent"],
        )
