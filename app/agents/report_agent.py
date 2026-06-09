from __future__ import annotations

from app.agents.base import Agent
from app.llm_client import LlmClient
from app.schemas.message import AgentContext, AgentResult


class ReportAgent(Agent):
    name = "report_agent"
    required_inputs = ("case_text", "LLM_API_KEY")

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        blocking = [result for result in previous if result.status not in {"ready", "skipped"}]
        uncertainty_result = self.previous_result(previous, "uncertainty_assessment_agent")
        uncertainties = (
            uncertainty_result.data.get("uncertainties", [])
            if uncertainty_result and uncertainty_result.status == "ready"
            else []
        )
        agent_handoffs = [
            {
                "agent": result.agent,
                "used_previous_agents": result.data.get("used_previous_agents", []),
                "handoff_to": result.data.get("handoff_to", []),
            }
            for result in previous
        ]

        if blocking:
            required: list[str] = []
            for result in blocking:
                required.extend(item for item in result.required_inputs if item not in required)
            return AgentResult(
                agent=self.name,
                status="needs_data",
                summary="Final symptom query report cannot be completed until required services are configured.",
                required_inputs=required,
                data={
                    "completed_agents": [
                        result.agent for result in previous if result.status == "ready"
                    ],
                    "uncertainties": uncertainties,
                    "agent_handoffs": agent_handoffs,
                    "blocked_agents": [
                        {
                            "agent": result.agent,
                            "summary": result.summary,
                            "required_inputs": result.required_inputs,
                        }
                        for result in blocking
                    ],
                },
                confidence=0.0,
            )

        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        knowledge_result = self.previous_result(previous, "medical_knowledge_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")
        evidence_result = self.previous_result(previous, "evidence_review_agent")
        safety_result = self.previous_result(previous, "safety_check_agent")

        symptom_candidates = symptom_result.data.get("symptom_candidates", []) if symptom_result else []
        retrieved_documents = knowledge_result.data.get("documents", []) if knowledge_result else []
        differential_output = differential_result.data.get("model_output", "") if differential_result else ""
        evidence_output = evidence_result.data.get("model_output", "") if evidence_result else ""
        red_flags = safety_result.data.get("red_flags", []) if safety_result else []
        safety_recommendations = safety_result.recommendations if safety_result else []

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the final clinical report agent in a multi-agent decision support system. "
                    "Create a concise doctor-facing report. Do not make a final diagnosis. "
                    "Integrate symptoms, retrieved evidence, differential candidates, evidence review, "
                    "and safety red flags. Clearly separate: summary, differential considerations, "
                    "evidence basis, red flags, next questions/tests, and limitations. Respond in Chinese."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Doctor question: {context.question}\n"
                    f"Case text: {context.case_text}\n"
                    f"Normalized symptoms: {symptom_candidates}\n"
                    f"Retrieved documents: {retrieved_documents}\n"
                    f"DifferentialDiagnosisAgent output: {differential_output}\n"
                    f"EvidenceReviewAgent output: {evidence_output}\n"
                    f"Safety red flags: {red_flags}\n"
                    f"Safety recommendations: {safety_recommendations}\n"
                    f"Workflow uncertainties: {uncertainties}"
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
                    "used_previous_agents": [item.agent for item in previous],
                    "agent_handoffs": agent_handoffs,
                    "uncertainties": uncertainties,
                    "red_flags": red_flags,
                    "retrieved_document_count": len(retrieved_documents),
                }
            )
            return missing

        return self.ready(
            summary="Final symptom query report is ready for doctor review.",
            findings=[result.content],
            recommendations=safety_recommendations,
            data={
                "model_output": result.content,
                "used_previous_agents": [item.agent for item in previous],
                "agent_handoffs": agent_handoffs,
                "uncertainties": uncertainties,
                "red_flags": red_flags,
                "retrieved_document_count": len(retrieved_documents),
                "api_call_role": "final_report_synthesis",
                "safety_note": (
                    "AI output is clinical decision support for qualified doctors "
                    "and must not replace clinician judgment."
                ),
            },
            confidence=0.75,
        )
