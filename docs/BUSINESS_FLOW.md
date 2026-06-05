# 业务流程说明

当前系统由三层组成：

```text
Kotlin Spring Boot 后端
  -> 接收医生症状查询
  -> 创建任务
  -> 发布 Kafka 消息
  -> 接收 AI 结果并更新任务

Kafka
  -> ai.symptom.query
  -> ai.symptom.result

Python AI Worker
  -> 消费症状查询任务
  -> 执行 multi-agent 工作流
  -> 返回任务结果
```

## 任务状态

```text
RECEIVED
  后端已经接收请求，并创建任务。

PUBLISHED
  后端已经把任务发布到 Kafka。

COMPLETED
  Python AI Worker 完成分析，并返回 ready 结果。

NEEDS_DATA
  Python AI Worker 完成流程，但缺少必要配置或数据，例如 API Key 或医学知识库。

FAILED
  后端或 AI Worker 执行失败。
```

## Kafka Topic

```text
ai.symptom.query
  Spring Boot -> Python AI Worker

ai.symptom.result
  Python AI Worker -> Spring Boot
```

## 请求消息

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

## 结果消息

```json
{
  "taskId": "task-001",
  "status": "ready",
  "result": {},
  "errorMessage": null
}
```

## 当前 Multi-Agent 业务流程

```text
SymptomExtractionAgent
  -> 本地规则提取症状候选词

MedicalKnowledgeAgent
  -> 调用 RagMcpClient
  -> 从本地医学知识库检索相关疾病和症状

DifferentialDiagnosisAgent
  -> 第 1 次 LLM 调用
  -> 生成候选鉴别诊断

EvidenceReviewAgent
  -> 第 2 次 LLM 调用
  -> 结合 RAG 证据评估候选疾病

SafetyCheckAgent
  -> 本地规则检查红旗征

ReportAgent
  -> 第 3 次 LLM 调用
  -> 汇总最终医生报告
```

## 后续可建模的不确定性

这些点适合后续基于 PSUM 或其他模型生成测试用例：

```text
RAG 不确定性
  -> 无检索结果
  -> 检索结果弱相关
  -> 检索结果过多

LLM 不确定性
  -> API 超时
  -> API 失败
  -> 输出过长
  -> 输出缺少关键字段

Agent 协作不确定性
  -> 上游 agent needs_data
  -> 下游 agent 是否继续执行
  -> SafetyCheckAgent 与 LLM 结论冲突

微服务不确定性
  -> Kafka 延迟
  -> Kafka 堵塞
  -> 重复提交
  -> 后端任务状态未及时更新
```

## 推荐下一步业务增强

```text
1. 后端任务去重
2. Python Worker 先回写 RUNNING 状态
3. 增加任务摘要接口
4. 增加更大的医学知识库
5. 增加 agent 执行耗时和失败原因记录
```
