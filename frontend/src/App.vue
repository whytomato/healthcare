<template>
  <main class="app-shell">
    <EncounterSidebar
      :form="form"
      :demo-cases="demoCases"
      :tasks="tasks"
      :selected-task-id="selectedTaskId"
      :is-creating="isCreating"
      @create-encounter="createEncounter"
      @refresh-tasks="refreshTasks"
      @apply-demo-case="applyDemoCase"
      @select-task="selectTask"
    />

    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Current Encounter</p>
          <h2>{{ selectedTaskId ? shortId(selectedTaskId) : "Waiting for an encounter" }}</h2>
        </div>
        <div class="topbar-actions">
          <span class="service-pill" :class="serviceStatus.encounter ? 'ok' : 'warn'">
            <CircleDot :size="13" />
            Encounter
          </span>
          <span class="service-pill" :class="serviceStatus.record ? 'ok' : 'warn'">
            <CircleDot :size="13" />
            Records
          </span>
          <button class="ghost-button" :disabled="!selectedTaskId || isCurrentTaskPolling" @click="pollSelectedTask">
            <RefreshCw :class="{ spin: isCurrentTaskPolling }" :size="18" />
          </button>
        </div>
      </header>

      <section v-if="errorMessage" class="alert">
        <TriangleAlert :size="18" />
        <span>{{ errorMessage }}</span>
      </section>

      <EmergencySurgePanel
        v-model:count="surgeCount"
        :is-running="isSurgeRunning"
        :results="surgeResults"
        @run-surge="runEmergencySurge"
        @select-task="selectTask"
      />

      <section class="metrics-grid">
        <article class="metric">
          <span>Status</span>
          <strong>{{ currentTask?.status || "-" }}</strong>
        </article>
        <article class="metric">
          <span>Patient</span>
          <strong>{{ currentTask?.patientId || "-" }}</strong>
        </article>
        <article class="metric">
          <span>Doctor</span>
          <strong>{{ currentTask?.doctorId || "-" }}</strong>
        </article>
        <article class="metric">
          <span>Specialties</span>
          <strong>{{ selectedSpecialtiesText }}</strong>
        </article>
      </section>

      <HospitalJourneyOverview
        :stages="journeyStages"
        :progress-text="journeyProgressText"
        :progress-percent="journeyProgressPercent"
        :stats="workflowStats"
      />

      <WorkflowDisplayPanel
        :timeline="timeline"
        :timeline-caption="timelineCaption"
        :workflow-name="workflowName"
        :selected-task-id="selectedTaskId"
        :executed-path="executedPath"
        :displayed-decisions="displayedDecisions"
      />
    </section>

    <ClinicalRecordPane
      :patient-history="patientHistory"
      :clinical-record="clinicalRecord"
      :current-task-updated-at="currentTask?.updatedAt"
      :disposition-text="dispositionText"
      :final-report-text="finalReportText"
      :final-report-html="finalReportHtml"
      :compact-record-json="compactRecordJson"
    />
  </main>
</template>

<script setup lang="ts">
import MarkdownIt from "markdown-it";
import { computed, onMounted, reactive, ref } from "vue";
import ClinicalRecordPane from "./components/ClinicalRecordPane.vue";
import EmergencySurgePanel from "./components/EmergencySurgePanel.vue";
import EncounterSidebar from "./components/EncounterSidebar.vue";
import HospitalJourneyOverview from "./components/HospitalJourneyOverview.vue";
import WorkflowDisplayPanel from "./components/WorkflowDisplayPanel.vue";
import { demoCases, emergencySurgeTemplate } from "./demoCases";
import { normalizeReportMarkdownText } from "./reportFormatting";
import {
  extractSurgePractitionerAssignment,
  extractSurgeReadiness
} from "./surgeExtractors";
import type {
  AiTask,
  ClinicalRecord,
  DemoCase,
  EncounterForm,
  PatientHistorySummary,
  SurgeResult,
  TaskStatus,
  TimelineEvent,
  WorkflowDecision,
  WorkflowProgressEvent,
  WorkflowResult
} from "./types";
import { CircleDot, RefreshCw, TriangleAlert } from "lucide-vue-next";

const terminalStatuses = new Set<TaskStatus>(["COMPLETED", "FAILED", "NEEDS_DATA"]);
const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true
});

const journeyStageDefinitions = [
  {
    key: "registration",
    label: "Registration",
    detail: "Registration, history lookup, intake, and vital signs.",
    agents: ["registration_agent", "intake_agent", "nurse_vitals_agent"]
  },
  {
    key: "triage",
    label: "Triage",
    detail: "Appointment priority, red-flag recognition, and urgency classification.",
    agents: ["appointment_agent", "triage_nurse_agent"]
  },
  {
    key: "routing",
    label: "Routing",
    detail: "Department route and specialist branch selection.",
    agents: ["department_router_agent", "specialist_router_agent"]
  },
  {
    key: "consultation",
    label: "Consultation",
    detail: "Emergency physician, general practitioner, and parallel specialists.",
    agents: [
      "emergency_physician_agent",
      "general_practitioner_agent",
      "respiratory_specialist_agent",
      "cardiology_specialist_agent",
      "infectious_disease_specialist_agent",
      "neurology_specialist_agent"
    ]
  },
  {
    key: "diagnostics",
    label: "Exam Review Loop",
    detail: "Ordering clinicians request exams; lab and imaging results return for clinician review.",
    agents: ["lab_result_interpreter_agent", "imaging_interpreter_agent", "ordering_clinician_review_agent"]
  },
  {
    key: "medication",
    label: "Medication",
    detail: "Pharmacy safety review and medication planning.",
    agents: ["pharmacy_safety_agent", "medication_plan_agent"]
  },
  {
    key: "disposition",
    label: "Disposition",
    detail: "Follow-up, admission, human review, and care coordination.",
    agents: ["care_plan_agent", "follow_up_agent", "disposition_coordinator_agent", "admission_coordinator_agent"]
  },
  {
    key: "report",
    label: "Report",
    detail: "Final hospital workflow report.",
    agents: ["final_hospital_report_agent"]
  }
] as const;

const form = reactive<EncounterForm>({
  patientId: "p001",
  doctorId: "d001",
  language: "zh-CN",
  caseText: "A 67-year-old male has fever, productive cough, chest discomfort and confusion."
});

const tasks = ref<AiTask[]>([]);
const currentTask = ref<AiTask | null>(null);
const clinicalRecord = ref<ClinicalRecord | null>(null);
const patientHistory = ref<PatientHistorySummary | null>(null);
const progressEvents = ref<TimelineEvent[]>([]);
const selectedTaskId = ref("");
const errorMessage = ref("");
const isCreating = ref(false);
const pollingTaskId = ref<string | null>(null);
const surgeCount = ref(5);
const isSurgeRunning = ref(false);
const surgeResults = ref<SurgeResult[]>([]);
const serviceStatus = reactive({
  encounter: false,
  record: false
});
let pollGeneration = 0;

const workflowResult = computed<WorkflowResult | null>(() => {
  return clinicalRecord.value?.rawResult || null;
});

const finalTimeline = computed<TimelineEvent[]>(() => {
  return clinicalRecord.value?.handoffTimeline || workflowResult.value?.handoff_timeline || [];
});

const timeline = computed<TimelineEvent[]>(() => {
  return mergeTimelineEvents(progressEvents.value, finalTimeline.value);
});

const progressCompletedAgents = computed<string[]>(() => {
  const seen = new Set<string>();
  return progressEvents.value
    .filter((event) => event.event_type === "agent_completed" && event.agent)
    .map((event) => event.agent as string)
    .filter((agent) => {
      if (seen.has(agent)) {
        return false;
      }
      seen.add(agent);
      return true;
    });
});

const executedPath = computed<string[]>(() => {
  return clinicalRecord.value?.executedPath || workflowResult.value?.executed_path || progressCompletedAgents.value;
});

const workflowDecisions = computed<WorkflowDecision[]>(() => {
  return clinicalRecord.value?.workflowDecisions || workflowResult.value?.workflow_decisions || [];
});

const displayedDecisions = computed<WorkflowDecision[]>(() => {
  const timelineDecisions = timeline.value
    .filter((event) => event.event_type === "decision_made" && event.decision)
    .map((event) => ({
      decision: event.decision,
      made_by: event.agent,
      agent: event.agent,
      reason: event.reason
    }));
  const seen = new Set<string>();
  return [...timelineDecisions, ...workflowDecisions.value].filter((decision) => {
    const key = `${decision.made_by || decision.agent || "workflow"}:${decision.decision}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
});

const selectedSpecialtiesText = computed(() => {
  const specialties = clinicalRecord.value?.selectedSpecialties || workflowResult.value?.selected_specialties || [];
  return specialties.length ? specialties.join(", ") : "-";
});

const workflowName = computed(() => workflowResult.value?.workflow || "agent_hospital_lite");

const isCurrentTaskPolling = computed(() => {
  return Boolean(selectedTaskId.value && pollingTaskId.value === selectedTaskId.value);
});

const timelineCaption = computed(() => {
  if (timeline.value.length) {
    return `${timeline.value.length} events / ${timelineAgentCount.value} agents`;
  }
  if (selectedTaskId.value) {
    return `Live polling / ${currentTask.value?.status || "UNKNOWN"}`;
  }
  return "Waiting for encounter";
});

const timelineAgentCount = computed(() => {
  if (executedPath.value.length) {
    return executedPath.value.length;
  }
  return new Set(timeline.value.map((event) => event.agent).filter(Boolean)).size;
});

const completedAgentSet = computed(() => {
  return new Set([
    ...executedPath.value,
    ...timeline.value
      .filter((event) => event.event_type === "agent_completed" && event.agent)
      .map((event) => event.agent as string)
  ]);
});

const journeyStages = computed(() => {
  const completed = completedAgentSet.value;
  const firstWaitingIndex = journeyStageDefinitions.findIndex((stage) => {
    return !stage.agents.some((agent) => completed.has(agent));
  });
  const activeIndex = selectedTaskId.value
    ? firstWaitingIndex === -1
      ? journeyStageDefinitions.length - 1
      : firstWaitingIndex
    : -1;

  return journeyStageDefinitions.map((stage, index) => {
    const isDone = stage.agents.some((agent) => completed.has(agent));
    return {
      ...stage,
      state: isDone ? "done" : index === activeIndex ? "active" : "waiting"
    };
  });
});

const journeyProgressPercent = computed(() => {
  if (!journeyStages.value.length) {
    return 0;
  }
  const done = journeyStages.value.filter((stage) => stage.state === "done").length;
  return Math.round((done / journeyStages.value.length) * 100);
});

const journeyProgressText = computed(() => {
  if (!selectedTaskId.value) {
    return "Create or select a patient encounter to watch the hospital workflow.";
  }
  const activeStage = journeyStages.value.find((stage) => stage.state === "active");
  if (journeyProgressPercent.value === 100) {
    return "Hospital multi-agent workflow completed; final record is ready for review.";
  }
  return activeStage ? `Current stage: ${activeStage.label} / ${activeStage.detail}` : "Syncing workflow progress.";
});

const workflowStats = computed(() => {
  return {
    agentEvents: timeline.value.filter((event) => event.event_type === "agent_completed").length,
    decisionEvents: timeline.value.filter((event) => event.event_type === "decision_made").length,
    parallelBranches: timeline.value.filter((event) => event.event_type?.includes("parallel")).length
  };
});

const finalReportText = computed(() => {
  const result = workflowResult.value;
  return extractFirstFinalReportText([
    clinicalRecord.value?.finalReport,
    result?.final_report,
    result?.agent_results?.find((item) => item.agent === "final_hospital_report_agent"),
    result?.agent_results?.find((item) => item.agent === "final_hospital_report_agent")?.data
  ]);
});

const finalReportHtml = computed(() => markdown.render(normalizeReportMarkdownText(finalReportText.value, "")));

const dispositionText = computed(() => {
  const disposition = workflowResult.value?.disposition;
  if (!disposition) return "-";
  if (typeof disposition === "string") return disposition;
  if (typeof disposition === "object") {
    const value = disposition as Record<string, unknown>;
    return String(value.disposition || value.decision || value.status || "-");
  }
  return String(disposition);
});

const compactRecordJson = computed(() => {
  if (!clinicalRecord.value) return "{}";
  return JSON.stringify(
    {
      taskId: clinicalRecord.value.taskId,
      status: clinicalRecord.value.status,
      executedPath: clinicalRecord.value.executedPath,
      selectedSpecialties: clinicalRecord.value.selectedSpecialties,
      updatedAt: clinicalRecord.value.updatedAt
    },
    null,
    2
  );
});

onMounted(async () => {
  await Promise.all([checkHealth(), refreshTasks()]);
});

async function createEncounter() {
  isCreating.value = true;
  errorMessage.value = "";
  try {
    const task = await createWorkflowTask({
      caseText: form.caseText,
      patientId: form.patientId,
      doctorId: form.doctorId,
      language: form.language
    });
    await focusTask(task);
    await refreshTasks();
    void startTaskPolling(task.taskId);
  } catch (error) {
    setError(error);
  } finally {
    isCreating.value = false;
  }
}

function applyDemoCase(demoCase: DemoCase) {
  form.patientId = demoCase.patientId;
  form.doctorId = demoCase.doctorId;
  form.language = demoCase.language;
  form.caseText = demoCase.caseText;
}

async function runEmergencySurge(count: number) {
  isSurgeRunning.value = true;
  errorMessage.value = "";
  const batchId = Date.now();
  const surgeInputs = Array.from({ length: count }, (_, index) => ({
    caseText: emergencySurgeTemplate.caseText,
    patientId: `${emergencySurgeTemplate.patientId}-${batchId}-${index + 1}`,
    doctorId: emergencySurgeTemplate.doctorId,
    language: emergencySurgeTemplate.language
  }));
  surgeResults.value = surgeInputs.map((item) => ({
    patientId: item.patientId,
    status: "running",
    message: "Submitting"
  }));

  try {
    const submissions = await Promise.allSettled(surgeInputs.map((item) => createWorkflowTask(item)));
    const createdTasks: AiTask[] = [];
    surgeResults.value = submissions.map((outcome, index) => {
      const input = surgeInputs[index];
      if (outcome.status === "fulfilled") {
        createdTasks.push(outcome.value);
        return {
          patientId: input.patientId,
          taskId: outcome.value.taskId,
          status: "running",
          taskStatus: outcome.value.status,
          message: "Submitted"
        };
      }
      return {
        patientId: input.patientId,
        status: "failed",
        message: outcome.reason instanceof Error ? outcome.reason.message : String(outcome.reason)
      };
    });

    await refreshTasks();
    if (createdTasks[0]) {
      await focusTask(createdTasks[0]);
      void startTaskPolling(createdTasks[0].taskId);
    }
    await Promise.allSettled(createdTasks.map((task) => pollSurgeTask(task)));
    await refreshTasks();
  } catch (error) {
    setError(error);
  } finally {
    isSurgeRunning.value = false;
  }
}

async function createWorkflowTask(input: { caseText: string; patientId: string; doctorId: string; language: string }) {
  return requestJson<AiTask>("/api/ai/symptom-query", {
    method: "POST",
    body: JSON.stringify({
      caseText: input.caseText,
      question: "Run hospital consultation workflow",
      patientId: input.patientId,
      doctorId: input.doctorId,
      language: input.language
    })
  });
}

async function focusTask(task: AiTask) {
  selectedTaskId.value = task.taskId;
  currentTask.value = task;
  clinicalRecord.value = null;
  patientHistory.value = null;
  progressEvents.value = [];
  await loadPatientHistory(task.patientId);
}

async function pollSurgeTask(task: AiTask) {
  const deadline = Date.now() + 300000;
  while (Date.now() < deadline) {
    const latest = await requestJson<AiTask>(`/api/ai/tasks/${task.taskId}`);
    updateSurgeResult(task.taskId, {
      status: terminalStatuses.has(latest.status) ? "completed" : "running",
      taskStatus: latest.status
    });
    if (terminalStatuses.has(latest.status)) {
      try {
        const record = await requestJson<ClinicalRecord>(`/api/records/${task.taskId}`);
        updateSurgeResult(task.taskId, {
          status: latest.status === "COMPLETED" ? "completed" : "failed",
          readiness: extractSurgeReadiness(record),
          practitionerAssignment: extractSurgePractitionerAssignment(record),
          message: latest.errorMessage
        });
      } catch (error) {
        updateSurgeResult(task.taskId, {
          status: "failed",
          message: error instanceof Error ? error.message : String(error)
        });
      }
      return;
    }
    await delay(1200);
  }
  updateSurgeResult(task.taskId, { status: "failed", message: "Timed out waiting for task completion" });
}

function updateSurgeResult(taskId: string, patch: Partial<SurgeResult>) {
  surgeResults.value = surgeResults.value.map((result) => {
    return result.taskId === taskId ? { ...result, ...patch } : result;
  });
}

async function refreshTasks() {
  try {
    tasks.value = await requestJson<AiTask[]>("/api/ai/tasks");
    tasks.value.sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""));
  } catch (error) {
    setError(error);
  }
}

async function selectTask(taskId: string) {
  selectedTaskId.value = taskId;
  currentTask.value = tasks.value.find((task) => task.taskId === taskId) || null;
  clinicalRecord.value = null;
  patientHistory.value = null;
  await loadPatientHistory(currentTask.value?.patientId);
  progressEvents.value = [];
  await startTaskPolling(taskId);
}

async function pollSelectedTask() {
  if (!selectedTaskId.value) {
    return;
  }
  await startTaskPolling(selectedTaskId.value);
}

async function startTaskPolling(taskId: string) {
  const runId = ++pollGeneration;
  pollingTaskId.value = taskId;
  errorMessage.value = "";
  try {
    const deadline = Date.now() + 300000;
    while (Date.now() < deadline && isActivePollingRun(taskId, runId)) {
      const task = await requestJson<AiTask>(`/api/ai/tasks/${taskId}`);
      if (!isActivePollingRun(taskId, runId)) {
        return;
      }
      currentTask.value = task;
      await loadPatientHistory(task.patientId);
      await loadProgress(task.taskId);
      if (terminalStatuses.has(task.status)) {
        await loadClinicalRecord(task.taskId);
        await loadProgress(task.taskId);
        await refreshTasks();
        return;
      }
      await delay(800);
    }
    errorMessage.value = "Task did not finish within five minutes; refresh manually to continue.";
  } catch (error) {
    if (isActivePollingRun(taskId, runId)) {
      setError(error);
    }
  } finally {
    if (pollGeneration === runId) {
      pollingTaskId.value = null;
    }
  }
}

async function loadClinicalRecord(taskId: string) {
  try {
    const record = await requestJson<ClinicalRecord>(`/api/records/${taskId}`);
    if (selectedTaskId.value === taskId) {
      clinicalRecord.value = record;
    }
  } catch {
    if (selectedTaskId.value === taskId) {
      clinicalRecord.value = null;
    }
  }
}

async function loadPatientHistory(patientId?: string) {
  if (!patientId) {
    patientHistory.value = null;
    return;
  }
  try {
    patientHistory.value = await requestJson<PatientHistorySummary>(`/api/records/patients/${patientId}/history`);
  } catch {
    patientHistory.value = null;
  }
}

async function loadProgress(taskId: string) {
  try {
    const events = (await requestJson<WorkflowProgressEvent[]>(`/api/ai/tasks/${taskId}/progress`)).map(toTimelineEvent);
    if (selectedTaskId.value !== taskId) {
      return;
    }
    if ((events.length || !progressEvents.value.length) && events.length >= progressEvents.value.length) {
      progressEvents.value = events;
    }
  } catch {
    if (selectedTaskId.value === taskId && !progressEvents.value.length) {
      progressEvents.value = [];
    }
  }
}

function isActivePollingRun(taskId: string, runId: number) {
  return pollGeneration === runId && selectedTaskId.value === taskId;
}

async function checkHealth() {
  const [encounter, record] = await Promise.allSettled([
    requestJson<{ status: string }>("/api/ai/health"),
    requestJson<{ status: string }>("/api/records/health")
  ]);
  serviceStatus.encounter = encounter.status === "fulfilled";
  serviceStatus.record = record.status === "fulfilled";
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} for ${url}`);
  }
  return (await response.json()) as T;
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function setError(error: unknown) {
  errorMessage.value = error instanceof Error ? error.message : String(error);
}

function shortId(taskId: string) {
  return taskId ? `${taskId.slice(0, 8)}...${taskId.slice(-4)}` : "-";
}

function toTimelineEvent(event: WorkflowProgressEvent): TimelineEvent {
  return {
    event_type: event.eventType,
    agent: event.agent,
    target_agents: event.targetAgents,
    decision: event.decision,
    decision_scope: event.decisionScope,
    reason: event.reason,
    payload: event.payload,
    duration_ms: event.durationMs ?? undefined,
    event_index: event.eventIndex
  };
}

function mergeTimelineEvents(progress: TimelineEvent[], finalEvents: TimelineEvent[]): TimelineEvent[] {
  if (!progress.length) {
    return finalEvents;
  }
  if (!finalEvents.length) {
    return progress;
  }
  const merged = new Map<string, TimelineEvent>();
  for (const event of [...progress, ...finalEvents]) {
    merged.set(timelineIdentity(event), event);
  }
  return [...merged.values()].sort((a, b) => (a.event_index ?? 0) - (b.event_index ?? 0));
}

function timelineIdentity(event: TimelineEvent) {
  if (event.event_index !== undefined) {
    return String(event.event_index);
  }
  return `${event.event_type || "event"}:${event.agent || "workflow"}:${event.decision || ""}:${event.target_agents?.join(",") || ""}`;
}

function extractFirstFinalReportText(candidates: unknown[]): string {
  for (const candidate of candidates) {
    const text = extractFinalReportText(candidate);
    if (text.trim()) {
      return text;
    }
  }
  return "";
}

function extractFinalReportText(report: unknown): string {
  if (typeof report === "string") {
    return report;
  }
  if (!report || typeof report !== "object") {
    return "";
  }
  const value = report as Record<string, unknown>;
  const data = value.data;
  if (data && typeof data === "object") {
    const text = extractFinalReportText(data);
    if (text.trim()) {
      return text;
    }
  }
  const markdownPreferredKeys = ["markdown", "report_markdown", "content", "text", "report_summary", "summary"];
  for (const key of markdownPreferredKeys) {
    if (typeof value[key] === "string") {
      return value[key] as string;
    }
  }
  if (Array.isArray(value.findings) && typeof value.findings[0] === "string") {
    return value.findings[0];
  }
  return "";
}

</script>
