from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from time import perf_counter
from typing import Any

from app.agents import (
    AdmissionCoordinatorAgent,
    AppointmentAgent,
    CardiologySpecialistAgent,
    CarePlanAgent,
    DepartmentRouterAgent,
    DiagnosticOrderAgent,
    DispositionCoordinatorAgent,
    EmergencyPhysicianAgent,
    FinalHospitalReportAgent,
    FollowUpAgent,
    GeneralPractitionerAgent,
    HospitalAgent,
    ImagingInterpreterAgent,
    InfectiousDiseaseSpecialistAgent,
    IntakeAgent,
    LabAdvisorAgent,
    LabResultInterpreterAgent,
    MedicationPlanAgent,
    NeurologySpecialistAgent,
    NurseVitalsAgent,
    OrderingClinicianReviewAgent,
    PharmacySafetyAgent,
    RegistrationAgent,
    RespiratorySpecialistAgent,
    SpecialistRouterAgent,
    TriageNurseAgent,
)
from app.agents.context import HospitalContext
from app.agents.llm import HospitalLlmClient, default_hospital_llm_client
from app.tools import AIConsultationTool, ClinicalToolRegistry, PatientHistoryLookupTool
from app.workflows.planner import HospitalWorkflowPlanner


class HospitalOrchestrator:
    def __init__(
        self,
        agents: list[HospitalAgent] | None = None,
        llm_client: HospitalLlmClient | None = None,
        consultation_tool: AIConsultationTool | None = None,
        patient_history_tool: PatientHistoryLookupTool | None = None,
        tool_registry: ClinicalToolRegistry | None = None,
        planner: HospitalWorkflowPlanner | None = None,
        entry_agents: list[str] | None = None,
    ) -> None:
        self.llm_client = llm_client or default_hospital_llm_client()
        self.consultation_tool = consultation_tool or AIConsultationTool()
        self.patient_history_tool = patient_history_tool or PatientHistoryLookupTool()
        self.tool_registry = tool_registry or ClinicalToolRegistry()
        self.agents = agents
        self.planner = planner or HospitalWorkflowPlanner()
        self.entry_agents = entry_agents
        self.agent_registry: dict[str, HospitalAgent] = {
            "registration_agent": RegistrationAgent(self.patient_history_tool),
            "intake_agent": IntakeAgent(),
            "nurse_vitals_agent": NurseVitalsAgent(),
            "appointment_agent": AppointmentAgent(),
            "triage_nurse_agent": TriageNurseAgent(self.tool_registry),
            "department_router_agent": DepartmentRouterAgent(),
            "emergency_physician_agent": EmergencyPhysicianAgent(
                self.llm_client,
                self.tool_registry,
            ),
            "general_practitioner_agent": GeneralPractitionerAgent(
                self.llm_client,
                self.consultation_tool,
            ),
            "specialist_router_agent": SpecialistRouterAgent(),
            "respiratory_specialist_agent": RespiratorySpecialistAgent(
                self.llm_client,
                self.tool_registry,
            ),
            "cardiology_specialist_agent": CardiologySpecialistAgent(
                self.llm_client,
                self.tool_registry,
            ),
            "infectious_disease_specialist_agent": InfectiousDiseaseSpecialistAgent(
                self.llm_client,
                self.tool_registry,
            ),
            "neurology_specialist_agent": NeurologySpecialistAgent(
                self.llm_client,
                self.tool_registry,
            ),
            "diagnostic_order_agent": DiagnosticOrderAgent(self.tool_registry),
            "lab_advisor_agent": LabAdvisorAgent(),
            "lab_result_interpreter_agent": LabResultInterpreterAgent(self.tool_registry),
            "imaging_interpreter_agent": ImagingInterpreterAgent(self.tool_registry),
            "ordering_clinician_review_agent": OrderingClinicianReviewAgent(),
            "pharmacy_safety_agent": PharmacySafetyAgent(
                self.patient_history_tool,
                self.tool_registry,
            ),
            "medication_plan_agent": MedicationPlanAgent(),
            "care_plan_agent": CarePlanAgent(self.llm_client, self.patient_history_tool),
            "follow_up_agent": FollowUpAgent(
                self.patient_history_tool,
                self.tool_registry,
            ),
            "disposition_coordinator_agent": DispositionCoordinatorAgent(self.tool_registry),
            "admission_coordinator_agent": AdmissionCoordinatorAgent(self.tool_registry),
            "final_hospital_report_agent": FinalHospitalReportAgent(
                self.llm_client,
                self.patient_history_tool,
            ),
        }

    def run(
        self,
        case_text: str,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        language: str = "zh-CN",
        progress_publisher: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        context = HospitalContext(
            case_text=case_text,
            patient_id=patient_id,
            doctor_id=doctor_id,
            language=language,
            metadata=metadata or {},
        )
        results = []
        workflow_decisions = []
        timeline = _HandoffTimeline(progress_publisher=progress_publisher)
        if self.agents is not None:
            custom_registry = {agent.name: agent for agent in self.agents}
            pending = self.entry_agents or _initial_custom_agents(self.agents)
            completed = set()
            self._run_handoff_queue(
                context=context,
                results=results,
                workflow_decisions=workflow_decisions,
                timeline=timeline,
                registry=custom_registry,
                pending=pending,
                completed=completed,
                allow_planner_fallback=False,
            )
        else:
            self._run_handoff_queue(
                context=context,
                results=results,
                workflow_decisions=workflow_decisions,
                timeline=timeline,
                registry=self.agent_registry,
                pending=self.entry_agents or ["registration_agent"],
                completed=set(),
                allow_planner_fallback=True,
            )

        result_payloads = [asdict(result) for result in results]
        router = next(
            (result for result in results if result.agent == "specialist_router_agent"),
            None,
        )
        gp_result = next(
            (result for result in results if result.agent == "general_practitioner_agent"),
            None,
        )
        final_report = next(
            (result for result in results if result.agent == "final_hospital_report_agent"),
            None,
        )
        disposition = next(
            (result for result in results if result.agent == "disposition_coordinator_agent"),
            None,
        )
        return {
            "workflow": "agent_hospital_lite",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "language": language,
            "executed_path": [result.agent for result in results],
            "workflow_decisions": workflow_decisions,
            "selected_specialties": (
                router.decisions.get("selected_specialties", []) if router else []
            ),
            "disposition": (
                disposition.decisions.get("disposition", {})
                if disposition
                else {"decision": "not_available"}
            ),
            "care_pathway": _care_pathway(results),
            "ai_consultation": (
                gp_result.data.get("ai_consultation_tool", {})
                if gp_result
                else {"workflow": "ai_consultation_tool"}
            ),
            "final_report": (
                asdict(final_report) if final_report else {"summary": "Final report unavailable."}
            ),
            "handoff_timeline": timeline.events,
            "agent_results": result_payloads,
        }

    def _planned_agents(
        self,
        results: list,
        workflow_decisions: list[dict[str, str]],
    ) -> list[HospitalAgent]:
        plan = self.planner.plan(results)
        for decision in plan.decisions:
            if decision not in workflow_decisions:
                workflow_decisions.append(decision)
        completed = {result.agent for result in results}
        return [self.agent_registry[name] for name in plan.agent_names if name not in completed]

    def _run_handoff_queue(
        self,
        context: HospitalContext,
        results: list,
        workflow_decisions: list[dict[str, str]],
        timeline: Any,
        registry: dict[str, HospitalAgent],
        pending: list[str],
        completed: set[str],
        allow_planner_fallback: bool,
    ) -> None:
        barriers = [
            _FanInBarrier(
                required_agents={
                    "lab_result_interpreter_agent",
                    "imaging_interpreter_agent",
                },
                target_agents=["ordering_clinician_review_agent"],
                parallel_group="diagnostic_results_fanin",
            )
        ]
        while True:
            if not pending and allow_planner_fallback:
                pending.extend(
                    agent.name
                    for agent in self._planned_agents(results, workflow_decisions)
                    if agent.name not in completed
                )
            if not pending:
                return

            next_names = _next_execution_names(pending)
            pending = pending[len(next_names) :]
            next_batch = [
                registry[name]
                for name in next_names
                if name not in completed and name in registry
            ]
            if not next_batch:
                continue
            if len(next_batch) == 1:
                batch_results = [_run_agent(next_batch[0], context, results)]
                parallel_group = None
            else:
                prior_results = list(results)
                parallel_group = timeline.record_parallel_fanout(next_batch)
                with ThreadPoolExecutor(max_workers=len(next_batch)) as executor:
                    batch_results = list(
                        executor.map(
                            lambda agent: _run_agent(agent, context, prior_results),
                            next_batch,
                        )
                    )
            for result, duration_ms in batch_results:
                results.append(result)
                completed.add(result.agent)
                timeline.record_agent_result(
                    result,
                    duration_ms,
                    parallel_group=parallel_group,
                )
                for target in result.handoff_to:
                    if _is_barrier_target(target, barriers):
                        continue
                    if target not in completed and target not in pending:
                        pending.append(target)
                for barrier in barriers:
                    if barrier.ready(completed) and not barrier.released:
                        timeline.record_fanin_agents(
                            completed_agents=barrier.completed_agents(),
                            target_agents=barrier.target_agents,
                            parallel_group=barrier.parallel_group,
                        )
                        barrier.released = True
                        for target in barrier.target_agents:
                            if target not in completed and target not in pending:
                                pending.append(target)
            if parallel_group:
                timeline.record_fanin(next_batch, parallel_group)


def _next_execution_names(remaining: list[str]) -> list[str]:
    if not remaining or not _is_specialist_agent(remaining[0]):
        return remaining[:1]
    batch = []
    for agent_name in remaining:
        if not _is_specialist_agent(agent_name):
            break
        batch.append(agent_name)
    return batch


def _is_specialist_agent(agent_name: str) -> bool:
    return agent_name.endswith("_specialist_agent")


class _FanInBarrier:
    def __init__(
        self,
        required_agents: set[str],
        target_agents: list[str],
        parallel_group: str,
    ) -> None:
        self.required_agents = required_agents
        self.target_agents = target_agents
        self.parallel_group = parallel_group
        self.released = False

    def ready(self, completed: set[str]) -> bool:
        return self.required_agents.issubset(completed)

    def completed_agents(self) -> list[str]:
        order = [
            "lab_result_interpreter_agent",
            "imaging_interpreter_agent",
        ]
        return [agent for agent in order if agent in self.required_agents]


def _is_barrier_target(agent_name: str, barriers: list[_FanInBarrier]) -> bool:
    return any(agent_name in barrier.target_agents and not barrier.released for barrier in barriers)


def _initial_custom_agents(agents: list[HospitalAgent]) -> list[str]:
    targeted = {
        target
        for agent in agents
        for target in getattr(agent, "handoff_to", [])
    }
    names = [agent.name for agent in agents]
    roots = [name for name in names if name not in targeted]
    return roots or names[:1]


def _run_agent(
    agent: HospitalAgent,
    context: HospitalContext,
    previous: list,
) -> tuple[Any, int]:
    started = perf_counter()
    result = agent.run(context, previous)
    duration_ms = int((perf_counter() - started) * 1000)
    return result, duration_ms


class _HandoffTimeline:
    def __init__(self, progress_publisher: Any | None = None) -> None:
        self.events: list[dict[str, Any]] = []
        self._parallel_group_count = 0
        self.progress_publisher = progress_publisher

    def record_agent_result(
        self,
        result: Any,
        duration_ms: int,
        parallel_group: str | None = None,
    ) -> None:
        self._append(
            {
                "event_type": "agent_completed",
                "agent": result.agent,
                "duration_ms": duration_ms,
                **({"parallel_group": parallel_group} if parallel_group else {}),
            }
        )
        for event in _decision_events(result):
            self._append(_role_scoped_decision_event(result, event))
        for event in _tool_events(result):
            self._append(event)
        if result.handoff_to:
            self._append(
                {
                    "event_type": "handoff_created",
                    "agent": result.agent,
                    "target_agents": result.handoff_to,
                    "reason": _handoff_reason(result),
                    "payload": {
                        "decision_type": "role_scoped_agent_decision",
                        "role": result.role,
                        "handoff_to": list(result.handoff_to),
                        "tool_choices": _tool_choices(result),
                        "evidence": _decision_evidence(result),
                    },
                }
            )

    def record_parallel_fanout(self, agents: list[HospitalAgent]) -> str:
        self._parallel_group_count += 1
        parallel_group = f"specialist_consultation_{self._parallel_group_count}"
        self._append(
            {
                "event_type": "parallel_fanout",
                "agent": "hospital_workflow_planner",
                "target_agents": [agent.name for agent in agents],
                "parallel_group": parallel_group,
                "reason": "selected specialists can consult after shared upstream context is available",
            }
        )
        return parallel_group

    def record_fanin(self, agents: list[HospitalAgent], parallel_group: str) -> None:
        completed_agents = [agent.name for agent in agents]
        self.record_fanin_agents(
            completed_agents=completed_agents,
            target_agents=["lab_result_interpreter_agent", "imaging_interpreter_agent"],
            parallel_group=parallel_group,
        )

    def record_fanin_agents(
        self,
        completed_agents: list[str],
        target_agents: list[str],
        parallel_group: str,
    ) -> None:
        self._append(
            {
                "event_type": "fanin_completed",
                "agent": "hospital_workflow_planner",
                "target_agents": target_agents,
                "parallel_group": parallel_group,
                "payload": {"completed_agents": completed_agents},
            }
        )

    def _append(self, event: dict[str, Any]) -> None:
        event["event_index"] = len(self.events)
        self.events.append(event)
        if self.progress_publisher is not None:
            self.progress_publisher(dict(event))


def _decision_events(result: Any) -> list[dict[str, Any]]:
    agent = result.agent
    decisions = result.decisions
    if agent == "registration_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "registration_completed",
                "decision_scope": "administrative",
                "reason": decisions.get("registration_status", "complete"),
                "payload": {
                    "visit_type": decisions.get("visit_type"),
                    "missing_fields": decisions.get("missing_fields", []),
                },
            }
        ]
    if agent == "nurse_vitals_agent":
        status = decisions.get("vitals_status", "stable")
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": (
                    "abnormal_vitals_detected"
                    if status == "abnormal"
                    else "stable_vitals_recorded"
                ),
                "decision_scope": "triage",
                "reason": f"nurse vitals status: {status}",
                "payload": {
                    "vitals_status": status,
                    "recommended_vitals": decisions.get("recommended_vitals", []),
                    "risk_terms": decisions.get("risk_terms", []),
                },
            }
        ]
    if agent == "triage_nurse_agent":
        urgency = decisions.get("urgency_level")
        if urgency == "high":
            return [
                {
                    "event_type": "decision_made",
                    "agent": agent,
                    "decision": "emergency_branch",
                    "decision_scope": "routing",
                    "reason": "high triage urgency",
                    "payload": {
                        "urgency_level": urgency,
                        "recommended_department": decisions.get("recommended_department"),
                        "red_flags": decisions.get("red_flags", []),
                        "selected_branch": {
                            "target": "department_router_agent",
                            "reason": "high triage urgency",
                        },
                    },
                }
            ]
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "outpatient_branch",
                "decision_scope": "routing",
                "reason": "standard triage urgency",
                "payload": {
                    "urgency_level": urgency,
                    "recommended_department": decisions.get("recommended_department"),
                    "red_flags": decisions.get("red_flags", []),
                    "selected_branch": {
                        "target": "department_router_agent",
                        "reason": "standard triage urgency",
                    },
                },
            }
        ]
    if agent == "department_router_agent":
        urgency = decisions.get("urgency_level")
        selected_target = (
            "emergency_physician_agent"
            if urgency == "high"
            else "general_practitioner_agent"
        )
        selected_reason = (
            "high triage urgency routes to emergency physician first"
            if urgency == "high"
            else "standard urgency routes to general practitioner first"
        )
        skipped_target = (
            "general_practitioner_agent"
            if urgency == "high"
            else "emergency_physician_agent"
        )
        skipped_reason = (
            "high urgency prioritizes emergency physician review before routine GP path"
            if urgency == "high"
            else "standard urgency routes to general practitioner first"
        )
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "department_route_selected",
                "decision_scope": "routing",
                "reason": f"primary department: {decisions.get('primary_department')}",
                "payload": {
                    "primary_department": decisions.get("primary_department"),
                    "candidate_departments": decisions.get("candidate_departments", []),
                    "selected_branch": {
                        "target": selected_target,
                        "reason": selected_reason,
                    },
                    "skipped_branches": [
                        {
                            "target": skipped_target,
                            "reason": skipped_reason,
                        }
                    ],
                },
            }
        ]
    if agent == "emergency_physician_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "emergency_resource_readiness_confirmed",
                "decision_scope": "resource_readiness",
                "reason": "emergency physician requested staff, resources, and stat exams before downstream review",
                "payload": {
                    "readiness": decisions.get("emergency_resource_readiness"),
                    "ordering_agent": decisions.get("ordering_agent"),
                    "ordered_exams": decisions.get("ordered_exams", []),
                },
            }
        ]
    if agent == "specialist_router_agent":
        selected = decisions.get("selected_specialties", [])
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "specialist_consultation_branch",
                "decision_scope": "routing",
                "reason": ", ".join(selected) if selected else "no specialty selected",
                "payload": {
                    "selected_specialties": selected,
                    "parallel_branch": len(selected) > 1,
                    "selected_branches": [
                        {
                            "target": f"{specialty}_specialist_agent",
                            "reason": f"{specialty} specialty selected by role router",
                        }
                        for specialty in selected
                    ],
                },
            }
        ]
    if agent.endswith("_specialist_agent"):
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "ordering_clinician_review_required",
                "decision_scope": "review_loop",
                "reason": "exam results should return to the clinician that ordered them",
                "payload": {
                    "ordering_agent": decisions.get("ordering_agent", agent),
                    "requested_exams": decisions.get("requested_exams", []),
                    "review_loop": decisions.get("review_loop"),
                },
            }
        ]
    if agent == "diagnostic_order_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "diagnostic_orders_created",
                "decision_scope": "orders",
                "reason": f"order priority: {decisions.get('order_priority', 'routine')}",
                "payload": {"orders": decisions.get("orders", [])},
            }
        ]
    if agent == "lab_advisor_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "diagnostic_workup_selected",
                "decision_scope": "clinical",
                "reason": "selected specialties determine diagnostic workup in the demo workflow",
                "payload": {"recommended_tests": decisions.get("recommended_tests", [])},
            }
        ]
    if agent == "lab_result_interpreter_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "lab_results_interpreted",
                "decision_scope": "clinical",
                "reason": "demo lab interpretation produced downstream risk flags",
                "payload": {
                    "lab_interpretation": decisions.get("lab_interpretation", []),
                    "requires_repeat_labs": decisions.get("requires_repeat_labs", False),
                },
            }
        ]
    if agent == "imaging_interpreter_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "imaging_results_interpreted",
                "decision_scope": "clinical",
                "reason": "demo imaging pathway interpreted for disposition planning",
                "payload": {
                    "imaging_interpretation": decisions.get("imaging_interpretation", []),
                    "requires_follow_up_imaging": decisions.get(
                        "requires_follow_up_imaging",
                        False,
                    ),
                },
            }
        ]
    if agent == "ordering_clinician_review_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "ordering_clinician_review_completed",
                "decision_scope": "review_loop",
                "reason": "interpreted exam results returned to the clinician that ordered them",
                "payload": {
                    "ordering_agents": decisions.get("ordering_agents", []),
                    "reviewed_findings": decisions.get("reviewed_findings", []),
                    "review_status": decisions.get("review_status"),
                },
            }
        ]
    if agent == "pharmacy_safety_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "medication_safety_review_required",
                "decision_scope": "clinical",
                "reason": "medication suggestions require allergy and medication-history confirmation",
                "payload": {
                    "requires_allergy_check": decisions.get("requires_allergy_check", False)
                },
            }
        ]
    if agent == "medication_plan_agent":
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "medication_plan_created",
                "decision_scope": "medication",
                "reason": decisions.get("medication_plan_status", "ready"),
                "payload": {
                    "medication_plan_status": decisions.get("medication_plan_status"),
                    "requires_pharmacist_review": decisions.get(
                        "requires_pharmacist_review",
                        False,
                    ),
                },
            }
        ]
    if agent == "disposition_coordinator_agent":
        disposition = decisions.get("disposition", {})
        decision = disposition.get("decision", "disposition_selected")
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": decision,
                "decision_scope": "disposition",
                "reason": disposition.get("reason", ""),
                "payload": {
                    "disposition": disposition,
                    "monitoring_plan": decisions.get("monitoring_plan", []),
                },
            }
        ]
    if agent == "admission_coordinator_agent":
        pathway = decisions.get("admission_pathway", {})
        return [
            {
                "event_type": "decision_made",
                "agent": agent,
                "decision": "admission_pathway_selected",
                "decision_scope": "admission",
                "reason": pathway.get("reason", ""),
                "payload": {"admission_pathway": pathway},
            }
        ]
    return []


def _role_scoped_decision_event(
    result: Any,
    event: dict[str, Any],
) -> dict[str, Any]:
    payload = event.setdefault("payload", {})
    payload.setdefault("decision_type", "role_scoped_agent_decision")
    payload.setdefault("role", result.role)
    payload.setdefault("handoff_to", list(result.handoff_to))
    payload.setdefault("tool_choices", _tool_choices(result))
    payload.setdefault("evidence", _decision_evidence(result))
    return event


def _tool_events(result: Any) -> list[dict[str, Any]]:
    tool_results = _agent_tool_results(result)
    events = []
    for tool_result in tool_results:
        tool_name = tool_result.get("tool", "unknown_tool")
        status = tool_result.get("status", "unknown")
        reason = _tool_reason(result.agent, tool_result)
        raw_payload = (
            tool_result.get("payload", {})
            if isinstance(tool_result.get("payload"), dict)
            else {}
        )
        events.append(
            {
                "event_type": "tool_skipped" if status == "skipped" else "tool_invoked",
                "agent": result.agent,
                "decision": tool_name,
                "decision_scope": "tool_use",
                "reason": reason,
                "payload": {
                    **raw_payload,
                    "tool": tool_name,
                    "status": status,
                    "choice": _tool_choice(status),
                    "selection_reason": reason,
                    "decision_type": "role_scoped_agent_decision",
                    "role": result.role,
                    "handoff_to": list(result.handoff_to),
                    "summary": tool_result.get("summary"),
                    "patientId": tool_result.get("patientId"),
                },
            }
        )
    return events


def _agent_tool_results(result: Any) -> list[dict[str, Any]]:
    tool_results = []
    history_lookup = result.data.get("patient_history_lookup")
    if isinstance(history_lookup, dict):
        tool_results.append(history_lookup)
    extra_tools = result.data.get("tool_results", [])
    if isinstance(extra_tools, list):
        tool_results.extend(item for item in extra_tools if isinstance(item, dict))
    return tool_results


def _tool_choices(result: Any) -> list[dict[str, Any]]:
    choices = []
    for tool_result in _agent_tool_results(result):
        tool_name = tool_result.get("tool", "unknown_tool")
        status = tool_result.get("status", "unknown")
        choices.append(
            {
                "tool": tool_name,
                "status": status,
                "choice": _tool_choice(status),
                "reason": _tool_reason(result.agent, tool_result),
            }
        )
    return choices


def _tool_choice(status: str) -> str:
    if status == "skipped":
        return "skipped"
    if status == "unavailable":
        return "unavailable"
    return "selected"


def _decision_evidence(result: Any) -> list[str]:
    evidence = ["current_encounter_context"]
    if result.decisions:
        evidence.append("role_decision_fields")
    if result.findings:
        evidence.append("role_findings")
    if result.recommendations:
        evidence.append("role_recommendations")
    if result.handoff_to:
        evidence.append("selected_handoff_targets")
    tool_results = _agent_tool_results(result)
    if tool_results:
        evidence.append("agent_tool_results")
    if any(
        tool_result.get("tool") == "patient_history_lookup"
        for tool_result in tool_results
    ):
        evidence.append("patient_history_summary")
    return evidence


def _handoff_reason(result: Any) -> str:
    targets = ", ".join(result.handoff_to)
    if not targets:
        return ""
    return f"{result.role} selected downstream handoff target(s): {targets}."


def _tool_reason(agent_name: str, tool_result: dict[str, Any]) -> str:
    if tool_result.get("tool") == "patient_history_lookup":
        return _history_tool_reason(agent_name)
    if tool_result.get("summary"):
        return str(tool_result["summary"])
    return f"{agent_name} selected {tool_result.get('tool', 'an internal tool')}."


def _history_tool_reason(agent_name: str) -> str:
    reasons = {
        "registration_agent": "identify whether this is a new or returning patient",
        "pharmacy_safety_agent": "check allergies and current medications before medication planning",
        "care_plan_agent": "compare the proposed care plan with prior dispositions",
        "follow_up_agent": "compare follow-up planning with previous dispositions",
        "final_hospital_report_agent": "include relevant prior report context in the final summary",
    }
    return reasons.get(agent_name, "retrieve patient history for this role decision")


def _care_pathway(results: list) -> dict:
    by_agent = {result.agent: result for result in results}
    registration = by_agent.get("registration_agent")
    vitals = by_agent.get("nurse_vitals_agent")
    department = by_agent.get("department_router_agent")
    triage = by_agent.get("triage_nurse_agent")
    router = by_agent.get("specialist_router_agent")
    orders = by_agent.get("diagnostic_order_agent")
    lab = by_agent.get("lab_advisor_agent")
    lab_interpreter = by_agent.get("lab_result_interpreter_agent")
    imaging = by_agent.get("imaging_interpreter_agent")
    review = by_agent.get("ordering_clinician_review_agent")
    pharmacy = by_agent.get("pharmacy_safety_agent")
    medication = by_agent.get("medication_plan_agent")
    emergency = by_agent.get("emergency_physician_agent")
    disposition = by_agent.get("disposition_coordinator_agent")
    admission = by_agent.get("admission_coordinator_agent")
    return {
        "registration": (
            registration.decisions if registration else {}
        ),
        "vitals": vitals.decisions if vitals else {},
        "department_route": (
            department.decisions if department else {}
        ),
        "encounter_type": (
            by_agent.get("appointment_agent", None).decisions.get("encounter_type")
            if by_agent.get("appointment_agent")
            else None
        ),
        "triage_level": triage.decisions.get("urgency_level") if triage else None,
        "immediate_actions": (
            emergency.decisions.get("immediate_actions", []) if emergency else []
        ),
        "consultations": (
            router.decisions.get("selected_specialties", []) if router else []
        ),
        "diagnostic_order_set": orders.decisions if orders else {},
        "diagnostic_orders": _ordered_exams_from_results(results),
        "lab_interpretation": (
            lab_interpreter.decisions.get("lab_interpretation", [])
            if lab_interpreter
            else []
        ),
        "imaging_interpretation": (
            imaging.decisions.get("imaging_interpretation", []) if imaging else []
        ),
        "ordering_clinician_review": review.decisions if review else {},
        "medication_safety": pharmacy.recommendations if pharmacy else [],
        "medication_plan": medication.decisions if medication else {},
        "disposition": (
            disposition.decisions.get("disposition", {}) if disposition else {}
        ),
        "admission_pathway": (
            admission.decisions.get("admission_pathway", {}) if admission else {}
        ),
        "monitoring_plan": (
            disposition.decisions.get("monitoring_plan", []) if disposition else []
        ),
    }


def _ordered_exams_from_results(results: list) -> list[str]:
    exams: list[str] = []
    for result in results:
        for key in ("requested_exams", "ordered_exams"):
            value = result.decisions.get(key)
            if isinstance(value, list):
                exams.extend(str(item) for item in value)
    return list(dict.fromkeys(exams))
