# Healthcare Multi-Agent 项目

本项目是一个 healthcare 场景的临床决策辅助原型，核心目标是让医生输入症状或病例描述后，系统通过后端、Kafka、Python AI Worker、RAG 和多 agent 流程生成辅助分析报告。

系统不会给出最终诊断，输出只作为医生参考。

## 当前架构

```text
医生/前端/Apifox
  -> Kotlin Spring Boot 后端
    -> 创建 AI 任务
    -> 发布 Kafka 消息
  -> Kafka
    -> ai.symptom.query
  -> Python AI Worker
    -> Orchestrator
    -> AgentCoordinator
      -> SymptomExtractionAgent
      -> MedicalKnowledgeAgent
        -> RagMcpClient
        -> 本地医学知识库
      -> DifferentialDiagnosisAgent
        -> DeepSeek / OpenAI-compatible LLM
      -> EvidenceReviewAgent
        -> DeepSeek / OpenAI-compatible LLM
      -> SafetyCheckAgent
      -> ReportAgent
        -> DeepSeek / OpenAI-compatible LLM
  -> Kafka
    -> ai.symptom.result
  -> Kotlin Spring Boot 后端
    -> 更新任务结果
```

一次完整 AI 分析默认使用 3 次大模型 API：

```text
1. differential_diagnosis_agent：生成候选鉴别诊断
2. evidence_review_agent：结合 RAG 证据评估候选疾病
3. report_agent：生成最终医生报告
```

## 目录说明

```text
app/                 Python AI 服务、agent、FastAPI、Kafka worker
backend/             Kotlin Spring Boot 后端
mcp_servers/         MCP 风格的知识检索服务
data/                本地医学知识库
docs/                中文说明文档
infra/               Kafka Docker Compose
scripts/             数据准备脚本
tests/               最小主流程测试
examples/            worker 本地测试输入
outputs/             本地运行输出，已忽略提交
```

## 环境配置

复制配置文件：

```powershell
Copy-Item .env.example .env
```

编辑项目根目录下的 `.env`：

```text
LLM_API_KEY=你的 DeepSeek 或 OpenAI-compatible API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=60
MEDICAL_KNOWLEDGE_BASE=E:\study\university 5.2\healthcare\data\health_knowledge_graph.json
```

`.env` 不会提交到 Git。

## 准备医学知识库

当前使用一个小规模公开数据集作为初始 RAG 知识库：

```text
https://github.com/clinicalml/HealthKnowledgeGraph
```

生成本地 JSON：

```powershell
conda activate healthcare
python scripts\prepare_health_knowledge_graph.py
```

输出文件：

```text
data/health_knowledge_graph.json
```

## 单独测试 Python AI 流程

```powershell
cd "E:\study\university 5.2\healthcare"
conda activate healthcare
python -B -m app.main --case-text "fever, cough, chest discomfort" --question "What diseases should be considered?" --output outputs\ai_test.json
```

控制台只显示每个 agent 的状态，完整 JSON 会写入 `outputs\ai_test.json`。

## 启动 FastAPI 调试入口

FastAPI 主要用于单独调试 Python AI 服务，不是正式后端。

```powershell
cd "E:\study\university 5.2\healthcare"
conda activate healthcare
uvicorn app.main:api --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

## 启动 Kafka

```powershell
cd "E:\study\university 5.2\healthcare"
docker compose -f infra\docker-compose.kafka.yml up -d
```

检查端口：

```powershell
Test-NetConnection 127.0.0.1 -Port 9092
```

## 启动 Python AI Worker

```powershell
cd "E:\study\university 5.2\healthcare"
conda activate healthcare
python -B -m app.worker.kafka_worker --bootstrap-servers 127.0.0.1:9092
```

成功后应看到：

```text
listening on Kafka topic ai.symptom.query, producing to ai.symptom.result
```

## 启动 Kotlin Spring Boot 后端

需要 JDK 17 和 Maven。

```powershell
cd "E:\study\university 5.2\healthcare\backend"
mvn spring-boot:run
```

后端配置文件：

```text
backend/src/main/resources/application.yml
```

当前 Kafka 已启用：

```yaml
healthcare:
  kafka:
    enabled: true
```

## 后端接口测试

创建症状查询任务：

```powershell
curl -X POST http://localhost:8080/api/ai/symptom-query `
  -H "Content-Type: application/json" `
  -d "{\"caseText\":\"A 67-year-old male has fever, productive cough, shortness of breath and confusion.\",\"question\":\"请分析需要考虑哪些疾病或情况，哪些红旗征需要优先处理。\",\"doctorId\":\"d001\",\"patientId\":\"p001\",\"language\":\"zh-CN\"}"
```

查询任务结果：

```powershell
curl http://localhost:8080/api/ai/tasks/{taskId}
```

完整状态流：

```text
RECEIVED -> PUBLISHED -> COMPLETED
```

如果缺少 API Key 或知识库，则可能返回：

```text
NEEDS_DATA
```

## 不经过 Kafka 的 Worker 测试

```powershell
cd "E:\study\university 5.2\healthcare"
conda activate healthcare
python -B -m app.worker.kafka_worker --once-file examples\symptom_task.json --output outputs\worker_once_result.json
```

## 自动化测试

当前只保留最小主流程测试，用来确认 agent 编排和缺配置时的状态不会被改坏。

```powershell
cd "E:\study\university 5.2\healthcare"
conda activate healthcare
python -B -m pytest
```

## 重要说明

- 本项目是临床决策辅助原型，不是自动诊断系统。
- RAG 当前使用英文小数据集，英文症状输入的检索效果更好。
- 输出中文报告是由提示词控制的，不代表系统有独立翻译模块。
- 后续可以继续补充任务去重、RUNNING 状态回写、任务摘要接口和更完整的医学知识库。
