from pathlib import Path

from app.llm_client import LlmResult
from app.scenario import generate_mock_scenario, run_uncertainty_scenario


class FakeScenarioLlmClient:
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        return LlmResult(
            status="ready",
            content="""
{
  "name": "llm_generated_rag_llm_conflict",
  "case_text": "fever and cough",
  "mock_rag_documents": [
    {
      "disease": "pneumonia",
      "retrieval_score": 2.0,
      "matched_query_terms": ["fever", "cough"]
    }
  ],
  "mock_llm_output": "heart failure should be considered",
  "expected_uncertainties": ["agent_conflict", "unsupported_candidate"]
}
""",
        )


def test_llm_generated_mock_data_is_saved_as_executable_scenario() -> None:
    scenario_path = Path("tests/scenarios/generated_healthcare_uncertainty_scenarios.test.json")
    scenario = generate_mock_scenario(
        client=FakeScenarioLlmClient(),
        uncertainty_type="agent_conflict",
        output_path=scenario_path,
        replace=True,
    )

    assert scenario["name"] == "llm_generated_rag_llm_conflict"
    assert scenario_path.exists()

    result = run_uncertainty_scenario(scenario_path, "llm_generated_rag_llm_conflict")
    uncertainty = next(
        item for item in result["results"] if item["agent"] == "uncertainty_assessment_agent"
    )
    uncertainty_types = {item["type"] for item in uncertainty["data"]["uncertainties"]}

    assert set(scenario["expected_uncertainties"]).issubset(uncertainty_types)
