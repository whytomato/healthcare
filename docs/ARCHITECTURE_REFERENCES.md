# 架构参考说明

本项目采用的是 retrieval-augmented multi-agent clinical decision-support 架构，可以翻译为：

```text
基于检索增强生成的多智能体临床决策辅助架构
```

核心思想有三点：

```text
1. Multi-Agent：将复杂医疗分析拆成多个职责明确的 agent
2. RAG：用外部医学知识库约束大模型输出
3. MCP 风格工具边界：让 agent 通过统一 client/server 接口访问知识库
```

## 当前代码中的对应关系

```text
医生症状查询
  -> SymptomExtractionAgent
    -> 症状结构化
  -> MedicalKnowledgeAgent
    -> RAG 检索医学知识
  -> DifferentialDiagnosisAgent
    -> 生成候选鉴别诊断
  -> EvidenceReviewAgent
    -> 基于检索证据评估候选疾病
  -> SafetyCheckAgent
    -> 检查红旗征
  -> ReportAgent
    -> 生成最终医生报告
```

## 可引用的论文方向

### Almanac

论文方向：临床医学 RAG。

可以用于说明为什么医疗 LLM 不应该只依赖模型内部知识，而应该接入医学指南、治疗建议和外部知识。

链接：

```text
https://arxiv.org/abs/2303.01229
```

### MDAgents

论文方向：医疗任务中的多 agent 协作。

可以用于说明为什么将医疗推理拆成多个 agent，而不是一次性让一个 LLM 完成所有工作。

链接：

```text
https://arxiv.org/abs/2404.15155
```

### MedAgents

论文方向：多个 LLM agent 作为医学推理协作者。

可以用于说明 multi-agent 在医学推理中的角色分工和协作价值。

链接：

```text
https://arxiv.org/abs/2311.10537
```

### KG4Diagnosis

论文方向：知识图谱增强的层次化多 agent 诊断辅助框架。

可以用于说明后续为什么可以把当前 RAG 知识库扩展为医学知识图谱。

链接：

```text
https://arxiv.org/abs/2412.16833
```

## 和本项目的关系

当前项目不是直接复现某一篇论文，而是采用这些工作中比较稳定的架构思想：

```text
症状理解
  -> 对应 SymptomExtractionAgent

知识检索
  -> 对应 MedicalKnowledgeAgent + RagMcpClient

多阶段 LLM 推理
  -> 对应 DifferentialDiagnosisAgent + EvidenceReviewAgent + ReportAgent

安全检查
  -> 对应 SafetyCheckAgent

系统调度
  -> 对应 AgentCoordinator + Orchestrator
```

## MCP 在本项目中的作用

MCP 不是医学推理本身，而是工具和数据源边界。

当前使用方式：

```text
MedicalKnowledgeAgent
  -> RagMcpClient
    -> 本地医学知识库
```

后续可以扩展为：

```text
Agent
  -> MCP Client
    -> Spring Boot 服务
    -> 数据库
    -> 医学指南库
    -> 医院内部系统
```

这样 agent 不需要直接关心数据库、HTTP 接口或微服务实现，只需要通过稳定工具接口拿数据。
