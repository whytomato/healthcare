<template>
  <aside class="record-pane">
    <section class="panel history-panel">
      <div class="panel-title">
        <History :size="18" />
        <h2>Patient History</h2>
      </div>
      <dl>
        <div>
          <dt>Prior Encounters</dt>
          <dd>{{ patientHistory?.recentEncounters.length ?? 0 }}</dd>
        </div>
        <div>
          <dt>Allergies</dt>
          <dd>{{ historyListText(patientHistory?.allergies) }}</dd>
        </div>
        <div>
          <dt>Medications</dt>
          <dd>{{ historyListText(patientHistory?.currentMedications) }}</dd>
        </div>
        <div>
          <dt>Previous Disposition</dt>
          <dd>{{ historyListText(patientHistory?.previousDispositions) }}</dd>
        </div>
      </dl>
      <div v-if="patientHistory?.lastFinalReports.length" class="history-excerpts">
        <span>Latest report excerpt</span>
        <p>{{ patientHistory.lastFinalReports[0] }}</p>
      </div>
      <p v-else class="muted">No prior clinical summary available.</p>
    </section>

    <section class="panel record-summary">
      <div class="panel-title">
        <ClipboardPlus :size="18" />
        <h2>Clinical Record</h2>
      </div>
      <dl>
        <div>
          <dt>Record Status</dt>
          <dd>{{ clinicalRecord?.status || "-" }}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd>{{ formatTime(clinicalRecord?.updatedAt || currentTaskUpdatedAt) }}</dd>
        </div>
        <div>
          <dt>Disposition</dt>
          <dd>{{ dispositionText }}</dd>
        </div>
      </dl>
    </section>

    <section class="panel report-panel">
      <div class="panel-title">
        <FileText :size="18" />
        <h2>Final Report</h2>
      </div>
      <div v-if="finalReportText" class="markdown-report" v-html="finalReportHtml" />
      <p v-else class="muted">Final report appears after workflow completion.</p>
    </section>

    <section class="panel raw-panel">
      <div class="panel-title">
        <Database :size="18" />
        <h2>Record JSON</h2>
      </div>
      <pre>{{ compactRecordJson }}</pre>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { ClipboardPlus, Database, FileText, History } from "lucide-vue-next";

type WorkflowDecision = {
  decision?: string;
  made_by?: string;
  agent?: string;
  reason?: string;
};

type TimelineEvent = {
  event_type?: string;
  agent?: string;
  target_agents?: string[];
  decision?: string;
  decision_scope?: string;
  reason?: string;
  payload?: Record<string, unknown>;
  duration_ms?: number;
  event_index?: number;
};

type WorkflowResult = {
  workflow?: string;
  executed_path?: string[];
  workflow_decisions?: WorkflowDecision[];
  selected_specialties?: string[];
  disposition?: unknown;
  care_pathway?: unknown;
  ai_consultation?: unknown;
  final_report?: Record<string, unknown>;
  handoff_timeline?: TimelineEvent[];
  agent_results?: Record<string, unknown>[];
};

type ClinicalRecord = {
  taskId: string;
  status: string;
  executedPath?: string[];
  workflowDecisions?: WorkflowDecision[];
  handoffTimeline?: TimelineEvent[];
  selectedSpecialties?: string[];
  carePathway?: unknown;
  aiConsultation?: unknown;
  finalReport?: Record<string, unknown>;
  rawResult?: WorkflowResult;
  errorMessage?: string;
  createdAt?: string;
  updatedAt?: string;
};

type PatientHistoryEncounter = {
  taskId: string;
  status: string;
  updatedAt?: string;
  selectedSpecialties?: string[];
  disposition?: string;
  reportExcerpt?: string;
};

type PatientHistorySummary = {
  patientId: string;
  recentEncounters: PatientHistoryEncounter[];
  knownConditions: string[];
  allergies: string[];
  currentMedications: string[];
  previousDispositions: string[];
  lastFinalReports: string[];
};

defineProps<{
  patientHistory: PatientHistorySummary | null;
  clinicalRecord: ClinicalRecord | null;
  currentTaskUpdatedAt?: string;
  dispositionText: string;
  finalReportText: string;
  finalReportHtml: string;
  compactRecordJson: string;
}>();

function formatTime(value?: string) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function historyListText(values?: string[]) {
  return values?.length ? values.join(", ") : "-";
}
</script>
