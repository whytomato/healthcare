from app.orchestrator import Orchestrator


def test_symptom_query_flow_reports_missing_real_services(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_BASE", "")
    result = Orchestrator().run(case_text="real symptom text", patient_id="p001")

    assert result["patient_id"] == "p001"
    assert [item["agent"] for item in result["results"]] == [
        "symptom_extraction_agent",
        "medical_knowledge_agent",
        "differential_diagnosis_agent",
        "evidence_review_agent",
        "safety_check_agent",
        "report_agent",
    ]
    assert result["results"][0]["status"] == "ready"
    assert result["results"][1]["status"] == "needs_data"
    assert result["results"][2]["status"] == "needs_data"
    assert result["results"][3]["status"] == "needs_data"
    assert result["results"][4]["status"] == "ready"
    assert result["results"][5]["status"] == "needs_data"
    assert result["results"][1]["data"]["used_previous_agents"] == ["symptom_extraction_agent"]
    assert "symptom_extraction_agent" in result["results"][2]["data"].get("used_previous_agents", [])
    assert "DifferentialDiagnosisAgent" in result["results"][3]["summary"]
    assert "symptom_extraction_agent" in result["results"][4]["data"].get("used_previous_agents", [])
    assert "MEDICAL_KNOWLEDGE_BASE" in result["results"][1]["required_inputs"]
    assert "LLM_API_KEY" in result["results"][2]["required_inputs"]
    assert result["results"][5]["data"]["agent_handoffs"]


def test_symptom_query_requires_case_text() -> None:
    result = Orchestrator().run(case_text="")

    first_result = result["results"][0]
    assert first_result["agent"] == "symptom_extraction_agent"
    assert first_result["status"] == "needs_data"
    assert "case_text" in first_result["required_inputs"]
