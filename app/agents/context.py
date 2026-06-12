from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HospitalContext:
    case_text: str
    patient_id: str | None = None
    doctor_id: str | None = None
    language: str = "zh-CN"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HospitalAgentResult:
    agent: str
    status: str
    summary: str
    role: str
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    decisions: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    handoff_to: list[str] = field(default_factory=list)
    confidence: float = 0.7
