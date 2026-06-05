from __future__ import annotations

from app.agents.base import Agent
from app.llm_client import LlmClient
from app.schemas.message import AgentContext, AgentResult


class DifferentialDiagnosisAgent(Agent):
    name = "differential_diagnosis_agent"
    required_inputs = ("case_text", "LLM_API_KEY")

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        if not context.case_text.strip():
            return self.needs_data("Differential diagnosis requires case_text.")

        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        if not symptom_result or symptom_result.status != "ready":
            return self.needs_data("Differential diagnosis requires SymptomExtractionAgent output.")

        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        symptom_candidates = symptom_result.data.get("symptom_candidates", [])
        retrieved_documents = (
            knowledge_result.data.get("documents", [])
            if knowledge_result and knowledge_result.status == "ready"
            else []
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a clinical differential diagnosis agent for doctors. "
                    "Generate candidate diseases or conditions only, not a final diagnosis. "
                    "For each candidate, state why it should be considered, what information is missing, "
                    "and whether the candidate is high, medium, or low concern. Respond in Chinese."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Doctor question: {context.question}\n"
                    f"Case text: {context.case_text}\n"
                    f"Normalized symptoms: {symptom_candidates}\n"
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
                        "symptom_extraction_agent",
                        "medical_knowledge_agent",
                    ],
                    "symptom_candidates": symptom_candidates,
                    "retrieved_document_count": len(retrieved_documents),
                }
            )
            return missing

        return self.ready(
            summary="Differential diagnosis candidates were generated using the configured model.",
            findings=[result.content],
            data={
                "model_output": result.content,
                "used_previous_agents": [
                    "symptom_extraction_agent",
                    "medical_knowledge_agent",
                ],
                "symptom_candidates": symptom_candidates,
                "retrieved_document_count": len(retrieved_documents),
                "api_call_role": "differential_diagnosis",
                "handoff_to": ["evidence_review_agent", "safety_check_agent", "report_agent"],
            },
            confidence=0.7,
        )
