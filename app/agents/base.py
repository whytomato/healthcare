from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.message import AgentContext, AgentResult


STATUS_READY = "ready"
STATUS_NEEDS_DATA = "needs_data"
STATUS_SKIPPED = "skipped"


class Agent(ABC):
    name: str
    required_inputs: tuple[str, ...] = ()

    @abstractmethod
    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        """Run one agent against the case context and prior agent outputs."""

    def previous_result(
        self,
        previous: list[AgentResult],
        agent_name: str,
    ) -> AgentResult | None:
        return next((result for result in previous if result.agent == agent_name), None)

    def needs_data(self, summary: str) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=STATUS_NEEDS_DATA,
            summary=summary,
            required_inputs=list(self.required_inputs),
            confidence=0.0,
        )

    def missing_tool(self, summary: str, required_inputs: list[str]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=STATUS_NEEDS_DATA,
            summary=summary,
            required_inputs=required_inputs,
            confidence=0.0,
        )

    def skipped(self, summary: str, data: dict | None = None) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=STATUS_SKIPPED,
            summary=summary,
            data=data or {},
            confidence=0.0,
        )

    def ready(
        self,
        summary: str,
        findings: list[str] | None = None,
        recommendations: list[str] | None = None,
        data: dict | None = None,
        confidence: float = 1.0,
    ) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=STATUS_READY,
            summary=summary,
            findings=findings or [],
            recommendations=recommendations or [],
            data=data or {},
            confidence=confidence,
        )
