from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_CARE_COORDINATION_BASE_URL = "http://localhost:8084"
DEFAULT_CARE_COORDINATION_TIMEOUT_SECONDS = 0.5


class CareCoordinationTool:
    name = "care_coordination"

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("CARE_COORDINATION_BASE_URL", DEFAULT_CARE_COORDINATION_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else _env_timeout(
                "CARE_COORDINATION_TIMEOUT_SECONDS",
                DEFAULT_CARE_COORDINATION_TIMEOUT_SECONDS,
            )
        )

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        doctor_id: str | None,
        disposition: str,
        triage_urgency: str,
        selected_specialties: list[str],
        monitoring_plan: list[str],
    ) -> dict[str, Any]:
        payload = {
            "taskId": task_id,
            "patientId": patient_id,
            "doctorId": doctor_id,
            "disposition": disposition,
            "triageUrgency": triage_urgency,
            "selectedSpecialties": selected_specialties,
            "monitoringPlan": monitoring_plan,
        }
        request = Request(
            f"{self.base_url}/api/care/coordination-plans",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                plan = json.loads(response.read().decode("utf-8"))
            return {
                "tool": self.name,
                "status": "ready",
                "summary": "Care coordination service returned a plan.",
                "payload": plan,
            }
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            return {
                "tool": self.name,
                "status": "unavailable",
                "summary": "Care coordination service is unavailable; using local fallback plan.",
                "payload": {
                    "taskId": task_id,
                    "patientId": patient_id,
                    "status": "unavailable",
                    "disposition": disposition,
                    "followUpActions": monitoring_plan,
                    "referralActions": [
                        f"Schedule {specialty.replace('_', ' ')} review."
                        for specialty in selected_specialties
                    ],
                    "admissionActions": (
                        ["Check emergency observation capacity."]
                        if triage_urgency == "high"
                        else ["No admission coordination required for outpatient pathway."]
                    ),
                    "humanReviewRequired": triage_urgency == "high"
                    or len(selected_specialties) >= 3,
                    "message": str(exc),
                },
            }


def _env_timeout(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default
