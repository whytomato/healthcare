from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.llm_client import LlmResult
from app.mock_scenario_generator import generate_mock_scenario


class FileBackedScenarioLlmClient:
    def __init__(self, response_file: Path) -> None:
        self.response_file = response_file

    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        return LlmResult(
            status="ready",
            content=self.response_file.read_text(encoding="utf-8"),
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a healthcare uncertainty scenario with an LLM or a mock response file."
    )
    parser.add_argument("--uncertainty-type")
    parser.add_argument(
        "--uncertainty-types",
        help="Comma-separated uncertainty types used for batch generation.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Total number of scenarios to generate.",
    )
    parser.add_argument("--output", required=True, help="Path to scenario JSON array to write.")
    parser.add_argument(
        "--mock-response-file",
        help="Use a local JSON object as the LLM response instead of calling a real LLM.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the output scenario file instead of appending.",
    )
    args = parser.parse_args()
    uncertainty_types = _uncertainty_types_from_args(args)
    if args.count < 1:
        parser.error("--count must be >= 1")

    client = (
        FileBackedScenarioLlmClient(Path(args.mock_response_file))
        if args.mock_response_file
        else None
    )
    scenarios = []
    for index in range(args.count):
        uncertainty_type = uncertainty_types[index % len(uncertainty_types)]
        scenario = generate_mock_scenario(
            uncertainty_type=uncertainty_type,
            output_path=Path(args.output),
            client=client,
            replace=args.replace and index == 0,
        )
        if args.count > 1:
            scenario["name"] = f"{scenario['name']}_{index + 1}"
            _rewrite_generated_name(Path(args.output), old_name=scenario["name"].rsplit("_", 1)[0], new_name=scenario["name"])
        scenarios.append(scenario)

    payload = scenarios[0] if args.count == 1 else {
        "generated_count": len(scenarios),
        "uncertainty_types": uncertainty_types,
        "scenarios": scenarios,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _uncertainty_types_from_args(args: argparse.Namespace) -> list[str]:
    if args.uncertainty_types:
        return [
            item.strip()
            for item in args.uncertainty_types.split(",")
            if item.strip()
        ]
    if args.uncertainty_type:
        return [args.uncertainty_type]
    raise SystemExit("--uncertainty-type or --uncertainty-types is required")


def _rewrite_generated_name(path: Path, old_name: str, new_name: str) -> None:
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    for scenario in reversed(scenarios):
        if scenario.get("name") == old_name:
            scenario["name"] = new_name
            break
    path.write_text(
        json.dumps(scenarios, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
