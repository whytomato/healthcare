type MarkdownRenderer = {
  render(value: string): string;
};

const labels = {
  summary: "\u62a5\u544a\u6458\u8981",
  findings: "\u4e34\u5e8a\u53d1\u73b0",
  recommendations: "\u5efa\u8bae\u4e0e\u5b89\u6392",
  handoffReason: "\u4ea4\u63a5\u539f\u56e0",
  confidence: "\u7f6e\u4fe1\u5ea6"
};

export function renderReportMarkdown(
  markdown: MarkdownRenderer,
  value?: string,
  emptyText = "No report excerpt available."
) {
  return markdown.render(normalizeReportMarkdownText(value, emptyText));
}

export function normalizeReportMarkdownText(value?: string, emptyText = "No report excerpt available.") {
  const text = value?.trim() || "";
  if (!text) {
    return emptyText;
  }

  const textWithStructuredFences = text.replace(
    /```(?:json)?\s*\r?\n([\s\S]*?)\r?\n```/gi,
    (match, body: string) => structuredJsonReportText(body) || match
  );
  const jsonText = unwrapJsonCodeFence(textWithStructuredFences);
  if (!looksLikeJsonReport(jsonText)) {
    return textWithStructuredFences;
  }
  return structuredJsonReportText(jsonText) || textWithStructuredFences;
}

export function unwrapJsonCodeFence(value: string) {
  const trimmed = value.trim();
  if (!trimmed.startsWith("```")) {
    return trimmed;
  }
  const lines = trimmed.split(/\r?\n/);
  const opening = lines[0]?.trim().toLowerCase();
  if ((opening === "```json" || opening === "```") && lines.at(-1)?.trim() === "```") {
    return lines.slice(1, -1).join("\n").trim();
  }
  return trimmed;
}

export function looksLikeJsonReport(value: string) {
  const trimmed = value.trim();
  return trimmed.startsWith("{") && trimmed.endsWith("}");
}

export function structuredJsonReportText(jsonText: string) {
  const text = unwrapJsonCodeFence(jsonText);
  if (!looksLikeJsonReport(text)) {
    return "";
  }
  try {
    return extractStructuredReportText(JSON.parse(text) as unknown);
  } catch {
    return "";
  }
}

export function extractStructuredReportText(value: unknown): string {
  if (!value || typeof value !== "object") {
    return "";
  }
  const report = value as Record<string, unknown>;
  const lines: string[] = [];
  if (typeof report.summary === "string" && report.summary.trim()) {
    lines.push(`### ${labels.summary}`, "", report.summary.trim());
  }
  appendStringList(lines, labels.findings, report.findings);
  appendStringList(lines, labels.recommendations, report.recommendations);
  if (typeof report.handoff_reason === "string" && report.handoff_reason.trim()) {
    lines.push("", `**${labels.handoffReason}:** ${report.handoff_reason.trim()}`);
  }
  if (typeof report.confidence === "number") {
    lines.push(`**${labels.confidence}:** ${report.confidence}`);
  }
  return lines.join("\n");
}

function appendStringList(lines: string[], heading: string, value: unknown) {
  const items = Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
  if (!items.length) {
    return;
  }
  lines.push("", `**${heading}:**`);
  for (const item of items) {
    lines.push(`- ${item.trim()}`);
  }
}
