from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.rules import selected_specialties


class LabAdvisorAgent(HospitalAgent):
    name = "lab_advisor_agent"
    role = "lab_advisor"

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        selected = selected_specialties(previous)
        tests = ["CBC", "CRP"]
        if "respiratory" in selected:
            tests.extend(["chest X-ray", "oxygen saturation"])
        if "cardiology" in selected:
            tests.extend(["ECG", "troponin"])
        if "infectious_disease" in selected:
            tests.extend(["blood culture", "pathogen testing"])
        if "neurology" in selected:
            tests.extend(["neurological exam", "head CT if clinically indicated"])
        return self.ready(
            summary="Lab advisor recommended diagnostic workup items.",
            recommendations=tests,
            decisions={"recommended_tests": tests},
            handoff_to=["diagnostic_order_agent"],
        )
