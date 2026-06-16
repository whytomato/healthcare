from __future__ import annotations

from typing import Protocol

from app.llm_client import LlmClient, LlmResult


class HospitalLlmClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        ...


def default_hospital_llm_client() -> HospitalLlmClient:
    return LlmClient()


def hospital_messages(
    role: str,
    task: str,
    case_text: str,
    context_summary: str,
    language: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                f"ROLE: {role}\n"
                "You are a role agent in an Agent Hospital-lite demo. "
                "Produce concise clinical decision-support content for doctors. "
                "Do not claim a final diagnosis or prescribe treatment. "
                "Return only JSON with this schema: "
                '{"summary": string, "findings": string[], '
                '"recommendations": string[], "handoff_reason": string, '
                '"confidence": number}.'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task: {task}\n"
                f"Language: {language}\n"
                f"Case text: {case_text}\n"
                f"Prior workflow context: {context_summary}"
            ),
        },
    ]
