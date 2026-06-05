from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from pathlib import Path


DEFAULT_URL = (
    "https://raw.githubusercontent.com/clinicalml/HealthKnowledgeGraph/"
    "master/DerivedKnowledgeGraph_final.csv"
)
DEFAULT_OUTPUT = Path("data/health_knowledge_graph.json")
SOURCE_URL = "https://github.com/clinicalml/HealthKnowledgeGraph"
PAPER_URL = "https://www.nature.com/articles/s41598-017-05778-z"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and convert clinicalml/HealthKnowledgeGraph to local RAG JSON."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="CSV URL to download.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Keep symptom edges with numeric score greater than this value.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(args.url, timeout=60) as response:
        csv_text = response.read().decode("utf-8-sig")

    documents = convert_csv_to_documents(csv_text, min_score=args.min_score)
    output.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(documents)} documents to {output}")


def convert_csv_to_documents(csv_text: str, min_score: float) -> list[dict]:
    rows = list(csv.DictReader(csv_text.splitlines()))
    if not rows:
        return []

    if {"Diseases", "Symptoms"}.issubset(rows[0].keys()):
        return _convert_disease_symptom_rows(rows, min_score)

    disease_field = _choose_disease_field(rows[0])
    documents = []
    for row_index, row in enumerate(rows, start=1):
        disease = (row.get(disease_field) or f"disease_{row_index}").strip()
        symptoms = []
        for field, raw_value in row.items():
            if field == disease_field:
                continue
            score = _parse_score(raw_value)
            if score is not None and score > min_score:
                symptoms.append({"name": field.strip(), "score": score})

        if not symptoms:
            continue

        symptoms.sort(key=lambda item: item["score"], reverse=True)
        symptom_names = [item["name"] for item in symptoms[:30]]
        documents.append(
            {
                "id": f"hkg-{row_index:03d}",
                "title": disease,
                "source": "clinicalml/HealthKnowledgeGraph",
                "url": SOURCE_URL,
                "paper": PAPER_URL,
                "language": "en",
                "content": (
                    f"{disease} is associated with symptoms including "
                    f"{', '.join(symptom_names)}."
                ),
                "disease": disease,
                "symptoms": symptoms,
            }
        )
    return documents


def _convert_disease_symptom_rows(rows: list[dict[str, str]], min_score: float) -> list[dict]:
    documents = []
    for row_index, row in enumerate(rows, start=1):
        disease = (row.get("Diseases") or f"disease_{row_index}").strip()
        symptoms = _parse_symptom_list(row.get("Symptoms", ""), min_score=min_score)
        if not symptoms:
            continue

        symptom_names = [item["name"] for item in symptoms[:30]]
        documents.append(
            {
                "id": f"hkg-{row_index:03d}",
                "title": disease,
                "source": "clinicalml/HealthKnowledgeGraph",
                "url": SOURCE_URL,
                "paper": PAPER_URL,
                "language": "en",
                "content": (
                    f"{disease} is associated with symptoms including "
                    f"{', '.join(symptom_names)}."
                ),
                "disease": disease,
                "symptoms": symptoms,
            }
        )
    return documents


def _parse_symptom_list(value: str, min_score: float) -> list[dict]:
    symptoms = []
    for match in re.finditer(r"([^,]+?)\s*\(([-+]?\d*\.?\d+)\)", value):
        name = match.group(1).strip()
        score = float(match.group(2))
        if name and score > min_score:
            symptoms.append({"name": name, "score": score})
    symptoms.sort(key=lambda item: item["score"], reverse=True)
    return symptoms


def _choose_disease_field(first_row: dict[str, str]) -> str:
    for candidate in ("disease", "Disease", "condition", "Condition", ""):
        if candidate in first_row:
            return candidate
    return next(iter(first_row))


def _parse_score(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


if __name__ == "__main__":
    main()
