<template>
  <section class="surge-panel">
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
        <span>
          <strong>{{ result.patientId }}</strong>
          <small>{{ result.taskId || result.message || "not submitted" }}</small>
        </span>
        <em>
          resources {{ result.readiness?.readinessStatus || result.taskStatus || result.status }}
          <template v-if="result.practitionerAssignment">
            / staff {{ result.practitionerAssignment.assignmentStatus }}
          </template>
        </em>
        <small v-if="result.readiness || result.practitionerAssignment">
          <template v-if="result.readiness">
            reserved {{ result.readiness.reservedResources.length }} /
            unavailable {{ result.readiness.unavailableResources.length }}
          </template>
          <template v-if="result.practitionerAssignment">
            / assignedPractitioners {{ result.practitionerAssignment.assignedPractitioners.length }} /
            unavailableSpecialties {{ result.practitionerAssignment.unavailableSpecialties.length }}
          </template>
        </small>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Activity, Zap } from "lucide-vue-next";
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
</script>
