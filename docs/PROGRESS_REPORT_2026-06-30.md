# Progress Report - 2026-06-30

## 当前目标

当前阶段目标是把 healthcare 多 agent + 微服务 demo 稳定到可以手动演示的状态，重点包括：

- 急诊并发场景可以展示真实资源和人员竞争。
- ER workflow 使用真实 taskId 贯穿 agent tool 和微服务记录。
- 前端 surge 面板尽量避免因为 clinical-record-service 稍晚落库而显示 `unknown`。
- 保持前端组件化，不让 `App.vue` 重新膨胀。

## 本次已完成

### 1. 修复 ER 微服务记录 taskId 丢失

问题：

- 之前 `EmergencyPhysicianAgent` 从 `HospitalContext.metadata` 取 `taskId`。
- Python worker 调用 `HospitalOrchestrator.run()` 时没有传入 task metadata。
- 结果是 `practitioner-service` 和 `resource-service` 里的记录使用 fallback 值 `workflow-local`，不方便和前端 task 对齐，也影响后续按 taskId release/reset。

修复：

- `app/worker/kafka_worker.py` 现在会把真实 Kafka taskId 注入 workflow metadata：

```text
taskId
task_id
```

影响：

- 新跑的 Patient Encounter 会把真实 taskId 传给 ER tools。
- 新的 practitioner assignment / resource reservation 记录应能追踪到前端 taskId。
- 旧数据库里已经存在的 `workflow-local` 记录不会自动修正，需要重新跑新任务。

### 2. 修复 ER tool 过短 timeout 导致 fallback 误判

问题：

- ER 微服务 tool 默认 timeout 是 `0.5s`。
- 并发 surge 时，服务端可能已经成功落库，但 Python worker 没在 0.5s 内拿到响应，就把 tool result 标成 `fallback_ready` / `fallback_assigned`。
- 这会造成前端显示 fallback，但数据库实际已经成功分配。

修复：

- `app/tools/emergency_operations.py` 中 `DEFAULT_EMERGENCY_SERVICE_TIMEOUT_SECONDS` 从 `0.5` 提升到 `2.0`。

影响：

- 本地 ER 微服务有更多时间返回结果。
- 普通外部可选 tool，如 patient history / care coordination，仍保持短 timeout，不影响普通演示响应。

### 3. 修复 surge 卡片 `Resources unknown / Staff unknown`

问题：

- 前端在 task 进入 terminal 状态后只查询一次 clinical record。
- 如果 clinical-record-service 稍晚才写入完整 `handoff_timeline`，前端会提前提取不到 `resource_reservation` 和 `practitioner_assignment`，显示 `unknown`。

修复：

- 新增 `frontend/src/surgeRecordPolling.ts`。
- `App.vue` 在 surge task 完成后最多重试 10 次 clinical record 查询，直到 record 中出现：

```text
resource_reservation
practitioner_assignment
```

影响：

- surge 面板更稳定，减少临时 `unknown`。
- `App.vue` 维持在组件化阈值内，目前约 750 行。

### 4. 优化 surge 前端展示

当前 `Emergency Surge Scenario` 面板已经支持：

- 汇总 `Completed`
- 汇总 `Resource limited`
- 汇总 `Staff limited`
- 汇总 `Failed`
- 每个 patient card 分别展示 resource status 和 staff status

状态含义：

```text
Resources ready       所需 ER 资源全部预留成功
Resources partial     只拿到部分 ER 资源
Resources unavailable 关键 ER 资源不可用

Staff assigned        所需人员全部分配成功
Staff partial         只分配到部分人员
Staff unavailable     关键人员不可用
```

## 已验证

Python 测试：

```text
pytest -q
104 passed in 5.98s
```

前端构建：

```text
npm run build
vite build passed
```

新增/更新的测试覆盖：

- worker 会把真实 taskId 传入 workflow metadata。
- ER 微服务 tool 默认 timeout 为 2 秒。
- surge 前端轮询会等待 resource/staff tool payload 出现。
- `App.vue` 仍保持组件化入口文件大小约束。

## 当前已知问题

### `/api/ai/tasks` 500 Internal Server Error

用户在清空数据库并重启后报告：

```text
500 Internal Server Error for /api/ai/tasks
```

这个问题尚未完成诊断。它属于 `encounter-service` 的任务列表接口问题，不是前端 surge 展示逻辑本身。

优先怀疑方向：

1. `encounter-service` 启动时数据库 schema 与当前 entity 不一致。
2. 清空 Docker volume 后服务启动顺序导致 JPA 初始化或连接池异常。
3. `patient_encounters` 或相关表为空/结构异常时，`GET /api/ai/tasks` 查询路径没有正确处理。
4. 前一次后台服务进程没有停干净，8081 上运行的不是最新代码。

建议下一步诊断命令：

```powershell
cd "E:\study\university 5.2\healthcare"

Invoke-RestMethod http://localhost:8081/api/ai/health
Invoke-WebRequest http://localhost:8081/api/ai/tasks

Get-Content outputs\service-logs\encounter-service.err.log -Tail 200
Get-Content outputs\service-logs\encounter-service.log -Tail 200

docker exec healthcare-postgres psql -U user -d healthcare -c "\dt"
docker exec healthcare-postgres psql -U user -d healthcare -c "select count(*) from patient_encounters;"
```

如果服务是 IDEA 启动的，应优先看 IDEA 控制台里的 encounter-service stack trace。

## 当前建议启动顺序

```powershell
cd "E:\study\university 5.2\healthcare"
docker compose -f infra\docker-compose.kafka.yml up -d
```

然后启动 8 个 Spring Boot 服务：

```text
encounter-service              8081
triage-service                 8082
clinical-record-service        8083
care-coordination-service      8084
practitioner-service           8085
resource-service               8086
scheduling-service             8087
emergency-encounter-service    8088
```

如果本机 PowerShell 有 Maven：

```powershell
.\scripts\start-healthcare-services.ps1 -Verify
```

启动 worker：

```powershell
cd "E:\study\university 5.2\healthcare"
$env:PYTHONPATH="."
python -B -m app.worker.kafka_worker --bootstrap-servers 127.0.0.1:9092 --concurrency 4
```

启动前端：

```powershell
cd "E:\study\university 5.2\healthcare\frontend"
npm run dev -- --host 127.0.0.1 --port 5174
```

打开：

```text
http://127.0.0.1:5174
```

## 下一步建议

P0：

- 先诊断并修复 `/api/ai/tasks` 500。
- 确认清库重启后 `encounter-service` 能正常返回空任务列表，而不是 500。
- 重新跑一轮普通门诊、急诊、ER surge。

P1：

- 对 `practitioner-service` / `resource-service` 增加更明确的 reset/release 演示入口。
- 在前端 Graph inspector 中更清楚展示 tool payload：资源拿到了什么、缺了什么，人员分配了谁、缺了什么。
- 整理微服务 contract 表，说明每个服务拥有的状态、端口、API 和 Kafka topic。

P2：

- 清理或忽略 `backend/*/target`、`frontend/dist` 等编译产物，避免提交时混入生成文件。
- 修复旧 TODO 和部分文档中的中文乱码。
