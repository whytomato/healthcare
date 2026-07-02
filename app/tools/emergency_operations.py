from __future__ import annotations

import json
import os
from time import sleep
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PRACTITIONER_BASE_URL = "http://localhost:8085"
DEFAULT_RESOURCE_BASE_URL = "http://localhost:8086"
DEFAULT_SCHEDULING_BASE_URL = "http://localhost:8087"
DEFAULT_EMERGENCY_ENCOUNTER_BASE_URL = "http://localhost:8088"
DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS = 2.0
DEFAULT_EMERGENCY_SERVICE_RETRIES = 2
DEFAULT_EMERGENCY_SERVICE_RETRY_DELAY_SECONDS = 0.2


class EmergencyEncounterTool:
    name = "emergency_encounter"

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("EMERGENCY_ENCOUNTER_BASE_URL", DEFAULT_EMERGENCY_ENCOUNTER_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or _env_timeout(
            "EMERGENCY_SERVICE_TIMEOUT_SECONDS",
            DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS,
        )

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        triage_urgency: str,
        red_flags: list[str],
    ) -> dict[str, Any]:
        payload = {
            "taskId": task_id,
            "patientId": patient_id,
            "triageUrgency": triage_urgency,
            "redFlags": red_flags,
        }
        fallback = {
            "taskId": task_id,
            "patientId": patient_id,
            "emergencyEncounterId": f"local-{task_id}",
            "status": "fallback_opened",
            "triageUrgency": triage_urgency,
            "redFlags": red_flags,
            "message": "Emergency encounter service unavailable; local encounter state opened.",
        }
        return _post_json_tool_result(
            tool=self.name,
            url=f"{self.base_url}/api/emergency/encounters",
            payload=payload,
            ready_summary="Emergency encounter service opened acute-care state.",
            fallback_payload=fallback,
            unavailable_summary="Emergency encounter service is unavailable; using local emergency encounter fallback.",
            timeout_seconds=self.timeout_seconds,
        )

    def update_readiness(
        self,
        task_id: str,
        emergency_encounter_id: str,
        resource_readiness_status: str,
        reserved_resources: list[str],
    ) -> dict[str, Any]:
        payload = {
            "taskId": task_id,
            "emergencyEncounterId": emergency_encounter_id,
            "resourceReadinessStatus": resource_readiness_status,
            "reservedResources": reserved_resources,
        }
        fallback = {
            "taskId": task_id,
            "emergencyEncounterId": emergency_encounter_id,
            "status": "fallback_readiness_updated",
            "resourceReadinessStatus": resource_readiness_status,
            "reservedResources": reserved_resources,
            "message": "Emergency encounter service unavailable; local readiness state updated.",
        }
        return _post_json_tool_result(
            tool="emergency_readiness_update",
            url=f"{self.base_url}/api/emergency/encounters/readiness",
            payload=payload,
            ready_summary="Emergency encounter service recorded resource readiness.",
            fallback_payload=fallback,
            unavailable_summary="Emergency encounter service is unavailable; using local readiness update fallback.",
            timeout_seconds=self.timeout_seconds,
        )


def readiness_status_from_tool_result(tool_result: dict[str, Any]) -> str:
    payload = tool_result.get("payload", {})
    if isinstance(payload, dict):
        return str(payload.get("readinessStatus") or payload.get("resourceReadinessStatus") or "ready")
    return "ready"


class PractitionerAssignmentTool:
    name = "practitioner_assignment"

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("PRACTITIONER_BASE_URL", DEFAULT_PRACTITIONER_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or _env_timeout(
            "EMERGENCY_SERVICE_TIMEOUT_SECONDS",
            DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS,
        )

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        urgency_level: str,
        required_specialties: list[str],
    ) -> dict[str, Any]:
        payload = {
            "taskId": task_id,
            "patientId": patient_id,
            "urgencyLevel": urgency_level,
            "requiredSpecialties": required_specialties,
        }
        fallback = {
            "taskId": task_id,
            "patientId": patient_id,
            "assignmentStatus": "fallback_assigned",
            "assignedPractitioners": [
                "emergency_physician_on_call",
                "charge_nurse",
                *[f"{specialty}_consultant" for specialty in required_specialties],
            ],
            "unavailableSpecialties": [],
            "message": "Practitioner service unavailable; local fallback assignment used.",
        }
        return _post_json_tool_result(
            tool=self.name,
            url=f"{self.base_url}/api/practitioners/emergency-assignments",
            payload=payload,
            ready_summary="Practitioner service assigned emergency staff.",
            fallback_payload=fallback,
            unavailable_summary="Practitioner service is unavailable; using local staff assignment fallback.",
            timeout_seconds=self.timeout_seconds,
        )


class ResourceReservationTool:
    name = "resource_reservation"

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("RESOURCE_BASE_URL", DEFAULT_RESOURCE_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or _env_timeout(
            "EMERGENCY_SERVICE_TIMEOUT_SECONDS",
            DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS,
        )

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        urgency_level: str,
        required_resources: list[str],
    ) -> dict[str, Any]:
        resources = required_resources or [
            "resuscitation_room",
            "emergency_observation_bed",
            "portable_monitor",
        ]
        payload = {
            "taskId": task_id,
            "patientId": patient_id,
            "urgencyLevel": urgency_level,
            "requiredResources": resources,
        }
        fallback = {
            "taskId": task_id,
            "patientId": patient_id,
            "readinessStatus": "fallback_ready",
            "reservedResources": resources,
            "unavailableResources": [],
            "message": "Resource service unavailable; local emergency readiness fallback used.",
        }
        return _post_json_tool_result(
            tool=self.name,
            url=f"{self.base_url}/api/resources/emergency-reservations",
            payload=payload,
            ready_summary="Resource service reserved emergency room readiness.",
            fallback_payload=fallback,
            unavailable_summary="Resource service is unavailable; using local emergency readiness fallback.",
            timeout_seconds=self.timeout_seconds,
        )


class ExamSchedulingTool:
    name = "exam_scheduling"

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("SCHEDULING_BASE_URL", DEFAULT_SCHEDULING_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or _env_timeout(
            "EMERGENCY_SERVICE_TIMEOUT_SECONDS",
            DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS,
        )

    def run(
        self,
        task_id: str,
        patient_id: str | None,
        ordering_agent: str,
        requested_exams: list[str],
        urgency_level: str,
    ) -> dict[str, Any]:
        payload = {
            "taskId": task_id,
            "patientId": patient_id,
            "orderingAgent": ordering_agent,
            "requestedExams": requested_exams,
            "urgencyLevel": urgency_level,
        }
        scheduled = [
            f"{'stat' if urgency_level == 'high' else 'routine'}:{exam}"
            for exam in requested_exams
        ]
        fallback = {
            "taskId": task_id,
            "patientId": patient_id,
            "orderingAgent": ordering_agent,
            "scheduleStatus": "fallback_scheduled",
            "scheduledExams": scheduled,
            "message": "Scheduling service unavailable; local emergency exam schedule fallback used.",
        }
        return _post_json_tool_result(
            tool=self.name,
            url=f"{self.base_url}/api/schedules/emergency-exams",
            payload=payload,
            ready_summary="Scheduling service created emergency exam schedule.",
            fallback_payload=fallback,
            unavailable_summary="Scheduling service is unavailable; using local emergency exam scheduling fallback.",
            timeout_seconds=self.timeout_seconds,
        )


def _post_json_tool_result(
    tool: str,
    url: str,
    payload: dict[str, Any],
    ready_summary: str,
    fallback_payload: dict[str, Any],
    unavailable_summary: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(DEFAULT_EMERGENCY_SERVICE_RETRIES + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                service_payload = json.loads(response.read().decode("utf-8"))
            return {
                "tool": tool,
                "status": "ready",
                "summary": ready_summary,
                "payload": service_payload,
            }
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if not _should_retry(exc, attempt):
                break
            sleep(DEFAULT_EMERGENCY_SERVICE_RETRY_DELAY_SECONDS)
    return {
        "tool": tool,
        "status": "unavailable",
        "summary": unavailable_summary,
        "payload": {**fallback_payload, "message": str(last_error)},
    }


def _should_retry(exc: Exception, attempt: int) -> bool:
    if attempt >= DEFAULT_EMERGENCY_SERVICE_RETRIES:
        return False
    if isinstance(exc, HTTPError):
        return 500 <= exc.code < 600
    return isinstance(exc, (TimeoutError, URLError))


def _env_timeout(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default
