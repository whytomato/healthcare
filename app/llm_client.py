from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.config import load_env_file


@dataclass(frozen=True)
class LlmConfig:
    api_key: str | None
    base_url: str
    model: str
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "LlmConfig":
        load_env_file()
        return cls(
            api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
        )


@dataclass(frozen=True)
class LlmResult:
    status: str
    content: str = ""
    message: str = ""
    required_config: list[str] | None = None
    raw: dict[str, Any] | None = None


class LlmClient:
    """Minimal OpenAI-compatible chat completion client.

    The client is intentionally small and dependency-free. It only makes a
    network request when an API key is configured.
    """

    def __init__(self, config: LlmConfig | None = None) -> None:
        self.config = config or LlmConfig.from_env()

    def chat(self, messages: list[dict[str, str]]) -> LlmResult:
        if not self.config.api_key:
            return LlmResult(
                status="not_configured",
                message="LLM API key is not configured.",
                required_config=["LLM_API_KEY"],
            )

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return LlmResult(
                status="error",
                message=f"LLM HTTP error: {exc.code}",
                required_config=["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"],
            )
        except urllib.error.URLError as exc:
            return LlmResult(
                status="error",
                message=f"LLM connection error: {exc.reason}",
                required_config=["LLM_BASE_URL", "NETWORK_OR_PROXY"],
            )

        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return LlmResult(status="ready", content=content, raw=body)
