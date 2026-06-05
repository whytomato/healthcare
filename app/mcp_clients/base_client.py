from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class McpClientConfig:
    name: str
    command: str
    args: list[str]


@dataclass(frozen=True)
class ToolResult:
    tool: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    required_config: list[str] = field(default_factory=list)


class BaseMcpClient:
    def __init__(self, config: McpClientConfig) -> None:
        self.config = config

    def describe(self) -> dict:
        return {
            "name": self.config.name,
            "command": self.config.command,
            "args": self.config.args,
        }

    def not_configured(self, tool: str, required_config: list[str], message: str) -> ToolResult:
        return ToolResult(
            tool=tool,
            status="not_configured",
            message=message,
            required_config=required_config,
        )
