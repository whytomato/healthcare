# 业务流程说明

当前系统同时推进两条线：一条是 Python 侧的 Agent Hospital workflow，另一条是 `backend/` 内的 Spring Boot 多模块微服务骨架。

## 微服务链路

```text
encounter-service
  -> REST 创建 Patient Encounter / AI task
  -> 持久化 patient_encounters
  -> 发布 Kafka healthcare.encounter.created

triage-service
  -> 消费 healthcare.encounter.created
  -> 执行分诊评估
  -> 发布 Kafka ai.symptom.query

Python AI Worker
  -> 消费 ai.symptom.query
  -> 运行 HospitalOrchestrator
  -> 执行过程中发布 ai.workflow.progress
  -> 发布 ai.symptom.result

Hospital Role Agents
  -> 在具体角色需要时调用 PatientHistoryLookupTool
  -> PatientHistoryLookupTool 按 patientId 查询 clinical-record-service 的 Patient History Summary
  -> 通过 ClinicalToolRegistry 自主调用或跳过 guideline、lab、imaging、medication、bed、referral、follow-up、human-review 等内部 tool

encounter-service
  -> 消费 ai.workflow.progress
  -> 持久化 workflow_progress_events
  -> 消费 ai.symptom.result
  -> 更新任务状态和错误信息
  -> encounter-service 只维护 task 状态，不保存完整 workflow result

clinical-record-service
  -> 消费 ai.symptom.result
  -> 持久化 workflow_result_records
  -> clinical-record-service 负责完整 Workflow Record
  -> 保存结构化病历、agent path、workflow decisions、handoff timeline、care pathway、AI consultation、final report
  -> 提供 taskId 查询接口和 patientId 历史病历摘要接口

care-coordination-service
  -> POST /api/care/coordination-plans
  -> 生成 followUpActions、referralActions、admissionActions、humanReviewRequired
  -> 不消费 Kafka；由 AdmissionCoordinatorAgent 通过 CareCoordinationTool 同步调用
  -> 服务不可用时，CareCoordinationTool 返回 unavailable 并生成本地 fallback plan
```

## 持久化数据

本地演示使用 `infra/docker-compose.kafka.yml` 启动 Kafka 和 Docker Postgres。默认连接为：

```text
jdbc:postgresql://localhost:5432/healthcare
user / password
```

当前落库边界：

```text
encounter-service
  patient_encounters
  -> taskId、状态、患者/医生标识、原始主诉、错误信息

encounter-service
  workflow_progress_events
  -> taskId、agent、event type、decision、decision scope、target agents、parallel group、event index

clinical-record-service
  workflow_result_records
  -> taskId、patientId、状态、executed_path、workflow_decisions、handoff_timeline、专科选择、care_pathway、AI consultation、final_report、raw_result
```

## 当前后端接口

```text
encounter-service
  POST /api/ai/symptom-query
  GET  /api/ai/tasks/{taskId}
  GET  /api/ai/tasks/{taskId}/progress

triage-service
  POST /api/triage/assess
  GET  /api/triage/health

clinical-record-service
  POST /api/records/workflow-results
  GET  /api/records/{taskId}
  GET  /api/records/patients/{patientId}/history

care-coordination-service
  POST /api/care/coordination-plans
  GET  /health
```

## 当前 Kafka Topics

```text
healthcare.encounter.created
  encounter-service 发布
  triage-service 消费

ai.symptom.query
  triage-service 发布
  Python AI worker 消费

ai.workflow.progress
  Python AI worker 发布
  encounter-service 消费

ai.symptom.result
  Python AI worker 发布
  encounter-service 消费
  clinical-record-service 消费
```

## Agent / Tool / Policy 边界

```text
Agent:
  医院业务角色，负责产生结构化交接信息和业务判断。

Tool:
  agent 内部使用的能力，例如知识检索、LLM 咨询综合、检验/影像/用药/随访/人工审核/照护协调。
  tool 可以是纯本地 demo 能力，也可以封装对微服务的调用。

Policy / Planner:
  workflow 规划和路由策略，例如 HospitalWorkflowPlanner。
```

## 当前 LLM 使用位置

LLM-capable role agents：

```text
EmergencyPhysicianAgent
GeneralPractitionerAgent
RespiratorySpecialistAgent
CardiologySpecialistAgent
InfectiousDiseaseSpecialistAgent
NeurologySpecialistAgent
CarePlanAgent
FinalHospitalReportAgent
```

内部 tool 中也可以使用 LLM：

```text
AIConsultationTool
  -> RagMcpClient
  -> LlmClient
```

## 当前分支

```text
RegistrationAgent
  -> IntakeAgent
  -> NurseVitalsAgent

AppointmentAgent / NurseVitalsAgent
  -> TriageNurseAgent

TriageNurseAgent
  -> emergency_branch
     -> DepartmentRouterAgent
     -> EmergencyPhysicianAgent
     -> GeneralPractitionerAgent
     -> SpecialistRouterAgent
     -> selected SpecialistAgents
     -> DiagnosticOrderAgent
     -> LabAdvisorAgent
     -> LabResultInterpreterAgent
     -> ImagingInterpreterAgent
     -> PharmacySafetyAgent
     -> MedicationPlanAgent
     -> DispositionCoordinatorAgent
     -> AdmissionCoordinatorAgent
     -> FinalHospitalReportAgent

  -> outpatient_branch
     -> DepartmentRouterAgent
     -> GeneralPractitionerAgent
     -> SpecialistRouterAgent
     -> selected SpecialistAgents
     -> DiagnosticOrderAgent
     -> LabAdvisorAgent
     -> LabResultInterpreterAgent
     -> ImagingInterpreterAgent
     -> PharmacySafetyAgent
     -> MedicationPlanAgent
     -> CarePlanAgent
     -> FollowUpAgent
     -> DispositionCoordinatorAgent
     -> AdmissionCoordinatorAgent
     -> FinalHospitalReportAgent
```

`HospitalOrchestrator` 现在以 agent 输出的 `handoff_to` 作为真实调度输入：入口从 `registration_agent` 开始，下游 agent 由上游 handoff 推入队列，专科 handoff 可并发执行。`HospitalWorkflowPlanner` 保留为 fallback 和 `workflow_decisions` 捕获边界，不再强行提前执行未被 handoff 的 agent。

`handoff_timeline` 是 workflow 展示主契约，用于记录 agent 完成、行政建档、生命体征、分诊、科室路由、检查医嘱、检验解释、影像解释、用药计划、处置、住院协调、交接、并发专科 fan-out 和 fan-in 汇总事件。

前端 `AgentWorkflowGraph.vue` 使用 Vue Flow 将 `handoff_timeline` 渲染为本次 Patient Encounter 的 workflow 覆盖图。图中 agent 节点表示医院角色，实线表示本次实际 handoff，虚线表示系统存在但本次未触发的分支，边标签显示 agent 决策，tool 节点可按需打开以展示 `tool_invoked` / `tool_skipped` / unavailable。

## Patient History Summary

`clinical-record-service` 现在同时承担 demo 级历史病历摘要能力。它按 `patientId` 从已持久化的 `workflow_result_records` 聚合：

```text
recentEncounters
knownConditions
allergies
currentMedications
previousDispositions
lastFinalReports
```

`RegistrationAgent`、`PharmacySafetyAgent`、`CarePlanAgent`、`FollowUpAgent` 和 `FinalHospitalReportAgent` 会在各自角色决策中主动调用 `PatientHistoryLookupTool` 查询该摘要。Python AI Worker 不预取病历，也不把病历塞入 `HospitalContext.metadata`。历史病历会影响 registration、pharmacy safety、care plan、follow-up 和 final report，但不会覆盖 Current Encounter Safety Signal，也不会直接降低急诊红旗分流。tool 调用会进入 `handoff_timeline` / realtime progress，前端可以展示哪个 agent 在何时查了病历。

前端 Patient History 面板会把历史 final report excerpt 作为 Markdown 渲染。如果历史记录中保存的是结构化 JSON final report，前端会先提取 `summary`、`findings`、`recommendations`、`handoff_reason` 和 `confidence`，再转换为可读 Markdown，避免把原始 JSON 展示给用户。
