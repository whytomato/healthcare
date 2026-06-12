# Healthcare Multi-Agent Service Workflow

This context defines the domain language for a healthcare-themed sample system used to build and test a complete multi-agent service workflow. The healthcare domain is a demo vehicle for service workflow complexity, not a production clinical diagnosis product.

## Language

**Healthcare Multi-Agent Service Workflow Sample System**:
A healthcare-themed sample system whose purpose is to demonstrate a complete service workflow where role-oriented agents and backend services cooperate around a patient encounter.
_Avoid_: Automatic diagnosis system, diagnosis product, single prompt demo

**Agent Hospital-lite Workflow**:
A demo-grade end-to-end hospital service workflow that covers intake, appointment classification, triage, GP review, specialist consultation, AI consultation tool use, lab advice, pharmacy safety, care planning, follow-up, and final reporting.
_Avoid_: Production hospital platform, isolated symptom query

**Patient Encounter**:
A single healthcare service episode that starts from a patient request or appointment and gathers triage, consultation, evidence, orders, reports, and follow-up decisions.
_Avoid_: Raw symptom query, isolated prompt

**Role-Oriented Healthcare Multi-Agent Workflow**:
A healthcare workflow where agents represent service roles or departments such as triage nurse, general practitioner, specialist, lab, pharmacy safety, care plan, and follow-up coordination.
_Avoid_: Pipeline step masquerading as healthcare role, single question-answering agent

**Hospital Role Agent**:
An agent that represents a healthcare service role or department and produces a structured handoff for downstream roles in the patient encounter.
_Avoid_: Internal pipeline step, hidden helper function

**AI Consultation Tool**:
The internal tool that lets a hospital role agent perform symptom extraction, knowledge retrieval, and LLM consultation synthesis without treating those steps as top-level hospital agents.
_Avoid_: Hospital role agent, external microservice boundary

**Hospital Service Boundary**:
A business capability boundary such as patient intake, appointment, encounter, consultation, lab advice, medication review, report, or follow-up. The first implementation may keep these boundaries in one backend process while preserving separable responsibilities.
_Avoid_: Assuming every boundary must be a separate deployed service in the first demo

**LLM-Capable Role Agent**:
A hospital role agent that can call the configured LLM for reasoning or synthesis and can fall back to deterministic demo output when using mock mode.
_Avoid_: Always-live LLM dependency, untestable agent
