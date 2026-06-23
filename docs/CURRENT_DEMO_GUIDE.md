# Current Demo Guide

This guide explains the current implementation state for meetings and manual demos.

## One-Sentence Pitch

This project is a healthcare multi-agent workflow test system. A patient encounter is not handled by one prompt; it is routed through hospital role agents, agent-selected tools, backend microservices, realtime progress events, persistent clinical records, and a frontend workflow graph.

## Current Default Workflow

```text
RegistrationAgent
  -> IntakeAgent + NurseVitalsAgent
  -> AppointmentAgent + TriageNurseAgent
  -> DepartmentRouterAgent
  -> EmergencyPhysicianAgent or GeneralPractitionerAgent
  -> SpecialistRouterAgent
  -> selected specialist agents in parallel
  -> LabResultInterpreterAgent + ImagingInterpreterAgent
  -> OrderingClinicianReviewAgent
  -> PharmacySafetyAgent
  -> MedicationPlanAgent
  -> CarePlanAgent / DispositionCoordinatorAgent
  -> AdmissionCoordinatorAgent
  -> FinalHospitalReportAgent
```

`LabAdvisorAgent` and `DiagnosticOrderAgent` are paused in the default path. Their code remains available, but the current demo follows the hospital-style loop where the ordering clinician requests exams, results are interpreted, and then results return to the ordering clinician before medication and disposition.

## ER Microservice Chain

High-urgency cases make `EmergencyPhysicianAgent` call these tools:

```text
EmergencyEncounterTool     -> emergency-encounter-service
PractitionerAssignmentTool -> practitioner-service
ResourceReservationTool    -> resource-service
ExamSchedulingTool         -> scheduling-service
```

The important point is separation of ownership: agents decide what to do; tools call services; services own business state such as emergency encounter state, staff assignment, resource capacity, and exam scheduling.

`practitioner-service` and `resource-service` are Postgres-backed demo schedulers now. Practitioner assignment records active staff load and unavailable specialties. Resource reservation records available rooms, beds, monitors, partial reservations, and unavailable resources. Start the Python worker with `--concurrency 4` for ER surge demos so multiple Kafka tasks are processed at the same time.

## Frontend Demo Steps

1. Start Kafka/Postgres, backend services, Python worker with `--concurrency 4`, and frontend.
2. Open the Vue workbench.
3. Run one normal demo case and switch to the Graph view.
4. Turn on `Tool nodes` to show tool calls and unavailable/fallback states.
5. Run `Emergency Surge Scenario` with several patients.
6. Inspect surge cards for `resource_reservation` readiness and `practitioner_assignment` staffing.
7. Open completed surge tasks and inspect the same tool nodes in the Graph view.

## How To Explain The Graph

- Solid highlighted edges are the actual path for this encounter.
- Available edges show possible branches that were not taken.
- Skipped edges/tools show explicit agent decisions to avoid a branch or tool.
- Tool nodes show calls made by agents, including ready, skipped, and unavailable states.
- Decision labels are edge labels, not separate decision nodes.

## What To Emphasize

- Workflow is handoff-driven, not a fixed linear chain.
- Specialist branches can run in parallel.
- The current diagnostic loop is `exam scheduling -> lab/imaging interpretation -> ordering clinician review`.
- Microservices are used where state ownership matters, especially records, care coordination, ER encounter state, practitioners, resources, and scheduling.
- The surge demo is a real concurrent workflow demo, not a mocked frontend animation.
- For repeated manual surge runs, release a completed task's staff/resources with:
  `POST /api/practitioners/emergency-assignments/{taskId}/release` and
  `POST /api/resources/emergency-reservations/{taskId}/release`.
