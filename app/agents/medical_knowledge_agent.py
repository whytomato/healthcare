from __future__ import annotations

from app.agents.base import Agent
from app.mcp_clients.rag_client import RagMcpClient
from app.schemas.message import AgentContext, AgentResult


class MedicalKnowledgeAgent(Agent):
    name = "medical_knowledge_agent"
    required_inputs = ("case_text", "knowledge_base")

    def __init__(self, client: RagMcpClient | None = None) -> None:
        self.client = client or RagMcpClient()

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        if not context.case_text.strip():
            return self.needs_data("Medical knowledge retrieval requires case_text.")

        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        if not symptom_result or symptom_result.status != "ready":
            return self.needs_data(
                "Medical knowledge retrieval requires normalized symptoms from SymptomExtractionAgent."
            )

        symptom_candidates = symptom_result.data.get("symptom_candidates", [])
        retrieval_query = symptom_result.data.get("retrieval_query") or context.case_text
        tool_result = self.client.search_medical_knowledge(str(retrieval_query))
        if tool_result.status != "ready":
            result = self.missing_tool(
                tool_result.message,
                [*self.required_inputs, *tool_result.required_config],
            )
            result.data.update(
                {
                    "used_previous_agents": ["symptom_extraction_agent"],
                    "retrieval_query": retrieval_query,
                    "symptom_candidates": symptom_candidates,
                }
            )
            return result

        documents = tool_result.data.get("documents", [])
        return self.ready(
            summary="Medical knowledge was retrieved from a configured knowledge base.",
            findings=[str(item) for item in documents],
            data={
                **tool_result.data,
                "used_previous_agents": ["symptom_extraction_agent"],
                "retrieval_query": retrieval_query,
                "symptom_candidates": symptom_candidates,
                "handoff_to": [
                    "differential_diagnosis_agent",
                    "evidence_review_agent",
                    "report_agent",
                ],
            },
            confidence=0.8,
        )
