from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_RECORD_BASE_URL = "http://localhost:8083"


class PatientHistoryLookupTool:
    """Internal tool used by role agents to retrieve longitudinal patient context."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("CLINICAL_RECORD_BASE_URL", DEFAULT_RECORD_BASE_URL)).rstrip("/")
        self._cache: dict[str, dict[str, Any]] = {}

    def run(self, patient_id: str | None) -> dict[str, Any]:
        if not patient_id:
            return {
                "tool": "patient_history_lookup",
                "status": "needs_data",
                "patientId": None,
                "summary": empty_patient_history(None),
                "message": "patient_id is required for patient history lookup.",
            }
        if patient_id in self._cache:
            return self._cache[patient_id]

        url = f"{self.base_url}/api/records/patients/{quote(patient_id, safe='')}/history"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=3) as response:
                summary = json.loads(response.read().decode("utf-8"))
            result = {
                "tool": "patient_history_lookup",
                "status": "ready",
                "patientId": patient_id,
                "summary": summary,
            }
            self._cache[patient_id] = result
            return result
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            result = {
                "tool": "patient_history_lookup",
                "status": "unavailable",
                "patientId": patient_id,
                "summary": empty_patient_history(patient_id),
                "message": str(exc),
            }
            self._cache[patient_id] = result
            return result


def empty_patient_history(patient_id: str | None) -> dict[str, Any]:
    return {
        "patientId": patient_id,
        "recentEncounters": [],
        "knownConditions": [],
        "allergies": [],
        "currentMedications": [],
        "previousDispositions": [],
        "lastFinalReports": [],
    }
