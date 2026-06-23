from __future__ import annotations

from pathlib import Path


def test_kafka_worker_exposes_configurable_concurrent_task_processing() -> None:
    worker = Path("app/worker/kafka_worker.py").read_text(encoding="utf-8")

    assert "ThreadPoolExecutor" in worker
    assert "--concurrency" in worker
    assert "max_workers=concurrency" in worker
    assert "max_poll_records=concurrency" in worker
    assert "submit_kafka_task" in worker
    assert "pending_futures" in worker
    assert "concurrency: int" in worker


def test_readme_documents_worker_concurrency_for_er_surge() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "--concurrency 4" in readme
    assert "ER surge" in readme
