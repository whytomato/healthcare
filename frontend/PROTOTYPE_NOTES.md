# Prototype Notes

Question: Should the workflow display feel realtime, and should the final report render as a clinical document instead of raw text?

Verdict:
- The frontend should poll the current task and show a live hospital-stage progress view while the backend task is running.
- When the backend returns the real `handoff_timeline`, the UI should replace the stage placeholder with the true agent event timeline.
- The final report should render Markdown-like headings, lists, bold text, and separators, because the LLM report is authored as a clinical Markdown document.

Remaining backend gap:
- The current services publish the full workflow result only after the Python worker finishes. True per-agent realtime display needs an intermediate progress event stream, such as `ai.workflow.progress`, Server-Sent Events, or WebSocket updates.
