from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.orchestrator import Orchestrator
from app.schemas.message import AgentResult


orchestrator = Orchestrator()


try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None


if FastAPI is not None:
    api = FastAPI(title="Healthcare Multi-Agent API")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/analyze")
    def analyze(payload: dict[str, str]) -> dict:
        case_text = payload.get("case_text", "")
        patient_id = payload.get("patient_id")
        doctor_id = payload.get("doctor_id")
        question = payload.get(
            "question",
            "What diseases or conditions should be considered for these symptoms?",
        )
        language = payload.get("language", "zh-CN")
        return orchestrator.run(
            case_text=case_text,
            patient_id=patient_id,
            doctor_id=doctor_id,
            question=question,
            language=language,
        )
else:
    api = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the healthcare multi-agent flow.")
    parser.add_argument("--case-text", required=True, help="Real symptom or case text to pass through agents.")
    parser.add_argument(
        "--question",
        default="What diseases or conditions should be considered for these symptoms?",
        help="Doctor's question for the AI workflow.",
    )
    parser.add_argument("--patient-id", default=None, help="Optional real patient identifier.")
    parser.add_argument("--doctor-id", default=None, help="Optional real doctor identifier.")
    parser.add_argument("--language", default="zh-CN", help="Preferred response language.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide per-agent progress logs.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the full JSON result to the console.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the full JSON result. Defaults to outputs/run_<timestamp>.json.",
    )
    args = parser.parse_args()

    result = orchestrator.run(
        case_text=args.case_text,
        patient_id=args.patient_id,
        doctor_id=args.doctor_id,
        question=args.question,
        language=args.language,
        progress_callback=None if args.quiet else print_agent_progress,
    )
    output_path = write_result_json(result, args.output)
    print_summary(result, output_path)
    if args.print_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


def write_result_json(result: dict, output: str | None) -> Path:
    if output:
        path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("outputs") / f"run_{timestamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_summary(result: dict, output_path: Path) -> None:
    print("")
    print("[summary]")
    for item in result.get("results", []):
        print(f"- {item.get('agent')}: {item.get('status')}")
    print(f"[output] full JSON written to {output_path}")


def print_agent_progress(agent_name: str, result: AgentResult | None) -> None:
    if result is None:
        print(f"[agent:start] {agent_name}")
        return

    print(f"[agent:done]  {agent_name} -> {result.status}")
    print(f"              {result.summary}")
    if result.required_inputs:
        print(f"              required_inputs: {', '.join(result.required_inputs)}")


if __name__ == "__main__":
    main()
