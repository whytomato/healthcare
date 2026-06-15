<template>
  <section class="panel journey-panel">
    <div class="panel-title split">
      <div>
        <div class="title-line">
          <Map :size="18" />
          <h2>Hospital Journey Overview</h2>
        </div>
        <p>{{ progressText }}</p>
      </div>
      <div class="journey-percent">{{ progressPercent }}%</div>
    </div>
    <div class="journey-progress">
      <div :style="{ width: `${progressPercent}%` }" />
    </div>
    <div class="journey-stages">
      <div v-for="stage in stages" :key="stage.key" class="journey-stage" :class="stage.state">
        <div class="journey-stage-icon">
          <CheckCircle2 v-if="stage.state === 'done'" :size="15" />
          <Loader2 v-else-if="stage.state === 'active'" class="spin" :size="15" />
          <Circle v-else :size="15" />
        </div>
        <div>
          <strong>{{ stage.label }}</strong>
          <span>{{ stage.detail }}</span>
        </div>
      </div>
    </div>
    <div class="journey-stats">
      <span><Activity :size="14" /> Agent events {{ stats.agentEvents }}</span>
      <span><BrainCircuit :size="14" /> Decision events {{ stats.decisionEvents }}</span>
      <span><GitBranch :size="14" /> Parallel branches {{ stats.parallelBranches }}</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Activity, BrainCircuit, CheckCircle2, Circle, GitBranch, Loader2, Map } from "lucide-vue-next";

type JourneyStage = {
  key: string;
  label: string;
  detail: string;
  state: "done" | "active" | "waiting";
};

defineProps<{
  stages: JourneyStage[];
  progressText: string;
  progressPercent: number;
  stats: {
    agentEvents: number;
    decisionEvents: number;
    parallelBranches: number;
  };
}>();
</script>
