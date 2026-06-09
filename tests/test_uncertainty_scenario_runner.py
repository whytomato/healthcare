from pathlib import Path
import json

from app.scenario import run_uncertainty_scenario


SCENARIO_PATH = Path("tests/scenarios/healthcare_uncertainty_scenarios.json")


def test_missing_evidence_scenario_drives_expected_uncertainties() -> None:
    result = run_uncertainty_scenario(
        SCENARIO_PATH,
        "missing_evidence_skips_candidate_reasoning",
    )
    scenario = _scenario("missing_evidence_skips_candidate_reasoning")

    uncertainty = next(
        item for item in result["results"] if item["agent"] == "uncertainty_assessment_agent"
    )
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert set(scenario["expected_uncertainties"]).issubset(uncertainty_types)


def test_rag_llm_conflict_scenario_drives_expected_uncertainties() -> None:
    result = run_uncertainty_scenario(
        SCENARIO_PATH,
        "rag_llm_conflict",
    )
    scenario = _scenario("rag_llm_conflict")

    uncertainty = next(
        item for item in result["results"] if item["agent"] == "uncertainty_assessment_agent"
    )
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert set(scenario["expected_uncertainties"]).issubset(uncertainty_types)


def test_weak_evidence_unsupported_candidate_demo_drives_expected_uncertainties() -> None:
    result = run_uncertainty_scenario(
        SCENARIO_PATH,
        "weak_evidence_unsupported_candidate_demo",
    )
    scenario = _scenario("weak_evidence_unsupported_candidate_demo")

    uncertainty = next(
        item for item in result["results"] if item["agent"] == "uncertainty_assessment_agent"
    )
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert set(scenario["expected_uncertainties"]).issubset(uncertainty_types)


def _scenario(name: str) -> dict:
    scenarios = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    return next(item for item in scenarios if item["name"] == name)
