from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.clinical_policy import assess_patient_encounter


class NurseVitalsAgent(HospitalAgent):
    name = "nurse_vitals_agent"
    role = "nurse_vitals"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        risk_terms = assess_patient_encounter(context.case_text).vital_risk_terms
        status = "abnormal" if risk_terms else "stable"
        recommended = (
            ["blood pressure", "heart rate", "respiratory rate", "temperature", "oxygen saturation"]
            if risk_terms
            else ["temperature", "heart rate", "oxygen saturation"]
        )

        return self.ready(
            summary=f"Nurse vitals marked the patient as {status}.",
            findings=[f"Vital risk term: {term}" for term in risk_terms],
            recommendations=[f"Collect {item}." for item in recommended],
            decisions={
                "vitals_status": status,
                "risk_terms": risk_terms,
                "recommended_vitals": recommended,
            },
            handoff_to=["triage_nurse_agent"],
            confidence=0.78,
        )
