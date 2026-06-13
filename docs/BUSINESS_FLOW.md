# 业务流程说明

本文档描述当前 Agent Hospital-lite 的业务流程。系统目标是展示一个可运行的 healthcare 多 agent 服务闭环，而不是只运行单个问诊 prompt。

## 系统层次

```text
Kotlin Spring Boot Backend
  -> 接收请求
  -> 创建任务
  -> 发布 Kafka 消息
  -> 监听结果并更新任务状态

Kafka
  -> ai.symptom.query
  -> ai.symptom.result

Python AI Worker
  -> 消费任务
  -> 运行 HospitalOrchestrator
  -> 返回 workflow result

Python Hospital Workflow
  -> 调用医院角色 agent
  -> 角色 agent 可以调用内部 tool
```

## Agent 和 Tool 的边界

Agent 是医院业务角色，负责做决策、产生交接信息、推动流程继续向下走。比如护士分诊、全科医生、专科医生、药房安全、随访协调。

Tool 是 agent 内部使用的能力，负责完成一个具体功能。比如 `AIConsultationTool` 可以做症状抽取、知识检索和 LLM 咨询综合，但它本身不是顶层医院角色。

因此当前结构是：

```text
app/agents/       顶层医院角色 agent
app/tools/        agent 内部工具
app/workflows/    工作流编排
```

## Agent Hospital-lite Flow

```text
IntakeAgent
  -> 记录患者本次就诊文本

AppointmentAgent
  -> 判断就诊类型和优先级

TriageNurseAgent
  -> 检查紧急程度和危险信号

  -> high urgency:
     EmergencyPhysicianAgent
     -> 识别即时安全行动，进入急诊分支

  -> standard urgency:
     GeneralPractitionerAgent
     -> 进入普通门诊分支

GeneralPractitionerAgent
  -> 做全科初评，判断是否需要专科会诊

SpecialistRouterAgent
  -> 根据病例文本选择需要激活的专科角色，不再默认运行所有专科

RespiratorySpecialistAgent / CardiologySpecialistAgent /
InfectiousDiseaseSpecialistAgent / NeurologySpecialistAgent
  -> 只在被 SpecialistRouterAgent 选中时产生对应专科视角的会诊意见

AIConsultationTool
  -> 被 GeneralPractitionerAgent 作为内部工具调用
  -> 内部执行症状抽取、知识检索和 LLM 咨询综合

LabAdvisorAgent
  -> 给出检查建议

PharmacySafetyAgent
  -> 做 demo 级别的用药安全检查

CarePlanAgent
  -> 汇总诊疗计划

FollowUpAgent
  -> 在普通门诊分支给出随访计划

DispositionCoordinatorAgent
  -> 汇总分诊、检查、药房和随访信息，决定急诊复评或门诊随访等 demo 级去向

FinalHospitalReportAgent
  -> 生成最终 workflow report
```

当前 workflow 是有分支的：

```text
TriageNurseAgent
  -> emergency_branch
     -> EmergencyPhysicianAgent
     -> GeneralPractitionerAgent
     -> SpecialistRouterAgent
     -> selected SpecialistAgents
     -> LabAdvisorAgent
     -> PharmacySafetyAgent
     -> DispositionCoordinatorAgent
     -> FinalHospitalReportAgent

  -> outpatient_branch
     -> GeneralPractitionerAgent
     -> SpecialistRouterAgent
     -> selected SpecialistAgents
     -> LabAdvisorAgent
     -> PharmacySafetyAgent
     -> CarePlanAgent
     -> FollowUpAgent
     -> DispositionCoordinatorAgent
     -> FinalHospitalReportAgent
```

`HospitalOrchestrator` 会在输出中返回 `executed_path` 和 `workflow_decisions`，用于展示实际执行路径和每个分支选择的原因。

## LLM 使用位置

可使用 LLM 的角色 agent：

```text
GeneralPractitionerAgent
EmergencyPhysicianAgent
RespiratorySpecialistAgent
CardiologySpecialistAgent
InfectiousDiseaseSpecialistAgent
NeurologySpecialistAgent
CarePlanAgent
FinalHospitalReportAgent
```

规则或确定性 agent：

```text
IntakeAgent
AppointmentAgent
TriageNurseAgent
SpecialistRouterAgent
LabAdvisorAgent
PharmacySafetyAgent
FollowUpAgent
DispositionCoordinatorAgent
```

内部 tool 中也可以使用 LLM：

```text
AIConsultationTool
  -> RagMcpClient
  -> LlmClient
```

## Demo 命令

Mock LLM demo：

```powershell
python -B -m app.main `
  --case-text "fever, cough, chest discomfort and confusion" `
  --patient-id p001 `
  --doctor-id d001 `
  --output outputs\hospital_mock_demo.json `
  --mock-llm `
  --print-json
```

Real LLM demo：

```powershell
python -B -m app.main `
  --case-text "67-year-old male with fever, productive cough, chest discomfort and confusion." `
  --patient-id p001 `
  --doctor-id d001 `
  --output outputs\hospital_demo.json `
  --print-json
```
