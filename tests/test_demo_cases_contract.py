from __future__ import annotations

from app.demo_cases import demo_cases
from app.workflows.hospital import HospitalOrchestrator
from tests.test_hospital_orchestrator import FakeAIConsultationTool, FakeHospitalLlmClient


def test_demo_cases_cover_manual_paths_for_frontend_and_cli() -> None:
    cases = demo_cases()

    assert {
        "emergency_multi_specialty",
        "standard_outpatient",
        "low_risk_followup",
        "human_review",
        "service_fallback",
    }.issubset({case["id"] for case in cases})
    assert all(case["caseText"].strip() for case in cases)
    assert all(case["patientId"].strip() for case in cases)


def test_demo_cases_drive_distinct_agent_workflow_paths() -> None:
    cases = {case["id"]: case for case in demo_cases()}
    orchestrator = HospitalOrchestrator(
        llm_client=FakeHospitalLlmClient(),
        consultation_tool=FakeAIConsultationTool(),
    )

    outpatient = orchestrator.run(case_text=cases["standard_outpatient"]["caseText"])
    emergency = orchestrator.run(case_text=cases["emergency_multi_specialty"]["caseText"])
    human_review = orchestrator.run(case_text=cases["human_review"]["caseText"])

    assert "emergency_physician_agent" not in outpatient["executed_path"]
    assert "emergency_physician_agent" in emergency["executed_path"]
    assert len(emergency["selected_specialties"]) > len(outpatient["selected_specialties"])
    assert any(
        event["payload"].get("tool") == "human_review_request"
        and event["payload"].get("choice") == "selected"
        for event in human_review["handoff_timeline"]
        if event["event_type"] == "tool_invoked"
    )
