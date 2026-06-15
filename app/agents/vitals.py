from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import matched_terms


VITAL_RISK_TERMS = {
    "chest discomfort",
    "chest pain",
    "shortness of breath",
    "confusion",
    "high fever",
    "severe",
    "胸痛",
    "胸闷",
    "呼吸困难",
    "意识模糊",
    "高热",
}


class NurseVitalsAgent(HospitalAgent):
    name = "nurse_vitals_agent"
    role = "nurse_vitals"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        risk_terms = matched_terms(context.case_text, VITAL_RISK_TERMS)
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
