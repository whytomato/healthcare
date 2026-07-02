from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError

import app.tools.care_coordination as care_coordination_module
import app.tools.emergency_operations as emergency_operations_module
import app.tools.patient_history_lookup as patient_history_module
from app.llm_client import LlmResult
from app.tools import AIConsultationTool, ClinicalToolRegistry
from app.workflows.planner import HospitalWorkflowPlanner
from app.workflows.hospital import HospitalOrchestrator


class FakeHospitalLlmClient:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        self.calls.append(messages)
        role = messages[0]["content"].split("ROLE:", 1)[1].split("\n", 1)[0].strip()
        return LlmResult(
            status="ready",
            content=f"LLM generated hospital output for {role}.",
        )


class JsonHospitalLlmClient(FakeHospitalLlmClient):
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        self.calls.append(messages)
        return LlmResult(
            status="ready",
            content=json.dumps(
                {
                    "summary": "Structured role summary.",
                    "findings": ["Structured finding."],
                    "recommendations": ["Structured recommendation."],
                    "handoff_reason": "Structured handoff reason.",
                    "confidence": 0.86,
                }
            ),
        )


class FakeAIConsultationTool:
    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        language: str = "zh-CN",
    ) -> dict:
        return {
            "workflow": "ai_consultation_tool",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "status": "ready",
            "symptoms": ["mock symptom"],
            "llm_output": "mock tool output",
        }


class FakePatientHistoryLookupTool:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, patient_id: str | None) -> dict:
        self.calls.append(patient_id or "")
        return {
            "tool": "patient_history_lookup",
            "status": "ready",
            "patientId": patient_id,
            "summary": {
                "patientId": patient_id,
                "recentEncounters": [{"taskId": "prior-task"}],
                "allergies": ["penicillin"],
                "currentMedications": ["metformin"],
                "previousDispositions": ["outpatient_follow_up"],
                "lastFinalReports": ["Prior respiratory follow-up completed."],
            },
        }


class FakeCareCoordinationTool:
    name = "care_coordination"

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        doctor_id: str | None,
        disposition: str,
        triage_urgency: str,
        selected_specialties: list[str],
        monitoring_plan: list[str],
    ) -> dict:
        return {
            "tool": self.name,
            "status": "ready",
            "summary": "Mock care coordination plan returned.",
            "payload": {
                "taskId": task_id,
                "patientId": patient_id,
                "doctorId": doctor_id,
                "status": "ready",
                "disposition": disposition,
                "triageUrgency": triage_urgency,
                "selectedSpecialties": selected_specialties,
                "followUpActions": monitoring_plan,
                "referralActions": [],
                "admissionActions": [],
                "humanReviewRequired": triage_urgency == "high",
            },
        }


class FakePractitionerAssignmentTool:
    name = "practitioner_assignment"

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        urgency_level: str,
        required_specialties: list[str],
    ) -> dict:
        return {
            "tool": self.name,
            "status": "ready",
            "summary": "Mock practitioner assignment returned.",
            "payload": {
                "taskId": task_id,
                "patientId": patient_id,
                "urgencyLevel": urgency_level,
                "requiredSpecialties": required_specialties,
                "assignedPractitioners": ["emergency_physician_on_call"],
                "unavailableSpecialties": [],
                "assignmentStatus": "ready",
            },
        }


class FakeEmergencyEncounterTool:
    name = "emergency_encounter"

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        triage_urgency: str,
        red_flags: list[str],
    ) -> dict:
        return {
            "tool": self.name,
            "status": "ready",
            "summary": "Mock emergency encounter returned.",
            "payload": {
                "taskId": task_id,
                "patientId": patient_id,
                "emergencyEncounterId": f"mock-{task_id}",
                "status": "opened",
                "triageUrgency": triage_urgency,
                "redFlags": red_flags,
            },
        }

    def update_readiness(
        self,
        task_id: str,
        emergency_encounter_id: str,
        resource_readiness_status: str,
        reserved_resources: list[str],
    ) -> dict:
        return {
            "tool": "emergency_readiness_update",
            "status": "ready",
            "summary": "Mock emergency readiness update returned.",
            "payload": {
                "taskId": task_id,
                "emergencyEncounterId": emergency_encounter_id,
                "status": "readiness_confirmed",
                "resourceReadinessStatus": resource_readiness_status,
                "reservedResources": reserved_resources,
            },
        }


class FakeResourceReservationTool:
    name = "resource_reservation"

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        urgency_level: str,
        required_resources: list[str],
    ) -> dict:
        return {
            "tool": self.name,
            "status": "ready",
            "summary": "Mock resource reservation returned.",
            "payload": {
                "taskId": task_id,
                "patientId": patient_id,
                "urgencyLevel": urgency_level,
                "requiredResources": required_resources,
                "reservedResources": required_resources or ["resuscitation_room"],
                "readinessStatus": "ready",
            },
        }


class FakeExamSchedulingTool:
    name = "exam_scheduling"

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        ordering_agent: str,
        requested_exams: list[str],
        urgency_level: str,
    ) -> dict:
        return {
            "tool": self.name,
            "status": "ready",
            "summary": "Mock exam scheduling returned.",
            "payload": {
                "taskId": task_id,
                "patientId": patient_id,
                "orderingAgent": ordering_agent,
                "requestedExams": requested_exams,
                "scheduledExams": requested_exams,
                "scheduleStatus": "ready",
                "urgencyLevel": urgency_level,
            },
        }


class FastClinicalToolRegistry(ClinicalToolRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.care_coordination = FakeCareCoordinationTool()
        self.emergency_encounter = FakeEmergencyEncounterTool()
        self.practitioner_assignment = FakePractitionerAssignmentTool()
        self.resource_reservation = FakeResourceReservationTool()
        self.exam_scheduling = FakeExamSchedulingTool()


class SlowFakeHospitalLlmClient(FakeHospitalLlmClient):
    def __init__(self, delay_seconds: float) -> None:
        super().__init__()
        self.delay_seconds = delay_seconds

    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        time.sleep(self.delay_seconds)
        return super().chat(messages)


class FakeHandoffAgent:
    def __init__(self, name: str, handoff_to: list[str] | None = None) -> None:
        self.name = name
        self.role = name.replace("_agent", "")
        self._handoff_to = handoff_to or []

    def run(self, context, previous):
        return self.ready(
            summary=f"{self.name} completed.",
            handoff_to=self._handoff_to,
        )

    def ready(self, **kwargs):
        from app.agents.context import HospitalAgentResult

        return HospitalAgentResult(
            agent=self.name,
            status="ready",
            role=self.role,
            summary=kwargs["summary"],
            handoff_to=kwargs.get("handoff_to", []),
        )


class RoguePlanner:
    def plan(self, results):
        from app.workflows.planner import WorkflowPlan

        return WorkflowPlan(["registration_agent", "final_hospital_report_agent"])


def test_hospital_orchestrator_runs_complete_agent_hospital_workflow() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    agent_names = [item["agent"] for item in result["agent_results"]]

    assert result["workflow"] == "agent_hospital_lite"
    assert agent_names == result["executed_path"]
    assert all(item["status"] == "ready" for item in result["agent_results"])
    assert {"respiratory", "cardiology", "infectious_disease", "neurology"}.issubset(
        set(result["selected_specialties"])
    )
    assert result["ai_consultation"]["workflow"] == "ai_consultation_tool"
    assert result["final_report"]["summary"]


def test_final_hospital_report_agent_returns_markdown_for_frontend_rendering() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="A 67-year-old male has fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    markdown = result["final_report"]["data"]["markdown"]

    assert markdown.startswith("## Final Hospital Report")
    assert "- **Selected specialties:**" in markdown
    assert "- **Disposition:**" in markdown


def test_hospital_orchestrator_uses_agent_handoffs_as_real_scheduling_input() -> None:
    result = HospitalOrchestrator(
        agents=[
            FakeHandoffAgent("third_agent"),
            FakeHandoffAgent("first_agent", ["second_agent"]),
            FakeHandoffAgent("second_agent", ["third_agent"]),
        ],
        entry_agents=["first_agent"],
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(case_text="handoff scheduling demo")

    assert result["executed_path"] == [
        "first_agent",
        "second_agent",
        "third_agent",
    ]
    handoffs = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] == "handoff_created"
    ]
    assert handoffs[0]["target_agents"] == ["second_agent"]
    assert handoffs[1]["target_agents"] == ["third_agent"]


def test_default_hospital_workflow_is_scheduled_from_agent_handoffs() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest pain, shortness of breath and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    handoff_targets = [
        target
        for event in result["handoff_timeline"]
        if event["event_type"] == "handoff_created"
        for target in event["target_agents"]
    ]

    assert "emergency_physician_agent" in handoff_targets
    assert "emergency_physician_agent" in result["executed_path"]
    assert_path_contains_in_order(
        result["executed_path"],
        [
            "triage_nurse_agent",
            "department_router_agent",
            "emergency_physician_agent",
            "general_practitioner_agent",
            "specialist_router_agent",
        ],
    )


def test_default_hospital_workflow_does_not_run_unhandoffed_planner_agents() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        planner=RoguePlanner(),
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p002",
        doctor_id="d001",
    )

    assert result["executed_path"][:3] == [
        "registration_agent",
        "intake_agent",
        "nurse_vitals_agent",
    ]
    assert result["executed_path"].index("final_hospital_report_agent") > result[
        "executed_path"
    ].index("disposition_coordinator_agent")


def test_hospital_workflow_models_complete_demo_hospital_visit_decision_points() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    expected_agents = [
        "registration_agent",
        "nurse_vitals_agent",
        "department_router_agent",
        "lab_result_interpreter_agent",
        "imaging_interpreter_agent",
        "ordering_clinician_review_agent",
        "medication_plan_agent",
        "admission_coordinator_agent",
    ]
    for agent_name in expected_agents:
        assert agent_name in result["executed_path"]

    decisions = {
        event["decision"]: event
        for event in result["handoff_timeline"]
        if event["event_type"] == "decision_made"
    }

    assert decisions["registration_completed"]["decision_scope"] == "administrative"
    assert decisions["abnormal_vitals_detected"]["decision_scope"] == "triage"
    assert decisions["department_route_selected"]["decision_scope"] == "routing"
    assert decisions["lab_results_interpreted"]["decision_scope"] == "clinical"
    assert decisions["imaging_results_interpreted"]["decision_scope"] == "clinical"
    assert decisions["ordering_clinician_review_completed"]["decision_scope"] == "review_loop"
    assert decisions["medication_plan_created"]["decision_scope"] == "medication"
    assert decisions["admission_pathway_selected"]["decision_scope"] == "admission"

    assert result["care_pathway"]["department_route"]
    assert result["care_pathway"]["lab_interpretation"]
    assert result["care_pathway"]["imaging_interpretation"]
    assert result["care_pathway"]["medication_plan"]
    assert result["care_pathway"]["admission_pathway"]


def test_high_risk_patient_encounter_follows_emergency_branch() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    assert_path_contains_in_order(
        result["executed_path"],
        [
            "specialist_router_agent",
            "respiratory_specialist_agent",
            "cardiology_specialist_agent",
            "infectious_disease_specialist_agent",
            "neurology_specialist_agent",
            "lab_result_interpreter_agent",
            "imaging_interpreter_agent",
            "ordering_clinician_review_agent",
        ],
    )
    assert result["workflow_decisions"][0] == {
        "decision": "emergency_branch",
        "made_by": "triage_nurse_agent",
        "reason": "high triage urgency",
    }
    assert {"respiratory", "cardiology", "infectious_disease", "neurology"}.issubset(
        set(result["selected_specialties"])
    )
    assert result["disposition"]["decision"] == "emergency_reassessment"
    assert result["care_pathway"]["triage_level"] == "high"
    assert result["care_pathway"]["diagnostic_orders"]
    assert result["care_pathway"]["medication_safety"]


def test_standard_patient_encounter_follows_outpatient_branch() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p002",
        doctor_id="d001",
    )

    assert result["workflow_decisions"][0] == {
        "decision": "outpatient_branch",
        "made_by": "triage_nurse_agent",
        "reason": "standard triage urgency",
    }
    assert "emergency_physician_agent" not in result["executed_path"]
    assert "respiratory_specialist_agent" in result["executed_path"]
    assert "cardiology_specialist_agent" not in result["executed_path"]
    assert "neurology_specialist_agent" not in result["executed_path"]
    assert result["selected_specialties"] == ["respiratory"]
    assert result["disposition"]["decision"] == "outpatient_follow_up"


def test_frontend_outpatient_demo_case_does_not_treat_negated_red_flags_as_emergency() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text=(
            "A 34-year-old female has cough, low-grade fever, sore throat and fatigue "
            "for three days. She is alert, able to drink fluids, and reports no chest "
            "pain, confusion or severe shortness of breath."
        ),
        patient_id="p-outpatient-001",
        doctor_id="d-gp-001",
    )

    triage_event = next(
        event
        for event in result["handoff_timeline"]
        if event.get("agent") == "triage_nurse_agent"
        and event.get("event_type") == "decision_made"
    )
    vitals_event = next(
        event
        for event in result["handoff_timeline"]
        if event.get("agent") == "nurse_vitals_agent"
        and event.get("event_type") == "decision_made"
    )

    assert result["workflow_decisions"][0]["decision"] == "outpatient_branch"
    assert triage_event["payload"]["red_flags"] == []
    assert vitals_event["decision"] == "stable_vitals_recorded"
    assert "emergency_physician_agent" not in result["executed_path"]
    assert "cardiology_specialist_agent" not in result["executed_path"]
    assert "neurology_specialist_agent" not in result["executed_path"]


def test_patient_history_lookup_tool_informs_registration_without_worker_prefetch() -> None:
    history_tool = FakePatientHistoryLookupTool()

    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        patient_history_tool=history_tool,
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p-history-001",
        doctor_id="d001",
    )

    results_by_agent = {item["agent"]: item for item in result["agent_results"]}

    assert history_tool.calls
    assert result["workflow_decisions"][0]["decision"] == "outpatient_branch"
    assert results_by_agent["registration_agent"]["decisions"]["visit_type"] == "returning_patient"
    assert results_by_agent["registration_agent"]["decisions"]["prior_encounter_count"] == 1
    assert results_by_agent["registration_agent"]["data"]["patient_history_lookup"]["status"] == "ready"
    assert "patient_history" not in result


def test_patient_history_lookup_is_rendered_as_agent_tool_use_not_prefetch() -> None:
    history_tool = FakePatientHistoryLookupTool()

    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        patient_history_tool=history_tool,
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p-history-001",
        doctor_id="d001",
    )

    tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] == "tool_invoked"
    ]

    assert {
        "registration_agent",
        "pharmacy_safety_agent",
        "care_plan_agent",
        "follow_up_agent",
        "final_hospital_report_agent",
    }.issubset({event["agent"] for event in tool_events})
    assert "triage_nurse_agent" not in {event["agent"] for event in tool_events}
    assert tool_events[0]["decision_scope"] == "tool_use"
    assert tool_events[0]["payload"]["tool"] == "patient_history_lookup"
    assert tool_events[0]["payload"]["status"] == "ready"
    assert tool_events[0]["reason"] == "identify whether this is a new or returning patient"
    assert tool_events[0]["payload"]["choice"] == "selected"
    assert tool_events[0]["payload"]["selection_reason"] == tool_events[0]["reason"]
    assert "{'patientId'" not in tool_events[0]["reason"]


def test_patient_history_lookup_tool_informs_pharmacy_and_final_report_not_triage() -> None:
    history_tool = FakePatientHistoryLookupTool()

    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        patient_history_tool=history_tool,
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p-history-001",
        doctor_id="d001",
    )

    results_by_agent = {item["agent"]: item for item in result["agent_results"]}

    assert result["workflow_decisions"][0]["decision"] == "outpatient_branch"
    assert results_by_agent["pharmacy_safety_agent"]["decisions"]["known_allergies"] == ["penicillin"]
    assert "metformin" in results_by_agent["pharmacy_safety_agent"]["recommendations"][0]
    assert results_by_agent["final_hospital_report_agent"]["data"]["patient_history_used"] is True
    assert "Prior respiratory follow-up completed." in results_by_agent["final_hospital_report_agent"]["findings"]


def test_hospital_agents_choose_from_multiple_internal_tools_during_visit() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest pain, shortness of breath and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    ]
    tool_names = {event["payload"]["tool"] for event in tool_events}
    tool_statuses = {
        event["payload"]["tool"]: event["payload"]["status"]
        for event in tool_events
    }

    assert {
        "guideline_lookup",
        "exam_scheduling",
        "lab_result_fetch",
        "imaging_result_fetch",
        "medication_interaction",
        "bed_availability",
        "human_review_request",
    }.issubset(tool_names)
    assert tool_statuses["exam_scheduling"] in {"ready", "unavailable"}
    assert tool_statuses["bed_availability"] == "ready"
    assert tool_statuses["human_review_request"] == "ready"


def test_admission_agent_can_use_care_coordination_service_tool() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest pain, shortness of breath and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    admission = next(
        item
        for item in result["agent_results"]
        if item["agent"] == "admission_coordinator_agent"
    )
    tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] == "tool_invoked"
        and event["payload"]["tool"] == "care_coordination"
    ]

    assert admission["data"]["care_coordination_plan"]["status"] in {
        "ready",
        "unavailable",
    }
    assert "followUpActions" in admission["data"]["care_coordination_plan"]
    assert tool_events


def test_standard_visit_can_skip_tools_when_agent_decides_they_are_not_needed() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p002",
        doctor_id="d001",
    )

    skipped = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] == "tool_skipped"
    ]

    assert any(event["payload"]["tool"] == "bed_availability" for event in skipped)
    assert any(event["payload"]["tool"] == "human_review_request" for event in skipped)


def test_chinese_red_flag_patient_encounter_follows_emergency_branch() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="患者出现胸痛、呼吸困难和意识模糊。",
        patient_id="p003",
        doctor_id="d001",
    )

    assert result["workflow_decisions"][0]["decision"] == "emergency_branch"
    assert result["care_pathway"]["triage_level"] == "high"
    assert "emergency_physician_agent" in result["executed_path"]


def test_workflow_planner_is_public_boundary_for_branch_decisions() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        planner=HospitalWorkflowPlanner(),
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p002",
        doctor_id="d001",
    )

    assert result["workflow_decisions"][0]["made_by"] == "triage_nurse_agent"
    assert result["workflow_decisions"][0]["decision"] == "outpatient_branch"


def test_hospital_orchestrator_uses_llm_for_reasoning_roles_when_client_is_available() -> None:
    client = FakeHospitalLlmClient()

    result = HospitalOrchestrator(
        llm_client=client,
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="fever, productive cough, chest discomfort and confusion",
        patient_id="p001",
        doctor_id="d001",
    )

    results_by_agent = {item["agent"]: item for item in result["agent_results"]}

    for agent_name in [
        "emergency_physician_agent",
        "general_practitioner_agent",
        "respiratory_specialist_agent",
        "cardiology_specialist_agent",
        "infectious_disease_specialist_agent",
        "neurology_specialist_agent",
        "final_hospital_report_agent",
    ]:
        assert results_by_agent[agent_name]["data"]["llm_driven"] is True
        assert "LLM generated hospital output" in results_by_agent[agent_name]["findings"][0]

    assert len(client.calls) >= 7


def test_llm_capable_agents_request_and_expose_structured_role_outputs() -> None:
    client = JsonHospitalLlmClient()

    result = HospitalOrchestrator(
        llm_client=client,
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="fever, productive cough, chest discomfort and confusion",
        patient_id="p001",
        doctor_id="d001",
    )

    emergency = next(
        item for item in result["agent_results"] if item["agent"] == "emergency_physician_agent"
    )
    final_report = result["final_report"]

    assert "Return only JSON" in client.calls[0][0]["content"]
    assert '"summary"' in client.calls[0][0]["content"]
    assert emergency["data"]["llm_structured"]["summary"] == "Structured role summary."
    assert emergency["data"]["llm_structured"]["findings"] == ["Structured finding."]
    assert final_report["data"]["llm_structured"]["recommendations"] == [
        "Structured recommendation."
    ]


def test_llm_capable_agents_parse_fenced_json_structured_outputs() -> None:
    class FencedJsonHospitalLlmClient:
        def chat(self, messages):
            return LlmResult(
                status="ready",
                content=(
                    "```json\n"
                    "{\n"
                    '  "summary": "Readable clinical summary.",\n'
                    '  "findings": ["Readable finding."],\n'
                    '  "recommendations": ["Readable recommendation."],\n'
                    '  "handoff_reason": "Readable handoff.",\n'
                    '  "confidence": 0.91\n'
                    "}\n"
                    "```"
                ),
            )

    result = HospitalOrchestrator(
        llm_client=FencedJsonHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="A 45-year-old male requests low risk allergy follow-up.",
        patient_id="p-fenced-json",
        doctor_id="d001",
    )

    final_report = result["final_report"]

    assert final_report["summary"] == "Readable clinical summary."
    assert final_report["data"]["report_summary"] == "Readable clinical summary."
    assert "```json" not in final_report["summary"]
    assert "```json" not in final_report["data"]["markdown"]
    assert final_report["data"]["llm_structured"]["findings"] == ["Readable finding."]


def test_optional_external_tools_use_short_demo_timeouts(monkeypatch) -> None:
    patient_history_timeouts: list[float] = []
    care_coordination_timeouts: list[float] = []

    def slow_patient_history_response(request, timeout):
        patient_history_timeouts.append(timeout)
        raise TimeoutError("history service did not answer in demo time")

    def slow_care_coordination_response(request, timeout):
        care_coordination_timeouts.append(timeout)
        raise TimeoutError("care service did not answer in demo time")

    monkeypatch.delenv("CLINICAL_RECORD_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("CARE_COORDINATION_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setattr(patient_history_module, "urlopen", slow_patient_history_response)
    monkeypatch.setattr(care_coordination_module, "urlopen", slow_care_coordination_response)

    history = patient_history_module.PatientHistoryLookupTool().run("p-timeout")
    care = care_coordination_module.CareCoordinationTool().run(
        task_id="t-timeout",
        patient_id="p-timeout",
        doctor_id="d001",
        disposition="outpatient_follow_up",
        triage_urgency="standard",
        selected_specialties=["respiratory"],
        monitoring_plan=["Review test results when available."],
    )

    assert history["status"] == "unavailable"
    assert care["status"] == "unavailable"
    assert patient_history_timeouts == [0.5]
    assert care_coordination_timeouts == [0.5]


def test_emergency_operation_tools_allow_service_response_time_under_surge(monkeypatch) -> None:
    captured_timeouts: list[float] = []

    def service_response(request, timeout):
        captured_timeouts.append(timeout)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(
                    {
                        "taskId": "er-timeout-task",
                        "patientId": "p-timeout",
                        "readinessStatus": "ready",
                        "reservedResources": ["resuscitation_room"],
                        "unavailableResources": [],
                    }
                ).encode("utf-8")

        return Response()

    monkeypatch.delenv("EMERGENCY_SERVICE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setattr(emergency_operations_module, "urlopen", service_response)

    result = emergency_operations_module.ResourceReservationTool().run(
        task_id="er-timeout-task",
        patient_id="p-timeout",
        urgency_level="high",
        required_resources=["resuscitation_room"],
    )

    assert result["status"] == "ready"
    assert result["payload"]["readinessStatus"] == "ready"
    assert captured_timeouts == [2.0]


def test_emergency_operation_tools_retry_transient_service_errors_before_fallback(monkeypatch) -> None:
    attempts = 0

    def transient_service_response(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise HTTPError(request.full_url, 500, "temporary lock conflict", {}, None)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(
                    {
                        "taskId": "er-retry-task",
                        "patientId": "p-retry",
                        "assignmentStatus": "assigned",
                        "assignedPractitioners": ["er-physician-1", "charge-nurse-1"],
                        "unavailableSpecialties": [],
                    }
                ).encode("utf-8")

        return Response()

    monkeypatch.setattr(emergency_operations_module, "urlopen", transient_service_response)
    monkeypatch.setattr(emergency_operations_module, "sleep", lambda seconds: None, raising=False)

    result = emergency_operations_module.PractitionerAssignmentTool().run(
        task_id="er-retry-task",
        patient_id="p-retry",
        urgency_level="high",
        required_specialties=[],
    )

    assert result["status"] == "ready"
    assert result["payload"]["assignmentStatus"] == "assigned"
    assert attempts == 3


def test_hospital_orchestrator_runs_selected_specialist_consultations_in_parallel() -> None:
    client = SlowFakeHospitalLlmClient(delay_seconds=0.2)

    started = time.perf_counter()
    result = HospitalOrchestrator(
        llm_client=client,
        consultation_tool=FakeAIConsultationTool(),
        patient_history_tool=FakePatientHistoryLookupTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="fever, productive cough, chest discomfort and confusion",
        patient_id="p001",
        doctor_id="d001",
    )
    elapsed = time.perf_counter() - started

    assert_path_contains_in_order(
        result["executed_path"],
        [
            "registration_agent",
            "nurse_vitals_agent",
            "triage_nurse_agent",
            "department_router_agent",
            "emergency_physician_agent",
            "general_practitioner_agent",
            "specialist_router_agent",
            "lab_result_interpreter_agent",
            "imaging_interpreter_agent",
            "ordering_clinician_review_agent",
            "pharmacy_safety_agent",
            "medication_plan_agent",
            "disposition_coordinator_agent",
            "admission_coordinator_agent",
            "final_hospital_report_agent",
        ],
    )
    assert elapsed < 1.2


def test_hospital_orchestrator_returns_agent_handoff_timeline() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    timeline = result["handoff_timeline"]
    event_types = [event["event_type"] for event in timeline]
    decisions = {
        event["decision"]: event
        for event in timeline
        if event["event_type"] == "decision_made"
    }

    assert [event["event_index"] for event in timeline] == list(range(len(timeline)))
    assert "agent_completed" in event_types
    assert "decision_made" in event_types
    assert "handoff_created" in event_types
    assert "parallel_fanout" in event_types
    assert "fanin_completed" in event_types

    assert decisions["emergency_branch"]["decision_scope"] == "routing"
    assert decisions["specialist_consultation_branch"]["decision_scope"] == "routing"
    assert decisions["ordering_clinician_review_completed"]["decision_scope"] == "review_loop"
    assert decisions["medication_safety_review_required"]["decision_scope"] == "clinical"
    assert decisions["emergency_reassessment"]["decision_scope"] == "disposition"

    fanout = next(event for event in timeline if event["event_type"] == "parallel_fanout")
    fanin = next(event for event in timeline if event["event_type"] == "fanin_completed")
    assert fanout["target_agents"] == [
        "respiratory_specialist_agent",
        "cardiology_specialist_agent",
        "infectious_disease_specialist_agent",
        "neurology_specialist_agent",
    ]
    assert fanout["parallel_group"] == fanin["parallel_group"]
    assert fanin["payload"]["completed_agents"] == fanout["target_agents"]


def test_timeline_explains_role_scoped_agent_decisions_and_tool_choices() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest pain, shortness of breath and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    timeline = result["handoff_timeline"]
    decisions = {
        event["decision"]: event
        for event in timeline
        if event["event_type"] == "decision_made"
    }
    key_decisions = [
        "emergency_branch",
        "department_route_selected",
        "specialist_consultation_branch",
        "ordering_clinician_review_completed",
        "medication_safety_review_required",
        "emergency_reassessment",
        "admission_pathway_selected",
    ]

    for decision_name in key_decisions:
        payload = decisions[decision_name]["payload"]
        assert payload["decision_type"] == "role_scoped_agent_decision"
        assert payload["role"]
        assert isinstance(payload["handoff_to"], list)
        assert isinstance(payload["tool_choices"], list)
        assert payload["evidence"]

    assert decisions["emergency_branch"]["payload"]["handoff_to"] == [
        "department_router_agent"
    ]
    assert decisions["department_route_selected"]["payload"]["handoff_to"] == [
        "emergency_physician_agent"
    ]
    assert {
        "respiratory_specialist_agent",
        "cardiology_specialist_agent",
        "infectious_disease_specialist_agent",
        "neurology_specialist_agent",
    }.issubset(
        set(decisions["specialist_consultation_branch"]["payload"]["handoff_to"])
    )

    guideline_choice = next(
        choice
        for choice in decisions["emergency_branch"]["payload"]["tool_choices"]
        if choice["tool"] == "guideline_lookup"
    )
    assert guideline_choice["choice"] == "selected"
    assert guideline_choice["reason"]

    tool_events = [
        event
        for event in timeline
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    ]
    assert tool_events
    for event in tool_events:
        payload = event["payload"]
        assert payload["decision_type"] == "role_scoped_agent_decision"
        assert payload["role"]
        assert payload["choice"] in {"selected", "skipped", "unavailable"}
        assert payload["selection_reason"] == event["reason"]


def test_demo_paths_expose_distinct_selected_and_skipped_branches() -> None:
    outpatient = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="35-year-old patient with mild dry cough for two days.",
        patient_id="p002",
        doctor_id="d001",
    )
    emergency = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest pain, shortness of breath and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    outpatient_decisions = {
        event["decision"]: event
        for event in outpatient["handoff_timeline"]
        if event["event_type"] == "decision_made"
    }
    emergency_decisions = {
        event["decision"]: event
        for event in emergency["handoff_timeline"]
        if event["event_type"] == "decision_made"
    }

    assert "emergency_physician_agent" not in outpatient["executed_path"]
    assert "emergency_physician_agent" in emergency["executed_path"]
    assert outpatient_decisions["outpatient_branch"]["payload"]["selected_branch"] == {
        "target": "department_router_agent",
        "reason": "standard triage urgency",
    }
    assert outpatient_decisions["department_route_selected"]["payload"]["skipped_branches"] == [
        {
            "target": "emergency_physician_agent",
            "reason": "standard urgency routes to general practitioner first",
        }
    ]
    assert emergency_decisions["department_route_selected"]["payload"]["selected_branch"] == {
        "target": "emergency_physician_agent",
        "reason": "high triage urgency routes to emergency physician first",
    }
    assert emergency_decisions["specialist_consultation_branch"]["payload"]["parallel_branch"] is True
    assert outpatient_decisions["specialist_consultation_branch"]["payload"]["parallel_branch"] is False

    outpatient_tools = {
        event["payload"]["tool"]: event["payload"]
        for event in outpatient["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    }
    emergency_tools = {
        event["payload"]["tool"]: event["payload"]
        for event in emergency["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    }

    assert outpatient_tools["guideline_lookup"]["choice"] == "skipped"
    assert outpatient_tools["human_review_request"]["choice"] == "skipped"
    assert outpatient_tools["bed_availability"]["choice"] == "skipped"
    assert emergency_tools["guideline_lookup"]["choice"] == "selected"
    assert emergency_tools["human_review_request"]["choice"] == "selected"
    assert emergency_tools["bed_availability"]["choice"] == "selected"


def test_hospital_orchestrator_waits_for_lab_and_imaging_before_pharmacy_fanin() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    timeline = result["handoff_timeline"]
    completed_index = {
        event["agent"]: event["event_index"]
        for event in timeline
        if event["event_type"] == "agent_completed"
    }
    fanin = next(
        event
        for event in timeline
        if event["event_type"] == "fanin_completed"
        and event["target_agents"] == ["ordering_clinician_review_agent"]
    )

    assert fanin["payload"]["completed_agents"] == [
        "lab_result_interpreter_agent",
        "imaging_interpreter_agent",
    ]
    assert completed_index["lab_result_interpreter_agent"] < completed_index["ordering_clinician_review_agent"]
    assert completed_index["imaging_interpreter_agent"] < completed_index["ordering_clinician_review_agent"]
    assert fanin["event_index"] < completed_index["ordering_clinician_review_agent"]
    assert completed_index["ordering_clinician_review_agent"] < completed_index["pharmacy_safety_agent"]


def test_emergency_room_workflow_front_loads_microservice_resource_readiness() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="67-year-old male with chest pain, shortness of breath, fever and confusion.",
        patient_id="p-er-001",
        doctor_id="d-er-001",
        metadata={"taskId": "er-task-001"},
    )

    tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    ]
    emergency_tools = {
        event["payload"]["tool"]: event
        for event in tool_events
        if event["agent"] == "emergency_physician_agent"
    }

    assert emergency_tools["practitioner_assignment"]["event_type"] == "tool_invoked"
    assert emergency_tools["resource_reservation"]["event_type"] == "tool_invoked"
    assert emergency_tools["exam_scheduling"]["event_type"] == "tool_invoked"
    assert emergency_tools["practitioner_assignment"]["payload"]["choice"] in {"selected", "unavailable"}
    assert emergency_tools["resource_reservation"]["payload"]["choice"] in {"selected", "unavailable"}
    assert emergency_tools["exam_scheduling"]["payload"]["choice"] in {"selected", "unavailable"}
    assert "assignedPractitioners" in emergency_tools["practitioner_assignment"]["payload"]
    assert "unavailableSpecialties" in emergency_tools["practitioner_assignment"]["payload"]
    assert emergency_tools["exam_scheduling"]["payload"]["orderingAgent"] == "emergency_physician_agent"
    assert "resuscitation_room" in emergency_tools["resource_reservation"]["payload"]["reservedResources"]
    assert any(
        event["event_type"] == "decision_made"
        and event["agent"] == "emergency_physician_agent"
        and event["decision"] == "emergency_resource_readiness_confirmed"
        for event in result["handoff_timeline"]
    )


def test_emergency_room_workflow_opens_emergency_encounter_before_resource_allocation() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with chest pain, shortness of breath, fever and confusion.",
        patient_id="p-er-003",
        doctor_id="d-er-001",
        metadata={"taskId": "er-task-003"},
    )

    emergency_tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
        and event["agent"] == "emergency_physician_agent"
    ]
    event_by_tool = {
        event["payload"]["tool"]: event
        for event in emergency_tool_events
    }

    assert event_by_tool["emergency_encounter"]["event_type"] == "tool_invoked"
    assert event_by_tool["emergency_encounter"]["payload"]["triageUrgency"] == "high"
    assert event_by_tool["emergency_encounter"]["event_index"] < event_by_tool[
        "practitioner_assignment"
    ]["event_index"]
    assert event_by_tool["emergency_encounter"]["event_index"] < event_by_tool[
        "resource_reservation"
    ]["event_index"]
    assert event_by_tool["emergency_encounter"]["event_index"] < event_by_tool[
        "exam_scheduling"
    ]["event_index"]


def test_emergency_room_workflow_updates_emergency_encounter_after_resource_reservation() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
        tool_registry=FastClinicalToolRegistry(),
    ).run(
        case_text="67-year-old male with chest pain, shortness of breath, fever and confusion.",
        patient_id="p-er-004",
        doctor_id="d-er-001",
        metadata={"taskId": "er-task-004"},
    )

    emergency_tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
        and event["agent"] == "emergency_physician_agent"
    ]
    event_by_tool = {
        event["payload"]["tool"]: event
        for event in emergency_tool_events
    }

    assert event_by_tool["emergency_readiness_update"]["event_type"] == "tool_invoked"
    assert event_by_tool["resource_reservation"]["event_index"] < event_by_tool[
        "emergency_readiness_update"
    ]["event_index"]
    assert event_by_tool["emergency_readiness_update"]["payload"][
        "resourceReadinessStatus"
    ] == event_by_tool["resource_reservation"]["payload"]["readinessStatus"]
    assert event_by_tool["emergency_readiness_update"]["payload"]["reservedResources"]


def test_specialist_orders_exams_and_receives_ordering_clinician_review_signal() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with chest pain, shortness of breath, fever and confusion.",
        patient_id="p-er-002",
        doctor_id="d-er-001",
        metadata={"taskId": "er-task-002"},
    )

    tool_events = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] in {"tool_invoked", "tool_skipped"}
    ]
    specialist_exam_schedules = [
        event
        for event in tool_events
        if event["payload"]["tool"] == "exam_scheduling"
        and event["agent"].endswith("_specialist_agent")
    ]

    assert specialist_exam_schedules
    assert all(
        event["payload"]["orderingAgent"] == event["agent"]
        for event in specialist_exam_schedules
    )
    assert any(
        event["event_type"] == "decision_made"
        and event["decision"] == "ordering_clinician_review_required"
        and event["payload"]["ordering_agent"].endswith("_specialist_agent")
        for event in result["handoff_timeline"]
    )


def test_workflow_pauses_lab_advisor_and_diagnostic_order_agents_for_ordering_clinician_loop() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with chest pain, shortness of breath, fever and confusion.",
        patient_id="p-loop-001",
        doctor_id="d-er-001",
        metadata={"taskId": "loop-task-001"},
    )

    path = result["executed_path"]
    assert "lab_advisor_agent" not in path
    assert "diagnostic_order_agent" not in path
    assert "lab_result_interpreter_agent" in path
    assert "imaging_interpreter_agent" in path
    assert "ordering_clinician_review_agent" in path
    assert path.index("lab_result_interpreter_agent") < path.index("ordering_clinician_review_agent")
    assert path.index("imaging_interpreter_agent") < path.index("ordering_clinician_review_agent")

    decisions = [
        event
        for event in result["handoff_timeline"]
        if event["event_type"] == "decision_made"
    ]
    assert any(
        event["decision"] == "ordering_clinician_review_completed"
        and event["payload"]["ordering_agents"]
        for event in decisions
    )


def test_hospital_cli_writes_complete_workflow_result() -> None:
    output = Path("outputs/hospital_workflow.test.json")

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "app.main",
            "--case-text",
            "fever, cough, chest discomfort and confusion",
            "--patient-id",
            "p001",
            "--doctor-id",
            "d001",
            "--output",
            str(output),
            "--mock-llm",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert "agent_hospital_lite" in completed.stdout
    assert payload["workflow"] == "agent_hospital_lite"
    assert payload["final_report"]["agent"] == "final_hospital_report_agent"


def test_agent_and_tool_packages_are_separate_public_boundaries() -> None:
    assert callable(AIConsultationTool)
    assert Path("app/agents").is_dir()
    assert Path("app/tools").is_dir()
    assert Path("app/policies/clinical_policy.py").is_file()
    assert Path("app/tools/patient_history_lookup.py").is_file()
    assert not Path("app/agents/history.py").exists()
    assert Path("app/workflows").is_dir()
    assert not Path("app/hospital").exists()
    assert not Path("app/consultation").exists()


def test_clinical_rules_live_in_policy_boundary_not_agent_package() -> None:
    rules = Path("app/agents/rules.py").read_text(encoding="utf-8")

    assert "config/clinical-policy.json" not in rules
    assert "URGENT_TERMS = {" not in rules
    assert "def _is_negated_clinical_mention" not in rules
    assert "from app.policies.clinical_policy import" in rules


def assert_path_contains_in_order(path: list[str], expected: list[str]) -> None:
    cursor = 0
    for agent_name in path:
        if cursor < len(expected) and agent_name == expected[cursor]:
            cursor += 1
    assert cursor == len(expected)
