from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict

from app.agents.coordinator import AgentCoordinator
from app.schemas.message import AgentResult


class Orchestrator:
    """Top-level service used by FastAPI, scripts, and tests."""

    def __init__(self, coordinator: AgentCoordinator | None = None) -> None:
        self.coordinator = coordinator or AgentCoordinator()

    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        question: str = "What diseases or conditions should be considered for these symptoms?",
        language: str = "zh-CN",
        progress_callback: Callable[[str, AgentResult | None], None] | None = None,
    ) -> dict:
        results = self.coordinator.run_case(
            case_text=case_text,
            patient_id=patient_id,
            doctor_id=doctor_id,
            question=question,
            language=language,
            progress_callback=progress_callback,
        )
        return {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "question": question,
            "language": language,
            "results": [asdict(result) for result in results],
        }
