import json
import subprocess
import sys
from pathlib import Path


def test_run_uncertainty_scenario_script_outputs_expected_uncertainties() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            "tests/scenarios/healthcare_uncertainty_scenarios.json",
            "--scenario",
            "rag_llm_conflict",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["scenario"] == "rag_llm_conflict"
    assert {"agent_conflict", "unsupported_candidate"}.issubset(
        set(payload["uncertainty_types"])
    )


def test_run_uncertainty_scenario_script_can_summarize_all_scenarios() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            "tests/scenarios/healthcare_uncertainty_scenarios.json",
            "--all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["total_scenarios"] == 3
    assert {"missing_evidence", "agent_conflict", "unsupported_candidate"}.issubset(
        set(payload["covered_uncertainty_types"])
    )
    assert {item["scenario"] for item in payload["scenarios"]} == {
        "missing_evidence_skips_candidate_reasoning",
        "rag_llm_conflict",
        "weak_evidence_unsupported_candidate_demo",
    }


def test_run_uncertainty_scenario_script_rejects_all_with_output() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            "tests/scenarios/healthcare_uncertainty_scenarios.json",
            "--all",
            "--output",
            "outputs/uncertainty_scenario_summary.test.json",
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "--output writes a single full workflow result" in completed.stderr


def test_run_uncertainty_scenario_script_writes_all_summary_output() -> None:
    output = Path("outputs/uncertainty_scenario_summary.test.json")

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            "tests/scenarios/healthcare_uncertainty_scenarios.json",
            "--all",
            "--summary-output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_payload = json.loads(completed.stdout)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert file_payload == stdout_payload
    assert file_payload["total_scenarios"] == 3


def test_generate_mock_scenario_script_saves_executable_scenario() -> None:
    output = Path("tests/scenarios/cli_generated_healthcare_uncertainty_scenarios.test.json")

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/generate_mock_scenario.py",
            "--uncertainty-type",
            "agent_conflict",
            "--output",
            str(output),
            "--mock-response-file",
            "tests/scenarios/mock_llm_agent_conflict_response.json",
            "--replace",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["name"] == "cli_generated_rag_llm_conflict"
    assert output.exists()

    run_completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            str(output),
            "--scenario",
            "cli_generated_rag_llm_conflict",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    run_payload = json.loads(run_completed.stdout)
    assert set(payload["expected_uncertainties"]).issubset(
        set(run_payload["uncertainty_types"])
    )


def test_generate_mock_scenario_script_can_generate_many_scenarios() -> None:
    output = Path("tests/scenarios/cli_generated_many_uncertainty_scenarios.test.json")

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/generate_mock_scenario.py",
            "--uncertainty-types",
            "agent_conflict,unsupported_candidate",
            "--count",
            "3",
            "--output",
            str(output),
            "--mock-response-file",
            "tests/scenarios/mock_llm_agent_conflict_response.json",
            "--replace",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["generated_count"] == 3
    assert len(payload["scenarios"]) == 3
    assert output.exists()

    run_completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_uncertainty_scenario.py",
            "--scenarios",
            str(output),
            "--all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    run_payload = json.loads(run_completed.stdout)
    assert run_payload["total_scenarios"] == 3
