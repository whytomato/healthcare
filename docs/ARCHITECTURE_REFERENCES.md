# Architecture References

本项目不是复现某一篇医学论文，而是借用 healthcare 场景构造一个 multi-agent workflow，用于研究不确定性建模和模型驱动测试。

## Architecture Positioning

当前架构可以描述为：

```text
retrieval-augmented multi-agent clinical decision-support workflow
```

中文可表述为：

```text
基于检索增强的多智能体临床决策辅助工作流
```

注意这里的重点是 workflow uncertainty modeling，不是自动诊断产品。

## Related Directions

### Clinical RAG

代表方向：将外部医学知识、指南或知识库接入 LLM，减少只依赖模型内部知识的问题。

可用于解释本项目中的：

```text
MedicalKnowledgeAgent
RagMcpClient
Small Disease-Symptom Association Knowledge Base
RetrievalQualityAgent
```

### Medical Multi-Agent Reasoning

代表方向：把医学推理拆成多个角色或阶段，例如症状理解、候选诊断、证据审查、安全检查和报告生成。

可用于解释本项目中的：

```text
SymptomExtractionAgent
DifferentialDiagnosisAgent
EvidenceReviewAgent
SafetyCheckAgent
ReportAgent
```

### Model-Based Testing for Uncertain Workflows

代表方向：把系统中可能变化、失败、冲突或被跳过的路径建模，然后根据模型生成测试用例。

可用于解释本项目中的：

```text
BranchPlannerAgent
UncertaintyAssessmentAgent
controlled scenario JSON
expected_uncertainties
scenario replay runner
```

## Useful Paper Search Terms

后续查论文时可以从这些关键词开始：

```text
medical multi-agent LLM
clinical decision support LLM agents
retrieval augmented generation healthcare
model based testing uncertainty
workflow uncertainty modeling
LLM agent evaluation testing
```

## Mapping to Current Code

```text
Symptom understanding
  -> SymptomExtractionAgent

Knowledge retrieval
  -> MedicalKnowledgeAgent
  -> RagMcpClient
  -> data/health_knowledge_graph.json

Evidence sufficiency
  -> RetrievalQualityAgent

Candidate reasoning
  -> DifferentialDiagnosisAgent

Candidate support and consistency
  -> CandidateSupportAgent
  -> RagLlmConsistencyAgent

Safety risk
  -> SafetyCheckAgent

Uncertainty convergence
  -> UncertaintyAssessmentAgent

Report synthesis
  -> ReportAgent

Controlled model-based test execution
  -> app/uncertainty_scenario_runner.py
  -> tests/scenarios/*.json
```
