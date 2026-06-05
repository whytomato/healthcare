from __future__ import annotations

from app.agents.base import Agent
from app.llm_client import LlmClient
from app.schemas.message import AgentContext, AgentResult


class EvidenceReviewAgent(Agent):
    name = "evidence_review_agent"
    required_inputs = ("case_text", "LLM_API_KEY")

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")

        if not differential_result or differential_result.status != "ready":
            return self.needs_data("Evidence review requires DifferentialDiagnosisAgent output.")

        retrieved_documents = (
            knowledge_result.data.get("documents", [])
            if knowledge_result and knowledge_result.status == "ready"
            else []
        )
        differential_output = differential_result.data.get("model_output", "")
        grounding_note = (
            "Use the retrieved documents as evidence and clearly mark unsupported claims."
            if retrieved_documents
            else "No retrieved documents are available. Clearly state that evidence support is missing."
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a clinical evidence review agent. Review the differential diagnosis candidates "
                    "against retrieved knowledge. For each candidate, list supporting evidence, opposing or "
                    "missing evidence, and what should be checked next. Respond in Chinese."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Case text: {context.case_text}\n"
                    f"Differential diagnosis candidates: {differential_output}\n"
                    f"Grounding instruction: {grounding_note}\n"
                    f"Retrieved medical knowledge: {retrieved_documents}"
                ),
            },
        ]
        result = self.client.chat(messages)
        if result.status != "ready":
            missing = self.missing_tool(
                result.message,
                result.required_config or ["LLM_API_KEY"],
            )
            missing.data.update(
                {
                    "used_previous_agents": [
                        "medical_knowledge_agent",
                        "differential_diagnosis_agent",
                    ],
                    "retrieved_document_count": len(retrieved_documents),
                }
            )
            return missing

        return self.ready(
            summary="Evidence review completed using retrieved knowledge and candidate diagnoses.",
            findings=[result.content],
            data={
                "model_output": result.content,
                "used_previous_agents": [
                    "medical_knowledge_agent",
                    "differential_diagnosis_agent",
                ],
                "retrieved_document_count": len(retrieved_documents),
                "api_call_role": "evidence_review",
                "handoff_to": ["safety_check_agent", "report_agent"],
            },
            confidence=0.7,
        )
