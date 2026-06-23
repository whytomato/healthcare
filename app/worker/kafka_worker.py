from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

from app.config import load_env_file
from app.contracts import SymptomQueryResult, SymptomQueryTask
from app.workflows.hospital import HospitalOrchestrator


DEFAULT_QUERY_TOPIC = "ai.symptom.query"
DEFAULT_RESULT_TOPIC = "ai.symptom.result"
DEFAULT_PROGRESS_TOPIC = "ai.workflow.progress"


def main() -> None:
    parser = argparse.ArgumentParser(description="Healthcare AI Kafka worker.")
    parser.add_argument("--once-file", help="Run one task from a local JSON file instead of Kafka.")
    parser.add_argument("--output", help="Output path for --once-file result JSON.")
    parser.add_argument("--bootstrap-servers", default=None, help="Kafka bootstrap servers.")
    parser.add_argument("--query-topic", default=DEFAULT_QUERY_TOPIC)
    parser.add_argument("--result-topic", default=DEFAULT_RESULT_TOPIC)
    parser.add_argument("--progress-topic", default=DEFAULT_PROGRESS_TOPIC)
    parser.add_argument("--group-id", default="healthcare-ai-worker")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("HEALTHCARE_WORKER_CONCURRENCY", "1")),
        help="Number of Kafka workflow tasks this worker may process concurrently.",
    )
    args = parser.parse_args()

    load_env_file()
    if args.once_file:
        result = run_once_file(Path(args.once_file))
        output = Path(args.output) if args.output else Path("outputs") / f"{result.task_id}_worker_result.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(to_backend_result_payload(result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"processed task {result.task_id}: {result.status}")
        print(f"result written to {output}")
        return

    run_kafka_worker(
        bootstrap_servers=args.bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        query_topic=args.query_topic,
        result_topic=args.result_topic,
        progress_topic=args.progress_topic,
        group_id=args.group_id,
        concurrency=max(args.concurrency, 1),
    )


def run_once_file(path: Path) -> SymptomQueryResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return process_task(SymptomQueryTask(**payload))


def process_task(
    task: SymptomQueryTask,
    progress_publisher=None,
    patient_history_client=None,
) -> SymptomQueryResult:
    def publish_progress(event: dict[str, Any]) -> None:
        if progress_publisher is not None:
            progress_publisher(to_backend_progress_payload(task.task_id, event))

    try:
        result = HospitalOrchestrator().run(
            case_text=task.case_text,
            patient_id=task.patient_id,
            doctor_id=task.doctor_id,
            language=task.language,
            progress_publisher=publish_progress if progress_publisher is not None else None,
        )
        result["input_metadata"] = task.metadata
        final_status = (
            result["agent_results"][-1]["status"] if result.get("agent_results") else "failed"
        )
        return SymptomQueryResult(
            task_id=task.task_id,
            status=final_status,
            result=result,
        )
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        return SymptomQueryResult(
            task_id=task.task_id,
            status="failed",
            error_message=str(exc),
        )


def run_kafka_worker(
    bootstrap_servers: str,
    query_topic: str,
    result_topic: str,
    progress_topic: str,
    group_id: str,
    concurrency: int,
) -> None:
    try:
        from kafka import KafkaConsumer, KafkaProducer
        from kafka.errors import NoBrokersAvailable
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "kafka-python is required for Kafka mode. Install it with: pip install kafka-python"
        ) from exc

    try:
        consumer = KafkaConsumer(
            query_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            enable_auto_commit=True,
            auto_offset_reset="earliest",
            max_poll_records=concurrency,
        )
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        )
    except NoBrokersAvailable as exc:
        raise SystemExit(
            "Kafka broker is not available at "
            f"{bootstrap_servers}. Start Kafka first, then rerun this worker.\n"
            "Suggested command: docker compose -f infra/docker-compose.kafka.yml up -d\n"
            "Then check: docker ps"
        ) from exc

    producer_lock = Lock()
    pending_futures: set[Future[None]] = set()
    print(
        f"listening on Kafka topic {query_topic}, producing to {result_topic}, "
        f"concurrency={concurrency}"
    )
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for message in consumer:
            payload: dict[str, Any] = message.value
            task = SymptomQueryTask(
                task_id=payload["taskId"],
                case_text=payload["caseText"],
                question=payload.get("question", "What diseases or conditions should be considered?"),
                patient_id=payload.get("patientId"),
                doctor_id=payload.get("doctorId"),
                language=payload.get("language", "zh-CN"),
                metadata=payload.get("metadata", {}),
            )
            pending_futures.add(
                executor.submit(
                    submit_kafka_task,
                    task,
                    producer,
                    producer_lock,
                    result_topic,
                    progress_topic,
                )
            )
            if len(pending_futures) >= concurrency:
                done, pending = wait(pending_futures, return_when=FIRST_COMPLETED)
                pending_futures = set(pending)
                _raise_failed_futures(done)


def submit_kafka_task(
    task: SymptomQueryTask,
    producer: Any,
    producer_lock: Lock,
    result_topic: str,
    progress_topic: str,
) -> None:
    def publish_progress(event: dict[str, Any]) -> None:
        with producer_lock:
            producer.send(progress_topic, event)
            producer.flush()

    result = process_task(
        task,
        progress_publisher=publish_progress,
    )
    with producer_lock:
        producer.send(result_topic, to_backend_result_payload(result))
        producer.flush()
    print(f"processed Kafka task {task.task_id}: {result.status}")


def _raise_failed_futures(futures: set[Future[None]]) -> None:
    for future in futures:
        future.result()


def to_backend_result_payload(result: SymptomQueryResult) -> dict[str, Any]:
    return {
        "taskId": result.task_id,
        "status": result.status,
        "result": result.result,
        "errorMessage": result.error_message,
    }


def to_backend_progress_payload(task_id: str, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": task_id,
        "eventType": event.get("event_type"),
        "agent": event.get("agent"),
        "decision": event.get("decision"),
        "decisionScope": event.get("decision_scope"),
        "reason": event.get("reason"),
        "targetAgents": event.get("target_agents", []),
        "parallelGroup": event.get("parallel_group"),
        "payload": event.get("payload"),
        "durationMs": event.get("duration_ms"),
        "eventIndex": event.get("event_index"),
    }


if __name__ == "__main__":
    main()
