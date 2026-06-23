from __future__ import annotations

from pathlib import Path


def test_start_script_runs_core_and_er_services_with_pid_tracking() -> None:
    script = Path("scripts/start-healthcare-services.ps1")
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "start-healthcare-services" in source
    assert "healthcare-services.pids.json" in source
    assert "outputs\\service-logs" in source
    assert "Start-Process" in source
    assert "-WindowStyle Hidden" in source
    assert "-PassThru" in source
    assert "ConvertTo-Json" in source
    assert "verify-healthcare-services.ps1" in source
    assert "-CoreOnly:$CoreOnly" in source
    assert '@("-pl", $service.Module, "spring-boot:run")' in source
    assert '$arguments -join' in source
    assert "CoreOnly" in source
    for module, port in [
        ("encounter-service", "8081"),
        ("triage-service", "8082"),
        ("clinical-record-service", "8083"),
        ("care-coordination-service", "8084"),
        ("practitioner-service", "8085"),
        ("resource-service", "8086"),
        ("scheduling-service", "8087"),
        ("emergency-encounter-service", "8088"),
    ]:
        assert module in source
        assert port in source


def test_stop_script_stops_pid_file_services_without_touching_source() -> None:
    script = Path("scripts/stop-healthcare-services.ps1")
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "healthcare-services.pids.json" in source
    assert "ConvertFrom-Json" in source
    assert "Get-Process" in source
    assert "Stop-Process" in source
    assert "Remove-Item" in source
    assert "processId" in source
