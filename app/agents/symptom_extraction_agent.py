from __future__ import annotations

import re

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class SymptomExtractionAgent(Agent):
    name = "symptom_extraction_agent"
    required_inputs = ("case_text",)

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        text = context.case_text.strip()
        if not text:
            return self.needs_data("Symptom extraction requires case_text.")

        candidates = [item.strip() for item in re.split(r"[,，;；、。\n\r]+", text) if item.strip()]
        retrieval_query = " ".join(candidates)
        return self.ready(
            summary="Input symptoms were normalized from the doctor's text.",
            findings=candidates,
            data={
                "raw_text": text,
                "symptom_candidates": candidates,
                "retrieval_query": retrieval_query,
                "handoff_to": [
                    "medical_knowledge_agent",
                    "differential_diagnosis_agent",
                    "safety_check_agent",
                ],
                "extraction_method": "punctuation_split_no_medical_inference",
            },
            confidence=0.6,
        )
