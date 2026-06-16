from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import PROJECT_ROOT


DEMO_CASES_PATH = PROJECT_ROOT / "config" / "demo-cases.json"


@lru_cache(maxsize=1)
def demo_cases() -> list[dict[str, Any]]:
    return json.loads(DEMO_CASES_PATH.read_text(encoding="utf-8"))


def demo_case(case_id: str) -> dict[str, Any]:
    for item in demo_cases():
        if item["id"] == case_id:
            return dict(item)
    available = ", ".join(item["id"] for item in demo_cases())
    raise ValueError(f"Unknown demo case '{case_id}'. Available: {available}")
