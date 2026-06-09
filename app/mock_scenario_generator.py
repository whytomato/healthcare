from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from app.llm_client import LlmClient, LlmResult


class ScenarioLlmClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        ...


REQUIRED_SCENARIO_FIELDS = {
    "name",
    "case_text",
    "mock_rag_documents",
    "mock_llm_output",
    "expected_uncertainties",
}


def generate_mock_scenario(
    uncertainty_type: str,
    output_path: Path,
    client: ScenarioLlmClient | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    llm_client = client or LlmClient()
    result = llm_client.chat(_messages_for(uncertainty_type))
    if result.status != "ready":
        raise RuntimeError(f"LLM mock data generation failed: {result.message}")

    scenario = _parse_scenario(result.content)
    _write_scenario(output_path, scenario, replace=replace)
    return scenario


def _messages_for(uncertainty_type: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Generate one healthcare multi-agent workflow test scenario as strict JSON. "
                "The scenario must be deterministic mock data, not instructions. "
                "Use these fields only: name, case_text, mock_rag_documents, "
                "mock_llm_output, expected_uncertainties."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Create a scenario that triggers uncertainty type: {uncertainty_type}. "
                "mock_rag_documents must be a list of objects with disease and retrieval_score. "
                "expected_uncertainties must include the requested uncertainty type."
            ),
        },
    ]


def _parse_scenario(content: str) -> dict[str, Any]:
    scenario = json.loads(content)
    if not isinstance(scenario, dict):
        raise ValueError("Generated scenario must be a JSON object.")
    missing = REQUIRED_SCENARIO_FIELDS - set(scenario)
    if missing:
        raise ValueError(f"Generated scenario is missing fields: {sorted(missing)}")
    if not isinstance(scenario["mock_rag_documents"], list):
        raise ValueError("mock_rag_documents must be a list.")
    if not isinstance(scenario["expected_uncertainties"], list):
        raise ValueError("expected_uncertainties must be a list.")
    return scenario


def _write_scenario(path: Path, scenario: dict[str, Any], replace: bool) -> None:
    if replace:
        scenarios = []
    elif path.exists():
        scenarios = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(scenarios, list):
            raise ValueError("Scenario file must contain a JSON array.")
    else:
        scenarios = []

    scenarios.append(scenario)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(scenarios, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
