import type { DemoCase } from "./types";

export const demoCases: DemoCase[] = [
  {
    id: "emergency_multi_specialty",
    name: "Emergency multi-specialty",
    preview: "Chest pain, fever, dyspnea, and confusion trigger ER-first routing and parallel specialists.",
    patientId: "p-emergency-001",
    doctorId: "d-er-001",
    language: "zh-CN",
    caseText:
      "A 67-year-old male has fever, productive cough, chest discomfort, shortness of breath and confusion. He looks acutely ill and the family reports worsening symptoms over the last 12 hours."
  },
  {
    id: "standard_outpatient",
    name: "Standard outpatient",
    preview: "Cough and low-grade fever without active red flags stay on the outpatient route.",
    patientId: "p-outpatient-001",
    doctorId: "d-gp-001",
    language: "zh-CN",
    caseText:
      "A 34-year-old female has cough, low-grade fever, sore throat and fatigue for three days. She is alert, able to drink fluids, and reports no chest pain, confusion or severe shortness of breath."
  },
  {
    id: "low_risk_followup",
    name: "Low-risk follow-up",
    preview: "Improving symptoms highlight the follow-up and disposition branch.",
    patientId: "p-followup-001",
    doctorId: "d-followup-001",
    language: "zh-CN",
    caseText:
      "A 45-year-old male requests follow-up after a recent outpatient visit for mild seasonal allergies. Symptoms are improving with mild nasal congestion and no fever, chest pain, dyspnea or neurologic symptoms."
  },
  {
    id: "human_review",
    name: "Human review",
    preview: "Multiple red flags and uncertain allergy history show human review tool selection.",
    patientId: "p-review-001",
    doctorId: "d-review-001",
    language: "zh-CN",
    caseText:
      "A 72-year-old patient reports chest pain, shortness of breath, high fever and confusion after recent medication changes. The family is unsure about allergies and asks whether admission is needed."
  },
  {
    id: "service_fallback",
    name: "Service fallback",
    preview: "Use this while a microservice is stopped to show tool unavailable fallback behavior.",
    patientId: "p-fallback-001",
    doctorId: "d-fallback-001",
    language: "zh-CN",
    caseText:
      "A 52-year-old patient has cough and fever with prior outpatient records expected, but external history or care coordination service may be unavailable during this demo."
  }
];

export const emergencySurgeTemplate: DemoCase = {
  id: "emergency_surge_template",
  name: "Emergency surge",
  preview: "Concurrent high-acuity patients compete for finite ER staff, rooms, monitors, and exam scheduling.",
  patientId: "p-surge",
  doctorId: "d-er-surge",
  language: "zh-CN",
  caseText:
    "A 68-year-old patient arrives with chest pain, shortness of breath, fever and confusion. The patient looks acutely ill and requires emergency physician review, monitored space, staff assignment and urgent exams."
};
