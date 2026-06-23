# TODO

## 2026-06-23 completed in current pass

- [x] Paused `LabAdvisorAgent` and `DiagnosticOrderAgent` in the current default workflow without deleting their implementations.
- [x] Added the ordering-clinician review loop: ordering clinician or specialist schedules exams, lab/imaging interpreters process results, and `OrderingClinicianReviewAgent` reviews findings before pharmacy safety.
- [x] Added a frontend `Emergency Surge Scenario` panel that submits multiple real ER encounters concurrently and displays `resource_reservation` readiness from final clinical records.
- [x] Split frontend demo cases, shared types, encounter sidebar, and surge panel out of `App.vue`.
- [x] Updated workflow graph static coverage to show the current exam-review loop instead of the old lab-advisor/diagnostic-order path.
- [x] Added `docs/CURRENT_DEMO_GUIDE.md` for the current meeting/demo explanation.
- [x] Persisted ER resource inventory and reservations in Postgres-backed `resource-service`, with transactional reservation and release by `taskId`.
- [x] Persisted ER practitioner pool and assignments in Postgres-backed `practitioner-service`, with active assignment counts and release by `taskId`.
- [x] Added Python Kafka worker `--concurrency` support for concurrent ER surge task processing.
- [x] Extended frontend ER surge cards to show both resource readiness and practitioner staffing status.

本文档记录当前已经明确的下一步。当前目标是先完成一个可展示的 healthcare 多 agent + 微服务系统，再逐步增加业务复杂性和后续测试建模入口。

## 后续重构约束

- [ ] 将完整业务流程中的服务整理为边界清晰、职责单一、数据所有权明确、接口契约明确的微服务架构。
- [ ] 后续允许调整 Agent Workflow，并允许现有 Agent 退出新流程，但不得删除任何已有 Agent 实现。
- [ ] 本次微服务设计围绕以下六个服务展开：`patient-service`、`clinical-record-service`、`practitioner-service`、`resource-service`、`scheduling-service`、`emergency-encounter-service`。
- [x] 急诊最小演示先落地 `emergency-encounter-service`、`practitioner-service`、`resource-service`、`scheduling-service` 四个业务微服务骨架。
- [x] 高风险急诊 workflow 前置打开急诊 encounter，调用人员分配、资源预留、readiness 回写和急诊检查排程 tool，并把结果写入 `handoff_timeline`。
- [x] `resource-service` 增加最小 constrained capacity 语义，为后续多并发测试暴露 partial / unavailable readiness。
- [x] 分科专家可以作为开单 agent 调用检查排程；检查结果后续应回到开单 agent 复看。
- [ ] `triage-service` 属于已有能力，本次不讨论其内部重新设计；后续只定义它与上述服务的集成契约。
- [ ] 严格区分 Business Microservice 与 Agent Tool：微服务拥有权威业务状态和独立生命周期，Tool 只负责查询或命令服务及本地能力。

## 明日实现：多 agent 医院系统增强

### P0：前端展示 bug

- [x] 修复 `ClinicalRecordPane.vue` 中 Patient History Summary 的渲染 bug，重点检查历史病历摘要、既往 encounters、allergies/current medications/previous dispositions 的空值和数组展示。
- [x] 移除 `WorkflowDisplayPanel.vue` 中 timeline 为空时的旧 `live-flow` 阶段列表。Agent Handoff Timeline 区域只保留真实 `AgentTimeline` 事件流；如果还没有 realtime events，只显示简短 loading/empty state，不再展示 Registration、Patient Intake、Nurse Vitals、Appointment Classification 等临时阶段流程。

### 待拆解：体验与架构增强

- [ ] 完善微服务：优先优化后端服务边界、启动体验、接口契约和持久化一致性；不要求把微服务事件展示进前端 Agent Workflow Graph。

### P1：流程展示增强

- [x] 新增 `Agent Workflow Graph` 前端视图，用图形化方式展示每一次 Patient Encounter 的实际 agent workflow：agent 节点、handoff 边、decision 节点、tool 调用节点、parallel fan-out/fan-in 汇合点。
- [x] `Agent Workflow Graph` 数据来源优先使用 `handoff_timeline` / realtime progress events，不手写固定医院流程图；同一个病例只展示本次实际触发的 agent 和 tool。
- [x] 在 `WorkflowDisplayPanel.vue` 中提供 Timeline / Graph 两种视图切换；Timeline 保留事件细节，Graph 用于汇报时快速看清 agent workflow 和 tool 调用关系。
- [x] Graph 视图验收标准：能区分 agent、decision、tool、fan-out、fan-in；tool 节点显示 tool 名称和 ready/skipped/unavailable 状态；点击或悬停节点能看到对应 timeline event 摘要。

### P1：微服务架构优化

- [x] 明确 `encounter-service` 与 `clinical-record-service` 的职责边界：`encounter-service` 负责 Patient Encounter、task status、realtime progress；`clinical-record-service` 负责 Workflow Record 和 Longitudinal Patient Record，避免两个服务长期重复保存完整 workflow result。
- [x] 整理核心服务和 ER 服务的启动和健康检查体验：`encounter-service`、`triage-service`、`clinical-record-service`、`care-coordination-service`、`emergency-encounter-service`、`practitioner-service`、`resource-service`、`scheduling-service` 都应有清晰端口、health endpoint、README 启动命令和手动验证命令。
- [ ] 补齐微服务契约文档：列出 REST API、Kafka topic、输入/输出消息字段、持久化表职责，作为后续扩展服务的边界说明。
- [x] 增加演示稳定性脚本：已提供 `scripts/start-healthcare-services.ps1` / `scripts/stop-healthcare-services.ps1`，减少手动启动多个 Spring Boot 服务的成本。
- [ ] 微服务事件暂不进入前端 `Agent Workflow Graph`；Graph 聚焦 agent workflow 和 tool 调用，微服务优化先服务于后端架构清晰和运行稳定。

### P0：Agent Workflow 自主决策

- [x] 将“自主决策”统一为 `Role-Scoped Agent Decision`：每个关键 Hospital Role Agent 在自己的角色边界内，基于当前 encounter context、上游 handoff、可用 tools 和必要的 patient history 决定下一步，而不是由全局 planner 预先决定完整流程。
- [x] 提升可展示决策密度：把关键 agent 的判断显式记录为 `decision_made`，重点覆盖 triage、department routing、specialist routing、diagnostics、pharmacy safety、medication planning、disposition、admission/care coordination。
- [x] 强化真实分支差异：普通门诊、急诊、多专科、人工审核、服务不可用 fallback 等路径应在 `handoff_timeline` 和最终 Graph 中呈现出明显不同的 agent path、decision path 和 tool path。
- [x] 增强 agent 自主决策可解释性：每个关键 Hospital Role Agent 输出“本角色为什么继续/跳过某个下游 agent 或 tool”的结构化 decision reason，并进入 `handoff_timeline`。
- [x] 增强 tool 选择展示：把当前 tool 调用从“调用结果”提升为“agent 选择了哪些 tool、跳过哪些 tool、为什么跳过”的 timeline 事件，便于 Graph 视图画出 agent -> tool 的决策边。
- [x] 增加人工审核分支的可展示路径：当 high-risk、service unavailable、LLM 输出不稳定或 care coordination 需要人工确认时，workflow 应出现 human review decision/tool event，而不是只在最终报告里说明。
- [x] 增强 outpatient / emergency / multi-specialty 三类 demo path 的差异：普通门诊不应展示急诊角色，多专科病例应展示并发专科 fan-out/fan-in，急诊病例应展示 emergency physician、diagnostics、pharmacy/admission/care coordination 的完整链路。

## P0：完成可展示闭环

- [ ] 用 IDEA 验证 `backend/pom.xml` 多模块 Maven 工程可以正常导入和编译。
- [ ] 分别启动并验证 `encounter-service`、`triage-service`、`clinical-record-service`、`care-coordination-service` 的 REST 接口。
- [ ] 跑通完整 Kafka 链路：`encounter-service -> healthcare.encounter.created -> triage-service -> ai.symptom.query -> Python AI worker -> ai.symptom.result -> encounter-service`。
- [ ] 确认 `encounter-service` 接收到 `ai.symptom.result` 后能正确更新 task 状态和保存 workflow result。
- [x] 增加一个完整 demo 脚本，自动创建任务、等待 worker 处理、查询最终结果。
- [ ] 修复 README 和 `docs/BUSINESS_FLOW.md` 在 PowerShell 中显示乱码的问题，保证中文文档可读。

## P1：完善后端微服务

- [x] 将 `clinical-record-service` 接入 Kafka，消费 `ai.symptom.result` 或后续 record topic，而不是只提供手工 POST 接口。
- [x] 让 `clinical-record-service` 保存更多结构化字段：`executed_path`、`workflow_decisions`、`care_pathway`、`ai_consultation`、`final_report`。
- [x] 增加 Patient History Summary：按 patientId 从持久化 workflow records 聚合历史病历摘要。
- [x] 让医院角色 agent 通过 `PatientHistoryLookupTool` 主动查询 Patient History Summary，而不是由 Python AI worker 预取。
- [x] 让 `care-coordination-service` 从 skeleton 变成真实服务，处理 disposition、follow-up、referral、admission 等后续安排。
- [x] 将 Python workflow 的 disposition/admission/follow-up 结果接入 `care-coordination-service`，让后续安排从独立微服务生成。
- [ ] 明确是否保留 `encounter-service` 对 `ai.symptom.result` 的消费。如果 `clinical-record-service` 负责结果保存，`encounter-service` 可以只维护 task 状态。
- [ ] 为各服务整理端口、topic、REST API 表，写入 README。
- [x] 增加 Spring Boot 服务启动/停止脚本和 `scripts/demo_healthcare_flow.py`，对齐 eCommerce 的演示体验。

## P1：完善 Agent Workflow

- [x] 增加多种 agent 可选内部 tool：guideline、lab、imaging、medication interaction、bed availability、referral、follow-up、human review，并在 timeline 展示 `tool_invoked` / `tool_skipped`。
- [x] 让 `handoff_to` 参与真实调度：workflow 从 agent handoff 队列推进，`HospitalWorkflowPlanner` 只作为 fallback 和 decision capture。
- [x] 继续增强 handoff 调度：增加更明确的 fan-in barrier、人工审核分支和服务化后续流程。
- [ ] 把规则/策略从 `app/agents/rules.py` 迁移到更清晰的位置，例如 `app/policies/` 或 `app/domain/`。
- [ ] 统一 Python agent 和 `triage-service` 的分诊规则，避免两套规则长期漂移。
- [ ] 增加 LLM 输出结构约束，至少让关键 LLM-capable agent 输出稳定字段，便于前端展示和测试。
- [ ] 增加更多 demo 病例：普通门诊、急诊、多专科、无明显红旗、需要人工审核。

## P2：前端展示

- [x] 新建前端页面，支持输入病例文本、医生 ID、患者 ID。
- [x] 前端调用 `encounter-service` 创建任务。
- [x] 前端轮询任务状态并展示结果。
- [x] 展示 `executed_path` 为 agent 执行时间线。
- [x] 展示 `workflow_decisions` 为分支决策卡片。
- [x] 展示 `selected_specialties`、`care_pathway`、`ai_consultation` 和 `final_report`。
- [x] 给 mock demo 准备固定输入按钮，便于汇报时稳定演示。
- [x] 展示 Patient History Summary，说明本次 workflow 可参考既往病历。
- [x] 将 realtime agent timeline 和 clinical record/report 右栏拆成 Vue 组件，避免 `App.vue` 继续膨胀。

## P2：测试和演示稳定性

- [ ] 增加 backend contract tests，覆盖 REST 路径、topic 名、消息字段。
- [ ] 增加 worker once-file demo 输入，覆盖 triage metadata。
- [ ] 增加 Kafka 全链路 smoke test 脚本。
- [ ] 增加 mock LLM / real LLM 两种运行说明。
- [ ] 清理或忽略 `__pycache__`、`backend/target`、临时 outputs，避免仓库状态混乱。

## P3：后续研究预留

- [ ] 记录每次 workflow 的事件轨迹：服务事件、agent 决策、tool 调用、LLM 状态、耗时、失败原因。
- [ ] 为后续模型化测试保留统一 schema，例如 `executed_path`、`workflow_decisions`、`service_events`、`tool_events`。
- [ ] 设计 mock 外部系统：mock EHR、mock lab、mock insurance、mock LLM failure。
- [ ] 后续再讨论 PSUM / model-based testing 时，将测试生成目标绑定到真实服务链路和 agent 分支，而不是只围绕单个 prompt。

## 当前已完成

- [x] `backend/` 已改成多模块 Maven skeleton。
- [x] 原 `backend/src` 已迁移到 `backend/encounter-service`。
- [x] `triage-service` 已有 REST 分诊接口。
- [x] `triage-service` 已能消费 `healthcare.encounter.created` 并发布 `ai.symptom.query`。
- [x] `clinical-record-service` 已有 workflow result 保存和查询接口。
- [x] Python worker 已保留 triage metadata 到 workflow result。
- [x] Python workflow 已抽出 `HospitalWorkflowPlanner`。
- [x] `scripts/demo_healthcare_flow.py` 已提供完整任务创建、轮询和结果输出脚本。
- [x] Python 测试当前通过：`python -B -m pytest -q`。
