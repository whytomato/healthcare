import type {
  ClinicalRecord,
  SurgePractitionerAssignment,
  SurgeReadiness,
  TimelineEvent
} from "./types";

export function extractSurgeReadiness(record: ClinicalRecord): SurgeReadiness {
  const payload = findToolPayload(record, "resource_reservation");
  return {
    readinessStatus: String(payload.readinessStatus || payload.resourceReadinessStatus || payload.status || "unknown"),
    reservedResources: toStringList(payload.reservedResources),
    unavailableResources: toStringList(payload.unavailableResources)
  };
}

export function extractSurgePractitionerAssignment(record: ClinicalRecord): SurgePractitionerAssignment {
  const payload = findToolPayload(record, "practitioner_assignment");
  return {
    assignmentStatus: String(payload.assignmentStatus || payload.status || "unknown"),
    assignedPractitioners: toStringList(payload.assignedPractitioners),
    unavailableSpecialties: toStringList(payload.unavailableSpecialties)
  };
}

function findToolPayload(record: ClinicalRecord, toolName: string): Record<string, unknown> {
  const events: TimelineEvent[] = record.handoffTimeline || record.rawResult?.handoff_timeline || [];
  return events.find((item) => item.payload?.tool === toolName)?.payload || {};
}

function toStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}
