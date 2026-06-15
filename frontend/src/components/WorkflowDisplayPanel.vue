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
        <span class="status-badge">{{ workflowName }}</span>
      </div>

      <AgentTimeline
        v-if="timeline.length"
        :events="timeline"
        :selected-task-id="selectedTaskId"
      />
      <div v-else-if="selectedTaskId" class="live-flow">
        <div class="live-flow-head">
          <Loader2 class="spin" :size="18" />
          <strong>{{ liveFlowTitle }}</strong>
        </div>
        <div class="stage-list">
          <div v-for="stage in liveStages" :key="stage.agent" class="stage-item" :class="stage.state">
            <div class="stage-icon">
              <CheckCircle2 v-if="stage.state === 'done'" :size="16" />
              <Loader2 v-else-if="stage.state === 'active'" class="spin" :size="16" />
              <Circle :size="16" v-else />
            </div>
            <div>
              <strong>{{ stage.label }}</strong>
              <span>{{ stage.description }}</span>
            </div>
          </div>
        </div>
        <p class="live-note">
          Polling realtime agent progress. Events switch this panel to the real agent timeline and branch decisions.
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
import { Activity, BrainCircuit, CheckCircle2, Circle, Loader2, Route, Workflow } from "lucide-vue-next";
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

type LiveStage = {
  agent: string;
  label: string;
  description: string;
  state: "done" | "active" | "waiting";
};

defineProps<{
  timeline: TimelineEvent[];
  timelineCaption: string;
  workflowName: string;
  selectedTaskId: string;
  liveFlowTitle: string;
  liveStages: LiveStage[];
  executedPath: string[];
  displayedDecisions: WorkflowDecision[];
}>();

function formatAgent(agent?: string) {
  if (!agent) return "Workflow";
  return agent
    .replace(/_agent$/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
</script>
