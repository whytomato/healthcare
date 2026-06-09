from __future__ import annotations

from app.agents.base import Agent
from app.schemas.message import AgentContext, AgentResult


class SafetyCheckAgent(Agent):
    name = "safety_check_agent"

    red_flag_terms = {
        "胸痛": "胸痛需要排除急性冠脉综合征、肺栓塞等高危情况。",
        "胸闷": "胸闷若伴呼吸困难、低氧或胸痛，应优先评估心肺急症。",
        "呼吸困难": "呼吸困难是需要及时评估的红旗征。",
        "气促": "气促提示可能存在呼吸或循环风险。",
        "咯血": "咯血需要排除肺栓塞、严重感染、肿瘤等情况。",
        "意识障碍": "意识障碍属于急危重症信号。",
        "意识模糊": "意识模糊需要优先评估中枢神经系统感染、代谢异常或休克。",
        "高热": "持续高热需要评估重症感染风险。",
        "抽搐": "抽搐需要紧急评估神经系统或代谢异常。",
        "颈项强直": "发热伴颈项强直需要警惕脑膜炎或蛛网膜下腔出血。",
        "neck stiffness": "Fever with neck stiffness requires urgent assessment for meningitis or intracranial bleeding.",
        "severe headache": "Severe headache with fever or neck stiffness is a neurological red flag.",
    }

    def run(self, context: AgentContext, previous: list[AgentResult]) -> AgentResult:
        symptom_result = self.previous_result(previous, "symptom_extraction_agent")
        differential_result = self.previous_result(previous, "differential_diagnosis_agent")
        evidence_result = self.previous_result(previous, "evidence_review_agent")

        if not symptom_result or symptom_result.status != "ready":
            return self.ready(
                summary="Safety red-flag check completed with incomplete symptom extraction.",
                recommendations=[
                    "No normalized symptoms were available; collect missing case details before full analysis."
                ],
                data={
                    "used_previous_agents": [
                        "symptom_extraction_agent_missing",
                        (
                            "differential_diagnosis_agent"
                            if differential_result
                            else "differential_diagnosis_agent_missing"
                        ),
                        "evidence_review_agent" if evidence_result else "evidence_review_agent_missing",
                    ],
                    "red_flags": [],
                    "limited_by_incomplete_input": True,
                    "handoff_to": ["report_agent"],
                },
                confidence=0.3,
            )

        symptoms = symptom_result.data.get("symptom_candidates", [])
        text = " ".join([context.case_text, *[str(item) for item in symptoms]]).lower()
        detected = [
            {"term": term, "reason": reason}
            for term, reason in self.red_flag_terms.items()
            if term.lower() in text
        ]

        recommendations = []
        if detected:
            recommendations.append(
                "存在红旗征线索，建议医生优先评估生命体征、血氧、意识状态和急诊风险。"
            )
        else:
            recommendations.append(
                "未通过本地规则发现明确红旗征；仍需结合查体和检查结果判断。"
            )

        return self.ready(
            summary="Safety red-flag check completed using symptom extraction and multi-agent workflow state.",
            findings=[f"{item['term']}: {item['reason']}" for item in detected],
            recommendations=recommendations,
            data={
                "used_previous_agents": [
                    "symptom_extraction_agent",
                    (
                        "differential_diagnosis_agent"
                        if differential_result
                        else "differential_diagnosis_agent_missing"
                    ),
                    "evidence_review_agent" if evidence_result else "evidence_review_agent_missing",
                ],
                "red_flags": detected,
                "differential_ready": bool(
                    differential_result and differential_result.status == "ready"
                ),
                "evidence_ready": bool(evidence_result and evidence_result.status == "ready"),
                "handoff_to": ["report_agent"],
            },
            confidence=0.75 if detected else 0.6,
        )
