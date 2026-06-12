from __future__ import annotations

from dataclasses import asdict

from app.agents import (
    AppointmentAgent,
    CardiologySpecialistAgent,
    CarePlanAgent,
    FinalHospitalReportAgent,
    FollowUpAgent,
    GeneralPractitionerAgent,
    HospitalAgent,
    InfectiousDiseaseSpecialistAgent,
    IntakeAgent,
    LabAdvisorAgent,
    NeurologySpecialistAgent,
    PharmacySafetyAgent,
    RespiratorySpecialistAgent,
    SpecialistRouterAgent,
    TriageNurseAgent,
)
from app.agents.context import HospitalContext
from app.agents.llm import HospitalLlmClient, default_hospital_llm_client
from app.tools import AIConsultationTool


class HospitalOrchestrator:
    def __init__(
        self,
        agents: list[HospitalAgent] | None = None,
        llm_client: HospitalLlmClient | None = None,
        consultation_tool: AIConsultationTool | None = None,
    ) -> None:
        self.llm_client = llm_client or default_hospital_llm_client()
        self.consultation_tool = consultation_tool or AIConsultationTool()
        self.agents = agents or [
            IntakeAgent(),
            AppointmentAgent(),
            TriageNurseAgent(),
            GeneralPractitionerAgent(self.llm_client, self.consultation_tool),
            SpecialistRouterAgent(),
            RespiratorySpecialistAgent(self.llm_client),
            CardiologySpecialistAgent(self.llm_client),
            InfectiousDiseaseSpecialistAgent(self.llm_client),
            NeurologySpecialistAgent(self.llm_client),
            LabAdvisorAgent(),
            PharmacySafetyAgent(),
            CarePlanAgent(self.llm_client),
            FollowUpAgent(),
            FinalHospitalReportAgent(self.llm_client),
        ]

    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        language: str = "zh-CN",
    ) -> dict:
        context = HospitalContext(
            case_text=case_text,
            patient_id=patient_id,
            doctor_id=doctor_id,
            language=language,
        )
        results = []
        for agent in self.agents:
            results.append(agent.run(context, results))

        result_payloads = [asdict(result) for result in results]
        router = next(
            (result for result in results if result.agent == "specialist_router_agent"),
            None,
        )
        gp_result = next(
            (result for result in results if result.agent == "general_practitioner_agent"),
            None,
        )
        final_report = next(
            (result for result in results if result.agent == "final_hospital_report_agent"),
            None,
        )
        return {
            "workflow": "agent_hospital_lite",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "selected_specialties": (
                router.decisions.get("selected_specialties", []) if router else []
            ),
            "ai_consultation": (
                gp_result.data.get("ai_consultation_tool", {})
                if gp_result
                else {"workflow": "ai_consultation_tool"}
            ),
            "final_report": (
                asdict(final_report) if final_report else {"summary": "Final report unavailable."}
            ),
            "agent_results": result_payloads,
        }
