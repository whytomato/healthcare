<template>
  <div class="timeline">
    <div v-for="event in events" :key="eventKey(event)" class="timeline-event">
      <div class="timeline-dot" :class="eventClass(event.event_type)" />
      <div class="timeline-body">
        <div class="event-head">
          <div>
            <strong>{{ eventLabel(event) }}</strong>
            <span>{{ formatEventType(event.event_type) }}</span>
          </div>
          <span>#{{ event.event_index ?? "-" }}</span>
        </div>
        <div class="event-meta">
          <span class="event-agent">{{ formatAgent(event.agent) }}</span>
          <span v-if="event.duration_ms !== undefined" class="event-duration">
            {{ formatDuration(event.duration_ms) }}
          </span>
        </div>
        <span v-if="event.decision_scope" class="event-scope">{{ event.decision_scope }}</span>
        <p>{{ eventSummary(event) }}</p>
        <p v-if="event.decision">Decision: {{ event.decision }}</p>
        <p v-if="isToolEvent(event) && event.payload?.tool">
          Tool: {{ event.payload?.tool }}
          <span v-if="event.payload?.status">- {{ event.payload?.status }}</span>
        </p>
        <div v-if="event.target_agents?.length" class="timeline-targets">
          <span v-for="target in event.target_agents" :key="target">{{ formatAgent(target) }}</span>
        </div>
      </div>
    </div>
    <div ref="timelineEnd" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

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

const props = defineProps<{
  events: TimelineEvent[];
  selectedTaskId?: string;
}>();

const timelineEnd = ref<HTMLElement | null>(null);

watch(
  () => props.events.length,
  async () => {
    await nextTick();
    timelineEnd.value?.scrollIntoView({ block: "nearest" });
  }
);

function formatAgent(agent?: string) {
  if (!agent) return "Workflow";
  return agent
    .replace(/_agent$/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatEventType(type?: string) {
  if (!type) return "Event";
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function eventClass(type?: string) {
  if (type === "decision_made") return "decision";
  if (type === "tool_invoked" || type === "tool_skipped") return "tool";
  if (type === "handoff_created") return "handoff";
  if (type?.includes("parallel")) return "parallel";
  return "complete";
}

function eventLabel(event: TimelineEvent) {
  if (event.event_type === "agent_completed") return "Agent finished";
  if (event.event_type === "decision_made") return "Decision point";
  if (event.event_type === "tool_invoked") return "Tool invoked";
  if (event.event_type === "tool_skipped") return "Tool skipped";
  if (event.event_type === "handoff_created") return "Handoff created";
  if (event.event_type === "parallel_fanout") return "Parallel fan-out";
  if (event.event_type === "fanin_completed") return "Parallel fan-in";
  return "Workflow event";
}

function eventSummary(event: TimelineEvent) {
  if (event.reason) {
    return event.reason;
  }
  if (event.event_type === "agent_completed") {
    return `${formatAgent(event.agent)} completed its hospital role output.`;
  }
  if (event.event_type === "tool_invoked") {
    return `${formatAgent(event.agent)} used ${event.payload?.tool || "an internal tool"} for this role decision.`;
  }
  if (event.event_type === "tool_skipped") {
    return `${formatAgent(event.agent)} skipped ${event.payload?.tool || "an internal tool"} for this role decision.`;
  }
  if (event.event_type === "handoff_created" && event.target_agents?.length) {
    return "Downstream hospital roles received the handoff.";
  }
  if (event.event_type === "parallel_fanout") {
    return "Selected specialists can consult concurrently from the shared patient context.";
  }
  if (event.event_type === "fanin_completed") {
    return "Parallel specialist outputs converged into downstream planning.";
  }
  return "Workflow progress event received.";
}

function formatDuration(durationMs: number) {
  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }
  return `${(durationMs / 1000).toFixed(1)} s`;
}

function isToolEvent(event: TimelineEvent) {
  return event.event_type === "tool_invoked" || event.event_type === "tool_skipped";
}

function eventKey(event: TimelineEvent) {
  return `${props.selectedTaskId || "task"}-${event.event_index ?? `${event.event_type}-${event.agent}-${event.decision ?? ""}`}`;
}
</script>
