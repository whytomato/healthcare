from __future__ import annotations

from app.agents.context import HospitalAgentResult


def selected_specialties(previous: list[HospitalAgentResult]) -> list[str]:
    router = next(
        (result for result in previous if result.agent == "specialist_router_agent"),
        None,
    )
    if not router:
        return []
    return list(router.decisions.get("selected_specialties", []))
