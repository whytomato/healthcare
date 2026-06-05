from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SymptomQuery:
    case_text: str
    question: str = "What diseases or conditions should be considered for these symptoms?"
    patient_id: str | None = None
    doctor_id: str | None = None
    language: str = "zh-CN"


@dataclass(frozen=True)
class AgentContext:
    case_text: str
    question: str = "What diseases or conditions should be considered for these symptoms?"
    patient_id: str | None = None
    doctor_id: str | None = None
    language: str = "zh-CN"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    agent: str
    status: str
    summary: str
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
