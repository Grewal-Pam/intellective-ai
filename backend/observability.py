from __future__ import annotations

import json
import logging
import threading
import time
from collections import Counter
from typing import Any

LOG_FORMAT = "%(message)s"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {"args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName"}:
                continue
            if key not in payload:
                payload[key] = value
        return json.dumps(payload, default=str)


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._request_counts: Counter[tuple[str, int]] = Counter()
        self._request_duration_ms = 0.0
        self._request_total = 0
        self._adapter_calls: Counter[str] = Counter()

    def record_request(self, method: str, path: str, status: int, duration_ms: float) -> None:
        with self._lock:
            self._request_counts[(method, status)] += 1
            self._request_duration_ms += duration_ms
            self._request_total += 1

    def record_adapter_call(self, provider: str) -> None:
        with self._lock:
            self._adapter_calls[provider] += 1

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                '# HELP intellective_ai_http_requests_total Total HTTP requests handled by the app',
                '# TYPE intellective_ai_http_requests_total counter',
            ]
            for (method, status), count in sorted(self._request_counts.items()):
                lines.append(
                    f'intellective_ai_http_requests_total{{method="{method}",status="{status}"}} {count}'
                )

            lines.extend(
                [
                    '# HELP intellective_ai_http_request_duration_ms Cumulative HTTP request duration in milliseconds',
                    '# TYPE intellective_ai_http_request_duration_ms counter',
                    f"intellective_ai_http_request_duration_ms {self._request_duration_ms:.3f}",
                    '# HELP intellective_ai_http_requests_seen_total Number of HTTP requests seen by the app',
                    '# TYPE intellective_ai_http_requests_seen_total counter',
                    f"intellective_ai_http_requests_seen_total {self._request_total}",
                    '# HELP intellective_ai_model_adapter_calls_total Model adapter calls grouped by provider',
                    '# TYPE intellective_ai_model_adapter_calls_total counter',
                ]
            )
            for provider, count in sorted(self._adapter_calls.items()):
                lines.append(
                    f'intellective_ai_model_adapter_calls_total{{provider="{provider}"}} {count}'
                )
            lines.append("")
            return "\n".join(lines)


_metrics = MetricsRegistry()


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("intellective_ai")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter(LOG_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


request_logger = configure_logging()
metrics = _metrics


def observe_request(method: str, path: str, status: int, start_time: float) -> None:
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    metrics.record_request(method, path, status, duration_ms)
    request_logger.info(
        "request_completed",
        extra={
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": round(duration_ms, 3),
        },
    )


def observe_adapter_call(provider: str) -> None:
    metrics.record_adapter_call(provider)
    request_logger.info("adapter_called", extra={"provider": provider})
