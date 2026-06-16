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
        <div class="markdown-report history-markdown" v-html="historyReportExcerptHtml" />
      </div>
      <p v-else class="muted">No prior clinical summary available.</p>

      <div v-if="patientHistory?.recentEncounters.length" class="history-encounters">
        <span>Recent encounters</span>
        <article v-for="encounter in patientHistory.recentEncounters" :key="encounter.taskId">
          <strong>{{ encounter.disposition || encounter.status || "Prior encounter" }}</strong>
          <small>{{ formatTime(encounter.updatedAt) }}</small>
          <p v-if="encounter.selectedSpecialties?.length">
            Specialties: {{ historyListText(encounter.selectedSpecialties) }}
          </p>
          <div
            v-if="encounter.reportExcerpt"
            class="markdown-report history-markdown"
            v-html="encounterReportExcerptHtml(encounter)"
          />
        </article>
      </div>
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
import MarkdownIt from "markdown-it";
import { computed } from "vue";
import { renderReportMarkdown } from "../reportFormatting";

type ClinicalRecord = {
  status?: string;
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
  recentEncounters: PatientHistoryEncounter[];
  allergies: string[];
  currentMedications: string[];
  previousDispositions: string[];
  lastFinalReports: string[];
};

const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true
});

const props = defineProps<{
  patientHistory: PatientHistorySummary | null;
  clinicalRecord: ClinicalRecord | null;
  currentTaskUpdatedAt?: string;
  dispositionText: string;
  finalReportText: string;
  finalReportHtml: string;
  compactRecordJson: string;
}>();

const historyReportExcerptHtml = computed(() => {
  return renderMarkdown(props.patientHistory?.lastFinalReports?.[0]);
});

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

function encounterReportExcerptHtml(encounter: PatientHistoryEncounter) {
  return renderMarkdown(encounter.reportExcerpt);
}

function renderMarkdown(value?: string) {
  return renderReportMarkdown(markdown, value);
}
</script>
