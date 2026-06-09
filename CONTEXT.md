# Healthcare Multi-Agent Uncertainty Modeling

This context defines the domain language for a healthcare-themed sample system used to explore uncertainty modeling in multi-agent workflows. The healthcare scenario is a vehicle for studying workflow and testing complexity, not a production clinical diagnosis product.

## Language

**Multi-Agent Healthcare Uncertainty Modeling Sample System**:
A healthcare-themed sample system whose purpose is to model uncertainty introduced by a multi-agent clinical decision-support workflow and use that model to guide test-case construction.
_Avoid_: Healthcare system, automatic diagnosis system, diagnosis product

**Multi-Agent Clinical Decision-Support Workflow**:
A workflow where multiple agents contribute intermediate analysis such as symptom normalization, knowledge retrieval, differential-diagnosis candidates, evidence review, safety checks, and report synthesis for doctor review.
_Avoid_: Automatic diagnosis workflow, autonomous diagnosis

**Observable Serial Agent Workflow**:
A multi-agent workflow where agents run in a fixed order, each agent has a clear responsibility, and each intermediate result is visible as a workflow state for later uncertainty modeling and test-case construction.
_Avoid_: Dynamic agent swarm, free-form agent debate, autonomous expert panel

**Branching Agent Workflow**:
A multi-agent workflow where an upstream agent result determines which downstream agents run, which path is skipped, and which dependencies become required for the case.
_Avoid_: Single fixed pipeline, always-run agent chain

**Task-Oriented Tree Agent Workflow**:
A tree-shaped workflow where branches are organized around analysis tasks such as information quality, evidence quality, candidate support, safety risk, and consistency rather than around medical specialties.
_Avoid_: Specialty-based medical expert tree, fully autonomous agent swarm

**Branch Trigger**:
An explicit condition in an agent result that selects the next workflow path, such as insufficient information, urgent-risk detected, weak evidence, or conflicting agent outputs.
_Avoid_: Hidden control flow, implicit routing decision

**Dynamic Branch Activation**:
A workflow behavior where the branch planner marks each branch as active or skipped for a case based on explicit branch triggers rather than running every branch unconditionally.
_Avoid_: Always-run branch tree, hidden branch activation

**Urgent Risk Priority**:
A workflow rule where detected urgent risk requires an emergency-facing report section and priority handling, while non-emergency analysis may continue if its dependencies are available.
_Avoid_: Silent red flag, hard stop on urgent risk, routine-only report

**Clarification Path**:
A workflow path used when the case information is insufficient; it keeps safety-risk checking active, skips candidate reasoning, and produces clarification questions plus a safety note instead of a full analysis report.
_Avoid_: Forced diagnosis on incomplete input, full report despite missing basics

**Small Disease-Symptom Association Knowledge Base**:
A small local knowledge base that links diseases with associated symptoms and scores, suitable for retrieval-quality and candidate-support checks but not for guideline-level clinical reasoning.
_Avoid_: Medical guideline database, specialty database, clinical pathway database

**Evidence Sufficiency State**:
The evidence-quality state produced by retrieval-quality checks, using `evidence_sufficient`, `evidence_weak`, or `evidence_missing` to describe whether retrieved disease-symptom associations can support downstream candidate reasoning.
_Avoid_: Medical proof, clinical certainty

**Knowledge Gap Path**:
A workflow path used when retrieved evidence is weak or missing; it records the evidence limitation explicitly and constrains downstream candidate reasoning or report synthesis.
_Avoid_: Pretending evidence is sufficient, unsupported full analysis

**Weak Evidence Continuation**:
A workflow rule where weak retrieved evidence allows candidate reasoning to continue, but downstream agents must preserve the weak-evidence marker, lower confidence, and surface the limitation in the final report.
_Avoid_: Treating weak evidence as sufficient, hiding weak evidence, hard stop on weak evidence

**RAG-LLM Consistency State**:
The comparison state between retrieved disease-symptom evidence and LLM-generated candidate diagnoses, using `consistent`, `partially_consistent`, `conflicting`, or `not_comparable`.
_Avoid_: Silent merge, unexamined synthesis

**Conflict Resolution Path**:
A workflow path used when agent outputs conflict; it records the disagreement explicitly and prevents final report synthesis from hiding the conflict.
_Avoid_: Report-only conflict handling, silent conflict suppression

**Non-Decisive Conflict Handling**:
A conflict-handling rule where the system records conflicting agents, conflict type, follow-up needs, and report impact without claiming which side is clinically correct.
_Avoid_: LLM adjudication, unconditional RAG priority, hidden final arbitration

**Uncertainty Assessment Agent**:
The required convergence agent that collects uncertainty signals from active, skipped, blocked, and conflicting branches into a structured uncertainty summary for report generation and test-case coverage.
_Avoid_: Final diagnosis agent, hidden report-only uncertainty handling

**Uncertainty Type**:
A structured category emitted by the uncertainty assessment step; the first version uses `incomplete_input`, `urgent_risk`, `weak_evidence`, `missing_evidence`, `unsupported_candidate`, `agent_conflict`, and `branch_skipped`.
_Avoid_: Free-form uncertainty note, hidden limitation

**Real Agent Output**:
An output produced during real workflow execution by the configured LLM, RAG source, or rule-based agent.
_Avoid_: Test fixture output, generated mock case

**Controlled Agent Output**:
A fixed or fixture-backed agent output used during model-based test execution to trigger a specific branch or uncertainty state reproducibly.
_Avoid_: Live LLM call during automated tests, uncontrolled mock

**LLM-Assisted Mock Data**:
Mock cases or fixture outputs drafted with help from an LLM before test execution, then stored as controlled data so generated tests remain reproducible.
_Avoid_: Real-time LLM mocking during every test run, non-reproducible test oracle

**Mockable Uncertainty Source**:
A workflow data or service point that can be controlled during model-based testing to trigger a branch, state transition, or expected uncertainty; examples include case input, RAG output, LLM output, branch activation, agent status, and backend messaging state.
_Avoid_: LLM-only mock, uncontrolled runtime dependency

**Strong Agent Dependency**:
A workflow dependency where a downstream agent requires a specific upstream agent result to perform its own responsibility, while the system records the missing dependency explicitly instead of hiding it.
_Avoid_: Best-effort chaining, implicit dependency, silent fallback

**Workflow Design Phase**:
The current project phase, focused on shaping the multi-agent process before committing to a complete uncertainty taxonomy.
_Avoid_: Finished uncertainty model, finalized business model
