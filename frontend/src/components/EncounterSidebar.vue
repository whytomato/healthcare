<template>
  <aside class="sidebar">
    <section class="brand">
      <div class="brand-mark">
        <Hospital :size="26" />
      </div>
      <div>
        <h1>Healthcare Workbench</h1>
        <p>Agent hospital workflow demo</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">
        <FilePlus2 :size="18" />
        <h2>Create Patient Encounter</h2>
      </div>

      <label class="field">
        <span>Patient ID</span>
        <input v-model="form.patientId" autocomplete="off" />
      </label>

      <label class="field">
        <span>Doctor ID</span>
        <input v-model="form.doctorId" autocomplete="off" />
      </label>

      <label class="field">
        <span>Language</span>
        <select v-model="form.language">
          <option value="zh-CN">zh-CN</option>
          <option value="en-US">en-US</option>
        </select>
      </label>

      <label class="field">
        <span>Chief Complaint</span>
        <textarea v-model="form.caseText" rows="7" />
      </label>

      <div class="button-row">
        <button
          class="primary-button"
          :disabled="isCreating || !form.caseText.trim()"
          @click="emit('create-encounter')"
        >
          <Loader2 v-if="isCreating" class="spin" :size="18" />
          <Send v-else :size="18" />
          <span>{{ isCreating ? "Submitting" : "Submit encounter" }}</span>
        </button>
        <button class="ghost-button" @click="emit('refresh-tasks')">
          <RefreshCw :size="18" />
        </button>
      </div>
    </section>

    <section class="panel compact">
      <div class="panel-title">
        <ClipboardList :size="18" />
        <h2>Demo Cases</h2>
      </div>
      <div class="demo-case-list">
        <button
          v-for="demoCase in demoCases"
          :key="demoCase.name"
          class="demo-case"
          @click="emit('apply-demo-case', demoCase)"
        >
          <span class="demo-case-name">{{ demoCase.name }}</span>
          <span class="demo-case-text">{{ demoCase.preview }}</span>
        </button>
      </div>
    </section>

    <section class="panel compact">
      <div class="panel-title">
        <ListChecks :size="18" />
        <h2>Recent Tasks</h2>
      </div>
      <div class="task-list">
        <button
          v-for="task in tasks"
          :key="task.taskId"
          class="task-item"
          :class="{ active: task.taskId === selectedTaskId }"
          @click="emit('select-task', task.taskId)"
        >
          <span class="task-main">{{ task.patientId || "unknown patient" }}</span>
          <span class="task-sub">{{ shortId(task.taskId) }} / {{ task.status }}</span>
        </button>
        <p v-if="tasks.length === 0" class="muted">No tasks yet</p>
      </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
import {
  ClipboardList,
  FilePlus2,
  Hospital,
  ListChecks,
  Loader2,
  RefreshCw,
  Send
} from "lucide-vue-next";
import type { AiTask, DemoCase, EncounterForm } from "../types";

defineProps<{
  form: EncounterForm;
  demoCases: DemoCase[];
  tasks: AiTask[];
  selectedTaskId: string;
  isCreating: boolean;
}>();

const emit = defineEmits<{
  "create-encounter": [];
  "refresh-tasks": [];
  "apply-demo-case": [demoCase: DemoCase];
  "select-task": [taskId: string];
}>();

function shortId(taskId: string) {
  return taskId ? `${taskId.slice(0, 8)}...${taskId.slice(-4)}` : "-";
}
</script>
