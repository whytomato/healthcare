from __future__ import annotations

import re

from app.agents.context import HospitalAgentResult


URGENT_TERMS = {
    "chest discomfort",
    "chest pain",
    "shortness of breath",
    "confusion",
    "severe headache",
    "neck stiffness",
    "high fever",
    "seizure",
    "hemoptysis",
    "胸痛",
    "胸闷",
    "呼吸困难",
    "意识模糊",
    "高热",
    "抽搐",
    "咯血",
    "颈项强直",
}


RESPIRATORY_TERMS = {
    "cough",
    "fever",
    "sputum",
    "shortness of breath",
    "咳嗽",
    "发热",
}


CARDIOLOGY_TERMS = {
    "chest discomfort",
    "chest pain",
    "troponin",
    "palpitation",
    "胸痛",
    "胸闷",
}


INFECTIOUS_DISEASE_TERMS = {
    "fever",
    "infection",
    "sepsis",
    "high fever",
    "高热",
    "感染",
}


NEUROLOGY_TERMS = {
    "confusion",
    "headache",
    "seizure",
    "意识模糊",
    "抽搐",
}


SPECIALTY_RECOMMENDATIONS = {
    "respiratory": "Assess respiratory infection, hypoxia risk, and need for chest imaging.",
    "cardiology": "Assess acute coronary syndrome risk when chest symptoms are present.",
    "infectious_disease": "Assess severe infection risk and consider pathogen testing.",
    "neurology": "Assess altered mental status, meningitis signs, seizure risk, or intracranial causes.",
}


def matched_terms(text: str, terms: set[str]) -> list[str]:
    matched = []
    for term in terms:
        if any(
            not _is_negated_clinical_mention(text, match.start())
            for match in _term_matches(text, term)
        ):
            matched.append(term)
    return sorted(matched)


def select_specialties(case_text: str) -> list[str]:
    selected: list[str] = []
    if matched_terms(case_text, RESPIRATORY_TERMS):
        selected.append("respiratory")
    if matched_terms(case_text, CARDIOLOGY_TERMS):
        selected.append("cardiology")
    if matched_terms(case_text, INFECTIOUS_DISEASE_TERMS):
        selected.append("infectious_disease")
    if matched_terms(case_text, NEUROLOGY_TERMS):
        selected.append("neurology")
    return selected


def selected_specialties(previous: list[HospitalAgentResult]) -> list[str]:
    router = next(
        (result for result in previous if result.agent == "specialist_router_agent"),
        None,
    )
    if not router:
        return []
    return list(router.decisions.get("selected_specialties", []))


def _term_matches(text: str, term: str) -> list[re.Match[str]]:
    if _contains_cjk(term):
        return list(re.finditer(re.escape(term), text, flags=re.IGNORECASE))
    pattern = r"\b" + r"\s+".join(re.escape(part) for part in term.split()) + r"\b"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE))


def _is_negated_clinical_mention(text: str, term_start: int) -> bool:
    segment = text[_last_sentence_boundary(text, term_start) : term_start].lower()
    segment = _after_last_contrast(segment)
    if len(segment) > 96:
        segment = segment[-96:]

    english_cues = [
        "no evidence of",
        "negative for",
        "not experiencing",
        "denies",
        "denied",
        "deny",
        "without",
        "free of",
        "absence of",
        "no",
    ]
    chinese_cues = ["没有", "未见", "未出现", "否认", "不伴", "无", "未"]

    return any(_cue_present(segment, cue) for cue in english_cues) or any(
        cue in segment for cue in chinese_cues
    )


def _last_sentence_boundary(text: str, term_start: int) -> int:
    boundaries = [text.rfind(mark, 0, term_start) for mark in [".", "?", "!", "\n", ";", "。", "？", "！", "；"]]
    return max(boundaries) + 1


def _after_last_contrast(segment: str) -> str:
    contrast_markers = [" but ", " however ", " though ", " except ", "但", "但是", "不过"]
    positions = [segment.rfind(marker) + len(marker) for marker in contrast_markers if marker in segment]
    return segment[max(positions) :] if positions else segment


def _cue_present(segment: str, cue: str) -> bool:
    if " " in cue:
        return cue in segment
    return re.search(rf"\b{re.escape(cue)}\b", segment) is not None


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)
