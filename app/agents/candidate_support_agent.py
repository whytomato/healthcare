from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class CandidateSupportAgent(Agent):
    name = "candidate_support_agent"
    required_inputs = ("medical_knowledge_agent", "differential_diagnosis_agent")

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")
        retrieval_quality_result = self.previous_result(previous, "retrieval_quality_agent")
        if not knowledge_result or not differential_result:
            return self.needs_data("Candidate support requires evidence and candidate outputs.")

        if knowledge_result.status != "ready" or differential_result.status != "ready":
            return self.needs_data("Candidate support requires ready evidence and candidate outputs.")

        evidence_state = (
            retrieval_quality_result.data.get("evidence_state")
            if retrieval_quality_result and retrieval_quality_result.status == "ready"
            else "not_assessed"
        )
        rag_diseases = [
            str(document.get("disease", "")).strip().lower()
            for document in knowledge_result.data.get("documents", [])
            if str(document.get("disease", "")).strip()
        ]
        llm_output = str(differential_result.data.get("model_output", "")).lower()
        matched_diseases = [disease for disease in rag_diseases if disease in llm_output]

        if not llm_output.strip():
            support_state = "unknown"
        elif matched_diseases:
            support_state = "supported"
        elif evidence_state == "evidence_missing":
            support_state = "unknown"
        else:
            support_state = "unsupported"

        return self.ready(
            summary="Candidate support was checked against retrieved disease-symptom evidence.",
            data={
                "candidate_support_state": support_state,
                "evidence_state": evidence_state,
                "rag_diseases": sorted(set(rag_diseases)),
                "matched_diseases": sorted(set(matched_diseases)),
                "used_previous_agents": [
                    "medical_knowledge_agent",
                    "retrieval_quality_agent",
                    "differential_diagnosis_agent",
                ],
                "handoff_to": [
                    "rag_llm_consistency_agent",
                    "uncertainty_assessment_agent",
                    "report_agent",
                ],
            },
            confidence=0.7 if support_state != "unknown" else 0.3,
        )
