from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.demo_cases import demo_case, demo_cases
from app.llm_client import LlmResult
from app.workflows.hospital import HospitalOrchestrator


try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None


class MockHospitalLlmClient:
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        role = messages[0]["content"].split("ROLE:", 1)[1].split("\n", 1)[0].strip()
        return LlmResult(
            status="ready",
            content=f"Mock LLM output for {role}.",
        )


class MockAIConsultationTool:
    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        language: str = "zh-CN",
    ) -> dict:
        symptoms = [
            symptom
            for symptom in ["fever", "cough", "chest discomfort", "confusion"]
            if symptom in case_text.lower()
        ]
        return {
            "workflow": "ai_consultation_tool",
            "status": "ready",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "symptoms": symptoms or ["case_text"],
            "llm_status": "ready",
            "llm_output": "Mock AI consultation tool output.",
            "retrieved_documents": [],
            "required_config": [],
        }


def build_orchestrator(mock_llm: bool = False) -> HospitalOrchestrator:
    if not mock_llm:
        return HospitalOrchestrator()
    return HospitalOrchestrator(
        llm_client=MockHospitalLlmClient(),
        consultation_tool=MockAIConsultationTool(),
    )


if FastAPI is not None:
    api = FastAPI(title="Healthcare Agent Hospital API")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/analyze")
    def analyze(payload: dict[str, str]) -> dict:
        return build_orchestrator().run(
            case_text=payload.get("case_text", ""),
            patient_id=payload.get("patient_id"),
            doctor_id=payload.get("doctor_id"),
            language=payload.get("language", "zh-CN"),
        )
else:
    api = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Agent Hospital-lite workflow.")
    parser.add_argument("--case-text", default=None, help="Patient case text.")
    parser.add_argument(
        "--demo-case",
        choices=[item["id"] for item in demo_cases()],
        default=None,
        help="Use a fixed manual demo case.",
    )
    parser.add_argument("--patient-id", default=None, help="Optional patient identifier.")
    parser.add_argument("--doctor-id", default=None, help="Optional doctor identifier.")
    parser.add_argument("--language", default="zh-CN", help="Preferred response language.")
    parser.add_argument("--mock-llm", action="store_true", help="Use deterministic mock outputs.")
    parser.add_argument("--print-json", action="store_true", help="Print the full JSON result.")
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the full JSON result. Defaults to outputs/run_<timestamp>.json.",
    )
    args = parser.parse_args()
    selected_demo = demo_case(args.demo_case) if args.demo_case else {}
    case_text = args.case_text or selected_demo.get("caseText")
    if not case_text:
        parser.error("--case-text is required unless --demo-case is provided.")

    result = build_orchestrator(mock_llm=args.mock_llm).run(
        case_text=str(case_text),
        patient_id=args.patient_id or selected_demo.get("patientId"),
        doctor_id=args.doctor_id or selected_demo.get("doctorId"),
        language=args.language or selected_demo.get("language", "zh-CN"),
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
    print(f"[workflow] {result.get('workflow')}")
    print(f"[agents] {len(result.get('agent_results', []))}")
    print(f"[specialties] {', '.join(result.get('selected_specialties', []))}")
    print(f"[output] full JSON written to {output_path}")


if __name__ == "__main__":
    main()
