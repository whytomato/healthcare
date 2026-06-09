from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class RagLlmConsistencyAgent(Agent):
    name = "rag_llm_consistency_agent"
    required_inputs = ("medical_knowledge_agent", "differential_diagnosis_agent")

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")
        if not knowledge_result or not differential_result:
            return self.needs_data("RAG-LLM consistency requires evidence and candidate outputs.")

        if knowledge_result.status != "ready" or differential_result.status != "ready":
            return self.needs_data("RAG-LLM consistency requires ready evidence and candidate outputs.")

        rag_diseases = [
            str(document.get("disease", "")).strip().lower()
            for document in knowledge_result.data.get("documents", [])
            if str(document.get("disease", "")).strip()
        ]
        llm_output = str(differential_result.data.get("model_output", "")).lower()

        if not rag_diseases or not llm_output.strip():
            consistency_state = "not_comparable"
            matched_diseases: list[str] = []
        else:
            matched_diseases = [disease for disease in rag_diseases if disease in llm_output]
            if not matched_diseases:
                consistency_state = "conflicting"
            elif len(matched_diseases) == len(set(rag_diseases)):
                consistency_state = "consistent"
            else:
                consistency_state = "partially_consistent"

        return self.ready(
            summary="RAG evidence and LLM candidate output were compared with rule-based text matching.",
            data={
                "consistency_state": consistency_state,
                "rag_diseases": sorted(set(rag_diseases)),
                "matched_diseases": sorted(set(matched_diseases)),
                "used_previous_agents": [
                    "medical_knowledge_agent",
                    "differential_diagnosis_agent",
                ],
                "handoff_to": ["uncertainty_assessment_agent", "report_agent"],
            },
            confidence=0.7 if consistency_state != "not_comparable" else 0.3,
        )
