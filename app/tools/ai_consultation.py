from __future__ import annotations

import re
from typing import Any, Protocol

from app.llm_client import LlmClient, LlmResult
from app.mcp_clients.rag_client import RagMcpClient


class ConsultationLlmClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        ...


class AIConsultationTool:
    """Internal tool used by role agents; not a top-level hospital agent."""

    def __init__(
        self,
        llm_client: ConsultationLlmClient | None = None,
        rag_client: RagMcpClient | None = None,
    ) -> None:
        self.llm_client = llm_client or LlmClient()
        self.rag_client = rag_client or RagMcpClient()

    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        language: str = "zh-CN",
    ) -> dict[str, Any]:
        symptoms = _extract_symptoms(case_text)
        retrieval_query = " ".join(symptoms)
        rag_result = self.rag_client.search_medical_knowledge(retrieval_query)
        documents = (
            rag_result.data.get("documents", [])
            if rag_result.status == "ready"
            else []
        )
        llm_result = self.llm_client.chat(
            _messages_for(
                case_text=case_text,
                symptoms=symptoms,
                documents=documents,
                language=language,
            )
        )
        llm_output = (
            llm_result.content
            if llm_result.status == "ready"
            else "AI consultation LLM output is unavailable; role agents should rely on structured workflow outputs and clinician review."
        )
        return {
            "workflow": "ai_consultation_tool",
            "status": "ready",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "symptoms": symptoms,
            "retrieval_query": retrieval_query,
            "retrieval_status": rag_result.status,
            "retrieved_documents": documents,
            "llm_status": llm_result.status,
            "llm_output": llm_output,
            "required_config": rag_result.required_config
            + (llm_result.required_config or []),
        }


def _extract_symptoms(case_text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,;，；。\n\r]+", case_text)
        if item.strip()
    ]


def _messages_for(
    case_text: str,
    symptoms: list[str],
    documents: list[dict[str, Any]],
    language: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an internal AI consultation tool used by hospital role agents. "
                "Summarize possible clinical considerations, evidence gaps, and useful next questions. "
                "Do not present yourself as a hospital role agent and do not make a final diagnosis."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Language: {language}\n"
                f"Case text: {case_text}\n"
                f"Extracted symptoms: {symptoms}\n"
                f"Retrieved knowledge: {documents}"
            ),
        },
    ]
