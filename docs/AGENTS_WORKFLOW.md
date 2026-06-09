# Agent 职责与不确定性映射

本文档记录当前 multi-agent workflow 中每个 agent 的职责、下游作用，以及它可能引出的显式不确定性。

## Agent 列表

| Agent | 作用 | 可能引出的不确定性 |
|---|---|---|
| `SymptomExtractionAgent` | 从病例文本中提取和规范化症状候选词。 | `incomplete_input`：输入为空或信息不足。 |
| `BranchPlannerAgent` | 根据输入状态规划哪些 workflow 分支运行、哪些分支跳过。 | `branch_skipped`：某些分支被主动跳过，例如输入不足时跳过候选推理。 |
| `MedicalKnowledgeAgent` | 调用本地 RAG / knowledge base，检索疾病-症状证据。 | `missing_evidence`：知识库没配置，或没有检索到可用结果。 |
| `RetrievalQualityAgent` | 判断 RAG 检索结果质量，将证据分为 `evidence_sufficient`、`evidence_weak`、`evidence_missing`。 | `missing_evidence`、`weak_evidence`。 |
| `DifferentialDiagnosisAgent` | 调用 LLM，根据病例和 RAG 证据生成候选诊断/候选疾病。 | 本身不直接输出 uncertainty type，但它的输出可能成为 `unsupported_candidate` 或 `agent_conflict` 的来源。 |
| `CandidateSupportAgent` | 检查 LLM 给出的候选是否被 RAG 检索证据支持。 | `unsupported_candidate`：LLM 提到的候选没有被 RAG 证据支持。 |
| `EvidenceReviewAgent` | 调用 LLM，对候选诊断和 RAG 证据做语义审查，主要服务最终报告。 | 目前不是核心不确定性判定 agent；如果它无法运行，可能导致一致性/报告相关分支 blocked。 |
| `RagLlmConsistencyAgent` | 比较 RAG 证据和 LLM 候选输出是否一致。 | `agent_conflict`：RAG 证据和 LLM 候选结果冲突。 |
| `SafetyCheckAgent` | 用本地规则检查红旗症状/紧急风险。 | `urgent_risk`：检测到需要优先处理的风险信号。 |
| `UncertaintyAssessmentAgent` | 汇总所有 agent 和 branch 状态，生成最终显式不确定性列表。 | 不制造新的业务不确定性，负责收集和输出 uncertainty oracle。 |
| `ReportAgent` | 生成最终医生可读报告。真实流程中会调用 LLM。 | 如果上游 blocking 或 LLM 未配置，会 `needs_data`；它携带 uncertainties，但不是主要判定者。 |

## 当前主线理解

```text
输入是否足够
-> 症状提取
-> 分支规划
-> RAG 证据检索
-> 证据质量判断
-> LLM 候选诊断
-> 候选是否被证据支持
-> RAG 和 LLM 是否冲突
-> 安全风险检查
-> 不确定性汇总
-> 最终报告
```

## 核心不确定性来源

```text
SymptomExtractionAgent     -> incomplete_input
BranchPlannerAgent        -> branch_skipped
MedicalKnowledgeAgent      -> missing_evidence
RetrievalQualityAgent      -> missing_evidence / weak_evidence
CandidateSupportAgent      -> unsupported_candidate
RagLlmConsistencyAgent     -> agent_conflict
SafetyCheckAgent           -> urgent_risk
UncertaintyAssessmentAgent -> 汇总所有不确定性
```

## 每种不确定性如何触发

当前第一版显式建模 7 种不确定性。它们覆盖输入、证据、分支执行、agent 协作冲突、候选支持和安全风险，作为 workflow design phase 的第一版是足够的。

后续可以继续扩展更多 uncertainty type，但不建议一次性全部加入。更合理的方式是：先让第一版 workflow、scenario replay、测试结果解释跑稳定，再根据论文/PSUM 建模需要逐步增加。

### `incomplete_input`

触发条件：

```text
case_text 为空，或症状提取阶段认为缺少必要输入。
```

典型 mock 输入：

```json
{
  "case_text": ""
}
```

结果表现：

- `SymptomExtractionAgent` 返回 `needs_data`。
- `BranchPlannerAgent` 进入 `clarification_path`。
- 候选推理、证据审查、一致性检查等分支被跳过。
- `UncertaintyAssessmentAgent` 输出 `incomplete_input`，通常还会伴随 `branch_skipped`。

### `branch_skipped`

触发条件：

```text
BranchPlannerAgent 将某些分支标记为 skipped，或运行过程中因为上游依赖缺失导致下游分支不能执行。
```

典型 mock 输入：

```json
{
  "case_text": ""
}
```

或者：

```json
{
  "case_text": "zzzzunknownsymptom",
  "mock_rag_documents": [],
  "mock_llm_output": null
}
```

结果表现：

- `BranchPlannerAgent.data.branches[*].state` 中出现 `skipped`。
- 或某些 agent 的 `status` 为 `skipped`，并带有 `data.skipped_branch`。
- `UncertaintyAssessmentAgent` 输出 `branch_skipped`。

### `missing_evidence`

触发条件：

```text
RAG 知识库不可用，或 RAG 检索结果为空。
```

典型 mock 输入：

```json
{
  "name": "missing_evidence_demo",
  "case_text": "zzzzunknownsymptom",
  "mock_rag_documents": [],
  "mock_llm_output": null,
  "expected_uncertainties": ["missing_evidence", "branch_skipped"]
}
```

结果表现：

- `MedicalKnowledgeAgent` 或 `ScenarioMedicalKnowledgeAgent` 没有提供可用文档。
- `RetrievalQualityAgent.data.evidence_state` 为 `evidence_missing`。
- candidate reasoning 和 consistency 分支可能被跳过。
- `UncertaintyAssessmentAgent` 输出 `missing_evidence`。

现有例子：

```text
tests/scenarios/healthcare_uncertainty_scenarios.json
-> missing_evidence_skips_candidate_reasoning
```

### `weak_evidence`

触发条件：

```text
RAG 有检索结果，但最高 retrieval_score 低于当前阈值 1.0。
```

典型 mock 输入：

```json
{
  "mock_rag_documents": [
    {
      "disease": "pneumonia",
      "retrieval_score": 0.4,
      "matched_query_terms": ["fever"]
    }
  ]
}
```

结果表现：

- `RetrievalQualityAgent.data.evidence_state` 为 `evidence_weak`。
- workflow 不会直接停止，候选推理仍可继续。
- `UncertaintyAssessmentAgent` 输出 `weak_evidence`。

现有例子：

```text
tests/scenarios/healthcare_uncertainty_scenarios.json
-> weak_evidence_unsupported_candidate_demo
```

### `unsupported_candidate`

触发条件：

```text
LLM 候选输出中提到的疾病，没有出现在 RAG 检索证据的 disease 字段中。
```

典型 mock 输入：

```json
{
  "mock_rag_documents": [
    {
      "disease": "pneumonia",
      "retrieval_score": 0.4,
      "matched_query_terms": ["fever"]
    }
  ],
  "mock_llm_output": "migraine should be considered"
}
```

结果表现：

- `CandidateSupportAgent.data.rag_diseases` 包含 `pneumonia`。
- `CandidateSupportAgent.data.matched_diseases` 为空。
- `CandidateSupportAgent.data.candidate_support_state` 为 `unsupported`。
- `UncertaintyAssessmentAgent` 输出 `unsupported_candidate`。

现有例子：

```text
tests/scenarios/healthcare_uncertainty_scenarios.json
-> weak_evidence_unsupported_candidate_demo
-> rag_llm_conflict
```

### `agent_conflict`

触发条件：

```text
RAG 检索证据中的 disease 和 LLM 候选输出完全匹配不上。
```

典型 mock 输入：

```json
{
  "mock_rag_documents": [
    {
      "disease": "pneumonia",
      "retrieval_score": 2.0,
      "matched_query_terms": ["fever", "cough"]
    }
  ],
  "mock_llm_output": "heart failure should be considered"
}
```

结果表现：

- `RagLlmConsistencyAgent.data.rag_diseases` 包含 `pneumonia`。
- `RagLlmConsistencyAgent.data.matched_diseases` 为空。
- `RagLlmConsistencyAgent.data.consistency_state` 为 `conflicting`。
- `UncertaintyAssessmentAgent` 输出 `agent_conflict`。

现有例子：

```text
tests/scenarios/healthcare_uncertainty_scenarios.json
-> rag_llm_conflict
```

### `urgent_risk`

触发条件：

```text
case_text 或症状候选词中包含 SafetyCheckAgent 的红旗风险词。
```

当前已有英文红旗词示例：

```text
severe headache
neck stiffness
```

典型输入：

```json
{
  "case_text": "fever with severe headache and neck stiffness"
}
```

结果表现：

- `SafetyCheckAgent.data.red_flags` 非空。
- `UncertaintyAssessmentAgent` 输出 `urgent_risk`。

当前说明：

```text
urgent_risk 已在 workflow 测试中覆盖，但还没有独立的 scenario JSON 样例。
```

## 运行现有 Scenario 查看触发结果

运行单个 scenario：

```powershell
python -B scripts\run_uncertainty_scenario.py `
    --scenarios tests\scenarios\healthcare_uncertainty_scenarios.json `
    --scenario weak_evidence_unsupported_candidate_demo `
    --output outputs\weak_evidence_unsupported_candidate_demo.json
```

批量查看覆盖了哪些不确定性：

```powershell
python -B scripts\run_uncertainty_scenario.py `
    --scenarios tests\scenarios\healthcare_uncertainty_scenarios.json `
    --all `
    --summary-output outputs\manual_scenario_summary.json
```

## 待讨论点

`EvidenceReviewAgent` 目前更像是报告增强 agent，而不是核心不确定性判定 agent。后续可以考虑让它输出结构化结果，例如：

```json
{
  "supported_claims": [],
  "unsupported_claims": [],
  "missing_evidence": [],
  "follow_up_questions": []
}
```

这样它可以更直接参与不确定性建模，而不是只作为最终报告的输入。
