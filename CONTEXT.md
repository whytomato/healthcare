# Healthcare Multi-Agent Service Workflow

This context defines the domain language for a healthcare-themed sample system used to build and test a complete multi-agent service workflow. The healthcare domain is a demo vehicle for service workflow complexity, not a production clinical diagnosis product.

## Language

**Healthcare Multi-Agent Service Workflow Sample System**:
A healthcare-themed sample system whose purpose is to demonstrate a complete service workflow where role-oriented agents and backend services cooperate around a patient encounter.
_Avoid_: Automatic diagnosis system, diagnosis product, single prompt demo

**Agent Hospital-lite Workflow**:
A demo-grade end-to-end hospital service workflow that covers registration, intake, nurse vitals, appointment classification, triage, department routing, GP or emergency review, specialist consultation, AI consultation tool use, diagnostic orders, lab and imaging interpretation, pharmacy safety, medication planning, disposition, admission coordination, follow-up, and final reporting.
_Avoid_: Production hospital platform, isolated symptom query

**Patient Encounter**:
A single healthcare service episode that starts from a patient request or appointment and gathers triage, consultation, evidence, orders, reports, and follow-up decisions.
_Avoid_: Raw symptom query, isolated prompt

**Task Status**:
The user-facing progress state of a patient encounter workflow, used to tell whether the demo workflow is received, published, completed, failed, or waiting for more data.
_Avoid_: Clinical record, final report

**Workflow Record**:
A structured record of a completed or attempted patient encounter workflow, including the executed role path, workflow decisions, care pathway, consultation output, and final report.
_Avoid_: Task status, raw Kafka message, longitudinal patient medical history

**Longitudinal Patient Record**:
A patient-centered clinical history across multiple patient encounters, used to bring prior conditions, allergies, medications, previous dispositions, and earlier workflow summaries into a new encounter.
_Avoid_: Single workflow record, task status, raw workflow result archive

**Patient History Summary**:
A demo-grade, agent-facing summary of a longitudinal patient record, focused on recent encounters, known conditions, allergies, current medications, previous dispositions, and final-report excerpts that can support the next patient encounter.
_Avoid_: Full electronic health record, raw archive dump, frontend-only chart browser, replacement for current encounter safety signals

**Current Encounter Safety Signal**:
An acute signal from the current patient encounter, such as present red flags, current vitals, or current symptom severity, used to protect urgent routing decisions before longitudinal history is considered.
_Avoid_: Historical diagnosis, prior disposition, background risk factor alone

**History-Informed Agent Decision**:
A hospital role agent decision that can use the patient history summary as supporting context, such as registration status, pharmacy safety checks, care planning, follow-up planning, and final reporting.
_Avoid_: Letting historical context override current encounter safety signals or acute triage red flags

**Role-Scoped Agent Decision**:
A decision made by a hospital role agent within its own responsibility boundary, using the current patient encounter context, prior handoffs, available tools, and patient history when appropriate to decide what to do next, which tools to call or skip, and which downstream roles should receive a handoff.
_Avoid_: Unbounded autonomous planning, hidden global routing, precomputing every downstream step outside the agent role

**Role-Oriented Healthcare Multi-Agent Workflow**:
A healthcare workflow where agents represent service roles or departments such as registration, nurse vitals, triage nurse, department routing, emergency physician, general practitioner, specialist, diagnostic orders, lab interpretation, imaging interpretation, pharmacy safety, medication planning, admission coordination, disposition coordination, and follow-up coordination.
_Avoid_: Pipeline step masquerading as healthcare role, single question-answering agent

**Branched Hospital Workflow**:
A role-oriented healthcare workflow where triage and routing decisions determine which hospital role agents participate in a patient encounter.
_Avoid_: Fixed agent chain, always-run specialist pipeline

**Parallel Consultation Workflow**:
A workflow pattern where independent consultation roles for the same patient encounter can produce their handoffs concurrently after shared upstream context is available.
_Avoid_: Branched workflow, sequential consultation chain

**Agent Handoff Timeline**:
A chronological record of how hospital role agents complete work, make decisions, create handoffs, branch, run parallel consultations, and converge into downstream roles during a patient encounter.
_Avoid_: Raw agent result list, execution path only

**Agent Workflow Graph**:
A visual representation of a specific patient encounter's executed agent workflow, showing hospital role agents, agent handoffs, branch decisions, parallel fan-out and fan-in, and internal tool calls as connected nodes and edges.
_Avoid_: Static architecture diagram, fixed ideal workflow, raw timeline list

**Realtime Agent Progress**:
Intermediate progress events emitted while a patient encounter workflow is running, used to show agent start, completion, decisions, handoffs, parallel fan-out, and fan-in before the final workflow record is available.
_Avoid_: Final workflow record, task status, completed report

**Hospital Role Agent**:
An agent that represents a healthcare service role or department and produces a structured handoff for downstream roles in the patient encounter.
_Avoid_: Internal pipeline step, hidden helper function

**Emergency Physician Agent**:
A hospital role agent that participates when triage identifies high urgency and produces immediate safety actions for the patient encounter.
_Avoid_: General practitioner, specialist consultant, internal safety tool

**Disposition Coordinator Agent**:
A hospital role agent that decides the demo-level patient encounter disposition such as emergency reassessment or outpatient follow-up.
_Avoid_: Final report writer, follow-up note, discharge automation

**AI Consultation Tool**:
The internal tool that lets a hospital role agent perform symptom extraction, knowledge retrieval, and LLM consultation synthesis without treating those steps as top-level hospital agents.
_Avoid_: Hospital role agent, external microservice boundary

**Patient History Lookup Tool**:
An internal tool that lets a hospital role agent actively retrieve an agent-facing patient history summary during a patient encounter.
_Avoid_: Treating longitudinal history as a preloaded static prompt, treating history lookup as a top-level hospital role agent, frontend-only record browsing

**Hospital Service Boundary**:
A business capability boundary such as patient intake, appointment, encounter, consultation, lab advice, medication review, report, or follow-up. The first implementation may keep these boundaries in one backend process while preserving separable responsibilities.
_Avoid_: Assuming every boundary must be a separate deployed service in the first demo

**LLM-Capable Role Agent**:
A hospital role agent that can call the configured LLM for reasoning or synthesis and can fall back to deterministic demo output when using mock mode.
_Avoid_: Always-live LLM dependency, untestable agent
