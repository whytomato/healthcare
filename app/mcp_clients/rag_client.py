from __future__ import annotations

import json
import os
from pathlib import Path

from app.config import load_env_file
from app.mcp_clients.base_client import BaseMcpClient, McpClientConfig, ToolResult


class RagMcpClient(BaseMcpClient):
    def __init__(self) -> None:
        super().__init__(
            McpClientConfig(
                name="rag",
                command="python",
                args=["-m", "mcp_servers.rag_server"],
            )
        )

    def search_medical_knowledge(self, query: str) -> ToolResult:
        load_env_file()
        knowledge_base = os.getenv("MEDICAL_KNOWLEDGE_BASE")
        if knowledge_base:
            path = Path(knowledge_base)
            if not path.exists():
                return self.not_configured(
                    tool="search_medical_knowledge",
                    required_config=["MEDICAL_KNOWLEDGE_BASE"],
                    message=f"Configured medical knowledge base does not exist: {path}",
                )

            with path.open("r", encoding="utf-8") as file:
                documents = json.load(file)

            terms = [term for term in query.lower().split() if term]
            matched = _rank_documents(documents, terms, top_k=8)
            return ToolResult(
                tool="search_medical_knowledge",
                status="ready",
                data={
                    "source": str(path),
                    "documents": matched,
                    "query": query,
                },
                message="Medical knowledge search completed from local JSON knowledge base.",
            )

        return self.not_configured(
            tool="search_medical_knowledge",
            required_config=["MEDICAL_KNOWLEDGE_BASE"],
            message=(
                "RAG MCP client is defined, but no real medical knowledge base "
                "has been configured."
            ),
        )


def _rank_documents(documents: list[dict], terms: list[str], top_k: int) -> list[dict]:
    ranked = []
    for item in documents:
        symptom_scores = {
            str(symptom.get("name", "")).lower(): float(symptom.get("score", 0.0))
            for symptom in item.get("symptoms", [])
            if isinstance(symptom, dict)
        }
        content = json.dumps(item, ensure_ascii=False).lower()
        score = 0.0
        matched_terms = []
        for term in terms:
            term_score = max(
                (value for name, value in symptom_scores.items() if term in name or name in term),
                default=0.0,
            )
            if term_score > 0:
                score += term_score * 10
                matched_terms.append(term)
            elif term in content:
                score += 0.1
                matched_terms.append(term)

        if score > 0:
            ranked.append((score, matched_terms, item))

    ranked.sort(key=lambda entry: entry[0], reverse=True)
    results = []
    for score, matched_terms, item in ranked[:top_k]:
        results.append(
            {
                **item,
                "retrieval_score": round(score, 4),
                "matched_query_terms": sorted(set(matched_terms)),
            }
        )
    return results
