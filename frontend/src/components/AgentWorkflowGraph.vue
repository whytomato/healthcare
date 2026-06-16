<template>
  <div class="workflow-graph-shell">
    <div class="graph-title-row">
      <div>
        <strong>Hospital Agent Coverage Graph</strong>
        <span>
          {{ executedAgentCount }} / {{ AGENTS.length }} agents executed ·
          {{ decisionCount }} decisions · {{ selectedToolCount }} tools selected
        </span>
      </div>
      <span class="graph-task">{{ selectedTaskId || "live encounter" }}</span>
    </div>

    <div class="graph-legend" aria-label="Workflow graph legend">
      <span><i class="legend-line edge-selected" /> Actual workflow</span>
      <span><i class="legend-line edge-available" /> Available but not taken</span>
      <span><i class="legend-line edge-skipped" /> Explicitly skipped</span>
      <span><i class="legend-line edge-tool-selected" /> Tool selected</span>
      <span><i class="legend-line edge-tool-skipped" /> Tool skipped</span>
      <span><i class="legend-line edge-tool-unavailable" /> Tool unavailable</span>
    </div>

    <div class="graph-filters" aria-label="Workflow graph display filters">
      <label>
        <input v-model="showDecisionLabels" type="checkbox" />
        <span>Decision labels</span>
      </label>
      <label>
        <input v-model="showTools" type="checkbox" />
        <span>Tool nodes</span>
      </label>
      <label>
        <input v-model="showAvailable" type="checkbox" />
        <span>Unused branches</span>
      </label>
      <label>
        <input v-model="showEdgeLabels" type="checkbox" />
        <span>Edge labels</span>
      </label>
    </div>

    <div class="workflow-graph">
      <VueFlow
        :key="graphRenderKey"
        :nodes="graphNodes"
        :edges="graphEdges"
        :fit-view-on-init="true"
        :min-zoom="0.18"
        :max-zoom="1.6"
        class="workflow-flow"
        @node-click="onNodeClick"
      >
        <template #node-workflow="{ data }">
          <div class="workflow-node-card">
            <span class="node-kicker">{{ data.kindLabel }}</span>
            <strong>{{ data.label }}</strong>
            <small v-if="data.badge">{{ data.badge }}</small>
            <em>{{ data.statusLabel }}</em>
          </div>
        </template>

        <Background pattern-color="#d9e4e5" :gap="18" />
        <Controls position="bottom-right" />
        <MiniMap pannable zoomable node-color="#1f7a68" />
      </VueFlow>
    </div>

    <aside class="graph-inspector">
      <div>
        <strong>{{ selectedSummary.title }}</strong>
        <span>{{ selectedSummary.kind }}</span>
      </div>
      <p>{{ selectedSummary.detail }}</p>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Background } from "@vue-flow/background";
import { Controls } from "@vue-flow/controls";
import { MiniMap } from "@vue-flow/minimap";
import { VueFlow, type Edge, type GraphNode, type NodeMouseEvent } from "@vue-flow/core";
import "@vue-flow/controls/dist/style.css";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import "@vue-flow/minimap/dist/style.css";

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

type WorkflowNodeKind = "agent" | "tool";
type WorkflowNodeStatus = "executed" | "available" | "selected" | "skipped" | "unavailable";

type WorkflowNodeData = {
  label: string;
  detail: string;
  kind: WorkflowNodeKind;
  kindLabel: string;
  status: WorkflowNodeStatus;
  statusLabel: string;
  badge?: string;
  event?: TimelineEvent;
};

type GraphDisplayOptions = {
  showDecisionLabels: boolean;
  showTools: boolean;
  showAvailable: boolean;
  showEdgeLabels: boolean;
};

type StaticAgent = {
  id: string;
  label: string;
  group: string;
  detail: string;
  x: number;
  y: number;
};

type StaticWorkflowEdge = {
  source: string;
  target: string;
  label: string;
  mode: "handoff" | "branch" | "parallel" | "diagnostic" | "disposition";
};

type StaticTool = {
  agent: string;
  tool: string;
  label: string;
};

const AGENTS: StaticAgent[] = [
  {
    id: "registration_agent",
    label: "Registration",
    group: "Intake",
    detail: "Patient registration, visit type, prior record lookup, and administrative readiness.",
    x: 0,
    y: 150
  },
  {
    id: "intake_agent",
    label: "Patient Intake",
    group: "Intake",
    detail: "Chief complaint and encounter context collection.",
    x: 260,
    y: 55
  },
  {
    id: "nurse_vitals_agent",
    label: "Nurse Vitals",
    group: "Intake",
    detail: "Vitals planning and abnormal vital sign risk recognition.",
    x: 260,
    y: 245
  },
  {
    id: "appointment_agent",
    label: "Appointment",
    group: "Intake",
    detail: "Appointment priority and routing readiness.",
    x: 520,
    y: 55
  },
  {
    id: "triage_nurse_agent",
    label: "Triage Nurse",
    group: "Triage",
    detail: "Urgency classification, red flag recognition, and guideline tool decision.",
    x: 520,
    y: 245
  },
  {
    id: "department_router_agent",
    label: "Department Router",
    group: "Routing",
    detail: "Routes the encounter to emergency-first or general-practitioner-first workflow.",
    x: 800,
    y: 245
  },
  {
    id: "emergency_physician_agent",
    label: "Emergency Physician",
    group: "Clinical",
    detail: "Emergency physician review for high-urgency and red-flag encounters.",
    x: 1080,
    y: 110
  },
  {
    id: "general_practitioner_agent",
    label: "General Practitioner",
    group: "Clinical",
    detail: "General clinical assessment before specialty routing.",
    x: 1080,
    y: 355
  },
  {
    id: "specialist_router_agent",
    label: "Specialist Router",
    group: "Routing",
    detail: "Selects one or more specialist consultation branches.",
    x: 1360,
    y: 245
  },
  {
    id: "respiratory_specialist_agent",
    label: "Respiratory Specialist",
    group: "Specialist",
    detail: "Respiratory specialty consultation branch.",
    x: 1640,
    y: 0
  },
  {
    id: "cardiology_specialist_agent",
    label: "Cardiology Specialist",
    group: "Specialist",
    detail: "Cardiology specialty consultation branch.",
    x: 1640,
    y: 150
  },
  {
    id: "infectious_disease_specialist_agent",
    label: "Infectious Disease",
    group: "Specialist",
    detail: "Infectious disease specialty consultation branch.",
    x: 1640,
    y: 300
  },
  {
    id: "neurology_specialist_agent",
    label: "Neurology Specialist",
    group: "Specialist",
    detail: "Neurology specialty consultation branch.",
    x: 1640,
    y: 450
  },
  {
    id: "lab_advisor_agent",
    label: "Lab Advisor",
    group: "Diagnostics",
    detail: "Aggregates consultation recommendations into diagnostic priorities.",
    x: 1940,
    y: 245
  },
  {
    id: "diagnostic_order_agent",
    label: "Diagnostic Orders",
    group: "Diagnostics",
    detail: "Creates lab and imaging orders according to urgency and specialties.",
    x: 2220,
    y: 245
  },
  {
    id: "lab_result_interpreter_agent",
    label: "Lab Interpreter",
    group: "Diagnostics",
    detail: "Fetches and interprets lab result placeholders.",
    x: 2500,
    y: 120
  },
  {
    id: "imaging_interpreter_agent",
    label: "Imaging Interpreter",
    group: "Diagnostics",
    detail: "Fetches and interprets imaging result placeholders.",
    x: 2500,
    y: 370
  },
  {
    id: "pharmacy_safety_agent",
    label: "Pharmacy Safety",
    group: "Medication",
    detail: "Checks allergy, medication history, and interaction safety.",
    x: 2800,
    y: 245
  },
  {
    id: "medication_plan_agent",
    label: "Medication Plan",
    group: "Medication",
    detail: "Creates medication plan and pharmacist review status.",
    x: 3080,
    y: 245
  },
  {
    id: "care_plan_agent",
    label: "Care Plan",
    group: "Disposition",
    detail: "Outpatient care-plan branch for lower-risk encounters.",
    x: 3360,
    y: 95
  },
  {
    id: "follow_up_agent",
    label: "Follow Up",
    group: "Disposition",
    detail: "Schedules follow-up and specialty referral actions when appropriate.",
    x: 3640,
    y: 95
  },
  {
    id: "disposition_coordinator_agent",
    label: "Disposition",
    group: "Disposition",
    detail: "Chooses outpatient follow-up, emergency reassessment, or admission review.",
    x: 3360,
    y: 385
  },
  {
    id: "admission_coordinator_agent",
    label: "Admission",
    group: "Disposition",
    detail: "Checks bed availability and admission/observation pathway requirements.",
    x: 3640,
    y: 385
  },
  {
    id: "final_hospital_report_agent",
    label: "Final Report",
    group: "Report",
    detail: "Generates the final hospital workflow report with relevant context.",
    x: 3920,
    y: 245
  }
];

const WORKFLOW_EDGES: StaticWorkflowEdge[] = [
  { source: "registration_agent", target: "intake_agent", label: "handoff", mode: "handoff" },
  { source: "registration_agent", target: "nurse_vitals_agent", label: "handoff", mode: "handoff" },
  { source: "intake_agent", target: "appointment_agent", label: "handoff", mode: "handoff" },
  { source: "intake_agent", target: "triage_nurse_agent", label: "handoff", mode: "handoff" },
  { source: "nurse_vitals_agent", target: "triage_nurse_agent", label: "vitals", mode: "handoff" },
  { source: "appointment_agent", target: "triage_nurse_agent", label: "priority", mode: "handoff" },
  { source: "triage_nurse_agent", target: "department_router_agent", label: "urgency", mode: "branch" },
  { source: "department_router_agent", target: "emergency_physician_agent", label: "emergency", mode: "branch" },
  { source: "department_router_agent", target: "general_practitioner_agent", label: "outpatient", mode: "branch" },
  { source: "emergency_physician_agent", target: "general_practitioner_agent", label: "stabilize + review", mode: "handoff" },
  { source: "emergency_physician_agent", target: "specialist_router_agent", label: "urgent consult", mode: "handoff" },
  { source: "general_practitioner_agent", target: "specialist_router_agent", label: "clinical consult", mode: "handoff" },
  { source: "specialist_router_agent", target: "respiratory_specialist_agent", label: "parallel", mode: "parallel" },
  { source: "specialist_router_agent", target: "cardiology_specialist_agent", label: "parallel", mode: "parallel" },
  { source: "specialist_router_agent", target: "infectious_disease_specialist_agent", label: "parallel", mode: "parallel" },
  { source: "specialist_router_agent", target: "neurology_specialist_agent", label: "parallel", mode: "parallel" },
  { source: "respiratory_specialist_agent", target: "lab_advisor_agent", label: "consult", mode: "parallel" },
  { source: "cardiology_specialist_agent", target: "lab_advisor_agent", label: "consult", mode: "parallel" },
  { source: "infectious_disease_specialist_agent", target: "lab_advisor_agent", label: "consult", mode: "parallel" },
  { source: "neurology_specialist_agent", target: "lab_advisor_agent", label: "consult", mode: "parallel" },
  { source: "lab_advisor_agent", target: "diagnostic_order_agent", label: "orders", mode: "diagnostic" },
  { source: "diagnostic_order_agent", target: "lab_result_interpreter_agent", label: "labs", mode: "diagnostic" },
  { source: "diagnostic_order_agent", target: "imaging_interpreter_agent", label: "imaging", mode: "diagnostic" },
  { source: "lab_result_interpreter_agent", target: "pharmacy_safety_agent", label: "results", mode: "diagnostic" },
  { source: "imaging_interpreter_agent", target: "pharmacy_safety_agent", label: "results", mode: "diagnostic" },
  { source: "pharmacy_safety_agent", target: "medication_plan_agent", label: "safety", mode: "handoff" },
  { source: "medication_plan_agent", target: "care_plan_agent", label: "outpatient", mode: "disposition" },
  { source: "medication_plan_agent", target: "disposition_coordinator_agent", label: "urgent", mode: "disposition" },
  { source: "care_plan_agent", target: "follow_up_agent", label: "plan", mode: "disposition" },
  { source: "follow_up_agent", target: "disposition_coordinator_agent", label: "follow-up", mode: "disposition" },
  { source: "disposition_coordinator_agent", target: "admission_coordinator_agent", label: "disposition", mode: "disposition" },
  { source: "admission_coordinator_agent", target: "final_hospital_report_agent", label: "report", mode: "disposition" }
];

const TOOLS: StaticTool[] = [
  { agent: "registration_agent", tool: "patient_history_lookup", label: "History Lookup" },
  { agent: "triage_nurse_agent", tool: "guideline_lookup", label: "Guideline Lookup" },
  { agent: "diagnostic_order_agent", tool: "lab_order", label: "Lab Order" },
  { agent: "diagnostic_order_agent", tool: "imaging_order", label: "Imaging Order" },
  { agent: "lab_result_interpreter_agent", tool: "lab_result_fetch", label: "Lab Result Fetch" },
  { agent: "imaging_interpreter_agent", tool: "imaging_result_fetch", label: "Imaging Result Fetch" },
  { agent: "pharmacy_safety_agent", tool: "patient_history_lookup", label: "History Lookup" },
  { agent: "pharmacy_safety_agent", tool: "medication_interaction", label: "Interaction Check" },
  { agent: "care_plan_agent", tool: "patient_history_lookup", label: "History Lookup" },
  { agent: "follow_up_agent", tool: "patient_history_lookup", label: "History Lookup" },
  { agent: "follow_up_agent", tool: "follow_up_scheduling", label: "Follow-up Scheduling" },
  { agent: "follow_up_agent", tool: "referral_scheduling", label: "Referral Scheduling" },
  { agent: "disposition_coordinator_agent", tool: "human_review_request", label: "Human Review" },
  { agent: "admission_coordinator_agent", tool: "bed_availability", label: "Bed Availability" },
  { agent: "admission_coordinator_agent", tool: "care_coordination", label: "Care Coordination" },
  { agent: "final_hospital_report_agent", tool: "patient_history_lookup", label: "History Lookup" }
];

const AGENT_BY_ID = new Map(AGENTS.map((agent) => [agent.id, agent]));
const STATIC_EDGE_KEYS = new Set(WORKFLOW_EDGES.map((edge) => edgeKey(edge.source, edge.target)));

const props = defineProps<{
  events: TimelineEvent[];
  selectedTaskId?: string;
}>();

const selectedNodeId = ref<string>("");
const showDecisionLabels = ref(true);
const showTools = ref(false);
const showAvailable = ref(true);
const showEdgeLabels = ref(false);

const graphOptions = computed<GraphDisplayOptions>(() => ({
  showDecisionLabels: showDecisionLabels.value,
  showTools: showTools.value,
  showAvailable: showAvailable.value,
  showEdgeLabels: showEdgeLabels.value
}));
const graphRenderKey = computed(() => JSON.stringify(graphOptions.value));
const graphModel = computed(() => buildGraph(props.events, graphOptions.value));
const graphNodes = computed(() => graphModel.value.nodes);
const graphEdges = computed(() => graphModel.value.edges);
const executedAgentCount = computed(() => graphModel.value.executedAgentCount);
const decisionCount = computed(() => graphModel.value.decisionCount);
const selectedToolCount = computed(() => graphModel.value.selectedToolCount);

const selectedSummary = computed(() => {
  const selected =
    graphNodes.value.find((node) => node.id === selectedNodeId.value) ||
    graphNodes.value[0];
  if (!selected) {
    return {
      title: "No workflow events",
      kind: "Graph",
      detail: "Graph appears when realtime timeline events are available."
    };
  }
  const data = selected.data as WorkflowNodeData;
  return {
    title: data.label,
    kind: `${formatKind(data.kind)} · ${data.statusLabel}`,
    detail: data.detail
  };
});

function onNodeClick(event: NodeMouseEvent) {
  selectedNodeId.value = event.node.id;
}

function buildGraph(events: TimelineEvent[], options: GraphDisplayOptions) {
  const nodes = new Map<string, GraphNode>();
  const edges = new Map<string, Edge>();
  const executedAgents = collectExecutedAgents(events);
  const actualEdges = collectActualEdges(events);
  const skippedEdges = collectSkippedEdges(events);
  const edgeDecisionLabels = collectEdgeDecisionLabels(events);
  const decisionsByAgent = collectDecisionsByAgent(events);
  const toolEvents = collectToolEvents(events);

  function ensureNode(id: string, node: GraphNode) {
    if (!nodes.has(id)) {
      nodes.set(id, node);
    }
  }

  function ensureEdge(
    id: string,
    source: string,
    target: string,
    label: string,
    kind: string,
    mode?: string,
    animated = false,
    forceLabel = false
  ) {
    if (source === target || edges.has(id) || !nodes.has(source) || !nodes.has(target)) {
      return;
    }
    edges.set(id, {
      id,
      source,
      target,
      label: options.showEdgeLabels || forceLabel ? label : "",
      animated,
      type: "smoothstep",
      class: edgeClass(kind, mode),
      data: { edgeKind: kind, mode }
    });
  }

  for (const agent of AGENTS) {
    const isExecuted = executedAgents.has(agent.id);
    if (!options.showAvailable && !isExecuted) {
      continue;
    }
    const decisions = decisionsByAgent.get(agent.id) || [];
    const status: WorkflowNodeStatus = isExecuted ? "executed" : "available";
    const latestDecision = decisions.at(-1);
    ensureNode(agentNodeId(agent.id), {
      id: agentNodeId(agent.id),
      type: "workflow",
      position: { x: agent.x, y: agent.y },
      data: {
        label: agent.label,
        detail: nodeDetail(agent, status, latestDecision),
        kind: "agent",
        kindLabel: agent.group,
        status,
        statusLabel: status === "executed" ? "actual agent" : "not triggered",
        badge: latestDecision?.decision ? `Decision: ${formatDecision(latestDecision.decision)}` : undefined,
        event: latestDecision
      },
      class: nodeClass("agent", status, decisions.length > 0)
    });
  }

  for (const agent of [...executedAgents].filter((agent) => !AGENT_BY_ID.has(agent))) {
    const index = nodes.size - AGENTS.length;
    ensureNode(agentNodeId(agent), {
      id: agentNodeId(agent),
      type: "workflow",
      position: { x: 0, y: 760 + index * 92 },
      data: {
        label: formatAgent(agent),
        detail: "Runtime event included this agent, but it is not yet part of the static hospital capability map.",
        kind: "agent",
        kindLabel: "Runtime",
        status: "executed",
        statusLabel: "actual agent"
      },
      class: nodeClass("agent", "executed", false)
    });
  }

  for (const edge of WORKFLOW_EDGES) {
    const key = edgeKey(edge.source, edge.target);
    const isActual = actualEdges.has(key);
    const isSkipped = skippedEdges.has(key);
    if (!isActual && !isSkipped && !options.showAvailable) {
      continue;
    }
    const kind = isActual ? "selected" : isSkipped ? "skipped" : "available";
    const label = options.showDecisionLabels && edgeDecisionLabels.has(key)
      ? edgeDecisionLabels.get(key) as string
      : edge.label;
    const forceLabel = options.showDecisionLabels && edgeDecisionLabels.has(key);
    ensureEdge(
      `flow:${key}`,
      agentNodeId(edge.source),
      agentNodeId(edge.target),
      label,
      kind,
      edge.mode,
      isActual,
      forceLabel
    );
  }

  if (options.showTools) {
    addToolNodes(TOOLS, toolEvents, nodes, ensureEdge, options.showAvailable);
    addDynamicToolNodes(toolEvents, nodes, ensureEdge);
  }

  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
    executedAgentCount: [...executedAgents].filter((agent) => AGENT_BY_ID.has(agent)).length,
    decisionCount: [...events].filter((event) => event.event_type === "decision_made").length,
    selectedToolCount: [...toolEvents.values()].filter((event) => toolStatus(event) === "selected").length
  };
}

function addToolNodes(
  tools: StaticTool[],
  toolEvents: Map<string, TimelineEvent>,
  nodes: Map<string, GraphNode>,
  ensureEdge: (
    id: string,
    source: string,
    target: string,
    label: string,
    kind: string,
    mode?: string,
    animated?: boolean
  ) => void,
  showAvailable: boolean
) {
  const toolIndexByAgent = new Map<string, number>();
  for (const tool of tools) {
    const agent = AGENT_BY_ID.get(tool.agent);
    const slot = toolIndexByAgent.get(tool.agent) || 0;
    toolIndexByAgent.set(tool.agent, slot + 1);
    const event = toolEvents.get(toolKey(tool.agent, tool.tool));
    if (!event && !showAvailable) {
      continue;
    }
    const status = event ? toolStatus(event) : "available";
    const id = toolNodeId(tool.agent, tool.tool);
    nodes.set(id, {
      id,
      type: "workflow",
      position: {
        x: agent?.x ?? 0,
        y: 650 + slot * 82
      },
      data: {
        label: tool.label,
        detail: event ? toolDetail(event) : "This tool is available to the agent but was not used in this run.",
        kind: "tool",
        kindLabel: "Tool",
        status,
        statusLabel: toolStatusLabel(status),
        badge: formatAgent(tool.agent),
        event
      },
      class: nodeClass("tool", status, false)
    });
    ensureEdge(
      `tool:${tool.agent}:${tool.tool}`,
      agentNodeId(tool.agent),
      id,
      toolStatusLabel(status),
      status === "available" ? "available" : `tool-${status}`,
      "tool",
      status === "selected"
    );
  }
}

function addDynamicToolNodes(
  toolEvents: Map<string, TimelineEvent>,
  nodes: Map<string, GraphNode>,
  ensureEdge: (
    id: string,
    source: string,
    target: string,
    label: string,
    kind: string,
    mode?: string,
    animated?: boolean
  ) => void
) {
  const staticToolKeys = new Set(TOOLS.map((tool) => toolKey(tool.agent, tool.tool)));
  let index = 0;
  for (const [key, event] of toolEvents.entries()) {
    if (staticToolKeys.has(key) || !event.agent) {
      continue;
    }
    const tool = String(event.payload?.tool || event.decision || "tool");
    const status = toolStatus(event);
    const agent = AGENT_BY_ID.get(event.agent);
    const id = toolNodeId(event.agent, tool);
    nodes.set(id, {
      id,
      type: "workflow",
      position: { x: agent?.x ?? 0, y: 900 + index * 82 },
      data: {
        label: formatTool(tool),
        detail: toolDetail(event),
        kind: "tool",
        kindLabel: "Runtime Tool",
        status,
        statusLabel: toolStatusLabel(status),
        badge: formatAgent(event.agent),
        event
      },
      class: nodeClass("tool", status, false)
    });
    ensureEdge(
      `tool-runtime:${event.agent}:${tool}:${index}`,
      agentNodeId(event.agent),
      id,
      toolStatusLabel(status),
      `tool-${status}`,
      "tool",
      status === "selected"
    );
    index += 1;
  }
}

function collectExecutedAgents(events: TimelineEvent[]) {
  const executed = new Set<string>();
  for (const event of events) {
    if (event.event_type === "agent_completed" && event.agent) {
      executed.add(event.agent);
    }
  }
  return executed;
}

function collectActualEdges(events: TimelineEvent[]) {
  const actual = new Set<string>();
  const completedOrder = events
    .filter((event) => event.event_type === "agent_completed" && event.agent)
    .map((event) => event.agent as string);

  for (const event of events) {
    if (!event.agent) {
      continue;
    }
    for (const target of event.target_agents || payloadStringList(event.payload, "handoff_to")) {
      actual.add(edgeKey(event.agent, target));
    }
    for (const branch of selectedBranchTargets(event)) {
      actual.add(edgeKey(event.agent, branch.target));
    }
  }

  for (let index = 0; index < completedOrder.length - 1; index += 1) {
    const key = edgeKey(completedOrder[index], completedOrder[index + 1]);
    if (STATIC_EDGE_KEYS.has(key)) {
      actual.add(key);
    }
  }

  return actual;
}

function collectSkippedEdges(events: TimelineEvent[]) {
  const skipped = new Set<string>();
  for (const event of events) {
    if (!event.agent) {
      continue;
    }
    for (const branch of skippedBranchTargets(event)) {
      skipped.add(edgeKey(event.agent, branch.target));
    }
  }
  return skipped;
}

function collectEdgeDecisionLabels(events: TimelineEvent[]) {
  const labels = new Map<string, string>();
  for (const event of events) {
    if (event.event_type !== "decision_made" || !event.agent || !event.decision) {
      continue;
    }
    const decision = formatDecision(event.decision);
    for (const branch of selectedBranchTargets(event)) {
      labels.set(edgeKey(event.agent, branch.target), decision);
    }
    for (const branch of skippedBranchTargets(event)) {
      labels.set(edgeKey(event.agent, branch.target), decision);
    }
    for (const target of payloadStringList(event.payload, "handoff_to")) {
      labels.set(edgeKey(event.agent, target), decision);
    }
  }
  return labels;
}

function collectDecisionsByAgent(events: TimelineEvent[]) {
  const decisions = new Map<string, TimelineEvent[]>();
  for (const event of events) {
    if (event.event_type !== "decision_made" || !event.agent) {
      continue;
    }
    const existing = decisions.get(event.agent) || [];
    existing.push(event);
    decisions.set(event.agent, existing);
  }
  return decisions;
}

function collectToolEvents(events: TimelineEvent[]) {
  const tools = new Map<string, TimelineEvent>();
  for (const event of events) {
    if (
      (event.event_type === "tool_invoked" || event.event_type === "tool_skipped") &&
      event.agent
    ) {
      const tool = String(event.payload?.tool || event.decision || "tool");
      tools.set(toolKey(event.agent, tool), event);
    }
  }
  return tools;
}

function selectedBranchTargets(event: TimelineEvent) {
  const branches = [];
  const selectedBranch = event.payload?.selected_branch;
  if (isBranch(selectedBranch)) {
    branches.push(selectedBranch);
  }
  const selectedBranches = event.payload?.selected_branches;
  if (Array.isArray(selectedBranches)) {
    branches.push(...selectedBranches.filter(isBranch));
  }
  return branches;
}

function skippedBranchTargets(event: TimelineEvent) {
  const skippedBranches = event.payload?.skipped_branches;
  return Array.isArray(skippedBranches) ? skippedBranches.filter(isBranch) : [];
}

function isBranch(value: unknown): value is { target: string; reason?: string } {
  return Boolean(
    value &&
      typeof value === "object" &&
      typeof (value as Record<string, unknown>).target === "string"
  );
}

function payloadStringList(payload: Record<string, unknown> | undefined, key: string) {
  const value = payload?.[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function nodeDetail(agent: StaticAgent, status: WorkflowNodeStatus, decision?: TimelineEvent) {
  const runStatus = status === "executed" ? "This agent executed in the current run." : "This agent is available but was not triggered by the current run.";
  const decisionDetail = decision?.decision
    ? ` Decision recorded: ${formatDecision(decision.decision)}${decision.reason ? ` (${decision.reason})` : ""}.`
    : "";
  return `${runStatus} ${agent.detail}${decisionDetail}`;
}

function toolDetail(event: TimelineEvent) {
  const status = event.payload?.status ? `Status: ${event.payload.status}. ` : "";
  const reason = event.reason || "Tool choice recorded by the role agent.";
  return `${status}${reason}`;
}

function toolStatus(event: TimelineEvent): WorkflowNodeStatus {
  const choice = String(event.payload?.choice || event.payload?.status || "");
  const status = String(event.payload?.status || "");
  if (event.event_type === "tool_skipped" || choice === "skipped") {
    return "skipped";
  }
  if (choice === "unavailable" || status === "unavailable") {
    return "unavailable";
  }
  return "selected";
}

function toolStatusLabel(status: WorkflowNodeStatus) {
  const labels: Record<WorkflowNodeStatus, string> = {
    executed: "actual agent",
    available: "not used",
    selected: "selected",
    skipped: "skipped",
    unavailable: "unavailable"
  };
  return labels[status];
}

function agentNodeId(agent: string) {
  return `agent:${agent}`;
}

function toolNodeId(agent: string, tool: string) {
  return `tool:${agent}:${tool}`;
}

function toolKey(agent: string, tool: string) {
  return `${agent}:${tool}`;
}

function edgeKey(source: string, target: string) {
  return `${source}->${target}`;
}

function nodeClass(kind: WorkflowNodeKind, status: WorkflowNodeStatus, hasDecision: boolean) {
  return [
    "graph-node",
    `graph-node-${kind}`,
    `graph-node-${status}`,
    hasDecision ? "graph-node-has-decision" : ""
  ]
    .filter(Boolean)
    .join(" ");
}

function edgeClass(kind: string, mode?: string) {
  return [`edge-${kind}`, mode ? `edge-mode-${mode}` : ""].filter(Boolean).join(" ");
}

function formatAgent(agent?: string) {
  if (!agent) return "Workflow";
  return agent
    .replace(/_agent$/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDecision(decision: string) {
  return decision
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatTool(tool: string) {
  return tool
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatKind(kind: WorkflowNodeKind) {
  return kind
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
</script>
