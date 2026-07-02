import type { ClinicalRecord } from "./types";

export async function loadSurgeClinicalRecordWithTools(
  taskId: string,
  requestRecord: (taskId: string) => Promise<ClinicalRecord>,
  wait: (milliseconds: number) => Promise<unknown>
) {
  let lastRecord: ClinicalRecord | null = null;
  for (let attempt = 0; attempt < 10; attempt += 1) {
    const record = await requestRecord(taskId);
    if (hasSurgeToolPayloads(record)) return record;
    lastRecord = record;
    await wait(900);
  }
  return lastRecord || requestRecord(taskId);
}

export function hasSurgeToolPayloads(record: ClinicalRecord) {
  const events = record.handoffTimeline || record.rawResult?.handoff_timeline || [];
  return ["resource_reservation", "practitioner_assignment"].every((tool) => {
    return events.some((event) => event.payload?.tool === tool);
  });
}
