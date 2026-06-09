# Business Flow

本文档描述当前 healthcare multi-agent uncertainty modeling 样例系统的业务流程。

## System Layers

```text
Kotlin Spring Boot Backend
  -> receives symptom query request
  -> creates AI task
  -> publishes Kafka message
  -> listens for AI result and updates task status

Kafka
  -> ai.symptom.query
  -> ai.symptom.result

Python AI Worker
  -> consumes symptom query task
  -> runs multi-agent workflow
  -> returns workflow result
```

## Task Status

```text
RECEIVED
  Backend accepted the request and created a task.

PUBLISHED
  Backend published the task to Kafka.

COMPLETED
  Python worker finished the workflow and returned a ready result.

NEEDS_DATA
  Workflow ran, but required configuration or data was missing.

FAILED
  Backend or worker failed during execution.
```

## Kafka Topics

```text
ai.symptom.query
  Spring Boot -> Python AI Worker

ai.symptom.result
  Python AI Worker -> Spring Boot
```

## Request Message

```json
{
  "taskId": "task-001",
  "doctorId": "d001",
  "patientId": "p001",
  "caseText": "fever, cough, chest discomfort",
  "question": "What diseases should be considered?",
  "language": "zh-CN",
  "metadata": {
    "source": "springboot-backend"
  }
}
```

## Result Message

```json
{
  "taskId": "task-001",
  "status": "ready",
  "result": {},
  "errorMessage": null
}
```

## Current Agent Flow

```text
SymptomExtractionAgent
  -> normalizes explicit symptom text

BranchPlannerAgent
  -> marks workflow branches active or skipped

MedicalKnowledgeAgent
  -> retrieves local disease-symptom evidence through RagMcpClient

RetrievalQualityAgent
  -> classifies retrieved evidence as sufficient, weak, or missing

DifferentialDiagnosisAgent
  -> calls LLM for candidate reasoning in the real workflow

CandidateSupportAgent
  -> checks whether candidate output is supported by retrieved evidence

EvidenceReviewAgent
  -> calls LLM for evidence review in the real workflow

RagLlmConsistencyAgent
  -> compares retrieved evidence with candidate output

SafetyCheckAgent
  -> checks local red-flag rules

UncertaintyAssessmentAgent
  -> collects explicit uncertainty signals

ReportAgent
  -> calls LLM for final report in the real workflow
```

## Scenario Replay Flow

Scenario replay replaces real data-producing agents with controlled agents:

```text
ScenarioMedicalKnowledgeAgent
  -> uses mock_rag_documents

ScenarioDifferentialDiagnosisAgent
  -> uses mock_llm_output

ScenarioEvidenceReviewAgent
  -> uses mock_evidence_review_output or an empty controlled output

ScenarioReportAgent
  -> assembles report data without live LLM
```

This keeps automated uncertainty tests reproducible.
