from __future__ import annotations

import json
from typing import Any

from app.agents.context import HospitalAgentResult, HospitalContext
from app.agents.llm import HospitalLlmClient, hospital_messages


class HospitalAgent:
    name: str
    role: str

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        raise NotImplementedError

    def previous_result(
        self,
        previous: list[HospitalAgentResult],
        agent_name: str,
    ) -> HospitalAgentResult | None:
        return next((result for result in previous if result.agent == agent_name), None)

    def ready(
        self,
        summary: str,
        findings: list[str] | None = None,
        recommendations: list[str] | None = None,
        decisions: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        handoff_to: list[str] | None = None,
        confidence: float = 0.7,
    ) -> HospitalAgentResult:
        return HospitalAgentResult(
            agent=self.name,
            status="ready",
            summary=summary,
            role=self.role,
            findings=findings or [],
            recommendations=recommendations or [],
            decisions=decisions or {},
            data=data or {},
            handoff_to=handoff_to or [],
            confidence=confidence,
        )


class LlmBackedHospitalAgent(HospitalAgent):
    llm_task: str

    def __init__(self, llm_client: HospitalLlmClient | None = None) -> None:
        self.llm_client = llm_client

    def llm_finding(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> tuple[str | None, dict[str, Any]]:
        if self.llm_client is None:
            return None, {"llm_driven": False, "llm_status": "not_configured"}

        result = self.llm_client.chat(
            hospital_messages(
                role=self.role,
                task=self.llm_task,
                case_text=context.case_text,
                context_summary=_context_summary(previous),
                language=context.language,
            )
        )
        if result.status != "ready":
            return None, {
                "llm_driven": False,
                "llm_status": result.status,
                "llm_message": result.message,
            }
        structured = _structured_llm_output(result.content)
        if structured:
            return structured["summary"], {
                "llm_driven": True,
                "llm_status": "ready",
                "llm_structured": structured,
            }
        return result.content, {"llm_driven": True, "llm_status": "ready"}


def _context_summary(previous: list[HospitalAgentResult]) -> str:
    if not previous:
        return "No prior role outputs."
    return "\n".join(
        f"{result.agent}: {result.summary}; decisions={result.decisions}"
        for result in previous
    )


def _structured_llm_output(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(_json_payload(content))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None

    summary = parsed.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    return {
        "summary": summary,
        "findings": _string_list(parsed.get("findings")),
        "recommendations": _string_list(parsed.get("recommendations")),
        "handoff_reason": str(parsed.get("handoff_reason", "")),
        "confidence": _confidence(parsed.get("confidence")),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _confidence(value: Any) -> float | None:
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    return None


def _json_payload(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].strip().lower() in {"```json", "```"} and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text
