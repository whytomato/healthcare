<template>
  <section class="content-grid">
    <article class="panel main-panel">
      <div class="panel-title split">
        <div>
          <div class="title-line">
            <Activity :size="18" />
            <h2>Agent Handoff Timeline</h2>
          </div>
          <p>{{ timelineCaption }}</p>
        </div>
        <div class="panel-actions">
          <div class="view-toggle" role="tablist" aria-label="Workflow view">
            <button
              type="button"
              :class="{ active: activeWorkflowView === 'timeline' }"
              @click="activeWorkflowView = 'timeline'"
            >
              <ListTree :size="15" />
              <span>Timeline</span>
            </button>
            <button
              type="button"
              :class="{ active: activeWorkflowView === 'graph' }"
              @click="activeWorkflowView = 'graph'"
            >
              <GitBranch :size="15" />
              <span>Graph</span>
            </button>
          </div>
          <span class="status-badge">{{ workflowName }}</span>
        </div>
      </div>

      <AgentTimeline
        v-if="timeline.length && activeWorkflowView === 'timeline'"
        :events="timeline"
        :selected-task-id="selectedTaskId"
      />
      <AgentWorkflowGraph
        v-else-if="timeline.length && activeWorkflowView === 'graph'"
        :events="timeline"
        :selected-task-id="selectedTaskId"
      />
      <div v-else-if="selectedTaskId" class="timeline-empty-state">
        <div class="timeline-empty-head">
          <Loader2 class="spin" :size="18" />
          <strong>Waiting for realtime agent events</strong>
        </div>
        <p class="live-note">
          Polling the selected Patient Encounter. The real Agent Handoff Timeline appears as soon as workflow progress events arrive.
        </p>
      </div>
      <div v-else class="empty-state">
        <Workflow :size="36" />
        <p>Create or select a patient encounter to show the agent handoff timeline.</p>
      </div>
    </article>

    <aside class="details-column">
      <article class="panel">
        <div class="panel-title">
          <Route :size="18" />
          <h2>Executed Path</h2>
        </div>
        <div v-if="executedPath.length" class="agent-path">
          <span v-for="agent in executedPath" :key="agent">{{ formatAgent(agent) }}</span>
        </div>
        <p v-else class="muted">No executed path yet.</p>
      </article>

      <article class="panel">
        <div class="panel-title">
          <BrainCircuit :size="18" />
          <h2>Workflow Decisions</h2>
        </div>
        <div v-if="displayedDecisions.length" class="decision-list">
          <div
            v-for="decision in displayedDecisions"
            :key="`${decision.made_by || decision.agent}-${decision.decision}`"
            class="decision-item"
          >
            <strong>{{ decision.decision }}</strong>
            <span>{{ decision.made_by || decision.agent || "workflow" }}</span>
            <p>{{ decision.reason || "No reason provided" }}</p>
          </div>
        </div>
        <p v-else class="muted">No workflow decisions yet.</p>
      </article>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Activity, BrainCircuit, GitBranch, ListTree, Loader2, Route, Workflow } from "lucide-vue-next";
import AgentWorkflowGraph from "./AgentWorkflowGraph.vue";
import AgentTimeline from "./AgentTimeline.vue";

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

type WorkflowDecision = {
  decision?: string;
  made_by?: string;
  agent?: string;
  reason?: string;
};

defineProps<{
  timeline: TimelineEvent[];
  timelineCaption: string;
  workflowName: string;
  selectedTaskId: string;
  executedPath: string[];
  displayedDecisions: WorkflowDecision[];
}>();

const activeWorkflowView = ref<"timeline" | "graph">("timeline");

function formatAgent(agent?: string) {
  if (!agent) return "Workflow";
  return agent
    .replace(/_agent$/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
</script>
