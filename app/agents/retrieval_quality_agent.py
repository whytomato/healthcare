from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class RetrievalQualityAgent(Agent):
    name = "retrieval_quality_agent"
    required_inputs = ("medical_knowledge_agent",)

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        if not knowledge_result or knowledge_result.status != "ready":
            return self.needs_data("Retrieval quality requires ready medical knowledge results.")

        documents = knowledge_result.data.get("documents", [])
        if not documents:
            evidence_state = "evidence_missing"
            summary = "No retrieved disease-symptom evidence was available for this case."
            confidence = 0.0
        else:
            top_score = max(float(item.get("retrieval_score", 0.0)) for item in documents)
            evidence_state = "evidence_sufficient" if top_score >= 1.0 else "evidence_weak"
            summary = "Retrieved disease-symptom evidence quality was assessed."
            confidence = 0.8 if evidence_state == "evidence_sufficient" else 0.5

        return self.ready(
            summary=summary,
            data={
                "evidence_state": evidence_state,
                "retrieved_document_count": len(documents),
                "used_previous_agents": ["medical_knowledge_agent"],
                "handoff_to": ["differential_diagnosis_agent", "uncertainty_assessment_agent"],
            },
            confidence=confidence,
        )
