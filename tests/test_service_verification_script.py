from __future__ import annotations

from pathlib import Path


def test_verify_services_script_checks_all_health_endpoints_and_demo_chain_prerequisites() -> None:
    script = Path("scripts/verify-healthcare-services.ps1")
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert 'EncounterBaseUrl = "http://localhost:8081"' in source
    assert 'TriageBaseUrl = "http://localhost:8082"' in source
    assert 'RecordBaseUrl = "http://localhost:8083"' in source
    assert 'CareBaseUrl = "http://localhost:8084"' in source
    assert "$EncounterBaseUrl/api/ai/health" in source
    assert "$TriageBaseUrl/api/triage/health" in source
    assert "$RecordBaseUrl/api/records/health" in source
    assert "$CareBaseUrl/health" in source
    assert "POST" in source
    assert "/api/triage/assess" in source
    assert "/api/care/coordination-plans" in source
    assert "Exit 1" in source
