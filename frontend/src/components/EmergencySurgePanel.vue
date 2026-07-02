<template>
  <section class="surge-panel">
    <div class="surge-head">
      <div class="surge-copy">
        <p class="eyebrow">Emergency Surge Scenario</p>
        <h3>Concurrent ER resource contention</h3>
        <p>
          Submit several real emergency workflow tasks at once. Inspect each completed run for
          resource_reservation readinessStatus and practitioner_assignment staffing.
        </p>
      </div>

      <div class="surge-controls">
        <label>
          <span>Patients</span>
          <input
            :value="count"
            type="number"
            min="2"
            max="8"
            @input="onCountInput"
          />
        </label>
        <button class="primary-button" :disabled="isRunning" @click="emit('run-surge', count)">
          <Activity v-if="isRunning" class="spin" :size="18" />
          <Zap v-else :size="18" />
          <span>{{ isRunning ? "Running surge" : "Run surge" }}</span>
        </button>
      </div>
    </div>

    <div v-if="results.length" class="surge-summary" aria-label="Surge Run Summary">
      <span>Surge Run Summary</span>
      <strong><CheckCircle2 :size="15" /> Completed {{ surgeSummary.completed }}</strong>
      <strong><Bed :size="15" /> Resource limited {{ surgeSummary.resourceLimited }}</strong>
      <strong><UserRoundCheck :size="15" /> Staff limited {{ surgeSummary.staffLimited }}</strong>
      <strong><AlertTriangle :size="15" /> Failed {{ surgeSummary.failed }}</strong>
    </div>

    <div
      v-if="results.length"
      class="surge-results"
      aria-label="resource_reservation and practitioner_assignment surge results"
    >
      <button
        v-for="result in results"
        :key="result.patientId"
        class="surge-result"
        :class="result.readiness?.readinessStatus || result.status"
        @click="result.taskId && emit('select-task', result.taskId)"
      >
        <span class="surge-result-head">
          <strong>{{ result.patientId }}</strong>
          <small>{{ result.taskId || result.message || "not submitted" }}</small>
        </span>
        <span class="resource-status-grid">
          <em class="status-chip" :class="statusTone(result.readiness?.readinessStatus || result.taskStatus || result.status)">
            <Bed :size="14" />
            Resources {{ result.readiness?.readinessStatus || result.taskStatus || result.status }}
          </em>
          <em class="status-chip" :class="statusTone(result.practitionerAssignment?.assignmentStatus || result.taskStatus || result.status)">
            <UserRoundCheck :size="14" />
            Staff {{ result.practitionerAssignment?.assignmentStatus || result.taskStatus || result.status }}
          </em>
        </span>
        <span v-if="result.readiness || result.practitionerAssignment" class="surge-result-detail">
          <small v-if="result.readiness">
            reserved {{ result.readiness.reservedResources.length }} /
            unavailable {{ result.readiness.unavailableResources.length }}
          </small>
          <small v-if="result.practitionerAssignment">
            assignedPractitioners {{ result.practitionerAssignment.assignedPractitioners.length }} /
            unavailableSpecialties {{ result.practitionerAssignment.unavailableSpecialties.length }}
          </small>
        </span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Activity, AlertTriangle, Bed, CheckCircle2, UserRoundCheck, Zap } from "lucide-vue-next";
import type { SurgeResult } from "../types";

const props = defineProps<{
  count: number;
  isRunning: boolean;
  results: SurgeResult[];
}>();

const emit = defineEmits<{
  "update:count": [count: number];
  "run-surge": [count: number];
  "select-task": [taskId: string];
}>();

function onCountInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  emit("update:count", Number.isFinite(value) ? Math.min(Math.max(value, 2), 8) : props.count);
}

const surgeSummary = computed(() => {
  return props.results.reduce(
    (summary, result) => {
      const resourceStatus = result.readiness?.readinessStatus;
      const staffStatus = result.practitionerAssignment?.assignmentStatus;
      if (result.status === "completed") summary.completed += 1;
      if (resourceStatus === "partial" || resourceStatus === "unavailable") summary.resourceLimited += 1;
      if (staffStatus === "partial" || staffStatus === "unavailable") summary.staffLimited += 1;
      if (result.status === "failed") summary.failed += 1;
      return summary;
    },
    { completed: 0, resourceLimited: 0, staffLimited: 0, failed: 0 }
  );
});

function statusTone(status?: string) {
  if (status === "ready" || status === "assigned" || status === "COMPLETED" || status === "completed") {
    return "ok";
  }
  if (status === "partial" || status === "running" || status === "PUBLISHED" || status === "RECEIVED") {
    return "warn";
  }
  if (status === "unavailable" || status === "failed" || status === "FAILED") {
    return "danger";
  }
  return "neutral";
}
</script>
