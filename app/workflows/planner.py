from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.context import HospitalAgentResult


@dataclass
class WorkflowPlan:
    agent_names: list[str]
    decisions: list[dict[str, str]] = field(default_factory=list)


class HospitalWorkflowPlanner:
    def plan(self, results: list[HospitalAgentResult]) -> WorkflowPlan:
        plan = [
            "registration_agent",
            "intake_agent",
            "nurse_vitals_agent",
            "appointment_agent",
            "triage_nurse_agent",
        ]
        decisions: list[dict[str, str]] = []
        triage = _result(results, "triage_nurse_agent")
        if triage is None:
            return WorkflowPlan(plan, decisions)

        urgency = triage.decisions.get("urgency_level")
        plan.append("department_router_agent")
        if urgency == "high":
            _record_decision(
                decisions,
                decision="emergency_branch",
                made_by="triage_nurse_agent",
                reason="high triage urgency",
            )
            plan.extend(["emergency_physician_agent", "general_practitioner_agent"])
        else:
            _record_decision(
                decisions,
                decision="outpatient_branch",
                made_by="triage_nurse_agent",
                reason="standard triage urgency",
            )
            plan.append("general_practitioner_agent")

        plan.append("specialist_router_agent")
        router = _result(results, "specialist_router_agent")
        if router is None:
            return WorkflowPlan(plan, decisions)

        selected = list(router.decisions.get("selected_specialties", []))
        _record_decision(
            decisions,
            decision="specialist_consultation_branch",
            made_by="specialist_router_agent",
            reason=", ".join(selected) if selected else "no specialty selected",
        )
        plan.extend(f"{specialty}_specialist_agent" for specialty in selected)
        plan.extend(
            [
                "diagnostic_order_agent",
                "lab_advisor_agent",
                "lab_result_interpreter_agent",
                "imaging_interpreter_agent",
                "pharmacy_safety_agent",
                "medication_plan_agent",
            ]
        )
        if urgency == "high":
            plan.extend(
                [
                    "disposition_coordinator_agent",
                    "admission_coordinator_agent",
                    "final_hospital_report_agent",
                ]
            )
        else:
            plan.extend(
                [
                    "care_plan_agent",
                    "follow_up_agent",
                    "disposition_coordinator_agent",
                    "admission_coordinator_agent",
                    "final_hospital_report_agent",
                ]
            )
        return WorkflowPlan(plan, decisions)


def _result(
    results: list[HospitalAgentResult],
    agent_name: str,
) -> HospitalAgentResult | None:
    return next((result for result in results if result.agent == agent_name), None)


def _record_decision(
    workflow_decisions: list[dict[str, str]],
    decision: str,
    made_by: str,
    reason: str,
) -> None:
    item = {"decision": decision, "made_by": made_by, "reason": reason}
    if item not in workflow_decisions:
        workflow_decisions.append(item)
