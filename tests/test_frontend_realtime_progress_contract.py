from pathlib import Path


def test_frontend_polls_realtime_agent_progress_and_renders_decision_events() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    timeline = Path("frontend/src/components/AgentTimeline.vue").read_text(encoding="utf-8")

    assert "`/api/ai/tasks/${taskId}/progress`" in app
    assert "progressEvents.value.length" in app
    assert "Decision: {{ event.decision }}" in timeline
    assert "eventClass(event.event_type)" in timeline
    assert "await delay(800)" in app
    assert "displayedDecisions" in app
    assert "完成后一次性写入真实 handoff timeline" not in app

def test_frontend_renders_agent_tool_use_events_in_realtime_timeline() -> None:
    timeline = Path("frontend/src/components/AgentTimeline.vue").read_text(encoding="utf-8")

    assert "tool_invoked" in timeline
    assert "tool_skipped" in timeline
    assert 'return "Tool invoked"' in timeline
    assert 'return "Tool skipped"' in timeline
    assert 'eventClass(event.event_type)' in timeline
    assert 'event.payload?.tool' in timeline
    assert 'event.payload?.status' in timeline


def test_frontend_task_switching_uses_task_scoped_polling_contract() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")

    assert "pollGeneration" in app
    assert "pollingTaskId" in app
    assert "isActivePollingRun(taskId, runId)" in app
    assert "selectedTaskId.value !== taskId" in app
    assert "currentTask.value = tasks.value.find((task) => task.taskId === taskId) || null" in app
    assert "isCurrentTaskPolling" in app
    assert "isPolling" not in app


def test_frontend_merges_live_progress_with_final_timeline_and_report_shapes() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")

    assert "mergeTimelineEvents(progressEvents.value, finalTimeline.value)" in app
    assert "progressCompletedAgents" in app
    assert "extractFirstFinalReportText" in app
    assert '"markdown", "report_markdown", "content", "text", "report_summary", "summary"' in app
    assert "normalizeReportMarkdownText(finalReportText.value" in app
    assert "result?: WorkflowResult" not in app
    assert "currentTask.value?.result" not in app
    assert "clinicalRecord.value?.rawResult || null" in app


def test_frontend_exposes_demo_cases_for_stable_manual_flow_demos() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    sidebar = Path("frontend/src/components/EncounterSidebar.vue").read_text(encoding="utf-8")
    demo_cases = Path("frontend/src/demoCases.ts").read_text(encoding="utf-8")

    assert "EncounterSidebar" in app
    assert "Demo Cases" in sidebar
    assert "emergency_multi_specialty" in demo_cases
    assert "standard_outpatient" in demo_cases
    assert "low_risk_followup" in demo_cases
    assert "@click=\"emit('apply-demo-case', demoCase)\"" in sidebar


def test_frontend_exposes_emergency_surge_panel_for_concurrent_er_demo() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    surge_panel = Path("frontend/src/components/EmergencySurgePanel.vue").read_text(encoding="utf-8")
    demo_cases = Path("frontend/src/demoCases.ts").read_text(encoding="utf-8")

    assert "EmergencySurgePanel" in app
    assert "runEmergencySurge" in app
    assert "Promise.allSettled" in app
    assert "surgeResults" in app
    assert "extractSurgeReadiness" in app
    assert "extractSurgePractitionerAssignment" in app
    assert "Emergency Surge Scenario" in surge_panel
    assert "resource_reservation" in surge_panel
    assert "practitioner_assignment" in surge_panel
    assert "readinessStatus" in surge_panel
    assert "assignedPractitioners" in surge_panel
    assert "unavailableSpecialties" in surge_panel
    assert "emergency_surge_template" in demo_cases


def test_frontend_app_shell_uses_smaller_componentized_entrypoint() -> None:
    app_path = Path("frontend/src/App.vue")
    app = app_path.read_text(encoding="utf-8")

    assert Path("frontend/src/types.ts").is_file()
    assert Path("frontend/src/demoCases.ts").is_file()
    assert Path("frontend/src/components/EncounterSidebar.vue").is_file()
    assert "from \"./types\"" in app
    assert "from \"./demoCases\"" in app
    assert "EncounterSidebar" in app
    assert len(app.splitlines()) < 760


def test_frontend_presents_a_hospital_journey_overview_for_the_whole_flow() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    journey = Path("frontend/src/components/HospitalJourneyOverview.vue").read_text(encoding="utf-8")

    assert "HospitalJourneyOverview" in app
    assert "Hospital Journey Overview" in journey
    assert "journeyStages" in app
    assert "journeyProgressPercent" in app
    assert "Agent events" in journey
    assert "Decision events" in journey
    assert "Parallel branches" in journey


def test_frontend_uses_workflow_display_panel_for_timeline_path_and_decisions() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/WorkflowDisplayPanel.vue").read_text(encoding="utf-8")

    assert "WorkflowDisplayPanel" in app
    assert "AgentTimeline" in panel
    assert "Agent Handoff Timeline" in panel
    assert "Executed Path" in panel
    assert "Workflow Decisions" in panel


def test_frontend_graph_view_uses_realtime_timeline_events_not_fixed_stages() -> None:
    panel = Path("frontend/src/components/WorkflowDisplayPanel.vue").read_text(encoding="utf-8")
    graph_path = Path("frontend/src/components/AgentWorkflowGraph.vue")
    package_json = Path("frontend/package.json").read_text(encoding="utf-8")
    styles = Path("frontend/src/styles.css").read_text(encoding="utf-8")

    assert graph_path.is_file()
    graph = graph_path.read_text(encoding="utf-8")

    assert '"@vue-flow/core"' in package_json
    assert '"@vue-flow/background"' in package_json
    assert '"@vue-flow/controls"' in package_json
    assert '"@vue-flow/minimap"' in package_json
    assert "VueFlow" in graph
    assert "Background" in graph
    assert "Controls" in graph
    assert "MiniMap" in graph
    assert "@vue-flow/core/dist/style.css" in graph
    assert "AgentWorkflowGraph" in panel
    assert "activeWorkflowView" in panel
    assert (
        'activeWorkflowView === "timeline"' in panel
        or "activeWorkflowView === 'timeline'" in panel
    )
    assert (
        'activeWorkflowView === "graph"' in panel
        or "activeWorkflowView === 'graph'" in panel
    )
    assert ':events="timeline"' in panel
    assert "Hospital Agent Coverage Graph" in graph
    assert "graphNodes" in graph
    assert "graphEdges" in graph
    assert "@node-click" in graph
    assert "selectedSummary" in graph
    assert "Decision labels" in graph
    assert "Decision nodes" not in graph
    assert "addDecisionNodes" not in graph
    assert "choice" in graph
    assert "status" in graph
    assert "agent_completed" in graph
    assert "decision_made" in graph
    assert "tool_invoked" in graph
    assert "tool_skipped" in graph
    assert 'mode: "parallel"' in graph
    assert "edge-mode-parallel" in styles
    assert "selected_branch" in graph
    assert "selected_branches" in graph
    assert "collectEdgeDecisionLabels" in graph
    assert "journeyStageDefinitions" not in graph


def test_frontend_graph_distinguishes_selected_skipped_tool_and_parallel_paths() -> None:
    graph = Path("frontend/src/components/AgentWorkflowGraph.vue").read_text(encoding="utf-8")
    styles = Path("frontend/src/styles.css").read_text(encoding="utf-8")

    assert "graph-legend" in graph
    assert "Actual workflow" in graph
    assert "Available but not taken" in graph
    assert "Explicitly skipped" in graph
    assert "Tool selected" in graph
    assert "Tool skipped" in graph
    assert "Tool unavailable" in graph
    assert "Tool nodes" in graph
    assert "Unused branches" in graph
    assert "skippedBranchTargets" in graph
    assert "skipped_branches" in graph
    assert "edgeKind" in graph
    assert "edge-selected" in graph
    assert "edge-skipped" in graph
    assert "edge-tool-selected" in graph
    assert "edge-tool-skipped" in graph
    assert "edge-tool-unavailable" in graph
    assert "practitioner_assignment" in graph
    assert "resource_reservation" in graph
    assert "exam_scheduling" in graph
    assert "emergency_encounter" in graph
    assert "emergency_readiness_update" in graph
    assert "Practitioner Assignment" in graph
    assert "Resource Reservation" in graph
    assert "Exam Scheduling" in graph
    assert "Emergency Encounter" in graph
    assert "Readiness Update" in graph
    assert "edge-mode-parallel" in styles
    assert "graph-node-${status}" in graph
    assert ".graph-legend" in styles
    assert ".workflow-flow .edge-available" in styles
    assert ".workflow-flow .edge-skipped" in styles
    assert ".workflow-flow .edge-tool-unavailable" in styles
    assert ".workflow-flow .graph-node-skipped" in styles


def test_frontend_timeline_empty_state_does_not_show_legacy_live_flow() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/WorkflowDisplayPanel.vue").read_text(encoding="utf-8")

    assert "liveStages" not in app
    assert "liveFlowTitle" not in app
    assert "stage-list" not in panel
    assert "stage-item" not in panel
    assert "Patient Intake" not in panel
    assert "timeline-empty-state" in panel


def test_frontend_timeline_nodes_surface_event_meaning_for_manual_review() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/WorkflowDisplayPanel.vue").read_text(encoding="utf-8")
    timeline = Path("frontend/src/components/AgentTimeline.vue").read_text(encoding="utf-8")

    assert "WorkflowDisplayPanel" in app
    assert "AgentTimeline" in panel
    assert "eventLabel(event)" in timeline
    assert "eventSummary(event)" in timeline
    assert "formatDuration(event.duration_ms)" in timeline
    assert "timeline-targets" in timeline


def test_frontend_fetches_and_displays_patient_history_summary() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    record_pane = Path("frontend/src/components/ClinicalRecordPane.vue").read_text(encoding="utf-8")

    assert "ClinicalRecordPane" in app
    assert "Patient History" in record_pane
    assert "`/api/records/patients/${patientId}/history`" in app
    assert "patientHistory" in app
    assert "recentEncounters" in record_pane
    assert "allergies" in record_pane
    assert "currentMedications" in record_pane
    assert "history-encounters" in record_pane
    assert "recentEncounters.length" in record_pane
    assert "formatTime(encounter.updatedAt)" in record_pane
    assert "historyListText(encounter.selectedSpecialties)" in record_pane


def test_frontend_record_pane_renders_markdown_report_and_record_json() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    record_pane = Path("frontend/src/components/ClinicalRecordPane.vue").read_text(encoding="utf-8")

    assert 'import { normalizeReportMarkdownText } from "./reportFormatting"' in app
    assert "normalizeReportMarkdownText(finalReportText.value" in app
    assert "const markdownPreferredKeys = [\"markdown\", \"report_markdown\", \"content\", \"text\", \"report_summary\", \"summary\"]" in app
    assert "const data = value.data" in app
    assert "extractFinalReportText(data)" in app
    assert "Final Report" in record_pane
    assert "v-html=\"finalReportHtml\"" in record_pane
    assert "Record JSON" in record_pane
    assert "compactRecordJson" in record_pane


def test_frontend_history_report_excerpts_render_markdown_not_plain_text() -> None:
    record_pane = Path("frontend/src/components/ClinicalRecordPane.vue").read_text(encoding="utf-8")
    formatter = Path("frontend/src/reportFormatting.ts").read_text(encoding="utf-8")

    assert 'import MarkdownIt from "markdown-it"' in record_pane
    assert 'import { renderReportMarkdown } from "../reportFormatting"' in record_pane
    assert "historyReportExcerptHtml" in record_pane
    assert "encounterReportExcerptHtml(encounter)" in record_pane
    assert "renderReportMarkdown(markdown, value)" in record_pane
    assert "normalizeReportMarkdownText" in formatter
    assert "extractStructuredReportText" in formatter
    assert "looksLikeJsonReport" in formatter
    assert "unwrapJsonCodeFence" in formatter
    assert 'opening === "```json"' in formatter
    assert 'v-html="historyReportExcerptHtml"' in record_pane
    assert 'v-html="encounterReportExcerptHtml(encounter)"' in record_pane
    assert "{{ patientHistory.lastFinalReports[0]" not in record_pane
    assert "{{ encounter.reportExcerpt }}" not in record_pane
