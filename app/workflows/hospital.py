from __future__ import annotations

from dataclasses import asdict

from app.agents import (
    AppointmentAgent,
    CardiologySpecialistAgent,
    CarePlanAgent,
    DispositionCoordinatorAgent,
    EmergencyPhysicianAgent,
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
        self.agents = agents
        self.agent_registry: dict[str, HospitalAgent] = {
            "intake_agent": IntakeAgent(),
            "appointment_agent": AppointmentAgent(),
            "triage_nurse_agent": TriageNurseAgent(),
            "emergency_physician_agent": EmergencyPhysicianAgent(self.llm_client),
            "general_practitioner_agent": GeneralPractitionerAgent(
                self.llm_client,
                self.consultation_tool,
            ),
            "specialist_router_agent": SpecialistRouterAgent(),
            "respiratory_specialist_agent": RespiratorySpecialistAgent(self.llm_client),
            "cardiology_specialist_agent": CardiologySpecialistAgent(self.llm_client),
            "infectious_disease_specialist_agent": InfectiousDiseaseSpecialistAgent(
                self.llm_client
            ),
            "neurology_specialist_agent": NeurologySpecialistAgent(self.llm_client),
            "lab_advisor_agent": LabAdvisorAgent(),
            "pharmacy_safety_agent": PharmacySafetyAgent(),
            "care_plan_agent": CarePlanAgent(self.llm_client),
            "follow_up_agent": FollowUpAgent(),
            "disposition_coordinator_agent": DispositionCoordinatorAgent(),
            "final_hospital_report_agent": FinalHospitalReportAgent(self.llm_client),
        }

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
        workflow_decisions = []
        if self.agents is not None:
            for agent in self.agents:
                results.append(agent.run(context, results))
        else:
            while True:
                remaining = self._planned_agents(results, workflow_decisions)
                if not remaining:
                    break
                results.append(remaining[0].run(context, results))

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
        disposition = next(
            (result for result in results if result.agent == "disposition_coordinator_agent"),
            None,
        )
        return {
            "workflow": "agent_hospital_lite",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "executed_path": [result.agent for result in results],
            "workflow_decisions": workflow_decisions,
            "selected_specialties": (
                router.decisions.get("selected_specialties", []) if router else []
            ),
            "disposition": (
                disposition.decisions.get("disposition", {})
                if disposition
                else {"decision": "not_available"}
            ),
            "care_pathway": _care_pathway(results),
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

    def _planned_agents(
        self,
        results: list,
        workflow_decisions: list[dict[str, str]],
    ) -> list[HospitalAgent]:
        completed = {result.agent for result in results}
        plan = [
            "intake_agent",
            "appointment_agent",
            "triage_nurse_agent",
        ]
        triage = next(
            (result for result in results if result.agent == "triage_nurse_agent"),
            None,
        )
        if triage is None:
            return [self.agent_registry[name] for name in plan if name not in completed]

        urgency = triage.decisions.get("urgency_level")
        if urgency == "high":
            _record_decision(
                workflow_decisions,
                decision="emergency_branch",
                made_by="triage_nurse_agent",
                reason="high triage urgency",
            )
            plan.extend(["emergency_physician_agent", "general_practitioner_agent"])
        else:
            _record_decision(
                workflow_decisions,
                decision="outpatient_branch",
                made_by="triage_nurse_agent",
                reason="standard triage urgency",
            )
            plan.append("general_practitioner_agent")

        plan.append("specialist_router_agent")
        router = next(
            (result for result in results if result.agent == "specialist_router_agent"),
            None,
        )
        if router:
            selected = list(router.decisions.get("selected_specialties", []))
            _record_decision(
                workflow_decisions,
                decision="specialist_consultation_branch",
                made_by="specialist_router_agent",
                reason=", ".join(selected) if selected else "no specialty selected",
            )
            plan.extend(f"{specialty}_specialist_agent" for specialty in selected)
            plan.extend(["lab_advisor_agent", "pharmacy_safety_agent"])
            if urgency == "high":
                plan.extend(["disposition_coordinator_agent", "final_hospital_report_agent"])
            else:
                plan.extend(
                    [
                        "care_plan_agent",
                        "follow_up_agent",
                        "disposition_coordinator_agent",
                        "final_hospital_report_agent",
                    ]
                )

        return [self.agent_registry[name] for name in plan if name not in completed]


def _record_decision(
    workflow_decisions: list[dict[str, str]],
    decision: str,
    made_by: str,
    reason: str,
) -> None:
    item = {"decision": decision, "made_by": made_by, "reason": reason}
    if item not in workflow_decisions:
        workflow_decisions.append(item)


def _care_pathway(results: list) -> dict:
    by_agent = {result.agent: result for result in results}
    triage = by_agent.get("triage_nurse_agent")
    router = by_agent.get("specialist_router_agent")
    lab = by_agent.get("lab_advisor_agent")
    pharmacy = by_agent.get("pharmacy_safety_agent")
    emergency = by_agent.get("emergency_physician_agent")
    disposition = by_agent.get("disposition_coordinator_agent")
    return {
        "encounter_type": (
            by_agent.get("appointment_agent", None).decisions.get("encounter_type")
            if by_agent.get("appointment_agent")
            else None
        ),
        "triage_level": triage.decisions.get("urgency_level") if triage else None,
        "immediate_actions": (
            emergency.decisions.get("immediate_actions", []) if emergency else []
        ),
        "consultations": (
            router.decisions.get("selected_specialties", []) if router else []
        ),
        "diagnostic_orders": (
            lab.decisions.get("recommended_tests", []) if lab else []
        ),
        "medication_safety": pharmacy.recommendations if pharmacy else [],
        "disposition": (
            disposition.decisions.get("disposition", {}) if disposition else {}
        ),
        "monitoring_plan": (
            disposition.decisions.get("monitoring_plan", []) if disposition else []
        ),
    }
