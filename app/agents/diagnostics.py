from __future__ import annotations

from app.agents.base import HospitalAgent
from app.agents.context import HospitalAgentResult, HospitalContext
from app.policies.workflow_state import selected_specialties
from app.tools import ClinicalToolRegistry


class DiagnosticOrderAgent(HospitalAgent):
    name = "diagnostic_order_agent"
    role = "diagnostic_orders"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        specialties = selected_specialties(previous)
        orders = ["CBC", "CRP"]
        if "respiratory" in specialties:
            orders.extend(["chest X-ray", "oxygen saturation"])
        if "cardiology" in specialties:
            orders.extend(["ECG", "troponin"])
        if "infectious_disease" in specialties:
            orders.extend(["blood culture", "pathogen testing"])
        if "neurology" in specialties:
            orders.extend(["neurological exam", "head CT if clinically indicated"])

        deduped = list(dict.fromkeys(orders))
        priority = "stat" if len(specialties) >= 3 else "routine"
        lab_order = self.tools.lab_order.run(deduped, priority)
        imaging_order = self.tools.imaging_order.run(deduped, priority)
        return self.ready(
            summary=f"Diagnostic orders created for {len(deduped)} tests.",
            recommendations=[f"Order {item}." for item in deduped],
            decisions={
                "orders": deduped,
                "order_priority": priority,
            },
            data={"tool_results": [lab_order, imaging_order]},
            handoff_to=["lab_result_interpreter_agent", "imaging_interpreter_agent"],
            confidence=0.82,
        )


class LabResultInterpreterAgent(HospitalAgent):
    name = "lab_result_interpreter_agent"
    role = "lab_result_interpretation"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        orders = _orders(previous)
        infection_risk = "blood culture" in orders or "CRP" in orders
        cardiac_risk = "troponin" in orders
        interpretation = []
        if infection_risk:
            interpretation.append("infection_workup_required")
        if cardiac_risk:
            interpretation.append("cardiac_marker_review_required")
        if not interpretation:
            interpretation.append("basic_labs_sufficient_for_demo")
        lab_results = self.tools.lab_result_fetch.run(orders)

        return self.ready(
            summary="Lab interpreter produced demo-level risk interpretation.",
            findings=interpretation,
            decisions={
                "lab_interpretation": interpretation,
                "requires_repeat_labs": infection_risk and cardiac_risk,
            },
            data={"tool_results": [lab_results]},
            handoff_to=["pharmacy_safety_agent"],
            confidence=0.74,
        )


class ImagingInterpreterAgent(HospitalAgent):
    name = "imaging_interpreter_agent"
    role = "imaging_interpretation"

    def __init__(self, tools: ClinicalToolRegistry | None = None) -> None:
        self.tools = tools or ClinicalToolRegistry()

    def run(
        self,
        context: HospitalContext,
        previous: list[HospitalAgentResult],
    ) -> HospitalAgentResult:
        orders = _orders(previous)
        interpretations = []
        if "chest X-ray" in orders:
            interpretations.append("chest_imaging_needed_for_respiratory_risk")
        if "head CT if clinically indicated" in orders:
            interpretations.append("neuroimaging_contingency_for_confusion")
        if not interpretations:
            interpretations.append("no_advanced_imaging_required_for_demo")
        imaging_results = self.tools.imaging_result_fetch.run(orders)

        return self.ready(
            summary="Imaging interpreter reviewed demo imaging pathway.",
            findings=interpretations,
            decisions={
                "imaging_interpretation": interpretations,
                "requires_follow_up_imaging": len(interpretations) > 1,
            },
            data={"tool_results": [imaging_results]},
            handoff_to=["pharmacy_safety_agent"],
            confidence=0.72,
        )


def _orders(previous: list[HospitalAgentResult]) -> list[str]:
    order_agent = next(
        (result for result in previous if result.agent == "diagnostic_order_agent"),
        None,
    )
    return list(order_agent.decisions.get("orders", [])) if order_agent else []
