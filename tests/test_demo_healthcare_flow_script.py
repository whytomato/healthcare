from __future__ import annotations

import importlib
from pathlib import Path


def test_demo_script_submits_encounter_and_polls_until_completed(monkeypatch) -> None:
    demo = importlib.import_module("scripts.demo_healthcare_flow")
    output_path = Path("outputs/demo_healthcare_flow.test.json")
    if output_path.exists():
        output_path.unlink()
    calls: list[tuple[str, str, dict | None]] = []
    writes: list[tuple[Path, dict]] = []
    responses = [
        {"taskId": "task-001", "status": "PUBLISHED"},
        {"taskId": "task-001", "status": "PUBLISHED"},
        {
            "taskId": "task-001",
            "status": "COMPLETED",
        },
    ]

    def fake_request_json(method: str, url: str, payload: dict | None = None) -> dict:
        calls.append((method, url, payload))
        return responses.pop(0)

    monkeypatch.setattr(demo, "request_json", fake_request_json)
    monkeypatch.setattr(demo.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(demo, "write_json", lambda path, payload: writes.append((path, payload)))

    result = demo.run_demo(
        base_url="http://localhost:8081",
        case_text="fever and cough",
        patient_id="p001",
        doctor_id="d001",
        language="zh-CN",
        timeout_seconds=5,
        interval_seconds=1,
        output_path=output_path,
        record_base_url=None,
    )

    try:
        assert result["status"] == "COMPLETED"
        assert calls[0] == (
            "POST",
            "http://localhost:8081/api/ai/symptom-query",
            {
                "caseText": "fever and cough",
                "question": "Run hospital consultation workflow",
                "patientId": "p001",
                "doctorId": "d001",
                "language": "zh-CN",
            },
        )
        assert calls[1][0] == "GET"
        assert calls[1][1] == "http://localhost:8081/api/ai/tasks/task-001"
        assert writes[0][0] == output_path
        assert writes[0][1]["status"] == "COMPLETED"
    finally:
        pass


def test_demo_script_documents_service_start_order() -> None:
    source = importlib.import_module("scripts.demo_healthcare_flow").__doc__ or ""

    assert "encounter-service" in source
    assert "triage-service" in source
    assert "Python AI worker" in source
    assert "clinical-record-service" in source


def test_demo_script_exposes_named_manual_demo_cases() -> None:
    demo = importlib.import_module("scripts.demo_healthcare_flow")

    assert "emergency_multi_specialty" in [
        item["id"] for item in demo.demo_cases()
    ]
    assert demo.demo_case("standard_outpatient")["patientId"] == "p-outpatient-001"


def test_demo_script_can_verify_clinical_record_storage(monkeypatch) -> None:
    demo = importlib.import_module("scripts.demo_healthcare_flow")
    output_path = Path("outputs/demo_healthcare_flow.record.test.json")
    calls: list[tuple[str, str, dict | None, bool]] = []
    writes: list[tuple[Path, dict]] = []
    responses = [
        {"taskId": "task-002", "status": "PUBLISHED"},
        {
            "taskId": "task-002",
            "status": "COMPLETED",
        },
        None,
        {
            "taskId": "task-002",
            "status": "ready",
            "executedPath": ["intake_agent", "final_hospital_report_agent"],
            "rawResult": {
                "workflow": "agent_hospital_lite",
                "executed_path": ["intake_agent", "final_hospital_report_agent"],
            },
        },
    ]

    def fake_request_json(
        method: str,
        url: str,
        payload: dict | None = None,
        allow_error: bool = False,
    ) -> dict | None:
        calls.append((method, url, payload, allow_error))
        return responses.pop(0)

    monkeypatch.setattr(demo, "request_json", fake_request_json)
    monkeypatch.setattr(demo.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(demo, "write_json", lambda path, payload: writes.append((path, payload)))

    result = demo.run_demo(
        base_url="http://localhost:8081",
        case_text="fever and cough",
        patient_id="p001",
        doctor_id="d001",
        language="zh-CN",
        timeout_seconds=5,
        interval_seconds=1,
        output_path=output_path,
        record_base_url="http://localhost:8083",
        record_timeout_seconds=5,
    )

    assert result["status"] == "COMPLETED"
    assert result["clinicalRecord"]["taskId"] == "task-002"
    assert calls[2] == (
        "GET",
        "http://localhost:8083/api/records/task-002",
        None,
        True,
    )
    assert writes[0][1]["clinicalRecord"]["status"] == "ready"
