# 不确定性 Scenario 数据

这里的 JSON 文件是可执行的 controlled scenario。它们用于固定 workflow 输入和部分 agent 输出，从而稳定触发某些不确定性分支。

Scenario replay 不调用真实 LLM。真实 LLM 可以辅助生成 mock 数据，但生成结果必须先保存成 JSON 文件，再作为测试输入。

## 核心文件

```text
healthcare_uncertainty_scenarios.json
```

手工维护的核心 scenario。它适合作为回归测试和讲解样例。

```text
llm_generated_cases.json
```

LLM-assisted mock 样例数据。这个文件需要保留，不要作为临时生成物删除。

注意：LLM 生成的数据不一定能稳定触发它声称的 expected uncertainty，后续需要增加 scenario 校验器。

```text
mock_llm_agent_conflict_response.json
```

给 `scripts/generate_mock_scenario.py` 使用的本地 mock response 文件，用来避免生成测试时真实调用 LLM。

## Scenario 字段

一条 scenario 的基本结构如下：

```json
{
  "name": "weak_evidence_unsupported_candidate_demo",
  "case_text": "patient has fever, cough, and mild shortness of breath",
  "mock_rag_documents": [
    {
      "disease": "pneumonia",
      "retrieval_score": 0.4,
      "matched_query_terms": ["fever"]
    }
  ],
  "mock_llm_output": "migraine should be considered",
  "expected_uncertainties": [
    "weak_evidence",
    "agent_conflict",
    "unsupported_candidate"
  ]
}
```

字段含义：

- `name`：scenario 名称，用于 CLI 的 `--scenario` 参数。
- `case_text`：输入病例文本。
- `mock_rag_documents`：固定的 RAG 检索结果。
- `mock_llm_output`：固定的候选诊断 agent 输出。
- `mock_evidence_review_output`：可选，固定 evidence review 输出。
- `expected_uncertainties`：期望最终暴露的不确定性类型。

## 运行单个 Scenario

```powershell
python -B scripts\run_uncertainty_scenario.py `
    --scenarios tests\scenarios\healthcare_uncertainty_scenarios.json `
    --scenario weak_evidence_unsupported_candidate_demo `
    --output outputs\weak_evidence_unsupported_candidate_demo.json
```

## 批量运行 Scenario

```powershell
python -B scripts\run_uncertainty_scenario.py `
    --scenarios tests\scenarios\healthcare_uncertainty_scenarios.json `
    --all `
    --summary-output outputs\manual_scenario_summary.json
```

## 生成物说明

这些文件是测试或实验生成物，默认不提交：

```text
*.test.json
generated*.json
```

`llm_generated_cases.json` 是例外，它当前作为 LLM-assisted mock 样例保留。
