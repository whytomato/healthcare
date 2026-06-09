# 文档入口

仓库地址：<https://github.com/whytomato/healthcare>

建议阅读顺序：

1. [README.md](../README.md)
   - 项目目标、完整 demo 链路、agent workflow、scenario replay 和常用命令。

2. [AGENTS_WORKFLOW.md](./AGENTS_WORKFLOW.md)
   - 每个 agent 的职责、下游作用、可能引出的不确定性，以及每种不确定性的触发方式。

3. [BUSINESS_FLOW.md](./BUSINESS_FLOW.md)
   - Spring Boot、Kafka、Python Worker 之间的业务链路。

4. [ARCHITECTURE_REFERENCES.md](./ARCHITECTURE_REFERENCES.md)
   - 当前架构定位和可参考的研究方向。

5. [adr/0001-rule-driven-branch-planner.md](./adr/0001-rule-driven-branch-planner.md)
   - 为什么第一版使用 rule-driven `BranchPlannerAgent`。

6. [../TODO.md](../TODO.md)
   - 当前不确定事项和后续可能扩展方向。

补充说明：

- [中文架构参考报告.md](./中文架构参考报告.md) 是早期参考报告，部分 agent 列表和当前代码已经不完全一致。当前实现以 README 和 AGENTS_WORKFLOW 为准。
