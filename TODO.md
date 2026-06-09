# TODO

这个文件只记录当前已经明确的待办和可能的下一步。后续研究方向还没有完全确定，暂时不把路线写死。

## 已知待整理

- [ ] 确认 `llm_generated_cases.json` 中哪些 scenario 能稳定触发预期不确定性。
- [ ] 补充 README 中可能遗漏的实际运行命令。
- [ ] 根据后续和学长/老师讨论的结果，再决定是否增加新的 agent、branch 或 uncertainty type。
- [ ] 重新评估 `EvidenceReviewAgent` 的定位：它现在主要服务于最终报告，不是核心不确定性判定 agent。
- [ ] 确认 workflow 图中每个 agent 是否都有清晰的下游消费者，避免出现“断头节点”。
- [ ] 讨论是否让 `EvidenceReviewAgent` 输出结构化字段，例如 `supported_claims`、`unsupported_claims`、`missing_evidence`、`follow_up_questions`，使其更直接参与不确定性建模。
- [ ] 决定是否继续保留 `docs/中文架构参考报告.md`。它是早期参考报告，部分 agent 列表已经和当前 workflow 不完全一致。
- [ ] 决定 `ScenarioReportAgent` 是否需要进一步模拟真实 `ReportAgent` 的报告结构。目前它会收集上游结果，但仍然不会调用真实 LLM 生成自然语言报告。
- [ ] 决定动态分支触发逻辑是否要更多回收到 `BranchPlannerAgent`。当前 `evidence_missing` 导致跳过下游分支的逻辑主要在 `AgentCoordinator` 中。

## 可能的下一步

- [ ] 如果需要批量评估 mock 数据质量，再添加 scenario 校验脚本。
- [ ] 如果开始做 PSUM/model-based testing，再整理 workflow 状态和 branch trigger 的模型格式。
- [ ] 如果要扩展业务复杂性，再新增更复杂的分支或 agent 调用链。

## 可能扩展的不确定性类型

以下只是候选方向，不代表已经决定实现。

### Agent / LLM 相关

- [ ] `llm_low_confidence`：LLM 输出中明确表达不确定，例如“可能”“无法判断”“需要更多信息”。
- [ ] `llm_format_error`：LLM 输出格式不符合预期，缺字段或无法解析。
- [ ] `llm_overreach`：LLM 给出超出证据范围的强结论。
- [ ] `inconsistent_report`：最终报告没有忠实反映前面 agent 暴露的不确定性。

### Evidence / RAG 相关

- [ ] `retrieval_noise`：检索结果相关性混杂，噪声较多。
- [ ] `over_retrieval`：检索结果过多，导致下游难以聚焦。
- [ ] `evidence_conflict`：RAG 检索到的不同证据之间互相冲突。
- [ ] `stale_evidence`：检索证据过时，不适合当前病例或当前知识状态。

### Workflow / Dependency 相关

- [ ] `dependency_blocked`：强依赖 agent 没有 ready，导致下游无法运行。当前部分体现在 `branch_skipped` 中。
- [ ] `inconsistent_branch_state`：branch plan 和实际 agent 执行状态不一致。
- [ ] `missing_handoff`：上游 agent 没有明确把结果交给需要的下游 agent。

### Service / Backend 相关

- [ ] `timeout_or_service_failure`：LLM、RAG、Kafka 或后端服务超时/失败。
- [ ] `duplicate_task`：后端或 Kafka 层重复提交、重复消费任务。
- [ ] `stale_task_status`：worker 已完成但后端状态没有及时更新。

如果后续想优先增强 healthcare / multi-agent 特色，可以优先讨论：

```text
evidence_conflict
llm_overreach
llm_format_error
inconsistent_report
```
