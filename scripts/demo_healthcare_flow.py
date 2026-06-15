"""Run the healthcare demo flow after starting the backend services and Python AI worker.

Expected running components:
- encounter-service on http://localhost:8081
- triage-service consuming healthcare.encounter.created and publishing ai.symptom.query
- Python AI worker consuming ai.symptom.query and publishing ai.symptom.result
- clinical-record-service consuming ai.symptom.result and storing workflow records
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"COMPLETED", "FAILED", "NEEDS_DATA"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the healthcare microservice demo flow.")
    parser.add_argument("--base-url", default="http://localhost:8081", help="encounter-service base URL.")
    parser.add_argument(
        "--case-text",
        default="A 67-year-old male has fever, productive cough, chest discomfort and confusion.",
        help="Patient encounter text.",
    )
    parser.add_argument("--patient-id", default="p001")
    parser.add_argument("--doctor-id", default="d001")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="outputs/demo_healthcare_flow.json")
    parser.add_argument(
        "--record-base-url",
        default="http://localhost:8083",
        help="clinical-record-service base URL.",
    )
    parser.add_argument("--record-timeout-seconds", type=int, default=20)
    parser.add_argument(
        "--skip-record-check",
        action="store_true",
        help="Do not verify clinical-record-service storage.",
    )
    args = parser.parse_args()

    result = run_demo(
        base_url=args.base_url,
        case_text=args.case_text,
        patient_id=args.patient_id,
        doctor_id=args.doctor_id,
        language=args.language,
        timeout_seconds=args.timeout_seconds,
        interval_seconds=args.interval_seconds,
        output_path=Path(args.output),
        record_base_url=None if args.skip_record_check else args.record_base_url,
        record_timeout_seconds=args.record_timeout_seconds,
    )
    print_summary(result, Path(args.output))
    return 0


def run_demo(
    base_url: str,
    case_text: str,
    patient_id: str,
    doctor_id: str,
    language: str,
    timeout_seconds: int,
    interval_seconds: float,
    output_path: Path,
    record_base_url: str | None = None,
    record_timeout_seconds: int = 20,
) -> dict[str, Any]:
    payload = {
        "caseText": case_text,
        "question": "Run hospital consultation workflow",
        "patientId": patient_id,
        "doctorId": doctor_id,
        "language": language,
    }
    base = base_url.rstrip("/")
    created = request_json("POST", f"{base}/api/ai/symptom-query", payload)
    task_id = str(created["taskId"])
    print(f"[created] taskId={task_id} status={created.get('status')}")

    deadline = time.monotonic() + timeout_seconds
    last = created
    while time.monotonic() < deadline:
        current = request_json("GET", f"{base}/api/ai/tasks/{task_id}")
        last = current
        status = str(current.get("status", "UNKNOWN"))
        print(f"[poll] taskId={task_id} status={status}")
        if status in TERMINAL_STATUSES:
            final_payload = dict(current)
            if record_base_url:
                final_payload["clinicalRecord"] = wait_for_clinical_record(
                    record_base_url=record_base_url,
                    task_id=task_id,
                    timeout_seconds=record_timeout_seconds,
                    interval_seconds=interval_seconds,
                )
            write_json(output_path, final_payload)
            return final_payload
        time.sleep(interval_seconds)

    write_json(output_path, last)
    raise TimeoutError(f"Task {task_id} did not finish within {timeout_seconds} seconds.")


def wait_for_clinical_record(
    record_base_url: str,
    task_id: str,
    timeout_seconds: int,
    interval_seconds: float,
) -> dict[str, Any]:
    base = record_base_url.rstrip("/")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        record = request_json("GET", f"{base}/api/records/{task_id}", allow_error=True)
        if record is not None:
            print(f"[record] taskId={task_id} status={record.get('status')}")
            return record
        print(f"[record] waiting taskId={task_id}")
        time.sleep(interval_seconds)
    raise TimeoutError(
        f"Clinical record {task_id} was not available within {timeout_seconds} seconds."
    )


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    allow_error: bool = False,
) -> dict[str, Any] | None:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        if allow_error:
            return None
        raise SystemExit(f"HTTP request failed for {url}: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def print_summary(result: dict[str, Any], output_path: Path) -> None:
    workflow = (result.get("result") or {}).get("workflow") if isinstance(result.get("result"), dict) else None
    print(f"[done] taskId={result.get('taskId')} status={result.get('status')} workflow={workflow}")
    if "clinicalRecord" in result:
        record = result["clinicalRecord"]
        print(f"[record] taskId={record.get('taskId')} status={record.get('status')}")
    print(f"[output] {output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
