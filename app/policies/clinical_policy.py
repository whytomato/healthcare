from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT


POLICY_PATH = PROJECT_ROOT / "config" / "clinical-policy.json"


@dataclass(frozen=True)
class ClinicalAssessment:
    urgency_level: str
    recommended_department: str
    red_flags: list[str]
    selected_specialties: list[str]
    vital_risk_terms: list[str]


@lru_cache(maxsize=1)
def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _terms(name: str) -> set[str]:
    return set(_policy()[name])


URGENT_TERMS = _terms("urgentTerms")
VITAL_RISK_TERMS = _terms("vitalRiskTerms")
SPECIALTY_RECOMMENDATIONS = dict(_policy()["specialtyRecommendations"])


def assess_patient_encounter(case_text: str) -> ClinicalAssessment:
    red_flags = matched_terms(case_text, URGENT_TERMS)
    urgency_level = "high" if red_flags else "standard"
    return ClinicalAssessment(
        urgency_level=urgency_level,
        recommended_department="emergency" if red_flags else "general_medicine",
        red_flags=red_flags,
        selected_specialties=select_specialties(case_text),
        vital_risk_terms=matched_terms(case_text, VITAL_RISK_TERMS),
    )


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
    specialty_terms = _policy()["specialtyTerms"]
    for specialty in ["respiratory", "cardiology", "infectious_disease", "neurology"]:
        if matched_terms(case_text, set(specialty_terms[specialty])):
            selected.append(specialty)
    return selected


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

    negation = _policy()["negationCues"]
    return any(_cue_present(segment, cue) for cue in negation["english"]) or any(
        cue in segment for cue in negation["chinese"]
    )


def _last_sentence_boundary(text: str, term_start: int) -> int:
    boundaries = [
        text.rfind(mark, 0, term_start)
        for mark in _policy()["sentenceBoundaries"]
    ]
    return max(boundaries) + 1


def _after_last_contrast(segment: str) -> str:
    positions = [
        segment.rfind(marker) + len(marker)
        for marker in _policy()["contrastMarkers"]
        if marker in segment
    ]
    return segment[max(positions) :] if positions else segment


def _cue_present(segment: str, cue: str) -> bool:
    if " " in cue:
        return cue in segment
    return re.search(rf"\b{re.escape(cue)}\b", segment) is not None


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)
