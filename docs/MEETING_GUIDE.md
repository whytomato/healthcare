# 组会讲解稿：Healthcare Multi-Agent Workflow

这份文档用于组会展示。推荐讲法是：先讲系统目标，再讲整体链路，然后用五个 demo 对照前端 Graph 解释 agent 分支、tool 调用和微服务架构。

## 1. 一句话介绍

本项目是一个 healthcare 场景下的多 agent + 微服务被测系统。它不是单一问答模型，而是把一次 Patient Encounter 拆成多个医院角色 agent，由这些 agent 根据当前输入、病人历史、tool 调用结果和上游 handoff，动态决定下一步 workflow。

可以这样开场：

> 我们构建的是一个医院服务流程型的多 agent 系统。输入不是简单症状问答，而是一名患者的一次就诊请求。系统会经过登记、问诊、生命体征、分诊、科室路由、急诊或门诊医生、多专科会诊、检查医嘱、检验影像解释、药房安全、用药计划、随访/住院协调和最终报告。不同输入会触发不同 agent、不同分支、不同 tool。

## 2. 前端 Graph 怎么看

前端中间区域的 `Graph` 是本次真实 workflow 的覆盖图。

- 高亮实线：本次真实走过的 agent handoff。
- 灰色虚线：系统存在但本次没有走的分支。
- 红色虚线：本次明确跳过的分支或 tool。
- 线上的文字：agent 做出的分支决策，例如 `Outpatient Branch`、`Emergency Branch`、`Specialist Consultation Branch`。
- `Tool nodes` 开关：打开后可以看到 agent 调用了哪些 tool，哪些 tool 被跳过或不可用。
- `Unused branches` 开关：关闭后只看本次实际路径；打开后可以解释完整医院能力图。

建议演示时先关闭 `Tool nodes`，讲清楚主 workflow；然后打开 `Tool nodes`，讲 agent 如何主动调用外部能力。

## 3. 整体微服务链路

当前系统有四个 Spring Boot 微服务和一个 Python AI Worker。

```text
Frontend
  -> encounter-service 创建 Patient Encounter
  -> Kafka: healthcare.encounter.created
  -> triage-service 转成 AI workflow 请求
  -> Kafka: ai.symptom.query
  -> Python AI Worker 执行 HospitalOrchestrator
       -> Hospital Role Agents
       -> PatientHistoryLookupTool 调 clinical-record-service
       -> CareCoordinationTool 调 care-coordination-service
  -> Kafka: ai.workflow.progress 实时进度
  -> Kafka: ai.symptom.result 最终结果
  -> encounter-service 更新任务状态
  -> clinical-record-service 保存完整 Workflow Record
  -> Frontend 展示 Timeline、Graph、Patient History、Final Report
```

四个服务职责：

| 服务 | 端口 | 职责 |
| --- | --- | --- |
| encounter-service | 8081 | 创建就诊任务、维护 task status、保存 realtime progress、给前端查询任务 |
| triage-service | 8082 | 消费 encounter event，转发为 AI workflow 请求 |
| clinical-record-service | 8083 | 保存完整 workflow record，提供历史病历摘要 |
| care-coordination-service | 8084 | 生成随访、转诊、住院/留观、人工审核等后续安排 |

一句话解释：

> encounter-service 管任务，triage-service 管事件转发，clinical-record-service 管病历持久化，care-coordination-service 管后续安排。真正的多 agent 医院 workflow 在 Python AI Worker 里执行。

## 4. Agent 角色与作用

| Agent | 作用 | 关键决策 / 输出 |
| --- | --- | --- |
| RegistrationAgent | 登记、识别新病人/复诊、主动查历史病历 | 是否完成登记，handoff 给 intake 和 nurse vitals |
| IntakeAgent | 采集主诉和上下文 | handoff 给 appointment 和 triage |
| NurseVitalsAgent | 记录建议生命体征，识别异常体征/风险词 | `stable_vitals_recorded` 或 `abnormal_vitals_detected` |
| AppointmentAgent | 就诊优先级和预约分类 | handoff 给 triage |
| TriageNurseAgent | 识别红旗和紧急程度 | `outpatient_branch` 或 `emergency_branch` |
| DepartmentRouterAgent | 决定进入急诊医生还是普通门诊医生 | emergency path 或 outpatient path |
| EmergencyPhysicianAgent | 急诊高风险评估 | 高风险病人先走急诊评估 |
| GeneralPractitionerAgent | 全科医生综合评估 | 可调用 AIConsultationTool，handoff 给 specialist router |
| SpecialistRouterAgent | 选择需要并发会诊的专科 | respiratory / cardiology / infectious disease / neurology |
| RespiratorySpecialistAgent | 呼吸科会诊 | 咳嗽、气促、胸片等呼吸系统意见 |
| CardiologySpecialistAgent | 心内科会诊 | 胸痛、心血管风险、肌钙蛋白等 |
| InfectiousDiseaseSpecialistAgent | 感染科会诊 | 发热、感染风险、血培养/病原体检查 |
| NeurologySpecialistAgent | 神经科会诊 | 意识混乱、神经系统红旗 |
| LabAdvisorAgent | 汇总专科意见，形成检查建议 | handoff 给 diagnostic orders |
| DiagnosticOrderAgent | 生成检验和影像医嘱 | lab_order / imaging_order |
| LabResultInterpreterAgent | 获取并解释检验结果占位 | lab_result_fetch |
| ImagingInterpreterAgent | 获取并解释影像结果占位 | imaging_result_fetch |
| PharmacySafetyAgent | 用药安全、过敏史、相互作用检查 | patient_history_lookup / medication_interaction |
| MedicationPlanAgent | 形成用药计划 | 是否需要药师审核 |
| CarePlanAgent | 门诊护理和照护计划 | 参考历史病历生成 care plan |
| FollowUpAgent | 随访和转诊安排 | follow_up_scheduling / referral_scheduling |
| DispositionCoordinatorAgent | 判断最终处置方向 | outpatient follow-up / emergency reassessment，是否 human review |
| AdmissionCoordinatorAgent | 判断住院/留观路径，调用后续安排服务 | bed_availability / care_coordination |
| FinalHospitalReportAgent | 汇总最终报告 | 生成 final hospital workflow report |

## 5. Tool 的功能

Tool 不是顶层 agent，而是 agent 可以选择调用或跳过的能力。

| Tool | 调用者 | 功能 |
| --- | --- | --- |
| PatientHistoryLookupTool | Registration、PharmacySafety、CarePlan、FollowUp、FinalReport | 查询 clinical-record-service 的历史病历摘要 |
| GuidelineLookupTool | TriageNurse | 有红旗时查急诊安全建议；无红旗时跳过 |
| AIConsultationTool | GeneralPractitioner | 结合 RAG/LLM 生成咨询意见 |
| LabOrderTool | DiagnosticOrder | 创建 demo 检验医嘱 |
| ImagingOrderTool | DiagnosticOrder | 创建 demo 影像医嘱 |
| LabResultFetchTool | LabResultInterpreter | 获取 demo 检验结果占位 |
| ImagingResultFetchTool | ImagingInterpreter | 获取 demo 影像结果占位 |
| MedicationInteractionTool | PharmacySafety | 检查过敏史、当前用药、相互作用风险 |
| FollowUpSchedulingTool | FollowUp | 生成复诊安排占位 |
| ReferralSchedulingTool | FollowUp | 生成专科转诊安排占位 |
| HumanReviewRequestTool | DispositionCoordinator | 高风险或多专科复杂病例触发人工审核 |
| BedAvailabilityTool | AdmissionCoordinator | 高紧急度时检查急诊留观/床位能力 |
| CareCoordinationTool | AdmissionCoordinator | 调 care-coordination-service 生成后续安排；服务不可用时 fallback |

关键讲法：

> agent 负责判断该做什么，tool 负责提供某类能力。tool 是否调用不是预先固定的，而是由对应角色 agent 在自己的职责范围内决定。

## 6. 五个 Demo 怎么讲

### 6.1 普通门诊

输入特征：

- 34 岁女性。
- 咳嗽、低热、咽痛、乏力三天。
- 没有胸痛、意识混乱、严重气促。

图上重点：

```text
Triage Nurse -> Department Router: Outpatient Branch
Department Router -> General Practitioner
Specialist Router -> Respiratory + Infectious Disease
```

讲法：

> 这个 demo 展示标准门诊路径。系统先完成登记、问诊、生命体征和分诊。由于当前输入没有明显红旗，TriageNurseAgent 决策为 outpatient branch。因此 DepartmentRouterAgent 不会进入 EmergencyPhysicianAgent，而是进入 GeneralPractitionerAgent。随后 SpecialistRouterAgent 根据咳嗽、发热等症状选择呼吸科和感染科两个并发会诊分支。后续系统继续生成检查医嘱、解释检验和影像结果、做药房安全检查、生成用药计划、护理计划、随访安排和最终报告。

Tool 重点：

- `guideline_lookup` 跳过，因为没有急性红旗。
- `lab_order`、`imaging_order` 调用。
- `human_review_request` 跳过。
- `bed_availability` 跳过。

### 6.2 低风险随访

输入特征：

- 45 岁男性。
- 过敏复诊，症状改善。
- 轻微鼻塞，没有发热、胸痛、呼吸困难或神经症状。

图上重点：

```text
Triage Nurse -> Department Router: Outpatient Branch
Specialist Router -> Respiratory only
Care Plan -> Follow Up
```

讲法：

> 低风险随访也走门诊分支，但它比普通门诊更轻。系统不会进入急诊，也不会触发多专科扩展，只保留必要的呼吸相关评估。这个 demo 的重点不是急诊诊断，而是展示 care plan 和 follow-up：系统会生成复诊建议、后续安排和专科转诊占位。

Tool 重点：

- `guideline_lookup` 跳过。
- `follow_up_scheduling` 调用。
- `referral_scheduling` 调用。
- `human_review_request` 跳过。
- `bed_availability` 跳过。

### 6.3 急诊多专科

输入特征：

- 67 岁男性。
- 发热、咳痰、胸部不适、呼吸困难、意识混乱。
- 12 小时内加重。

图上重点：

```text
Triage Nurse -> Department Router: Emergency Branch
Department Router -> Emergency Physician
Specialist Router -> Respiratory + Cardiology + Infectious Disease + Neurology
```

讲法：

> 这个 demo 展示高风险急诊路径。输入里有胸部不适、呼吸困难、意识混乱和快速加重等红旗，因此 TriageNurseAgent 判断为 emergency branch。DepartmentRouterAgent 会优先把病人交给 EmergencyPhysicianAgent，而不是直接走普通门诊。之后系统进入多专科并发会诊：呼吸科处理呼吸感染风险，心内科处理胸痛和心血管风险，感染科处理发热感染风险，神经科处理意识混乱风险。

Tool 重点：

- `guideline_lookup` 调用，因为有红旗。
- `lab_order` 和 `imaging_order` 优先级更高。
- `human_review_request` 调用。
- `bed_availability` 调用。
- `care_coordination` 调用。

### 6.4 人工审核

输入特征：

- 72 岁患者。
- 胸痛、气短、高热、意识混乱。
- 近期换药。
- 家属不确定过敏史。
- 询问是否需要住院。

图上重点：

```text
Emergency Branch
四专科并发
DispositionCoordinatorAgent -> HumanReviewRequestTool
```

讲法：

> 人工审核 demo 的主路径和急诊多专科相似，也会触发 emergency branch 和四专科并发。但它的展示重点是 agent 主动触发人工审核。由于患者年龄高、症状复杂、近期换药、过敏史不确定，并且涉及是否住院，DispositionCoordinatorAgent 会调用 HumanReviewRequestTool。这个 demo 说明系统不是所有场景都强行自动化，而是在高风险和信息不完整时把病例升级给人工复核。

Tool 重点：

- `human_review_request` 调用。
- `medication_interaction` 调用。
- `patient_history_lookup` 调用。
- `bed_availability` 调用。
- `care_coordination` 调用。

### 6.5 服务降级

输入特征：

- 52 岁患者。
- 咳嗽发热。
- 预期使用既往病历和后续安排服务。

图上重点：

```text
服务在线时：类似普通门诊
关闭 care-coordination-service 时：CareCoordinationTool -> unavailable
关闭 clinical-record-service 时：PatientHistoryLookupTool -> unavailable
```

讲法：

> 服务降级 demo 不是为了展示新的医学分支，而是展示微服务依赖不可用时 workflow 如何处理。正常情况下它会像普通门诊一样走 outpatient branch，并调用历史病历和后续安排服务。如果关闭 care-coordination-service，AdmissionCoordinatorAgent 调用 CareCoordinationTool 会失败，tool 状态变为 unavailable，但整个 workflow 不会崩溃，而是使用本地 fallback plan 继续生成最终报告。如果关闭 clinical-record-service，历史病历查询会不可用，agent 会使用空历史摘要继续执行。

Tool 重点：

- `care_coordination` 可展示 unavailable。
- `patient_history_lookup` 可展示 unavailable。
- workflow 应继续完成。
- final report 中可以说明服务降级。

## 7. 关闭 care-coordination-service 会发生什么

关闭 `care-coordination-service`，也就是端口 `8084` 后：

```text
AdmissionCoordinatorAgent
  -> CareCoordinationTool
  -> POST http://localhost:8084/api/care/coordination-plans
  -> request failed / timeout
  -> status = unavailable
  -> local fallback plan
  -> workflow continues
```

结果：

- agent workflow 不会失败。
- final report 仍然生成。
- `care_coordination` tool 状态变成 `unavailable`。
- Graph 打开 `Tool nodes` 后可以看到不可用 tool。
- 对急诊病例，fallback 会要求检查急诊留观能力并可能要求人工审核。
- 对门诊病例，fallback 会说明无需住院协调。

可以这样总结：

> care-coordination-service 做成微服务，不是因为它现在逻辑多复杂，而是为了展示 agent 调用外部医院业务系统、处理服务不可用和 fallback 的能力。直接让 agent 生成后续安排当然可以，但那样无法展示微服务依赖、tool unavailable 和系统降级。

## 8. 收尾总结

最后可以这样收尾：

> 这五个 demo 覆盖了从普通门诊到复杂急诊的不同路径。普通门诊展示 outpatient branch；低风险随访展示轻症复诊和后续安排；急诊多专科展示 emergency branch 和多专科并发；人工审核展示高风险情况下 human review tool 被主动触发；服务降级展示微服务不可用时的 fallback。通过同一张 workflow graph，我们可以看到系统不是固定链式执行，而是多个医院角色 agent 基于当前输入、上游 handoff、历史病历和 tool 调用结果动态选择分支，并形成完整的 Patient Encounter Workflow Record。
