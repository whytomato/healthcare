import subprocess


def test_frontend_normalizes_fenced_json_inside_final_report_markdown() -> None:
    script = r"""
import fs from "node:fs";
import ts from "./frontend/node_modules/typescript/lib/typescript.js";

const source = fs.readFileSync("frontend/src/reportFormatting.ts", "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ES2020,
    target: ts.ScriptTarget.ES2020
  }
}).outputText;
const moduleUrl = "data:text/javascript;base64," + Buffer.from(compiled).toString("base64");
const { normalizeReportMarkdownText } = await import(moduleUrl);

const raw = `## Final Hospital Report

\`\`\`json
{
  "summary": "45岁男性，因季节性过敏复诊，症状改善中。",
  "findings": ["生命体征稳定", "无需专科转诊"],
  "recommendations": ["等待CBC结果", "按计划门诊随访"],
  "handoff_reason": "门诊随访工作流程完成",
  "confidence": 0.85
}
\`\`\`

### Workflow Summary
- **Selected specialties:** respiratory
- **Disposition:** outpatient_follow_up`;

const formatted = normalizeReportMarkdownText(raw);
if (formatted.includes("\`\`\`json") || formatted.includes('"summary"')) {
  throw new Error(formatted);
}
if (!formatted.includes("45岁男性") || !formatted.includes("生命体征稳定")) {
  throw new Error(formatted);
}
if (!formatted.includes("### Workflow Summary")) {
  throw new Error(formatted);
}
"""
    result = subprocess.run(
        ["node", "--input-type=module"],
        input=script,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
