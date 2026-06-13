from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.llm_client import LlmResult
from app.tools import AIConsultationTool
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


def test_high_risk_patient_encounter_follows_emergency_branch() -> None:
    result = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    ).run(
        case_text="67-year-old male with fever, productive cough, chest discomfort and confusion.",
        patient_id="p001",
        doctor_id="d001",
    )

    assert result["executed_path"] == [
        "intake_agent",
        "appointment_agent",
        "triage_nurse_agent",
        "emergency_physician_agent",
        "general_practitioner_agent",
        "specialist_router_agent",
        "respiratory_specialist_agent",
        "cardiology_specialist_agent",
        "infectious_disease_specialist_agent",
        "neurology_specialist_agent",
        "lab_advisor_agent",
        "pharmacy_safety_agent",
        "disposition_coordinator_agent",
        "final_hospital_report_agent",
    ]
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
    assert Path("app/workflows").is_dir()
    assert not Path("app/hospital").exists()
    assert not Path("app/consultation").exists()
