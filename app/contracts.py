from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SymptomQueryTask:
    task_id: str
    case_text: str
    question: str
    patient_id: str | None = None
    doctor_id: str | None = None
    language: str = "zh-CN"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SymptomQueryResult:
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error_message: str | None = None
