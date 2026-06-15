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
    assert '"report_summary", "summary", "markdown", "content", "text"' in app
    assert "markdown.render(finalReportText.value)" in app


def test_frontend_exposes_demo_cases_for_stable_manual_flow_demos() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")

    assert "Demo Cases" in app
    assert "急诊多专科" in app
    assert "普通门诊" in app
    assert "低风险随访" in app
    assert "@click=\"applyDemoCase(demoCase)\"" in app


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
    assert "liveStages" in app


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


def test_frontend_record_pane_renders_markdown_report_and_record_json() -> None:
    app = Path("frontend/src/App.vue").read_text(encoding="utf-8")
    record_pane = Path("frontend/src/components/ClinicalRecordPane.vue").read_text(encoding="utf-8")

    assert "markdown.render(finalReportText.value)" in app
    assert "Final Report" in record_pane
    assert "v-html=\"finalReportHtml\"" in record_pane
    assert "Record JSON" in record_pane
    assert "compactRecordJson" in record_pane
