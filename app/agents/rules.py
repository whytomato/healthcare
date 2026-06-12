from __future__ import annotations

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


SPECIALTY_RECOMMENDATIONS = {
    "respiratory": "Assess respiratory infection, hypoxia risk, and need for chest imaging.",
    "cardiology": "Assess acute coronary syndrome risk when chest symptoms are present.",
    "infectious_disease": "Assess severe infection risk and consider pathogen testing.",
    "neurology": "Assess altered mental status, meningitis signs, seizure risk, or intracranial causes.",
}


def matched_terms(text: str, terms: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted(term for term in terms if term.lower() in lowered)


def select_specialties(case_text: str) -> list[str]:
    lowered = case_text.lower()
    selected: list[str] = []
    if any(
        term in lowered
        for term in ["cough", "fever", "sputum", "shortness of breath", "咳嗽", "发热"]
    ):
        selected.append("respiratory")
    if any(term in lowered for term in ["chest", "troponin", "palpitation", "胸痛", "胸闷"]):
        selected.append("cardiology")
    if any(term in lowered for term in ["fever", "infection", "sepsis", "高热", "感染"]):
        selected.append("infectious_disease")
    if any(term in lowered for term in ["confusion", "headache", "seizure", "意识模糊", "抽搐"]):
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
