# Rule-Driven Branch Planner

The first tree-shaped agent workflow will use a rule-driven `BranchPlannerAgent` instead of letting an LLM freely choose the next agent chain. This keeps branch activation explainable and mockable, which matters because the project goal is to model uncertainty explicitly and construct test cases around branch triggers such as incomplete input, weak retrieval evidence, urgent risk, and cross-agent conflict.
