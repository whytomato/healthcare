from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.uncertainty_scenario_runner import run_uncertainty_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a healthcare uncertainty scenario.")
    parser.add_argument("--scenarios", required=True, help="Path to scenario JSON array.")
    parser.add_argument("--scenario", help="Scenario name in the scenario file.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios in the scenario file and print a coverage summary.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the full workflow result JSON.",
    )
    parser.add_argument(
        "--summary-output",
        help="Optional path to write the --all coverage summary JSON.",
    )
    args = parser.parse_args()
    scenario_path = Path(args.scenarios)

    if args.all and args.output:
        parser.error("--output writes a single full workflow result; use it with --scenario")
    if args.summary_output and not args.all:
        parser.error("--summary-output writes an --all coverage summary; use it with --all")

    if args.all:
        summary = _run_all(scenario_path)
        if args.summary_output:
            summary_output_path = Path(args.summary_output)
            summary_output_path.parent.mkdir(parents=True, exist_ok=True)
            summary_output_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not args.scenario:
        parser.error("--scenario is required unless --all is used")

    result = run_uncertainty_scenario(scenario_path, args.scenario)
    summary = _summary_for(args.scenario, result)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _summary_for(scenario_name: str, result: dict[str, Any]) -> dict[str, Any]:
    uncertainty_result = next(
        item for item in result["results"] if item["agent"] == "uncertainty_assessment_agent"
    )
    uncertainties = uncertainty_result["data"]["uncertainties"]
    return {
        "scenario": scenario_name,
        "uncertainty_types": sorted({item["type"] for item in uncertainties}),
        "uncertainties": uncertainties,
        "agent_statuses": {
            item["agent"]: item["status"]
            for item in result["results"]
        },
    }


def _run_all(scenario_path: Path) -> dict[str, Any]:
    scenarios = json.loads(scenario_path.read_text(encoding="utf-8"))
    summaries = []
    covered: set[str] = set()
    for scenario in scenarios:
        scenario_name = scenario["name"]
        result = run_uncertainty_scenario(scenario_path, scenario_name)
        summary = _summary_for(scenario_name, result)
        summaries.append(summary)
        covered.update(summary["uncertainty_types"])
    return {
        "scenario_file": str(scenario_path),
        "total_scenarios": len(summaries),
        "covered_uncertainty_types": sorted(covered),
        "scenarios": summaries,
    }


if __name__ == "__main__":
    raise SystemExit(main())
