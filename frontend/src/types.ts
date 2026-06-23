export type TaskStatus = "RECEIVED" | "PUBLISHED" | "COMPLETED" | "NEEDS_DATA" | "FAILED";

export type AiTask = {
  taskId: string;
  status: TaskStatus;
  caseText: string;
  question?: string;
  doctorId?: string;
  patientId?: string;
  language?: string;
  errorMessage?: string;
  createdAt?: string;
  updatedAt?: string;
};

export type TimelineEvent = {
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

export type WorkflowDecision = {
  decision?: string;
  made_by?: string;
  agent?: string;
  reason?: string;
};

export type WorkflowResult = {
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

export type ClinicalRecord = {
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

export type PatientHistoryEncounter = {
  taskId: string;
  status: string;
  updatedAt?: string;
  selectedSpecialties?: string[];
  disposition?: string;
  reportExcerpt?: string;
};

export type PatientHistorySummary = {
  patientId: string;
  recentEncounters: PatientHistoryEncounter[];
  knownConditions: string[];
  allergies: string[];
  currentMedications: string[];
  previousDispositions: string[];
  lastFinalReports: string[];
};

export type WorkflowProgressEvent = {
  taskId: string;
  eventType: string;
  agent?: string;
  decision?: string;
  decisionScope?: string;
  reason?: string;
  targetAgents?: string[];
  parallelGroup?: string;
  payload?: Record<string, unknown>;
  durationMs?: number;
  eventIndex: number;
  createdAt?: string;
};

export type EncounterForm = {
  patientId: string;
  doctorId: string;
  language: string;
  caseText: string;
};

export type DemoCase = EncounterForm & {
  id: string;
  name: string;
  preview: string;
};

export type SurgeReadiness = {
  readinessStatus: string;
  reservedResources: string[];
  unavailableResources: string[];
};

export type SurgePractitionerAssignment = {
  assignmentStatus: string;
  assignedPractitioners: string[];
  unavailableSpecialties: string[];
};

export type SurgeResult = {
  patientId: string;
  taskId?: string;
  status: "submitted" | "running" | "completed" | "failed";
  taskStatus?: TaskStatus;
  readiness?: SurgeReadiness;
  practitionerAssignment?: SurgePractitionerAssignment;
  message?: string;
};
