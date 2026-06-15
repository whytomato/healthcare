from __future__ import annotations

from typing import Any


def history_summary(history_lookup: dict[str, Any]) -> dict[str, Any]:
    summary = history_lookup.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def history_list(history_lookup: dict[str, Any], key: str) -> list[Any]:
    value = history_summary(history_lookup).get(key, [])
    return list(value) if isinstance(value, list) else []


def has_history(history_lookup: dict[str, Any]) -> bool:
    return any(
        history_list(history_lookup, key)
        for key in [
            "recentEncounters",
            "knownConditions",
            "allergies",
            "currentMedications",
            "previousDispositions",
            "lastFinalReports",
        ]
    )
